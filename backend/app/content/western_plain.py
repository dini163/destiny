"""西洋本命盘的白话判语表（戊组 spec §4、§5）。

**这张表是平台自撰的**，不是任何古籍的转述——仓库里没有一句西洋占星的既有判语可转
（spec §1：本命盘响应的全部字段是天文与结构值）。自撰的诚实性支点是另一件事，而且它今天
仍然为真：**句子全部预写于表，请求时不生成**。引擎只按盘面已经算出的位置与相位逐条选句，
不现编一个字的中文（`plain_compose.compose` 的第四条立身规矩）。这句话就是 `WesternChart`
的出处 note 与三页文案的共同事实来源（spec §1.1 裁定 R50）。

覆盖面 = 页面已印事实的全集（R47），刻意不建的键族见 spec §2 与本计划偏差表第 17 行：
十二宫头星座 144、DES/IC 轴星座 24、南交点逐座逐宫 24、任何综合分数或档位收尾句。
"""

WESTERN_PLAIN_SOURCE = (
    "平台自撰的通行教义转述表，把西洋占星行星落座、落宫与相位的通行语义整理成白话，"
    "逐条对应本命盘已经算出的行星星座、宫位、相位、四轴与元素计数。"
    "不是古籍引文，不署任何书名，不构成医疗、法律、财务建议。"
)


def planet_sign_key(planet: str, sign: str) -> str:
    return f"western.planet_sign.{planet}.{sign}"


def planet_house_key(planet: str, house: int) -> str:
    return f"western.planet_house.{planet}.{house}"


def aspect_key(first: str, second: str, aspect: str) -> str:
    return f"western.aspect.{first}.{second}.{aspect}"


def axis_sign_key(axis: str, sign: str) -> str:
    return f"western.axis_sign.{axis}.{sign}"


def node_sign_key(sign: str) -> str:
    return f"western.node_sign.{sign}"


def node_house_key(house: int) -> str:
    return f"western.node_house.{house}"


def house_theme_key(house: int) -> str:
    return f"western.house_theme.{house}"


def element_key(element: str) -> str:
    return f"western.element.{element}"


def modality_key(modality: str) -> str:
    return f"western.modality.{modality}"


def retrograde_key(planet: str) -> str:
    return f"western.retrograde.{planet}"


# 分表 import 必须排在构造器之后、聚合面之前：`western_plain_placement` 反过来要引本模块的
# 构造器，两模块构成刻意的环，而 CPython 只接受「先完整 import 本模块」这一个入口次序——
# 构造器先定义，环内的兄弟才能拿到它们。所有消费方（plain_corpora 与本计划的本地测）都
# 按本模块先行的次序进入。复测见 `western_plain_placement` 的头注。
from app.content import western_plain_aspect, western_plain_placement

#: 小节名 → 页面上那一格的标题。八个小节由 `build_plain` 的发射序消费（T16），
#: 覆盖面由 `test_western_plain_corpus.py::test_sections_and_openers_cover_the_declared_shape` 钉。
WESTERN_SECTION_TITLES: dict[str, str] = {
    "planet_sign": "十星落座",
    "planet_house": "十星落宫",
    "aspect": "主要相位",
    "retrograde": "逆行诸星",
    "axis": "上升与天顶",
    "nodes": "北交点",
    "house_theme": "十二宫主题",
    "balance": "元素与形态",
}

#: 能空的两族（spec §6 的 G15 续用：条件性小节必须有「本段无触发」的第二条开篇句）。
#: 只有相位与逆行真能空——落座/落宫恒 10 条、轴恒 2 条、交点恒 2 条、宫题恒 12 条，
#: 而元素与形态按 `count > 0` 过滤但任何十颗星的盘必有非零元素，所以不配（偏差表第 5 行）。
#: 键 = 小节名，值 = 空态开篇句在 `WESTERN_OPENERS` 里的键。
WESTERN_NONE_BRANCHES: dict[str, str] = {"aspect": "aspect_none", "retrograde": "retrograde_none"}

WESTERN_OPENERS: dict[str, str] = {
    "planet_sign": "先说十颗星各自落在哪个星座，这一段讲的是你那十股力气各自习惯用什么方式出手。",
    "planet_house": "再说十颗星各自落在第几宫，宫位是舞台，这一段说的是你的这些力气主要在生活中哪一块使上劲。",
    "aspect": "接着看星与星之间成的相位，相位是你盘上几股力气之间的实际关系，这一段逐条说它们怎么配合或怎么拉扯。",
    "aspect_none": "这张盘上十颗星之间没有达到经典容许度的主要相位，这一段今天没有可逐条说的关系句，落座与落宫仍是你盘的事实。",
    "retrograde": "再看逆行，逆行只说明从地球上看这颗星在往回走，它给你的是一种反复、内转的节奏，不是残缺。",
    "retrograde_none": "这张盘上十颗星此刻都不逆行，这一段没有要逐条解释的逆行节奏，你的十股力气都是直接朝外用的。",
    "axis": "上升与天顶是你这张盘立起来的两根轴，一个是对外的入口，一个是对上的方向。",
    "nodes": "北交点在盘上只有一个点，传统把它读作你后半程要往那边走的方向，这里按它落的座与宫逐条说。",
    "house_theme": "十二宫各管生活中的一块，这一段按宫序把十二块各自管什么说清楚，好让你读前面那些落宫时有对照。",
    "balance": "最后是四元素与三形态在你这十颗星上的分布，它说的是整张盘的底色偏向哪一种运作方式，不是缺了什么。",
}

#: 轴 / 交点 / 宫题 / 元素 / 形态 / 逆行 七族（77 条），由 T7-T9 填。留空是刻意的：
#: 聚合面与本地门从 T1 就要能跑完整形状，不然门在第一批就被绕过去。
WESTERN_SMALL_READINGS: dict[str, str] = {}

#: 542 条的唯一聚合面（工厂与 `build_plain` 都只吃这一张）。三张分表按族拆开是为了给 14 个
#: 语料批各自的编辑边界与可读的评审 diff（偏差表第 1 行）；**`dict` 合并会静默覆盖同名键**，
#: 所以覆盖的代价由 `test_the_aggregation_has_no_key_collision` 逐字节兜住，不靠人记。
WESTERN_READINGS: dict[str, str] = {
    **western_plain_placement.WESTERN_PLACEMENT_READINGS,
    **WESTERN_SMALL_READINGS,
    **western_plain_aspect.WESTERN_ASPECT_READINGS,
}
