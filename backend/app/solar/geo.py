"""City -> coordinate lookup backed by a bundled GeoNames-derived snapshot."""

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from app.core.errors import InvalidBirthDataError

_CITIES_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "cities.json"


@dataclass(frozen=True)
class City:
    """A geocoded city used for True Solar Time and ascendant computation."""

    name: str
    province: str
    latitude: float
    longitude: float


@lru_cache(maxsize=1)
def _load_cities() -> tuple[City, ...]:
    with _CITIES_PATH.open(encoding="utf-8") as handle:
        raw = json.load(handle)
    return tuple(
        City(name=item["name"], province=item["province"], latitude=item["lat"], longitude=item["lon"])
        for item in raw
    )


def search_cities(query: str, limit: int = 10) -> list[City]:
    """Return cities whose name contains the query (case-insensitive)."""
    needle = query.strip().lower()
    if not needle:
        return list(_load_cities()[:limit])
    matches = [c for c in _load_cities() if needle in c.name.lower() or needle in c.province.lower()]
    return matches[:limit]


def resolve_coordinates(city: str | None, latitude: float | None, longitude: float | None) -> tuple[float, float]:
    """Resolve (latitude, longitude) from explicit coords or a city name.

    Explicit coordinates win; otherwise the city name is geocoded. Raises
    :class:`InvalidBirthDataError` when neither yields a usable location.
    """
    if latitude is not None and longitude is not None:
        return latitude, longitude
    if city:
        matches = search_cities(city, limit=1)
        if matches:
            return matches[0].latitude, matches[0].longitude
        raise InvalidBirthDataError(f"Unknown city: {city}. Provide latitude/longitude instead.")
    raise InvalidBirthDataError("Birth location is required: supply city or latitude/longitude.")
