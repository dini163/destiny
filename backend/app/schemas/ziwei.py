"""Pydantic schemas for the 紫微斗数 (Zi Wei Dou Shu) system.

Field names are snake_case end-to-end. The chart is fully deterministic: from the
农历 birth data it fixes the 命宫 / 身宫, the 五行局 (纳音), lays the fourteen 主星
plus the 乙级 吉煞 stars into the twelve 地支 palaces, applies the 生年干 四化 and
marks each 大限 range. No star position is invented at runtime — every one is
walked from the 安星 tables in :mod:`app.content.ziwei`.
"""

from pydantic import BaseModel, Field

from app.schemas.common import BirthInput, Gender


class ZiweiRequest(BirthInput):
    """Input for a 紫微斗数 chart.

    Extends the shared :class:`BirthInput` and makes ``gender`` mandatory because
    the 大限 direction (阳男阴女顺行 / 阴男阳女逆行) depends on it. ``calendar``
    matters here more than for 八字: 斗数 reads the 农历 month / day directly.
    """

    gender: Gender = Field(description="Required: fixes the 大限 direction.")
    apply_true_solar_time: bool = Field(
        default=True, description="Correct to True Solar Time before deriving the 时辰 (PRD 7)."
    )
    name: str | None = Field(default=None, max_length=40, description="命主称谓，仅回显。")


class StarPlacement(BaseModel):
    """One star seated in a palace, with any 四化 mark it carries."""

    name: str = Field(description="星名, e.g. 紫微.")
    kind: str = Field(description="主星 | 吉 | 煞 | 禄马.")
    element: str = Field(description="五行 of the star.")
    yin_yang: str | None = Field(default=None, description="阴 / 阳 (主星 only).")
    group: str | None = Field(default=None, description="紫微系 / 天府系 (主星 only).")
    nature: str | None = Field(default=None, description="星情 keyword (主星 only).")
    sihua: str | None = Field(default=None, description="化禄 / 化权 / 化科 / 化忌 when marked.")


class Palace(BaseModel):
    """One of the twelve 地支 palaces, ordered by 地支 index (子=0 … 亥=11)."""

    index: int = Field(description="地支 index 0-11 (子=0), for grid placement.")
    zhi: str = Field(description="地支, e.g. 未.")
    gan: str = Field(description="宫干 from 五虎遁, e.g. 癸.")
    ganzhi: str = Field(description="宫干支, e.g. 癸未.")
    name: str = Field(description="宫名, e.g. 命宫.")
    is_ming: bool = Field(description="This palace is the 命宫.")
    is_shen: bool = Field(description="This palace is the 身宫.")
    dayun: str | None = Field(default=None, description="大限 age range seated here, e.g. 3-12.")
    stars: list[StarPlacement] = Field(description="Stars seated in this palace.")


class SiHuaInfo(BaseModel):
    """The 生年干 四化 assignments."""

    year_gan: str = Field(description="生年天干, e.g. 庚.")
    lu: str = Field(description="化禄 star.")
    quan: str = Field(description="化权 star.")
    ke: str = Field(description="化科 star.")
    ji: str = Field(description="化忌 star.")


class ZiweiProvenance(BaseModel):
    """Chart provenance — engine, corpus version and the 四化 school note."""

    engine: str
    content_version: str
    source: str
    school_note: str = Field(description="四化派别与安星口径说明，诚实标注分歧点。")


class ZiweiChart(BaseModel):
    """Complete 紫微斗数 chart produced by :mod:`app.engines.ziwei`."""

    # Echo / provenance of the birth input
    name: str | None = Field(description="命主称谓回显.")
    gender: str = Field(description="male | female.")
    calendar: str = Field(description="solar | lunar (of the supplied birth date).")
    standard_datetime: str = Field(description="Wall-clock birth datetime.")
    true_solar_time: str | None = Field(description="Corrected cast datetime, when TST applied.")
    tst_applied: bool = Field(description="Whether True Solar Time correction ran.")
    tst_offset_minutes: float | None = Field(description="TST offset in minutes, when applied.")
    longitude: float = Field(description="Longitude used for TST.")

    # 农历 birth facts (the real 安星 inputs)
    lunar_date: str = Field(description="农历生日中文, e.g. 庚辰年七月十七.")
    lunar_year_ganzhi: str = Field(description="农历年干支 (正月初一界), e.g. 庚辰.")
    lunar_month: int = Field(description="农历月 1-12 (闰月取同号).")
    lunar_day: int = Field(description="农历日 1-30.")
    lunar_leap: bool = Field(description="Whether the birth month is a 闰月.")
    time_zhi: str = Field(description="时支, e.g. 丑.")

    # Core chart anchors
    ming_gong_zhi: str = Field(description="命宫地支, e.g. 未.")
    ming_gong_ganzhi: str = Field(description="命宫干支, e.g. 癸未.")
    ming_gong_nayin: str = Field(description="命宫纳音, e.g. 杨柳木.")
    shen_gong_zhi: str = Field(description="身宫地支.")
    shen_gong_name: str = Field(description="身宫所落宫名, e.g. 迁移.")
    wuxing_ju: str = Field(description="五行局名, e.g. 木三局.")
    wuxing_ju_number: int = Field(description="局数 2-6，亦为大限起运岁数.")
    ming_zhu: str = Field(description="命主 (by 生年支).")
    shen_zhu: str = Field(description="身主 (by 生年支).")
    ziwei_zhi: str = Field(description="紫微星所落地支宫.")
    tianfu_zhi: str = Field(description="天府星所落地支宫.")

    # Stars, palaces and 四化
    palaces: list[Palace] = Field(description="十二宫，按地支 index 0-11 排列.")
    sihua: SiHuaInfo = Field(description="生年干四化.")

    # 大限
    dayun_direction: str = Field(description="顺行 | 逆行.")
    dayun_start_age: int = Field(description="大限起运虚岁 = 局数.")

    engine: str = Field(default="ziwei-deterministic")
    provenance: ZiweiProvenance
