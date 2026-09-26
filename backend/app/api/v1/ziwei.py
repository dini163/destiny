"""紫微斗数 (Zi Wei Dou Shu) HTTP adapter (thin layer over the chart engine)."""

from fastapi import APIRouter

from app.engines.ziwei import compute_ziwei_chart
from app.schemas.ziwei import ZiweiChart, ZiweiRequest
from app.solar.geo import resolve_longitude
from app.solar.true_solar_time import STANDARD_MERIDIAN_CN

router = APIRouter(prefix="/ziwei")


def _chart_longitude(request: ZiweiRequest) -> float:
    """校正开启时经度必须由城市或显式经度定下来；关闭时取标准经线（同八字口径）。"""
    if request.apply_true_solar_time:
        return resolve_longitude(request.city, request.longitude)
    return request.longitude if request.longitude is not None else STANDARD_MERIDIAN_CN


@router.post("/chart", response_model=ZiweiChart, summary="Compute a Zi Wei Dou Shu chart")
async def ziwei_chart(request: ZiweiRequest) -> ZiweiChart:
    """Chart the 紫微斗数 board: 命宫 / 五行局 / 十四主星 / 四化 / 十二宫 / 大限.

    A location is required when True Solar Time correction is enabled (the 时辰
    must be honest); otherwise the standard meridian is assumed. Everything is
    derived deterministically from the 农历 birth data — no runtime invention.
    """
    return compute_ziwei_chart(
        birth_date=request.birth_date,
        birth_time=request.birth_time,
        calendar=request.calendar,
        longitude=_chart_longitude(request),
        gender=request.gender,
        apply_true_solar_time=request.apply_true_solar_time,
        name=request.name,
    )
