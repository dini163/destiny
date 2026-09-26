"""卡巴拉生命之树 (Kabbalah Tree of Life) content — 10 原质 + 22 路径.

The Tree of Life is a fixed map of ten *Sephiroth* (原质, emanations) joined by
twenty-two *Paths* (路径). Every attribution here follows the Golden Dawn system
(the standard Western Hermetic arrangement): each Sephirah carries its pillar,
four-world (Atziluth→Assiah) station, planetary sphere, King-Scale colour,
archangel and divine name; each Path carries its Hebrew letter (with gematria
value), the matching Tarot trump and its planet / sign / element correspondence.

Nothing is generated at runtime (PRD no-mock rule). Tarot trumps use the Golden
Dawn numbering, where 力量 is VIII and 正义 is XI (not the Rider-Waite swap).
Coordinates ``x``/``y`` are normalised to 0-1 so the frontend can lay the tree
out at any size; ``y`` grows downward (Kether at the crown, Malkuth at the root).
"""

from dataclasses import dataclass

KABBALAH_SOURCE = (
    "Golden Dawn 卡巴拉生命之树通行对应体系 · 十原质（Sephiroth）四界三柱与 22 路径"
    "（希伯来字母 / 塔罗大阿卡纳 / 行星星座元素），塔罗序号从黄金黎明制（力量 VIII · 正义 XI）"
)


# --- Pillars & worlds -------------------------------------------------------

@dataclass(frozen=True)
class Pillar:
    """One of the three vertical columns of the Tree."""

    id: str           # mercy | severity | equilibrium
    name_zh: str
    name_en: str      # Jachin | Boaz | Middle
    side: str         # right | left | middle (as viewed)
    virtue: str       # one-line quality


PILLARS: dict[str, Pillar] = {
    p.id: p
    for p in (
        Pillar("mercy", "慈悲之柱", "Jachin", "right", "扩张、给予、主动的阳性之力。"),
        Pillar("severity", "严厉之柱", "Boaz", "left", "收敛、约束、赋形的阴性之力。"),
        Pillar("equilibrium", "中柱·平衡", "Middle", "middle", "调和两极、贯通天地的中道。"),
    )
}

#: 四界（Four Worlds）——从上到下，神圣之光逐层降落的四个层面。
WORLDS: dict[str, str] = {
    "atziluth": "原型界 · Atziluth",
    "bria": "创造界 · Briah",
    "yetzirah": "形成界 · Yetzirah",
    "assiah": "物质界 · Assiah",
}


# --- Sephiroth --------------------------------------------------------------

@dataclass(frozen=True)
class Sephirah:
    """One emanation (原质) on the Tree of Life."""

    number: int           # 1-10; 0 marks the hidden Daath
    id: str
    name_hebrew: str
    name: str             # English transliteration
    name_zh: str
    meaning: str
    keywords: tuple[str, ...]
    pillar: str           # mercy | severity | equilibrium
    world: str            # atziluth | bria | yetzirah | assiah
    sphere: str           # planetary / elemental sphere (zh)
    color: str            # King-Scale hex (adapted for a dark ground)
    archangel: str
    divine_name: str
    x: float              # 0-1 horizontal position
    y: float              # 0-1 vertical position (0 = crown, 1 = root)
    is_hidden: bool = False


def _seph(
    number: int,
    name_hebrew: str,
    name: str,
    name_zh: str,
    meaning: str,
    keywords: tuple[str, ...],
    pillar: str,
    world: str,
    sphere: str,
    color: str,
    archangel: str,
    divine_name: str,
    x: float,
    y: float,
    is_hidden: bool = False,
) -> Sephirah:
    return Sephirah(
        number=number,
        id=("daath" if is_hidden else f"sephirah-{number}"),
        name_hebrew=name_hebrew,
        name=name,
        name_zh=name_zh,
        meaning=meaning,
        keywords=keywords,
        pillar=pillar,
        world=world,
        sphere=sphere,
        color=color,
        archangel=archangel,
        divine_name=divine_name,
        x=x,
        y=y,
        is_hidden=is_hidden,
    )


