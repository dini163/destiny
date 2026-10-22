"""紫微斗数 reference tables (策展静态数据，非运行时产物).

紫微斗数 builds on the 农历 birth data that ``lunar-python`` supplies; this module
holds the *star-placement* reference the engine walks: the fourteen 主星 with their
五行 / 阴阳 / 星系 and 星情 keyword, the 乙级 吉煞 stars, the 生年干 四化 table
(《紫微斗数全书》通行本), the 命主 / 身主 tables, the 纳音五行 → 五行局 map and the
十二宫 order. Nothing here is computed at request time; the engine only *reads* it.

School note: the 四化 table follows the most widely circulated 《全书》 version.
The 庚 / 壬 化科 have well-known school variants (e.g. 庚 天府/天相科, 壬 天府科);
this build fixes one table so charts stay reproducible, and says so in provenance.

主星吉凶倾向档（2026-10-22 综合结论 verdict 层新增，verdict-card spec §2b）：十四颗主星
各带一个定性档 `tendency`（吉 / 平 / 动 / 忌）与逐星 `tendency_source`。定性依据
《紫微斗数全书·诸星问答论》所载星情别名——帝座/官禄主/财帛主/福星/财库/田宅主/印星/
荫星归吉，囚星/暗星/将星(肃杀)/耗星归忌，善星机变(天机)归平，桃花欲望(贪狼)归动。
本表只给**定性档与古籍出处**，把档换算成分数的数字权重是模型参数（非古籍赋分），住
`engines/ziwei.py` 并以 `MODEL_PARAM_SOURCE` 署名，不在本表造数。
"""

from dataclasses import dataclass

# 紫微斗数安星诸表之总出处；四化从《全书》通行本，命身主/五行局/十二宫为斗数通例。
ZIWEI_SOURCE = "《紫微斗数全书》通行安星法 · 四化从全书派"

# --- 干支 constants ---------------------------------------------------------

GAN = "甲乙丙丁戊己庚辛壬癸"
ZHI = "子丑寅卯辰巳午未申酉戌亥"
ZHI_INDEX = {zhi: index for index, zhi in enumerate(ZHI)}
GAN_INDEX = {gan: index for index, gan in enumerate(GAN)}

# --- 十四主星 ---------------------------------------------------------------


@dataclass(frozen=True)
class MajorStar:
    """One of the fourteen 主星 with the attributes the chart displays."""

    key: str            # ascii key, e.g. ziwei
    name: str           # 星名, e.g. 紫微
    element: str        # 五行, e.g. 土
    yin_yang: str       # 阴 / 阳
    group: str          # 紫微系 / 天府系
    nature: str         # 星情 keyword (one factual phrase)
    tendency: str       # 吉凶倾向档：吉 / 平 / 动 / 忌（定性，出处见 tendency_source）
    tendency_source: str  # 该倾向的古籍出处（到《全书·诸星问答论》星条目，不现编）


#: 倾向档合法取值。吉=贵福财印荫一类正面星；平=中性安稳；动=中性活跃（吉凶随搭配）；
#: 忌=囚暗杀耗一类牵制星。档是定性标签，数字权重在引擎侧（模型参数），不在本表。
MAJOR_TENDENCIES: frozenset[str] = frozenset({"吉", "平", "动", "忌"})


