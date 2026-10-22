"""Golden tests for the 西洋合盘 (synastry / composite) engine.

Reference pair: two people born at Greenwich (51.4769N, 0.0005E), UT offset 0, Placidus
houses, Moshier ephemeris (no data files):

* Person A — 1990-06-15 08:30 → Sun Gemini (83.99°), ASC Leo.
* Person B — 1992-11-20 18:45 → Sun Scorpio (238.71°), ASC Cancer.

Composite longitudes are the shorter-arc midpoints of the two natal longitudes and are
checked against that arithmetic directly (composite Sun = midpoint of 83.99 and 238.71
= 161.35). The score is a ledger: ``Σ factors[].delta == value`` and the base leads. The
anchors here are hand-derivable arithmetic, not engine read-backs:

* **中点** — `_midpoint` is pure modular arithmetic; the wrap-through-0° case and the
  diametric (exactly 180° apart) tie-break are pinned below with the reason for the choice.
* **相位表** — `synastry_aspects` is monotonic in orb and free of duplicate
  `(point_a, point_b, type)` triples; its per-type orb ceiling is the same shared
  `ASPECTS` table (`app/engines/western.py:60-66`) the natal and transit tables use, and the
  inclusive `<=` boundary is forced at the 8.0 conjunction limit. Cross-table agreement is
  *not* proved here — it lives in
  `tests/golden/test_western_golden.py::test_aspect_orb_inclusion_is_identical_across_the_three_tables`.
* **对称性** — swapping the two people leaves the (unordered) aspect set and the score value
  unchanged; `counted` is decided by whether *both* endpoints are personal points, not by
  which side is A.
* **账本** — only `counted` rows enter the ledger; a non-counted aspect's rule is absent.
* **白话层**（多系统白话 spec §6）— 逐行白话必须是「受控 frame + 两端受控点义」的填槽结果，
  总论只重排命中的核心轴；四档收尾句的键集合等于 `SYNASTRY_TIERS` 的档名。

Recount this file's tests: `cd backend && PYTHONIOENCODING=utf-8
.venv/Scripts/python.exe -m pytest tests/golden/test_synastry_golden.py -v`.
"""

from datetime import date, time

import pytest
from fastapi.testclient import TestClient

from app.content import synastry_plain
from app.content.synastry import SYNASTRY_TIERS
from app.core.provenance import MODEL_PARAM_SOURCE
from app.engines.plain_compose import compose_template, reading
from app.engines.plain_corpora import PLAIN_CORPORA, SYNASTRY
from app.engines.synastry import (
    _AXIS_ZH,
    _midpoint,
    _synastry_aspects,
    compute_synastry,
    synastry_plain_summary,
)
from app.engines.western import ASPECTS
from app.schemas.synastry import SynastryPerson
from tests.plain_wording import VERDICT_TOKENS

#: Conjunction's maximum orb, shared across the three aspect tables (`western.py:61`).
#: Recount: `python -c "from app.engines.western import ASPECTS; print(ASPECTS)"`.
CONJUNCTION_ORB = next(orb for name, _g, _a, orb in ASPECTS if name == "conjunction")

# 「个人点」六名集合的 external oracle 以字面量住在 `test_only_personal_point_pairs_are_counted`
# 里（Task 8A 修复轮 1 的裁定：不把它换成模块常量，因为那要动既有测）。这里不再留第二份，
# 因为 F2 删掉了 swap 测里那段与既有测逐字重复的判定循环后，本文件已无人用它。

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


def test_verdict_card_carries_grade_stars_counts_and_advice() -> None:
    """结论卡片：档位词 = score.tier，星级 = 署名映射 SYNASTRY_STARS，points 复述计入相位数
    与核心羁绊数（账本事实），headline/advice 套框架句。"""
    from app.engines.synastry import SYNASTRY_STARS

    chart = _chart()
    card = chart.verdict
    assert card.grade == chart.score.tier == "中和可处"
    assert card.stars == SYNASTRY_STARS["中和可处"] == 3
    counted = [a for a in chart.synastry_aspects if a.counted]
    bonds = {tuple(sorted((a.point_a, a.point_b))) for a in chart.synastry_aspects if a.counted and a.core_bond}
    assert any(f"计入相位：{len(counted)} 条" == p for p in card.points)
    assert any(f"核心羁绊：{len(bonds)} 条" == p for p in card.points)
    assert "中和可处" in card.headline
    assert str(round(chart.score.value, 2)) in card.headline or "46.41" in card.headline
    assert card.advice


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


