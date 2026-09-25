"""Norse rune cast HTTP adapter (thin layer over the draw engine).

The body only forwards the request, matching ``api/v1/tarot.py``: anything that
could be validated here is already validated by ``RuneCastRequest``, and
anything that could be interpreted is already in the corpus. An unknown
``spread_id`` surfaces as ``UnsupportedMethodError`` from the engine, which the
app-wide handler turns into the shared 422 error shape -- the same path tarot
takes, so the two systems cannot drift into two error formats.
"""

from fastapi import APIRouter

from app.engines.runes import draw
from app.schemas.runes import RuneCastRequest, RuneCastResponse

router = APIRouter(prefix="/runes")


@router.post("/cast", response_model=RuneCastResponse, summary="Cast and read a rune spread")
async def cast_runes(request: RuneCastRequest) -> RuneCastResponse:
    """Draw stones for a chosen spread using a cryptographically secure draw.

    Each position is filled by a unique stone, oriented upright or reversed only
    where a reversal is geometrically meaningful for that glyph. The response
    carries the position meanings, a synthesis composed from the real corpus
    readings, the group counts, and the full 24+1 codex the drawer renders from.
    It carries no score and no percentage: a cast takes neither a birth date nor
    a location, so there is nothing such a figure could be computed from.
    """
    return draw(
        spread_id=request.spread_id,
        include_wyrd=request.include_wyrd,
        allow_reversed=request.allow_reversed,
        question=request.question,
    )
