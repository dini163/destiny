"""吠陀占星 (Jyotish) reference content — signs, Navagraha, 27 Nakshatras and the
Vimshottari dasha spans.

These are the *fixed* taxonomies of the Vedic system; all astronomical positions
come from Swiss Ephemeris at runtime (see :mod:`app.engines.vedic`). Nothing here
is chart data — it is the standard reference frame every Jyotish chart is read
against, so it honours the no-mock rule (no reading or verdict is stored here).
"""

from dataclasses import dataclass

VEDIC_SOURCE = (
    "吠陀占星（Jyotish）通行体系 · 恒星黄道以 Lahiri（Chitrapaksha）岁差为基准，"
    "27 宿（Nakshatra）各占 13°20'、分四足（pada）；Vimshottari 大运依月宿起运，"
    "九曜（Navagraha）值年共 120 年：计都 7 · 金星 20 · 太阳 6 · 太阴 10 · 火星 7 · "
    "罗睺 18 · 木星 16 · 土星 19 · 水星 17。分宫用整宫制（一星座即一宫），以命度（Lagna）所在宿起第一宫。"
)

# --- Signs (Rashi) ----------------------------------------------------------
# The same twelve signs as the tropical zodiac, but measured against the fixed
# stars (sidereal). Sanskrit + Chinese names; the glyphs match the Western set.
SIGNS_EN = (
    "Mesha", "Vrishabha", "Mithuna", "Karka", "Simha", "Kanya",
    "Tula", "Vrischika", "Dhanu", "Makara", "Kumbha", "Meena",
)
SIGNS_ZH = (
    "白羊", "金牛", "双子", "巨蟹", "狮子", "处女",
    "天秤", "天蝎", "射手", "摩羯", "水瓶", "双鱼",
)
SIGN_GLYPHS = ("♈", "♉", "♊", "♋", "♌", "♍", "♎", "♏", "♐", "♑", "♒", "♓")

# --- Navagraha (nine grahas) ------------------------------------------------


@dataclass(frozen=True)
class Graha:
    """One of the nine Vedic luminaries/planetary nodes."""

    name: str       # English key (Sun..Saturn match the Western names; Rahu/Ketu are the nodes)
    glyph: str
    name_zh: str
    name_sa: str    # Sanskrit name


GRAHAS: tuple[Graha, ...] = (
    Graha("Sun", "☉", "太阳", "Surya"),
    Graha("Moon", "☽", "太阴", "Chandra"),
    Graha("Mars", "♂", "火星", "Mangala"),
    Graha("Mercury", "☿", "水星", "Budha"),
    Graha("Jupiter", "♃", "木星", "Guru"),
    Graha("Venus", "♀", "金星", "Shukra"),
    Graha("Saturn", "♄", "土星", "Shani"),
    Graha("Rahu", "☊", "罗睺", "Rahu"),
    Graha("Ketu", "☋", "计都", "Ketu"),
)

GRAHA_BY_NAME: dict[str, Graha] = {graha.name: graha for graha in GRAHAS}

# --- Vimshottari dasha ------------------------------------------------------
# The nine grahas in their fixed dasha order and their year-spans (sum = 120).
DASHA_ORDER: tuple[str, ...] = (
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
)
DASHA_SPANS: dict[str, int] = {
    "Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
    "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17,
}
VIMSHOTTARI_TOTAL = 120

# Span by dasha-order index, for the engine's arithmetic.
DASHA_SPANS_BY_ORDER: tuple[int, ...] = tuple(DASHA_SPANS[name] for name in DASHA_ORDER)

# --- Nakshatras (27 lunar mansions) ----------------------------------------

#: Each nakshatra spans 360°/27 = 13°20'.
NAKSHATRA_SPAN = 360.0 / 27.0


@dataclass(frozen=True)
class Nakshatra:
    """One of the 27 lunar mansions."""

    index: int
    name_en: str
    name_devanagari: str
    name_zh: str
    deity: str
    deity_zh: str
    lord: str              # Vimshottari lord, derived from the fixed order
    start_degree: float    # sidereal longitude where this nakshatra begins
    span_degrees: float


