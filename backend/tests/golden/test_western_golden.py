"""Golden tests for the Western engine, anchored on independently derivable astronomy.

Reference chart: 2000-01-01 12:00 UT at Greenwich (51.4769N, 0.0005E) — the J2000
epoch. The anchors below are *not* read back from the engine; each class is derived
by hand and only the value is then compared against the engine, so a wrong engine
would be caught rather than self-confirmed:

* **Julian day** — `2451545.0` is the definition of J2000 (noon TT/UT at the epoch),
  an external constant, not engine output.
* **落座算术** — `sign_index == int(longitude // 30)` and
  `degree_in_sign == round(longitude % 30, 4)` are pure arithmetic on the response's
  own longitude (the `_degree_in_sign` width 4 is from `app/engines/western.py:80-81`);
  the sign/degree helpers are additionally pinned at the 0° / 29°59′ / 30° boundaries
  and at the 60′ text carry (`_format_degree`, `app/engines/western.py:84-92`).
* **宫制** — Whole Sign (W) keeps every longitude and sign_index while only renumbering
  houses, and its house follows `((sign_index - asc_sign_index) % 12) + 1`; there is no
  whole-sign branch in the engine — house always comes from `_house_of` over the cusps
  Swiss Ephemeris returns (`app/engines/western.py:217`), so the formula is a property of
  the sign-aligned W cusps, not a special case.
* **逆行** — `retrograde == (speed < 0)` over all ten bodies, plus Saturn's negative speed
  at the pinned date.
* **相位表** — the natal aspect list is monotonic in orb, free of duplicate
  `(planet1, planet2, type)` triples, and respects the shared `ASPECTS` per-type orb limits;
  the inclusive `<=` boundary is forced arithmetically (orb 7.9/8.0/8.1 vs the 8.0
  conjunction limit at `app/engines/western.py:61`). The natal/transit/synastry boundary tests
  each pin only their own table, so this file also owns the one cross-table relation test
  (`test_aspect_orb_inclusion_is_identical_across_the_three_tables`): one construction, fed
  into all three helpers, must be kept or dropped identically.

Recount this file's tests: 31 = 21 既有 + 6 白话 + 2 装配纪律（控制器 2026-10-06 在 T16 后补的两颗钉：
空段崩而不静默、balance 段键序）+ 2 出处（T17）。
`cd backend && PYTHONIOENCODING=utf-8
.venv/Scripts/python.exe -m pytest tests/golden/test_western_golden.py -v`.
"""

from datetime import date, time

import pytest
from fastapi.testclient import TestClient

from app.content import CONTENT_VERSION
from app.content.western_plain import (
    WESTERN_NONE_BRANCHES,
    WESTERN_PLAIN_NOTE,
    WESTERN_PLAIN_SOURCE,
    WESTERN_SECTION_TITLES,
    axis_sign_key,
    element_key,
    modality_key,
    node_house_key,
    node_sign_key,
    retrograde_key,
)
from app.core.errors import UnsupportedMethodError
from app.engines.plain_corpora import WESTERN
from app.engines.synastry import _synastry_aspects
from app.engines.transit import _cross_aspects
from app.engines.western import (
    ASPECTS,
    _compute_aspects,
    _degree_in_sign,
    _format_degree,
    _sign_index,
    compute_western_chart,
)
from app.schemas.transit import MovingPoint
from app.schemas.western import PlanetPlacement

#: Conjunction's maximum orb, shared by all three aspect tables (`western.py:61`).
#: Recount: `python -c "from app.engines.western import ASPECTS; print(ASPECTS)"`.
CONJUNCTION_ORB = next(orb for name, _g, _a, orb in ASPECTS if name == "conjunction")

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


# ------------------------------------------------------- Step 1(b): 落座边界的纯算术

def _pp(name: str, longitude: float) -> PlanetPlacement:
    """A PlanetPlacement bare enough to feed ``_compute_aspects`` (only name/longitude read).

    The other fields are placeholders — `_compute_aspects` (`app/engines/western.py:131-155`)
    only touches ``name`` and ``longitude`` — so they carry no assertion meaning.
    """
    return PlanetPlacement(
        name=name, glyph="", name_zh="", longitude=longitude, sign="", sign_zh="",
        sign_glyph="", sign_index=0, degree_in_sign=0.0, degree_text="", house=1,
        retrograde=False, speed=0.0,
    )


