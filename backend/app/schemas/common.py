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
    前端镜像在 `frontend/src/components/ui/PlainSectionList.tsx:4`（Plan F T18 才搬进
    `types/common.ts`；AGENTS §3 说的是「镜像 `schemas/common.py` 的**落点**是 types/」，
    那一步归 T18，本任务只把后端契约立起来）。
    """

    title: str = Field(description="小节名，取自各系统 content 的小节名册，不是引擎现编的词。")
    text: str = Field(description="开篇句 + 逐条判语，段内以 \\n 分行；全表没有一句请求时生成。")
