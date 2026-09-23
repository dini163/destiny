"""`POST /bazi/hehun` 的端点契约（spec §9、§10.7，计划 Task 9）。

这一页有两类信封、三种状态码：域错误过 `DestinyError` 处理器，带
`{"error": {code, message, context}}`，轴的越界是 422；缺字段与 `axis_years` 自身越界过
pydantic，带 `{"detail": [...]}`，也是 422；而一造生辰非法走的是 `/natal` 那条链上现成的
`invalid_birth_data`，**状态码维持 400**（§9.2 明写"code、message、状态码一字不动"，
`tests/golden/test_bazi_golden.py::test_bazi_natal_requires_location_when_tst_enabled`
已把 400 钉在其它端点上）。形状不同而状态码有重合，
所以每个用例都两头各断一次 —— 只看 status_code 的测试放得过任何一侧。

合婚特有的一条是 `context.partner`：一造合法一造非法时整请求失败（§9.1），
而失败要说得出是谁（§9.2）。这一项只在八字合婚出现，所以它在契约测里必须留下痕迹，
否则前端 `CONTEXT_LABEL` 那条新键就没有对拍对象。
"""

from typing import Any

from fastapi.testclient import TestClient

from app.schemas.bazi_hehun import BaziHehunResult

_MALE: dict[str, Any] = {
    "birth_date": "1988-02-15",
    "birth_time": "23:30",
    "calendar": "solar",
    "city": "成都",
    "apply_true_solar_time": True,
    "name": "乾测",
}
_FEMALE: dict[str, Any] = {
    "birth_date": "1990-06-15",
    "birth_time": "10:00",
    "calendar": "solar",
    "city": "北京",
    "apply_true_solar_time": True,
    "name": "坤测",
}
_BASE: dict[str, Any] = {"male": _MALE, "female": _FEMALE, "reference_date": "2026-09-22"}


def _post(client: TestClient, **overrides: Any) -> Any:
    payload: dict[str, Any] = {
        "male": {**_MALE, **overrides.pop("male", {})},
        "female": {**_FEMALE, **overrides.pop("female", {})},
        **overrides,
    }
    return client.post("/api/v1/bazi/hehun", json={**_BASE, **payload})


def _error(response: Any) -> dict[str, Any]:
    """域错误的那半边信封；缺 `error` 键时直接判红，而不是回一个 None。"""
    body = response.json()
    assert "error" in body, body
    return body["error"]


def test_the_default_request_returns_the_whole_page(client: TestClient) -> None:
    """缺省轴：起点 = `max(坤出生年 1990, 参考年 2026) = 2026`，长度 21 → 2026—2046。"""
    body = _post(client).json()
    assert body["male"]["four_pillars"] == "戊辰 甲寅 庚子 丁亥"
    assert body["female"]["four_pillars"] == "庚午 壬午 辛亥 癸巳"
    assert (body["male"]["name"], body["female"]["name"]) == ("乾测", "坤测")
    assert (body["score"]["value"], body["score"]["tier"]) == (0.0, "欠和宜慎")
    assert len(body["fired"]) == 20 and len(body["score"]["factors"]) == 21
    assert body["provenance"]["reference_date"] == "2026-09-22"
    assert (body["axis"]["start_year"], body["axis"]["end_year"]) == (2026, 2046)
    assert len(body["axis"]["rows"]) == 21


def test_matrix_cells_are_lists_and_axis_rows_carry_no_factors(client: TestClient) -> None:
    """§10.6 呈现完整性的 JSON 侧：空格是 `[]` 而不是 `null`；轴行只有分与档。

    前端拿 `hits.length` 决定"无"这一格怎么画，`null` 会把它整格抹掉；
    轴行不带 `factors` 是切片 3 的简表约定（明细走岁运页的下钻链接）。
    """
    body = _post(client, axis_start_year=2024, axis_years=5).json()
    assert len(body["matrix"]) == 16
    assert sum(1 for cell in body["matrix"] if cell["hits"] == []) == 7  # 12 条命中落在 9 格里
    assert [cell["hits"] for cell in body["matrix"] if cell["hits"]][0][0]["direction"] == "mutual"
    row = body["axis"]["rows"][0]
    assert set(row) == {"year", "ganzhi", "male", "female", "gap", "sync"}
    assert set(row["male"]) == {"value", "tier", "dayun", "dayun_start_age"}
    assert (row["year"], row["ganzhi"], row["male"]["value"], row["female"]["value"]) == (
        2024,
        "甲辰",
        33.0,
        42.0,
    )
    assert [s["label"] for s in body["axis"]["segments"]] == [
        "乾·第 4 运 戊午（37—46 岁）／坤·第 4 运 戊寅（34—43 岁）"
    ]


