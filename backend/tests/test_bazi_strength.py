"""Three-factor day-master strength: every number is recomputable from the ledger.

Expected values are derived by hand from spec §6.1/§6.4 against the reference
chart 戊辰 甲寅 庚子 丁亥; the hidden-stem tables are lunar-python's, so
辰=戊乙癸, 寅=甲丙戊, 子=癸, 亥=壬甲.
"""

from datetime import date, time

import pytest

from app.engines.bazi import compute_bazi_chart
from app.engines.bazi_strength import (
    FACTOR_WEIGHTS,
    assess_strength,
    element_weight_scores,
    fuyin_choices,
    hidden_stem_weight,
)
from app.schemas.common import Gender

BASE = compute_bazi_chart(
    birth_date=date(1988, 2, 15),
    birth_time=time(23, 30),
    longitude=104.1,
    gender=Gender.MALE,
    apply_true_solar_time=True,
)


def _factor(rule_prefix: str):
    assessment = assess_strength(BASE.pillars)
    return next(f for f in assessment.score.factors if f.rule.startswith(rule_prefix))


def test_weighted_element_tally_of_reference_chart() -> None:
    """木2.20 土1.70 水1.70 火1.30 金1.00 over the 4 stems + 9 hidden stems."""
    assert element_weight_scores(BASE.pillars) == {
        "木": pytest.approx(2.2),
        "火": pytest.approx(1.3),
        "土": pytest.approx(1.7),
        "金": pytest.approx(1.0),
        "水": pytest.approx(1.7),
    }
    assert sum(element_weight_scores(BASE.pillars).values()) == pytest.approx(7.9)


def test_single_hidden_stem_weighs_a_full_point() -> None:
    assert hidden_stem_weight(0, 1) == 1.0
    assert hidden_stem_weight(0, 3) == 0.6
    assert hidden_stem_weight(2, 3) == 0.1


def test_de_ling_is_qiu_30_for_geng_in_yin_month() -> None:
    """寅月木旺，金克木 → 我克者囚 = 30."""
    assert _factor("strength.deling").delta == pytest.approx(0.4 * 30.0)


def test_de_di_normalises_over_the_full_hidden_weight() -> None:
    """通根占比：支持五行 辰戊0.6 + 寅戊0.1 = 0.70；四支满分 辰1.0 + 寅1.0 + 子1.0 + 亥0.9 = 3.90。

    0.70/3.90*100 = 17.9487；账本记的是加权占比，不是每支 25 分的预算（spec §6.4 第 2 点）。
    """
    assert _factor("strength.dedi").delta == pytest.approx(0.4 * 17.9487, abs=0.01)


def test_de_shi_counts_only_year_month_hour_stems() -> None:
    """戊(偏印)命中，甲(偏财)/丁(正官)不命中 → 1/3*100 = 33.33."""
    assert _factor("strength.deshi").delta == pytest.approx(0.2 * 33.3333, abs=0.01)


def test_factor_scalars_are_the_unweighted_values_behind_the_ledger() -> None:
    """§6.6 学业维要读"得地"一项：标量与账本同源，读者不必再从 rule 字符串反解。"""
    assessment = assess_strength(BASE.pillars)
    assert assessment.deling == pytest.approx(30.0)
    assert assessment.dedi == pytest.approx(17.9487, abs=0.01)
    assert assessment.deshi == pytest.approx(33.3333, abs=0.01)
    for prefix, weight, value in (
        ("strength.deling", FACTOR_WEIGHTS[0], assessment.deling),
        ("strength.dedi", FACTOR_WEIGHTS[1], assessment.dedi),
        ("strength.deshi", FACTOR_WEIGHTS[2], assessment.deshi),
    ):
        assert _factor(prefix).delta == pytest.approx(weight * value, abs=0.01)


def test_strength_value_band_and_borderline() -> None:
    result = assess_strength(BASE.pillars)
    assert result.score.value == pytest.approx(25.85, abs=0.01)
    assert (result.level, result.label) == ("weak", "身弱")
    assert result.borderline is False


def test_ledger_reproduces_the_value() -> None:
    assessment = assess_strength(BASE.pillars)
    factors = assessment.score.factors
    assert factors[0].rule == "strength.base"
    assert sum(f.delta for f in factors) == pytest.approx(assessment.score.value, abs=0.05)


def test_fuyin_orders_chosen_elements_by_weight() -> None:
    """身弱庚金 → 喜印(土)与比劫(金)；加权分高者排前，输出次序可核对。"""
    scores = element_weight_scores(BASE.pillars)
    favourable, unfavourable = fuyin_choices("weak", "金", scores)
    assert favourable == ["土", "金"]
    assert unfavourable == ["木", "水", "火"]
    assert scores["土"] > scores["金"]
    assert unfavourable == sorted(unfavourable, key=lambda e: -scores[e])
