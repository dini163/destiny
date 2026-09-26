"""西洋合盘端点契约（Task 8A Step 2）：偏移活在两人各自本命盘里、内层越界仍归 pydantic。

盘的**对错**测在 `tests/golden/test_synastry_golden.py`（中点算术、对称性、账本进账门），
本模块只管 `POST /api/v1/synastry/chart` 的 HTTP/契约面——一律走 `TestClient` 断言 JSON，
不 import 引擎函数（分派同 `tests/test_western_api.py`）。

与 golden 的分工：golden 已覆盖「未知宫制 → 422 信封」「缺 person_b → 422 detail」「缺坐标 →
400 信封」「round trip 回显」四条端点面，本模块**不重复**这些；这里钉的是 golden 没测的
偏移契约（每人各自的 `utc_datetime`/`julian_day`/来源旗标）、**嵌套字段**越界的 422
（`person_a.utc_offset_hours`/`person_b.latitude`），以及交付 JSON 的落座自洽。

要点：

* **每人一份时区**：偏移与来源旗标活在嵌入的 `person_a`/`person_b` 本命盘里；`SynastryChart`
  顶层与合成盘都没有时区字段（finding）。
* **嵌套 `ge/le` 归 pydantic**（AGENTS 第 4 条）：`person_*` 子模型字段的越界仍是 422 `detail`，
  `loc` 一路点到 `["body", "person_a", "utc_offset_hours"]`，不是信封。

finding（不动契约、只记）：顶层与 `composite` 均无 `utc_offset_hours`，只有两份嵌入本命盘回显；
本轮只测不改，上报待控制器裁定。

复测本文件测数：`cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m pytest
tests/test_synastry_api.py -v`。
"""

from datetime import date

import pytest
from fastapi.testclient import TestClient

URL = "/api/v1/synastry/chart"
LAT = 51.4769
LON = -0.0005


