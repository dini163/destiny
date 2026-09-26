"""西洋本命端点契约（Task 8A Step 2）：`utc_offset_hours` 的时区/儒略日口径与错误各归其位。

盘的**对错**测在三份 `tests/golden/test_*_golden.py`（落座算术、宫制、逆行、相位表边界），
本模块只管 `POST /api/v1/western/natal` 这一层有没有把引擎算好的时移、坐标、盘如实递出去——
一律走 `TestClient` 断言 JSON，不 import 引擎函数（分派同 `tests/test_vedic_api.py`）。

钉三件事（每个偏移极值都各测一次）：

* **时移逐字对拍**：`utc_datetime` = 本地钟点 − 偏移（到分钟，含半小时/一刻钟区），
  手算 UTC 时刻与响应字面比。
* **儒略日独立推算**：由 `utc_datetime` 反算 `jd = date.toordinal() + 1721424.5 + 秒/86400`
  （proleptic Gregorian 序数 + 当日比例），与响应 `julian_day` 相符——不引 swisseph。
* **跨日不错位**：偏移把 UTC 推到前一天/后一天时，`utc_datetime` 的**日期段**必须跟着变。

错误分工（AGENTS 第 4 条）：`utc_offset_hours`/`latitude`/`longitude` 的 `ge/le` 越界是字段
自身非法 → 422 pydantic `detail`（`schemas/western.py:21-25`）；缺坐标是字段之间/前提问题 →
引擎抛 `InvalidBirthDataError` → 400 信封；未知宫制由引擎抛 `UnsupportedMethodError` →
422 信封（`app/core/errors.py`，该子类覆写 422）。信封一律读 `error.code`，不读文案。

finding（不动契约、只记）：`WesternChart` 顶层回显 `utc_offset_hours`，但行运/合盘的顶层
不回显（见 `test_transit_api.py`、`test_synastry_api.py`）——偏移只活在嵌入的本命盘里。

复测本文件测数：`cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m pytest
tests/test_western_api.py -v`。
"""

from datetime import date

import pytest
from fastapi.testclient import TestClient

URL = "/api/v1/western/natal"

#: 参考请求：正午 UTC 格林尼治，与 golden 同一张盘（值互不重复断言，本模块只测契约面）。
BASE: dict[str, object] = {
    "birth_date": "2000-01-01",
    "birth_time": "12:00",
    "latitude": 0.0,
    "longitude": 0.0,
}


def _post(client: TestClient, **overrides: object):
    return client.post(URL, json={**BASE, **overrides})


def _body(client: TestClient, **overrides: object) -> dict[str, object]:
    response = _post(client, **overrides)
    assert response.status_code == 200, response.text
    return response.json()


def _jd_from_utc_text(utc_text: str) -> float:
    """由响应里的 `"%Y-%m-%d %H:%M"` 独立反算儒略日：序数日 + 1721424.5 + 当日秒比。

    1721424.5 把 proleptic-Gregorian 序数 1（公元 1-01-01）对齐到儒略日的 noon 起点，
    与本仓 swisseph 无关，是纯历法常数。复测：
    `python -c "from datetime import date;print(date(2000,1,1).toordinal()+1721424.5+0.5)"` → 2451545.0。
    """
    day_part, time_part = utc_text.split(" ")
    year, month, dom = (int(p) for p in day_part.split("-"))
    hour, minute = (int(p) for p in time_part.split(":"))
    return date(year, month, dom).toordinal() + 1721424.5 + (hour * 3600 + minute * 60) / 86400.0


# ------------------------------------------------------------------ 偏移极值：时移 + 儒略日