def test_each_partner_keeps_its_own_true_solar_time_decision(client: TestClient) -> None:
    """§5.1：`apply_true_solar_time` 各造一份 —— 关掉坤的校正不能带动乾的。

    坤 10:00 北京 校正后 09:45 仍在巳时，所以两造的柱一个字都不动，动的只有回显的
    那一刻与开关。这正是"共用一个开关"会被否决的理由：关掉校正时那一侧根本无时刻可言。
    """
    body = _post(client, female={"apply_true_solar_time": False, "city": None}).json()
    assert (body["female"]["tst_applied"], body["female"]["true_solar_time"]) == (False, None)
    assert (body["male"]["tst_applied"], body["male"]["true_solar_time"]) == (
        True,
        "1988-02-15 22:12",
    )
    assert body["female"]["four_pillars"] == "庚午 壬午 辛亥 癸巳"


def test_an_illegal_partner_is_named_and_no_half_chart_comes_back(client: TestClient) -> None:
    """§9.1 + §9.2：一造非法即整请求失败，`context.partner` 说是谁；没有半张盘。

    400 不是笔误：`InvalidBirthDataError` 沿 `/natal` 的链原样再抛（§9.2），合婚不给它
    另开一个状态码。反向那一半才是这条测的价值 —— 乾非法时 `partner` 必须是 `male`，
    否则"永远报坤"的写法也能绿（引擎侧 `test_bazi_hehun.py::test_an_illegal_partner...`
    已在 `compute_partner_charts` 上两头断过，这里是它在 HTTP 侧的留痕）。
    """
    response = _post(client, female={"city": "不存在的地方"})
    error = _error(response)
    assert (response.status_code, error["code"]) == (400, "invalid_birth_data")
    assert error["context"] == {"partner": "female"}
    assert "matrix" not in response.json()
    reversed_ = _error(_post(client, male={"city": "不存在的地方"}, female={"city": "北京"}))
    assert reversed_["context"] == {"partner": "male"}


def test_an_axis_before_the_later_birth_year_is_a_domain_422(client: TestClient) -> None:
    """轴起早于坤的出生年：机器码 + 五项 context，前端据此把轴挪回去（§8 的 CONTEXT_LABEL）。"""
    response = _post(client, axis_start_year=1989)
    error = _error(response)
    assert response.status_code == 422
    assert error["code"] == "hehun_axis_out_of_range"
    assert error["context"] == {
        "requested_from": 1989,
        "requested_to": 2009,
        "male_available_from": 1988,
        "female_available_from": 1990,
        "supported_to": 2082,
    }


def test_an_axis_past_the_shared_end_is_the_same_code(client: TestClient) -> None:
    response = _post(client, axis_start_year=2080, axis_years=5)
    error = _error(response)
    assert response.status_code == 422
    assert error["code"] == "hehun_axis_out_of_range"
    assert (error["context"]["requested_to"], error["context"]["supported_to"]) == (2084, 2082)


def test_an_axis_longer_than_the_cap_is_a_pydantic_422_not_a_domain_422(client: TestClient) -> None:
    """§9.3 的两类 422 分界：轴长自身越界是入参错误，拿不到也不该拿到机器码。"""
    response = _post(client, axis_years=31)
    body = response.json()
    assert response.status_code == 422
    assert "error" not in body
    assert {item["loc"][-1] for item in body["detail"]} == {"axis_years"}


def test_a_missing_partner_field_is_a_validation_error(client: TestClient) -> None:
    """两组生辰里少一个字段：`detail` 侧、指向那一造的键，不被合婚的任何域错误吸走。"""
    response = client.post(
        "/api/v1/bazi/hehun",
        json={"male": _MALE, "female": {k: v for k, v in _FEMALE.items() if k != "birth_time"}},
    )
    body = response.json()
    assert response.status_code == 422
    assert "error" not in body
    assert {tuple(item["loc"]) for item in body["detail"]} == {("body", "female", "birth_time")}


def test_the_response_round_trips_through_the_contract_model(client: TestClient) -> None:
    """`response_model` 丢字段是这类端点最容易犯的病：序列化回来再解析一次，逐字段相等。"""
    body = _post(client, axis_start_year=2024, axis_years=5).json()
    parsed = BaziHehunResult.model_validate(body)
    assert parsed.model_dump(mode="json") == body
