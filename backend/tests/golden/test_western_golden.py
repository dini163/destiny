"""Golden tests for the Western engine, pinned to Swiss Ephemeris output.

Reference chart: 2000-01-01 12:00 UT at Greenwich (51.4769N, 0.0005E). This is
the J2000 epoch, so the Julian day is exactly 2451545.0, and the expected
positions below were read directly from pyswisseph 2.10 (Moshier) and are
astronomically self-consistent (e.g. at local noon the Sun culminates on the MC).
"""

from datetime import date, time

import pytest
from fastapi.testclient import TestClient

from app.core.errors import UnsupportedMethodError
from app.engines.western import compute_western_chart

GREENWICH_LAT = 51.4769
GREENWICH_LON = -0.0005


def _greenwich_chart():
    return compute_western_chart(
        birth_date=date(2000, 1, 1),
        birth_time=time(12, 0),
        latitude=GREENWICH_LAT,
        longitude=GREENWICH_LON,
        utc_offset_hours=0.0,
    )


def test_julian_day_at_j2000_epoch() -> None:
    assert _greenwich_chart().julian_day == pytest.approx(2451545.0, abs=1e-4)


def test_sun_moon_ascendant_signs() -> None:
    chart = _greenwich_chart()
    assert chart.sun_sign == "Capricorn"
    assert chart.moon_sign == "Scorpio"
    assert chart.ascendant_sign == "Aries"
    sun = next(p for p in chart.planets if p.name == "Sun")
    assert sun.sign_index == 9
    assert sun.degree_in_sign == pytest.approx(10.37, abs=0.05)
    assert sun.retrograde is False


def test_sun_culminates_near_midheaven_at_local_noon() -> None:
    chart = _greenwich_chart()
    mc = next(a for a in chart.axes if a.name == "MC")
    sun = next(p for p in chart.planets if p.name == "Sun")
    assert mc.sign == "Capricorn"
    assert abs(mc.longitude - sun.longitude) < 2.0


def test_saturn_retrograde_flag_matches_negative_speed() -> None:
    saturn = next(p for p in _greenwich_chart().planets if p.name == "Saturn")
    assert saturn.speed < 0
    assert saturn.retrograde is True


def test_chart_structure_counts() -> None:
    chart = _greenwich_chart()
    assert len(chart.planets) == 10
    assert len(chart.houses) == 12
    assert {axis.name for axis in chart.axes} == {"ASC", "DES", "MC", "IC"}
    assert sum(chart.element_balance.values()) == 10
    assert sum(chart.modality_balance.values()) == 10


def test_axes_are_opposite_pairs() -> None:
    longitudes = {axis.name: axis.longitude for axis in _greenwich_chart().axes}
    assert longitudes["DES"] == pytest.approx((longitudes["ASC"] + 180) % 360, abs=1e-3)
    assert longitudes["IC"] == pytest.approx((longitudes["MC"] + 180) % 360, abs=1e-3)


def test_first_house_cusp_equals_ascendant() -> None:
    chart = _greenwich_chart()
    ascendant = next(a.longitude for a in chart.axes if a.name == "ASC")
    assert chart.houses[0].house == 1
    assert chart.houses[0].longitude == pytest.approx(ascendant, abs=1e-3)


def test_nodes_are_opposite_and_in_expected_sign() -> None:
    nodes = _greenwich_chart().nodes
    assert nodes.south_node_longitude == pytest.approx((nodes.north_node_longitude + 180) % 360, abs=1e-3)
    assert nodes.north_node_sign == "Leo"  # ~125 degrees


def test_aspects_respect_their_orbs() -> None:
    valid_types = {"conjunction", "sextile", "square", "trine", "opposition"}
    for aspect in _greenwich_chart().aspects:
        assert aspect.type in valid_types
        assert 0.0 <= aspect.orb <= 8.0


def test_utc_offset_converts_local_to_universal() -> None:
    chart = compute_western_chart(
        birth_date=date(1990, 6, 15),
        birth_time=time(8, 30),
        latitude=39.9042,
        longitude=116.4074,
        utc_offset_hours=8.0,
    )
    assert chart.local_datetime == "1990-06-15 08:30"
    assert chart.utc_datetime == "1990-06-15 00:30"
    assert chart.sun_sign == "Gemini"  # mid-June
    assert chart.utc_offset_source == "explicit"


def test_longitude_fallback_offset_is_flagged() -> None:
    chart = compute_western_chart(
        birth_date=date(1990, 6, 15),
        birth_time=time(8, 30),
        latitude=39.9042,
        longitude=116.4074,
        utc_offset_hours=None,
    )
    assert chart.utc_offset_source == "longitude_approximation"
    assert chart.utc_offset_hours == 8.0  # round(116.4074 / 15)


def test_unsupported_house_system_raises() -> None:
    with pytest.raises(UnsupportedMethodError):
        compute_western_chart(
            birth_date=date(2000, 1, 1),
            birth_time=time(12, 0),
            latitude=0.0,
            longitude=0.0,
            house_system="Z",
        )


def test_western_natal_endpoint(client: TestClient) -> None:
    response = client.post(
        "/api/v1/western/natal",
        json={
            "birth_date": "2000-01-01",
            "birth_time": "12:00",
            "latitude": GREENWICH_LAT,
            "longitude": GREENWICH_LON,
            "utc_offset_hours": 0,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["sun_sign"] == "Capricorn"
    assert body["ascendant_sign"] == "Aries"
    assert len(body["planets"]) == 10
    assert body["engine"] == "pyswisseph"


def test_western_natal_requires_location(client: TestClient) -> None:
    response = client.post(
        "/api/v1/western/natal",
        json={"birth_date": "2000-01-01", "birth_time": "12:00"},
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_birth_data"
