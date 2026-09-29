"""流时的一天：请求、十二格简表、聚焦时辰明细、单日响应（spec §7.1/§7.3）。

一页 = 一个八字日的 12 格 + 至多一格的全明细。与流日矩阵同一条体积纪律：简表格
**不含 `reading`**（spec §2.5 的实测是一格详批 ≥ 13.1 KB，12 份全文不是"偏大"而是不可发）。
`hour_hits` 只含 `shi.` 行 —— 年/月/日三段在十二格之间逐字相同（决策 1），重复 12 遍是
纯体积，要看全账的读者有 `focused.score.factors`。

`null` 两处：`dayun_ganzhi`（童年段未起运，与流日同）、`focused`（未请求聚焦时辰）。
"""

from datetime import date

from pydantic import BaseModel, Field

from app.schemas.bazi import BaziNatalRequest, BaziPillar
from app.schemas.bazi_breakdown import Provenance
from app.schemas.bazi_liuri import AlmanacYiJi
from app.schemas.bazi_rules import BranchGroup, RelationPair, ShenShaEntry
from app.schemas.bazi_transit import TransitFired, TransitTenGod
from app.schemas.scoring import ScoreValue


class BaziLiushiRequest(BaziNatalRequest):
    """流时入参：命盘入参 + 两个可空件（哪一天、聚焦哪个时辰）。

    与 `BaziLiuriRequest` 同一条理由：日期/时辰合不合法是域错误，`model_validator` 会把
    它们包成 `validation_error` 而丢掉机器码。`solar_date` 缺省取 `reference_date`，
    "打开页面就是今天"不需要前端传东西；`focus_hour_zhi` 缺省即不聚焦。
    """

    solar_date: date | None = Field(default=None, description="八字日；缺省 = 参考日。")
    focus_hour_zhi: str | None = Field(
        default=None, description="地支单字（子丑寅卯辰巳午未申酉戌亥）；给出则该时辰升级为全明细。"
    )


class TransitHourHit(BaseModel):
    """一格上的时辰段命中：账本行的可读镜像，判语全文在聚焦卡。形状与 `TransitDayHit` 同构。"""

    key: str = Field(description="带 `shi.` 前缀的规则键。")
    label: str = Field(description="短名 +「（流时）」后缀。")
    family: str = Field(description="九族之一。")
    delta: float = Field(description="本行分值。")


class TransitHourCell(BaseModel):
    """十二格之一。钟面区间由库给（`getMinHm()/getMaxHm()`），前端不推算时辰边界。"""

    index: int = Field(ge=0, le=11, description="0 = 子时首格（当日 23:00），与 `HOUR_ZHI` 同序。")
    zhi: str = Field(description="时支单字。")
    ganzhi: str = Field(description="时柱，五鼠遁。")
    start_clock: str = Field(description="北京钟面起（HH:MM），23:00 那格起于前一日钟面。")
    end_clock: str = Field(description="北京钟面终；时辰划分不做真太阳时校正（决策 6）。")
    value: float = Field(ge=0, le=100, description="四段账本的 value。")
    tier: str = Field(description="顺 / 平 / 滞。")
    qi_strength: str = Field(description="日主临时支的十二长生，纯描述：纵轴只有 `value` 一把尺（决策 9）。")
    hour_hits: list[TransitHourHit] = Field(description="只含 `shi.` 行；时段一条未中为 []，此时本格分值等于日头分。")


class TransitHourDetail(TransitHourCell):
    """聚焦时辰 = 简表行 + 全部明细。继承而非另立字段表，同刻事实不漂移。"""

    pillar: BaziPillar = Field(description="合成时柱，`position` 为 transit_hour。")
    ten_god: TransitTenGod = Field(description="时干对日主的十神释义，不参与账本。")
    score: ScoreValue = Field(description="四段账本：年段无前缀 / `yue.` / `ri.` / `shi.`。")
    fired: list[TransitFired] = Field(description="四段命中 + 判语全文。")
    narrative: str = Field(description="命中判语连缀；一条未中为空串。")
    relations: list[RelationPair]
    shensha: list[ShenShaEntry]
    branch_groups: list[BranchGroup]


class BaziLiushiResult(BaseModel):
    """一个八字日的完整流时页：命局摘要 + 日头回显 + 十二格 + 可选聚焦时辰明细。"""

    # 命局摘要：九件，与 BaziTransitResult / BaziLiuriResult 逐字同名（spec §7.3 不抽基类的理由）
    four_pillars: str
    pillars: list[BaziPillar]
    day_master: str
    day_master_element: str
    favorable_elements: list[str]
    unfavorable_elements: list[str]
    true_solar_time: str | None
    tst_applied: bool
    longitude: float

    # 日头回显：当日三段账本与历注，即流日矩阵那一天的那一份（§9.2 第 1 条红线）
    solar_date: str
    weekday: int = Field(ge=0, le=6, description="0 = 周一 … 6 = 周日。")
    lunar_day: str
    day_ganzhi: str
    year: int
    year_ganzhi: str
    year_age: int
    dayun_index: int
    dayun_ganzhi: str | None = Field(default=None, description="童年段未起运 → None。")
    month_index: int = Field(ge=0, le=11)
    month_in_chinese: str
    month_ganzhi: str
    month_start_solar: str
    month_end_solar: str
    day_score: ScoreValue = Field(description="三段账本（年/月/日），逐字等于流日矩阵同日那格。")
    day_fired: list[TransitFired]
    day_almanac: AlmanacYiJi = Field(description="日粒度历注，页头一句带过，不进十二格（决策 13）。")

    hours: list[TransitHourCell] = Field(description="恒 12 格，子时首格在 0。")
    focused: TransitHourDetail | None = Field(default=None, description="仅 `focus_hour_zhi` 所指那一格给出。")
    provenance: Provenance = Field(description="与流日页同源：12 张表，由 `liuri_provenance` 一处产出。")
