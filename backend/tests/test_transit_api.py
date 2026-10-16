"""行运端点契约（Task 8A Step 2）：偏移活在嵌入的本命盘里、目标儒略日可独立反算、错误各归其位。

盘的**对错**测在 `tests/golden/test_transit_golden.py`（目标历法日、MovingPoint 逆行同号、
行运相位表边界），本模块只管 `POST /api/v1/transit/chart` 这一层的 HTTP/契约面——一律走
`TestClient` 断言 JSON，不 import 引擎函数（分派同 `tests/test_western_api.py`）。

要点：

* **时区契约落在 `natal` 子盘上**：`TransitChart` 顶层**没有** `utc_offset_hours`（finding，
  见下），偏移与来源旗标只活在 `natal: WesternChart` 里；所以 `utc_offset_hours` 的手算对拍
  与独立儒略日反算都读 `body["natal"]`。
* **target 只管后三层、不动本命**：`target_date` 只喂 `target_julian_day`/推运/行运，本命时刻
  由 `birth_*` 决定，二者各测各的。
* **交付 JSON 的落座自洽**：`natal` 的行星/轴/宫头三表与 `transit_positions`、
  `progression.positions`、`solar_arc.positions` 三个运动层，每条都过
  `degree_in_sign == round(longitude % 30, 4)`（带 `sign_index` 者再核 `sign_index`），
  口径与 `tests/test_western_api.py` 一致，不引引擎。
* **错误分工（AGENTS 第 4 条）**：`utc_offset_hours/latitude/longitude` 越界 → 422 pydantic
  `detail`；`target_date` 缺失是必填字段缺失 → 422 `missing`；`target < birth` 与未知宫制由引擎
  抛 `UnsupportedMethodError` → 422 信封；缺坐标 → `InvalidBirthDataError` → 400 信封。读码不读文案。

finding（不动契约、只记）：行运/合盘顶层不回显 `utc_offset_hours`（只有嵌入的本命盘里有），
且合成盘根本没有时区字段——本轮只测不改，上报待控制器裁定。

复测本文件测数：`cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m pytest
tests/test_transit_api.py -v`。
"""

from datetime import date

import pytest
from fastapi.testclient import TestClient

URL = "/api/v1/transit/chart"

BASE: dict[str, object] = {
    "birth_date": "2000-01-01",
    "birth_time": "12:00",
    "latitude": 0.0,
    "longitude": 0.0,
    "utc_offset_hours": 0,
    "house_system": "P",
    "target_date": "2026-09-25",
}


def _post(client: TestClient, **overrides: object):
    return client.post(URL, json={**BASE, **overrides})


def _body(client: TestClient, **overrides: object) -> dict[str, object]:
    response = _post(client, **overrides)
    assert response.status_code == 200, response.text
    return response.json()


def _jd_from_utc_text(utc_text: str) -> float:
    """由 `"%Y-%m-%d %H:%M"` 独立反算儒略日：序数日 + 1721424.5 + 当日秒比（纯历法，不引 swisseph）。"""
    day_part, time_part = utc_text.split(" ")
    year, month, dom = (int(p) for p in day_part.split("-"))
    hour, minute = (int(p) for p in time_part.split(":"))
    return date(year, month, dom).toordinal() + 1721424.5 + (hour * 3600 + minute * 60) / 86400.0


# ------------------------------------------------------------------ 偏移契约（在 natal 里）

def test_an_explicit_offset_shifts_the_embedded_natal_chart(client: TestClient) -> None:
    """+5.5 偏移：`natal.utc_datetime` = 本地 − 偏移，`explicit` 标记，独立反算的儒略日对拍。

    本地 12:00 − 5:30 = 06:30（同日）。复测：`python -c "from datetime import datetime,timedelta as td;print(datetime(2000,1,1,12)-td(hours=5.5))"`。
    """
    body = _body(client, utc_offset_hours=5.5)
    natal = body["natal"]
    assert natal["local_datetime"] == "2000-01-01 12:00"
    assert natal["utc_offset_hours"] == 5.5
    assert natal["utc_offset_source"] == "explicit"
    assert natal["utc_datetime"] == "2000-01-01 06:30"
    assert natal["julian_day"] == pytest.approx(_jd_from_utc_text("2000-01-01 06:30"), abs=1e-4)


