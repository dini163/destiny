"""Tarot spread HTTP adapter (thin layer over the draw engine)."""

from fastapi import APIRouter

from app.engines.tarot import draw_spread
from app.schemas.tarot import TarotSpreadRequest, TarotSpreadResponse

router = APIRouter(prefix="/tarot")


@router.post("/spread", response_model=TarotSpreadResponse, summary="Draw and interpret a tarot spread")
async def tarot_spread(request: TarotSpreadRequest) -> TarotSpreadResponse:
    """Draw cards for a chosen spread using a cryptographically secure shuffle.

    Each position is filled by a unique card and oriented upright or reversed
    (when ``allow_reversed``); the response carries the position meanings and a
    synthesis composed from the real card interpretations.
    """
    return draw_spread(
        spread_id=request.spread_id,
        allow_reversed=request.allow_reversed,
        question=request.question,
    )
