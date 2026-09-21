"""姓名学五格剖象 HTTP 适配器（薄层：只做请求到引擎的映射）。"""

from fastapi import APIRouter

from app.engines.name_numerology import analyze_name
from app.schemas.name import NameAnalysis, NameAnalyzeRequest

router = APIRouter(prefix="/name")


@router.post("/analyze", response_model=NameAnalysis, summary="Derive the five-grid name analysis")
async def name_analyze(request: NameAnalyzeRequest) -> NameAnalysis:
    """核定康熙笔画并推出五格、三才与综合气象指数。

    笔画来自固化的 Unihan 推导语料；一简对多繁未指定时返回 422 + 候选列表，
    本端点不猜正体（spec 决策六）。语料范围外的字不报错：受影响的那几格如实为
    null，三才与指数整块不出（spec 决策八）。
    """
    return analyze_name(
        surname=request.surname,
        given=request.given,
        variants=request.variants,
    )
