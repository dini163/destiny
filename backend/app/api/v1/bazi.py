"""BaZi HTTP adapter (thin layer over the computation engines)."""

from fastapi import APIRouter

from app.engines.bazi import compute_bazi_chart
from app.engines.bazi_transit import compute_transit
from app.schemas.bazi import BaziChart, BaziNatalRequest
from app.schemas.bazi_transit import BaziTransitRequest, BaziTransitResult
from app.solar.geo import resolve_longitude
from app.solar.true_solar_time import STANDARD_MERIDIAN_CN

router = APIRouter(prefix="/bazi")


def _chart_longitude(request: BaziNatalRequest) -> float:
    """校正开启时经度必须由城市或显式经度定下来；关闭时两者皆可省，取标准经线。

    两个端点共用这一段判断，所以"同一条命在命盘页和岁运页用同一条经线"这件事只有一处
    实现，改一处不会漏另一处。抛 `InvalidBirthDataError` 的是 `resolve_longitude`：城市
    认不出来就是一项入参错误，与岁运区间无关。
    """
    if request.apply_true_solar_time:
        return resolve_longitude(request.city, request.longitude)
    return request.longitude if request.longitude is not None else STANDARD_MERIDIAN_CN


@router.post("/natal", response_model=BaziChart, summary="Compute a BaZi natal chart")
async def bazi_natal(request: BaziNatalRequest) -> BaziChart:
    """Chart the four pillars from birth data, applying True Solar Time by default.

    A location is required when True Solar Time correction is enabled; otherwise
    the standard meridian (120E) is assumed and no correction is applied. The
    reference date is passed through as supplied: its default lives in the
    engine and is echoed in ``provenance.reference_date``, so this adapter never
    has its own idea of "today".
    """
    return compute_bazi_chart(
        birth_date=request.birth_date,
        birth_time=request.birth_time,
        calendar=request.calendar,
        longitude=_chart_longitude(request),
        gender=request.gender,
        apply_true_solar_time=request.apply_true_solar_time,
        reference_date=request.reference_date,
        name=request.name,
    )


@router.post(
    "/liuyue", response_model=BaziTransitResult, summary="Project annual and monthly luck cycles"
)
async def bazi_liuyue(request: BaziTransitRequest) -> BaziTransitResult:
    """推演一段流年，`focus_year` 所指之年再下钻到十二节气流月。

    路由名沿用产品路线图的 `liuyue`（流月），而载荷同时含流年区间与可选流月 —— 改名会
    让本页与后续的 `/bazi/liuri/matrix`、`/bazi/liushi` 断成两套命名，故名字保粒度、
    契约保实态（spec 决策 7）。

    区间三个字段一律原样透传：缺省补齐、上限与"早于本命盘大运"的判定都在引擎里做，
    失败时抛 `TransitRangeError`，经域错误处理器带着机器码与 `context` 出去。这里若
    先用 pydantic 拦一道，前端就只剩 `validation_error`，拿不到"最多 10 年"那个数字。
    """
    return compute_transit(
        birth_date=request.birth_date,
        birth_time=request.birth_time,
        calendar=request.calendar,
        longitude=_chart_longitude(request),
        gender=request.gender,
        apply_true_solar_time=request.apply_true_solar_time,
        start_year=request.start_year,
        end_year=request.end_year,
        focus_year=request.focus_year,
        reference_date=request.reference_date,
        name=request.name,
    )
