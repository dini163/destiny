"""Line-level reference tables for 装卦 (dressing a hexagram): 纳甲 and 六神.

纳甲 (Jing Fang najia) assigns a heavenly stem and earthly branch to each of the
six lines. The lower trigram (内卦) supplies lines 1-3 from its *inner* triple;
the upper trigram (外卦) supplies lines 4-6 from its *outer* triple. Only 乾 and
坤 use different stems for inner and outer; the other six trigrams keep one stem.

六神 (the six spirits / 六兽) adorn lines 1-6 in a fixed cyclic order starting
from a beast chosen by the day's heavenly stem (日干).

These are immutable classical tables (real reference data), not runtime output.
"""

#: 装卦表的出处（只有周易一页引它，故不并进偏差 5 的三张共用串）。
ZHOUYI_NAJIA_SOURCE = "京房纳甲爻辰与六神日干起例"

# Trigram key -> {"inner": lines 1-3, "outer": lines 4-6} as (stem, branch) pairs.
NAJIA: dict[str, dict[str, tuple[tuple[str, str], ...]]] = {
    "qian": {"inner": (("甲", "子"), ("甲", "寅"), ("甲", "辰")), "outer": (("壬", "午"), ("壬", "申"), ("壬", "戌"))},
    "kun":  {"inner": (("乙", "未"), ("乙", "巳"), ("乙", "卯")), "outer": (("癸", "丑"), ("癸", "亥"), ("癸", "酉"))},
    "zhen": {"inner": (("庚", "子"), ("庚", "寅"), ("庚", "辰")), "outer": (("庚", "午"), ("庚", "申"), ("庚", "戌"))},
    "xun":  {"inner": (("辛", "丑"), ("辛", "亥"), ("辛", "酉")), "outer": (("辛", "未"), ("辛", "巳"), ("辛", "卯"))},
    "kan":  {"inner": (("戊", "寅"), ("戊", "辰"), ("戊", "午")), "outer": (("戊", "申"), ("戊", "戌"), ("戊", "子"))},
    "li":   {"inner": (("己", "卯"), ("己", "丑"), ("己", "亥")), "outer": (("己", "酉"), ("己", "未"), ("己", "巳"))},
    "gen":  {"inner": (("丙", "辰"), ("丙", "午"), ("丙", "申")), "outer": (("丙", "戌"), ("丙", "子"), ("丙", "寅"))},
    "dui":  {"inner": (("丁", "巳"), ("丁", "卯"), ("丁", "丑")), "outer": (("丁", "亥"), ("丁", "酉"), ("丁", "未"))},
}


def najia_for_hexagram(lower_key: str, upper_key: str) -> tuple[tuple[str, str], ...]:
    """Return the six ``(stem, branch)`` pairs for lines 1-6 of a hexagram."""
    return NAJIA[lower_key]["inner"] + NAJIA[upper_key]["outer"]


# 六神 in their fixed cyclic order (applied to lines 1-6 from the day-stem start).
LIUSHEN_ORDER: tuple[str, ...] = ("青龙", "朱雀", "勾陈", "螣蛇", "白虎", "玄武")

# Day heavenly stem -> starting 六神 index (甲乙起青龙, 丙丁起朱雀, …).
LIUSHEN_START_BY_DAY_GAN: dict[str, int] = {
    "甲": 0, "乙": 0,   # 青龙
    "丙": 1, "丁": 1,   # 朱雀
    "戊": 2,            # 勾陈
    "己": 3,            # 螣蛇
    "庚": 4, "辛": 4,   # 白虎
    "壬": 5, "癸": 5,   # 玄武
}


def liushen_for_day_gan(day_gan: str) -> tuple[str, ...]:
    """Return the six 六神 names for lines 1-6 given the day's heavenly stem."""
    start = LIUSHEN_START_BY_DAY_GAN[day_gan]
    return tuple(LIUSHEN_ORDER[(start + offset) % 6] for offset in range(6))
