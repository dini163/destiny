"""Meta endpoints: city geocoding and True Solar Time preview."""

from datetime import datetime

from fastapi import APIRouter, Query

from app.schemas.common import TrueSolarTimeResponse
from app.solar import true_solar_time as tst_module
from app.solar.geo import search_cities

router = APIRouter(prefix="/meta")


@router.get("/cities", summary="Search geocoded cities")
async def cities(q: str = Query(default="", description="City name fragment")) -> list[dict]:
    """Return matching cities with coordinates for the location picker."""
    return [
        {"name": c.name, "province": c.province, "latitude": c.latitude, "longitude": c.longitude}
        for c in search_cities(q)
    ]


@router.get("/true-solar-time", summary="Preview True Solar Time correction", response_model=TrueSolarTimeResponse)
async def true_solar_time(
    date: str = Query(description="ISO date, e.g. 1988-02-15"),
    time: str = Query(description="HH:MM local standard time, e.g. 23:30"),
    longitude: float = Query(description="Longitude in degrees east"),
) -> TrueSolarTimeResponse:
    """Compute the True Solar Time for a standard-time moment and longitude."""
    standard_dt = datetime.fromisoformat(f"{date}T{time}:00")
    corrected = tst_module.true_solar_time(standard_dt, longitude)
    return TrueSolarTimeResponse(
        standard_time=standard_dt.strftime("%Y-%m-%d %H:%M"),
        true_solar_time=corrected.strftime("%Y-%m-%d %H:%M"),
        offset_minutes=round(tst_module.true_solar_offset_minutes(standard_dt, longitude), 2),
        longitude=longitude,
    )
