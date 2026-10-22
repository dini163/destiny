"""Pydantic schemas for the 奇门遁甲 (Qi Men Dun Jia) system.

Field names are snake_case end-to-end. 奇门 is time-based divination, not a natal
chart: from the 用事时辰 it fixes the 阴阳遁 and 局数 (节气 + 三元符头), lays the
三奇六仪 地盘, finds the 值符/值使 from the 时辰旬首, then rotates the 天盘九星、
人盘八门、神盘八神 into the 洛书九宫. Nothing is invented at runtime — every star,
door, god and 干 is walked from the tables in :mod:`app.content.qimen`.
"""

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import PlainSection, ProvenanceTable, Verdict


class QimenRequest(BaseModel):
    """Input for a 奇门遁甲 起局.

    ``cast_time`` defaults to the current moment and supplies the 年月日时 干支; the
    时辰 fixes the 值符值使, while the 节气 + 日干支符头 fix the 局. ``question`` is the
    optional 占问事项, echoed back only.
    """

    cast_time: datetime | None = Field(default=None, description="用事时刻；缺省取服务器当前时间。")
    question: str | None = Field(default=None, max_length=120, description="占问事项，仅回显。")


class StarInfo(BaseModel):
    """One 九星 seated on the 天盘, with its 五行·吉凶·类象."""

    name: str = Field(description="星名, e.g. 天心.")
    element: str = Field(description="五行.")
    luck: str = Field(description="吉 | 凶 | 中平.")
    nature: str = Field(description="星情类象 keyword.")
    is_zhifu: bool = Field(default=False, description="此星为本局值符星。")


class DoorInfo(BaseModel):
    """One 八门 seated on the 人盘."""

    name: str = Field(description="门名, e.g. 开门.")
    element: str = Field(description="五行.")
    luck: str = Field(description="吉 | 凶 | 中平.")
    nature: str = Field(description="门意类象 keyword.")
    is_zhishi: bool = Field(default=False, description="此门为本局值使门。")


class GodInfo(BaseModel):
    """One 八神 seated on the 神盘."""

    name: str = Field(description="神名, e.g. 值符.")
    luck: str = Field(description="吉 | 凶.")
    nature: str = Field(description="神意类象 keyword.")


class QimenPalace(BaseModel):
    """One 洛书宫 cell of the board (中五宫 carries only its 地盘干)."""

    number: int = Field(description="洛书数 1-9.")
    gua: str = Field(description="卦名, e.g. 坎.")
    direction: str = Field(description="方位, e.g. 北.")
    element: str = Field(description="宫五行.")
    zhi: str = Field(description="所纳地支, e.g. 子；中宫为空。")
    row: int = Field(description="3×3 grid row (南上北下).")
    col: int = Field(description="3×3 grid column.")
    is_center: bool = Field(description="中五宫（无门无神，天禽寄坤二）。")
    dipan_gan: str = Field(description="地盘干（固定，由局数布）。")
    tianpan_gan: list[str] = Field(description="天盘干（旋转后落此宫；坤二寄中宫干时可两枚）。")
    stars: list[StarInfo] = Field(description="天盘九星（天禽寄坤二时可两枚）。")
    door: DoorInfo | None = Field(default=None, description="人盘八门；中宫为 null。")
    god: GodInfo | None = Field(default=None, description="神盘八神；中宫为 null。")
    kong: bool = Field(description="此宫地支落旬空。")
    ma: bool = Field(description="此宫地支落驿马。")
    is_zhifu_palace: bool = Field(description="值符星落此宫。")
    is_zhishi_palace: bool = Field(description="值使门落此宫。")
    plain: str = Field(description="本宫白话：卦位开篇句 + 逐星 + 门 + 神，段内以 \\n 分行；中宫只有开篇句。")


class QimenProvenance(BaseModel):
    """Chart provenance — engine, corpus version and the school notes."""

    engine: str
    content_version: str
    source: str
    school_note: str = Field(description="起局/排盘/寄宫/八神口径说明，诚实标注派别分歧。")
    tables: list[ProvenanceTable] = Field(description="本响应真正读过的语料表（AGENTS §7：读了就列，宁缺勿多）。")


class QimenChart(BaseModel):
    """Complete 奇门遁甲 局 produced by :mod:`app.engines.qimen`."""

    # Echo
    question: str | None = Field(description="占问事项回显。")
    cast_time: str = Field(description="用事时刻, e.g. 2026-09-25 14:30.")

    # 四柱干支
    year_ganzhi: str = Field(description="年干支。")
    month_ganzhi: str = Field(description="月干支。")
    day_ganzhi: str = Field(description="日干支。")
    time_ganzhi: str = Field(description="时干支。")

    # 定局
    jieqi: str = Field(description="用事所属节气, e.g. 秋分。")
    yuan: str = Field(description="上元 | 中元 | 下元（日干支符头定）。")
    dun: str = Field(description="阳遁 | 阴遁。")
    ju_number: int = Field(description="局数 1-9。")
    ju_name: str = Field(description="局名, e.g. 阴遁七局。")

    # 值符值使
    xunshou: str = Field(description="时辰旬首, e.g. 甲辰。")
    xunshou_yi: str = Field(description="旬首所遁六仪, e.g. 壬。")
    zhifu_star: str = Field(description="值符星名, e.g. 天禽。")
    zhishi_door: str = Field(description="值使门名, e.g. 死门。")
    zhifu_palace: int = Field(description="值符星落宫洛书数。")
    zhishi_palace: int = Field(description="值使门落宫洛书数。")
    kongwang: str = Field(description="旬空二支, e.g. 寅卯。")
    yima: str = Field(description="驿马地支, e.g. 巳。")

    palaces: list[QimenPalace] = Field(description="洛书九宫，按 1-9 排列。")
    plain: list[PlainSection] = Field(
        description="全局白话：值符主线、值使门线、时干落宫、旬空与驿马四节（逐字取自 content/qimen_plain.py 的框架句）。"
    )

    verdict: Verdict = Field(description="综合结论卡片：档位/星级/结论句/分项/建议，由值符值使两宫吉凶计数判定层合成。")

    engine: str = Field(default="qimen-luoshu-rotating")
    provenance: QimenProvenance
