"""奇门遁甲 (Qi Men Dun Jia) HTTP adapter (thin layer over the chart engine)."""

from datetime import datetime

from fastapi import APIRouter

from app.engines.qimen import compute_qimen_chart
from app.schemas.qimen import QimenChart, QimenRequest

router = APIRouter(prefix="/qimen")


@router.post("/chart", response_model=QimenChart, summary="Cast a Qi Men Dun Jia board")
async def qimen_chart(request: QimenRequest) -> QimenChart:
    """起一局时家奇门：定阴阳遁与局数，布三奇六仪地盘，转九星八门八神入洛书九宫。

    The cast moment defaults to now; it supplies the 年月日时干支 — the 节气 + 日干支符头
    fix the 局, and the 时辰旬首 fixes the 值符值使. Everything is derived deterministically
    from the classical 安盘 tables; no position is invented at runtime.
    """
    return compute_qimen_chart(
        cast_time=request.cast_time or datetime.now(),
        question=request.question,
    )