# ------------------------------------------------------- Step 1(a): 中点的纯模运算

def test_diametric_midpoint_walks_counterclockwise_from_a() -> None:
    """两点相差恰 180° 时无短弧，两个合法答案相差 180°；实现取「从 A 逆时针 +90°」这一支。

    `_midpoint`（`app/engines/synastry.py:95-98`）先算 `delta = (lon_b - lon_a) % 360`，
    恰好 180 时 `delta > 180` 为假，不减 360，于是结果 = `lon_a + 180/2 = lon_a + 90`。所以
    `_midpoint(0, 180) == 90`（A+90）、`_midpoint(180, 0) == 270`（仍是 A+90，A=180）。
    这是「按参数顺序定方向」的确定性取舍，不是几何唯一解——把这条写死，谁改了取法会在这里红。
    """
    assert _midpoint(0.0, 180.0) == pytest.approx(90.0)
    assert _midpoint(180.0, 0.0) == pytest.approx(270.0)
    assert _midpoint(350.0, 10.0) == pytest.approx(0.0)  # 短弧过 0°（已有锚的镜像）


# ------------------------------------------------------- Step 3: 相位表完备性与对称

def test_synastry_aspects_are_sorted_unique_and_within_their_orbs() -> None:
    """合盘相位列的独有条：`(point_a, point_b, type)` 三元组全表唯一 + 按类型不越共享上限。

    「orb 非降序」已由 `test_synastry_aspects_are_valid_and_sorted` 钉过，本条不重复；本条多出来
    的是三元组唯一性，以及把上限从写死的 8.0 换成按 `ASPECTS` 逐型收紧（六合 6.0、刑 7.0 在
    `app/engines/western.py:60-66`），那是强化而非重复。
    """
    limit_by_type = {name: orb for name, _g, _a, orb in ASPECTS}
    aspects = _chart().synastry_aspects
    triples = {(a.point_a, a.point_b, a.type) for a in aspects}
    assert len(triples) == len(aspects)
    for a in aspects:
        assert 0.0 <= a.orb <= limit_by_type[a.type], (a.point_a, a.point_b, a.type)


def test_synastry_aspect_orb_boundary_is_inclusive_at_the_shared_limit() -> None:
    """合盘表这一侧：构造 7.9/8.0 计入、8.1 剔除，只证明 `_synastry_aspects` 用 `orb <= orb_limit`。

    `_synastry_aspects` 迭同一份 `ASPECTS`、同一句比较（`app/engines/synastry.py:175-177`），
    但本条看不到另外两张表——「三表同口径」由跨表关系测
    `tests/golden/test_western_golden.py::test_aspect_orb_inclusion_is_identical_across_the_three_tables`
    一次喂三张表来证（本命、行运各自的姊妹条同理，也只钉自己那一张）。8.0 是合相上限
    （`CONJUNCTION_ORB`，`app/engines/western.py:61`）。
    """
    assert CONJUNCTION_ORB == 8.0
    points = lambda lon: [("Sun", "太阳", "☉", lon)]  # noqa: E731 — 仅构造单点输入
    assert [a.orb for a in _synastry_aspects(points(0.0), points(7.9))] == [7.9]
    assert [a.orb for a in _synastry_aspects(points(0.0), points(8.0))] == [8.0]
    assert _synastry_aspects(points(0.0), points(8.1)) == []


