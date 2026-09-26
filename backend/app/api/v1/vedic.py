"""吠陀占星 (Vedic / Jyotish) HTTP adapter — thin layer over the computation engine."""

from datetime import date

from fastapi import APIRouter

from app.core.config import get_settings
from app.engines.vedic import compute_vedic_chart
from app.schemas.vedic import VedicChart, VedicNatalRequest
from app.solar.geo import resolve_coordinates

router = APIRouter(prefix="/vedic")


@router.post("/natal", response_model=VedicChart, summary="Compute a Vedic (sidereal) natal chart")
async def vedic_natal(request: VedicNatalRequest) -> VedicChart:
    """Chart the nine grahas on the sidereal zodiac with their nakshatras and Vimshottari dasha.

    Both latitude and longitude are required (directly or via a city) because the
    Lagna (ascendant) — and therefore the whole-sign houses — depend on the full
    geographic position. ``target_date`` defaults to today for the live dasha marker.
    """
    latitude, longitude = resolve_coordinates(request.city, request.latitude, request.longitude)
    settings = get_settings()
    return compute_vedic_chart(
        birth_date=request.birth_date,
        birth_time=request.birth_time,
        latitude=latitude,
        longitude=longitude,
        utc_offset_hours=request.utc_offset_hours,
        target_date=request.target_date or date.today(),
        ephemeris_path=settings.sweph_ephe_path or None,
    )
