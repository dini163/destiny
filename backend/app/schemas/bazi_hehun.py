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