#: (偏移小时, 期望 utc_datetime 字面, 是否跨日)——本地恒为 2000-01-01 12:00。
#: 手算：UTC = 本地 − 偏移。+14 → 前一日 22:00；-14 → 次日 02:00；
#: +5.5 → 06:30；+5.75 → 06:15（尼泊尔 5h45m）；+12.75 → 前一日 23:15（查塔姆 12h45m）。
#: 复测：`python -c "from datetime import datetime,timedelta as td;print((datetime(2000,1,1,12)-td(hours=12.75)))"`。
OFFSET_CASES = [
    (14.0, "1999-12-31 22:00", True),
    (-14.0, "2000-01-02 02:00", True),
    (5.5, "2000-01-01 06:30", False),
    (5.75, "2000-01-01 06:15", False),
    (12.75, "1999-12-31 23:15", True),
]


@pytest.mark.parametrize("offset,expected_utc,crosses_day", OFFSET_CASES,
                         ids=["东14区跨到前一日", "西14区跨到次日", "印度+5.5", "尼泊尔+5.75", "查塔姆+12.75跨日"])
def test_an_explicit_offset_shifts_the_clock_the_julian_day_and_the_date(
    client: TestClient, offset: float, expected_utc: str, crosses_day: bool
) -> None:
    """显式偏移：UTC 字面手算相符、`explicit` 标记、独立反算的儒略日对拍、跨日时日期段跟着挪。"""
    body = _body(client, utc_offset_hours=offset)
    assert body["local_datetime"] == "2000-01-01 12:00"
    assert body["utc_offset_hours"] == offset
    assert body["utc_offset_source"] == "explicit"
    assert body["utc_datetime"] == expected_utc
    # ② 儒略日由 utc_datetime 独立反算（到分钟，秒为 0），与响应 round 到 5 位的值相符。
    assert body["julian_day"] == pytest.approx(_jd_from_utc_text(expected_utc), abs=1e-4)
    # ③ 跨日不错位：UTC 的日期段要么变了（跨日），要么没变（同日）。
    assert (body["utc_datetime"].split(" ")[0] != "2000-01-01") is crosses_day


def test_julian_day_at_j2000_matches_the_calendar_constant(client: TestClient) -> None:
    """偏移 0：本地即 UTC，独立算式给出 J2000 定义值 2451545.0（不引引擎历法）。"""
    body = _body(client, utc_offset_hours=0)
    assert body["julian_day"] == pytest.approx(_jd_from_utc_text("2000-01-01 12:00"), abs=1e-4)
    assert body["julian_day"] == pytest.approx(2451545.0, abs=1e-4)


# ------------------------------------------------------------------ 缺省路径：按经度折时区

def test_an_omitted_offset_is_replaced_by_the_longitude_zone(client: TestClient) -> None:
    """不给偏移时 `utc_offset_source == "longitude_approximation"`，偏移 = `round(lon/15)`。

    东经 116.4074 → round(7.7604) = 8 小时（`app/engines/western.py:180`）；本地正午 12:00
    折成 UTC 04:00。西经 52.0 → round(-3.4667) = -3 小时。两支都是理论区时，与真实时区可差数小时。
    """
    beijing = _body(client, latitude=39.9042, longitude=116.4074)
    assert beijing["utc_offset_source"] == "longitude_approximation"
    assert beijing["utc_offset_hours"] == 8.0
    assert beijing["utc_datetime"] == "2000-01-01 04:00"
    west_atlantic = _body(client, latitude=0.0, longitude=-52.0)
    assert west_atlantic["utc_offset_source"] == "longitude_approximation"
    assert west_atlantic["utc_offset_hours"] == -3.0


def test_explicit_and_approximated_offsets_are_distinguishable(client: TestClient) -> None:
    """同一坐标、同一钟点：显式 0 与按经度折 8 给出两张不同的盘——徽标不能省。"""
    explicit = _body(client, latitude=39.9042, longitude=116.4074, utc_offset_hours=0)
    folded = _body(client, latitude=39.9042, longitude=116.4074)
    assert explicit["utc_offset_source"] == "explicit"
    assert folded["utc_offset_source"] == "longitude_approximation"
    assert explicit["utc_datetime"] == "2000-01-01 12:00"
    assert folded["utc_datetime"] == "2000-01-01 04:00"
    assert explicit["julian_day"] != folded["julian_day"]
    assert [p["longitude"] for p in explicit["planets"]] != [p["longitude"] for p in folded["planets"]]


