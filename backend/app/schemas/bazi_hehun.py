"""合婚的一进五出：spec §5 的结构，snake_case 直出前端，无映射层。

本文件是合婚的一进五出：一页的入参（`BaziHehunRequest`）、一造的精简档案
（`HehunPartner`）、一格对冲（`HehunCell`）、一条命中（`HehunFired`）、整页
（`BaziHehunResult`）。五者同源于 `engines/bazi_hehun.py::compute_hehun` 的一次装配。

`HehunPartner` 刻意**不是** `/natal` 的副本：神煞、格局、六维详批、藏干账本都是一个
人本命盘的事，双人页不重演，也不给同一份结论造第二个呈现口径（spec §5.2）。

`null` 只出现在结构性之处：`dayun` 段的 `ganzhi` 为空串即童限（沿用 `DayunStep`
既有约定）、`true_solar_time`（关闭校正）、`name`（未填称谓）。空格子不是缺键而是
`hits: []` —— 16 格恒在，前端才敢把"无"渲染出来而不是整格消失。
"""

from datetime import date, time
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.common import CalendarType

#: 乾/坤。键位即性别（spec §5.1），所以 `HehunProfile` 里没有 `gender` 字段。
PartnerSide = Literal["male", "female"]
#: 一条账本行的视角。互济族天生两向，其余四族无向（spec §6.2）。
HehunDirection = Literal["male_to_female", "female_to_male", "mutual"]
#: §2.6 的三档旺弱。**"平"既不落旺也不落弱**：它既不入互补图的四象限，也不进互济族的账。
Vigor = Literal["旺", "弱", "平"]


class HehunProfile(BaseModel):
    """一造的全部出生参数；性别由键位承载，不在 profile 里重复一份。"""

    birth_date: date
    birth_time: time
    calendar: CalendarType = CalendarType.SOLAR
    city: str | None = None
    latitude: float | None = None
    #: 缺省不设经线（与 `BirthInput.longitude` 同形）：显式经度一旦有默认值就会在
    #: `profile_longitude` 里恒胜过城市，地理编码永不发生，认不出的城市也就无从报错
    #: （spec §9.1）。标准经线 120E 的兜底只在**关闭校正**时由 `profile_longitude` 给出。
    longitude: float | None = Field(default=None, ge=-180, le=180)
    apply_true_solar_time: bool = True
    name: str | None = Field(default=None, max_length=40, description="称谓，仅回显，不进计算。")


class BaziHehunRequest(BaseModel):
    """合婚页入参：两造生辰 + 参考日 + 轴的起点与年数。

    `axis_years` 是唯一走 pydantic 的轴字段（1–30）：它单独越界就是入参错误。
    而 `axis_start_year` 越没越界，要两造的出生年都排完盘才知道，那是域错误，
    带机器码出去（spec §9.3）。
    """

    male: HehunProfile
    female: HehunProfile
    reference_date: date | None = None
    axis_start_year: int | None = None
    axis_years: int = Field(default=21, ge=1, le=30, description="轴长，默认对齐设计稿 2024–2044。")


class HehunCellHit(BaseModel):
    """矩阵一格里扫到的一条跨造事实。

    矩阵是呈现层：(乾日, 坤日) 那一格里被婚姻宫族收编的关系照样显示在这里，
    只是不再进账本（§6.2 的归属规则），所以 `rule` 只作标识、不代表那一行真的加了分。
    """

    kind: str = Field(description="关系中文名，与 `RELATION_TABLES` 的 kind 同词。")
    male_character: str = Field(description="乾那一根的干、支或整柱（伏吟/反吟论整柱）。")
    female_character: str = Field(description="坤那一根的干、支或整柱。")
    rule: str = Field(description="该 kind 的账本键。")
    direction: HehunDirection = Field(
        default="mutual",
        description="矩阵格一律 mutual —— 列出该字段是为了与 `HehunFired` 同一个渲染器，"
        "不是一格里藏着两个视角。",
    )


