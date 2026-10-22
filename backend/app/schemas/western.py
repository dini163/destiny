"""Pydantic schemas for the Western (tropical) natal-astrology system."""

from datetime import date, time

from pydantic import BaseModel, Field

from app.schemas.common import PlainSection, ProvenanceTable, Verdict


class WesternNatalRequest(BaseModel):
    """Input for a Western natal chart.

    ``latitude``/``longitude`` may be supplied directly or resolved from a city
    name. ``utc_offset_hours`` is the offset of the *local* birth time from UTC;
    when omitted it is approximated from the longitude (a theoretical time zone)
    and the response flags this so clients can supply an exact offset for
    precise ascendant timing.
    """

    birth_date: date = Field(description="Gregorian birth date.")
    birth_time: time = Field(description="Local clock birth time.")
    city: str | None = Field(default=None, description="City name for geocoding.")
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    utc_offset_hours: float | None = Field(
        default=None, ge=-14, le=14, description="Local-time offset from UTC in hours."
    )
    house_system: str = Field(default="P", description="House system code (P=Placidus, K=Koch, R=Regiomontanus, W=Whole).")


class PlanetPlacement(BaseModel):
    """A planet's tropical position, sign and house."""

    name: str
    glyph: str
    name_zh: str
    longitude: float = Field(description="Tropical ecliptic longitude, 0-360 degrees")
    sign: str
    sign_zh: str
    sign_glyph: str
    sign_index: int = Field(ge=0, le=11)
    degree_in_sign: float
    degree_text: str = Field(description="Degrees/minutes within the sign, e.g. 10°22'")
    house: int = Field(ge=1, le=12)
    retrograde: bool
    speed: float = Field(description="Longitudinal speed in degrees/day (negative = retrograde)")


class HouseCusp(BaseModel):
    """A house cusp position."""

    house: int
    longitude: float
    sign: str
    sign_zh: str
    degree_in_sign: float
    degree_text: str


class AxisPoint(BaseModel):
    """One of the four chart angles (ASC / DES / MC / IC)."""

    name: str = Field(description="ASC | DES | MC | IC")
    label: str = Field(description="Human-readable name, e.g. Ascendant")
    longitude: float
    sign: str
    sign_zh: str
    sign_index: int
    degree_in_sign: float
    degree_text: str
    house: int = Field(description="House the axis rules: ASC=1, IC=4, DES=7, MC=10")


class Aspect(BaseModel):
    """A major aspect between two planets."""

    planet1: str
    planet2: str
    type: str = Field(description="conjunction | sextile | square | trine | opposition")
    glyph: str
    angle: float = Field(description="Exact aspect angle in degrees")
    orb: float = Field(description="Absolute deviation from the exact angle")


class NodeInfo(BaseModel):
    """Lunar node positions (North / South)."""

    north_node_longitude: float
    north_node_sign: str
    north_node_sign_zh: str
    north_node_house: int
    south_node_longitude: float
    south_node_sign: str
    south_node_sign_zh: str
    south_node_house: int


class WesternProvenance(BaseModel):
    """本命页的出处块：一句自撰声明 + 本响应真读到的三张白话表。

    两格而不是 spec §8 说的四格（`engine`/`note`/`source`/`tables`）：`engine` 在同一响应的
    `chart.engine` 已有，`source` 与 `tables[*].source` 是同一个字符串——四格形状会让一张
    出处面板把同一句话印两遍（偏差表第 3 行）。真同形先例是 `ZiweiProvenance`/`QimenProvenance`
    （`VedicProvenance` 没有 `tables`，spec 那句「与 Vedic 同形」是假的）。
    **日后若全站统一 provenance 形状，这一家要动的是两处**：这里补格，
    以及 `app/engines/western.py::_western_tables()` 之外的 `engine` 注入点——
    别照别人的形状直接加 `engine`/`source`，那两格在本系统是重复印刷，不是缺格。
    """

    note: str = Field(description="自撰声明（R50 三句），页面出处块与免责文案共用。")
    tables: list[ProvenanceTable] = Field(description="本响应真读到的三张白话表（AGENTS §7 读了就列）。")


class WesternChart(BaseModel):
    """Complete Western natal chart produced by :mod:`app.engines.western`."""

    # Provenance
    local_datetime: str
    utc_datetime: str
    julian_day: float
    latitude: float
    longitude: float
    utc_offset_hours: float
    utc_offset_source: str = Field(description="explicit | longitude_approximation")
    house_system: str
    zodiac: str = Field(default="tropical")

    # Headline placements
    sun_sign: str
    sun_sign_zh: str
    moon_sign: str
    moon_sign_zh: str
    ascendant_sign: str
    ascendant_sign_zh: str

    # Chart data
    planets: list[PlanetPlacement] = Field(description="Ten major bodies: Sun..Pluto")
    axes: list[AxisPoint] = Field(description="ASC, DES, MC, IC")
    houses: list[HouseCusp] = Field(description="Twelve house cusps")
    aspects: list[Aspect] = Field(description="Major aspects among the planets")
    nodes: NodeInfo
    element_balance: dict[str, int] = Field(description="fire/earth/air/water counts among planets")
    modality_balance: dict[str, int] = Field(description="cardinal/fixed/mutable counts among planets")
    plain: list[PlainSection] = Field(
        description="页尾「白话详解」的八段，逐字取自自撰表 `content/western_plain*.py`（戊组 spec §8）。必填：缺白话即视为伪造响应。"
    )

    verdict: Verdict = Field(description="综合结论卡片：档位/星级/结论句/分项/建议，由相位性质计数判定层合成。")

    provenance: WesternProvenance = Field(
        description="出处块：自撰声明与被读取的三张白话表。必填，缺出处即视为伪造响应。"
    )

    engine: str = Field(default="pyswisseph")
