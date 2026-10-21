"""Wire types for the six-dimension reading layer (spec §6.6, §7)."""

from pydantic import BaseModel, Field

from app.schemas.common import Verdict
from app.schemas.scoring import ScoreValue


class DimensionReading(BaseModel):
    dimension: str = Field(description="事业 | 财运 | 婚姻 | 健康 | 学业 | 人际。")
    score: ScoreValue = Field(description="0-100 档位分 + 命中因子账本，缺一即视为伪造。")
    strengths: list[str] = Field(default_factory=list, description="正向因子的 label，按命中序。")
    cautions: list[str] = Field(default_factory=list, description="负向因子的 label，按命中序。")
    narrative: str = Field(description="命中因子 reading 的「；」拼接，末尾一个「。」，不现编句子。")
    plain: str = Field(
        description="白话长文：开篇句 + 命中因子逐条转述 + 档位收尾句，段间以换行分隔。"
    )
    source: str


class BaziInterpretation(BaseModel):
    six_dimensions: list[DimensionReading]
    summary: str = Field(description="六维档位复述（如「事业顺、财运平…」），不含额外判断。")
    plain_summary: str = Field(
        description="六维总论（结论卡片 headline 同串）：由 `PLAIN_SUMMARY_FRAME` 套入档位与"
        "六维复述而成，结论先行、明确好坏（2026-10-21 verdict-card spec §4）。"
    )
    verdict: Verdict = Field(
        description="结论卡片：档位词 + 星级 + 结论句 + 分项要点 + 一句建议，"
        "档位从六维账本均值派生（`app/engines/verdict.py`）。"
    )