class HehunCell(BaseModel):
    """(乾一根柱) × (坤一根柱) 的一格；恒 16 格，空格 `hits` 为空列表。"""

    male_position: str = Field(description="乾侧柱位，恒取自 `POSITION_ORDER`。")
    female_position: str = Field(description="坤侧柱位；两字段合起来才是格位，格位不设第三字段。")
    hits: list[HehunCellHit]


class HehunFired(BaseModel):
    """一条命中的合婚规则：账本行 + 它自己的判语（spec §5.2）。"""

    rule: str = Field(description="与 `ScoreFactor.rule` 逐字相等。")
    label: str
    family: str = Field(description="五族之一：relation | group | yongshen | nayin | palace。")
    direction: HehunDirection = Field(description="互济族带视角，其余四族 mutual（spec §6.2）。")
    delta: float = Field(description="本行分值，与账本里那一条同一个数。")
    reading: str = Field(description="单句判语；借古籍的那半句与自造的那半句同在一句里。")


#: §7.2 的 5×5 通行关系，主语固定为乾（"我"= 乾）。
NayinRelation = Literal["生我", "我生", "我克", "克我", "比和"]

#: 互补图横轴。这里不用 `Vigor`（旺|弱|平）：§7.1 的"平既不落象限也不入账本"要写进类型，
#: 否则契约承认一个引擎永远给不出的取值，前端就得为它写一条走不到的分支。
ComplementAxis = Literal["旺", "弱"]


class HehunComplementElement(BaseModel):
    """象限里的一个五行：只带名字与比值；规则与分值在同级的那一格上。"""

    element: str
    ratio: float = Field(
        description="该造此行的加权量对其自身五行均值的比值（§2.6 的尺，四位小数）。"
        "带它出来是为了让「这一行为什么算旺」当场可核，不必回命盘页重算。"
    )


class HehunComplementCell(BaseModel):
    """四象限的一格（§7.1）：纵轴是观看方的喜/忌，横轴是对方该行的旺/弱。"""

    rule: str = Field(
        description="该格的账本键。`elements` 里每一个五行都在 `score.factors` 里有一行同名账 —— "
        "§7.1 的诚实性约束，Task 5 由同一张事实表保证。"
    )
    name: str = Field(description="单字格名：补 | 阙 | 冲 | 安。")
    mine: Literal["favorable", "unfavorable"] = Field(description="纵轴：这一行对**观看方**是喜是忌。")
    theirs: ComplementAxis = Field(description="横轴：**对方**盘里这一行的旺弱。恒为 旺|弱 —— 表里没有 平 这一格。")
    delta: float = Field(description="该格单价，与 `rule` 那条账本行同一个数。")
    elements: list[HehunComplementElement] = Field(
        description="落在本格的五行，按观看方喜忌集自身的序；空格是空列表（§10.6）。"
    )


class HehunComplementView(BaseModel):
    """一个视角的四象限。"""

    viewer: PartnerSide = Field(description="视角主语：male = 乾视坤。")
    label: str = Field(description="「乾视坤」短名，与账本行 `label` 里的那一处字同一来源。")
    cells: list[HehunComplementCell] = Field(
        min_length=4,
        max_length=4,
        description="恒 4 格，序即 §7.1 表：补 阙 冲 安。",
    )


class HehunComplement(BaseModel):
    """五行互补（§7.1）：四象限 × 两视角，与互济族账本出自**同一次判定**。

    措辞要说准：账本与图不是同一次*遍历*（账本取事实表的 `.row`，图按 (视角, 象限) 分桶，
    各自还要走一遍），是同一批 `YongshenFact` 的两个投影 —— 一次判定，两处读数。
    """

    views: list[HehunComplementView] = Field(
        min_length=2,
        max_length=2,
        description="恒 2 视角：乾视坤、坤视乾（§6.2 的有向族）。",
    )


class HehunNayinSide(BaseModel):
    """一造的年命纳音：名、五行、取象原文逐字取自 `NayinCorpus`。"""

    ganzhi: str = Field(description="年柱干支，如 戊辰。")
    nayin: str = Field(description="纳音全称，如 大林木。")
    element: str = Field(description="纳音五行 —— 生克论的是这个，不是日主五行。")
    imagery: str = Field(description="《三命通会》取象原文首句，逐字转录，引擎不改写。")
    source: str