def _nak(index: int, name_en: str, devanagari: str, name_zh: str, deity: str, deity_zh: str) -> Nakshatra:
    """Build a Nakshatra; the Vimshottari lord is derived from the fixed cycle
    (Ashwini→Ketu, then Venus, Sun, Moon, Mars, Rahu, Jupiter, Saturn, Mercury,
    repeating), so the table can never drift from ``DASHA_ORDER``."""
    return Nakshatra(
        index=index,
        name_en=name_en,
        name_devanagari=devanagari,
        name_zh=name_zh,
        deity=deity,
        deity_zh=deity_zh,
        lord=DASHA_ORDER[index % 9],
        start_degree=round(index * NAKSHATRA_SPAN, 4),
        span_degrees=round(NAKSHATRA_SPAN, 4),
    )


NAKSHATRAS: tuple[Nakshatra, ...] = (
    _nak(0, "Ashwini", "अश्विनी", "阿湿毗尼", "Ashwini Kumaras", "双马童"),
    _nak(1, "Bharani", "भरणी", "婆罗尼", "Yama", "阎摩"),
    _nak(2, "Krittika", "कृत्तिका", "基栗底伽", "Agni", "阿耆尼"),
    _nak(3, "Rohini", "रोहिणी", "楼喜尼", "Brahma", "梵天"),
    _nak(4, "Mrigashira", "मृगशिरस्", "弥利迦奢罗", "Soma", "苏摩"),
    _nak(5, "Ardra", "आर्द्रा", "阿陀罗", "Rudra", "楼陀罗"),
    _nak(6, "Punarvasu", "पुनर्वसु", "布纳瓦苏", "Aditi", "阿底提"),
    _nak(7, "Pushya", "पुष्य", "布沙", "Brihaspati", "祭主仙"),
    _nak(8, "Ashlesha", "आश्लेषा", "阿湿利沙", "Nagas", "那伽"),
    _nak(9, "Magha", "मघा", "摩伽", "Pitris", "祖灵"),
    _nak(10, "Purva Phalguni", "पूर्वफल्गुनी", "前发座", "Bhaga", "婆伽"),
    _nak(11, "Uttara Phalguni", "उत्तरफल्गुनी", "后发座", "Aryaman", "阿利耶曼"),
    _nak(12, "Hasta", "हस्त", "哈斯塔", "Savitar", "萨维特里"),
    _nak(13, "Chitra", "चित्र", "质多罗", "Vishvakarma", "工巧神"),
    _nak(14, "Swati", "स्वाति", "室伐底", "Vayu", "伐由"),
    _nak(15, "Vishakha", "विशाखा", "毗舍佉", "Indragni", "因陀罗阿耆尼"),
    _nak(16, "Anuradha", "अनुराधा", "阿努罗陀", "Mitra", "密多罗"),
    _nak(17, "Jyeshtha", "ज्येष्ठा", "耆宿", "Indra", "因陀罗"),
    _nak(18, "Mula", "मूल", "牟拉", "Nirriti", "尼利提"),
    _nak(19, "Purva Ashadha", "पूर्वाषाढा", "前阿沙荼", "Apas", "水神"),
    _nak(20, "Uttara Ashadha", "उत्तराषाढा", "后阿沙荼", "Vishvedevas", "诸天"),
    _nak(21, "Shravana", "श्रवण", "室罗伐那", "Vishnu", "毗湿奴"),
    _nak(22, "Dhanishta", "धनिष्ठा", "陀尼沙", "Vasus", "八婆苏"),
    _nak(23, "Shatabhisha", "शतभिषक्", "百药", "Varuna", "伐楼那"),
    _nak(24, "Purva Bhadrapada", "पूर्वभाद्रपदा", "前婆罗钵提", "Aja Ekapada", "独足神"),
    _nak(25, "Uttara Bhadrapada", "उत्तरभाद्रपदा", "后婆罗钵提", "Ahir Budhnya", "深蛇神"),
    _nak(26, "Revati", "रेवती", "梨婆底", "Pushan", "布善"),
)


def nakshatra_of(longitude: float) -> Nakshatra:
    """The nakshatra containing a sidereal longitude (0-360)."""
    index = int((longitude % 360.0) // NAKSHATRA_SPAN)
    return NAKSHATRAS[index]


def pada_of(longitude: float) -> int:
    """The 1-based quarter (pada) of the nakshatra containing a sidereal longitude."""
    within = (longitude % 360.0) % NAKSHATRA_SPAN
    return int(within // (NAKSHATRA_SPAN / 4.0)) + 1
