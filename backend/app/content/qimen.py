"""奇门遁甲 (Qi Men Dun Jia) reference tables — 时家奇门 · 转盘法 · 拆补起局.

Every value here is a fixed piece of the classical 奇门 apparatus, never generated at
runtime (PRD no-mock rule): the 洛书 nine palaces, the 九星 / 八门 / 八神 with their
五行·吉凶·类象, the 三奇六仪 and their 甲遁, the 阳遁/阴遁 局数表 keyed by 节气, the
三元符头 rule and the 旬空/驿马 tables.

School notes carried into the response provenance:
* 起局用**拆补法**（以日干支符头定上中下元），非置闰超神接气法。
* 排盘用**转盘法**（天盘/人盘整体旋转），非飞盘法。
* 中五宫无门无神，**天禽星与中宫地盘干寄坤二宫**（转盘通行寄法）。
* 八神用 值符·螣蛇·太阴·六合·白虎·玄武·九地·九天 八将（他派 白虎作勾陈、玄武作朱雀）。
"""

from dataclasses import dataclass

QIMEN_SOURCE = "《烟波钓叟歌》阳遁/阴遁起局歌诀 · 时家奇门转盘法通行安盘"

GAN = "甲乙丙丁戊己庚辛壬癸"
ZHI = "子丑寅卯辰巳午未申酉戌亥"

# --- 六十甲子 ---------------------------------------------------------------
JIAZI: tuple[str, ...] = tuple(GAN[i % 10] + ZHI[i % 12] for i in range(60))
JIAZI_INDEX: dict[str, int] = {gz: i for i, gz in enumerate(JIAZI)}

# --- 洛书九宫 (南上北下 的传统盘方位) ---------------------------------------
@dataclass(frozen=True)
class LuoShuPalace:
    """One 洛书 palace: its number, 卦, 方位, 五行, 地支 and 3×3 grid cell."""

    number: int
    gua: str
    direction: str
    element: str
    zhi: str
    row: int
    col: int


LUOSHU: dict[int, LuoShuPalace] = {
    4: LuoShuPalace(4, "巽", "东南", "木", "辰巳", 0, 0),
    9: LuoShuPalace(9, "离", "南", "火", "午", 0, 1),
    2: LuoShuPalace(2, "坤", "西南", "土", "未申", 0, 2),
    3: LuoShuPalace(3, "震", "东", "木", "卯", 1, 0),
    5: LuoShuPalace(5, "中", "中宫", "土", "", 1, 1),
    7: LuoShuPalace(7, "兑", "西", "金", "酉", 1, 2),
    8: LuoShuPalace(8, "艮", "东北", "土", "丑寅", 2, 0),
    1: LuoShuPalace(1, "坎", "北", "水", "子", 2, 1),
    6: LuoShuPalace(6, "乾", "西北", "金", "戌亥", 2, 2),
}

#: 洛书数序（阳遁顺行序）——地盘布干用九宫全序。
LUOSHU_SEQ9: tuple[int, ...] = (1, 2, 3, 4, 5, 6, 7, 8, 9)
#: 转盘旋转环：洛书数序跳过中五（星/门/神只在八方旋转）。
RING8: tuple[int, ...] = (1, 2, 3, 4, 6, 7, 8, 9)
RING8_POS: dict[int, int] = {n: i for i, n in enumerate(RING8)}


# --- 九星 -------------------------------------------------------------------
@dataclass(frozen=True)
class QimenStar:
    name: str
    element: str
    home: int  # 洛书 home palace
    luck: str  # 吉 | 凶 | 中平
    nature: str


NINE_STARS: tuple[QimenStar, ...] = (
    QimenStar("天蓬", "水", 1, "凶", "贪狼·暗昧盗贼"),
    QimenStar("天芮", "土", 2, "凶", "巨门·疾病瘟癀"),
    QimenStar("天冲", "木", 3, "吉", "禄存·雷厉武动"),
    QimenStar("天辅", "木", 4, "吉", "文曲·文教辅助"),
    QimenStar("天禽", "土", 5, "吉", "廉贞·中正仁和"),
    QimenStar("天心", "金", 6, "吉", "武曲·医药谋略"),
    QimenStar("天柱", "金", 7, "凶", "破军·毁折口舌"),
    QimenStar("天任", "土", 8, "吉", "左辅·诚信敦厚"),
    QimenStar("天英", "火", 9, "凶", "右弼·血光浮躁"),
)
STAR_BY_HOME: dict[int, QimenStar] = {s.home: s for s in NINE_STARS}
STAR_BY_NAME: dict[str, QimenStar] = {s.name: s for s in NINE_STARS}


# --- 八门 -------------------------------------------------------------------
@dataclass(frozen=True)
class QimenDoor:
    name: str
    element: str
    home: int
    luck: str  # 吉 | 凶 | 中平
    nature: str


EIGHT_DOORS: tuple[QimenDoor, ...] = (
    QimenDoor("休门", "水", 1, "吉", "休养生息·谒贵求财"),
    QimenDoor("死门", "土", 2, "凶", "死寂闭塞·吊丧田猎"),
    QimenDoor("伤门", "木", 3, "凶", "伤害竞争·捕猎索债"),
    QimenDoor("杜门", "木", 4, "中平", "杜藏闭塞·隐身躲避"),
    QimenDoor("开门", "金", 6, "吉", "开通发达·求财赴任"),
    QimenDoor("惊门", "金", 7, "凶", "惊恐忧疑·官讼口舌"),
    QimenDoor("生门", "土", 8, "吉", "生发兴隆·求财营造"),
    QimenDoor("景门", "火", 9, "中平", "光明文书·宴乐奏章"),
)
DOOR_BY_HOME: dict[int, QimenDoor] = {d.home: d for d in EIGHT_DOORS}