def test_sign_index_and_degree_at_the_sign_boundaries() -> None:
    """0° / 29°59′ / 30° / 360° 上 `_sign_index`、`_degree_in_sign` 是纯算术，不引 swisseph。

    边界「进位」发生在 30.0 本身（`int(30.0 // 30) == 1`），而不是靠四舍五入蒙对：29.9999
    仍是第 0 座、359.9999 仍是第 11 座、360.0 归一化回第 0 座（`_normalize_longitude`）。
    `_degree_in_sign` 取 `round(x % 30, 4)`，30.0 归到 0.0。复测（会打印被钉的四对值）：
    `python -c "from app.engines.western import _sign_index as s,_degree_in_sign as d;print(s(29.9999),s(30.0),d(30.0),d(29.9999))"` → `0 1 0.0 29.9999`。
    """
    assert _sign_index(0.0) == 0
    assert _sign_index(29.9999) == 0
    assert _sign_index(30.0) == 1
    assert _sign_index(59.9999) == 1
    assert _sign_index(359.9999) == 11
    assert _sign_index(360.0) == 0  # wraps through _normalize_longitude (360 % 360 == 0)
    assert _degree_in_sign(0.0) == 0.0
    assert _degree_in_sign(29.9999) == 29.9999
    assert _degree_in_sign(30.0) == 0.0
    assert _degree_in_sign(359.9999) == 29.9999


def test_degree_text_carries_at_sixty_minutes() -> None:
    """`_format_degree` 的 60′ 进位规则（`app/engines/western.py:88-91`）：分凑满 60 进一度。

    4.9958° → 0.9958×60 = 59.748′ round 到 60 → 进位成 "5°00'"。座首的取整假象也要钉死：
    29.9917° 进位后文本写 "30°00'"，但 `sign_index` 仍停在上一座（度数文本只是显示口径，
    不代表跨座），这是刻意镜像的实现，不是被测值本身「正确」。
    """
    assert _format_degree(10.0) == "10°00'"
    assert _format_degree(0.0) == "0°00'"
    assert _format_degree(4.9958) == "5°00'"   # minutes rounded up into the next degree
    assert _format_degree(29.9917) == "30°00'"  # top-of-sign text artefact, sign unchanged
    assert _format_degree(24.2641) == "24°16'"  # 0.2641×60 = 15.85' → 16' (the J2000 ASC)


# ------------------------------------------------------- Step 1(c): 宫制只动宫不动星

def test_whole_sign_renumbers_houses_without_moving_the_planets() -> None:
    """同一本命 P（Placidus）与 W（Whole Sign）：黄经与 sign_index 完全不变，宫号却重排。

    宫制只喂给 `swe.houses` 定宫头，绝不参与 `swe.calc_ut` 的行星空——所以十曜的 longitude
    与 sign_index 在两制下一字不差；Whole Sign 的宫头按 30° 等分（实测 W cusps 全为 30 的
    整数倍），于是 `house == ((sign_index - asc_sign_index) % 12) + 1`（实现来自
    `app/engines/western.py:217` 的 `_house_of`，无专门整宫制分支）。
    """
    placidus = _greenwich_chart()
    whole = compute_western_chart(
        birth_date=date(2000, 1, 1), birth_time=time(12, 0),
        latitude=GREENWICH_LAT, longitude=GREENWICH_LON,
        utc_offset_hours=0.0, house_system="W",
    )
    # ① 天体位置不受宫制影响。
    assert [(p.name, p.longitude, p.sign_index) for p in whole.planets] == [
        (p.name, p.longitude, p.sign_index) for p in placidus.planets
    ]
    # ② 宫号分布确有变化（至少一颗行星换了宫）。
    assert {p.name: p.house for p in whole.planets} != {p.name: p.house for p in placidus.planets}
    # ③ Whole Sign 的宫号就是星座相对上升所在星座的序差。
    asc_sign_index = next(a.sign_index for a in whole.axes if a.name == "ASC")
    for planet in whole.planets:
        assert planet.house == ((planet.sign_index - asc_sign_index) % 12) + 1, planet.name
    # W 的宫头皆落在 30° 刻度上（整宫制的前提）。
    for cusp in whole.houses:
        assert cusp.longitude % 30 == pytest.approx(0.0, abs=1e-9)


