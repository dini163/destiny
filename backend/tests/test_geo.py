"""Unit tests for city geocoding (``app.solar.geo``)."""

import pytest

from app.core.errors import InvalidBirthDataError
from app.solar.geo import resolve_coordinates, resolve_longitude, search_cities

# The snapshot is regenerated from DataV / GeoNames (see scripts/build_cities.py), so
# exact digits shift between refreshes. 0.01° (~1 km) still pins the right city.
APPROX = 0.01


def test_search_cities_matches_exact_name() -> None:
    results = search_cities("北京")
    assert results
    assert results[0].name == "北京"
    assert results[0].latitude == pytest.approx(39.905, abs=APPROX)
    assert results[0].longitude == pytest.approx(116.405, abs=APPROX)


def test_search_cities_matches_substring() -> None:
    names = {city.name for city in search_cities("京")}
    assert {"北京", "南京"} <= names


def test_search_cities_empty_query_returns_default_page() -> None:
    results = search_cities("")
    assert 0 < len(results) <= 10


def test_search_cities_respects_limit() -> None:
    assert len(search_cities("", limit=3)) == 3


def test_resolve_coordinates_prefers_explicit_values() -> None:
    assert resolve_coordinates(None, 30.5, 114.3) == (30.5, 114.3)


def test_resolve_coordinates_geocodes_city_name() -> None:
    latitude, longitude = resolve_coordinates("上海", None, None)
    assert latitude == pytest.approx(31.2317, abs=APPROX)
    assert longitude == pytest.approx(121.4726, abs=APPROX)


def test_resolve_coordinates_unknown_city_raises() -> None:
    with pytest.raises(InvalidBirthDataError):
        resolve_coordinates("火星市", None, None)


def test_resolve_coordinates_without_location_raises() -> None:
    with pytest.raises(InvalidBirthDataError):
        resolve_coordinates(None, None, None)


def test_resolve_longitude_prefers_explicit_value() -> None:
    assert resolve_longitude(None, 104.1) == 104.1


def test_resolve_longitude_geocodes_city_name() -> None:
    assert resolve_longitude("成都", None) == pytest.approx(104.0657, abs=APPROX)


def test_snapshot_covers_every_prefecture_level_city() -> None:
    """A 地级 seat outside the original curated list must resolve, not just the capitals."""
    for name, latitude, longitude in (("佛山", 23.0288, 113.1227), ("延吉", 42.907, 129.5158)):
        assert resolve_coordinates(name, None, None) == pytest.approx((latitude, longitude), abs=APPROX)


def test_resolve_longitude_without_location_raises() -> None:
    with pytest.raises(InvalidBirthDataError):
        resolve_longitude(None, None)
