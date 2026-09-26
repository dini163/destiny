"""西洋合盘 (Western Synastry & Composite) HTTP adapter — thin layer over the engine."""

from fastapi import APIRouter

from app.core.config import get_settings
from app.engines.synastry import compute_synastry
from app.schemas.synastry import SynastryChart, SynastryRequest

router = APIRouter(prefix="/synastry")


@router.post(
    "/chart",
    response_model=SynastryChart,
    summary="Compare two natal charts (synastry, composite, compatibility score)",
)
async def synastry_chart(request: SynastryRequest) -> SynastryChart:
    """Build the synastry aspects, composite midpoint chart and 相契度 score for two people.

    Each person's location is resolved from a city or explicit latitude/longitude inside the
    engine (as for the bazi 合婚 two-person endpoint); both are required because the ascendant
    and house cusps feed the synastry angles and the composite alike.
    """
    settings = get_settings()
    return compute_synastry(
        person_a=request.person_a,
        person_b=request.person_b,
        house_system=request.house_system,
        ephemeris_path=settings.sweph_ephe_path or None,
    )