def test_the_offset_pushes_the_natal_utc_datetime_onto_the_previous_day(client: TestClient) -> None:
    """跨日不错位：+14 让本地正午落到**前一日** 22:00，natal 的 UTC 日期段跟着变。"""
    body = _body(client, utc_offset_hours=14.0)
    natal = body["natal"]
    assert natal["utc_datetime"] == "1999-12-31 22:00"
    assert natal["utc_datetime"].split(" ")[0] != natal["local_datetime"].split(" ")[0]
    assert natal["julian_day"] == pytest.approx(_jd_from_utc_text("1999-12-31 22:00"), abs=1e-4)


def test_an_omitted_offset_falls_back_to_the_longitude_zone_on_the_natal(client: TestClient) -> None:
    """不给偏移时 natal 标 `longitude_approximation`，折 `round(lon/15)`，与显式路径可区分。"""
    folded = _body(client, latitude=39.9042, longitude=116.4074, utc_offset_hours=None)
    assert folded["natal"]["utc_offset_source"] == "longitude_approximation"
    assert folded["natal"]["utc_offset_hours"] == 8.0
    assert folded["natal"]["utc_datetime"] == "2000-01-01 04:00"


# ------------------------------------------------------------------ 目标历日独立反算

def test_target_julian_day_is_the_noon_calendar_value(client: TestClient) -> None:
    """target 层用正午 UT：独立算式 = 序数 + 1721424.5 + 半日 = 2461309.0。

    复测：`python -c "from datetime import date;print(date(2026,9,25).toordinal()+1721424.5+0.5)"`。
    """
    body = _body(client)
    hand = date(2026, 9, 25).toordinal() + 1721424.5 + 0.5
    assert body["target_julian_day"] == pytest.approx(hand, abs=1e-4)


def test_the_top_level_has_no_utc_offset_hours_only_the_natal_carries_it(client: TestClient) -> None:
    """现状事实 + finding：`utc_offset_hours` 只在嵌入的本命盘回显，顶层 TransitChart 没有该键。

    本轮不动契约（ledger F-A1-7），把缺口钉成现状：顶层键集不含 `utc_offset_hours` /
    `utc_offset_source`，读取偏移必须下钻到 `natal`。若将来顶层加了该字段，本测会红，
    届时连同契约一起重定，而不是删断言。
    """
    body = _body(client)
    assert "utc_offset_hours" not in body
    assert "utc_offset_source" not in body
    assert "utc_offset_hours" in body["natal"]


# ------------------------------------------------------------------ 响应内部自洽（落座算术）

