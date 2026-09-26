"""Golden tests for the 西洋合盘 (synastry / composite) engine.

Reference pair: two people born at Greenwich (51.4769N, 0.0005E), UT offset 0, Placidus
houses, Moshier ephemeris (no data files):

* Person A — 1990-06-15 08:30 → Sun Gemini (83.99°), ASC Leo.
* Person B — 1992-11-20 18:45 → Sun Scorpio (238.71°), ASC Cancer.

Composite longitudes are the shorter-arc midpoints of the two natal longitudes and are
checked against that arithmetic directly (composite Sun = midpoint of 83.99 and 238.71
= 161.35). The score is a ledger: ``Σ factors[].delta == value`` and the base leads. All
other values were read from pyswisseph 2.10 (Moshier) via the engine and are stable.
"""

from datetime import date, time

import pytest
from fastapi.testclient import TestClient

from app.core.provenance import MODEL_PARAM_SOURCE
from app.engines.synastry import _midpoint, compute_synastry
from app.schemas.synastry import SynastryPerson

LAT = 51.4769
LON = -0.0005

A_SUN_LON = 83.9903
A_MOON_LON = 343.4131
B_SUN_LON = 238.7083
B_MOON_LON = 192.2743


def _person(birth_date: date, birth_time: time, name: str) -> SynastryPerson:
    return SynastryPerson(
        birth_date=birth_date, birth_time=birth_time,
        latitude=LAT, longitude=LON, utc_offset_hours=0.0, name=name,
    )


def _chart():
    return compute_synastry(
        person_a=_person(date(1990, 6, 15), time(8, 30), "A"),
        person_b=_person(date(1992, 11, 20), time(18, 45), "B"),
        house_system="P",
        ephemeris_path=None,
    )


def test_embeds_both_real_natal_charts() -> None:
    chart = _chart()
    assert chart.person_a.sun_sign == "Gemini"
    assert chart.person_a.sun_sign_zh == "双子"
    assert chart.person_a.ascendant_sign == "Leo"
    assert chart.person_b.sun_sign == "Scorpio"
    assert chart.person_b.sun_sign_zh == "天蝎"
    assert chart.person_b.ascendant_sign == "Cancer"
    assert len(chart.person_a.planets) == len(chart.person_b.planets) == 10
    assert (chart.person_a_name, chart.person_b_name) == ("A", "B")


def test_shorter_arc_midpoint_takes_the_short_way_round() -> None:
    # Same sign-side midpoint and a wrap-through-0° midpoint.
    assert _midpoint(10.0, 20.0) == pytest.approx(15.0)
    assert _midpoint(350.0, 10.0) == pytest.approx(0.0)
    assert _midpoint(83.9903, 238.7083) == pytest.approx(161.3493, abs=1e-3)


def test_composite_planets_are_natal_midpoints() -> None:
    chart = _chart()
    sun = next(p for p in chart.composite.planets if p.name == "Sun")
    moon = next(p for p in chart.composite.planets if p.name == "Moon")
    assert sun.longitude == pytest.approx(_midpoint(A_SUN_LON, B_SUN_LON), abs=1e-3)
    assert sun.longitude == pytest.approx(161.3493, abs=1e-3)
    assert moon.longitude == pytest.approx(_midpoint(A_MOON_LON, B_MOON_LON), abs=1e-3)
    assert chart.composite.sun_sign == "Virgo"
    assert chart.composite.sun_sign_zh == "处女"
    assert chart.composite.moon_sign == "Sagittarius"
    assert chart.composite.ascendant_sign == "Leo"
    # A midpoint is not a moving body.
    assert all(p.speed == 0.0 and p.retrograde is False for p in chart.composite.planets)


def test_composite_balance_and_shape() -> None:
    chart = _chart()
    assert chart.composite.method == "midpoint"
    assert chart.composite.element_balance == {"fire": 2, "earth": 4, "air": 2, "water": 2}
    assert chart.composite.modality_balance == {"cardinal": 2, "fixed": 3, "mutable": 5}
    assert len(chart.composite.houses) == 12
    assert [axis.name for axis in chart.composite.axes] == ["ASC", "DES", "MC", "IC"]
    assert len(chart.composite.aspects) == 14


