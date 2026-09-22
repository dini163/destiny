"""/bazi/liuri/matrix 的契约：载荷形状、缺省 anchor、两个域错误码。"""

from typing import Any

from fastapi.testclient import TestClient

from app.schemas.bazi_liuri import BaziLiuriResult

_MATRIX = "/api/v1/bazi/liuri/matrix"
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
    """域错误的路径都从这一处走：`reference_date` 固定，缺省锚点才有唯一答案可断。"""
    return client.post(_MATRIX, json={**_BASE, "reference_date": "2028-01-15", **payload})


def _error(client: TestClient, payload: dict[str, object]) -> dict[str, object]:
    """域错误的那半边信封；缺 `error` 键时直接判红，而不是回一个 None。"""
    response = _post(client, payload)
    assert response.status_code == 422, response.json()
    body = response.json()
    assert "error" in body, body
    return body["error"]


def test_the_matrix_endpoint_returns_the_declared_model(client: TestClient) -> None:
    """载荷原样过一遍 schema 的往返：字段少一个、多一个、形状换了都在这里红。"""
    response = _post(client, {"anchor_date": "2028-01-15", "focus_date": "2028-01-10"})
    assert response.status_code == 200, response.json()
    parsed = BaziLiuriResult.model_validate(response.json())
    assert parsed == BaziLiuriResult.model_validate(parsed.model_dump())


def test_an_absent_anchor_defaults_to_the_reference_segment(client: TestClient) -> None:
    body = _post(client, {}).json()
    assert (body["anchor_date"], body["month_ganzhi"], body["year"]) == ("2028-01-15", "癸丑", 2027)
    assert body["focused"] is None


def test_an_anchor_before_the_luck_window_answers_with_a_machine_code(client: TestClient) -> None:
    assert _error(client, {"anchor_date": "1980-06-01"}) == {
        "code": "liuri_month_unsupported",
        "message": "1980-06-01 所在的节气月推不出：本命盘可推年份 1988—2083。",
        "context": {"requested": "1980-06-01", "supported_from": 1988, "supported_to": 2083},
    }


def test_a_focus_date_outside_the_resolved_segment_answers_with_a_machine_code(client: TestClient) -> None:
    error = _error(client, {"anchor_date": "2028-01-15", "focus_date": "2028-03-01"})
    assert error["code"] == "liuri_focus_out_of_month"
    assert error["context"] == {
        "focus_date": "2028-03-01",
        "month_start_solar": "2028-01-06",
        "month_end_solar": "2028-02-03",
    }


def test_a_request_without_gender_is_a_pydantic_422_not_a_domain_422(client: TestClient) -> None:
    """两类 422 的分界同岁运页：字段没填走 FastAPI 的 `detail`，没有 `error`，也就没有机器码。

    本端点不自己划这条线 —— 它只多了一样东西（两个可空日期），域错误与校验错误的信封
    分工由 `register_error_handlers` 与 FastAPI 各管一半，所以这里钉的是"没把线挪过"。
    """
    payload = {key: value for key, value in _BASE.items() if key != "gender"}
    response = client.post(_MATRIX, json=payload)
    assert response.status_code == 422
    body = response.json()
    assert "error" not in body
    assert {item["loc"][-1] for item in body["detail"]} == {"gender"}


def test_a_turned_off_correction_leaves_true_solar_time_null(client: TestClient) -> None:
    body = _post(client, {"apply_true_solar_time": False}).json()
    assert body["true_solar_time"] is None and body["tst_applied"] is False
