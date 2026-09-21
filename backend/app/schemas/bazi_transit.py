"""岁运（流年 / 流月）的响应形态：spec §7.3 的结构，snake_case 直出前端，无映射层。

本文件是"一页岁运"的四件事：一条命中的规则（`TransitFired`）、一个流年（`TransitYear`）、
一个节气月（`TransitMonth`）、整页（`BaziTransitResult`）。请求模型 `BaziTransitRequest`
在 Task 11 追加于此后 —— 四者同源于 `engines/bazi_transit.py::compute_transit` 的一次
装配，分开定义只是让"一年长什么样"这件事先于"整页长什么样"稳定下来。

`fired` 是账本的人类可读镜像：一行账（`ScoreFactor`）配一句判语（`reading`）与一个
族名（`family`，前端按族折叠）。二者由同一个命中集派生，不可能分家。月段的行在 `key`
与 `rule` 上带 `yue.` 前缀、在 `label` 上带"（流月）"后缀 —— 同一条规则可以在一份月账本
里出现两次（年段一次、月段一次），不带前缀就读不出那一行是谁加的分（spec §6.4）。

`null` 只有四处，且都是结构性的而非兜底：`months`（未请求 `focus_year`）、`focus_year`
本身（只要年表）、`dayun_ganzhi`（童年段未起运）、`true_solar_time`（关闭校正）。
`score` 永不为 `null`：一条都没命中时账本只剩基准 50 分 / 档"平"，这本身是可核对的结论。
"""

from pydantic import BaseModel, Field

from app.schemas.bazi import BaziPillar, DayunStep
from app.schemas.bazi_breakdown import Provenance
from app.schemas.bazi_rules import BranchGroup, RelationPair, ShenShaEntry
from app.schemas.scoring import ScoreValue


class TransitFired(BaseModel):
    """一条命中的岁运规则：账本行 + 它自己的释义。"""

    key: str = Field(description="机器可读规则键，与 `ScoreFactor.rule` 逐字相等；月段带 `yue.` 前缀。")
    label: str = Field(description="短名，如 冲太岁；月段加\"（流月）\"后缀。")
    family: str = Field(description="九族之一（yongshen / taisui / …），前端按族折叠。")
    delta: float = Field(description="本行分值，与账本里那一条同一个数。")
    reading: str = Field(description="单句判语，古籍引文在此，末尾自署四书或'本系统'。")


class TransitTenGod(BaseModel):
    """岁运之干对日主的十神：只作释义，不参与账本（spec §6.3）。"""

    god: str = Field(description="十神名，如 正官；岁运柱不是日主，故无'日主'这一取值。")
    meaning: str = Field(description="《渊海子平》原句，取自 `ten_god_meaning`，引擎不组句。")
    source: str = Field(description="该释义的书级出处。")


class TransitMonth(BaseModel):
    """一个节气月：两段账本（年段 + 月段），明细表不重复挂（spec §7.3）。"""

    index: int = Field(ge=0, le=11, description="0 = 寅月（正月），与 `LiuYue.getIndex()` 同序。")
    month_in_chinese: str = Field(description="月名：正 / 二 / … / 冬 / 腊。")
    ganzhi: str = Field(description="月柱干支，由年干按五虎遁推出。")
    pillar: BaziPillar = Field(description="合成月柱，`position` 为 transit_month。")
    start_solar: str = Field(description="交节日（ISO）：立春起寅月，非农历初一。")
    end_solar: str = Field(description="下一交节前一日（ISO）。")
    score: ScoreValue = Field(description="两段账本：该流年全部命中行 + 该流月命中行。")
    fired: list[TransitFired] = Field(description="逐行可见：年段行无 `yue.` 前缀，月段行带。")


class TransitYear(BaseModel):
    """一个流年：合成柱、单段账本与三张岁运扫描明细。"""

    year: int
    age: int = Field(description="该年虚岁，由 lunar-python 的 `LiuNian.getAge()` 给。")
    pillar: BaziPillar = Field(description="流年合成柱，`position` 为 transit_year（spec §5）。")
    dayun_index: int = Field(description="所从出的大运段序号（0 为未起运的童年段）。")
    dayun_ganzhi: str | None = Field(default=None, description="童年段无运可论 → None。")
    ten_god: TransitTenGod
    score: ScoreValue = Field(description="单段（岁）账本；Σ factors[].delta == value。")
    fired: list[TransitFired]
    narrative: str = Field(
        description="命中判语连缀（\"；\".join(reading) + \"。\"），与六维详批同法。"
        "月卡不再重复此句：年段断语在年卡已给过一次，月段账本逐行可展开。"
    )
    relations: list[RelationPair] = Field(
        description="只含岁运落点（一端为 extra0）的关系；命局自有的关系不在此列。"
    )
    shensha: list[ShenShaEntry] = Field(
        description="只含 `matches` 落在 extra0 的条目；中性者亦呈现，只是不定价（spec §6.2）。"
    )
    branch_groups: list[BranchGroup] = Field(
        description="只含带 extra0 成员的局，是 `heyue` 族各行的凭据。"
    )
    months: list[TransitMonth] | None = Field(
        default=None, description="仅 `focus_year` 所指之年给出，其余年为 None。"
    )


class BaziTransitResult(BaseModel):
    """一整页岁运推演：命局摘要 + 区间回显 + 逐年账本（聚焦年含十二节气月）。"""

    # 命局摘要：只带这一页要用的那几件，不塞整个 BaziChart（spec §7.3）
    four_pillars: str = Field(description="四柱串，与主命盘 `four_pillars` 逐字相等。")
    pillars: list[BaziPillar] = Field(
        description="命局四柱：前端据此把 extra0 的落点标回是哪一柱。"
    )
    day_master: str = Field(description="日主天干，岁运十神与地势都以它论。")
    day_master_element: str = Field(description="日主五行。")
    favorable_elements: list[str] = Field(
        description="喜用：三法合并结果，镜像 `analysis.favorable_elements`，岁运不重判（§4 决策 3）。"
    )
    unfavorable_elements: list[str] = Field(description="忌神：同上，镜像 `analysis.unfavorable_elements`。")
    true_solar_time: str | None = Field(description="关闭真太阳时校正时为 None，而不是填回标准时。")
    tst_applied: bool = Field(description="校正是否生效；与 `true_solar_time` 是否为空同为一件事。")
    longitude: float = Field(description="用于校正的经度；未给经度时是东八区标准经线 120°。")

    # 区间回显：缺省补齐只在引擎里做一次
    start_year: int
    end_year: int
    focus_year: int | None = Field(default=None, description="给出流月的那一年；只要年表时为 None。")
    dayun_covered: list[DayunStep] = Field(
        description="区间跨过的运程，跨年段时可能两段；`is_current` 沿用主命盘的判定，不另起一套。"
    )
    years: list[TransitYear]

    provenance: Provenance = Field(
        description="`tables` = 主命盘八张 + 岁运两张（`bazi_changsheng`、`bazi_transit_rules`）。"
    )
