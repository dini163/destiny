"""Birth-input helpers shared by natal and report adapters.

`solar/geo.resolve_longitude` 只管「城市认不认得出来」；这里的 `chart_longitude`
决定「校正开关下经度从哪来」。它曾经住在 `api/v1/bazi.py`，报告层（`api/v1/report.py`）
也要用同一口径 —— 提升到横切底层，两处引用同一份实现，改一处不会漏另一处
（AGENTS.md：同一条命在命盘页和报告页用同一条经线）。
"""

from app.solar.geo import resolve_longitude
from app.solar.true_solar_time import STANDARD_MERIDIAN_CN


def chart_longitude(
    city: str | None, longitude: float | None, apply_true_solar_time: bool
) -> float:
    """校正开启时经度必须由城市或显式经度定下来；关闭时两者皆可省，取标准经线。

    抛 `InvalidBirthDataError` 的是 `resolve_longitude`：城市认不出来就是一项入参错误。
    """
    if apply_true_solar_time:
        return resolve_longitude(city, longitude)
    return longitude if longitude is not None else STANDARD_MERIDIAN_CN
