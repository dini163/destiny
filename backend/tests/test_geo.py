"""Unit tests for city geocoding (``app.solar.geo``)."""

import pytest

from app.core.errors import InvalidBirthDataError
from app.solar.geo import resolve_coordinates, resolve_longitude, search_cities


def test_search_cities_matches_exact_name() -> None:
    results = search_cities("北京")
    assert results
    assert results[0].name == "北京"
    assert results[0].latitude == pytest.approx(39.9042)
    assert results[0].longitude == pytest.approx(116.4074)


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
    assert latitude == pytest.approx(31.2304)
    assert longitude == pytest.approx(121.4737)


def test_resolve_coordinates_unknown_city_raises() -> None:
    with pytest.raises(InvalidBirthDataError):
        resolve_coordinates("火星市", None, None)


def test_resolve_coordinates_without_location_raises() -> None:
    with pytest.raises(InvalidBirthDataError):
        resolve_coordinates(None, None, None)


def test_resolve_longitude_prefers_explicit_value() -> None:
    assert resolve_longitude(None, 104.1) == 104.1


def test_resolve_longitude_geocodes_city_name() -> None:
    assert resolve_longitude("成都", None) == pytest.approx(104.0668)


def test_resolve_longitude_without_location_raises() -> None:
    with pytest.raises(InvalidBirthDataError):
        resolve_longitude(None, None)
