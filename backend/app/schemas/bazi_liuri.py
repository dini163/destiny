"""流日矩阵的一进二出：请求、矩阵简表、聚焦日明细、整段响应（spec §7）。

一页 = 一段节气月的 29—32 格 + 至多一格的全明细。简表格**不含 `reading`**：端点实发
的 29 格是 27.6 KB，逐格补上判语全文则 47.3 KB（同一序列化口径下的两次实测，spec §2.5
立这条时量到的是 24.7 → 44.9 KB，格上字段略有出入而倍数一致），判语是规则表的静态
文本，聚焦卡逐行给全即可。`TransitDayHit` 是 `TransitFired` 去掉 `reading` 的形状，四个
同名字段逐字相等由测试钉，而不是靠"引用同一个类型再塞个空串" —— 让 `reading` 可空
等于邀请前端到处兜底。

`null` 三处，都是结构性：`dayun_ganzhi`（童年段未起运）、`true_solar_time`（关闭校正）、
`focused`（未请求聚焦日）。`value` 永不为 `null`；`day_hits` 可以是空数组 —— 一条未中
本身就是"这一天没有可记的账"，是结论不是缺数据。
"""

from datetime import date

from pydantic import BaseModel, Field

from app.schemas.bazi import BaziNatalRequest, BaziPillar
from app.schemas.bazi_breakdown import Provenance
from app.schemas.bazi_rules import BranchGroup, RelationPair, ShenShaEntry
from app.schemas.bazi_transit import TransitFired, TransitTenGod
from app.schemas.scoring import ScoreValue


class BaziLiuriRequest(BaziNatalRequest):
    """流日矩阵入参：命盘入参 + 两个可空日期。

    继承 `BaziNatalRequest` 因而 `gender` 必填（无性别即无大运、无流年可摊）。两个日期
    都不做 pydantic 范围校验：段推不推得出、聚焦日在不在段内，都是前端要分支的域错误
    （`model_validator` 会被包成 `validation_error`，机器码就丢了）。`anchor_date` 缺省
    取 `reference_date`，于是"打开页面就是本月"不需要前端传任何东西。
    """

    anchor_date: date | None = Field(
        default=None, description="段内任一日；缺省 = 参考日所在的节气月段。"
    )
    focus_date: date | None = Field(
        default=None, description="给出则额外返回该日详批；必须落在解析出的段内。"
    )


class AlmanacYiJi(BaseModel):
    """历注宜忌：外部库所藏通书内容，不参与任何计分（决策 5）。"""

    yi: list[str] = Field(description="宜，全量数组，顺序即库给顺序；可为空数组（库给的空，服务端不代填）。")
    ji: list[str] = Field(description="忌，全量数组。")


class TransitDayHit(BaseModel):
    """矩阵格上的一条日段命中：账本行的可读镜像，判语全文在聚焦卡。"""

    key: str = Field(description="带 `ri.` 前缀的规则键，与 `ScoreFactor.rule` 逐字相等。")
    label: str = Field(description="短名 +「（流日）」后缀。")
    family: str = Field(description="九族之一，与 `TransitFired.family` 同源。")
    delta: float = Field(description="本行分值，与账本里那一条同一个数。")


class TransitDayCell(BaseModel):
    """矩阵里的一格。`weekday` 由服务端给，前端不做星期推算（时区一偏整列错位）。"""

    solar_date: str = Field(description="ISO 日期。")
    weekday: int = Field(ge=0, le=6, description="0 = 周一 … 6 = 周日，由 `Solar.getWeek()`（0 = 周日）换算。")
    lunar_day: str = Field(description="农历日串：月名 + 日名，闰月由库自带「闰」字，如 腊十九 / 闰五初二。")
    ganzhi: str = Field(description="日柱干支，平柱（spec §2.2）。")
    value: float = Field(ge=0, le=100, description="三段账本的 value，逐字取自账本而不是另算。")
    tier: str = Field(description="顺 / 平 / 滞，同一份账本的档位。")
    day_hits: list[TransitDayHit] = Field(description="只含 `ri.` 行；一条未中为 []。")
    almanac: AlmanacYiJi


class TransitDayDetail(TransitDayCell):
    """聚焦日 = 简表行 + 全部明细。继承而非另立字段表：同一天的两组事实不可能漂移。"""

    pillar: BaziPillar = Field(description="合成日柱，`position` 为 transit_day。")
    ten_god: TransitTenGod = Field(description="日干对日主的十神释义，不参与账本。")
    score: ScoreValue = Field(description="三段账本：年段无前缀 / 月段 `yue.` / 日段 `ri.`。")
    fired: list[TransitFired] = Field(description="三段命中 + 判语全文。")
    narrative: str = Field(description="命中判语连缀；一条未中为空串。")
    relations: list[RelationPair] = Field(description="只留 extra0 参与者的关系。")
    shensha: list[ShenShaEntry] = Field(description="只含落在 extra0 的神煞，中性者亦呈现。")
    branch_groups: list[BranchGroup] = Field(description="只含带 extra0 成员的合局。")


class BaziLiuriResult(BaseModel):
    """一整段流日矩阵：命局摘要 + 段回显 + 逐日格 + 可选聚焦日明细。"""

    # 命局摘要：九件，字段名与 BaziTransitResult 逐字相同（不抽基类的理由见 spec §7.3）
    four_pillars: str
    pillars: list[BaziPillar]
    day_master: str
    day_master_element: str
    favorable_elements: list[str]
    unfavorable_elements: list[str]
    true_solar_time: str | None
    tst_applied: bool
    longitude: float

    # 段回显：端点与月段账本都取自服务端一次定位，前端不重算
    anchor_date: str
    year: int = Field(description="段所属流年；段尾跨年时与 `month_end_solar` 的年不同。")
    year_ganzhi: str
    year_age: int = Field(description="该年虚岁，由 lunar-python 的 `LiuNian.getAge()` 给。")
    dayun_index: int
    dayun_ganzhi: str | None = Field(default=None, description="童年段未起运 → None。")
    month_index: int = Field(ge=0, le=11, description="0 = 寅月，与 `LiuYue.getIndex()` 同序。")
    month_in_chinese: str
    month_ganzhi: str
    month_start_solar: str = Field(description="交节日（ISO），非农历初一。")
    month_end_solar: str = Field(description="下一交节前一日（ISO）。")
    month_score: ScoreValue = Field(description="两段账本，逐字等于岁运页同段月卡（§9.2 红线）。")
    month_fired: list[TransitFired]

    days: list[TransitDayCell]
    focused: TransitDayDetail | None = Field(default=None, description="仅 `focus_date` 所指之日给出。")
    provenance: Provenance = Field(
        description="`tables` = 主命盘八张 + 岁运两张 + 历注一张 = 11。"
    )
