"""Shared Pydantic schemas used across divination systems."""

from datetime import date, time
from enum import Enum

from pydantic import BaseModel, Field


class CalendarType(str, Enum):
    """Calendar system of the supplied birth date."""

    SOLAR = "solar"
    LUNAR = "lunar"


class Gender(str, Enum):
    """Subject gender; required by systems whose luck pillars depend on it."""

    MALE = "male"
    FEMALE = "female"


class BirthInput(BaseModel):
    """Common birth-data input shared by natal-chart systems."""

    birth_date: date = Field(description="Birth date in the selected calendar.")
    birth_time: time = Field(description="Birth time, precise to the minute.")
    calendar: CalendarType = Field(default=CalendarType.SOLAR)
    city: str | None = Field(default=None, description="City name for geocoding.")
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    gender: Gender | None = Field(default=None)


class TrueSolarTimeResponse(BaseModel):
    """True Solar Time preview shown in the input console."""

    standard_time: str
    true_solar_time: str
    offset_minutes: float
    longitude: float


class ProvenanceTable(BaseModel):
    """一份被引用的数据表（系统无关，八字与姓名学共用）。"""

    name: str = Field(description="语料模块名，如 bazi_shensha。")
    version: str = Field(description="语料版本号，全表共用 content.CONTENT_VERSION。")
    source: str = Field(description="书级出处，或 模型参数/本系统纲要 声明。")


class PlainSection(BaseModel):
    """页尾白话块里的一格：`title` 是版面那一格的名字，`text` 是引擎拼好的整段。

    系统无关（紫微十二宫、奇门九宫、本命八段共用一个形状），所以住 `common.py`。
    前端镜像在 `frontend/src/types/common.ts`（Plan F T18 已搬；组件
    `components/ui/PlainSectionList.tsx` 改为 `import type` 消费它，那边不再有第二份定义）。
    AGENTS §3 说的是「镜像 `schemas/common.py` 的落点是 types/」，搬家的那笔是 `2825f79`。

    **为什么只有两格**：块容器只承载「格的名字 + 拼好的整段」。逐条判语在 `text` 里已经
    合成一段（那是 `plain_compose.compose` 的活），而段内计数、键值、出处都不进这一格——
    紫微/奇门那两边干脆连 pydantic 块都没有，直接把 `compose()` 的返回串放进 `plain: str`
    （`schemas/ziwei.py:54`、`schemas/qimen.py:77`）；命盘是唯一一处要按格发一列的系统。
    **日后若全站统一块形状，这一家要动的是各系统 content 的小节名册与 `compose()` 的返回
    契约，不是这两格**：给块加第三格（例如「本段计数」）要动的是三个系统的 `plain` 字段类型
    与前端那三处 `sections={...}` 映射，而它们并不载那个事实。写法参照同族的
    `schemas/western.py::WesternProvenance`（「日后若全站统一…要动的是哪几处」那段）。
    """

    title: str = Field(description="小节名，取自各系统 content 的小节名册，不是引擎现编的词。")
    text: str = Field(description="开篇句 + 逐条判语，段内以 \\n 分行；全表没有一句请求时生成。")