class HehunNayin(BaseModel):
    """年命纳音（§7.2）：一对纳音只出一个关系、只入一行账，主语固定为乾。"""

    male: HehunNayinSide
    female: HehunNayinSide
    relation: NayinRelation
    phrase: str = Field(description="三字生克句：水生木 / 木克土 / 木与木同气。")
    rule: str = Field(description="`hh.nayin.*`，与账本里那一行同键。")
    delta: float
    reading: str = Field(description="§7.2 的固定句式，末尾必带 `HEHUN_NAYIN_NOTE`。")


#: §7.3 的同频三档。
AxisSync = Literal["同频", "半同步", "背离"]


class HehunAxisSide(BaseModel):
    """一造在某一年的分数与档位 —— 与岁运年表同一条装配路径，不另算（§10.5）。"""

    value: float = Field(description="该年岁运分，`transit_ledger` 的 `value`，0–100。")
    tier: str = Field(description="岁运四档：顺 | 平 | 滞。与合婚总分的四档是两套词汇（§6.4）。")
    dayun: str | None = Field(description="该年所从出的大运干支；起运前为 None（页面标「童限」）。")
    dayun_start_age: int = Field(description="那一步大运的起龄（虚岁）。童限段给的是童限那一段的起龄。")


class HehunAxisRow(BaseModel):
    """轴的一年：两造各自的分数 + 它们之差。简表不带判语（§5.2，继承切片 3）。"""

    year: int = Field(description="公历年，与岁运同一口径（立春为界取该年干支）。")
    ganzhi: str = Field(description="流年干支；两造的 `LiuNian` 表对同一年给同一个字。")
    male: HehunAxisSide
    female: HehunAxisSide
    gap: float = Field(ge=0, description="|乾分 - 坤分|。")
    sync: AxisSync


class HehunAxisSegment(BaseModel):
    """一段大运边界切出来的区间（设计稿的时间轴卡片，§7.3）。"""

    start_year: int
    end_year: int
    label: str = Field(
        description="只写事实本身：「乾·第 4 运 戊午（37—46 岁）／坤·第 4 运 戊寅（34—43 岁）」，"
        "起运前那一段标「童限」。不另立家族称谓表 —— 轴的段就是大运段。"
    )


class HehunAxis(BaseModel):
    """同频演进轴（§7.3）：轻量流年表，一轴一次算，不给任何一格展开明细。"""

    start_year: int
    end_year: int
    rows: list[HehunAxisRow]
    segments: list[HehunAxisSegment] = Field(description="段的并集恰好覆盖 `rows`，序与轴同向（Task 6 不变式）。")


#: §7.4 的六个组名。交集在前、独集在后，宜先忌后 —— 页面按这个序读。
YiJiKind = Literal["同宜", "乾独宜", "坤独宜", "同忌", "乾独忌", "坤独忌"]


class HehunYiJiItem(BaseModel):
    """一个五行的通说配属。"""

    element: str
    direction: str = Field(description="方位（木东 火南 土中 金西 水北）。")
    color: str = Field(description="色（青 赤 黄 白 黑）。")
    season: str = Field(description="季节（春 夏 四季 秋 冬）。")


class HehunYiJiGroup(BaseModel):
    kind: YiJiKind
    items: list[HehunYiJiItem] = Field(
        description="该组的五行：交集组按乾造的序，独集组按该造自己的序；空组是空列表（§10.6）。"
    )


class HehunYiJi(BaseModel):
    """宜忌（§7.4）：唯一输入是两造本命盘的喜用与忌神。"""

    groups: list[HehunYiJiGroup] = Field(
        min_length=6,
        max_length=6,
        description="恒 6 组，序即 §7.4 的阅读序（同宜→乾独宜→坤独宜→同忌→乾独忌→坤独忌）。",
    )
    declaration: str = Field(description="逐字取自 `HEHUN_YIJI_DECLARATION`，前端不补算也不改写。")
