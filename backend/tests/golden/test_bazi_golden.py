"""Golden tests for the BaZi engine, pinned to authoritative lunar-python output.

Note on PRD Appendix B case 1
-----------------------------
The PRD lists ``Solar(1988,2,15,23,30,0)`` -> ``戊辰 甲寅 庚戌 丁亥``. Independent
verification (Julian Day Number, and lunar-python evaluated at 12:00 to remove
the zi-hour ambiguity) shows 1988-02-15 is a **庚子** day; 庚戌 is 1988-02-25.
The PRD literal therefore has a wrong day branch: its year (戊辰), month (甲寅)
and hour (丁亥) are exactly the True-Solar-Time-corrected result at ~104.1E, but
the day is 庚子. Per PRD 10.2 the library is authoritative and ganzhi must not be
self-computed, so these tests assert the real lunar-python output and the
uncorrected-vs-TST difference the PRD acceptance criteria require.
"""

from datetime import date, time

import pytest
from fastapi.testclient import TestClient

from app.engines.bazi import compute_bazi_chart
from app.schemas.common import Gender

BIRTH_DATE = date(1988, 2, 15)
BIRTH_TIME = time(23, 30)
CHENGDU_LONGITUDE = 104.1  # PRD 7.4 reference longitude for this case


def _chart(gender: Gender | None = Gender.MALE, *, apply_tst: bool = True):
    return compute_bazi_chart(
        birth_date=BIRTH_DATE,
        birth_time=BIRTH_TIME,
        longitude=CHENGDU_LONGITUDE,
        gender=gender,
        apply_true_solar_time=apply_tst,
    )


def test_uncorrected_chart_uses_standard_time_hour_pillar() -> None:
    chart = _chart(apply_tst=False)
    assert chart.four_pillars == "戊辰 甲寅 庚子 戊子"
    assert chart.tst_applied is False
    assert chart.true_solar_time is None
    assert chart.pillars[3].ganzhi == "戊子"  # 子时 (23:00-01:00)


def test_true_solar_time_shifts_hour_pillar() -> None:
    chart = _chart(apply_tst=True)
    # A -77.84 min correction moves 23:30 (子时) back to ~22:12 (亥时).
    assert chart.four_pillars == "戊辰 甲寅 庚子 丁亥"
    assert chart.tst_applied is True
    assert chart.tst_offset_minutes == pytest.approx(-77.84, abs=0.01)
    assert chart.pillars[3].ganzhi == "丁亥"
    # PRD 10.2: the corrected and uncorrected hour pillars must differ.
    assert _chart(apply_tst=False).pillars[3].ganzhi != chart.pillars[3].ganzhi


def test_day_pillar_day_master_and_zodiac() -> None:
    chart = _chart()
    assert chart.pillars[2].ganzhi == "庚子"  # 1988-02-15 is a 庚子 day (verified)
    assert chart.day_master == "庚"
    assert chart.day_master_element == "金"
    assert chart.zodiac == "龙"  # by Start-of-Spring, consistent with year branch 辰


def test_wuxing_count_is_the_eight_primary_characters() -> None:
    """The distribution card counts the eight characters, never hidden stems.

    Weights and hidden-stem roots belong to the strength ledger; a bare headcount
    stays exactly what its label says, so an already-integrated page cannot
    silently change meaning. Pinned here because the strength engine is being
    rebuilt on top of the same pillars.
    """
    chart = _chart()
    counts = {item.element: item.count for item in chart.wuxing}
    assert sum(counts.values()) == 8
    assert counts == {"木": 2, "火": 1, "土": 2, "金": 1, "水": 2}
    assert chart.missing_elements == []


def test_day_master_strength_is_weak_metal() -> None:
    """Reference chart: 庚金 born in 寅月 is 囚 → 身弱, supported by 土(印) and 金(比劫)."""
    analysis = _chart().analysis
    assert analysis.level == "weak"
    assert analysis.label == "身弱"
    assert analysis.strength.value == pytest.approx(25.85, abs=0.01)
    assert analysis.strength.tier == "身弱"
    assert analysis.borderline is False
    # 通关 does not fire here (1.70/2.20 = 0.77 < 0.80), so the classical 土金 answer stands.
    assert set(analysis.favorable_elements) == {"土", "金"}
    assert "木" in analysis.unfavorable_elements
    assert "火" not in analysis.favorable_elements


def test_male_dayun_sequence_is_forward() -> None:
    chart = _chart(gender=Gender.MALE)
    assert chart.dayun_direction == "forward"
    assert len(chart.dayun) == 10
    assert chart.dayun[0].ganzhi == ""  # childhood span before the first pillar
    assert chart.dayun[1].ganzhi == "乙卯"
    assert chart.dayun[1].start_year == 1994


def test_dayun_direction_flips_with_gender() -> None:
    male = _chart(gender=Gender.MALE, apply_tst=False)
    female = _chart(gender=Gender.FEMALE, apply_tst=False)
    assert male.dayun_direction != female.dayun_direction


def test_dayun_absent_without_gender() -> None:
    chart = _chart(gender=None, apply_tst=False)
    assert chart.dayun == []
    assert chart.dayun_direction is None


def test_bazi_natal_endpoint_returns_corrected_chart(client: TestClient) -> None:
    response = client.post(
        "/api/v1/bazi/natal",
        json={
            "birth_date": "1988-02-15",
            "birth_time": "23:30",
            "calendar": "solar",
            "longitude": 104.1,
            "gender": "male",
            "apply_true_solar_time": True,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["four_pillars"] == "戊辰 甲寅 庚子 丁亥"
    assert body["day_master"] == "庚"
    assert body["zodiac"] == "龙"
    assert body["pillars"][3]["nayin"]
    assert body["engine"] == "lunar-python"


def test_bazi_natal_requires_location_when_tst_enabled(client: TestClient) -> None:
    response = client.post(
        "/api/v1/bazi/natal",
        json={
            "birth_date": "1988-02-15",
            "birth_time": "23:30",
            "gender": "male",
            "apply_true_solar_time": True,
        },
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_birth_data"


def test_bazi_natal_is_reproducible_for_a_fixed_reference_date(client: TestClient) -> None:
    body = {"birth_date": "1988-02-15", "birth_time": "23:30", "gender": "male",
            "longitude": 104.1, "reference_date": "2026-09-20", "name": "示例甲"}
    first = client.post("/api/v1/bazi/natal", json=body).json()
    assert first == client.post("/api/v1/bazi/natal", json=body).json()   # 同请求逐字节相等
    assert first["provenance"]["reference_date"] == "2026-09-20"
    assert first["name"] == "示例甲"
    assert [step["index"] for step in first["dayun"] if step["is_current"]] == [
        first["dayun_current"]["index"]
    ]


def test_bazi_natal_without_reference_date_falls_back_to_today(client: TestClient) -> None:
    """缺省口径必须可见：回显当日而不是留空，否则响应无法复现。"""
    payload = client.post(
        "/api/v1/bazi/natal",
        json={"birth_date": "1988-02-15", "birth_time": "23:30", "gender": "male",
              "longitude": 104.1},
    ).json()
    assert payload["provenance"]["reference_date"] == date.today().isoformat()
    assert payload["name"] is None
