"""Classical five-element (五行) reference tables shared across systems.

These are immutable facts of Chinese metaphysics, used by the BaZi engine
(day-master strength / useful-god analysis) and the Zhouyi engine (六亲
relationship of each najia branch to its hexagram palace). They live in one
place so every system derives element relationships from a single source.

Cycles:
* 相生 (generates): 木生火, 火生土, 土生金, 金生水, 水生木.
* 相克 (controls):  木克土, 土克水, 水克火, 火克金, 金克木.
"""

# Canonical ordering of the five elements (木 fire earth metal water).
ELEMENT_ORDER = ("木", "火", "土", "金", "水")

# Heavenly stem (天干) -> element.
GAN_ELEMENT = {
    "甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土",
    "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水",
}

# Earthly branch (地支) -> element.
ZHI_ELEMENT = {
    "子": "水", "丑": "土", "寅": "木", "卯": "木", "辰": "土", "巳": "火",
    "午": "火", "未": "土", "申": "金", "酉": "金", "戌": "土", "亥": "水",
}

# 五行相生 (X generates Y).
GENERATES = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
# 五行相克 (X controls Y).
CONTROLS = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}
# Inverses: element -> what generates it, and what controls it.
GENERATED_BY = {value: key for key, value in GENERATES.items()}
CONTROLLED_BY = {value: key for key, value in CONTROLS.items()}
