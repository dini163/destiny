"""The 64 hexagrams (六十四卦): King Wen order, palace order and line structure.

Each hexagram is stored by its classical full name (e.g. ``水雷屯``, ``乾为天``),
which itself encodes the two component trigrams: for a compound name the first
character is the upper trigram's image and the second is the lower trigram's; a
pure hexagram is written ``<name>为<image>``. Trigrams — and therefore the six
lines — are parsed from these names rather than hand-entered, so the structure
cannot drift from the naming.

Two orderings of the same 64 names are curated and cross-checked:

* :data:`KING_WEN_SEQUENCE` — the received 卦序 (hexagram 1..64).
* :data:`PALACES` — the eight palaces (八宫) of the 京房 system, each listing its
  eight hexagrams in generation order (本宫 / 一世 … 五世 / 游魂 / 归魂). The
  palace fixes the 世 (shi) line, whose opposite is the 应 (ying) line, and the
  palace's five-element governs 六亲 assignment.
"""

from dataclasses import dataclass

from app.content.zhouyi_trigrams import TRIGRAM_BY_BINARY, TRIGRAM_BY_KEY, TRIGRAM_BY_NAME, TRIGRAM_BY_NATURE

# Generation names in palace order, and the 世 line position of each generation.
GENERATION_NAMES = ("本宫", "一世", "二世", "三世", "四世", "五世", "游魂", "归魂")
SHI_BY_GENERATION = (6, 1, 2, 3, 4, 5, 4, 3)

# King Wen sequence: (full_name_zh, short_name_zh, pinyin, english_name).
KING_WEN_SEQUENCE: tuple[tuple[str, str, str, str], ...] = (
    ("乾为天", "乾", "qián", "Heaven (The Creative)"),
    ("坤为地", "坤", "kūn", "Earth (The Receptive)"),
    ("水雷屯", "屯", "zhūn", "Difficulty at the Beginning"),
    ("山水蒙", "蒙", "méng", "Youthful Folly"),
    ("水天需", "需", "xū", "Waiting"),
    ("天水讼", "讼", "sòng", "Conflict"),
    ("地水师", "师", "shī", "The Army"),
    ("水地比", "比", "bǐ", "Holding Together"),
    ("风天小畜", "小畜", "xiǎo xù", "The Taming Power of the Small"),
    ("天泽履", "履", "lǚ", "Treading"),
    ("地天泰", "泰", "tài", "Peace"),
    ("天地否", "否", "pǐ", "Standstill"),
    ("天火同人", "同人", "tóng rén", "Fellowship with Others"),
    ("火天大有", "大有", "dà yǒu", "Possession in Great Measure"),
    ("地山谦", "谦", "qiān", "Modesty"),
    ("雷地豫", "豫", "yù", "Enthusiasm"),
    ("泽雷随", "随", "suí", "Following"),
    ("山风蛊", "蛊", "gǔ", "Work on What Has Been Spoiled"),
    ("地泽临", "临", "lín", "Approach"),
    ("风地观", "观", "guān", "Contemplation"),
    ("火雷噬嗑", "噬嗑", "shì kè", "Biting Through"),
    ("山火贲", "贲", "bì", "Grace"),
    ("山地剥", "剥", "bō", "Splitting Apart"),
    ("地雷复", "复", "fù", "Return"),
    ("天雷无妄", "无妄", "wú wàng", "Innocence"),
    ("山天大畜", "大畜", "dà xù", "The Taming Power of the Great"),
    ("山雷颐", "颐", "yí", "The Corners of the Mouth"),
    ("泽风大过", "大过", "dà guò", "Preponderance of the Great"),
    ("坎为水", "坎", "kǎn", "The Abysmal (Water)"),
    ("离为火", "离", "lí", "The Clinging (Fire)"),
    ("泽山咸", "咸", "xián", "Influence"),
    ("雷风恒", "恒", "héng", "Duration"),
    ("天山遁", "遁", "dùn", "Retreat"),
    ("雷天大壮", "大壮", "dà zhuàng", "The Power of the Great"),
    ("火地晋", "晋", "jìn", "Progress"),
    ("地火明夷", "明夷", "míng yí", "Darkening of the Light"),
    ("风火家人", "家人", "jiā rén", "The Family"),
    ("火泽睽", "睽", "kuí", "Opposition"),
    ("水山蹇", "蹇", "jiǎn", "Obstruction"),
    ("雷水解", "解", "xiè", "Deliverance"),
    ("山泽损", "损", "sǔn", "Decrease"),
    ("风雷益", "益", "yì", "Increase"),
    ("泽天夬", "夬", "guài", "Breakthrough"),
    ("天风姤", "姤", "gòu", "Coming to Meet"),
    ("泽地萃", "萃", "cuì", "Gathering Together"),
    ("地风升", "升", "shēng", "Pushing Upward"),
    ("泽水困", "困", "kùn", "Oppression"),
    ("水风井", "井", "jǐng", "The Well"),
    ("泽火革", "革", "gé", "Revolution"),
    ("火风鼎", "鼎", "dǐng", "The Cauldron"),
    ("震为雷", "震", "zhèn", "The Arousing (Thunder)"),
    ("艮为山", "艮", "gèn", "Keeping Still (Mountain)"),
    ("风山渐", "渐", "jiàn", "Development"),
    ("雷泽归妹", "归妹", "guī mèi", "The Marrying Maiden"),
    ("雷火丰", "丰", "fēng", "Abundance"),
    ("火山旅", "旅", "lǚ", "The Wanderer"),
    ("巽为风", "巽", "xùn", "The Gentle (Wind)"),
    ("兑为泽", "兑", "duì", "The Joyous (Lake)"),
    ("风水涣", "涣", "huàn", "Dispersion"),
    ("水泽节", "节", "jié", "Limitation"),
    ("风泽中孚", "中孚", "zhōng fú", "Inner Truth"),
    ("雷山小过", "小过", "xiǎo guò", "Preponderance of the Small"),
    ("水火既济", "既济", "jì jì", "After Completion"),
    ("火水未济", "未济", "wèi jì", "Before Completion"),
)