def test_synastry_aspects_are_valid_and_sorted() -> None:
    chart = _chart()
    valid_types = {"conjunction", "sextile", "square", "trine", "opposition"}
    valid_natures = {"fusion", "harmonious", "challenging"}
    assert len(chart.synastry_aspects) == 56
    orbs = [aspect.orb for aspect in chart.synastry_aspects]
    assert orbs == sorted(orbs)  # tightest first
    for aspect in chart.synastry_aspects:
        assert aspect.type in valid_types
        assert aspect.nature in valid_natures
        assert 0.0 <= aspect.orb <= 8.0


def test_score_ledger_is_self_consistent() -> None:
    chart = _chart()
    counted = [a for a in chart.synastry_aspects if a.counted]
    assert len(counted) == 8
    assert sum(1 for a in chart.synastry_aspects if a.core_bond) == 2
    # factors[0] is the base; one row per counted aspect; Σ delta == value.
    assert chart.score.factors[0].rule == "synastry.base"
    assert chart.score.factors[0].delta == 50.0
    assert len(chart.score.factors) == 1 + len(counted)
    assert sum(factor.delta for factor in chart.score.factors) == pytest.approx(chart.score.value, abs=1e-6)
    assert chart.score.value == pytest.approx(46.41, abs=1e-6)
    assert chart.score.tier == "中和可处"
    # Every non-base row is an explicit model parameter, never a fake classic.
    assert all(factor.source == MODEL_PARAM_SOURCE for factor in chart.score.factors[1:])


def test_only_personal_point_pairs_are_counted() -> None:
    chart = _chart()
    personal = {"Sun", "Moon", "Mercury", "Venus", "Mars", "ASC"}
    for aspect in chart.synastry_aspects:
        expected = aspect.point_a in personal and aspect.point_b in personal
        assert aspect.counted is expected


def test_unknown_house_system_raises_via_endpoint(client: TestClient) -> None:
    response = client.post(
        "/api/v1/synastry/chart",
        json={
            "person_a": {"birth_date": "1990-06-15", "birth_time": "08:30", "latitude": LAT, "longitude": LON},
            "person_b": {"birth_date": "1992-11-20", "birth_time": "18:45", "latitude": LAT, "longitude": LON},
            "house_system": "Z",
        },
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "unsupported_method"


def test_synastry_endpoint_round_trips(client: TestClient) -> None:
    response = client.post(
        "/api/v1/synastry/chart",
        json={
            "person_a": {
                "birth_date": "1990-06-15", "birth_time": "08:30",
                "latitude": LAT, "longitude": LON, "utc_offset_hours": 0, "name": "甲",
            },
            "person_b": {
                "birth_date": "1992-11-20", "birth_time": "18:45",
                "latitude": LAT, "longitude": LON, "utc_offset_hours": 0, "name": "乙",
            },
            "house_system": "P",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["engine"] == "pyswisseph"
    assert body["person_a_name"] == "甲"
    assert body["composite"]["sun_sign"] == "Virgo"
    assert body["score"]["value"] == pytest.approx(46.41, abs=1e-6)
    assert len(body["synastry_aspects"]) == 56
    assert body["provenance"]["tables"][0]["name"] == "synastry_scoring"


def test_missing_location_is_a_birth_data_error(client: TestClient) -> None:
    response = client.post(
        "/api/v1/synastry/chart",
        json={
            "person_a": {"birth_date": "1990-06-15", "birth_time": "08:30"},
            "person_b": {"birth_date": "1992-11-20", "birth_time": "18:45", "latitude": LAT, "longitude": LON},
        },
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_birth_data"


def test_missing_person_is_a_pydantic_422_not_a_domain_error(client: TestClient) -> None:
    response = client.post(
        "/api/v1/synastry/chart",
        json={"person_a": {"birth_date": "1990-06-15", "birth_time": "08:30", "latitude": LAT, "longitude": LON}},
    )
    body = response.json()
    assert response.status_code == 422
    assert "error" not in body
    assert {item["loc"][-1] for item in body["detail"]} == {"person_b"}
