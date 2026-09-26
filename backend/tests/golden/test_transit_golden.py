"""Golden tests for the transit / progression / solar-arc overlay engine.

Reference: natal 2000-01-01 12:00 UT at Greenwich (51.4769N, 0.0005E), projected to
target 2026-09-25. The natal anchor is the J2000 epoch (JD 2451545.0), so the target
Julian day is exactly natal JD + elapsed days, and the solar arc tracks the progressed
Sun's travel (≈1°/year × age). Values were read directly from pyswisseph 2.10 (Moshier)
via the engine and are astronomically self-consistent.
"""

from datetime import date, time

import pytest
from fastapi.testclient import TestClient

from app.core.errors import UnsupportedMethodError
from app.engines.transit import compute_transits

LAT = 51.4769
LON = -0.0005
BIRTH = date(2000, 1, 1)
TARGET = date(2026, 9, 25)


def _chart(target: date = TARGET):
    return compute_transits(
        birth_date=BIRTH,
        birth_time=time(12, 0),
        latitude=LAT,
        longitude=LON,
        utc_offset_hours=0.0,
        house_system="P",
        target_date=target,
        ephemeris_path=None,
    )


def test_embeds_the_real_natal_chart() -> None:
    chart = _chart()
    assert chart.natal.sun_sign == "Capricorn"
    assert chart.natal.ascendant_sign == "Aries"
    assert len(chart.natal.planets) == 10


def test_target_julian_day_is_real() -> None:
    chart = _chart()
    assert chart.target_date == "2026-09-25"
    # Noon UT on 2026-09-25; natal JD is J2000 = 2451545.0.
    assert chart.target_julian_day == pytest.approx(2461309.0, abs=0.01)


def test_progression_age_and_solar_arc_are_consistent() -> None:
    chart = _chart()
    assert chart.progression.age_years == pytest.approx(26.7329, abs=0.01)
    # Solar arc ≈ 1°/year × age: the directed arc the whole natal chart advances by.
    assert chart.solar_arc.arc_degrees == pytest.approx(27.2233, abs=0.05)
    assert chart.solar_arc.arc_text == "27°13'"
    # Day-for-a-year: ~26.7 days after the natal date.
    assert chart.progression.progressed_date == "2000-01-28"


def test_progressed_moon_sign_and_natal_house() -> None:
    chart = _chart()
    assert chart.progression.moon_sign_zh == "天蝎"
    assert chart.progression.moon_natal_house == 7


def test_three_layers_each_produce_positions_and_aspects() -> None:
    chart = _chart()
    moving_names = {p.name for p in chart.transit_positions}
    assert {"Sun", "Moon"} <= moving_names
    assert len(chart.transit_aspects) > 0
    assert len(chart.progression.aspects) > 0
    assert len(chart.solar_arc.aspects) > 0


def test_cross_aspect_types_orbs_and_natures_are_valid() -> None:
    chart = _chart()
    valid_types = {"conjunction", "sextile", "square", "trine", "opposition"}
    valid_natures = {"fusion", "harmonious", "challenging"}
    for aspect in chart.transit_aspects:
        assert aspect.type in valid_types
        assert aspect.nature in valid_natures
        assert 0.0 <= aspect.orb <= 10.0


def test_target_before_birth_raises() -> None:
    with pytest.raises(UnsupportedMethodError):
        _chart(target=date(1999, 1, 1))


def test_transit_endpoint(client: TestClient) -> None:
    response = client.post(
        "/api/v1/transit/chart",
        json={
            "birth_date": "2000-01-01",
            "birth_time": "12:00",
            "latitude": LAT,
            "longitude": LON,
            "utc_offset_hours": 0,
            "house_system": "P",
            "target_date": "2026-09-25",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["target_date"] == "2026-09-25"
    assert body["engine"] == "pyswisseph"
    assert body["solar_arc"]["arc_text"] == "27°13'"
    assert len(body["transit_aspects"]) > 0


def test_transit_endpoint_rejects_pre_birth_target(client: TestClient) -> None:
    response = client.post(
        "/api/v1/transit/chart",
        json={
            "birth_date": "2000-01-01",
            "birth_time": "12:00",
            "latitude": LAT,
            "longitude": LON,
            "utc_offset_hours": 0,
            "target_date": "1999-01-01",
        },
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "unsupported_method"
