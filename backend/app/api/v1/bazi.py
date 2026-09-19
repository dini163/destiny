"""BaZi natal-chart HTTP adapter (thin layer over the computation engine)."""

from datetime import date

from fastapi import APIRouter

from app.engines.bazi import compute_bazi_chart
from app.schemas.bazi import BaziChart, BaziNatalRequest
from app.solar.geo import resolve_longitude
from app.solar.true_solar_time import STANDARD_MERIDIAN_CN

router = APIRouter(prefix="/bazi")


@router.post("/natal", response_model=BaziChart, summary="Compute a BaZi natal chart")
async def bazi_natal(request: BaziNatalRequest) -> BaziChart:
    """Chart the four pillars from birth data, applying True Solar Time by default.

    A location is required when True Solar Time correction is enabled; otherwise
    the standard meridian (120E) is assumed and no correction is applied.
    """
    if request.apply_true_solar_time:
        longitude = resolve_longitude(request.city, request.longitude)
    else:
        longitude = request.longitude if request.longitude is not None else STANDARD_MERIDIAN_CN

    return compute_bazi_chart(
        birth_date=request.birth_date,
        birth_time=request.birth_time,
        calendar=request.calendar,
        longitude=longitude,
        gender=request.gender,
        apply_true_solar_time=request.apply_true_solar_time,
        reference_date=date.today(),
    )
