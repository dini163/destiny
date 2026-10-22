"""/bazi/liushi/day 的契约：载荷形状、缺省日、两个域错误码，以及 §9.2 第 4 条的字段清单。

一页 = 12 格简表 + 至多 1 份详批，简表格不含 `reading`（spec §2.5）。这里钉的是"契约长
什么样"，逐格分值归 `test_bazi_liushi.py`。
"""

from typing import Any

from fastapi.testclient import TestClient

from app.schemas.bazi import BaziChart
from app.schemas.bazi_liuri import BaziLiuriResult
from app.schemas.bazi_liushi import BaziLiushiResult
from app.schemas.bazi_transit import BaziTransitResult

_DAY_ENDPOINT = "/api/v1/bazi/liushi/day"
_BASE = {
    "birth_date": "1988-02-15",
    "birth_time": "23:30",
    "calendar": "solar",
    "city": "成都",
    "latitude": 30.67,
    "longitude": 104.07,
    "gender": "male",
    "apply_true_solar_time": True,
    "name": "示例",
}


def _post(client: TestClient, payload: dict[str, object]) -> Any:
    """域错误的两条路径都从这一处走：`reference_date` 固定，缺省日才有唯一答案可断。"""
    return client.post(_DAY_ENDPOINT, json={**_BASE, "reference_date": "2028-01-20", **payload})


def _error(client: TestClient, payload: dict[str, object]) -> dict[str, object]:
    """域错误的那半边信封；缺 `error` 键时直接判红，而不是回一个 None。"""
    response = _post(client, payload)
    assert response.status_code == 422, response.json()
    body = response.json()
    assert "error" in body, body
    return body["error"]


def test_the_day_endpoint_returns_the_declared_model(client: TestClient) -> None:
    """载荷原样过一遍 schema 的往返：字段少一个、多一个、形状换了都在这里红。"""
    response = _post(client, {"solar_date": "2028-01-26", "focus_hour_zhi": "辰"})
    assert response.status_code == 200, response.json()
    parsed = BaziLiushiResult.model_validate(response.json())
    assert parsed == BaziLiushiResult.model_validate(parsed.model_dump())
    assert len(parsed.hours) == 12 and parsed.focused is not None
    assert parsed.focused.zhi == "辰"


def test_an_absent_day_falls_back_to_the_reference_segment(client: TestClient) -> None:
    body = _post(client, {}).json()
    assert (body["solar_date"], body["day_ganzhi"], body["month_ganzhi"], body["year"]) == (
        "2028-01-20",
        "甲辰",
        "癸丑",
        2027,
    )
    assert body["focused"] is None and len(body["hours"]) == 12


def test_an_unknown_hour_branch_answers_with_a_machine_code(client: TestClient) -> None:
    """`supported` 是一整串十二支而不是数组：`contextFacts` 只渲染数字与非空字符串（决策 6）。"""
    assert _error(client, {"solar_date": "2028-01-26", "focus_hour_zhi": "十三"}) == {
        "code": "liushi_hour_out_of_day",
        "message": "「十三」不是十二时辰之一，取子丑寅卯辰巳午未申酉戌亥。",
        "context": {"requested": "十三", "supported": "子丑寅卯辰巳午未申酉戌亥"},
    }


def test_a_date_before_the_luck_window_answers_with_a_machine_code(client: TestClient) -> None:
    assert _error(client, {"solar_date": "1980-06-01"}) == {
        "code": "liushi_date_unsupported",
        "message": "1980-06-01 所在的节气月推不出：本命盘可推年份 1988—2083。",
        "context": {"requested": "1980-06-01", "supported_from": 1988, "supported_to": 2083},
    }


def test_a_request_without_gender_is_a_pydantic_422_not_a_domain_422(client: TestClient) -> None:
    """两类 422 的分界同岁运、流日页：字段没填走 FastAPI 的 `detail`，没有 `error`，也就没有机器码。"""
    payload = {key: value for key, value in _BASE.items() if key != "gender"}
    response = client.post(_DAY_ENDPOINT, json=payload)
    assert response.status_code == 422
    body = response.json()
    assert "error" not in body
    assert {item["loc"][-1] for item in body["detail"]} == {"gender"}


def test_a_turned_off_correction_leaves_true_solar_time_null(client: TestClient) -> None:
    body = _post(client, {"apply_true_solar_time": False}).json()
    assert body["true_solar_time"] is None and body["tst_applied"] is False


def test_three_transit_schemas_carry_their_own_field_lists() -> None:
    """§9.2 第 4 条：三份响应的字段清单逐字钉死，加字段必须在这里显式认一次。

    不抽公共基类（spec §7.3 的决定），代价就是三份清单会各自漂移；这条测试是那份代价的
    收款凭证。命局摘要那九件同名同序，是唯一允许重复的一段。
    """
    nine = [
        "four_pillars", "pillars", "day_master", "day_master_element", "favorable_elements",
        "unfavorable_elements", "true_solar_time", "tst_applied", "longitude",
    ]
    assert list(BaziChart.model_fields) == [
        "name", "standard_datetime", "calendar", "true_solar_time", "tst_applied",
        "tst_offset_minutes", "longitude", "lunar_date", "four_pillars", "pillars", "zodiac",
        "day_master", "day_master_element", "ming_gong", "ming_gong_nayin", "tai_yuan",
        "tai_yuan_nayin", "wuxing", "missing_elements", "analysis", "dayun_direction",
        "dayun_start_solar", "dayun", "current_liunian", "geju", "yongshen", "shensha",
        "ten_god_readings", "relations", "branch_groups", "hidden_stem_ledger",
        "dayun_current", "interpretation", "provenance", "engine",
    ]
    assert list(BaziTransitResult.model_fields) == [
        *nine, "start_year", "end_year", "focus_year", "dayun_covered", "years", "plain",
        "verdict", "provenance",
    ]
    assert list(BaziLiuriResult.model_fields) == [
        *nine, "anchor_date", "year", "year_ganzhi", "year_age", "dayun_index", "dayun_ganzhi",
        "month_index", "month_in_chinese", "month_ganzhi", "month_start_solar",
        "month_end_solar", "month_score", "month_fired", "days", "focused", "plain",
        "verdict", "provenance",
    ]
    assert list(BaziLiushiResult.model_fields) == [
        *nine, "solar_date", "weekday", "lunar_day", "day_ganzhi", "year", "year_ganzhi",
        "year_age", "dayun_index", "dayun_ganzhi", "month_index", "month_in_chinese",
        "month_ganzhi", "month_start_solar", "month_end_solar", "day_score", "day_fired",
        "day_almanac", "hours", "focused", "plain", "verdict", "provenance",
    ]