MAJOR_STARS: dict[str, MajorStar] = {
    star.name: star
    for star in (
        MajorStar("ziwei", "紫微", "土", "阴", "紫微系", "帝座·尊贵领导", "吉",
                  "《紫微斗数全书·诸星问答论》以紫微为帝座、官禄主，尊星"),
        MajorStar("tianji", "天机", "木", "阴", "紫微系", "智慧·谋略机变", "平",
                  "《紫微斗数全书·诸星问答论》以天机为善星，主智慧机变，性多动少静，不属吉凶"),
        MajorStar("taiyang", "太阳", "火", "阳", "紫微系", "光明·博爱贵气", "吉",
                  "《紫微斗数全书·诸星问答论》以太阳为官禄主，主光明博爱贵气"),
        MajorStar("wuqu", "武曲", "金", "阴", "紫微系", "财帛·刚毅果决", "吉",
                  "《紫微斗数全书·诸星问答论》以武曲为财帛主，主财且刚毅果决"),
        MajorStar("tiantong", "天同", "水", "阳", "紫微系", "福禄·温和享受", "吉",
                  "《紫微斗数全书·诸星问答论》以天同为福星，主福禄温和享受"),
        MajorStar("lianzhen", "廉贞", "火", "阴", "紫微系", "次桃花·政令囚星", "忌",
                  "《紫微斗数全书·诸星问答论》以廉贞为囚星、次桃花，主感情与官非牵制"),
        MajorStar("tianfu", "天府", "土", "阳", "天府系", "财库·稳重保守", "吉",
                  "《紫微斗数全书·诸星问答论》以天府为财库、令星，主稳重保守能藏"),
        MajorStar("taiyin", "太阴", "水", "阴", "天府系", "田宅·富洁母性", "吉",
                  "《紫微斗数全书·诸星问答论》以太阴为田宅主，主富洁与母性"),
        MajorStar("tanlang", "贪狼", "木", "阳", "天府系", "桃花·欲望才艺", "动",
                  "《紫微斗数全书·诸星问答论》以贪狼为桃花星，主欲望才艺，吉凶随搭配"),
        MajorStar("jumen", "巨门", "水", "阴", "天府系", "口舌·是非研究", "忌",
                  "《紫微斗数全书·诸星问答论》以巨门为暗星，主口舌是非"),
        MajorStar("tianxiang", "天相", "水", "阳", "天府系", "印星·辅佐公正", "吉",
                  "《紫微斗数全书·诸星问答论》以天相为印星，主辅佐公正"),
        MajorStar("tianliang", "天梁", "土", "阳", "天府系", "荫星·长寿消解", "吉",
                  "《紫微斗数全书·诸星问答论》以天梁为荫星（寿星），主消灾解厄延寿"),
        MajorStar("qisha", "七杀", "金", "阴", "天府系", "将星·冲劲肃杀", "忌",
                  "《紫微斗数全书·诸星问答论》以七杀为将星，主冲劲肃杀孤克"),
        MajorStar("pojun", "破军", "水", "阴", "天府系", "耗星·破旧立新", "忌",
                  "《紫微斗数全书·诸星问答论》以破军为耗星，主破旧立新而动荡"),
    )
}

# 紫微系 six stars, laid 逆行 from 紫微 at these fixed offsets.
ZIWEI_SERIES: tuple[tuple[str, int], ...] = (
    ("紫微", 0),
    ("天机", -1),
    ("太阳", -3),
    ("武曲", -4),
    ("天同", -5),
    ("廉贞", -8),
)

# 天府系 eight stars, laid 顺行 from 天府 at these fixed offsets.
TIANFU_SERIES: tuple[tuple[str, int], ...] = (
    ("天府", 0),
    ("太阴", 1),
    ("贪狼", 2),
    ("巨门", 3),
    ("天相", 4),
    ("天梁", 5),
    ("七杀", 6),
    ("破军", 10),
)

# --- 乙级星 (吉 / 煞) -------------------------------------------------------


@dataclass(frozen=True)
class MinorStar:
    """An 乙级 star: its 五行 and whether it is auspicious (吉) or malefic (煞)."""

    name: str
    element: str
    kind: str  # 吉 / 煞 / 禄马


MINOR_STARS: dict[str, MinorStar] = {
    star.name: star
    for star in (
        MinorStar("左辅", "土", "吉"),
        MinorStar("右弼", "水", "吉"),
        MinorStar("文昌", "金", "吉"),
        MinorStar("文曲", "水", "吉"),
        MinorStar("天魁", "火", "吉"),
        MinorStar("天钺", "火", "吉"),
        MinorStar("禄存", "土", "禄马"),
        MinorStar("天马", "火", "禄马"),
        MinorStar("擎羊", "金", "煞"),
        MinorStar("陀罗", "金", "煞"),
        MinorStar("火星", "火", "煞"),
        MinorStar("铃星", "火", "煞"),
        MinorStar("地空", "火", "煞"),
        MinorStar("地劫", "火", "煞"),
    )
}

# --- 四化 (生年干 → 四化星) -------------------------------------------------

# 《紫微斗数全书》通行四化表；每干四字：化禄、化权、化科、化忌。
SIHUA: dict[str, tuple[str, str, str, str]] = {
    "甲": ("廉贞", "破军", "武曲", "太阳"),
    "乙": ("天机", "天梁", "紫微", "太阴"),
    "丙": ("天同", "天机", "文昌", "廉贞"),
    "丁": ("太阴", "天同", "天机", "巨门"),
    "戊": ("贪狼", "太阴", "右弼", "天机"),
    "己": ("武曲", "贪狼", "天梁", "文曲"),
    "庚": ("太阳", "武曲", "太阴", "天同"),
    "辛": ("巨门", "太阳", "文曲", "文昌"),
    "壬": ("天梁", "紫微", "左辅", "武曲"),
    "癸": ("破军", "巨门", "太阴", "贪狼"),
}