# ------------------------------------------------------- Step 1(d): 逆行 = 速度为负

def test_retrograde_flag_is_the_sign_of_the_speed() -> None:
    """十曜全体 `retrograde == (speed < 0)`：逆行旗标就是速度符号，不是第二套判定。

    引擎 `retrograde = positions[name][3] < 0`、`speed = round(...,6)`（`app/engines/western.py:321-322`），
    二者天然同号（round 到 6 位不会把真实逆行速度抹成 0）。Saturn 于 2000-01-01 12:00 UT
    （金牛 10°24′、黄经 40.3956°）确实逆行这一**单点**锚已由
    `test_saturn_retrograde_flag_matches_negative_speed` 钉住，本条不重复它，只把同一式子推到
    十曜全体。复测：见本文件顶部 pytest -v。
    """
    chart = _greenwich_chart()
    for planet in chart.planets:
        assert planet.retrograde == (planet.speed < 0), planet.name


# ------------------------------------------------------- Step 3: 本命相位表完备性

def test_natal_aspects_are_sorted_unique_and_within_their_orbs() -> None:
    """本命相位列：orb 非降序、`(planet1, planet2, type)` 全表唯一、每种相位不越其共享容许度。

    `_compute_aspects` 对 i<j 每对只留最紧一个再按 orb 排序（`app/engines/western.py:131-155`），
    所以三元组天然唯一、orb 天然非降；上限表 `ASPECTS`（合 8/六合 6/刑 7/拱 8/冲 8）是三表共用，
    这里断言本命这一表不越界。
    """
    limit_by_type = {name: orb for name, _g, _a, orb in ASPECTS}
    aspects = _greenwich_chart().aspects
    orbs = [a.orb for a in aspects]
    assert orbs == sorted(orbs)  # tightest first / non-decreasing
    triples = {(a.planet1, a.planet2, a.type) for a in aspects}
    assert len(triples) == len(aspects)
    for a in aspects:
        assert 0.0 <= a.orb <= limit_by_type[a.type], (a.planet1, a.planet2, a.type)


def test_natal_aspect_orb_boundary_is_inclusive_at_the_shared_limit() -> None:
    """本命表这一侧：用纯构造把合相 orb 逼到 7.9 / 8.0 / 8.1，只有 8.1 被剔除。

    本条只证明 `_compute_aspects` 用的是 `orb <= orb_limit`（`app/engines/western.py:143`），
    对另外两张表一无所知——「三表同口径」是跨表关系测
    `tests/golden/test_western_golden.py::test_aspect_orb_inclusion_is_identical_across_the_three_tables`
    的活，那里把同一份构造同时喂进三张表。行运/合盘各自文件里的姊妹条也只钉自己那一张。
    8.0 是合相上限（`CONJUNCTION_ORB`，`app/engines/western.py:61`）。
    """
    assert CONJUNCTION_ORB == 8.0
    inside = _compute_aspects([_pp("Sun", 0.0), _pp("Moon", 7.9)])
    on_the_limit = _compute_aspects([_pp("Sun", 0.0), _pp("Moon", 8.0)])
    outside = _compute_aspects([_pp("Sun", 0.0), _pp("Moon", 8.1)])
    assert [a.orb for a in inside] == [7.9]
    assert [a.orb for a in on_the_limit] == [8.0]  # inclusive: == limit is kept
    assert outside == []  # 8.1 exceeds every orb limit at delta 8.1


