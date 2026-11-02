"""Reader promises checked against actual calendars and engine factors."""

from datetime import date, timedelta

from fastapi.testclient import TestClient

from app.engines.report_calendar import rolling_months, shift_month
from app.main import app
from app.schemas.report import ReportTimeRequest


def request(start):
    return ReportTimeRequest(
        birth_date="1988-02-15",
        birth_time="23:30",
        city="成都",
        gender="male",
        reference_date="2026-10-01",
        start_date=start,
        start_year=2026,
        end_year=2027,
        focus_year=2026,
    )


def test_rolling_calendar_covers_civil_buckets_without_gaps_or_overlaps():
    for anchor in [date(2026, 1, 1), date(2026, 10, 31), date(2028, 2, 29)]:
        start, end, periods = rolling_months(request(anchor), date(2026, 10, 1))
        assert start == anchor
        assert end == shift_month(anchor, 12) - timedelta(days=1)
        assert len(periods) == 12
        cursor = start
        for left, right, pieces in periods:
            assert left == cursor
            for a, b, term in pieces:
                assert a == cursor
                assert (
                    date.fromisoformat(term.start_solar)
                    <= a
                    <= b
                    <= date.fromisoformat(term.end_solar)
                )
                cursor = b + timedelta(days=1)
            assert cursor == right + timedelta(days=1)
        assert cursor == end + timedelta(days=1)


def test_report_no_internal_keys_or_repeated_punctuation_and_labels_annual_context():
    with TestClient(app) as client:
        for product in ("r1", "r2", "r3"):
            response = client.get(f"/api/v1/report/{product}/sample")
            assert response.status_code == 200, response.text
            doc = response.json()
            assert "。。" not in response.text
            assert "wrap（" not in response.text and "rest（" not in response.text
            assert not doc["token"]
            if product == "r1":
                windows = next(row for row in doc["sections"] if row["id"] == "windows")
                assert "年度" in windows["title"]
            if product == "r3":
                months = next(row for row in doc["sections"] if row["id"] == "months")
                assert len(months["bullets"]) == 12
                assert all("账本" in line for line in months["bullets"])
                assert "2026-10-01" in doc["input_summary"]
                assert "2027-09-30" in doc["input_summary"]


def test_rolling_start_cannot_overflow_the_calendar():
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/report/r3/generate",
            json=request(date(9999, 12, 31)).model_dump(mode="json"),
        )
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "transit_range_unsupported"