SIHUA_LABELS: tuple[str, str, str, str] = ("化禄", "化权", "化科", "化忌")

# --- 命主 / 身主 (by 生年支) ------------------------------------------------

MING_ZHU: dict[str, str] = {
    "子": "贪狼", "丑": "巨门", "寅": "禄存", "卯": "文曲", "辰": "廉贞", "巳": "武曲",
    "午": "破军", "未": "武曲", "申": "廉贞", "酉": "文曲", "戌": "禄存", "亥": "巨门",
}

SHEN_ZHU: dict[str, str] = {
    "子": "火星", "丑": "天相", "寅": "天梁", "卯": "天同", "辰": "文昌", "巳": "天机",
    "午": "火星", "未": "天相", "申": "天梁", "酉": "天同", "戌": "文昌", "亥": "天机",
}

# --- 五行局 (纳音五行 → 局数) -----------------------------------------------

# 纳音五行 → (局数, 局名). 局数即 大限 起运岁数。
WUXING_JU: dict[str, tuple[int, str]] = {
    "水": (2, "水二局"),
    "木": (3, "木三局"),
    "金": (4, "金四局"),
    "土": (5, "土五局"),
    "火": (6, "火六局"),
}

# --- 十二宫 -----------------------------------------------------------------

# 命宫起，逆布 (地支递减)。迁移恒为命宫对宫。
PALACE_NAMES: tuple[str, ...] = (
    "命宫", "兄弟", "夫妻", "子女", "财帛", "疾厄",
    "迁移", "仆役", "官禄", "田宅", "福德", "父母",
)

# 五虎遁：年干 → 寅宫天干 (正月建寅)。
YIN_GAN_BY_YEAR_GAN: dict[str, str] = {
    "甲": "丙", "己": "丙",
    "乙": "戊", "庚": "戊",
    "丙": "庚", "辛": "庚",
    "丁": "壬", "壬": "壬",
    "戊": "甲", "癸": "甲",
}

# 天乙贵人 (天魁 / 天钺) by 年干：甲戊庚牛羊、乙己鼠猴乡、丙丁猪鸡位、
# 壬癸兔蛇藏、六辛逢马虎。魁为阳贵、钺为阴贵。
TIANKUI_TIANYUE: dict[str, tuple[str, str]] = {
    "甲": ("丑", "未"), "戊": ("丑", "未"), "庚": ("丑", "未"),
    "乙": ("子", "申"), "己": ("子", "申"),
    "丙": ("亥", "酉"), "丁": ("亥", "酉"),
    "壬": ("卯", "巳"), "癸": ("卯", "巳"),
    "辛": ("午", "寅"),
}

# 禄存 by 年干 (临官禄位)。
LUCUN_BY_YEAR_GAN: dict[str, str] = {
    "甲": "寅", "乙": "卯", "丙": "巳", "丁": "午", "戊": "巳",
    "己": "午", "庚": "申", "辛": "酉", "壬": "亥", "癸": "子",
}

# 天马 by 年支三合局：申子辰马在寅、亥卯未马在巳、寅午戌马在申、巳酉丑马在亥。
TIANMA_BY_YEAR_ZHI: dict[str, str] = {
    "申": "寅", "子": "寅", "辰": "寅",
    "亥": "巳", "卯": "巳", "未": "巳",
    "寅": "申", "午": "申", "戌": "申",
    "巳": "亥", "酉": "亥", "丑": "亥",
}

# 火星起宫 by 年支三合局：寅午戌→丑、申子辰→寅、亥卯未→酉、巳酉丑→卯；顺行至生时。
HUOXING_BASE: dict[str, str] = {
    "寅": "丑", "午": "丑", "戌": "丑",
    "申": "寅", "子": "寅", "辰": "寅",
    "亥": "酉", "卯": "酉", "未": "酉",
    "巳": "卯", "酉": "卯", "丑": "卯",
}

# 铃星起宫 by 年支三合局：寅午戌→卯、余皆戌；顺行至生时。
LINGXING_BASE: dict[str, str] = {
    "寅": "卯", "午": "卯", "戌": "卯",
    "申": "戌", "子": "戌", "辰": "戌",
    "亥": "戌", "卯": "戌", "未": "戌",
    "巳": "戌", "酉": "戌", "丑": "戌",
}