def test_every_natal_and_moving_point_is_internally_consistent_with_its_longitude(
    client: TestClient,
) -> None:
    """行运响应的每一条 placement 都过落座算术：natal 三表 + 三个运动层，逐条核验。

    与本命那条同源、同口径：`tests/test_western_api.py::
    test_every_placement_is_internally_consistent_with_its_own_longitude`。差别只在这一盘的
    placement 不止嵌在 `natal` 里——`transit_positions`、`progression.positions`、
    `solar_arc.positions` 三个运动层是同一批 `MovingPoint`（`app/schemas/transit.py:38-53`），
    计划 Step 1(b) 要求「三系统响应里每一个 placement 都过落座算术」，漏的就是这三层。

    断言的是对**已交付 JSON** 的内部一致性，不引引擎、不回读原始值：
    `degree_in_sign == round(longitude % 30, 4)`；带 `sign_index` 的对象再核
    `sign_index == int(longitude // 30)`。`HouseCusp` 根本没有 `sign_index`
    （`app/schemas/western.py:47-55`），所以走 `if "sign_index" in item` 这条真实分支跳过它，
    而不是给它造字段。

    潜在陷阱（finding，同本命那条）：`_degree_in_sign` 对 29.99996° 这类座首值会 round 到
    30.0，而响应 longitude 同时 round 到整 30° → 二者在该刀锋点会不自洽；本参考盘不落在刀锋上
    （实测通过），故钉现状、不改引擎。复测：
    `python -c "from app.engines.western import _degree_in_sign as d;print(d(29.99996))"` → 30.0。
    """
    body = _body(client)
    natal = body["natal"]
    layers = {
        "natal.planets": natal["planets"],
        "natal.axes": natal["axes"],
        "natal.houses": natal["houses"],
        "transit_positions": body["transit_positions"],
        "progression.positions": body["progression"]["positions"],
        "solar_arc.positions": body["solar_arc"]["positions"],
    }
    for name, items in layers.items():
        assert items, name  # 空层会让下面的循环真空通过，先各钉一次非空
    for name, items in layers.items():
        for item in items:
            longitude = item["longitude"]
            assert item["degree_in_sign"] == round(longitude % 30, 4), (name, item.get("name", item.get("house")))
            if "sign_index" in item:
                assert item["sign_index"] == int(longitude // 30), (name, item.get("name"))


# ------------------------------------------------------------------ 错误分工

@pytest.mark.parametrize(
    "field, value, code",
    [
        ("utc_offset_hours", 14.5, "less_than_equal"),
        ("utc_offset_hours", -15, "greater_than_equal"),
        ("latitude", 91, "less_than_equal"),
        ("longitude", 181, "less_than_equal"),
    ],
    ids=["偏移上限外", "偏移下限外", "纬度上限外", "经度上限外"],
)
def test_field_level_bounds_are_pydantic_validation(client: TestClient, field: str, value: object, code: str) -> None:
    """单字段越 `ge/le` 界 → 422 `detail`（`schemas/transit.py:31-33`），不是信封。"""
    response = _post(client, **{field: value})
    assert response.status_code == 422
    body = response.json()
    assert "error" not in body
    assert body["detail"][0]["loc"] == ["body", field]
    assert body["detail"][0]["type"] == code


def test_a_missing_target_date_is_a_pydantic_required_field_error(client: TestClient) -> None:
    """`target_date` 是必填（`schemas/transit.py:35`），整个字段缺席 → 422 `missing`，不是信封。

    这里**删键**而不是发 null：发 null 会被判成日期解析错，删键才对应「必填字段没给」这条。
    """
    payload = dict(BASE)
    payload.pop("target_date")
    response = client.post(URL, json=payload)
    assert response.status_code == 422
    body = response.json()
    assert "error" not in body
    assert body["detail"][0]["loc"] == ["body", "target_date"]
    assert body["detail"][0]["type"] == "missing"


def test_a_pre_birth_target_is_an_unsupported_method_envelope(client: TestClient) -> None:
    """target 早于 birth 是前提错误（各字段单独看都合法）→ 引擎 `UnsupportedMethodError` → 422 信封。"""
    response = _post(client, target_date="1999-01-01")
    assert response.status_code == 422
    body = response.json()
    assert "detail" not in body
    assert body["error"]["code"] == "unsupported_method"


def test_an_unknown_house_system_is_an_unsupported_method_envelope(client: TestClient) -> None:
    """未知宫制由引擎判定（schema 只把它当普通字符串）→ 422 信封，读码不读文案。"""
    response = _post(client, house_system="Z")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "unsupported_method"


def test_a_missing_location_is_an_envelope(client: TestClient) -> None:
    """坐标与城市皆缺 → 引擎 `InvalidBirthDataError` → 400 信封（`error` 而非 `detail`）。"""
    response = _post(client, latitude=None, longitude=None)
    assert response.status_code == 400
    body = response.json()
    assert "detail" not in body
    assert body["error"]["code"] == "invalid_birth_data"


# ------------------------------------------------------------------ 白话五段（T24）

def test_the_plain_block_arrives_in_the_declared_section_order(client: TestClient) -> None:
    """响应 `plain` 五段的标题字面序（T24 Step 6；`build_plain` 的发射序钉成 API 契约）。

    `len(plain[0].text) > len(plain[3].text)` 抓「段序写反」：相位段恒多于月亮段（相位段
    行数 == 条数 + 1，fixture 那手 36 条 vs 月亮段恒 2 条），若装配把 `progressed_moon`
    排到 `transit_aspect` 前，长度断言立刻红。
    """
    body = _body(client)
    titles = [s["title"] for s in body["plain"]]
    assert titles == ["行运对本命相位", "次限对本命相位", "太阳弧对本命相位", "次限月亮", "次限上升与天顶"]
    assert len(body["plain"][0]["text"]) > len(body["plain"][3]["text"])


def test_the_provenance_declares_exactly_the_three_overlay_tables(client: TestClient) -> None:
    """`provenance.tables` 三行按 `TRANSIT_OVERLAY_CONTENT_SOURCES` 的字面序回显（T25）。

    序以名单为准（`app/content/__init__.py` 的 `TRANSIT_OVERLAY_CONTENT_SOURCES`），两边必须
    一致——这里钉的是「响应如实回显登记」，登记表自身那一半由本地门那颗逐字钉负责。
    """
    body = _body(client)
    tables = body["provenance"]["tables"]
    assert [t["name"] for t in tables] == ["transit_plain", "transit_plain_aspect", "aspects_nature"]
    assert len(tables) == 3
    assert all(t["version"] for t in tables)
    assert len({t["version"] for t in tables}) == 1
