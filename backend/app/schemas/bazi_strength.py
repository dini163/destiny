"""Wire types for the structure / hidden-stem layer (spec §6.1, §6.4, §7)."""

from pydantic import BaseModel, Field


class GeJu(BaseModel):
    name: str = Field(description="格局名，如 偏财格 / 建禄格 / 月刃格。")
    from_pillar: str = Field(description="定格所在柱，本切片恒为 month。")
    ten_god: str = Field(description="定格十神；建禄/月刃无对应十神，恒记 比肩。")
    is_success: bool = Field(description="成格与否：破格优先，两不命中亦为 False。")
    notes: list[str] = Field(default_factory=list, description="成/破判语，整句取自语料，按柱序。")
    source: str


class HiddenStemWeight(BaseModel):
    position: str = Field(description="year | month | day | hour")
    branch: str = Field(description="地支，如 辰")
    stem: str = Field(description="藏干，如 戊")
    role: str = Field(description="本气 | 中气 | 余气；与 weight 同一口径（模型参数）。")
    weight: float = Field(ge=0, le=1, description="0.6/0.3/0.1；单藏干支 1.0。")
    ten_god: str = Field(description="该藏干对日主的十神。")
    source: str
