"""The eight trigrams (八卦) — the atomic building blocks of every hexagram.

A trigram is three lines read bottom-to-top (1 = yang 阳, 0 = yin 阴). A
hexagram stacks a lower trigram (lines 1-3, 内卦) beneath an upper trigram
(lines 4-6, 外卦). The ``meihua_number`` is the Fu Xi (先天) ordinal used by the
plum-blossom time-casting method; ``nature`` is the classical image (象).
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Trigram:
    """One of the eight trigrams."""

    key: str                 # latin identifier, e.g. "qian"
    name_zh: str             # 卦名, e.g. "乾"
    pinyin: str              # e.g. "qián"
    symbol: str              # Unicode trigram glyph, e.g. "☰"
    nature_zh: str           # image (象), e.g. "天"
    nature_en: str           # e.g. "heaven"
    element: str             # 五行, e.g. "金"
    binary: tuple[int, int, int]   # lines bottom-to-top, 1=yang 0=yin
    meihua_number: int       # Fu Xi ordinal 1-8 (乾1 兑2 离3 震4 巽5 坎6 艮7 坤8)


TRIGRAMS: tuple[Trigram, ...] = (
    Trigram("qian", "乾", "qián", "☰", "天", "heaven", "金", (1, 1, 1), 1),
    Trigram("dui",  "兑", "duì",  "☱", "泽", "lake",   "金", (1, 1, 0), 2),
    Trigram("li",   "离", "lí",   "☲", "火", "fire",   "火", (1, 0, 1), 3),
    Trigram("zhen", "震", "zhèn", "☳", "雷", "thunder", "木", (1, 0, 0), 4),
    Trigram("xun",  "巽", "xùn",  "☴", "风", "wind",   "木", (0, 1, 1), 5),
    Trigram("kan",  "坎", "kǎn",  "☵", "水", "water",  "水", (0, 1, 0), 6),
    Trigram("gen",  "艮", "gèn",  "☶", "山", "mountain", "土", (0, 0, 1), 7),
    Trigram("kun",  "坤", "kūn",  "☷", "地", "earth",  "土", (0, 0, 0), 8),
)

TRIGRAM_BY_KEY: dict[str, Trigram] = {t.key: t for t in TRIGRAMS}
# Nature image -> trigram key (used to parse compound hexagram names such as 水雷屯).
TRIGRAM_BY_NATURE: dict[str, str] = {t.nature_zh: t.key for t in TRIGRAMS}
# Trigram name -> key (used to parse pure hexagram names such as 乾为天).
TRIGRAM_BY_NAME: dict[str, str] = {t.name_zh: t.key for t in TRIGRAMS}
# Line pattern -> trigram key (used to resolve a cast lower/upper trigram).
TRIGRAM_BY_BINARY: dict[tuple[int, int, int], str] = {t.binary: t.key for t in TRIGRAMS}
# Fu Xi number -> trigram key (used by the plum-blossom time method).
TRIGRAM_BY_MEIHUA: dict[int, str] = {t.meihua_number: t.key for t in TRIGRAMS}
