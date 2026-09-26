"""行运推运 (Transit & Progression) HTTP adapter — thin layer over the engine."""

from fastapi import APIRouter

from app.core.config import get_settings
from app.engines.transit import compute_transits
from app.schemas.transit import TransitChart, TransitRequest
from app.solar.geo import resolve_coordinates

router = APIRouter(prefix="/transit")


@router.post("/chart", response_model=TransitChart, summary="Project transits, progressions and solar arc onto a natal chart")
async def transit_chart(request: TransitRequest) -> TransitChart:
    """Layer transits, secondary progressions and solar arc over a natal chart.

    Both latitude and longitude are required (directly or via a city) because the
    natal ascendant and house cusps depend on the full geographic position; the
    moving layers reuse that same natal base.
    """
    latitude, longitude = resolve_coordinates(request.city, request.latitude, request.longitude)
    settings = get_settings()
    return compute_transits(
        birth_date=request.birth_date,
        birth_time=request.birth_time,
        latitude=latitude,
        longitude=longitude,
        utc_offset_hours=request.utc_offset_hours,
        house_system=request.house_system,
        target_date=request.target_date,
        ephemeris_path=settings.sweph_ephe_path or None,
    )
