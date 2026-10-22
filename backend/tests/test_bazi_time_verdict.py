"""岁运 / 流日 / 流时三页结论卡（verdict-card spec §4）的装配测：页级 `verdict` 逐字段断言。

锚点口径（任务冻结）：
- 岁运：`mean(year.score.value)`，均值过 `grade_for`；
- 流日：`focused.score.value`，无聚焦日则退回 `month_score.value`；
- 流时：`focused.score.value`，无聚焦则退回 `day_score.value`。

档位 / 星级一律过共享 `engines.verdict.grade_for`，headline / points / advice 全部来自
`content/bazi_transit_plain` 的结论卡框架句。本测按字段断言，不整字典对拍；三个系统各取
≥3 个不同案例（含无聚焦退回、低分段落凶档）。
"""

from datetime import date

import pytest

from app.content.bazi_transit_plain import (
    BAZI_TRANSIT_TIER_ADVICE,
    BAZI_TRANSIT_VERDICT_OUTLOOK,
)
from app.engines.verdict import GRADE_BANDS, grade_for

import tests.test_bazi_liuri as liuri
import tests.test_bazi_liushi as liushi
import tests.test_bazi_transit as transit


def _check_card(anchor: float, result, *, expect_points: int) -> None:
    """同一份字段断言：grade/stars 与 grade_for(anchor) 一致，三件文案非空且出自语料。"""
    grade, stars = grade_for(anchor)
    card = result.verdict
    assert card.grade == grade
    assert card.stars == stars
    assert BAZI_TRANSIT_VERDICT_OUTLOOK[grade] in card.headline
    assert grade in card.headline
    assert len(card.points) == expect_points
    assert all(isinstance(point, str) and point for point in card.points)
    assert card.advice.startswith("综合建议：")
    assert card.advice


# ---------------------------------------------------------------- 岁运（均值锚点）
def test_transit_default_mean_maps_to_ping() -> None:
    result = transit._default()
    anchor = sum(year.score.value for year in result.years) / len(result.years)
    assert anchor == pytest.approx(55.8)
    _check_card(anchor, result, expect_points=3)
    assert result.verdict.grade == "平"
    assert result.verdict.stars == 3


def test_transit_single_year_2029_maps_to_ji() -> None:
    result = transit._transit(start_year=2029, end_year=2029)
    anchor = result.years[0].score.value
    _check_card(anchor, result, expect_points=3)
    assert result.verdict.grade == "吉"
    assert result.verdict.stars == 4


def test_transit_childhood_span_mean_maps_to_ping() -> None:
    result = transit._transit(start_year=1990, end_year=1992)
    anchor = sum(year.score.value for year in result.years) / len(result.years)
    _check_card(anchor, result, expect_points=3)
    assert result.verdict.grade == "平"
    assert result.verdict.stars == 3


# ---------------------------------------------------------------- 流日（聚焦优先，退回月段）
def test_liuri_bare_anchors_on_month_score() -> None:
    result = liuri._matrix()
    assert result.focused is None
    _check_card(result.month_score.value, result, expect_points=1)
    assert result.verdict.grade == "平"
    assert result.verdict.stars == 3
    assert result.month_ganzhi in result.verdict.points[0]


def test_liuri_focused_anchors_on_focus_day() -> None:
    result = liuri._matrix_focused()
    assert result.focused is not None
    _check_card(result.focused.score.value, result, expect_points=2)
    assert result.verdict.grade == "平"
    assert result.verdict.stars == 3
    assert result.focused.solar_date in result.verdict.points[1]


def test_liuri_hostile_segment_anchors_to_xiong() -> None:
    result = liuri.compute_liuri_matrix(
        **liuri._NATAL_KWARGS,
        anchor_date=date(2026, 6, 15),
        reference_date=date(2026, 6, 15),
    )
    assert result.focused is None
    _check_card(result.month_score.value, result, expect_points=1)
    assert result.verdict.grade == "凶"
    assert result.verdict.stars == 1


# ---------------------------------------------------------------- 流时（聚焦优先，退回日段）
def test_liushi_bare_anchors_on_day_score() -> None:
    result = liushi._bare()
    assert result.focused is None
    _check_card(result.day_score.value, result, expect_points=1)
    assert result.verdict.grade == "平"
    assert result.verdict.stars == 3
    assert result.day_ganzhi in result.verdict.points[0]


def test_liushi_focused_anchors_on_focus_hour() -> None:
    result = liushi._focused()
    assert result.focused is not None
    _check_card(result.focused.score.value, result, expect_points=2)
    assert result.verdict.grade == "大吉"
    assert result.verdict.stars == 5
    assert result.focused.zhi in result.verdict.points[1]


def test_liushi_zero_day_anchors_to_xiong() -> None:
    result = liushi.compute_liushi_day(
        **liushi._NATAL_KWARGS,
        solar_date=date(2026, 6, 15),
        reference_date=date(2026, 6, 15),
    )
    assert result.focused is None
    _check_card(result.day_score.value, result, expect_points=1)
    assert result.verdict.grade == "凶"
    assert result.verdict.stars == 1


# ---------------------------------------------------------------- 语料键集自守
def test_verdict_outlook_keys_are_exactly_the_five_grades() -> None:
    assert set(BAZI_TRANSIT_VERDICT_OUTLOOK) == {band[1] for band in GRADE_BANDS}


def test_tier_advice_keys_are_the_three_tiers() -> None:
    assert set(BAZI_TRANSIT_TIER_ADVICE) == {"顺", "平", "滞"}
