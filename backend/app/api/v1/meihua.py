"""梅花易数 (Plum Blossom) HTTP adapter (thin layer over the derivation engine)."""

from datetime import datetime

from fastapi import APIRouter

from app.engines.meihua import cast_meihua
from app.schemas.meihua import MeihuaCast, MeihuaCastRequest

router = APIRouter(prefix="/meihua")


@router.post("/cast", response_model=MeihuaCast, summary="Raise and read a Plum Blossom hexagram")
async def meihua_cast(request: MeihuaCastRequest) -> MeihuaCast:
    """Raise a hexagram by 年月日时 or 报数 and read it through 体用生克.

    The cast moment defaults to now; it supplies the lunar numbers (time method /
    single-number method) and fixes the 月令 used for 卦气旺衰. The response locates
    the 体卦 / 用卦 by the moving line, reports the primary 生克 verdict, the 互卦
    (过程) and 变卦 (结局) tendencies and a transparent 吉凶指数 ledger.
    """
    return cast_meihua(
        method=request.method,
        numbers=request.numbers,
        question=request.question,
        cast_time=request.cast_time or datetime.now(),
    )
