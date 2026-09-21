"""岁运区间解析与排盘时刻共用件（spec §7.2、§5 的共用出口）。

区间一条线：缺省补齐 + 四道校验（倒序 / 过宽 / 越出大运窗 / focus 越界），错误走
`TransitRangeError` 的 422 而不是 pydantic 的 422 —— 前者是"这个命盘推不出这段
岁运"，后者是"你少填了一个字段"，两件事的文案与机器码都不该混在同一个 `code` 下。

排盘时刻一条线：`resolve_natal_moment` 是从 `compute_bazi_chart` 里原样搬出来的，
所以它的测法是"搬完仍等价" —— 拿它复现主命盘已经对外承诺的那几个字段，而不是另
造一套断言。
"""

from datetime import date, datetime, time

import pytest

from app.core.errors import TransitRangeError
from app.engines.bazi import compute_bazi_chart
from app.engines.bazi_transit import TransitRange, resolve_natal_moment, resolve_transit_range
from app.schemas.common import CalendarType

_WINDOW = {"supported_from": 1988, "supported_to": 2083}


def _range(**overrides: object) -> TransitRange:
    args: dict[str, object] = {
        "start_year": None,
        "end_year": None,
        "focus_year": None,
        "reference_year": 2026,
        **_WINDOW,
    }
    args.update(overrides)
    return resolve_transit_range(**args)  # type: ignore[arg-type]


def test_missing_bounds_default_to_five_years_from_the_reference() -> None:
    span = _range()
    assert (span.start_year, span.end_year, span.focus_year) == (2026, 2030, None)


def test_only_one_bound_supplies_the_other_by_the_default_span() -> None:
    from_start = _range(start_year=2000)
    from_end = _range(end_year=2000)
    assert (from_start.start_year, from_start.end_year) == (2000, 2004)
    assert (from_end.start_year, from_end.end_year) == (1996, 2000)


def test_ten_years_is_allowed_and_eleven_is_not() -> None:
    assert _range(start_year=2000, end_year=2009).end_year == 2009
    with pytest.raises(TransitRangeError) as excinfo:
        _range(start_year=2000, end_year=2010)
    assert excinfo.value.code == "transit_range_too_wide"
    assert excinfo.value.context == {"max_years": 10, "requested": 11}


def test_reversed_bounds_report_both_years() -> None:
    with pytest.raises(TransitRangeError) as excinfo:
        _range(start_year=2030, end_year=2029)
    assert excinfo.value.code == "transit_range_reversed"
    assert excinfo.value.context == {"start_year": 2030, "end_year": 2029}


def test_years_outside_the_luck_pillar_window_are_rejected() -> None:
    for start, end in ((1980, 1984), (2084, 2088)):
        with pytest.raises(TransitRangeError) as excinfo:
            _range(start_year=start, end_year=end)
        assert excinfo.value.code == "transit_range_unsupported"
        assert excinfo.value.context == {
            "supported_from": 1988,
            "supported_to": 2083,
            "requested_from": start,
            "requested_to": end,
        }


def test_focus_year_must_sit_inside_the_span() -> None:
    with pytest.raises(TransitRangeError) as excinfo:
        _range(start_year=2024, end_year=2028, focus_year=2030)
    assert excinfo.value.code == "transit_focus_out_of_range"
    assert excinfo.value.context == {"focus_year": 2030, "start_year": 2024, "end_year": 2028}


def test_error_status_is_422() -> None:
    with pytest.raises(TransitRangeError) as excinfo:
        _range(start_year=2030, end_year=2029)
    assert excinfo.value.status_code == 422


_BIRTH = (date(1988, 2, 15), time(23, 30))


def test_corrected_moment_matches_what_the_natal_chart_reports() -> None:
    """共用出口的第一条承诺：校正过的时刻就是主命盘已经对外给出的那几个字段。"""
    moment = resolve_natal_moment(
        birth_date=_BIRTH[0],
        birth_time=_BIRTH[1],
        calendar=CalendarType.SOLAR,
        longitude=104.1,
        apply_true_solar_time=True,
    )
    chart = compute_bazi_chart(
        birth_date=_BIRTH[0],
        birth_time=_BIRTH[1],
        calendar=CalendarType.SOLAR,
        longitude=104.1,
        gender="MALE",
        apply_true_solar_time=True,
    )
    assert moment.standard_datetime == datetime(1988, 2, 15, 23, 30)
    assert moment.true_solar_time_text == chart.true_solar_time == "1988-02-15 22:12"
    assert moment.offset_minutes == chart.tst_offset_minutes == -77.84
    assert moment.longitude_used == chart.longitude == 104.1
    assert moment.eight_char.toString() == chart.four_pillars
    assert moment.lunar.toString() == chart.lunar_date


def test_uncorrected_moment_carries_no_correction_to_invent() -> None:
    """关掉校正时不留"0 分钟"这种假事实：字段为空，且柱与主命盘的关闭路径同源。"""
    moment = resolve_natal_moment(
        birth_date=_BIRTH[0],
        birth_time=_BIRTH[1],
        calendar=CalendarType.SOLAR,
        longitude=104.1,
        apply_true_solar_time=False,
    )
    chart = compute_bazi_chart(
        birth_date=_BIRTH[0],
        birth_time=_BIRTH[1],
        calendar=CalendarType.SOLAR,
        longitude=104.1,
        gender="MALE",
        apply_true_solar_time=False,
    )
    assert moment.chart_datetime == moment.standard_datetime
    assert moment.true_solar_time_text is None
    assert moment.offset_minutes is None
    assert moment.eight_char.toString() == chart.four_pillars == "戊辰 甲寅 庚子 戊子"
