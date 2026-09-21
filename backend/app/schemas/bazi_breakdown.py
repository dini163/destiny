"""响应层独有的三类产物：命局十神摘要、当前大运摘要、数据溯源（spec §7）。

`BaziPillar` 里已有的裸列表（`hidden_stems` / `shishen_zhi`）保持原样，本模块只加
"带出处与权重的版本"，两者并存是为了不破坏已联调的前端；新字段一律 snake_case。
"""

from pydantic import BaseModel, Field

from app.schemas.bazi_rules import RelationPair
from app.schemas.common import ProvenanceTable


class TenGodReading(BaseModel):
    ten_god: str = Field(description="十神名，如 偏印。")
    count: int = Field(ge=1, description="命局出现次数：年/月/时干 + 四柱藏干，日主本身不计。")
    positions: list[str] = Field(description="落点，形如 month.gan、day.zhi(癸)，按柱序。")
    meaning: str = Field(description="整句取 content 十神语料，引擎不组句。")
    six_relation: str | None = Field(description="六亲对应，按请求性别取；无性别时为 None。")
    source: str


class DayunDetail(BaseModel):
    index: int = Field(ge=0, description="与 `dayun[].index` 同值，两个视图互指。")
    ganzhi: str
    start_age: int
    end_age: int
    relations: list[RelationPair] = Field(
        description="该运干支与命局四柱的二元关系（伏吟/反吟）；不含命局自身已有关系。"
    )


class Provenance(BaseModel):
    reference_date: str = Field(description="判定当前大运的截止日（ISO）；未传时为服务器当日。")
    engine: str = Field(description="四柱来源引擎，恒为 lunar-python。")
    tables: list[ProvenanceTable]