SEPHIROTH: tuple[Sephirah, ...] = (
    _seph(1, "כתר", "Kether", "王冠",
          "万物未分之纯有，创造的第一点，超越一切名相的至高源头。",
          ("源头", "纯有", "合一", "无限光"),
          "equilibrium", "atziluth", "原始涌动 · Primum Mobile", "#F7F3E3",
          "梅塔特隆 Metatron", "אהיה Eheieh · 自有永有", 0.50, 0.04),
    _seph(2, "חכמה", "Chokmah", "智慧",
          "源头涌出的第一道动力，纯粹而未成形的智慧火花，主动、扩张、给予。",
          ("智慧", "动力", "阳", "扩张"),
          "mercy", "atziluth", "恒星天 · 黄道 Mazaloth", "#7FA8E0",
          "拉结尔 Raziel", "יה Yah · 上主", 0.84, 0.16),
    _seph(3, "בינה", "Binah", "理解",
          "承接智慧之力的容器与形式，被动、收敛、赋形，万物之母与理解之海。",
          ("理解", "形式", "阴", "收敛"),
          "severity", "atziluth", "土星 Saturn", "#5B3A6E",
          "萨法基尔 Tzaphkiel", "אלהים Elohim · 神", 0.16, 0.16),
    _seph(4, "חסד", "Chesed", "仁慈",
          "无条件扩张的慈爱与丰盛，建构、宽厚、秩序与权柄的恩泽面。",
          ("仁慈", "丰盛", "建构", "恩泽"),
          "mercy", "bria", "木星 Jupiter", "#4B5BD6",
          "萨德基尔 Tzadkiel", "אל El · 至高神", 0.84, 0.40),
    _seph(5, "גבורה", "Geburah", "严厉",
          "约束、裁断与破除的力量，以严厉矫正过剩，赋予边界与勇气。",
          ("严厉", "裁断", "破除", "勇气"),
          "severity", "bria", "火星 Mars", "#D6384A",
          "卡麦尔 Khamael", "אלהים גבור Elohim Gibor · 大能之神", 0.16, 0.40),
    _seph(6, "תפארת", "Tiphareth", "美",
          "慈悲与严厉调和之核心，自我、和谐与救赎的中心，人格的太阳。",
          ("美", "和谐", "自我", "救赎"),
          "equilibrium", "bria", "太阳 Sun", "#F0C23C",
          "拉斐尔 Raphael", "אלוה ודעת Eloah Va-Daath · 神与知识", 0.50, 0.52),
    _seph(7, "נצח", "Netzach", "胜利",
          "情感、艺术与本能之胜利，驱动欲望、美感与不屈的生命热情。",
          ("胜利", "情感", "艺术", "热情"),
          "mercy", "yetzirah", "金星 Venus", "#3FBF6F",
          "亚纳尔 Haniel", "יהוה צבאות YHWH Tzabaoth · 万军之上主", 0.84, 0.66),
    _seph(8, "הוד", "Hod", "荣耀",
          "理智、语言与逻辑之荣耀，赋予思想以名相、分析与沟通的秩序。",
          ("荣耀", "理智", "沟通", "分析"),
          "severity", "yetzirah", "水星 Mercury", "#E08A2E",
          "米迦勒 Michael", "אלהים צבאות Elohim Tzabaoth · 万军之神", 0.16, 0.66),
    _seph(9, "יסוד", "Yesod", "根基",
          "汇聚上方诸力之根基，潜意识、梦境与记忆的机制，通往物质的门户。",
          ("根基", "潜意识", "机制", "门户"),
          "equilibrium", "yetzirah", "月亮 Moon", "#9B5DD6",
          "加百列 Gabriel", "שדי אל חי Shaddai El Chai · 全能永活之神", 0.50, 0.80),
    _seph(10, "מלכות", "Malkuth", "王国",
          "生命之树落地之果，物质世界与肉身，神圣之光最终显化之处。",
          ("王国", "物质", "肉身", "显化"),
          "equilibrium", "assiah", "地球 · 四元素 Earth", "#8C5A3C",
          "圣德芬 Sandalphon", "אדני מלך Adonai Melekh · 上主为王", 0.50, 0.94),
)