def test_swapping_the_two_people_leaves_the_aspect_set_and_score_unchanged() -> None:
    """交换 A/B 后相位「集合」相等（无序对 + 类型 + orb）、score.value 不变、counted 相位照样对得上。

    相位是两两几何关系，人对调只交换 point_a/point_b 的角色，不改变 orb；score 只由 counted 条目
    加权——「counted 取决于两端是否个人点」这条判据本身已由 `test_only_personal_point_pairs_are_counted`
    钉住，本条不重复那段循环，只证它在交换下不变。
    """
    swapped = compute_synastry(
        person_a=_person(date(1992, 11, 20), time(18, 45), "B"),
        person_b=_person(date(1990, 6, 15), time(8, 30), "A"),
        house_system="P",
        ephemeris_path=None,
    )

    def signature(chart) -> set[tuple[tuple[str, str], str, float]]:
        return {
            (tuple(sorted((a.point_a, a.point_b))), a.type, round(a.orb, 2))
            for a in chart.synastry_aspects
        }

    original = _chart()
    assert signature(original) == signature(swapped)
    assert original.score.value == pytest.approx(swapped.score.value, abs=1e-9)
    assert {round(a.orb, 2) for a in original.synastry_aspects if a.counted} == {
        round(a.orb, 2) for a in swapped.synastry_aspects if a.counted
    }


def test_only_counted_aspects_enter_the_score_ledger() -> None:
    """账本逐条对相位：非 counted 的相位其 rule 绝不出现在 factors；counted 的 rule 一条不缺。

    `_synastry_score` 跳过 `counted=False`（`app/engines/synastry.py:205-207`），每条 counted 相位生成
    一行 `synastry.<a>.<b>.<type>`。所以 factors（除 base）的 rule 集合恰等于 counted rule 集合，
    且所有 non-counted 的 rule 都在其外——这是一条真正的「进账门」，不靠数数相等蒙混。
    """
    chart = _chart()
    rules = {f.rule for f in chart.score.factors}
    assert "synastry.base" in rules
    counted_rules = {f"synastry.{a.point_a}.{a.point_b}.{a.type}" for a in chart.synastry_aspects if a.counted}
    not_counted_rules = {f"synastry.{a.point_a}.{a.point_b}.{a.type}" for a in chart.synastry_aspects if not a.counted}
    non_base_rules = {r for r in rules if r != "synastry.base"}
    assert non_base_rules == counted_rules
    assert not (non_base_rules & not_counted_rules)


# ------------------------------------------------------- 白话层（多系统白话 spec §6）

def test_synastry_corpus_is_the_one_the_registry_holds() -> None:
    """工厂按 `PLAIN_CORPORA.values()` 参数化跑表，看不见键覆盖：两行同 `system` 时
    Python 静默留最后一行，前一张表就此掉出闸外而两条形状断言照样绿。由消费方自证在场。"""
    assert PLAIN_CORPORA["synastry"] is SYNASTRY


def test_point_slots_cover_exactly_the_axes_the_engine_reads() -> None:
    """`_synastry_universe()` 里 ASC/MC 是字面量（不能 import 本模块，那是循环），本条就是它的对账。

    有人给合盘加第三根轴时，`_chart_points` 会多出点名、逐行白话那条测试当场 KeyError；
    本条先一步说明真正的原因在两张表的名单不同，而不是白话表写错了句。
    """
    assert set(_AXIS_ZH) == {"ASC", "MC"}


def test_every_aspect_carries_a_plain_line_made_of_two_slots_and_a_frame() -> None:
    """56 行逐条对拍：每行白话 = 受控 frame + 两端受控点义，一个字的现编都没有。"""
    chart = _chart()
    assert len(chart.synastry_aspects) == 56
    for aspect in chart.synastry_aspects:
        assert aspect.plain == compose_template(
            reading(SYNASTRY, synastry_plain.aspect_frame_key(aspect.type)),
            {
                "a": reading(SYNASTRY, synastry_plain.point_key(aspect.point_a)),
                "b": reading(SYNASTRY, synastry_plain.point_key(aspect.point_b)),
            },
        )


def test_aspect_frames_carry_no_verdict_words() -> None:
    """G2 的机检半边：框架句里不许出现结论词，判断只能来自被填进来的点义与档位收尾句。

    口径唯一正主在 `tests/plain_wording.py::VERDICT_TOKENS`（四字表），本条直接扫它。
    复测：`cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "
    from app.content.synastry_plain import SYNASTRY_ASPECT_FRAMES as F
    print([(w, [k for k, t in F.items() if w in t]) for w in '吉凶宜忌'])"` → 四个空列表
    （'吉凶宜忌' 即 `VERDICT_TOKENS` 那四字，复测命令不引 tests 侧，故留字面量）。
    """
    for key, frame in synastry_plain.SYNASTRY_ASPECT_FRAMES.items():
        for word in VERDICT_TOKENS:
            assert word not in frame, (key, word)


