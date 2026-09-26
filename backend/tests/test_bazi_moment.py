"""农历入参越界：小月填三十必须是带机器码的域错误，而不是裸 500（findings F-A1-1）。

`_standard_datetime` 是全仓唯一的 `Lunar.fromYmdHms` 调用点（grep 实测 2026-09-26：`app/` 内
只有这一处分支判 `CalendarType.LUNAR`），所以八字本命、岁运、流日、流时、合婚与紫微这六套
端点共用这一道门。lunar-python 对小月三十直接抛裸 `Exception`，`register_error_handlers`
只认 `DestinyError`，于是症状是 HTTP 500、无机器码、前端只能显示一句"服务器错误"—— 而真相
是「这个农历月没有三十」，一句用户改得动的实话。

日数取自 `LunarMonth.getDayCount()`，即权威库自己那张表（AGENTS.md 第 6 条：历法不自算）。
状态码 400 沿用 `InvalidBirthDataError` 的既有口径（`tests/test_bazi_hehun_api.py:112` 明写
"400 不是笔误"），这里不为农历越界另开一个码。

两道门按 AGENTS.md 第 4 条分工，所以两边各留一条测：`2023-02-30` 这种连公历都不存在的日子
由 pydantic 拦（422 `detail`），而每个字段单看都合法的「农历六月三十落在 29 天的小月」由引擎
拦（400 `invalid_birth_data`）。
"""

from datetime import date, time

import pytest
from fastapi.testclient import TestClient

from app.core.errors import InvalidBirthDataError
from app.engines.bazi_moment import resolve_natal_moment
from app.schemas.common import CalendarType

#: 1900 年正月是 29 天的小月（`LunarMonth.fromYm(1900, 1).getDayCount() == 29`），三十不存在。
#: 公历 1900-01-30 是真实的一天，所以这份输入能过 pydantic —— 坏的只是它与农历月的关系。
_IMPOSSIBLE = date(1900, 1, 30)


def _moment(birth_date: date, calendar: CalendarType = CalendarType.LUNAR):
    return resolve_natal_moment(
        birth_date=birth_date,
        birth_time=time(10, 0),
        calendar=calendar,
        longitude=116.4074,
        apply_true_solar_time=False,
    )


@pytest.mark.parametrize(("lunar_date", "month_days"), [(_IMPOSSIBLE, 29), (date(2023, 6, 30), 29)])
def test_a_day_the_lunar_month_does_not_have_is_a_domain_error(
    lunar_date: date, month_days: int
) -> None:
    with pytest.raises(InvalidBirthDataError) as raised:
        _moment(lunar_date)
    error = raised.value
    assert error.code == "invalid_birth_data"
    assert error.status_code == InvalidBirthDataError.status_code
    assert error.context == {"lunar_month_days": month_days}
    # 文案要自带可改正的事实：读者不看 context 也知道该把日改成几。
    assert str(month_days) in error.message and str(lunar_date.day) in error.message


@pytest.mark.parametrize("lunar_date", [date(1900, 1, 29), date(2025, 6, 30), date(2023, 12, 29)])
def test_a_day_the_lunar_month_has_casts(lunar_date: date) -> None:
    """边界另一侧：小月的最后一天与大月的三十日照常起盘。少这一条，`day >= days` 的
    越界写法也能绿。"""
    charted = _moment(lunar_date)
    assert charted.lunar.getYear() == lunar_date.year
    assert charted.lunar.getMonth() == lunar_date.month
    assert charted.lunar.getDay() == lunar_date.day


def test_the_same_day_number_is_fine_on_the_solar_path() -> None:
    """越界只属于农历：同一个 1900-01-30 走公历是真实存在的一天，不该被拦。"""
    assert _moment(_IMPOSSIBLE, CalendarType.SOLAR).standard_datetime.date() == _IMPOSSIBLE


@pytest.mark.parametrize("url", ["/api/v1/bazi/natal", "/api/v1/ziwei/chart"])
def test_the_single_cast_endpoints_answer_the_domain_envelope(client: TestClient, url: str) -> None:
    """走查实测这两处在修复前返回 500 且响应体没有 `error` 键（findings F-A1-1）。"""
    response = client.post(
        url,
        json={
            "birth_date": _IMPOSSIBLE.isoformat(),
            "birth_time": "10:00",
            "calendar": "lunar",
            "longitude": 116.4074,
            "gender": "male",
            "apply_true_solar_time": False,
        },
    )
    assert response.status_code == 400, response.text
    assert response.json()["error"]["code"] == "invalid_birth_data"


def test_the_hehun_endpoint_names_the_partner_whose_lunar_day_is_impossible(
    client: TestClient,
) -> None:
    """合婚一造非法即整请求失败，并说得出是谁（§9.1/§9.2）；农历越界走的是同一条链。"""
    broken = {
        "birth_date": _IMPOSSIBLE.isoformat(),
        "birth_time": "10:00",
        "calendar": "lunar",
        "city": "成都",
        "apply_true_solar_time": False,
    }
    sound = {
        "birth_date": "1990-06-15",
        "birth_time": "10:00",
        "calendar": "solar",
        "city": "北京",
        "apply_true_solar_time": False,
    }
    response = client.post(
        "/api/v1/bazi/hehun",
        json={"male": broken, "female": sound, "reference_date": "2026-09-22"},
    )
    assert response.status_code == 400, response.text
    error = response.json()["error"]
    assert (error["code"], error["context"]["partner"]) == ("invalid_birth_data", "male")


def test_a_lunar_february_thirtieth_is_rejected_by_pydantic_before_the_engine(
    client: TestClient,
) -> None:
    """`birth_date` 是 `datetime.date`，公历 2 月 30 日在 pydantic 就死了：422 + `detail`，
    引擎根本不被调用。这一条钉住分工，免得后来人把农历越界整段搬进 schema。"""
    response = client.post(
        "/api/v1/bazi/natal",
        json={
            "birth_date": "2023-02-30",
            "birth_time": "10:00",
            "calendar": "lunar",
            "longitude": 116.4074,
            "gender": "male",
        },
    )
    assert response.status_code == 422
    body = response.json()
    assert "error" not in body and "detail" in body