#: Daath（知识）——深渊之上的隐藏原质，不计入十原质之数，故 `number=0`。
DAATH: Sephirah = _seph(
    0, "דעת", "Daath", "知识（隐藏）",
    "隐藏之知识，横跨深渊的虚位：超界与人格界之间不可见的合一，有其位而无其质。",
    ("知识", "深渊", "隐藏", "虚位"),
    "equilibrium", "bria", "无 · 深渊 Abyss", "#C9C3A0",
    "无固定", "无 · 隐名", 0.50, 0.28, is_hidden=True,
)

SEPHIROTH_BY_NUMBER: dict[int, Sephirah] = {s.number: s for s in SEPHIROTH}


def get_sephirah(number: int) -> Sephirah:
    """Return the Sephirah by its number (1-10). Raises ``KeyError`` if absent."""
    return SEPHIROTH_BY_NUMBER[number]


# --- Paths ------------------------------------------------------------------

@dataclass(frozen=True)
class Path:
    """One of the 22 paths joining two Sephiroth (a Hebrew letter + Tarot trump)."""

    number: int           # 11-32 (Golden Dawn path numbering)
    id: str
    from_sephirah: int    # source Sephirah number
    to_sephirah: int      # target Sephirah number
    letter: str           # Hebrew letter glyph
    letter_name: str      # transliteration, e.g. Aleph
    letter_zh: str        # 音译, e.g. 阿列夫
    letter_value: int     # gematria value of the letter
    tarot: str            # Tarot trump name (en)
    tarot_zh: str         # Tarot trump name (zh)
    tarot_numeral: str    # GD roman numeral, e.g. VIII
    correspondence: str   # planet / sign / element (zh)
    meaning: str


def _path(
    number: int,
    from_sephirah: int,
    to_sephirah: int,
    letter: str,
    letter_name: str,
    letter_zh: str,
    letter_value: int,
    tarot: str,
    tarot_zh: str,
    tarot_numeral: str,
    correspondence: str,
    meaning: str,
) -> Path:
    return Path(
        number=number,
        id=f"path-{number}",
        from_sephirah=from_sephirah,
        to_sephirah=to_sephirah,
        letter=letter,
        letter_name=letter_name,
        letter_zh=letter_zh,
        letter_value=letter_value,
        tarot=tarot,
        tarot_zh=tarot_zh,
        tarot_numeral=tarot_numeral,
        correspondence=correspondence,
        meaning=meaning,
    )


