"""Rolling report windows assembled from authoritative transit solar-term boundaries."""

from calendar import monthrange
from datetime import date, timedelta

from app.core.chart_input import chart_longitude
from app.core.errors import TransitRangeError
from app.engines.bazi_transit import compute_transit


def shift_month(anchor: date, offset: int) -> date:
    absolute = anchor.year * 12 + anchor.month - 1 + offset
    year, month0 = divmod(absolute, 12)
    month = month0 + 1
    try:
        return date(year, month, min(anchor.day, monthrange(year, month)[1]))
    except ValueError as error:
        raise TransitRangeError(
            "transit_range_unsupported", "该起始日无法展开完整报告周期，请选择支持范围内的日期。"
        ) from error


def rolling_months(request, reference_date: date | None):
    """Civil month buckets clip, but never rederive, the lunar-python term intervals."""
    start = getattr(request, "start_date", None) or reference_date or date.today()
    end = shift_month(start, 12) - timedelta(days=1)
    longitude = chart_longitude(request.city, request.longitude, request.apply_true_solar_time)
    terms = []
    # January can belong to the preceding solar-term year; retain that real interval.
    first_year = start.year - 1 if start.month <= 2 else start.year
    for year in range(first_year, end.year + 1):
        result = compute_transit(
            birth_date=request.birth_date,
            birth_time=request.birth_time,
            calendar=request.calendar,
            longitude=longitude,
            gender=request.gender,
            apply_true_solar_time=request.apply_true_solar_time,
            start_year=year,
            end_year=year,
            focus_year=year,
            reference_date=reference_date,
            name=request.name,
        )
        terms.extend(month for row in result.years for month in (row.months or []))
    months = []
    for index in range(12):
        left = shift_month(start, index)
        right = shift_month(start, index + 1) - timedelta(days=1)
        pieces = []
        for term in terms:
            a = max(left, date.fromisoformat(term.start_solar))
            b = min(right, date.fromisoformat(term.end_solar))
            if a <= b:
                pieces.append((a, b, term))
        pieces.sort(key=lambda piece: piece[0])
        cursor = left
        for a, b, _ in pieces:
            if a != cursor:
                raise TransitRangeError(
                    "report_month_coverage",
                    "该时段的节气月覆盖不完整，请调整起始日。",
                    {"start_date": str(left)},
                )
            cursor = b + timedelta(days=1)
        if cursor != right + timedelta(days=1):
            raise TransitRangeError(
                "report_month_coverage",
                "该时段的节气月覆盖不完整，请调整起始日。",
                {"start_date": str(left)},
            )
        months.append((left, right, pieces))
    return start, end, months
