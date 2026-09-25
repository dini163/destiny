"""24 枚 Elder Futhark 卢恩符文，与可选的第 25 枚空白符 Wyrd（卢恩 spec §5.1）。

**字形凭据是 Unicode 官方字符名，不是肉眼**。每枚都存下 `codepoint` 与
`unicode_name` 两项，语料测断言 `unicodedata.name(chr(codepoint)) == unicode_name`
且 `glyph == chr(codepoint)`。这样字形对错不再靠人判：`unicodedata` 随解释器一起分发，
是一份离线、权威、可被单测直接调用的源（spec §2.1）。

设计稿在这一页印错了四个字形，本模块一个都不许收（spec §2.3）：

=========== ========= ===================================== ==================
设计稿印的   码位      Unicode 官方名                        正解
=========== ========= ===================================== ==================
ᚫ           U+16AB    RUNIC LETTER AESC（盎格鲁-撒克逊）    ᚨ U+16A8 ANSUZ A
ᛋ           U+16CB    RUNIC LETTER SIGEL LONG-BRANCH-SOL S  ᛊ U+16CA SOWILO S
                      （新 Futhark 长枝体，晚约四百年）
ᛝ           U+16DD    RUNIC LETTER ING（盎格鲁-撒克逊）      ᛜ U+16DC INGWAZ
᛭           U+16ED    RUNIC CROSS PUNCTUATION（标点）        Wyrd 是空白石，不印字符
=========== ========= ===================================== ==================

外加 Dagaz ᛞ U+16DE 在设计稿里整个不见了 —— 它那个「二十四系全典」抽屉只有 23 枚
真字母，因为 Wyrd 占了本该属于 Dagaz 的那格。故 `FUTHARK` 恰好 24 枚，Dagaz 在序位 23。

**逆位判据是几何的**：卢恩传统里逆位叫 merkstave（「暗枝」），指石碑掷出时上下颠倒。
于是「有没有逆位」等于「字形旋转 180° 后与原来重不重合」。重合者无从分辨颠倒与否，
也就没有逆位读法 —— 这样的有八枚（Gebo/Hagalaz/Isa/Jera/Eihwaz/Sowilo/Ingwaz/Dagaz），
本模块给它们 `reversible=False`、`reversed_meaning=None`，**绝不编一句逆位释义来凑满**。
判据写在 `REVERSIBLE_NOTE` 里并印到页面上，读者可以自己转一转字形核对。

一个易错处：**Eihwaz ᛇ（紫杉）对称、Ehwaz ᛖ（骏马）不对称** —— 两个名字差一个字母，
几何性质相反，中文音译也刻意拉开（艾赫瓦兹 / 埃瓦兹）以免跟着填反。

`name_meaning` 是符文名的**原始日耳曼语构拟词义**（spec 决策 8），不是占卜释义。
诚实补记：Elder Futhark 本身没有存世的符文诗，这些名字是学术重构（记作 *fehu 一类），
出处里写明「构拟」二字，不冒充原文。Perthro 的词源学界至今无定论，如实记「词源不详」。
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

# --- 出处 -------------------------------------------------------------------

#: 书级出处。拆成「名 + 限定语」两半，理由同 `numerology_cycles.CYCLES_SOURCE_NAME`：
#: 前端 `SourceNote` 对非古籍出处只印第一个「（」之前的半句，条目名缀在末尾会被切掉，
#: 于是同一张卡上两条不同的引用长得一模一样（数字命理走查查出的缺陷）。
RUNES_SOURCE_NAME = "北欧 Elder Futhark 卢恩符文序、字形与释义"
RUNES_SOURCE_QUALIFIER = (
    "序位据 Kylver 石碑，字形据 Unicode 标准字符名，"
    "符文名词义为原始日耳曼语构拟，释义为通行传统的摘要，非古籍、非逐字引文；"
    "第 25 枚空白符 Wyrd 为现代增补，不在此二凭据之列，另署出处"
)

#: 整串出处，逐字等于拆分前那一串：语料测与响应里的 `provenance.tables` 都按整串核。
RUNES_SOURCE = f"{RUNES_SOURCE_NAME}（{RUNES_SOURCE_QUALIFIER}）"


def runes_source(entry: str) -> str:
    """带条目名的出处，如 `…字形与释义·Fehu（序位据 Kylver 石碑…）`。

    条目名拼在限定语**之前**，这样截断后仍自证身份。
    """
    return f"{RUNES_SOURCE_NAME}·{entry}（{RUNES_SOURCE_QUALIFIER}）"


#: 空白符的出处**不能**共用上面那 24 枚的限定语：「序位据 Kylver 石碑、字形据 Unicode
#: 标准字符名」这两句对它都是假的 —— Kylver 石碑上没有第 25 格，空白符也没有字形可查。
#: 共用等于让一枚 1980 年代的商业增补借古石碑与 Unicode 的凭据，正是前端
#: `SourceNote` 那条注释要拦的事（它写的就是「模型算出来的数不得借书的权威」）。
#: 名也另起：`RUNES_SOURCE_NAME` 里的「Elder Futhark」同样不包含它。
WYRD_SOURCE_NAME = "北欧卢恩现代增补·空白符 Wyrd"
WYRD_SOURCE_QUALIFIER = (
    "现代增补，不见于 Kylver 石碑、埃达或任何古铭文；无字形，故不据 Unicode 字符名；"
    "名义取自现代商业符文牌组的通行说法，非古籍、非逐字引文"
)

#: 整串，逐字等于拆分前那一串。无「（」之前的部分就是前端角标会印的那一句。
WYRD_SOURCE = f"{WYRD_SOURCE_NAME}（{WYRD_SOURCE_QUALIFIER}）"


# --- 三组（ættir） ----------------------------------------------------------

AETT_FREYJA = "freyja"
AETT_HEIMDALL = "heimdall"
AETT_TYR = "tyr"

#: 分组本身有早期实物依据（Vadstena 铜片、Kylver 序列），但把它们叫 ætt 是近代用法，
#: 且三组的名字各家不一（spec §2.4）。故一并下发 `AETT_NAMING_NOTE`，不假装只有一种叫法。
AETT_NAMES: dict[str, str] = {
    AETT_FREYJA: "Freyja's Aett",
    AETT_HEIMDALL: "Heimdall's Aett",
    AETT_TYR: "Tyr's Aett",
}

AETT_NAMES_ZH: dict[str, str] = {
    AETT_FREYJA: "弗蕾亚之族",
    AETT_HEIMDALL: "海姆达尔之族",
    AETT_TYR: "提尔之族",
}

AETT_NAMING_NOTE = (
    "三组各八枚的分组有早期实物依据，但「ætt」这个称呼是近代才有的，"
    "且命名各家不一：第一组亦作 Freyr's Aett，第二组亦作 Hagal's Aett。"
    "本页取现代最通行的一版，不代表只有一种叫法。"
)

#: 第三组的中文说明沿用设计稿的措辞（分组主题是现代解读，非古文献）。
AETT_THEMES_ZH: dict[str, str] = {
    AETT_FREYJA: "物质与生命基石",
    AETT_HEIMDALL: "磨砺、秩序与觉醒",
    AETT_TYR: "超越、律法与宿命",
}

# --- 逆位判据（印到页面上的那一句） ----------------------------------------

REVERSIBLE_NOTE = (
    "卢恩的逆位叫 merkstave（暗枝），指石碑掷出时上下颠倒。故「有没有逆位」是个几何问题："
    "把字形转 180° 后与原形重合的，颠倒与否根本无从分辨，也就没有逆位读法。"
    "24 枚里有八枚如此（Gebo、Hagalaz、Isa、Jera、Eihwaz、Sowilo、Ingwaz、Dagaz），"
    "本页对它们不印逆位徽标、也不编逆位释义。你可以自己把这些字形转半圈核对。"
)

#: Wyrd 的现代性声明（spec §2.6、决策 3）。空白符不见于任何古铭文、Edda 或符文诗，
#: 是 1980 年代随商业符文牌组出现的现代增补。PRD 要求这个开关，故做；但当古符文卖就是假话。
WYRD_NOTE = (
    "空白符（Wyrd）是现代增补，不是古传统：它不见于任何古铭文、埃达或符文诗，"
    "是 1980 年代随商业符文牌组出现的第 25 枚（Ralph Blum《The Book of Runes》1982 一类）。"
    "名字取自古英语 wyrd「命运」，与古诺斯语 urðr（诺伦三女神之一）同源。"
    "故本页默认关闭它，并且不把它算进三组任何一组 —— 它不是 Elder Futhark 的字母。"
)


# --- 数据模型 ---------------------------------------------------------------


@dataclass(frozen=True)
class Rune:
    """一枚卢恩符文。`order` 25 与 `is_wyrd` 只属于空白符。"""

    order: int
    key: str
    glyph: str
    codepoint: int | None
    unicode_name: str | None
    name: str
    name_zh: str
    transliteration: str
    phoneme: str
    name_meaning: str
    name_meaning_uncertain: bool
    aett: str | None
    aett_zh: str | None
    reversible: bool
    upright_keywords: tuple[str, ...]
    reversed_keywords: tuple[str, ...] | None
    upright_meaning: str
    reversed_meaning: str | None
    is_wyrd: bool
    source: str

    def meaning_for(self, orientation: str) -> str:
        """按朝向取释义。

        不可逆的符文被问 `reversed` 是**程序错误**，故直接抛而不是静默回退到正位：
        回退会把引擎的定向 bug 藏起来，读者看到的将是一句与卡上徽标不符的话。
        """
        if orientation == "reversed":
            if self.reversed_meaning is None:
                raise ValueError(f"{self.name} 字形对称无逆位，不该被问 reversed")
            return self.reversed_meaning
        return self.upright_meaning

    def keywords_for(self, orientation: str) -> tuple[str, ...]:
        """按朝向取关键词。同 `meaning_for`：不可能的组合直接抛，不静默回退。"""
        if orientation == "reversed":
            if self.reversed_keywords is None:
                raise ValueError(f"{self.name} 字形对称无逆位，不该被问 reversed")
            return self.reversed_keywords
        return self.upright_keywords


def _rune(
    order: int,
    glyph: str,
    codepoint: int,
    unicode_name: str,
    name: str,
    name_zh: str,
    transliteration: str,
    phoneme: str,
    name_meaning: str,
    aett: str,
    upright_keywords: Sequence[str],
    reversed_keywords: Sequence[str] | None,
    upright_meaning: str,
    reversed_meaning: str | None,
    *,
    uncertain: bool = False,
) -> Rune:
    """由一行行读得下去的位置参数拼出一枚符文。

    `reversible` 不在参数里 —— 它由 `reversed_meaning is not None` 推出。少一个可以填错的
    旋钮：想标成可逆就必须真写出逆位释义，想标成对称就必须留 `None`，两者不可能对不上。
    """
    return Rune(
        order=order,
        key=name.lower(),
        glyph=glyph,
        codepoint=codepoint,
        unicode_name=unicode_name,
        name=name,
        name_zh=name_zh,
        transliteration=transliteration,
        phoneme=phoneme,
        name_meaning=name_meaning,
        name_meaning_uncertain=uncertain,
        aett=aett,
        aett_zh=AETT_NAMES_ZH[aett],
        reversible=reversed_meaning is not None,
        upright_keywords=tuple(upright_keywords),
        reversed_keywords=None if reversed_keywords is None else tuple(reversed_keywords),
        upright_meaning=upright_meaning,
        reversed_meaning=reversed_meaning,
        is_wyrd=False,
        source=runes_source(name),
    )


# --- 24 枚 Elder Futhark（Kylver 序，前六枚连读即 fuþark） ------------------

FUTHARK: tuple[Rune, ...] = (
    _rune(
        1, "ᚠ", 0x16A0, "RUNIC LETTER FEHU FEOH FE F",
        "Fehu", "费胡", "f", "清唇齿擦音，如英语 fee",
        "原始日耳曼语 *fehu「牲畜、动产」—— 财富以能自己走路的牲口计",
        AETT_FREYJA,
        ("财富", "动产", "生计", "起始资源", "流通"),
        ("守财", "损耗", "资金断裂", "贪吝"),
        "可动之财与原始动力：钱、物、精力与手上已有的资源。宜启动、宜投入流通，财在动中聚。",
        "财的暗面：守而不流通则滞，投入无度则耗。或指钱物上的损失、纠纷与吝啬自困。",
    ),
    _rune(
        2, "ᚢ", 0x16A2, "RUNIC LETTER URUZ UR U",
        "Uruz", "乌鲁兹", "u", "短促的后圆唇元音，如 book 里的 oo",
        "原始日耳曼语 *ūruz「原牛」—— 已绝迹的欧洲野牛，力与野性的原型",
        AETT_FREYJA,
        ("原力", "体魄", "野性", "成形之初", "耐力"),
        ("力弱", "错失时机", "蛮力失控", "体虚"),
        "未经驯化的原始力量：体魄、意志与事情的初生之势。宜趁力起手，也须给野性一个去处。",
        "力气不济或用错了地方：时机过去、身体透支，或空有蛮力而无方向。",
    ),
    _rune(
        3, "ᚦ", 0x16A6, "RUNIC LETTER THURISAZ THURS THORN",
        "Thurisaz", "图里萨兹", "þ", "清齿擦音，如英语 thin 的 th",
        "原始日耳曼语 *þurisaz「巨人、破坏者」—— 亦与「刺、荆棘」同源",
        AETT_FREYJA,
        ("阻力", "破坏力", "边界", "防卫", "必要的冲突"),
        ("受困于阻", "逞强", "危险的鲁莽", "旧伤未愈"),
        "撞上硬物的一击：阻力、冲突与破坏，同时也是把边界立起来的力。宜先认清挡路的是什么。",
        "阻力占了上风，或以暴制暴反伤自身。也指不肯面对的旧患在此时发作。",
    ),
    _rune(
        4, "ᚨ", 0x16A8, "RUNIC LETTER ANSUZ A",
        "Ansuz", "安苏兹", "a", "开元音，如英语 father",
        "原始日耳曼语 *ansuz「阿萨神族之一员」—— 神，尤其指 Odin",
        AETT_FREYJA,
        ("讯息", "言说", "名分", "师长", "约定"),
        ("误会", "失言", "欺瞒", "讯息受阻"),
        "话与讯息的通道：口舌、文书、教诲与名分。宜听清、说准、把约定写下来。",
        "话没传到、传错或本身不实：误会、诡辩、名不副实，或被花言巧语带偏。",
    ),
    _rune(
        5, "ᚱ", 0x16B1, "RUNIC LETTER RAIDO RAD REID R",
        "Raido", "莱多", "r", "颤音或近音 r",
        "原始日耳曼语 *raidō「骑行、旅程」—— 有节奏的前行，也指车辙与秩序",
        AETT_FREYJA,
        ("行进", "旅程", "节奏", "秩序", "正道"),
        ("行程受阻", "脱序", "原地打转", "方向错误"),
        "上了路就有节奏：行程、推进与按部就班的秩序。宜动不宜守，也宜守住该有的次序。",
        "车轮偏了：行程被打断、步骤乱了，或走得很快却不是往要去的地方。",
    ),
    _rune(
        6, "ᚲ", 0x16B2, "RUNIC LETTER KAUNA",
        "Kenaz", "肯纳兹", "k", "清软颚塞音，如英语 king",
        "原始日耳曼语 *kaunan「火炬」—— 古诺斯语 kaun 另解作「疮、溃口」",
        AETT_FREYJA,
        ("照亮", "技艺", "灵感", "转化", "可控之火"),
        ("灵感枯竭", "技艺生疏", "看不清", "火熄了"),
        "手里的一支火把：技艺、灵感与看清楚局部的能力。宜动手做、把想法烧成形状。",
        "光灭了或照错了地方：思路阻塞、手艺生疏，或在关键处看不明白。",
    ),
    _rune(
        7, "ᚷ", 0x16B7, "RUNIC LETTER GEBO GYFU G",
        "Gebo", "盖博", "g", "浊软颚塞音，如英语 good",
        "原始日耳曼语 *gebō「赠礼」—— 礼尚往来所系的盟约",
        AETT_FREYJA,
        ("赠予", "交换", "盟约", "平衡", "伴侣"),
        None,
        "一来一往才成立的关系：赠礼、结盟与对等的交换。宜给出也宜受，欠与亏都会毁约。",
        None,  # X 形，转半圈还是 X：无从颠倒，故无逆位
    ),
    _rune(
        8, "ᚹ", 0x16B9, "RUNIC LETTER WUNJO WYNN W",
        "Wunjo", "温乔", "w", "半元音 w，如英语 win",
        "原始日耳曼语 *wunjō「喜悦」",
        AETT_FREYJA,
        ("喜悦", "归属", "和谐", "如愿", "同盟之乐"),
        ("失和", "乐极生悲", "疏离", "期待落空"),
        "事情顺了之后的那份乐：归属、和谐与如愿。宜享受成果，也宜与人同乐。",
        "乐子散了或本来就有裂缝：关系失和、期待落空，或热闹底下的孤单。",
    ),
    _rune(
        9, "ᚺ", 0x16BA, "RUNIC LETTER HAGLAZ H",
        "Hagalaz", "哈加拉兹", "h", "清喉擦音，如英语 home",
        "原始日耳曼语 *haglaz「冰雹」—— 从天而降、不由人定",
        AETT_HEIMDALL,
        ("天灾", "突变", "不由人", "破而后立", "考验"),
        None,
        "从天上掉下来的、不由人定的那一场：突变、挫折与被打断的计划。宜认下损失，从中重整。",
        None,  # 两竖一斜，转半圈斜线自重合：无从颠倒，故无逆位
    ),
    _rune(
        10, "ᚾ", 0x16BE, "RUNIC LETTER NAUDIZ NYD NAUD N",
        "Nauthiz", "瑙提兹", "n", "鼻音 n，如英语 no",
        "原始日耳曼语 *naudiz「必需、匮乏」—— 逼着人动手的那种需要",
        AETT_HEIMDALL,
        ("必需", "约束", "忍耐", "自食其力", "补课"),
        ("被匮乏困死", "抗拒必要的苦", "自找的穷", "拖延"),
        "缺什么就被什么管着：必需、约束与不得不补的课。宜认下限制，把该做的苦工做完。",
        "被匮乏压住而动不了，或明明该补课却一味抗拒 —— 约束变成了自困。",
    ),
    _rune(
        11, "ᛁ", 0x16C1, "RUNIC LETTER ISAZ IS ISS I",
        "Isa", "伊萨", "i", "闭前元音，如英语 see",
        "原始日耳曼语 *īsaz「冰」",
        AETT_HEIMDALL,
        ("停滞", "封冻", "静止", "守成", "自我"),
        None,
        "结了冰的水面：停滞、冻结与不得不动的静止。宜等、宜守，硬闯只会破冰落水。",
        None,  # 单竖，转半圈还是那一竖：无从颠倒，故无逆位
    ),
    _rune(
        12, "ᛃ", 0x16C3, "RUNIC LETTER JERAN J",
        "Jera", "杰拉", "j", "半元音 y，如英语 year",
        "原始日耳曼语 *jērą「年、收成」—— 一年一熟，急不来",
        AETT_HEIMDALL,
        ("收成", "周期", "回报", "一年一熟", "因果"),
        None,
        "一年一轮的收成：先前种下的到此结果，好坏都是自己那份。宜按周期办事，不求速成。",
        None,  # 两枚反向的钩互相对称，转半圈重合：无从颠倒，故无逆位
    ),
    _rune(
        13, "ᛇ", 0x16C7, "RUNIC LETTER IWAZ EOH",
        "Eihwaz", "艾赫瓦兹", "ï", "介于 i 与 e 之间的长音（构拟）",
        "原始日耳曼语 *īhwaz「紫杉」—— 常青、长寿，也是制弓之材",
        AETT_HEIMDALL,
        ("长寿", "韧性", "转变", "生死之间", "弓材"),
        None,
        "常青的紫杉，也是制弓之材：耐力、跨越与转化。宜撑住这一段，弯而不折。",
        None,  # 一竖两端各一向外的钩，上下相反故转半圈重合：无逆位。别与 Ehwaz 混
    ),
    _rune(
        14, "ᛈ", 0x16C8, "RUNIC LETTER PERTHO PEORTH P",
        "Perthro", "佩尔索", "p", "清双唇塞音，如英语 pen",
        "词源不详（构拟 *perþō 一说为「签筒、骰盅」，无定论）",
        AETT_HEIMDALL,
        ("未知", "机运", "签筒", "秘密", "一掷"),
        ("坏签", "隐情败露", "误赌", "不肯认命"),
        "签筒里摇出来的是什么，掷之前谁也不知道：机运、隐秘与尚未揭晓的一段。"
        "宜留一手，也宜认命数。",
        "摇出来的不是想要的那一支：意外走漏、赌错了，或被自己不肯认的那部分反噬。",
        uncertain=True,
    ),
    _rune(
        15, "ᛉ", 0x16C9, "RUNIC LETTER ALGIZ EOLHX",
        "Algiz", "阿尔吉兹", "z", "浊齿擦音（后世演化为 r 音）",
        "原始日耳曼语 *algiz「驼鹿」—— 一说与「保护」同源，另解作「莎草」",
        AETT_HEIMDALL,
        ("护持", "警戒", "求援", "庇荫", "界限"),
        ("失去庇荫", "警戒失效", "被利用", "孤立"),
        "张开的手与警界的角：保护、警戒与可以求援的通道。宜守住界限，也宜及早呼救。",
        "护持不在了或没起作用：孤立无援、警戒失灵，或被人拿善意当缺口。",
    ),
    _rune(
        16, "ᛊ", 0x16CA, "RUNIC LETTER SOWILO S",
        "Sowilo", "索维洛", "s", "清齿擦音，如英语 sun",
        "原始日耳曼语 *sōwilō「太阳」",
        AETT_HEIMDALL,
        ("光明", "全胜", "生命力", "澄明", "目标达成"),
        None,
        "太阳当空：力气、澄明与看得见的成功。宜趁势推进，把该照亮的都照亮。",
        None,  # S 形折线转半圈仍是 S：无从颠倒，故无逆位
    ),
    _rune(
        17, "ᛏ", 0x16CF, "RUNIC LETTER TIWAZ TIR TYR T",
        "Tiwaz", "提瓦兹", "t", "清齿龈塞音，如英语 time",
        "原始日耳曼语 *tīwaz「战神提尔」—— 与拉丁语 deus、希腊语 Zeus 同源于 *dyeus",
        AETT_TYR,
        ("公断", "荣誉", "决断", "牺牲", "法治"),
        ("失义", "决断失误", "争讼不利", "白费的牺牲"),
        "提尔断腕立约的那把矛：公义、荣誉与必要的牺牲。宜依理裁断、认下代价，不徇私。",
        "理不直或断错了：争讼不利、誓言失效，或付出了却没换来该换来的。",
    ),
    _rune(
        18, "ᛒ", 0x16D2, "RUNIC LETTER BERKANAN BEORC BJARKAN B",
        "Berkana", "贝尔卡纳", "b", "浊双唇塞音，如英语 bed",
        "原始日耳曼语 *berkanō「桦树」—— 新生与哺育之木",
        AETT_TYR,
        ("新生", "孕育", "哺育", "成长", "家事"),
        ("生长受阻", "家事不宁", "不孕", "过度保护"),
        "桦树的新芽与哺乳的母亲：孕育、生长与家中事。宜养、宜护，让新起的慢慢长成。",
        "长不动或护过了头：新生受阻、家宅不宁，或以照顾之名把人捆住。",
    ),
    _rune(
        19, "ᛖ", 0x16D6, "RUNIC LETTER EHWAZ EH E",
        "Ehwaz", "埃瓦兹", "e", "半开元音，如英语 bed",
        "原始日耳曼语 *ehwaz「马」—— 与拉丁语 equus 同源",
        AETT_TYR,
        ("同行", "坐骑", "信义", "迁移", "协力"),
        ("失和的伙伴", "受阻的移动", "背信", "各行其是"),
        "马与骑手那种相托：伙伴关系、协力与快速移动。宜借力同行，也宜守住彼此的信。",
        "骑手与马不是一条心：伙伴失和、迁移受阻，或说好的没做到。",
        # 与 Eihwaz 只差一个字母，但那枚对称、这枚不对称（M 形转半圈成 W）：故这枚可逆
    ),
    _rune(
        20, "ᛗ", 0x16D7, "RUNIC LETTER MANNAZ MAN M",
        "Mannaz", "曼纳兹", "m", "鼻音 m，如英语 man",
        "原始日耳曼语 *mannaz「人、人类」",
        AETT_TYR,
        ("自我", "他人", "社群", "本分", "相待"),
        ("孤立", "自欺", "与人失和", "推诿"),
        "人与人相对而立：自己、他人与所处的社群。宜先认清自己那一份，再谈与人怎么处。",
        "与人断了线或与自己打了架：孤立、自欺、把责任推给别人。",
    ),
    _rune(
        21, "ᛚ", 0x16DA, "RUNIC LETTER LAUKAZ LAGU LOGR L",
        "Laguz", "拉古兹", "l", "边音 l，如英语 lake",
        "原始日耳曼语 *laguz「水、湖」",
        AETT_TYR,
        ("水", "直觉", "顺势", "深流", "梦"),
        ("直觉失灵", "被情绪卷走", "逆流", "自欺的想象"),
        "水自己知道往低处走：直觉、潜意识与顺势而行。宜跟着感觉探路，也宜提防暗流。",
        "水成了漩涡：判断被情绪带跑、直觉失灵，或沉在想象里不肯上岸。",
    ),
    _rune(
        22, "ᛜ", 0x16DC, "RUNIC LETTER INGWAZ",
        "Ingwaz", "英瓦兹", "ŋ", "软颚鼻音，如英语 sing 的尾音",
        "原始日耳曼语 *ingwaz「丰饶之神 Ing」",
        AETT_TYR,
        ("内孕", "圆满", "收成入库", "一段了结", "蓄势"),
        None,
        "种子在土里那一整个冬天：内孕、蓄势与一段事的圆满收束。宜先完成，别急着开新篇。",
        None,  # 菱形，转半圈重合：无从颠倒，故无逆位
    ),
    _rune(
        23, "ᛞ", 0x16DE, "RUNIC LETTER DAGAZ DAEG D",
        "Dagaz", "达加兹", "d", "浊齿龈塞音，如英语 day",
        "原始日耳曼语 *dagaz「日、白昼」",
        AETT_TYR,
        ("破晓", "转折", "通透", "转化", "苦尽"),
        None,
        "天亮的那一下：转折、通透与长夜之后的豁然。宜认下这个转捩点，往前走。",
        None,  # 两竖夹一个交叉，横竖两个方向都对称：无从颠倒，故无逆位
    ),
    _rune(
        24, "ᛟ", 0x16DF, "RUNIC LETTER OTHALAN ETHEL O",
        "Othala", "欧瑟拉", "o", "半闭后圆唇元音，如英语 note",
        "原始日耳曼语 *ōþalą「祖传产业、故土」",
        AETT_TYR,
        ("祖产", "故土", "传承", "家业", "界限"),
        ("失产", "被家所困", "无根", "旧约成累"),
        "传下来的那份产业：家、故土与既有的分际。宜守成、宜整理旧有，也宜分清什么是你的。",
        "产业或传承成了负担：失去依靠、被旧规矩捆住，或无处可归。",
    ),
)

#: 第 25 枚，可选。`glyph` 是空串而**不是** ᛭：设计稿拿 U+16ED 当空白符，
#: 而那个码位的官方名是 RUNIC CROSS PUNCTUATION —— 是标点，不是字母，更不是「空白」。
#: 「空白符」正确的视觉就是一块没有刻痕的石，故前端渲染空石面，不印任何字符。
WYRD = Rune(
    order=25,
    key="wyrd",
    glyph="",
    codepoint=None,
    unicode_name=None,
    name="Wyrd",
    name_zh="空白符",
    transliteration="",
    phoneme="无 —— 它不是字母，没有音值",
    name_meaning=(
        "现代牌组借古英语 wyrd「命运、际遇」为名（本义近「已发生之事」），"
        "与古诺斯语 urðr 同源 —— 那是诺伦三女神之一的名字。"
        "但空白石本无名字，此名系今人所加而非古有所传，故记为不确定。"
    ),
    name_meaning_uncertain=True,
    aett=None,
    aett_zh=None,
    reversible=False,
    upright_keywords=("未知", "尚未成形", "命运未定", "留白", "不可知"),
    reversed_keywords=None,
    upright_meaning=(
        "石面上什么也没刻：这一段还不成形，或它不该由占卜来答。"
        "宜承认有不知道的事，把这一格留给时间。"
    ),
    reversed_meaning=None,
    is_wyrd=True,
    source=WYRD_SOURCE,
)

#: 24 枚古符文；开启空白符时是 25 枚。抽牌不放回，故一次铸石内绝无重复。
DECK_24: tuple[Rune, ...] = FUTHARK
DECK_25: tuple[Rune, ...] = (*FUTHARK, WYRD)

DECK_SIZE = 24
DECK_SIZE_WITH_WYRD = 25

_RUNES_BY_KEY: dict[str, Rune] = {rune.key: rune for rune in DECK_25}


def get_rune(key: str) -> Rune:
    """按 `key` 取符文，未知则抛 `KeyError`（与塔罗 `get_card` 同一约定）。"""
    return _RUNES_BY_KEY[key]