PATHS: tuple[Path, ...] = (
    _path(11, 1, 2, "א", "Aleph", "阿列夫", 1, "The Fool", "愚者", "0", "风元素 Air",
          "太初之息，愚者纵身跃入未知，纯真的起点与无限可能。"),
    _path(12, 1, 3, "ב", "Beth", "贝特", 2, "The Magician", "魔术师", "I", "水星 Mercury",
          "意志化为行动，魔术师沟通上下，将源头之力导入形式。"),
    _path(13, 1, 6, "ג", "Gimel", "吉梅尔", 3, "The High Priestess", "女祭司", "II", "月亮 Moon",
          "跨越深渊之箭，女祭司以直觉守护隐秘律法，直抵美之核心。"),
    _path(14, 2, 3, "ד", "Daleth", "达列特", 4, "The Empress", "皇后", "III", "金星 Venus",
          "智慧与理解结合而孕育，皇后掌丰饶、爱与创造之门。"),
    _path(15, 2, 6, "ה", "Heh", "黑", 5, "The Emperor", "皇帝", "IV", "白羊座 Aries",
          "原始动力获得权柄与秩序，皇帝以意志统御、开创格局。"),
    _path(16, 2, 4, "ו", "Vav", "瓦夫", 6, "The Hierophant", "教皇", "V", "金牛座 Taurus",
          "天启落地为传承，教皇执掌教义、誓约与既定的智慧体系。"),
    _path(17, 3, 6, "ז", "Zayin", "扎因", 7, "The Lovers", "恋人", "VI", "双子座 Gemini",
          "理解导向合一之抉择，恋人在对立之间作出爱与价值的选择。"),
    _path(18, 3, 5, "ח", "Cheth", "海特", 8, "The Chariot", "战车", "VII", "巨蟹座 Cancer",
          "形式驾驭相反之力前行，战车以坚定意志凯旋，护持内在柔软。"),
    _path(19, 4, 5, "ט", "Teth", "泰特", 9, "Strength", "力量", "VIII", "狮子座 Leo",
          "仁慈与严厉相接，力量以柔克刚、驯服内在的兽性。"),
    _path(20, 4, 6, "י", "Yod", "尤德", 10, "The Hermit", "隐者", "IX", "处女座 Virgo",
          "丰盛收敛为一盏心灯，隐者独照幽微，以谦卑服务指向真我。"),
    _path(21, 4, 7, "כ", "Kaph", "卡夫", 20, "Wheel of Fortune", "命运之轮", "X", "木星 Jupiter",
          "慈爱推动命运的循环，轮转升降不息，把握时机者顺势而上。"),
    _path(22, 5, 6, "ל", "Lamed", "拉梅德", 30, "Justice", "正义", "XI", "天秤座 Libra",
          "严厉归于平衡，正义以剑与秤裁量因果，令万物各得其分。"),
    _path(23, 5, 8, "מ", "Mem", "梅姆", 40, "The Hanged Man", "倒吊人", "XII", "水元素 Water",
          "破除之后是臣服，倒吊人悬于深水之上，以牺牲换取全新视角。"),
    _path(24, 6, 7, "נ", "Nun", "农", 50, "Death", "死神", "XIII", "天蝎座 Scorpio",
          "自我经历蜕变之死，旧形腐朽而新生萌动，是转化而非终结。"),
    _path(25, 6, 9, "ס", "Samekh", "萨梅克", 60, "Temperance", "节制", "XIV", "射手座 Sagittarius",
          "真我调和两极倾注而下，节制以耐心熔炼，将神性注入根基。"),
    _path(26, 6, 8, "ע", "Ayin", "阿因", 70, "The Devil", "恶魔", "XV", "摩羯座 Capricorn",
          "光明投向阴影，恶魔揭示束缚自我的执念与物质枷锁。"),
    _path(27, 7, 8, "פ", "Peh", "佩", 80, "The Tower", "高塔", "XVI", "火星 Mars",
          "情感与理智激烈对撞，高塔以雷霆击碎虚妄结构，破而后立。"),
    _path(28, 7, 9, "צ", "Tzaddi", "萨迪", 90, "The Star", "星星", "XVII", "水瓶座 Aquarius",
          "热情沉淀为希望的清流，星星倾注灵感，疗愈而指引长远。"),
    _path(29, 7, 10, "ק", "Qoph", "库夫", 100, "The Moon", "月亮", "XVIII", "双鱼座 Pisces",
          "欲望沉入潜意识之海，月亮照见幻象与恐惧，须循直觉穿越幽暗。"),
    _path(30, 8, 9, "ר", "Resh", "雷什", 200, "The Sun", "太阳", "XIX", "太阳 Sun",
          "理智与根基同沐光明，太阳带来清晰、喜悦与蓬勃的生机。"),
    _path(31, 8, 10, "ש", "Shin", "辛", 300, "Judgement", "审判", "XX", "火元素 Fire",
          "思想召唤最终的觉醒，审判号角响起，旧我死去而复活受召。"),
    _path(32, 9, 10, "ת", "Tav", "塔夫", 400, "The World", "世界", "XXI", "土星 Saturn",
          "根基圆满落入物质，世界完成一个周期，整合、成就与新的启程。"),
)

PATHS_BY_NUMBER: dict[int, Path] = {p.number: p for p in PATHS}

#: Hebrew letter gematria values keyed by the letter glyph (for the calculator).
LETTER_VALUE_BY_GLYPH: dict[str, int] = {p.letter: p.letter_value for p in PATHS}


def get_path(number: int) -> Path:
    """Return the Path by its Golden Dawn number (11-32). Raises ``KeyError`` if absent."""
    return PATHS_BY_NUMBER[number]


def paths_of(number: int) -> tuple[Path, ...]:
    """Every path touching a given Sephirah, in path-number order."""
    return tuple(p for p in PATHS if p.from_sephirah == number or p.to_sephirah == number)
