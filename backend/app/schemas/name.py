"""`POST /api/v1/name/analyze` 的响应契约（spec §7）。

字段名 snake_case 直通前端，没有映射层。可空字段的规则是决策八：算不出就 None，
前端整块不渲染——所以这里不许出现 default=0 之类的"看着像值"的占位。
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.common import ProvenanceTable, Verdict
from app.schemas.scoring import ScoreValue


class NameInput(BaseModel):
    surname: str
    given: str
    resolved_traditional: str = Field(description="按指定/唯一候选核定后的正体全名。")
    modality: str = Field(description="单姓单名 / 单姓复名 / 复姓单名 / 复姓复名。")
    modality_formula: str = Field(description="本次实际采用的四格分支公式，使分支可核对。")


class NameReading(BaseModel):
    pinyin: str
    tone_number: int = Field(ge=1, le=5)
    tone_name: str


class NameChar(BaseModel):
    char: str = Field(description="页面上展示的字形（用户输入的那个）。")
    resolved: str = Field(description="用于计笔画的正体字形。")
    simplified: list[str] = Field(default_factory=list, description="Unihan kTraditionalVariant 指向的简体。")
    kangxi_strokes: int | None = None
    radical_no: int | None = Field(default=None, ge=1, le=214)
    residual_strokes: int | None = None
    radical_char: str | None = None
    radical_strokes: int | None = None
    readings: list[NameReading] = Field(default_factory=list, description="多音如实全给，不替用户选。")
    stroke_source: str | None = Field(default=None, description="笔画推导出处；未收录时为 None。")


class NameGrid(BaseModel):
    key: str = Field(description="tian / ren / di / wai / zong。")
    label: str
    formula: str = Field(description="算式，如 '16+8'；缺笔画的一侧以 '?' 如实显示。")
    value: int | None
    number: int | None = Field(default=None, ge=1, le=81, description="((value-1) mod 81)+1。")
    fortune: str | None
    yinyang: str | None = Field(default=None, description="奇阳偶阴，推导量（spec §6.3）。")
    wuxing: str | None = Field(default=None, description="尾数定五行，推导量。")
    pattern_name: str | None
    verdict: str | None
    source: str
    plain: str = Field(
        description="这一格的白话段：该格开篇句 + 数理转述，两行以换行分隔。未核定的一格搬「笔画未核定」那一条。"
    )


class SancaiElements(BaseModel):
    tian: str
    ren: str
    di: str


class SancaiPair(BaseModel):
    pair: str = Field(description="天人 / 人地 / 天地。")
    relation: str = Field(description="生我 / 我生 / 克我 / 我克 / 比和。")
    verdict: str
    source: str


class Sancai(BaseModel):
    elements: SancaiElements
    pairs: list[SancaiPair]
    tier: str
    plain: str = Field(
        description="三才整块一段白话：开篇 + 顺侧 + 注意侧 + 档位收尾。同关系多对只说一遍（去重不是丢条目）。"
    )


class CorpusProvenance(BaseModel):
    unicode_version: str
    corpus_date: str
    size: int
    source: str


class NameProvenance(BaseModel):
    corpus: CorpusProvenance
    tables: list[ProvenanceTable]


class NameAnalysis(BaseModel):
    input: NameInput
    chars: list[NameChar]
    grids: list[NameGrid] = Field(description="固定序：天 → 人 → 地 → 外 → 总。")
    sancai: Sancai | None = Field(default=None, description="天/人/地任一缺笔画时整块不出。")
    score: ScoreValue | None
    verdict: Verdict | None = Field(
        default=None,
        description="综合结论卡片：档位词（SCORE_TIERS 五档）+ 星级 + 结论句 + 五格/三才分项 + 建议；"
        "score 为 None（笔画未核定）时整块省略，同 score 的 None 纪律。",
    )
    plain_summary: str = Field(
        description="响应级白话总论：五格数理按顺/注意两侧重排，末尾落在综合指数档位上；算不出分时不出档位句（白话层不新增判断）。"
    )
    warnings: list[str] = Field(default_factory=list, description="机器码，如 stroke_unresolved:玄。")
    provenance: NameProvenance


class NameAnalyzeRequest(BaseModel):
    """`POST /name/analyze` 的入参。

    长度用 pydantic 兜（返回 FastAPI 的 detail 形状）；是不是汉字交给引擎，因为
    非汉字要回 422 + 机器码 `not_han`，而不是 `validation_error`。
    """

    surname: str = Field(min_length=1, max_length=2, description="姓（1–2 字）。")
    given: str = Field(min_length=1, max_length=3, description="名（1–3 字）。")
    variants: dict[str, str] | None = Field(
        default=None,
        description="简体字 → 指定正体字；对该字在姓名中的每次出现都生效，多余的键忽略。",
    )