def _mp(name: str, longitude: float) -> MovingPoint:
    """A MovingPoint bare enough to feed `_cross_aspects`.

    几何只读 `name`/`longitude`（`app/engines/transit.py:122-126`）；`name_zh` 与 `glyph` 会被
    抄进 `CrossAspect`（`app/engines/transit.py:132-133`），但下面的关系测只比 orb，所以这里的
    占位串不进入断言。与 `tests/golden/test_transit_golden.py::_mp` 同形状（本仓第二份
    MovingPoint 裸构造器，属已知重复、由收口轮统一处理）。
    """
    return MovingPoint(
        name=name, glyph="", name_zh="", longitude=longitude, sign="", sign_zh="",
        sign_glyph="", sign_index=0, degree_in_sign=0.0, degree_text="", natal_house=1,
        retrograde=False, speed=0.0,
    )


def _pair(name: str, longitude: float) -> list[tuple[str, str, str, float]]:
    """A single synastry point as `_synastry_aspects` wants it: `(name, name_zh, glyph, lon)`."""
    return [(name, "", "", longitude)]


def test_aspect_orb_inclusion_is_identical_across_the_three_tables() -> None:
    """真正的跨表关系测：同一个 delta 喂进三张相位表，必须**同进同出**。

    三条 `test_*_aspect_orb_boundary_is_inclusive_at_the_shared_limit`（本命 / 行运 / 合盘）
    各只钉自己那一张表，谁改了另一张的含/不含口径它们都不会红；本条才是它们没有声称过的那件事：
    同一份构造（相对 0° 点的 delta = `CONJUNCTION_ORB - 0.1 / +0.0 / +0.1`）同时走
    `_compute_aspects`、`_cross_aspects`、`_synastry_aspects`，三个返回集合逐一相等且等于期望的
    keep/keep/drop。上限一律从 `ASPECTS` 派生（`CONJUNCTION_ORB`），本文件不新写死数字。
    三表共用的正是 `app/engines/western.py:60-66` 这张表与同一句 `orb <= orb_limit`
    （`western.py:143`、`transit.py:138`、`synastry.py:136`）。
    """
    cases = [
        (CONJUNCTION_ORB - 0.1, [CONJUNCTION_ORB - 0.1]),  # strictly inside
        (CONJUNCTION_ORB, [CONJUNCTION_ORB]),              # exactly on the shared limit
        (CONJUNCTION_ORB + 0.1, []),                       # past it
    ]
    for delta, expected in cases:
        natal = [a.orb for a in _compute_aspects([_pp("Sun", 0.0), _pp("Moon", delta)])]
        transit = [a.orb for a in _cross_aspects([_mp("Sun", delta)], [("Saturn", "土星", 0.0)])]
        synastry = [a.orb for a in _synastry_aspects(_pair("Sun", 0.0), _pair("Saturn", delta))]
        assert natal == expected, (delta, "natal")
        assert transit == expected, (delta, "transit")
        assert synastry == expected, (delta, "synastry")


# ------------------------------------------- Step 7(T16): 页尾白话块的装配形状


def test_the_plain_block_is_eight_sections_in_the_declared_order() -> None:
    """页尾块的形状契约：八个小节、字面序、每格两键。

    发射序是**产品决定**（先讲星怎么出手，再讲落在哪块生活，再讲星与星的关系，最后给底色），
    所以钉成字面量清单而不是从 `WESTERN_SECTION_TITLES` 派生——派生写法在标题表被重排时不会红，
    而那正是用户会看见的变化。

    代价是这份字面量清单本身：它是发射序在全仓唯一的机器侧记录，**给页尾块加第九段时这里
    是必改的一处**（下面那份断言的列表与「八个小节」那句都要跟着改），漏改就是红而不是漏检。
    """
    chart = _greenwich_chart()
    assert [section.title for section in chart.plain] == [
        "十星落座", "十星落宫", "主要相位", "逆行诸星", "上升与天顶", "北交点", "十二宫主题", "元素与形态",
    ]