# The eight palaces (八宫): (palace trigram key, eight full names in generation order).
PALACES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("qian", ("乾为天", "天风姤", "天山遁", "天地否", "风地观", "山地剥", "火地晋", "火天大有")),
    ("kan", ("坎为水", "水泽节", "水雷屯", "水火既济", "泽火革", "雷火丰", "地火明夷", "地水师")),
    ("gen", ("艮为山", "山火贲", "山天大畜", "山泽损", "火泽睽", "天泽履", "风泽中孚", "风山渐")),
    ("zhen", ("震为雷", "雷地豫", "雷水解", "雷风恒", "地风升", "水风井", "泽风大过", "泽雷随")),
    ("xun", ("巽为风", "风天小畜", "风火家人", "风雷益", "天雷无妄", "火雷噬嗑", "山雷颐", "山风蛊")),
    ("li", ("离为火", "火山旅", "火风鼎", "火水未济", "山水蒙", "风水涣", "天水讼", "天火同人")),
    ("kun", ("坤为地", "地雷复", "地泽临", "地天泰", "雷天大壮", "泽天夬", "水天需", "水地比")),
    ("dui", ("兑为泽", "泽水困", "泽地萃", "泽山咸", "水山蹇", "地山谦", "雷山小过", "雷泽归妹")),
)


