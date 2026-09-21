"""Pydantic schemas for the BaZi (八字) natal-chart system.

Field names are snake_case end-to-end (JSON contract mirrors these models) so
the frontend can consume responses without a mapping layer.
"""

from datetime import date

from pydantic import BaseModel, Field

from app.schemas.bazi_breakdown import DayunDetail, Provenance, TenGodReading
from app.schemas.bazi_interpret import BaziInterpretation
from app.schemas.bazi_rules import BranchGroup, RelationPair, ShenShaEntry
from app.schemas.bazi_strength import GeJu, HiddenStemWeight, Yongshen
from app.schemas.common import BirthInput, Gender
from app.schemas.scoring import ScoreValue


class BaziNatalRequest(BirthInput):
    """Input for a BaZi natal chart.

    Extends the shared :class:`BirthInput` and makes ``gender`` mandatory, since
    the direction of the luck pillars (大运顺逆) depends on it.
    """

    gender: Gender = Field(description="Required: determines dayun (luck pillar) direction.")
    apply_true_solar_time: bool = Field(
        default=True,
        description="Correct the standard-time input to True Solar Time before charting (PRD 7).",
    )
    name: str | None = Field(
        default=None, max_length=40, description="命主称谓，仅回显，不参与任何计算。"
    )
    reference_date: date | None = Field(
        default=None,
        description="判定当前大运的截止日；缺省由引擎取服务器当日，并在响应 "
        "provenance.reference_date 里回显，因此响应自身即可复现。",
    )


class BaziPillar(BaseModel):
    """One of the four pillars (year / month / day / hour)."""

    position: str = Field(description="year | month | day | hour")
    label: str = Field(description="Chinese pillar label, e.g. 年柱")
    ganzhi: str = Field(description="Full pillar, e.g. 戊辰")
    gan: str = Field(description="Heavenly stem, e.g. 戊")
    zhi: str = Field(description="Earthly branch, e.g. 辰")
    gan_element: str = Field(description="Five-element of the stem")
    zhi_element: str = Field(description="Five-element of the branch")
    nayin: str = Field(description="Nayin (纳音), e.g. 大林木")
    hidden_stems: list[str] = Field(description="Branch hidden stems (藏干)")
    hidden_stem_elements: list[str] = Field(description="Five-elements of the hidden stems")
    shishen_gan: str = Field(description="Ten-god of the stem relative to the day master")
    shishen_zhi: list[str] = Field(description="Ten-gods of the hidden stems")
    di_shi: str = Field(description="Twelve life-stages (地势/十二长生)")
    xun: str = Field(description="Sexagenary decade (旬)")
    xun_kong: str = Field(description="Void branches of the decade (空亡)")


class WuxingScore(BaseModel):
    """Five-element presence: a headcount and a weighted strength score."""

    element: str
    count: int = Field(
        ge=0, le=8, description="八个主字（四干四支）中该五行的个数；不含藏干。"
    )
    score: float = Field(
        ge=0,
        description="含藏干的加权合计（天干 1.0、本中余 0.6/0.3/0.1，单藏干支本气 1.0）。"
        "这组权重是本地模型参数、非古籍赋分（spec §6.1）；它是分布条的长度，不是吉凶分数，"
        "日主强弱的可核对账本在 DayMasterAnalysis.strength。",
    )


class DayMasterAnalysis(BaseModel):
    """Deterministic day-master strength and useful-god analysis."""

    day_master: str = Field(description="Day stem, e.g. 庚")
    day_master_element: str = Field(description="Element of the day master, e.g. 金")
    strength: ScoreValue = Field(
        description="得令/得地/得势三因子账本（spec §6.4）；Σ factors[].delta == value。"
    )
    borderline: bool = Field(
        description="距 65/45 分界不足 3 分：档位可信但命局偏中和，UI 须明示临界。"
    )
    level: str = Field(description="weak | balanced | strong")
    label: str = Field(description="Chinese label, e.g. 身弱")
    favorable_elements: list[str] = Field(
        description="喜用神：三法合并结果，镜像 `yongshen.favorable_elements`（spec §6.5）。"
    )
    unfavorable_elements: list[str] = Field(
        description="忌神：三法合并结果，镜像 `yongshen.unfavorable_elements`。"
    )
    summary: str = Field(description="Concise human-readable restatement of the analysis")


class DayunStep(BaseModel):
    """A single luck-pillar (大运) step; index 0 is the pre-luck childhood span."""

    index: int
    ganzhi: str = Field(description="Luck pillar, empty for the childhood span")
    start_age: int
    end_age: int
    start_year: int
    end_year: int
    xun: str
    xun_kong: str
    is_current: bool = False


class LiunianYear(BaseModel):
    """A single annual-fortune (流年) year within the current luck pillar."""

    year: int
    age: int
    ganzhi: str


class BaziChart(BaseModel):
    """Complete BaZi natal chart produced by :mod:`app.engines.bazi`."""

    # Provenance / input echo
    name: str | None = Field(default=None, description="命主称谓，仅回显，不参与任何计算。")
    standard_datetime: str = Field(description="Civil standard-time input, e.g. 1988-02-15 23:30")
    calendar: str = Field(description="Calendar of the supplied date: solar | lunar")
    true_solar_time: str | None = Field(description="True Solar Time used for charting, if applied")
    tst_applied: bool = Field(description="Whether a True Solar Time correction was applied")
    tst_offset_minutes: float | None = Field(description="TST minus standard time, in minutes")
    longitude: float = Field(description="Longitude used for the TST correction")
    lunar_date: str = Field(description="Lunar-calendar date, e.g. 一九八七年腊月廿八")

    # Chart core
    four_pillars: str = Field(description="Space-joined four pillars, e.g. 戊辰 甲寅 庚子 丁亥")
    pillars: list[BaziPillar] = Field(description="Year, month, day and hour pillars in order")
    zodiac: str = Field(description="Birth zodiac by Start-of-Spring (consistent with year branch)")
    day_master: str
    day_master_element: str
    ming_gong: str = Field(description="Life palace (命宫)")
    ming_gong_nayin: str
    tai_yuan: str = Field(description="Conception palace (胎元)")
    tai_yuan_nayin: str

    # Five elements + analysis
    wuxing: list[WuxingScore] = Field(description="Five-element scores in 木火土金水 order")
    missing_elements: list[str] = Field(
        description="主字与藏干皆无的五行（与 `wuxing.count` 口径不同：后者不含藏干）。"
    )
    analysis: DayMasterAnalysis

    # Luck cycles
    dayun_direction: str | None = Field(description="forward | backward (顺行/逆行), null without gender")
    dayun_start_solar: str | None = Field(description="Solar date the first luck pillar begins")
    dayun: list[DayunStep]
    current_liunian: list[LiunianYear] = Field(description="Annual fortunes within the current dayun")

    # Interpretation breakdown (spec §7)
    geju: GeJu | None = None
    yongshen: Yongshen | None = None
    shensha: list[ShenShaEntry] = Field(default_factory=list)
    ten_god_readings: list[TenGodReading] = Field(default_factory=list)
    relations: list[RelationPair] = Field(default_factory=list)
    branch_groups: list[BranchGroup] = Field(default_factory=list)
    hidden_stem_ledger: list[HiddenStemWeight] = Field(default_factory=list)
    dayun_current: DayunDetail | None = None
    interpretation: BaziInterpretation | None = None
    provenance: Provenance | None = None

    engine: str = Field(default="lunar-python", description="Authoritative computation engine")