def test_the_north_node_section_is_a_byte_for_byte_transcription() -> None:
    """整段逐字节只抄一段（spec §10.3 与偏差表第 6 行）：北交点三行 = 开篇句 + 座 + 宫。

    期望串从**登记表本身**拼，不从响应拼：这样「装配器取了南交点的键」「开篇句串到别的段」
    「多一个空行」都会红，而语料改一个字不需要改这条测（抄 3000 字进 golden 就是 542 条的
    第二份手抄，那是 Plan E偏差 16 算过的债）。
    """
    chart = _greenwich_chart()
    nodes = chart.plain[5]
    expected = "\n".join(
        [
            WESTERN.openers["nodes"],
            WESTERN.entries[node_sign_key(chart.nodes.north_node_sign)],
            WESTERN.entries[node_house_key(chart.nodes.north_node_house)],
        ]
    )
    assert nodes.text == expected


def test_every_section_line_count_is_one_opener_plus_the_fired_facts() -> None:
    """七段的行数 == 该段实发键数 + 1（开篇句），逐段核对，不整块比字符串。

    这条管的是「漏句」：`keep` 分组按传入序逐条 `reading()`，少一个键就少一行，而整段字符串
    比对在 542 条规模上抄不动（上一段说的就是这件事）。行数与盘面事实的**计数**关系是唯一
    写得动、也真判得住的形状。
    """
    chart = _greenwich_chart()
    non_zero_elements = sum(1 for count in chart.element_balance.values() if count > 0)
    non_zero_modalities = sum(1 for count in chart.modality_balance.values() if count > 0)
    retro_count = sum(1 for planet in chart.planets if planet.retrograde)
    expected_lines = [11, 11, len(chart.aspects) + 1, retro_count + 1, 3, 3, 13,
                      non_zero_elements + non_zero_modalities + 1]
    assert [len(section.text.split("\n")) for section in chart.plain] == expected_lines


def test_the_axis_section_does_not_borrow_des_or_ic() -> None:
    """盘面四轴而白话两轴（偏差表第 17 行的覆盖面决定的）：`axis` 段必须逐字节等于 ASC 与 MC 两句。"""
    chart = _greenwich_chart()
    asc = next(a for a in chart.axes if a.name == "ASC")
    mc = next(a for a in chart.axes if a.name == "MC")
    expected = "\n".join(
        [
            WESTERN.openers["axis"],
            WESTERN.entries[axis_sign_key("ASC", asc.sign)],
            WESTERN.entries[axis_sign_key("MC", mc.sign)],
        ]
    )
    assert chart.plain[4].text == expected


def test_the_sun_and_moon_never_appear_in_the_retrograde_lines() -> None:
    """偏差表第 11 行的第二半：日月速度不为负 ⇒ 那两句今天不发射，段里不许有它们。

    第一半（两键仍在 `universe()` 里、也就仍在 entries 里）由 T15 追加的
    `test_the_key_universe_is_the_declared_542_and_the_table_covers_it` 钉；本条钉的是**发射面**。
    J2000 盘 Saturn 逆行（`test_saturn_retrograde_flag_matches_negative_speed` 已钉），所以这一段的
    那一行必须存在且只有它——一个反例都没有的「不出现」测是测不出装配错的。
    """
    chart = _greenwich_chart()
    lines = chart.plain[3].text.split("\n")
    assert lines[0] == WESTERN.openers["retrograde"]
    assert lines[1:] == [WESTERN.entries[retrograde_key("Saturn")]]
    assert WESTERN.entries[retrograde_key("Sun")] not in lines
    assert WESTERN.entries[retrograde_key("Moon")] not in lines