# ------------------------------------------------------------------ 响应内部自洽（落座算术）

def test_every_placement_is_internally_consistent_with_its_own_longitude(client: TestClient) -> None:
    """响应里每个 PlanetPlacement/AxisPoint/HouseCusp 的 sign_index、degree_in_sign 都等于对其
    longitude 做纯算术的结果（`int(lon // 30)`、`round(lon % 30, 4)`，`app/engines/western.py:76-81`）。

    这是对**已交付 JSON** 的内部一致性核验，不引引擎、不回读原始值。潜在陷阱（finding）：
    `_degree_in_sign` 对 29.99996° 这类座首值会 round 到 30.0，而响应 longitude 同时 round 到
    整 30° → 二者在该刀锋点会不自洽；本参考盘不落在刀锋上（实测通过），故钉现状、不改引擎。
    复测：`python -c "from app.engines.western import _degree_in_sign as d;print(d(29.99996))"` → 30.0。
    """
    body = _body(client, utc_offset_hours=0)
    placements = list(body["planets"]) + list(body["axes"]) + list(body["houses"])
    assert placements
    for item in placements:
        longitude = item["longitude"]
        assert item["degree_in_sign"] == round(longitude % 30, 4), item.get("name", item.get("house"))
        if "sign_index" in item:
            assert item["sign_index"] == int(longitude // 30), item.get("name")


# ------------------------------------------------------------------ 错误分工

@pytest.mark.parametrize(
    "field, value, code",
    [
        ("utc_offset_hours", 14.5, "less_than_equal"),
        ("utc_offset_hours", -15, "greater_than_equal"),
        ("latitude", 91, "less_than_equal"),
        ("latitude", -91, "greater_than_equal"),
        ("longitude", 181, "less_than_equal"),
        ("longitude", -181, "greater_than_equal"),
    ],
    ids=["偏移上限外", "偏移下限外", "纬度上限外", "纬度下限外", "经度上限外", "经度下限外"],
)
def test_field_level_bounds_are_pydantic_validation(client: TestClient, field: str, value: object, code: str) -> None:
    """单字段越 `ge/le` 界 → 422 `detail`，不是信封（AGENTS 第 4 条）。"""
    response = _post(client, **{field: value})
    assert response.status_code == 422
    body = response.json()
    assert "error" not in body
    assert body["detail"][0]["loc"] == ["body", field]
    assert body["detail"][0]["type"] == code


def test_a_missing_location_is_an_envelope_not_a_validation_error(client: TestClient) -> None:
    """坐标与城市皆缺是前提问题（每字段单独看都合法）→ 引擎 400 信封，读 `error.code`。"""
    response = _post(client, latitude=None, longitude=None)
    assert response.status_code == 400
    body = response.json()
    assert "detail" not in body
    assert set(body["error"]) == {"code", "message"}
    assert body["error"]["code"] == "invalid_birth_data"


def test_an_unknown_house_system_is_an_unsupported_method_envelope(client: TestClient) -> None:
    """宫制是字符串、pydantic 无枚举约束，由引擎判定 → `UnsupportedMethodError` → 422 信封。

    `UnsupportedMethodError` 覆写状态码为 422（`app/core/errors.py`），不是基类默认 400；
    它是字段之间/前提错误（值本身格式合法，坏在引擎不认），所以走信封而非 pydantic `detail`。
    """
    response = _post(client, house_system="Z")
    assert response.status_code == 422
    body = response.json()
    assert "detail" not in body
    assert body["error"]["code"] == "unsupported_method"


def test_the_natal_chart_echoes_the_offset_it_was_given(client: TestClient) -> None:
    """契约回显：本命盘顶层带 `utc_offset_hours` 与 `utc_offset_source`（行运/合盘顶层没有，见各自 api）。"""
    body = _body(client, utc_offset_hours=5.5)
    assert {"utc_offset_hours", "utc_offset_source"} <= set(body)
    assert body["utc_offset_hours"] == 5.5
