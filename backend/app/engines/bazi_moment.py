"""排盘时刻：把用户填的生辰校正成真太阳时，并起出历法对象。

`lunar-python` 原样使用它收到的墙上时间，不做任何天文或地理校正（PRD 7.2），所以校正
必须发生在 `Solar(...)` 之前，否则远离东经 120° 标准经线的命主会拿到错一个时辰的时柱
与日柱。这一步只有一个入口，两个消费者：`compute_bazi_chart` 用它起主命盘，
`compute_transit` 用它再走一次 `getYun()` 取流年与流月对象。

它单独立一个模块而不是住在某一个引擎里，是因为两个引擎都要它：谁住着，另一个就得反向
import —— 而岁运引擎本就要消费主命盘，环于是闭合，Python 会在半途初始化的模块上直接
ImportError。校正逻辑只有一份，两个口径就无从谈起。
"""

from dataclasses import dataclass
from datetime import date, datetime, time

from lunar_python import Lunar, Solar

from app.schemas.common import CalendarType
from app.solar.true_solar_time import true_solar_offset_minutes, true_solar_time


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
