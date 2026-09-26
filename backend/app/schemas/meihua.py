"""Pydantic schemas for the 梅花易数 (Plum Blossom Numerology) system.

Field names are snake_case end-to-end. 梅花易数 differs from 六爻纳甲: it does not
dress lines with 纳甲/六亲/六神/世应. Instead it locates the 体卦 (body) and 用卦
(use) by the moving line, reads their 五行生克 as the primary verdict, weighs it by
卦气旺衰 (seasonal strength) and by the 互卦/变卦 tendency, and reports a transparent
吉凶指数 ledger. The three hexagrams (本/互/变) carry structure plus the classical
卦辞 only.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class MeihuaMethod(str, Enum):
    """How the hexagram is raised (起卦法)."""

    TIME = "time"       # 年月日时起卦 (from the lunar cast moment)
    NUMBER = "number"   # 报数起卦 (one to three reported numbers)


class MeihuaCastRequest(BaseModel):
    """Input for a 梅花易数 cast.

    ``numbers`` is required only for the ``number`` method: one to three positive
    integers (报数). ``cast_time`` defaults to the current moment and supplies the
    lunar year/month/day/hour numbers (time method) and the 时辰 (single-number
    method); it also fixes the 月令 for 卦气旺衰 in every method.
    """

    method: MeihuaMethod = Field(default=MeihuaMethod.TIME)
    numbers: list[int] | None = Field(
        default=None, description="Number method only: one to three positive integers (报数)."
    )
    question: str | None = Field(default=None, description="Optional question the divination addresses.")
    cast_time: datetime | None = Field(default=None, description="Cast moment; defaults to now.")


class MeihuaDerivation(BaseModel):
    """The transparent 起卦 arithmetic that produced the hexagram."""

    upper_number: int = Field(description="先天卦数 of the upper (外) trigram, 1-8.")
    lower_number: int = Field(description="先天卦数 of the lower (内) trigram, 1-8.")
    moving_position: int = Field(description="Moving-line position 1-6, bottom to top.")
    formula: str = Field(description="Human-readable derivation, e.g. (年7+月12+日28)÷8余… .")
    inputs: str = Field(description="The lunar/number inputs used, echoed for auditability.")


class MeihuaTrigram(BaseModel):
    """One trigram of a hexagram with its 五行 and 象."""

    key: str = Field(description="Trigram key, e.g. qian.")
    name_zh: str = Field(description="卦名, e.g. 乾.")
    symbol: str = Field(description="Unicode trigram glyph, e.g. ☰.")
    nature_zh: str = Field(description="象, e.g. 天.")
    element: str = Field(description="五行 of the trigram.")
    position: str = Field(description="lower | upper (内卦 / 外卦).")


class MeihuaHexagram(BaseModel):
    """Structural identity of a hexagram plus its classical 卦辞."""

    number: int = Field(description="King Wen sequence number 1-64.")
    name_zh: str = Field(description="Short name, e.g. 屯.")
    full_name_zh: str = Field(description="Trigram-encoded name, e.g. 水雷屯.")
    symbol: str = Field(description="Unicode hexagram glyph, e.g. ䷂.")
    lines: list[int] = Field(description="Six lines bottom-to-top, 1=yang 0=yin.")
    lower: MeihuaTrigram
    upper: MeihuaTrigram
    gua_ci: str = Field(description="卦辞 — the classical hexagram judgment.")


class TiYongParty(BaseModel):
    """The 体卦 or 用卦: its trigram, 万物类象 and 卦气旺衰 state."""

    role: str = Field(description="ti | yong (体 / 用).")
    trigram: MeihuaTrigram
    leixiang: str = Field(description="八卦万物类象 one-line summary (《说卦传》).")
    wangshuai: str = Field(description="旺相休囚死 state of this trigram's element under the 月令.")
    wangshuai_text: str = Field(description="Interpretation of the 旺衰 state.")


class TiYongVerdict(BaseModel):
    """The primary 体用生克 relation and its judgement."""

    relation: str = Field(description="Machine key: yong_sheng_ti | bi_he | ti_ke_yong | ti_sheng_yong | yong_ke_ti.")
    relation_zh: str = Field(description="用生体 / 体用比和 / 体克用 / 体生用 / 用克体.")
    verdict: str = Field(description="大吉 / 吉 / 小吉 / 小凶 / 大凶.")
    grade: int = Field(description="Ordinal rank, +2 (best) … −2 (worst).")
    text: str = Field(description="Classical-flavoured judgement of the relation.")


class WangshuaiInfo(BaseModel):
    """The 卦气 (seasonal strength) context derived from the 月令."""

    month_zhi: str = Field(description="月建地支 that fixes the season, e.g. 卯.")
    season_zh: str = Field(description="季节名, e.g. 仲春.")
    commanding_element: str = Field(description="当令五行 (月令), e.g. 木.")


class ScoreFactor(BaseModel):
    """One line of the 吉凶指数 ledger (shows the arithmetic, per project ethos)."""

    label: str
    detail: str
    delta: int = Field(description="Signed contribution to the 0-100 index.")


class MeihuaCast(BaseModel):
    """Complete 梅花易数 cast produced by :mod:`app.engines.meihua`."""

    # Provenance
    method: str = Field(description="time | number")
    question: str | None = Field(description="The question echoed back, if provided.")
    cast_time: str = Field(description="Cast moment used, e.g. 2024-05-15 10:30.")
    derivation: MeihuaDerivation = Field(description="The transparent 起卦 arithmetic.")

    # Hexagrams
    ben: MeihuaHexagram = Field(description="本卦 — the primary hexagram as raised.")
    hu: MeihuaHexagram = Field(description="互卦 — nuclear hexagram (lines 2-3-4 / 3-4-5), the 事之中段.")
    bian: MeihuaHexagram = Field(description="变卦 — after the moving line changes, the 事之归宿.")
    moving_position: int = Field(description="Moving-line position 1-6, bottom to top.")

    # 体用
    ti: TiYongParty = Field(description="体卦 — the trigram without the moving line (主 / 自己).")
    yong: TiYongParty = Field(description="用卦 — the trigram with the moving line (客 / 事).")
    tiyong: TiYongVerdict = Field(description="The 体用生克 primary verdict.")
    wangshuai: WangshuaiInfo = Field(description="卦气 context (月令).")

    # 互变 auxiliary tendencies
    hu_analysis: str = Field(description="互卦 two trigrams' 生克 toward the 体卦 (过程).")
    bian_analysis: str = Field(description="变卦 changed trigram's 生克 toward the 体卦 (结局).")

    # Ledger
    score: int = Field(description="吉凶指数 0-100 (higher = more favourable).")
    score_factors: list[ScoreFactor] = Field(description="The factors that produced the index.")
    verdict: str = Field(description="综合吉凶 verdict label.")
    summary: str = Field(description="综合断语 synthesising 体用/卦气/互变.")

    engine: str = Field(default="meihua-tiyong", description="Derivation engine name.")
