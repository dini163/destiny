"""六维详批是映射函数的输出，不是自由发挥的文案：
每条判语可回溯到命中因子，每个分值可回溯到账本求和。"""

from datetime import date, time

import pytest

from app.content.bazi_dimensions import (
    DIMENSION_BASE, DIMENSION_ORDER, DIMENSION_RULES, DIMENSION_RULE_COUNT, dim_rule,
)
from app.engines.bazi import compute_bazi_chart
from app.engines.bazi_interpret import interpret_chart, ten_god_strength
from app.engines.bazi_rules import derive_branch_groups, derive_relations, derive_shensha
from app.engines.bazi_strength import assess_strength, detect_geju, element_weight_scores
from app.engines.bazi_yongshen import select_yongshen
from app.schemas.common import Gender
from app.schemas.scoring import MODEL_PARAM_SOURCE

CHART = compute_bazi_chart(  # 基准命 A：戊辰 甲寅 庚子 丁亥
    birth_date=date(1988, 2, 15), birth_time=time(23, 30),
    longitude=104.1, gender=Gender.MALE, apply_true_solar_time=True,
)
# `BaziChart` 不回显性别（性别属请求，Task 10 亦未把它列入响应字段），六维要它就得自己带上。
GENDER = Gender.MALE


def _interpretation():
    pillars = CHART.pillars
    strength = assess_strength(pillars)
    return interpret_chart(
        pillars, gender=GENDER, strength=strength, geju=detect_geju(pillars),
        yongshen=select_yongshen(
            level=strength.level, day_master_element="金", month_zhi="寅",
            element_scores=element_weight_scores(pillars),
        ),
        shensha=derive_shensha(pillars, day_master=CHART.day_master),
        relations=derive_relations(pillars),
        branch_groups=derive_branch_groups(pillars),
    )


def _reading(dimension: str):
    return next(r for r in _interpretation().six_dimensions if r.dimension == dimension)


# 十神分力（= 基准命 A 的五行加权去掉日主本身）：
#   官杀 火 1.30（丁透 1.0 + 寅丙 0.3）  印 土 1.70  财 木 2.20
#   食伤 水 1.70                          比劫 金 0.00（庚是日主，不计比劫）
# A 身弱、喜{土,金}、忌{木,水,火}、偏财格成格；神煞含 太极/文昌/将星/空亡，无天乙、无咸池、无六害。
EXPECTED = {
    "事业": (["career.officer.present", "career.officer.unfavourable",
              "career.officer.restrained", "career.structure.success",
              "career.star.jiangxing", "career.star.wenchang",
              "career.body.weak-under-officer"], 66.0, "顺"),
    "财运": (["wealth.star.present", "wealth.body.overloaded", "wealth.source.output",
              "wealth.guarded.officer"], 58.0, "平"),
    "婚姻": (["marriage.star.present", "marriage.palace.intact",
              "marriage.palace.bound"], 73.0, "顺"),
    "健康": (["health.void.branch", "health.flow.unobstructed"], 52.0, "平"),
    "学业": (["study.seal.present", "study.seal.favourable", "study.output.present",
              "study.wenchang"], 86.0, "顺"),
    "人际": (["social.noble.taiji", "social.officer.moderate"], 60.0, "平"),
}
BASE_RULE = {"事业": "career.base", "财运": "wealth.base", "婚姻": "marriage.base",
             "健康": "health.base", "学业": "study.base", "人际": "social.base"}


def test_six_dimensions_in_prd_order() -> None:
    assert [r.dimension for r in _interpretation().six_dimensions] == list(DIMENSION_ORDER)
    assert DIMENSION_ORDER == ("事业", "财运", "婚姻", "健康", "学业", "人际")
    assert DIMENSION_RULE_COUNT == 39
    assert DIMENSION_BASE == 50.0
    assert {k: len(v) for k, v in DIMENSION_RULES.items()} == {
        "事业": 8, "财运": 7, "婚姻": 7, "健康": 6, "学业": 5, "人际": 6,
    }


@pytest.mark.parametrize("dimension", DIMENSION_ORDER)
def test_every_dimension_score_carries_a_ledger(dimension: str) -> None:
    reading = _reading(dimension)
    assert reading.score.factors[0].rule == BASE_RULE[dimension]
    assert reading.score.factors[0].delta == DIMENSION_BASE
    assert sum(f.delta for f in reading.score.factors) == pytest.approx(reading.score.value)


@pytest.mark.parametrize("dimension", DIMENSION_ORDER)
def test_narrative_is_exactly_the_fired_rules_readings(dimension: str) -> None:
    """文案零现编：narrative 逐字等于命中因子的 reading 拼接，标签同源于同一命中集。"""
    reading = _reading(dimension)
    keys = [f.rule for f in reading.score.factors[1:]]
    assert keys == EXPECTED[dimension][0]
    assert reading.narrative == "；".join(dim_rule(k).reading for k in keys) + "。"
    assert reading.strengths == [dim_rule(k).label for k in keys if dim_rule(k).delta > 0]
    assert reading.cautions == [dim_rule(k).label for k in keys if dim_rule(k).delta < 0]
    assert (reading.score.value, reading.score.tier) == EXPECTED[dimension][1:]


def test_mutually_exclusive_rules_never_both_fire() -> None:
    """成对互斥：官杀之火是 A 的忌神 → 只记 unfavourable；A 日支无冲破 → 只记 intact。"""
    career = [f.rule for f in _reading("事业").score.factors]
    assert "career.officer.favourable" not in career
    assert "career.officer.unfavourable" in career
    marriage = [f.rule for f in _reading("婚姻").score.factors]
    assert "marriage.palace.intact" in marriage
    assert "marriage.palace.clashed" not in marriage
    assert ten_god_strength(CHART.pillars)["正官"] == 1.0
    assert ten_god_strength(CHART.pillars)["偏印"] == pytest.approx(1.7)
    assert ten_god_strength(CHART.pillars)["比肩"] == 0.0
    assert sum(ten_god_strength(CHART.pillars).values()) == pytest.approx(6.9)


def test_every_rule_reading_is_a_single_citable_clause() -> None:
    for rules in DIMENSION_RULES.values():
        for rule in rules:
            assert "。" not in rule.reading and "；" not in rule.reading, rule.key
            assert "《" in rule.reading or "本系统" in rule.reading, rule.key
            assert rule.label and -12.0 <= rule.delta <= 12.0


def test_summary_only_restates_tiers() -> None:
    result = _interpretation()
    assert result.summary == "、".join(
        f"{r.dimension}{r.score.tier}" for r in result.six_dimensions
    )
    assert _reading("事业").source == MODEL_PARAM_SOURCE
