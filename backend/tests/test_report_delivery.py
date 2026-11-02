"""Real report snapshots and authority boundaries; no generated response is hand-built."""

import os
import secrets
import sqlite3
from datetime import date, datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.core.report_store import load_delivery, purge_deliveries, revoke_delivery, save_delivery
from app.engines.report_composer import compose_report
from app.main import app
from app.schemas.bazi import BaziNatalRequest


def natal():
    return BaziNatalRequest(
        birth_date="1988-02-15",
        birth_time="23:30",
        city="成都",
        gender="male",
        reference_date=date(2026, 10, 1),
    )


def test_delivery_snapshot_is_fixed_and_individually_revocable(tmp_path):
    request = natal()
    doc = compose_report("r2", request, request.reference_date)
    path = str(tmp_path / "delivery.sqlite3")
    first, second = save_delivery(path, doc), save_delivery(path, doc)
    with sqlite3.connect(path) as connection:
        raw = connection.execute(
            "SELECT document FROM report_deliveries WHERE delivery_id=?", (first.order_id,)
        ).fetchone()[0]
    assert first.token not in raw
    assert first.order_id != second.order_id
    assert load_delivery(path, "r2", first.order_id, first.token) == first
    assert load_delivery(path, "r2", first.order_id, "invalid") is None
    assert load_delivery(path, "r1", first.order_id, first.token) is None
    assert revoke_delivery(path, first.order_id)
    assert load_delivery(path, "r2", first.order_id, first.token) is None
    assert load_delivery(path, "r2", second.order_id, second.token) == second
    assert purge_deliveries(path) == 1


def test_expired_snapshot_cannot_be_retrieved(tmp_path):
    request = natal()
    doc = compose_report("r2", request, request.reference_date)
    doc.expires_at = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    path = str(tmp_path / "delivery.sqlite3")
    issued = save_delivery(path, doc)
    assert load_delivery(path, "r2", issued.order_id, issued.token) is None
    assert purge_deliveries(path) == 1


def test_production_requires_manual_issue_but_allows_bearer_fetch(tmp_path):
    settings = Settings(
        _env_file=None,
        app_environment="production",
        report_secret=secrets.token_hex(32),
        report_operator_key=secrets.token_hex(32),
        report_store_path=str(tmp_path / "delivery.sqlite3"),
    )
    values = {
        "APP_ENVIRONMENT": settings.app_environment,
        "REPORT_SECRET": settings.report_secret,
        "REPORT_OPERATOR_KEY": settings.report_operator_key,
        "REPORT_STORE_PATH": settings.report_store_path,
    }
    previous = {key: os.environ.get(key) for key in values}
    os.environ.update(values)
    get_settings.cache_clear()
    try:
        with TestClient(app) as client:
            payload = natal().model_dump(mode="json")
            assert client.post("/api/v1/report/r2/generate", json=payload).status_code == 403
            assert client.post("/api/v1/report/r2/issue", json=payload).status_code == 403
            issued = client.post(
                "/api/v1/report/r2/issue",
                json=payload,
                headers={"X-Report-Operator-Key": settings.report_operator_key},
            )
            assert issued.status_code == 200, issued.text
            doc = issued.json()
            fetched = client.post(
                f"/api/v1/report/r2/delivery/{doc['order_id']}", json={"token": doc["token"]}
            )
            assert fetched.status_code == 200
            assert fetched.json() == doc
            assert (
                client.post(
                    f"/api/v1/report/delivery/{doc['order_id']}/revoke",
                    headers={"X-Report-Operator-Key": settings.report_operator_key},
                ).status_code
                == 200
            )
            assert (
                client.post(
                    f"/api/v1/report/r2/delivery/{doc['order_id']}", json={"token": doc["token"]}
                ).status_code
                == 404
            )
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        get_settings.cache_clear()
