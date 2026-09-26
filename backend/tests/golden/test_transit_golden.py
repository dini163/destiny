"""Golden tests for the transit / progression / solar-arc overlay engine.

Reference: natal 2000-01-01 12:00 UT at Greenwich (51.4769N, 0.0005E), projected to
target 2026-09-25. The anchors here are derived by hand, not read back from the engine:

* **儒略日** — the target is evaluated at noon UT, so its Julian day is the calendar
  formula `date(2026, 9, 25).toordinal() + 1721424.5 + 12/24 = 2461309.0` exactly
  (proleptic-Gregorian ordinal + fraction of the day), independent of Swiss Ephemeris.
* **逆行** — `retrograde == (speed < 0)` over the transit and progressed moving layers.
  The solar-arc *directed* points are exempt: they are geometric offsets with `speed`
  forced to 0.0 while keeping the natal retrograde label (`app/engines/transit.py:221`),
  so the rule deliberately does not apply to them — pinned here as a contract, not a bug.
* **相位表** — `transit_aspects` is monotonic in orb, free of duplicate
  `(moving, natal, type)` triples, and respects the same shared `ASPECTS` per-type orb
  limits as the natal and synastry tables; the inclusive `<=` boundary is forced at
  the 8.0 conjunction limit (`app/engines/western.py:61`). Cross-table agreement is *not*
  proved here — it lives in
  `tests/golden/test_western_golden.py::test_aspect_orb_inclusion_is_identical_across_the_three_tables`.

The progression / solar-arc age and arc values remain engine-derived calendar facts; this
file deliberately does not present its expected numbers as ephemeris read-backs — a
value copied out of the engine could only self-confirm it, so every anchor above is
hand-derivable arithmetic instead.

Recount this file's tests: `cd backend && PYTHONIOENCODING=utf-8
.venv/Scripts/python.exe -m pytest tests/golden/test_transit_golden.py -v`.
"""

from datetime import date, time

import pytest
from fastapi.testclient import TestClient

from app.core.errors import UnsupportedMethodError
from app.engines.transit import _cross_aspects, compute_transits
from app.engines.western import ASPECTS
from app.schemas.transit import MovingPoint

#: Conjunction's maximum orb, shared across all three aspect tables (`western.py:61`).
#: Recount: `python -c "from app.engines.western import ASPECTS; print(ASPECTS)"`.
CONJUNCTION_ORB = next(orb for name, _g, _a, orb in ASPECTS if name == "conjunction")


def _mp(name: str, longitude: float) -> MovingPoint:
    """A MovingPoint bare enough to feed `_cross_aspects`.

    几何判定只读 `name`/`longitude`（`app/engines/transit.py:130-134`）。但别把其余字段当惰性
    占位：`_cross_aspects` 会把 `body.name_zh` 与 `body.glyph` 原样抄进 `CrossAspect`
    （`app/engines/transit.py:140-141`），所以这里的空串会出现在输出里——下面的测只比 orb，
    不碰那两处，故无需填真值。
    """
    return MovingPoint(
        name=name, glyph="", name_zh="", longitude=longitude, sign="", sign_zh="",
        sign_glyph="", sign_index=0, degree_in_sign=0.0, degree_text="", natal_house=1,
        retrograde=False, speed=0.0,
    )

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


# ------------------------------------------------------- Step 1/Step 3 独立锚

def test_target_julian_day_from_the_calendar_alone() -> None:
    """目标儒略日 = 序数日 + 1721424.5 + 半日（正午 UT），是历法算式，不查 swisseph。

    `date.toordinal()` 是 proleptic Gregorian 日序，`+ 1721424.5` 把序数 1（公元 1-01-01）
    对齐到儒略历的 -0001-11-24 noon 起点，`+ 12/24` 加正午的半日 → 2461309.0，与响应逐位相符
    （响应 round 到 5 位）。复测：`python -c "from datetime import date;print(date(2026,9,25).toordinal()+1721424.5+0.5)"`。
    """
    chart = _chart()
    hand = date(2026, 9, 25).toordinal() + 1721424.5 + 12.0 / 24.0
    assert chart.target_julian_day == pytest.approx(hand, abs=1e-4)


def test_moving_layer_retrograde_matches_speed_sign_except_solar_arc() -> None:
    """行运/次限两层的 MovingPoint `retrograde == (speed < 0)`；太阳弧 directed 点刻意豁免。

    行运与次限走 `_moving_from_pos`（`app/engines/transit.py:101-103`，retrograde 与 speed 同源同号）；
    太阳弧走 `_moving(..., p.retrograde, 0.0)`（`app/engines/transit.py:220-223`），speed 恒 0 但
    沿用本命逆行标签，所以对弧点 `retrograde != (speed < 0)` 是设计而非缺陷——这里把它钉成契约。
    """
    chart = _chart()
    for layer in (chart.transit_positions, chart.progression.positions):
        for point in layer:
            assert point.retrograde == (point.speed < 0), point.name
    # 弧点的 speed 全为 0.0（被强制），故它不满足同一式子正是设计使然。
    assert all(p.speed == 0.0 for p in chart.solar_arc.positions)


def test_transit_aspects_are_sorted_unique_and_within_their_orbs() -> None:
    """行运相位列：orb 非降序、`(moving, natal, type)` 唯一、不越共享容许度上限。"""
    limit_by_type = {name: orb for name, _g, _a, orb in ASPECTS}
    aspects = _chart().transit_aspects
    orbs = [a.orb for a in aspects]
    assert orbs == sorted(orbs)
    triples = {(a.moving, a.natal, a.type) for a in aspects}
    assert len(triples) == len(aspects)
    for a in aspects:
        assert 0.0 <= a.orb <= limit_by_type[a.type], (a.moving, a.natal, a.type)


def test_transit_aspect_orb_boundary_is_inclusive_at_the_shared_limit() -> None:
    """行运表这一侧：构造 7.9/8.0 计入、8.1 剔除，只证明 `_cross_aspects` 用 `orb <= orb_limit`。

    `_cross_aspects` 迭的是同一份 `ASPECTS`、同一句比较（`app/engines/transit.py:136-138`），
    但本条看不到另外两张表——「三表同口径」由跨表关系测
    `tests/golden/test_western_golden.py::test_aspect_orb_inclusion_is_identical_across_the_three_tables`
    一次喂三张表来证（本命、合盘各自的姊妹条同理，也只钉自己那一张）。8.0 是合相上限
    （`CONJUNCTION_ORB`，`app/engines/western.py:61`）。
    """
    assert CONJUNCTION_ORB == 8.0
    assert [a.orb for a in _cross_aspects([_mp("Sun", 0.0)], [("Saturn", "土星", 7.9)])] == [7.9]
    assert [a.orb for a in _cross_aspects([_mp("Sun", 0.0)], [("Saturn", "土星", 8.0)])] == [8.0]
    assert _cross_aspects([_mp("Sun", 0.0)], [("Saturn", "土星", 8.1)]) == []