# --- 八神 -------------------------------------------------------------------
#: 阳遁顺布序；阴遁逆布（同一序列反向落宫）。
EIGHT_GODS: tuple[str, ...] = ("值符", "螣蛇", "太阴", "六合", "白虎", "玄武", "九地", "九天")
GOD_LUCK: dict[str, str] = {
    "值符": "吉", "螣蛇": "凶", "太阴": "吉", "六合": "吉",
    "白虎": "凶", "玄武": "凶", "九地": "吉", "九天": "吉",
}
GOD_NATURE: dict[str, str] = {
    "值符": "贵人首领·百恶不侵",
    "螣蛇": "虚惊怪异·缠绕不定",
    "太阴": "阴私暗助·隐秘谋划",
    "六合": "和合婚姻·交易中介",
    "白虎": "刚猛道路·凶伤血光",
    "玄武": "盗贼暧昧·欺瞒暗昧",
    "九地": "沉静厚载·守藏屯兵",
    "九天": "扬动高远·出行扩张",
}


# --- 三奇六仪 ---------------------------------------------------------------
#: 布地盘的固定次序：六仪（戊己庚辛壬癸）继以三奇（丁丙乙）。
DIPAN_SEQUENCE: tuple[str, ...] = ("戊", "己", "庚", "辛", "壬", "癸", "丁", "丙", "乙")
#: 六仪所遁旬首（甲遁于六仪，故盘上不见甲）。
YI_TO_XUNSHOU: dict[str, str] = {
    "戊": "甲子", "己": "甲戌", "庚": "甲申",
    "辛": "甲午", "壬": "甲辰", "癸": "甲寅",
}
#: 旬首 index（0,10,…,50）→ 所遁六仪。
XUNSHOU_INDEX_TO_YI: dict[int, str] = {0: "戊", 10: "己", 20: "庚", 30: "辛", 40: "壬", 50: "癸"}
THREE_QI: dict[str, str] = {"乙": "日奇", "丙": "月奇", "丁": "星奇"}
SIX_YI: frozenset[str] = frozenset("戊己庚辛壬癸")


def gan_kind(gan: str) -> str:
    """三奇 | 六仪 — the two families of the 遁甲 plate."""
    return "三奇" if gan in THREE_QI else "六仪"


# --- 局数表 (节气 → 上/中/下元 局数) ----------------------------------------
#: 阳遁歌诀：冬至惊蛰一七四，小寒二八五，大寒春分三九六，立春八五二，
#: 雨水九六三，清明立夏四一七，谷雨小满五二八，芒种六三九。
YANG_JU: dict[str, tuple[int, int, int]] = {
    "冬至": (1, 7, 4), "小寒": (2, 8, 5), "大寒": (3, 9, 6), "立春": (8, 5, 2),
    "雨水": (9, 6, 3), "惊蛰": (1, 7, 4), "春分": (3, 9, 6), "清明": (4, 1, 7),
    "谷雨": (5, 2, 8), "立夏": (4, 1, 7), "小满": (5, 2, 8), "芒种": (6, 3, 9),
}
#: 阴遁歌诀：夏至白露九三六，小暑八二五，大暑秋分七一四，立秋二五八，
#: 处暑一四七，立冬寒露六九三，霜降小雪五八二，大雪四七一。
YIN_JU: dict[str, tuple[int, int, int]] = {
    "夏至": (9, 3, 6), "小暑": (8, 2, 5), "大暑": (7, 1, 4), "立秋": (2, 5, 8),
    "处暑": (1, 4, 7), "白露": (9, 3, 6), "秋分": (7, 1, 4), "寒露": (6, 9, 3),
    "霜降": (5, 8, 2), "立冬": (6, 9, 3), "小雪": (5, 8, 2), "大雪": (4, 7, 1),
}


# --- 三元符头 (拆补法) ------------------------------------------------------
#: 符头（甲己日）地支 → 元：子午卯酉上元、寅申巳亥中元、辰戌丑未下元。
YUAN_BY_ZHI: dict[str, int] = {
    **{z: 0 for z in "子午卯酉"},
    **{z: 1 for z in "寅申巳亥"},
    **{z: 2 for z in "辰戌丑未"},
}
YUAN_NAMES: tuple[str, str, str] = ("上元", "中元", "下元")


# --- 旬空 · 驿马 ------------------------------------------------------------
#: 旬首 index → 该旬所空的两支。
XUNKONG_BY_XUNSHOU: dict[int, str] = {
    0: "戌亥", 10: "申酉", 20: "午未", 30: "辰巳", 40: "寅卯", 50: "子丑",
}
#: 时支 → 驿马（三合局冲处起马：申子辰马在寅、亥卯未马在巳、寅午戌马在申、巳酉丑马在亥）。
YIMA_BY_ZHI: dict[str, str] = {
    **{z: "寅" for z in "申子辰"},
    **{z: "巳" for z in "亥卯未"},
    **{z: "申" for z in "寅午戌"},
    **{z: "亥" for z in "巳酉丑"},
}
