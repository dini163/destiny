"""Golden tests for the Vedic (sidereal / Jyotish) engine.

Reference: 2000-01-01 12:00 UT at Greenwich (51.4769N, 0.0005E) — the J2000 epoch, so
the Julian day is exactly 2451545.0. Longitudes use the Lahiri (Chitrapaksha) ayanamsa
(≈23.86° at J2000): sidereal = tropical − ayanamsa. The Vimshottari timeline is derived
from the natal Moon's nakshatra and is astronomically self-consistent (the ten periods
tile exactly 120 years and follow the fixed lord cycle from the birth lord).
"""

from datetime import date, time

import pytest
from fastapi.testclient import TestClient

from app.content.vedic import DASHA_ORDER, GRAHAS, VIMSHOTTARI_TOTAL, nakshatra_of
from app.engines.vedic import compute_vedic_chart

LAT = 51.4769
LON = -0.0005
BIRTH = date(2000, 1, 1)
TARGET = date(2026, 9, 25)


def _chart(target: date = TARGET):
    return compute_vedic_chart(
        birth_date=BIRTH,
        birth_time=time(12, 0),
        latitude=LAT,
        longitude=LON,
        utc_offset_hours=0.0,
        target_date=target,
        ephemeris_path=None,
    )


def test_julian_day_and_lahiri_ayanamsa() -> None:
    chart = _chart()
    assert chart.julian_day == pytest.approx(2451545.0, abs=1e-4)
    assert chart.zodiac == "sidereal"
    assert chart.ayanamsa_name == "Lahiri (Chitrapaksha)"
    assert 23.0 < chart.ayanamsa < 25.0


def test_navagraha_are_the_nine_classical_grahas_in_order() -> None:
    chart = _chart()
    assert [p.name for p in chart.planets] == [g.name for g in GRAHAS]
    assert len(chart.planets) == 9
    # No modern planets in classical Jyotish.
    assert {"Uranus", "Neptune", "Pluto"}.isdisjoint({p.name for p in chart.planets})


def test_ketu_is_exactly_opposite_rahu() -> None:
    chart = _chart()
    rahu = next(p.longitude for p in chart.planets if p.name == "Rahu")
    ketu = next(p.longitude for p in chart.planets if p.name == "Ketu")
    assert ketu == pytest.approx((rahu + 180.0) % 360.0, abs=1e-6)


def test_lagna_and_moon_are_sidereal() -> None:
    chart = _chart()
    assert chart.lagna_sign_zh == "白羊"
    assert chart.lagna_degree_text == "0°24'"
    assert chart.moon_sign_zh == "天秤"
    assert chart.moon_nakshatra_zh == "室伐底"  # Swati, ruled by Rahu
    assert chart.moon_nakshatra_lord_zh == "罗睺"
    assert chart.moon_pada == 4


def test_each_graha_nakshatra_matches_its_own_longitude() -> None:
    chart = _chart()
    for planet in chart.planets:
        assert planet.nakshatra == nakshatra_of(planet.longitude).name_en
        assert 1 <= planet.pada <= 4


def test_whole_sign_houses_counted_from_lagna() -> None:
    chart = _chart()
    assert len(chart.rashis) == 12
    assert sum(1 for r in chart.rashis if r.is_lagna) == 1
    lagna = next(r for r in chart.rashis if r.is_lagna)
    assert lagna.house == 1
    for planet in chart.planets:
        cell = next(r for r in chart.rashis if r.sign_index == planet.sign_index)
        assert planet.house == cell.house
        assert planet.name in cell.planet_names


def test_vimshottari_span_and_birth_balance() -> None:
    chart = _chart()
    vs = chart.vimshottari
    assert vs.total_years == VIMSHOTTARI_TOTAL == 120
    assert vs.birth_nakshatra_zh == "室伐底"
    assert vs.birth_lord == "Rahu"
    assert vs.balance_at_birth_years == pytest.approx(0.7147, abs=0.01)
    assert 0.0 < vs.balance_at_birth_years <= 18.0  # Rahu's full span


def test_mahadashas_tile_the_full_cycle_in_fixed_order() -> None:
    chart = _chart()
    vs = chart.vimshottari
    assert sum(m.years for m in vs.mahadashas) == pytest.approx(120.0, abs=0.05)
    lords = [m.lord for m in vs.mahadashas]
    start = DASHA_ORDER.index(lords[0])
    for i, lord in enumerate(lords):
        assert lord == DASHA_ORDER[(start + i) % 9]


def test_antardashas_sum_to_their_mahadasha() -> None:
    chart = _chart()
    for md in chart.vimshottari.mahadashas:
        assert md.antardashas
        assert sum(a.years for a in md.antardashas) == pytest.approx(md.years, abs=0.05)


def test_exactly_one_current_period_is_marked() -> None:
    chart = _chart()
    vs = chart.vimshottari
    current_md = [m for m in vs.mahadashas if m.is_current]
    assert len(current_md) == 1
    assert current_md[0].lord == "Saturn"
    assert sum(1 for a in current_md[0].antardashas if a.is_current) == 1
    assert vs.current is not None
    assert vs.current.mahadasha_lord_zh == "土星"
    assert vs.current.antardasha_lord_zh == "太阳"
    assert vs.current.target_date == "2026-09-25"


def test_vedic_natal_endpoint(client: TestClient) -> None:
    response = client.post(
        "/api/v1/vedic/natal",
        json={
            "birth_date": "2000-01-01",
            "birth_time": "12:00",
            "latitude": LAT,
            "longitude": LON,
            "utc_offset_hours": 0,
            "target_date": "2026-09-25",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["zodiac"] == "sidereal"
    assert body["lagna_sign_zh"] == "白羊"
    assert len(body["planets"]) == 9
    assert body["vimshottari"]["total_years"] == 120
    assert body["engine"] == "pyswisseph"


def test_vedic_natal_requires_location(client: TestClient) -> None:
    response = client.post(
        "/api/v1/vedic/natal",
        json={"birth_date": "2000-01-01", "birth_time": "12:00"},
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_birth_data"
