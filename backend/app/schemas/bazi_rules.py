"""神煞与关系的响应形态：spec §6.2/§6.3 的结构，snake_case 直出前端，无映射层。"""

from pydantic import BaseModel, Field


class ShenShaMatch(BaseModel):
    position: str = Field(description="year | month | day | hour | extra<n>")
    character: str = Field(description="命中的那个字（干或支，或魁罡的整个日柱）")
    at: str = Field(description="gan | zhi | pillar：落点在柱的哪一侧。")


class ShenShaEntry(BaseModel):
    name: str
    quality: str = Field(description="吉 | 凶 | 中性")
    checked_from: str = Field(
        description="以什么基准起查，如 '申子辰局'、'日柱庚子·甲午旬'；"
        "年支与日支各起一局时两局并列，读得出'查过哪几局'才算可复核。"
    )
    matches: list[ShenShaMatch]
    meaning: str
    source: str


class RelationPair(BaseModel):
    kind: str = Field(description="与 spec §6.3 表格同词的中文名，如 天干五合、地支六冲。")
    pillar_a: str
    pillar_b: str
    character_a: str
    character_b: str
    strength: str = Field(description="紧临 | 隔位 | 远位：柱位距离决定力量，不是赋分。")
    transforming_element: str | None = Field(
        default=None, description="合化目标，非已化（spec §6.3 明确不做合化判定）。"
    )
    reading: str
    source: str


class BranchMember(BaseModel):
    pillar: str
    branch: str
    ten_god: str = Field(description="该支本气藏干对日主的十神。")


class BranchGroup(BaseModel):
    kind: str = Field(description="三合 | 半合 | 三会")
    element: str
    members: list[BranchMember] = Field(
        description="按柱序（年→月→日→时）列出，同一种局只出一条。"
    )
    is_complete: bool = Field(description="三支齐见才为真。")
    reading: str
    source: str
