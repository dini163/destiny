"""结论卡片档位派生的单元测（2026-10-21 verdict-card spec §3）。

`app/engines/verdict.py` 的五档映射是全仓共享的模型参数：六维账本均值 → (档位词, 星级)。
本文件钉三件事——① 五档阈值与边界逐值正确且单调；② `VERDICT_OUTLOOK` 的键与五档档位词
一一对应（框架句 `{outlook}` 槽按档位取词，缺档即 KeyError）；③ `TIER_ADVICE` 的键与
六维三档一一对应（建议句 `{tier_advice}` 槽按档位取词）。

阈值是模型参数（非古籍赋分，口径同 `MODEL_PARAM_SOURCE`），改阈值必须同步改
`app/engines/verdict.py` 的复测命令与本文件的边界值。
"""

import pytest

from app.content.bazi_plain import TIER_ADVICE, VERDICT_OUTLOOK
from app.engines.verdict import GRADE_BANDS, grade_for

GRADE_WORDS = [band[1] for band in GRADE_BANDS]
STAR_COUNTS = [band[2] for band in GRADE_BANDS]


@pytest.mark.parametrize(
    "score, grade, stars",
    [
        (100.0, "大吉", 5),
        (80.0, "大吉", 5),      # 上界含
        (79.99, "吉", 4),
        (65.0, "吉", 4),        # 65 是六维顺/平分界，均值至此整体即吉
        (64.99, "平", 3),
        (50.0, "平", 3),
        (49.99, "小凶", 2),
        (35.0, "小凶", 2),
        (34.99, "凶", 1),
        (0.0, "凶", 1),
    ],
)
def test_grade_for_maps_every_band_boundary(score: float, grade: str, stars: int) -> None:
    assert grade_for(score) == (grade, stars)


def test_grade_for_is_monotonic_and_covers_the_full_range() -> None:
    """档位随分只升不降；0-100 任意输入都有档（最末档为兜底，不必再抛 KeyError）。"""
    samples = [0.0, 34.99, 35.0, 49.99, 50.0, 64.99, 65.0, 79.99, 80.0, 100.0]
    stars = [grade_for(score)[1] for score in samples]
    assert stars == sorted(stars)  # 星级随分不降（单调）
    assert grade_for(-1.0) == (GRADE_WORDS[-1], STAR_COUNTS[-1])
    assert grade_for(101.0) == (GRADE_WORDS[0], STAR_COUNTS[0])


def test_verdict_outlook_keys_are_exactly_the_five_grades() -> None:
    """总论框架的 {outlook} 槽按档位取词：档位词表一动，语料必须跟上（多一档/少一档都红）。"""
    assert set(VERDICT_OUTLOOK) == set(GRADE_WORDS)


def test_tier_advice_keys_are_exactly_the_three_dimension_tiers() -> None:
    """建议句的 {tier_advice} 槽按六维档位取词，与 `bazi_interpret._tier` 的三档一致。"""
    assert set(TIER_ADVICE) == {"顺", "平", "滞"}
