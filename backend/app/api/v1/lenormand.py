"""雷诺曼 (Lenormand) HTTP adapter (thin layer over the draw engine)."""

from fastapi import APIRouter

from app.engines.lenormand import draw_lenormand
from app.schemas.lenormand import LenormandReading, LenormandRequest

router = APIRouter(prefix="/lenormand")


@router.post("/draw", response_model=LenormandReading, summary="Draw and read a Lenormand spread")
async def lenormand_draw(request: LenormandRequest) -> LenormandReading:
    """以密码学安全洗牌抽发所选牌阵（单张 / 三张 / 五行 / 九宫 / 大桌全景）。

    Each position is filled by a unique card, always upright; the response carries
    the position meanings, the 组合直读 pairs, the optional 指示牌 placement and a
    synthesis composed from the real card interpretations.
    """
    return draw_lenormand(
        spread_id=request.spread_id,
        question=request.question,
        significator=request.significator,
    )
