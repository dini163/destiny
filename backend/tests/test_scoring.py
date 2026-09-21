"""The score ledger is the project's no-mock contract: every number is explainable."""

import pytest

from app.schemas.scoring import MODEL_PARAM_SOURCE, ScoreFactor, ScoreValue, build_ledger


def test_ledger_value_is_base_plus_deltas() -> None:
    value = build_ledger(
        base=40.0,
        tier="中和",
        contributions=[
            ScoreFactor(rule="dedi.root.strength", label="通根力量", delta=12.0, source="模型参数"),
            ScoreFactor(rule="deshi.stem.count", label="天干生扶", delta=8.0, source="模型参数"),
        ],
    )
    assert value.value == pytest.approx(60.0)
    assert value.factors[0].delta == 40.0  # the base term is recorded first
    assert value.factors[0].rule.endswith(".base")


def test_ledger_clamps_to_range_and_records_the_clamp() -> None:
    value = build_ledger(
        base=90.0,
        tier="身强",
        contributions=[ScoreFactor(rule="x.y", label="x", delta=50.0, source=MODEL_PARAM_SOURCE)],
    )
    assert value.value == 100.0
    # 截断不是静默改数：账本里必须留下一行，Σ delta 才继续等于 value。
    assert [f.rule for f in value.factors] == ["score.base", "x.y", "score.clamped"]
    assert value.factors[-1].delta == -40.0
    assert sum(f.delta for f in value.factors) == value.value


def test_ledger_records_a_negative_clamp_too() -> None:
    value = build_ledger(
        base=10.0,
        tier="身弱",
        contributions=[ScoreFactor(rule="x.y", label="x", delta=-30.0, source=MODEL_PARAM_SOURCE)],
    )
    assert value.value == 0.0
    assert value.factors[-1].rule == "score.clamped"
    assert sum(f.delta for f in value.factors) == value.value


def test_ledger_rejects_negative_base() -> None:
    with pytest.raises(ValueError, match="base"):
        build_ledger(base=-1.0, tier="身弱", contributions=[])


def test_factors_must_carry_a_source() -> None:
    with pytest.raises(ValueError):
        ScoreFactor(rule="x", label="x", delta=1.0, source="   ")


def test_score_value_stays_inside_its_range() -> None:
    with pytest.raises(ValueError):
        ScoreValue(value=101.0, tier="身强", factors=[])


MODEL_BASE = "score.base"
