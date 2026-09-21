"""Score ledgers: every number the API returns must carry its own arithmetic.

This is the mechanical form of the project's no-mock rule. A score is never a
bare figure; it is a ``ScoreValue`` whose ``factors`` list starts with the base
term and continues with one ``ScoreFactor`` per rule that moved it, so

    value == Σ factor.delta over all factors

holds by construction (``build_ledger`` is the only place that arithmetic lives;
a clamp to 0-100 is recorded as its own ``score.clamped`` row rather than
silently dropped). A score without a ledger may not appear in a response or in
the UI.
"""

from pydantic import BaseModel, Field, field_validator

#: The one wording used when a figure comes from this system's own weighting
#: instead of a classic. Defined once so no module paraphrases it differently.
MODEL_PARAM_SOURCE = "模型参数（本系统加权，非古籍赋分）"


class ScoreFactor(BaseModel):
    """One line of a score's ledger: a rule, how much it moved, and where it comes from."""

    rule: str = Field(description="Machine-readable rule key, e.g. 'dedi.root.strength'.")
    label: str = Field(description="Short Chinese name, e.g. 通根力量.")
    delta: float = Field(description="Contribution; factors[0] carries the base term.")
    source: str = Field(
        description="Classical citation, or an explicit '模型参数' note. Never blank."
    )

    @field_validator("source")
    @classmethod
    def _source_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("every score factor needs a source")
        return value


class ScoreValue(BaseModel):
    """A clamped 0-100 score plus the ledger that produced it."""

    value: float = Field(ge=0, le=100)
    tier: str = Field(description="Chinese band label, e.g. 身强 / 中和 / 身弱.")
    factors: list[ScoreFactor]


def build_ledger(
    base: float,
    tier: str,
    contributions: list[ScoreFactor],
    base_rule: str = "score.base",
) -> ScoreValue:
    """Fold ``base`` and ``contributions`` into a self-explaining score."""
    if base < 0:
        raise ValueError("score base must not be negative")
    factors = [
        ScoreFactor(rule=base_rule, label="基准分", delta=base, source=MODEL_PARAM_SOURCE),
        *contributions,
    ]
    raw = sum(factor.delta for factor in factors)
    total = min(100.0, max(0.0, raw))
    if total != raw:
        # 截断本身是一行账，不然 Σ delta 与 value 分家，账本就失去可核对性。
        factors.append(
            ScoreFactor(
                rule="score.clamped",
                label="上下限截断",
                delta=total - raw,
                source=MODEL_PARAM_SOURCE,
            )
        )
    return ScoreValue(value=round(total, 2), tier=tier, factors=factors)
