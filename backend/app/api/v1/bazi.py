"""BaZi HTTP adapter (thin layer over the computation engines)."""

from fastapi import APIRouter

from app.engines.bazi import compute_bazi_chart
from app.engines.bazi_hehun import compute_hehun
from app.engines.bazi_liuri import compute_liuri_matrix
from app.engines.bazi_liushi import compute_liushi_day
from app.engines.bazi_transit import compute_transit
from app.schemas.bazi import BaziChart, BaziNatalRequest
from app.schemas.bazi_hehun import BaziHehunRequest, BaziHehunResult
from app.schemas.bazi_liuri import BaziLiuriRequest, BaziLiuriResult
from app.schemas.bazi_liushi import BaziLiushiRequest, BaziLiushiResult
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


@router.post(
    "/liuri/matrix", response_model=BaziLiuriResult, summary="Project a whole month of daily luck"
)
async def bazi_liuri_matrix(request: BaziLiuriRequest) -> BaziLiuriResult:
    """输出锚点日所在那一整个节气月的逐日吉凶，`focus_date` 时该日再下钻成三段明细。

    路由名带 `/matrix` 后缀是刻意的：粒度族名（`liuyue` / `liuri` / `liushi`）留给切片 4
    的"日内十二时辰"一个不撞名的位置（spec 决策 12）。

    两个日期一律原样透传：段定位与聚焦日归属都在引擎里判，失败时抛 `TransitRangeError`，
    经域错误处理器带着机器码与 `context` 出去 —— 这里若先用 pydantic 拦一道，前端就只剩
    `validation_error`，拿不到"这一段其实到 2028-02-03 为止"那两个日期。
    """
    return compute_liuri_matrix(
        birth_date=request.birth_date,
        birth_time=request.birth_time,
        calendar=request.calendar,
        longitude=_chart_longitude(request),
        gender=request.gender,
        apply_true_solar_time=request.apply_true_solar_time,
        anchor_date=request.anchor_date,
        focus_date=request.focus_date,
        reference_date=request.reference_date,
        name=request.name,
    )


@router.post(
    "/liushi/day", response_model=BaziLiushiResult, summary="Project a day of twelve hours"
)
async def bazi_liushi_day(request: BaziLiushiRequest) -> BaziLiushiResult:
    """输出一个八字日的十二时辰吉凶，`focus_hour_zhi` 时该时辰再下钻成四段明细。

    路由叫 `/day` 而不是 `/matrix`：一页就是一天，十二格恒在，没有"整段"可选。日界取
    23:00 属次日，所以 `solar_date` 是**八字日**而不是钟面上的那一天（spec §2.1）。

    两个入参一律原样透传：段定位与时辰归属都在引擎里判，失败时抛 `TransitRangeError`，
    经域错误处理器带着机器码与 `context` 出去 —— 这里若先用 pydantic 拦一道，前端就只剩
    `validation_error`，拿不到"可推年份 1988—2083"那两个数字。
    """
    return compute_liushi_day(
        birth_date=request.birth_date,
        birth_time=request.birth_time,
        calendar=request.calendar,
        longitude=_chart_longitude(request),
        gender=request.gender,
        apply_true_solar_time=request.apply_true_solar_time,
        solar_date=request.solar_date,
        focus_hour_zhi=request.focus_hour_zhi,
        reference_date=request.reference_date,
        name=request.name,
    )


@router.post(
    "/hehun",
    response_model=BaziHehunResult,
    summary="Compare two BaZi charts for marriage compatibility",
)
async def bazi_hehun(request: BaziHehunRequest) -> BaziHehunResult:
    """双人合盘：一次请求给全一页（总分、16 格矩阵、互补图、纳音、同频轴、宜忌）。

    这里薄到只剩转参数：两造各自的经线由引擎按 profile 决定（`profile_longitude`），
    不复用本文件的 `_chart_longitude` —— 那一个读的是单造请求上的那一份校正开关，
    而合婚的 `apply_true_solar_time` 是各造一份的（spec §5.1）。
    参考日也原样传下去：它的缺省只在引擎里解析一次，并经 `provenance.reference_date` 回显。
    """
    return compute_hehun(
        male=request.male,
        female=request.female,
        reference_date=request.reference_date,
        axis_start_year=request.axis_start_year,
        axis_years=request.axis_years,
    )
