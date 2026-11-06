"""Zhouyi / Liuyao casting HTTP adapter (thin layer over the derivation engine)."""

from datetime import datetime

from fastapi import APIRouter

from app.content.zhouyi_yangzhai import get_yangzhai_hexagram_meaning
from app.engines.zhouyi import cast_hexagram
from app.schemas.zhouyi import (
    ZhouyiCast,
    ZhouyiCastRequest,
    ZhouyiYangzhaiRequest,
    ZhouyiYangzhaiResponse,
)

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


@router.post(
    "/yangzhai",
    response_model=ZhouyiYangzhaiResponse,
    summary="周易卦象与阳宅后天八卦化命方位取象解析",
)
async def zhouyi_yangzhai(request: ZhouyiYangzhaiRequest) -> ZhouyiYangzhaiResponse:
    """解析周易六十四卦对应的文王后天八卦家庭角色与居所方位化命取象。"""
    meaning = get_yangzhai_hexagram_meaning(request.hexagram_name)
    return ZhouyiYangzhaiResponse(hexagram_name=request.hexagram_name, meaning=meaning)
