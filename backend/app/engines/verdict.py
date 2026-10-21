"""结论卡片（verdict card）的共享档位派生：0-100 倾向分 → (档位词, 星级)。

只做两件事：五档映射表与 `grade_for`。各系统引擎把已有账本/盘面事实聚合成一个 0-100 的
倾向分（有账本的系统从 `ScoreValue.value` 聚合，无账本的由各系统判定层合成），再交给
本模块换档——判定本身住在各系统引擎里，本模块不认识任何系统，也不现编中文。

阈值口径（复测命令见 `GRADE_BANDS` 下方）：65/45 本就是八字六维顺/平/滞的分界
（`app/engines/bazi_interpret._tier`），均值 ≥65 意味着多数维度属顺，整体即吉及以上；
≥80 为多数维度强顺，取大吉；50-65 好坏相抵取平；35-50 多数偏滞取小凶；<35 取凶。
这五条阈值是模型参数（古籍只给定性不给数，同 `MODEL_PARAM_SOURCE` 的一贯口径），
将来调阈值必须同步改这里的复测命令与 golden 断言。
"""

from __future__ import annotations

from typing import Final

#: (下限, 档位词, 星级)，按分从高到低；`grade_for` 取第一个 `score >= 下限` 的档。
#: 复测：`cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "from app.engines.verdict import GRADE_BANDS; print([(b[0], b[1], b[2]) for b in GRADE_BANDS])"` → `[(80.0, '大吉', 5), (65.0, '吉', 4), (50.0, '平', 3), (35.0, '小凶', 2), (-1e309, '凶', 1)]`。
GRADE_BANDS: Final[tuple[tuple[float, str, int], ...]] = (
    (80.0, "大吉", 5),
    (65.0, "吉", 4),
    (50.0, "平", 3),
    (35.0, "小凶", 2),
    (float("-inf"), "凶", 1),
)


def grade_for(score: float) -> tuple[str, int]:
    """0-100 倾向分 → (档位词, 星级)。确定性、单调：分越高档位只升不降。"""
    for lower, grade, stars in GRADE_BANDS:
        if score >= lower:
            return grade, stars
    return GRADE_BANDS[-1][1], GRADE_BANDS[-1][2]