@dataclass(frozen=True)
class Hexagram:
    """A hexagram with its full structural identity (no classical text)."""

    number: int                 # King Wen sequence number 1-64
    name_zh: str                # short name, e.g. 屯
    full_name_zh: str           # trigram-encoded name, e.g. 水雷屯
    pinyin: str
    name_en: str
    lower: str                  # lower (inner) trigram key
    upper: str                  # upper (outer) trigram key
    lines: tuple[int, int, int, int, int, int]   # bottom-to-top, 1=yang 0=yin
    palace: str                 # palace trigram key
    palace_element: str         # 五行 of the palace
    generation: str             # 本宫 / 一世 … 游魂 / 归魂
    shi: int                    # 世 line position (1-6)
    ying: int                   # 应 line position (1-6)

    @property
    def symbol(self) -> str:
        """Unicode hexagram glyph (U+4DC0.. are ordered by the King Wen sequence)."""
        return chr(0x4DC0 + self.number - 1)


def _parse_trigrams(full_name_zh: str) -> tuple[str, str]:
    """Return ``(lower_key, upper_key)`` parsed from a hexagram's full name."""
    if "为" in full_name_zh:                       # pure hexagram, e.g. 乾为天
        key = TRIGRAM_BY_NAME[full_name_zh[0]]
        return key, key
    upper = TRIGRAM_BY_NATURE[full_name_zh[0]]     # first image = upper trigram
    lower = TRIGRAM_BY_NATURE[full_name_zh[1]]     # second image = lower trigram
    return lower, upper


def _ying_of(shi: int) -> int:
    """The 应 line sits three positions from the 世 line (1-indexed, wrapping)."""
    return ((shi - 1 + 3) % 6) + 1


def _build_hexagrams() -> tuple[Hexagram, ...]:
    """Assemble the 64 hexagrams from the King Wen and palace orderings."""
    palace_of: dict[str, tuple[str, int]] = {}
    for palace_key, names in PALACES:
        for generation_index, name in enumerate(names):
            palace_of[name] = (palace_key, generation_index)

    hexagrams: list[Hexagram] = []
    for index, (full_name, short_name, pinyin, name_en) in enumerate(KING_WEN_SEQUENCE):
        number = index + 1
        lower, upper = _parse_trigrams(full_name)
        lines = TRIGRAM_BY_KEY[lower].binary + TRIGRAM_BY_KEY[upper].binary
        palace_key, generation_index = palace_of[full_name]
        shi = SHI_BY_GENERATION[generation_index]
        hexagrams.append(
            Hexagram(
                number=number,
                name_zh=short_name,
                full_name_zh=full_name,
                pinyin=pinyin,
                name_en=name_en,
                lower=lower,
                upper=upper,
                lines=lines,
                palace=palace_key,
                palace_element=TRIGRAM_BY_KEY[palace_key].element,
                generation=GENERATION_NAMES[generation_index],
                shi=shi,
                ying=_ying_of(shi),
            )
        )
    return tuple(hexagrams)


HEXAGRAMS: tuple[Hexagram, ...] = _build_hexagrams()

HEXAGRAM_COUNT = 64
HEXAGRAM_BY_NUMBER: dict[int, Hexagram] = {h.number: h for h in HEXAGRAMS}
# Six-line pattern (bottom-to-top) -> hexagram, used to resolve a cast.
HEXAGRAM_BY_LINES: dict[tuple[int, ...], Hexagram] = {h.lines: h for h in HEXAGRAMS}
# (lower_key, upper_key) -> hexagram, used to resolve trigram-based derivations.
HEXAGRAM_BY_TRIGRAMS: dict[tuple[str, str], Hexagram] = {(h.lower, h.upper): h for h in HEXAGRAMS}


def hexagram_from_lines(lines: tuple[int, ...]) -> Hexagram:
    """Return the hexagram whose six lines (bottom-to-top) equal ``lines``."""
    return HEXAGRAM_BY_LINES[tuple(lines)]


def hexagram_from_trigrams(lower_binary: tuple[int, int, int], upper_binary: tuple[int, int, int]) -> Hexagram:
    """Return the hexagram built from a lower and upper trigram line pattern."""
    lower = TRIGRAM_BY_BINARY[lower_binary]
    upper = TRIGRAM_BY_BINARY[upper_binary]
    return HEXAGRAM_BY_TRIGRAMS[(lower, upper)]