def test_an_empty_aspect_list_fires_the_none_opener_and_nothing_else() -> None:
    """`aspect_none` 分支用构造输入钉（真盘最少 11 条相位，见偏差表第 14 行）。

    入参全部来自 `_greenwich_chart()` 的**真实 schema 件**，只把 `aspects` 换成 `[]`——与
    `test_natal_aspect_orb_boundary_is_inclusive_at_the_shared_limit` 用 `_pp()` 构造行星对
    同一条路子（AGENTS §9：这是真实件的真实边界，不是 mock 响应）。
    """
    # 本文件仅有的两条函数级 import，都只为 `build_plain`（另一条在
    # `test_a_section_that_goes_empty_without_a_declared_none_branch_crashes`）。而
    # `app/engines/` 里那处（`build_plain` 自己）是该目录唯一一处；`app/` 下更早还有一处
    # `app/content/meihua.py:110`，所以「全站第一处」这个说法对 `app/` 不成立。
    # 为什么这里必须函数级而不能并进文件顶部的 import 段：T16 Step 1 要的是**逐条** RED——
    # 五条红在 `AttributeError: 'WesternChart' object has no attribute 'plain'`、本条红在
    # `ImportError: cannot import name 'build_plain'`，同一次运行里既有 21 条passed。而模块级
    # import 一个还不存在的名字会让 pytest 在**收集期**就中断（实测 `collected 0 items / 1 error`，
    # 整文件一条都不跑），那样的 RED 既分不出是哪一条门坏、也证明不了既有 21 条没被碰。
    # 换句话说：这里的函数级 import 不是风格选择，是「让门先红后绿」这条纪律能落地的前提。
    # 复现（Step 1 的RED）：把下面这行挪到文件顶部、删掉本注释，同一条命令得到
    # `collected 0 items / 1 error` 而 6 failed / 21 passed。
    from app.engines.western import build_plain

    chart = _greenwich_chart()
    plain = build_plain(
        planets=chart.planets, axes=chart.axes, aspects=[], nodes=chart.nodes,
        element_balance=chart.element_balance, modality_balance=chart.modality_balance,
    )
    aspect_section = plain[2]
    assert aspect_section.title == "主要相位"
    assert aspect_section.text == WESTERN.openers["aspect_none"]
    assert len(plain) == 8


def test_a_section_that_goes_empty_without_a_declared_none_branch_crashes() -> None:
    """一张恒非空的段收不到键就崩，不静默拼出「只有开篇句」的一段。

    `build_plain` 的 `emit` 有两个空态合取项，后半段（`section in WESTERN_NONE_BRANCHES`）
    在本任务落地时**零覆盖**：删掉它，本文件 27 条一条不红（控制器 2026-10-06 实测），
    而装配器会去拿 section 自己的开篇句拼一段空话——页面上读起来像「这一段今天没什么可说」，
    这与 `plain_compose` 开篇「未知键 `KeyError`（宁崩不漏）」是同一条纪律。

    本条用 `nodes` 那条路进不去（它恒两句，`node_sign_key`/`node_house_key` 永不返回空），
    所以改走 `axes`：传 `axes=[]` 即命中「收不到键且不在 none 表」——`axis` 段在真盘上恒两句，
    空 `axes` 因此是编程错误而不是「这一盘没有轴」。
    """
    # 与上面那条同一条纪律的第二个实例：本文件不在顶部 import `build_plain`，理由逐字见那条的注释。
    from app.engines.western import build_plain

    chart = _greenwich_chart()
    with pytest.raises(ValueError, match="west 段 'axis' 收不到任何键"):
        build_plain(
            planets=chart.planets, axes=[], aspects=chart.aspects, nodes=chart.nodes,
            element_balance=chart.element_balance, modality_balance=chart.modality_balance,
        )


def test_the_balance_section_keeps_the_declared_element_then_modality_order() -> None:
    """`balance` 段的键序：先四个元素（按引擎字面量序）、再三个形态（同样按字面量序）。

    为什么这条要单独钉：行数测只数个数，改字面量的**顺序**不红；逐字节比对本可以抓，
    但那会把 542 条之外的又一份手抄引进 golden。`element_balance` 与 `modality_balance`
    都是 `compute_western_chart` 里的 dict **字面量**（`app/engines/western.py:330-331`），
    插入序在 3.7+ 有保证，所以顺序稳定——但它是稳定地透传字面量序，改字面量会**静默**改掉
    用户在页面上看到的先后。期望值按字面量逐字写出而不是按 `set` 比较，就是为了让改序变红。
    """
    chart = _greenwich_chart()
    lines = chart.plain[7].text.split("\n")[1:]
    fired = {
        element_key(name) for name, count in chart.element_balance.items() if count > 0
    } | {
        modality_key(name) for name, count in chart.modality_balance.items() if count > 0
    }
    # 按字面量序逐字列出，而不是按 set：set 会把顺序这一半判据吃掉，而改序正是本条要抓的。
    expected = [
        key
        for key in (
            [element_key(name) for name in ("fire", "earth", "air", "water")]
            + [modality_key(name) for name in ("cardinal", "fixed", "mutable")]
        )
        if key in fired
    ]
    assert len(lines) == len(expected)
    for line, key in zip(lines, expected, strict=True):
        assert WESTERN.entries[key] == line


