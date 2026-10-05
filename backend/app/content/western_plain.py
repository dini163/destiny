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
WESTERN_SMALL_READINGS: dict[str, str] = {
    # 上升点 ASC 落十二座（12 条）
    axis_sign_key("ASC", "Aries"): "你上升在白羊座，陌生人先读到的是急与直，你介入环境的方式是不绕弯，第一印象里带着抢先开口的那股劲。",
    axis_sign_key("ASC", "Taurus"): "你上升在金牛座，外人看你做什么都是从从容容的，你不抢话也不赶场，把陌生环境坐熟了，话才一句一句多起来。",
    axis_sign_key("ASC", "Gemini"): "你上升在双子座，你搭话的由头永远是新鲜事，一个问题刚问完，下一个已经顺口带出来，冷掉的场子到你嘴里就能重新转起来。",
    axis_sign_key("ASC", "Cancer"): "你上升在巨蟹座，初见时你带着一点认生的慢，气氛被确认无害之后才慢慢接话，你的入口是软的，熟了以后判若两人。",
    axis_sign_key("ASC", "Leo"): "你上升在狮子座，你一开口场面就热起来，笑和气势都不往回收，认识你的人很难把你错认成角落里的人。",
    axis_sign_key("ASC", "Virgo"): "你上升在处女座，陌生人第一眼读到你的是仔细与克制，环境要先确认安全，你才肯把自己放出来。",
    axis_sign_key("ASC", "Libra"): "你上升在天秤座，你一进门就调平两头的重量，话留三分，语气放软，哪边情绪歪了，你总是先留意到。",
    axis_sign_key("ASC", "Scorpio"): "你上升在天蝎座，生人觉出你不好接近，这份冷是你自带的底色，不是端出来的架子，热络从来快不起来。",
    axis_sign_key("ASC", "Sagittarius"): "你上升在射手座，远远看到的是你一身不设防的松快，话直来直去，笑意也不压着，陌生的场合你待得住，走得越远越自在。",
    axis_sign_key("ASC", "Capricorn"): "你上升在摩羯座，初见时你端着副正经样子，玩笑接得慢，事情接得稳，等你松下来的那一段，多半已经熟到不用再客气。",
    axis_sign_key("ASC", "Aquarius"): "你上升在水瓶座，你给人的第一印象有点淡，客气里隔着距离，你看事情的角度跟眼前的人群不一样，这份不一样你也无意解释。",
    axis_sign_key("ASC", "Pisces"): "你上升在双鱼座，你走进一个地方先沾上现场的空气，客气里带着一层没对焦的软，感受说得清，边界说不清。",
    # 天顶 MC 落十二座（12 条）
    axis_sign_key("MC", "Aries"): "你天顶落在白羊座，共事的人留给你的是破局那一格，事僵住的时候你总是先推一把，收尾的长跑反倒最磨你。",
    axis_sign_key("MC", "Taurus"): "你天顶落在金牛座，别人放到你手上的活守得久，你接得住也守得住，名声是一点点做实在了才响的，不用喊。",
    axis_sign_key("MC", "Gemini"): "你天顶落在双子座，明处认的是你问答快，传话、谈条件、把两头接起来，换到你手上就乐意办。",
    axis_sign_key("MC", "Cancer"): "你天顶落在巨蟹座，事业形象走的是照顾与可靠那一档，别人对你的期待是你把一个地方顾住，而不是冲得多快。",
    axis_sign_key("MC", "Leo"): "你天顶落在狮子座，你被放到明处就自带台面，话要说得响亮，场要撑得住，站在人前你反而更来劲。",
    axis_sign_key("MC", "Virgo"): "你天顶落在处女座，挂在你名下的标准细，活儿要经得起回头核，做完之前自己先过一遍秤，漂亮话不算数。",
    axis_sign_key("MC", "Libra"): "你天顶落在天秤座，你的路在人和人中间，调停、说圆、维持场面的体面，润滑的活经了你手便顺，硬性表态你反而慢半拍。",
    axis_sign_key("MC", "Scorpio"): "你天顶落在天蝎座，托给你的是见底的事，面上的功夫你不肯演，接到手里就要做透，做不透就整个放下。",
    axis_sign_key("MC", "Sagittarius"): "你天顶落在射手座，你奔的是远处，格局越大你越舒展，一间屋子里磨细节的位置，你坐不长久。",
    axis_sign_key("MC", "Capricorn"): "你天顶落在摩羯座，这条方向给的是往上垒的慢账，担子一层层压上肩，你认慢，不跟慢较劲，脚下是一点点垫实的感觉。",
    axis_sign_key("MC", "Aquarius"): "你天顶落在水瓶座，朝外的方向连着群体，圈子里的规矩松动比头衔更要紧，位置怎么排，你有自己的一套。",
    axis_sign_key("MC", "Pisces"): "你天顶落在双鱼座，这条路不论职级，它给的是弥开的一层，旁人为难你跟着沉，软的东西到你手里成了安慰的形状，硬碰硬的台阶你不太想上。",
    # 北交点落十二座（12 条）
    node_sign_key("Aries"): "你的北交点在白羊座，方向是自己先开口，想要的那部分讲出来，决定权不再整份交出去，抢在前头是这一段要走的路。",
    node_sign_key("Taurus"): "你的北交点在金牛座，后半程的方向是把日子过出实感，手边一样样落定，心才跟着落地，只在脑子里琢磨的旧办法越走越不灵。",
    node_sign_key("Gemini"): "你的北交点在双子座，方向落在开口与联结上，话讲出去、消息接回来，多线并行你也不当它是散，是正课。",
    node_sign_key("Cancer"): "你的北交点在巨蟹座，后半程是把在意摊开来说，照顾不再只搁在自己心里，说出口、递到手，这一格才走得通。",
    node_sign_key("Leo"): "你的北交点在狮子座，要走的方向是把自己端正地摆到人前，被人看见从躲闪变成练习，这一段练的就是那份坦然。",
    node_sign_key("Virgo"): "你的北交点在处女座，接下来练的是细与放两头一起拿住，标准松一格不算塌，手里的活照样有秩序，较劲的力气慢慢转成顺手。",
    node_sign_key("Libra"): "你的北交点在天秤座，要走的路上练的是在关系里取舍，掂量不再自己悄悄做完，摆到两个人中间说开，比关起门定来得慢也来得稳。",
    node_sign_key("Scorpio"): "你的北交点在天蝎座，功课落在交底上，信任递出去，你生分，看穿不难，交出才难，路偏偏从难处进。",
    node_sign_key("Sagittarius"): "你的北交点在射手座，要走的那边是认一个更远的方向，信条换过几轮不算白走，步子迈得越开，自己的道理反而越立得住。",
    node_sign_key("Capricorn"): "你的北交点在摩羯座，往后是长坡，没准头的事你也肯多担一阵，眼前的轻快渐渐排不到你前面。",
    node_sign_key("Aquarius"): "你的北交点在水瓶座，往人群里走还保住自己，抽身出去看的旧习惯慢慢松开，独特不再只对着自己，开始有了对面的人。",
    node_sign_key("Pisces"): "你的北交点在双鱼座，后半程考的是给感受立一道边界，领了别人的情先站回自己脚下，软不是毛病，只是学会了什么时候开口。",
}

#: 542 条的唯一聚合面（工厂与 `build_plain` 都只吃这一张）。三张分表按族拆开是为了给 14 个
#: 语料批各自的编辑边界与可读的评审 diff（偏差表第 1 行）；**`dict` 合并会静默覆盖同名键**，
#: 所以覆盖的代价由 `test_the_aggregation_has_no_key_collision` 逐字节兜住，不靠人记。
WESTERN_READINGS: dict[str, str] = {
    **western_plain_placement.WESTERN_PLACEMENT_READINGS,
    **WESTERN_SMALL_READINGS,
    **western_plain_aspect.WESTERN_ASPECT_READINGS,
}