def _person(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {"latitude": LAT, "longitude": LON, "utc_offset_hours": 0}
    return {**base, **overrides}


def _payload(person_a: dict | None = None, person_b: dict | None = None) -> dict[str, object]:
    return {
        "person_a": person_a if person_a is not None else _person(
            birth_date="1990-06-15", birth_time="08:30", name="甲"),
        "person_b": person_b if person_b is not None else _person(
            birth_date="1992-11-20", birth_time="18:45", name="乙"),
        "house_system": "P",
    }


def _post(client: TestClient, person_a: dict | None = None, person_b: dict | None = None):
    return client.post(URL, json=_payload(person_a, person_b))


def _body(client: TestClient, person_a: dict | None = None, person_b: dict | None = None) -> dict[str, object]:
    response = _post(client, person_a=person_a, person_b=person_b)
    assert response.status_code == 200, response.text
    return response.json()


def _jd_from_utc_text(utc_text: str) -> float:
    """由 `"%Y-%m-%d %H:%M"` 独立反算儒略日：序数日 + 1721424.5 + 当日秒比（纯历法，不引 swisseph）。"""
    day_part, time_part = utc_text.split(" ")
    year, month, dom = (int(p) for p in day_part.split("-"))
    hour, minute = (int(p) for p in time_part.split(":"))
    return date(year, month, dom).toordinal() + 1721424.5 + (hour * 3600 + minute * 60) / 86400.0


# ------------------------------------------------------------------ 每人各自的偏移契约

def test_a_person_explicit_offset_shifts_their_natal_and_julian_day(client: TestClient) -> None:
    """甲偏移 +5.75：`person_a.utc_datetime` = 本地 − 偏移（含 45 分），`explicit`，独立反算儒略日。

    本地 08:30 − 5:45 = 02:45（同日 1990-06-15）。复测：
    `python -c "from datetime import datetime,timedelta as td;print(datetime(1990,6,15,8,30)-td(hours=5.75))"`。
    """
    body = _body(client, person_a=_person(birth_date="1990-06-15", birth_time="08:30", utc_offset_hours=5.75))
    person_a = body["person_a"]
    assert person_a["local_datetime"] == "1990-06-15 08:30"
    assert person_a["utc_offset_hours"] == 5.75
    assert person_a["utc_offset_source"] == "explicit"
    assert person_a["utc_datetime"] == "1990-06-15 02:45"
    assert person_a["julian_day"] == pytest.approx(_jd_from_utc_text("1990-06-15 02:45"), abs=1e-4)


def test_a_negative_offset_pushes_a_persons_utc_datetime_to_the_next_day(client: TestClient) -> None:
    """跨日不错位：乙偏移 −14 让本地 18:45 落到**次日** 08:45，其 UTC 日期段跟着变。

    18:45 − (−14) = 18:45 + 14h = 次日 08:45。复测：
    `python -c "from datetime import datetime,timedelta as td;print(datetime(1992,11,20,18,45)-td(hours=-14))"`。
    """
    body = _body(client, person_b=_person(birth_date="1992-11-20", birth_time="18:45", utc_offset_hours=-14))
    person_b = body["person_b"]
    assert person_b["utc_datetime"] == "1992-11-21 08:45"
    assert person_b["utc_datetime"].split(" ")[0] != person_b["local_datetime"].split(" ")[0]
    assert person_b["julian_day"] == pytest.approx(_jd_from_utc_text("1992-11-21 08:45"), abs=1e-4)


def test_a_person_without_an_offset_falls_back_to_the_longitude_zone(client: TestClient) -> None:
    """某人不给偏移时该人标 `longitude_approximation`，折 `round(lon/15)`；另一人仍可显式。

    甲按东经 116.4074 折 8 小时（08:30 → 00:30），乙显式 0（18:45 → 18:45），二人旗标各归各。
    """
    body = _body(
        client,
        person_a=_person(birth_date="1990-06-15", birth_time="08:30", latitude=39.9042,
                         longitude=116.4074, utc_offset_hours=None),
    )
    assert body["person_a"]["utc_offset_source"] == "longitude_approximation"
    assert body["person_a"]["utc_offset_hours"] == 8.0
    assert body["person_a"]["utc_datetime"] == "1990-06-15 00:30"
    assert body["person_b"]["utc_offset_source"] == "explicit"


# ------------------------------------------------------------------ 回显面（顶层没有时区）

def test_the_offset_lives_only_in_the_embedded_natal_charts_not_the_top_level(client: TestClient) -> None:
    """现状事实 + finding：偏移只在嵌入本命盘回显，顶层与合成盘都无 `utc_offset_hours`。

    若将来顶层加了该字段本测会红，届时连同契约一起重定（ledger F-A1-7：本轮不动契约）。
    """
    body = _body(client)
    assert "utc_offset_hours" not in body
    assert "utc_offset_hours" not in body["composite"]
    assert "utc_offset_hours" in body["person_a"]
    assert "utc_offset_hours" in body["person_b"]


def test_every_embedded_placement_is_internally_consistent_with_its_longitude(client: TestClient) -> None:
    """两人本命盘与合成盘的每个 placement：`degree_in_sign == round(longitude % 30, 4)`，
    有 `sign_index` 者再核 `sign_index == int(longitude // 30)`（`app/engines/western.py:76-81`）。

    这是对已交付 JSON 的纯算术核验，不引引擎。刀锋例外同本命 api：座首 round 到整 30° 时二者会
    不自洽，本参考盘不落在刀锋上（实测通过）。复测：见 `tests/test_western_api.py` 的同名口径注释。
    """
    body = _body(client)
    placements: list[dict] = []
    for chart_key in ("person_a", "person_b", "composite"):
        chart = body[chart_key]
        placements += list(chart["planets"]) + list(chart["axes"]) + list(chart["houses"])
    assert placements
    for item in placements:
        longitude = item["longitude"]
        assert item["degree_in_sign"] == round(longitude % 30, 4), (item.get("name"), item.get("house"))
        if "sign_index" in item:
            assert item["sign_index"] == int(longitude // 30), item.get("name")


# ------------------------------------------------------------------ 嵌套字段越界

@pytest.mark.parametrize(
    "person, field, value, code",
    [
        ("person_a", "utc_offset_hours", 14.5, "less_than_equal"),
        ("person_a", "utc_offset_hours", -15, "greater_than_equal"),
        ("person_b", "latitude", 91, "less_than_equal"),
        ("person_b", "longitude", 181, "less_than_equal"),
    ],
    ids=["甲偏移上限外", "甲偏移下限外", "乙纬度上限外", "乙经度上限外"],
)
def test_nested_field_bounds_are_pydantic_validation(client: TestClient, person: str, field: str,
                                                     value: object, code: str) -> None:
    """`SynastryPerson` 子模型的 `ge/le` 越界仍是 422 `detail`，`loc` 一路点到嵌套字段（AGENTS 第 4 条）。"""
    bad = _person(**{"birth_date": "1990-06-15", "birth_time": "08:30", field: value})
    payload = _payload()
    payload[person] = bad
    response = client.post(URL, json=payload)
    assert response.status_code == 422
    body = response.json()
    assert "error" not in body
    assert body["detail"][0]["loc"] == ["body", person, field]
    assert body["detail"][0]["type"] == code
