"""Zhouyi / Liuyao casting HTTP adapter (thin layer over the derivation engine)."""

from datetime import datetime

from fastapi import APIRouter

from app.engines.zhouyi import cast_hexagram
from app.schemas.zhouyi import ZhouyiCast, ZhouyiCastRequest

router = APIRouter(prefix="/zhouyi")


@router.post("/cast", response_model=ZhouyiCast, summary="Cast and derive a Zhouyi hexagram")
async def zhouyi_cast(request: ZhouyiCastRequest) -> ZhouyiCast:
    """Cast six lines and derive the primary, changed and nuclear hexagrams.

    The cast moment defaults to now; it fixes the day pillar (for 六神) and, for
    the ``time`` method, the lunar numbers. The primary hexagram's lines carry
    纳甲, 六亲, 六神 and 世应.
    """
    return cast_hexagram(
        method=request.method,
        manual_coins=request.manual_coins,
        question=request.question,
        cast_time=request.cast_time or datetime.now(),
    )
