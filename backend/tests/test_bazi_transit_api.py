"""`POST /bazi/liuyue` 的端点契约（spec §7.1 / §7.2，计划 Task 11）。

这一页最要紧的一件事是**两种 422 分得开**：域错误过 `DestinyError` 的处理器，带
`{"error": {code, message, context}}`，前端拿得到机器码，于是能把"最多 10 年"渲染成
可操作提示；缺字段过 pydantic，带 `{"detail": [...]}`，机器码只有 `validation_error`。
两者状态码相同，形状不同，所以每个用例都两头都断言一次 —— 只看 status_code 的测试
放得过任何一侧。

路由名叫 `liuyue` 而载荷同时含流年区间与可选流月（spec §8.1 决策 5）：那一句话写在
adapter 的 docstring 里，这里只钉它的行为。
"""

from typing import Any

from fastapi.testclient import TestClient

from app.engines.bazi_transit import TRANSIT_MAX_YEARS
from app.schemas.bazi_transit import BaziTransitResult

_BASE: dict[str, Any] = {
    "birth_date": "1988-02-15",
    "birth_time": "23:30",
    "calendar": "solar",
    "longitude": 104.1,
    "gender": "male",
    "apply_true_solar_time": True,
    "reference_date": "2026-09-21",
}


def _post(client: TestClient, **overrides: Any) -> Any:
    return client.post("/api/v1/bazi/liuyue", json={**_BASE, **overrides})


def _error(response: Any) -> dict[str, Any]:
    """域错误的那半边信封；缺 `error` 键时直接判红，而不是回一个 None。"""
    body = response.json()
    assert "error" in body, body
    return body["error"]


def test_the_default_request_returns_five_years_with_the_natal_summary(
    client: TestClient,
) -> None:
    body = _post(client).json()
    assert body["four_pillars"] == "戊辰 甲寅 庚子 丁亥"
    assert (body["start_year"], body["end_year"], body["focus_year"]) == (2026, 2030, None)
    assert [year["year"] for year in body["years"]] == [2026, 2027, 2028, 2029, 2030]
    assert [step["ganzhi"] for step in body["dayun_covered"]] == ["戊午"]
    assert body["provenance"]["reference_date"] == "2026-09-21"


def test_a_focus_year_expands_twelve_months_for_that_year_only(client: TestClient) -> None:
    body = _post(client, focus_year=2027).json()
    months = {year["year"]: year["months"] for year in body["years"]}
    assert [month["ganzhi"] for month in months[2027]][:2] == ["壬寅", "癸卯"]  # 丁未年起壬寅（五虎遁）
    assert [year for year, value in months.items() if value is not None] == [2027]


def test_missing_gender_is_a_pydantic_422_not_a_domain_422(client: TestClient) -> None:
    """两类 422 的分界：字段没填 → `detail`，没有 `error`，前端拿不到也不该拿到机器码。"""
    payload = {key: value for key, value in _BASE.items() if key != "gender"}
    body = client.post("/api/v1/bazi/liuyue", json=payload).json()
    assert "error" not in body
    assert {item["loc"][-1] for item in body["detail"]} == {"gender"}


def test_a_reversed_span_reports_its_own_code_and_both_years(client: TestClient) -> None:
    error = _error(_post(client, start_year=2030, end_year=2029))
    assert error["code"] == "transit_range_reversed"
    assert error["context"] == {"start_year": 2030, "end_year": 2029}


def test_a_span_over_the_cap_reports_the_cap_and_what_was_asked(client: TestClient) -> None:
    """上限是机器可读的：11 年请求里的 `requested` 与表里的 `max_years` 一起给出。"""
    error = _error(_post(client, start_year=2026, end_year=2026 + TRANSIT_MAX_YEARS))
    assert error["code"] == "transit_range_too_wide"
    assert error["context"] == {"max_years": TRANSIT_MAX_YEARS, "requested": TRANSIT_MAX_YEARS + 1}


def test_a_span_before_the_chart_reports_the_supported_window(client: TestClient) -> None:
    error = _error(_post(client, start_year=1900, end_year=1904))
    assert error["code"] == "transit_range_unsupported"
    assert error["context"]["supported_from"] == 1988
    assert error["context"]["supported_to"] == 2083


def test_a_focus_year_outside_the_span_is_its_own_fourth_code(client: TestClient) -> None:
    error = _error(_post(client, start_year=2026, end_year=2030, focus_year=2040))
    assert error["code"] == "transit_focus_out_of_range"
    assert error["context"] == {"focus_year": 2040, "start_year": 2026, "end_year": 2030}


def test_an_unknown_city_with_the_correction_on_stays_a_birth_data_error(
    client: TestClient,
) -> None:
    """`resolve_longitude` 抛的那一类原样透传，不被区间的三个码吸走。"""
    error = _error(_post(client, city="nowhereville", longitude=None))
    assert error["code"] == "invalid_birth_data"


def test_the_correction_switch_lets_the_coordinates_be_omitted(client: TestClient) -> None:
    payload = {key: value for key, value in _BASE.items() if key != "longitude"}
    payload["apply_true_solar_time"] = False
    body = client.post("/api/v1/bazi/liuyue", json=payload).json()
    assert "error" not in body
    assert (body["tst_applied"], body["true_solar_time"]) == (False, None)
    assert body["longitude"] == 120.0  # 东八区标准经线，与 /natal 同一缺省


def test_the_response_round_trips_through_the_contract_model(client: TestClient) -> None:
    """`response_model` 丢字段是这类端点最容易犯的病：序列化回来再解析一次，逐字段相等。"""
    body = _post(client, focus_year=2026).json()
    parsed = BaziTransitResult.model_validate(body)
    assert parsed.model_dump(mode="json") == body