def test_closers_cover_exactly_the_tiers_the_content_table_prints() -> None:
    """G3（spec §5 规则 6）：收尾句键集合 == `SYNASTRY_TIERS` 的档名（裁定 R25 由本系统自钉）。

    现账复测：`cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "
    from app.content.synastry import SYNASTRY_TIERS
    from app.content.synastry_plain import SYNASTRY_TIER_CLOSERS
    print({label for _, label in SYNASTRY_TIERS} == set(SYNASTRY_TIER_CLOSERS))"` → True。
    """
    assert {label for _, label in SYNASTRY_TIERS} == set(SYNASTRY.closers)


def test_plain_summary_relists_the_two_hit_core_axes_banded() -> None:
    """真实盘总论逐字节钉住（2026-09-30 由本文件那对 A/B 实算，56 行里命中两条核心轴）。

    命中的两条都 `counted`（`core_bond` 的行实测是 月金 六合 与 金火 刑，各一，无外行星端点），
    所以 `synastry_plain_summary` 里那道 `and aspect.counted` 对本盘是空操作——本条因此同时钉住
    「过滤条件改口径而输出不动」这件事。

    复测（2026-09-30 改写：旧写法 `_chart()` 未定义就 `NameError`，现在整条命令自给自足）：
    `cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "import sys;sys.path.insert(0,'tests/golden');from test_synastry_golden import _chart;from app.engines.synastry import synastry_plain_summary;print(synastry_plain_summary(_chart().synastry_aspects,'中和可处'))"`
    """
    chart = _chart()
    assert chart.score.tier == "中和可处"
    assert chart.plain_summary == "\n".join(
        [
            "把账本里命中的核心羁绊合起来看，你这段关系最要紧的几条轴各落在顺的一侧还是费劲的一侧，下面按两侧重排一遍。",
            "月金这一对是情绪与喜好叠在一处，你在这条轴上容易觉得被照顾，也容易把照顾与心动放进同一个口袋，它们同在一格里却是两件事。",
            "金火这一对管的是被吸引与往前冲的那股劲，你在这条轴上感受直接，它给的是热度，把热度认成什么，是这条轴不管的事。",
            "你这一份相契度落在中和可处，表的措辞在这一档是平的，顺与费劲两边都读得进去，轻重由那几条相位自己说，不由这个档位替你定。",
        ]
    )


def test_zero_counted_core_bond_summary_does_not_promise_a_reranking() -> None:
    """一条核心羁绊都没计入时，开篇句必须是「不逐条重排」那一条（终审 C1）。

    输入取 `_chart()` 真盘里那些 `not (core_bond and counted)` 的行：这条测的是装配器在空 `items`
    上选哪条开篇句，与星历无关，但绝不用手搓的假 `SynastryAspect`（AGENTS.md §9）。
    """
    rows = [a for a in _chart().synastry_aspects if not (a.core_bond and a.counted)]
    assert rows, "参考盘连一条不计入的行都没有，这条测就成了空转"
    lines = synastry_plain_summary(rows, "和合互补").split("\n")
    assert lines == [
        synastry_plain.SYNASTRY_SUMMARY_NONE_OPENER,
        synastry_plain.SYNASTRY_TIER_CLOSERS["和合互补"],
    ]


def test_counted_core_bonds_still_lead_with_the_reranking_opener() -> None:
    """常见盘的三行形状（开篇 + 羁绊 + 档位）不许被 C1 改动。"""
    rows = [a for a in _chart().synastry_aspects if a.core_bond and a.counted]
    assert rows, "参考盘没有计入的核心羁绊，那 C1 的那条支路才是常态，本测的口径要重定"
    lines = synastry_plain_summary(rows, "和合互补").split("\n")
    assert lines[0] == synastry_plain.SYNASTRY_SUMMARY_OPENER
    assert lines[-1] == synastry_plain.SYNASTRY_TIER_CLOSERS["和合互补"]
    assert len(lines) > 2
