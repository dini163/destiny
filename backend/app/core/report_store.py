"""Fixed report delivery snapshots; raw birth inputs are deliberately not persisted.

The computation engines remain stateless. Fulfilment is a separate local SQLite
store, intended for a single host with a persistent volume and restrictive ACLs.
"""

import hashlib
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from app.schemas.report import ReportDocument


@contextmanager
def connect(path: str):
    location = Path(path)
    location.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(location, timeout=10)
    connection.execute("PRAGMA busy_timeout=10000")
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("""CREATE TABLE IF NOT EXISTS report_deliveries (
        delivery_id TEXT PRIMARY KEY, product TEXT NOT NULL,
        token_hash TEXT NOT NULL, expires_at TEXT NOT NULL,
        revoked INTEGER NOT NULL DEFAULT 0, document TEXT NOT NULL
    )""")
    try:
        with connection:
            yield connection
    finally:
        connection.close()


def save_delivery(path: str, document: ReportDocument) -> ReportDocument:
    delivery_id = secrets.token_hex(16)
    snapshot = document.model_copy(
        update={"order_id": delivery_id, "token": secrets.token_urlsafe(32)}
    )
    digest = hashlib.sha256(snapshot.token.encode()).hexdigest()
    with connect(path) as connection:
        connection.execute(
            "INSERT INTO report_deliveries VALUES (?, ?, ?, ?, 0, ?)",
            (
                delivery_id,
                snapshot.product,
                digest,
                snapshot.expires_at,
                snapshot.model_copy(update={"token": ""}).model_dump_json(),
            ),
        )
    return snapshot


def load_delivery(path: str, product: str, delivery_id: str, token: str) -> ReportDocument | None:
    with connect(path) as connection:
        row = connection.execute(
            "SELECT token_hash, expires_at, revoked, document FROM report_deliveries WHERE delivery_id=? AND product=?",
            (delivery_id, product),
        ).fetchone()
    if (
        row is None
        or row[2]
        or not secrets.compare_digest(row[0], hashlib.sha256(token.encode()).hexdigest())
    ):
        return None
    expires = datetime.fromisoformat(row[1])
    if expires <= datetime.now(timezone.utc):
        return None
    return ReportDocument.model_validate_json(row[3]).model_copy(update={"token": token})


def revoke_delivery(path: str, delivery_id: str) -> bool:
    with connect(path) as connection:
        return (
            connection.execute(
                "UPDATE report_deliveries SET revoked=1 WHERE delivery_id=?", (delivery_id,)
            ).rowcount
            == 1
        )


def purge_deliveries(path: str) -> int:
    with connect(path) as connection:
        connection.execute("PRAGMA secure_delete=ON")
        removed = connection.execute(
            "DELETE FROM report_deliveries WHERE revoked=1 OR expires_at<=?",
            (datetime.now(timezone.utc).isoformat(),),
        ).rowcount
    return removed
