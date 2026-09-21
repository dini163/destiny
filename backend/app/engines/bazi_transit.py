"""岁运（流年 / 流月）引擎：区间解析、排盘时刻共用件，与其后的命中判定与账本装配。

本模块**不重复**任何命局推导：喜忌取自 `select_yongshen` 的合并结果，关系、合局、
神煞由 `bazi_rules` 的三个 derive 函数带上岁运之柱重扫一遍，柱的十神 / 地势 / 纳音
由 `bazi_pillar.build_transit_pillar` 合成。计分是岁运自己的一张表
（`content/bazi_transit_rules`，46 条），命局的 39 条判语、旺衰三因子与用神都不参
与，也不被改写（spec §4 决策 3）。

`resolve_natal_moment` 住在这里是刻意的：岁运要再走一次 `getYun()` 才拿得到流年与
流月对象，而那一刻必须先和主命盘用同一个真太阳时校正 —— 校正逻辑有两份，迟早分出
两个口径。所以它从 `compute_bazi_chart` 里原样搬来，主命盘改为消费它。
"""

from dataclasses import dataclass
from datetime import date, datetime, time

from lunar_python import Lunar, Solar

from app.core.errors import TransitRangeError
from app.schemas.common import CalendarType
from app.solar.true_solar_time import true_solar_offset_minutes, true_solar_time

#: 缺省区间长度与上限（spec §7.2）：一年一秒都不多给，越线即 422，不做静默裁剪。
TRANSIT_DEFAULT_YEARS = 5
TRANSIT_MAX_YEARS = 10


@dataclass(frozen=True)
class TransitRange:
    """请求区间被补齐之后的样子：`focus_year` 为空表示只出年表、不展开流月。"""

    start_year: int
    end_year: int
    focus_year: int | None


def resolve_transit_range(
    *,
    start_year: int | None,
    end_year: int | None,
    focus_year: int | None,
    reference_year: int,
    supported_from: int,
    supported_to: int,
) -> TransitRange:
    """补齐缺省、再做四道校验，产出实际要推演的年份区间。

    校验次序即依赖次序：先确认区间自身成形（倒序），再确认它不太宽，再确认它落在
    这个命盘推得出的年份里，最后才看 focus 年 —— 顺序换了，同一份入参报出来的码就
    换了，而调用方要的是一个能据以改表单的码。
    """
    span_start = start_year
    span_end = end_year
    if span_start is None and span_end is None:
        span_start = reference_year
    if span_end is None:
        span_end = span_start + TRANSIT_DEFAULT_YEARS - 1
    if span_start is None:
        span_start = span_end - TRANSIT_DEFAULT_YEARS + 1

    if span_end < span_start:
        raise TransitRangeError(
            "transit_range_reversed",
            f"起始年 {span_start} 晚于结束年 {span_end}，区间无从推起。",
            {"start_year": span_start, "end_year": span_end},
        )
    requested = span_end - span_start + 1
    if requested > TRANSIT_MAX_YEARS:
        raise TransitRangeError(
            "transit_range_too_wide",
            f"区间跨度 {requested} 年，超出 {TRANSIT_MAX_YEARS} 年上限。",
            {"max_years": TRANSIT_MAX_YEARS, "requested": requested},
        )
    if span_start < supported_from or span_end > supported_to:
        raise TransitRangeError(
            "transit_range_unsupported",
            f"本命盘的大运覆盖 {supported_from}—{supported_to} 年，"
            f"请求的 {span_start}—{span_end} 年在其之外。",
            {
                "supported_from": supported_from,
                "supported_to": supported_to,
                "requested_from": span_start,
                "requested_to": span_end,
            },
        )
    if focus_year is not None and not span_start <= focus_year <= span_end:
        raise TransitRangeError(
            "transit_focus_out_of_range",
            f"聚焦年 {focus_year} 不在 {span_start}—{span_end} 年区间内。",
            {"focus_year": focus_year, "start_year": span_start, "end_year": span_end},
        )
    return TransitRange(start_year=span_start, end_year=span_end, focus_year=focus_year)


@dataclass(frozen=True)
class NatalMoment:
    """排盘输入经真太阳时校正后的那一刻，与由它起出的 lunar-python 对象。

    `standard_datetime` 是用户填的那一刻（响应里的 `standard_datetime` 字段），
    `chart_datetime` 是校正后实际起柱的那一刻；关掉校正时两者相同，且
    `true_solar_time_text` / `offset_minutes` 留空而不是填 0 —— "没校正"和"校正量
    恰为零"是两件事。
    """

    standard_datetime: datetime
    chart_datetime: datetime
    longitude_used: float
    true_solar_time_text: str | None
    offset_minutes: float | None
    lunar: Lunar
    eight_char: object  # lunar_python.EightChar；本仓一贯不依赖其类型名


def resolve_natal_moment(
    *,
    birth_date: date,
    birth_time: time,
    calendar: CalendarType,
    longitude: float,
    apply_true_solar_time: bool,
) -> NatalMoment:
    """Resolve birth input into the instant the chart is actually cast from.

    A lunar-calendar date is converted to its Gregorian equivalent (preserving
    the wall-clock time) so both the True Solar Time correction and the pillar
    derivation operate on one standard civil datetime; ``lunar-python`` uses the
    supplied wall-clock time verbatim, hence the correction is applied *before*
    ``Solar(...)`` is constructed.
    """
    standard_dt = _standard_datetime(birth_date, birth_time, calendar)

    if apply_true_solar_time:
        chart_dt = true_solar_time(standard_dt, longitude)
        offset_minutes: float | None = round(true_solar_offset_minutes(standard_dt, longitude), 2)
        tst_text: str | None = chart_dt.strftime("%Y-%m-%d %H:%M")
    else:
        chart_dt = standard_dt
        offset_minutes = None
        tst_text = None

    solar = Solar.fromYmdHms(
        chart_dt.year, chart_dt.month, chart_dt.day, chart_dt.hour, chart_dt.minute, chart_dt.second
    )
    lunar = solar.getLunar()
    return NatalMoment(
        standard_datetime=standard_dt,
        chart_datetime=chart_dt,
        longitude_used=longitude,
        true_solar_time_text=tst_text,
        offset_minutes=offset_minutes,
        lunar=lunar,
        eight_char=lunar.getEightChar(),
    )


def _standard_datetime(birth_date: date, birth_time: time, calendar: CalendarType) -> datetime:
    """Return the civil standard-time datetime for the supplied birth data."""
    if calendar is CalendarType.LUNAR:
        lunar = Lunar.fromYmdHms(
            birth_date.year,
            birth_date.month,
            birth_date.day,
            birth_time.hour,
            birth_time.minute,
            birth_time.second,
        )
        solar = lunar.getSolar()
        return datetime(
            solar.getYear(),
            solar.getMonth(),
            solar.getDay(),
            solar.getHour(),
            solar.getMinute(),
            solar.getSecond(),
        )
    return datetime.combine(birth_date, birth_time)
