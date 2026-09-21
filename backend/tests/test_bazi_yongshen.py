"""用神三法：扶抑定基准，通关/调候只增不减，冲突如实并列（spec §6.5）。

下面的加权分是基准命 A-F 的真实数值（`element_weight_scores` 跑出来的），
所以断言可就地重算，不是凑出来的。
"""

import pytest

from app.content.bazi_tiaohou import SEASON_BY_MONTH_ZHI, TIAOHOU_PRESCRIPTION
from app.engines.bazi_yongshen import TIAOHOU_ALREADY_PRESENT, TONGGUAN_MIN_RATIO, select_yongshen

# 基准命 A：戊辰 甲寅 庚子 丁亥
CHART_A_WEIGHTS = {"木": 2.2, "火": 1.3, "土": 1.7, "金": 1.0, "水": 1.7}
# 基准命 E：戊午 乙丑 壬午 癸卯
CHART_E_WEIGHTS = {"木": 2.0, "火": 1.2, "土": 2.2, "金": 0.1, "水": 2.3}


def _chart_a(**override):
    args = dict(
        level="weak", day_master_element="金", month_zhi="寅", element_scores=CHART_A_WEIGHTS
    )
    args.update(override)
    return select_yongshen(**args)


def _chart_e(**override):
    args = dict(
        level="weak", day_master_element="水", month_zhi="丑", element_scores=CHART_E_WEIGHTS
    )
    args.update(override)
    return select_yongshen(**args)


def _method(result, name):
    return next(m for m in result.methods if m.method == name)


def test_fuyi_gives_the_base_set_for_a_weak_day_master() -> None:
    result = _chart_a()
    assert result.favorable_elements == ["土", "金"]
    assert result.unfavorable_elements == ["木", "水", "火"]
    assert _method(result, "扶抑").fired_rule == "weak.take-resource-and-parallel"


def test_guantong_stays_out_when_the_clash_is_one_sided() -> None:
    """A: 木2.2 vs 土1.7 clash, but 1.7/2.2 = 0.77 < 0.80 → not a standoff."""
    method = _method(_chart_a(), "通关")
    assert method.chosen_elements == []
    assert method.fired_rule == "clash-too-uneven"
    assert method.already_present is False  # 未选法，谈不上"已有"
    assert TONGGUAN_MIN_RATIO == pytest.approx(0.8)


def test_guantong_stays_out_when_the_top_two_do_not_clash() -> None:
    """C（戊辰 丙辰 乙巳 癸未）：前二 土2.9/火1.9 相生，压根不是"克"。"""
    method = _method(
        _chart_a(
            day_master_element="木",
            month_zhi="辰",
            element_scores={"木": 1.7, "火": 1.9, "土": 2.9, "金": 0.3, "水": 1.2},
        ),
        "通关",
    )
    assert method.fired_rule == "top-two.no-clash"
    assert method.chosen_elements == []


def test_guantong_fires_and_deduplicates_against_fuyi() -> None:
    """E: 水2.3 vs 土2.2 → mediating 金, already a 扶抑 choice; the method still reports."""
    result = _chart_e()
    method = _method(result, "通关")
    assert method.fired_rule == "mediates.土生金"
    assert method.chosen_elements == ["金"]  # 本法自己的选法
    assert method.already_present is True  # 但金本就在扶抑喜集里，不重复计
    assert result.favorable_elements == ["水", "金"]  # 加权分降序、去重
    assert result.conflict is None


def test_balanced_seasons_record_that_they_did_not_fire() -> None:
    assert SEASON_BY_MONTH_ZHI["寅"] == "spring"
    assert TIAOHOU_PRESCRIPTION["spring"] is None
    method = _method(_chart_a(), "调候")
    assert method.chosen_elements == []
    assert method.fired_rule == "season-balanced"


def test_winter_tiaohou_is_marked_already_present_when_fire_is_strong() -> None:
    """E again: 火 1.2/7.8 = 15.4% ≥ 15% → record it, do not add it."""
    method = _method(_chart_e(), "调候")
    assert method.fired_rule == "winter.take-火"
    assert method.chosen_elements == ["火"]
    assert method.already_present is True
    assert "火" not in _chart_e().favorable_elements
    assert TIAOHOU_ALREADY_PRESENT == pytest.approx(0.15)


def test_tiaohou_adds_a_missing_cure_and_records_the_clash_with_fuyi() -> None:
    """火弱、午月：调候取水，而水只占 0.2/5.2=3.8% → 真的补进喜集；水又是扶抑忌 → conflict。"""
    result = _chart_a(
        day_master_element="火",
        month_zhi="午",
        element_scores={"木": 1.2, "火": 2.0, "土": 1.0, "金": 0.8, "水": 0.2},
    )
    method = _method(result, "调候")
    assert method.fired_rule == "summer.take-水"
    assert method.already_present is False
    assert result.favorable_elements == ["火", "木", "水"]
    assert result.unfavorable_elements == ["土", "金", "水"]  # 只增不减，忌集原样保留
    assert result.conflict.element == "水"
    assert result.conflict.suppressed_by == "扶抑"
    assert "季节纲要" in result.conflict.source


def test_balanced_level_produces_no_fuyi_base_set() -> None:
    """D（中和）：三法皆不取时，响应是空集合而不是编一个默认喜用."""
    result = _chart_a(
        level="balanced",
        day_master_element="火",
        element_scores={"木": 1.5, "火": 2.2, "土": 2.1, "金": 1.0, "水": 1.1},
    )
    assert result.favorable_elements == []
    assert result.unfavorable_elements == []
    assert _method(result, "扶抑").fired_rule == "balanced.no-preference"


def test_conflict_is_recorded_when_a_later_method_overrides_fuyi() -> None:
    """Injected case: 甲木身强, 木3.0/金2.8 clash → 通关取水, 而水正是扶抑忌神."""
    result = _chart_a(
        level="strong",
        day_master_element="木",
        month_zhi="卯",
        element_scores={"木": 3.0, "火": 0.9, "土": 0.7, "金": 2.8, "水": 0.6},
    )
    assert _method(result, "通关").chosen_elements == ["水"]
    assert result.conflict is not None
    assert result.conflict.element == "水"
    assert result.conflict.suppressed_by == "扶抑"
    assert "水" in result.favorable_elements  # 后两法只增不减（spec §6.5）
    assert "水" in result.unfavorable_elements  # 冲突如实并列，不做静默取舍
    assert "模型参数" in result.conflict.source