def test_the_provenance_note_is_the_r50_declaration_verbatim() -> None:
    """用户可见的那句「这些中文从哪来」逐字钉：改写它要走裁定，不是顺手编辑。

    与上一条本地门的分工是「逐字 vs 判据」：本地门管三个诚实要点不许丢，本条管这句在响应里
    **就是这一句**。整串从 `content` 取而不是在这里重抄一遍——重抄就是第二份手抄（偏差 6/16
    算过的同一笔债），取源对象仍然能抓住「装配器填了别的串」。
    """
    chart = _greenwich_chart()
    assert chart.provenance.note == WESTERN_PLAIN_NOTE


def test_the_provenance_tables_are_the_three_plain_modules_in_order() -> None:
    """三行、次序、每行 `version == CONTENT_VERSION`：出处面板印的就是这三样。"""
    chart = _greenwich_chart()
    assert [row.name for row in chart.provenance.tables] == [
        "western_plain", "western_plain_placement", "western_plain_aspect",
    ]
    for row in chart.provenance.tables:
        assert row.version == CONTENT_VERSION, row.name
        assert row.source == WESTERN_PLAIN_SOURCE, row.name


def test_the_retrograde_none_opener_is_reachable_from_a_real_chart() -> None:
    """偏差 30 的补：`retrograde_none` 这句开篇句必须真被发出去，不是没人读的存货。

    `WESTERN_NONE_BRANCHES` 有两个键（偏差 5），但两条空态分支的**可达性**以前不对称：
    `aspect_none` 被 `test_an_empty_aspect_list_fires_the_none_opener_and_nothing_else` 用
    `aspects=[]` 的构造输入钉住，而 `retrograde_none` 走的是**真盘**——2001-01-27 14:00
    那盘零逆行（Plan F 地基表第二行：逆行 0 颗 ⇒ 57 句 / 65 行）。零颗逆行是真盘事实，
    所以今天不能用构造输入去代替真盘：构造输入证明的是「装配器能处理空」，真盘证明的是
    「真存在这样一盘」。

    本条钉两件事，缺一不可：
    ①**它真被发出去**——那条盘的第 4 段（逆行诸星）逐字节等于 `retrograde_none` 那句，
       不是别的什么（变异：把 `WESTERN_NONE_BRANCHES["retrograde"]` 换成任何一句别的话，
       本条红）；
    ②**它没有变成死字**——把这句改成一段没人会读到的存货（例如把 `retrograde_none`
       的值改掉）同样红。改动前本条不存在时，上面那个变异得到 **1437 passed / 0 failed**
       （控制器 2026-10-06 实测，`:golden 31 + :工厂 1406`），即全仓没有任何一条测会红——
       这就是「没有测的空态分支」的确切形状。
    """
    chart = compute_western_chart(
        birth_date=date(2001, 1, 27),
        birth_time=time(14, 0),
        latitude=51.5,
        longitude=-0.13,
        utc_offset_hours=0.0,
    )
    assert [planet.name for planet in chart.planets if planet.retrograde] == []
    retrograde_section = chart.plain[3]
    assert retrograde_section.title == WESTERN_SECTION_TITLES["retrograde"]
    assert retrograde_section.text == WESTERN.openers["retrograde_none"]
    # 这条盘顺带走另一个真盘空态：cardinal 计数为 0，所以「元素与形态」段只有
    # 元素三行 + 形态两行，少一个形态键。写在这里是因为它同样是「真盘上的空」而不是构造出来的空。
    assert chart.modality_balance["cardinal"] == 0
