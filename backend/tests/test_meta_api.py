"""API tests for the meta router (city search + True Solar Time preview)."""

from fastapi.testclient import TestClient


def test_health_probe(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_cities_endpoint_returns_coordinates(client: TestClient) -> None:
    response = client.get("/api/v1/meta/cities", params={"q": "上海"})
    assert response.status_code == 200
    payload = response.json()
    assert payload
    assert payload[0]["name"] == "上海"
    assert set(payload[0]) == {"name", "province", "latitude", "longitude"}


def test_true_solar_time_endpoint_matches_manual_offset(client: TestClient) -> None:
    response = client.get(
        "/api/v1/meta/true-solar-time",
        params={"date": "1988-02-15", "time": "23:30", "longitude": 116.4074},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["standard_time"] == "1988-02-15 23:30"
    # Beijing longitude offset (~-14.4 min) plus mid-February EOT (~-14 min).
    assert -30.0 < body["offset_minutes"] < -25.0
    assert body["true_solar_time"].startswith("1988-02-15 23:0")
    assert body["longitude"] == 116.4074
