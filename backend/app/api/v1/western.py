"""Western natal-chart HTTP adapter (thin layer over the computation engine)."""

from fastapi import APIRouter

from app.core.config import get_settings
from app.engines.western import compute_western_chart
from app.schemas.western import WesternChart, WesternNatalRequest
from app.solar.geo import resolve_coordinates

router = APIRouter(prefix="/western")


@router.post("/natal", response_model=WesternChart, summary="Compute a Western natal chart")
async def western_natal(request: WesternNatalRequest) -> WesternChart:
    """Chart planets, houses, angles and aspects for a birth moment and place.

    Both latitude and longitude are required (directly or via a city) because the
    ascendant and house cusps depend on the full geographic position.
    """
    latitude, longitude = resolve_coordinates(request.city, request.latitude, request.longitude)
    settings = get_settings()
    return compute_western_chart(
        birth_date=request.birth_date,
        birth_time=request.birth_time,
        latitude=latitude,
        longitude=longitude,
        utc_offset_hours=request.utc_offset_hours,
        house_system=request.house_system,
        ephemeris_path=settings.sweph_ephe_path or None,
    )
