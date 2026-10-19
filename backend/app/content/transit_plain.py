"""行运推运页的白话判语表（Plan G spec §4、§5；一张表同时服务行运、次限、太阳弧三层）。

**这张表是平台自撰的**，不是任何古籍的转述——西洋占星这一家在仓库里没有一句既有判语可转
（同 Plan F 的 `content/western_plain.py` 头注）。自撰的诚实性支点是另一件事，而且它今天仍
然为真：**句子全部预写于表，请求时不生成**。引擎只按三层已经算出的相位与推运位置逐条选句，
不现编一个字的中文（`plain_compose.compose` 的第四条立身规矩）。

为什么**三层共用一张表**（本文件最重要的一条形状裁定，spec 裁定 R46/Global Constraints 第二条）：
键式 `transit.aspect.{moving_en}.{natal_en}.{type}` **不含技术层名**，所以「火星与本命土星成
合相」这一句同时是行运火星、次限火星、太阳弧火星三种读法的合法说法——同一个键会在同一份响应
里被印到最多三个小节（复测：`cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "from datetime import date, time; from app.engines.transit import compute_transits; c=compute_transits(birth_date=date(1990,5,4),birth_time=time(9,12),latitude=30.67,longitude=104.07,target_date=date(2026,10,3)); ks=[a.moving+'.'+a.natal+'.'+a.type for a in c.transit_aspects+c.progression.aspects+c.solar_arc.aspects]; from collections import Counter; print(max(Counter(ks).values()))"`
→ 该数 ≥2 即证同一键跨层复用）。层名一进句子，这张表就得复制三份（648 → 1944 条），而复制
就是三份互相会漂的判语。层名因此只住在**开篇句**里，条目里出现层名或日历词由
`tests/content/test_transit_plain_corpus.py::test_no_layer_word_and_no_calendar_word_inside_an_entry`
（G37 两族同住，日历词十四串在 T2 整改轮 1 A2 进门、第 39 条在 T8-A 整改轮扩到廿六串）判红。

覆盖面 = 页面已印事实的全集（spec 裁定 R47）：三层各自那张相位表逐条、次限月亮落座与落本命
宫、次限上升与天顶落座。条数 = 648 = 600（10 移动星 × 12 本命点 × 5 相位）+ 12 推运月亮落座
+ 12 推运月亮落宫 + 24 推运两轴；复测：`cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "from app.engines.plain_corpora import TRANSIT; print(len(TRANSIT.universe()))"` → 648。
**刻意不建**（spec §5.3 的键式就是这张排除表）：三层各自的十星落座/落本命宫 720 条、移动层的
逆行状态、任何度数与日期、黄经度、任何综合分数或吉凶档位收尾句。

装配形状是 `keep` + `closers=None`（spec 裁定 R48）：不分带、不重排、不由合成器补结论句——
相位条目没有符号可喂给 `band` 分支（`plain_compose.py:64-67` 那条 `ValueError`），而页尾的
一句总吉凶本来就不该由白话层来说。
"""

TRANSIT_PLAIN_SOURCE = (
    "平台自撰的行运白话转述表，把西洋占星通行的相位与推运语义整理成白话，"
    "逐条对应行运、次限与太阳弧三层已经算出的相位、推运月亮落座落宫与推运四轴。"
    "不是古籍引文，不署任何书名，不构成医疗、法律、财务建议。"
)

#: 页面出处块与推运页三处文案共用的**自撰声明**（Plan F 裁定 R50 的同一条，本计划换到行运
#: 这一家）。它是「诚实双署」里「诚实」那一半的唯一用户可见落点：用户看见的「这些中文从哪来」
#: 就这一句，所以它必须自己说得全，而不是等一本书名来背书。
#: 三句、句间「。」、无「；」——`FORBIDDEN` 含「；」，本串的口径与语料同源，由
#: `tests/content/test_transit_plain_corpus.py::test_the_source_string_is_a_provenance_string_not_a_sentence`
#: 自守（出处串与 note 都不进 `wording_violations` 的遍历，谁用谁自守）。
#: **不列星历**：三层的位置与相位是 pyswisseph 实时计算的结构值，不是表（AGENTS §7「只列真
#: 读过的表」），所以本串只说「已经算出」，引擎名走 `chart.provenance.engine`。
#: **不讲逆行**：移动层的逆行状态不在 648 的键式里（spec 偏差 5），声明句不许声称转述它。
TRANSIT_PLAIN_NOTE = (
    "三层位置与相位由瑞士星历按目标日实时计算，页面先只报这些天文与结构事实。"
    "下方的白话逐条转述上面已经算出的相位、推运月亮与推运四轴，句子全部预先写在自撰语料表里，请求时不生成任何中文。"
    "这张表是平台自撰的通行教义归纳，不是古籍引文，不署任何书名，不构成医疗、法律或财务建议，也不预测具体事件。"
)


def aspect_key(moving: str, natal: str, aspect: str) -> str:
    return f"transit.aspect.{moving}.{natal}.{aspect}"


def progressed_moon_sign_key(sign: str) -> str:
    return f"transit.progressed_moon_sign.{sign}"


def progressed_moon_house_key(house: int) -> str:
    return f"transit.progressed_moon_house.{house}"


def progressed_axis_key(axis: str, sign: str) -> str:
    return f"transit.progressed_axis.{axis}.{sign}"


# 分表 import 必须排在构造器之后、聚合面之前：`transit_plain_aspect` 反过来要引本模块的
# `aspect_key`，两模块构成刻意的环。环里唯一的可行次序是「构造器先定义，环内的兄弟才拿得到
# 它们」——把这一行提到四个构造器之前，红法是 `ImportError: cannot import name 'aspect_key'
# from partially initialized module`（2026-10-07 实测）。所有消费方（`engines/plain_corpora.py`
# 的 content import 段与本计划的本地测）因此都从本模块进门。Plan F 的同一处有两份注释
# （`content/western_plain.py:74-78` 与 `content/western_plain_placement.py:7-13`），本计划的
# 另一份在 `transit_plain_aspect.py` 的头注里。复测：
# `cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "from app.content import transit_plain, transit_plain_aspect; print(len(transit_plain.TRANSIT_READINGS))"`。
from app.content import transit_plain_aspect

#: 小节名 → 页面上那一格的标题。五个小节由 `build_plain` 的发射序消费（归 T24），覆盖面由
#: `test_transit_plain_corpus.py::test_sections_and_openers_cover_the_declared_shape` 钉。
#: **三个相位小节的标题一律带「对本命」**——键式与条目句都不含层名之外的关系说明，读者从
#: 标题就知道这一格讲的是「移动点压向本命」的关系，而不是移动星自身的位置（spec 偏差 5
#: 那条代价的唯一落点：十星落座/落宫 720 条不建，所以「移动星自己在哪」这一格页面只用
#: 表格印，白话不重复说，标题必须把它指回本命）。
TRANSIT_SECTION_TITLES: dict[str, str] = {
    "transit_aspect": "行运对本命相位",
    "progressed_aspect": "次限对本命相位",
    "directed_aspect": "太阳弧对本命相位",
    "progressed_moon": "次限月亮",
    "progressed_axis": "次限上升与天顶",
}

#: 能空的三相（spec §6 的 G15 续用：条件性小节必须有「本段无触发」的第二条开篇句）。
#: 只有三层相位表真能空——月亮落座与落宫恒 1 条（`schemas/transit.py:94-95` 的 `moon_sign_zh: str`
#: 与 `moon_natal_house: int`，都是标量不是列表）、两轴恒 2 条（同文件 `:92` 的 `angles` 就是
#: Progressed ASC 与 MC 两枚），所以不配。复测：
#: `cd backend && grep -n "moon_sign_zh\|moon_natal_house\|Progressed ASC" app/schemas/transit.py`。
#: 键 = 小节名，值 = 空态开篇句在 `TRANSIT_OPENERS` 里的**键**（不是句子文本）：装配那行走的是
#: `compose(TRANSIT, opener, …)`，`opener` 进 `openers` 查文本（`engines/western.py:219-222` 同形）。
#: 写成文本会让查不到开篇句而崩，形状与 `WESTERN_NONE_BRANCHES`（`content/western_plain.py:96-97`）一致。
TRANSIT_NONE_BRANCHES: dict[str, str] = {
    "transit_aspect": "transit_aspect_none",
    "progressed_aspect": "progressed_aspect_none",
    "directed_aspect": "directed_aspect_none",
}

#: 八条开篇句（五小节 + 三条空态分支）。**层名只住在这里**（G37 的反向义务：每条开篇句必须含
#: 自己那一层的层名词，由本地门按 `LAYER_IN_OPENER` 对账）。日期也住在这里，而且同样有尺度：
#: 页面允许任选目标日，所以 T2 整改轮 1（B3）把这族文案改成「目标日」这类日期中立形状，
#: 开篇句与条目一样不吃 `CALENDAR_WORDS` 廿六串（本地门 `test_sections_and_openers_cover_the_declared_shape` 判）。
#: 「推运」在 `progressed_*` 两句里
#: 作为「推运盘」这一整体称呼出现是合法的——它是次限层在页面上的用户可见总称
#: （`frontend/src/pages/TransitPage.tsx:252` 的「次限推运要点」、`:256` 的「推运太阴」、
#: `:268` 的「推运上升/中天」），不是另一个层的名字。
TRANSIT_OPENERS: dict[str, str] = {
    "transit_aspect": "先说行运这一层：目标日那天的十颗星此刻压在你本命盘的哪些点上，下面逐条说的是那一天哪股力气被外面的天带动。",
    "transit_aspect_none": "行运这一层在目标日没有任何一条达到经典容许度的相位，这一段没有可逐条说的话，你本命盘的落座与宫位仍是它的事实。",
    "progressed_aspect": "再看次限这一层，它看的是把出生后的一天当一年推出来的那张盘，下面逐条说的是这张盘上的星与你的本命点成什么相。",
    "progressed_aspect_none": "次限这一层在目标日没有达到经典容许度的相位，这一段没有可逐条说的关系句，你推运盘上的落座与宫位仍是它的事实。",
    "directed_aspect": "太阳弧这一层把你本命每一颗星往前推同一段弧度，它说的是推前之后的那张盘与本命的关系，读的时候要连着前两段一起看。",
    "directed_aspect_none": "太阳弧这一层在目标日没有达到经典容许度的相位，这一段没有可逐条说的话，你本命每一颗星被推进同一段弧度这件事仍是事实。",
    "progressed_moon": "次限的月亮是这张推运盘上最好读的一格，它在星座与你的本命宫之间慢慢挪，走到哪一格，生活里哪一块就近了些。",
    "progressed_axis": "次限上升与次限天顶是你推运盘的两根轴，它们不由出生时刻锁死，会随年月一点点挪，这两格讲的是方向上的变化。",
}

#: 推运月亮落座 12 + 落本命宫 12 + 次限两轴落座 24 = 48 条，由 T22 填（键籍序＝`SIGNS` 序 →
#: 1→12 → ASC 十二座然后 MC 十二座，计划 Task 22 Step 1）。留空是刻意的：
#: 聚合面与九道本地门从 T2 就要能跑完整形状，不然门在第一批就被绕过去（Plan F 的同一句
#: 理由，`content/western_plain.py:112-113`）。
#: 三族纪律（与相位族是三副不同的身体，计划 Task 22 Step 3）：`progressed_moon_sign` 键上有
#: 星座 ⇒ G34 的 `"sign" in arg` 分支生效，讲元素/形态必须等于键上那一格，一句两类并现即红；
#: 主语必须是「月亮」，只禁别的点名。`progressed_moon_house` 键上没有星座 ⇒ 任何元素/形态词
#: 即红；宫号必须恰好是键上那一宫且中文写法（`第九宫`），阿拉伯数字被 G35 与命名门同时抓；
#: 禁写「月亮逆行」（`OUT_OF_SCOPE_WORDS` 十五串）与「月亮入庙」（响应里没有的结构事实）。
#: `progressed_axis` 键上有 `axis` 与 `sign` ⇒ 自己的轴名（`上升`/`天顶`）必须在文中，别的点名
#: 不许出现（变异红串＝`['四轴条目里出现别的点名「太阳」']`）；`中天` 一律不许（十五串里，
#: 与 T25 页面统一后的字面冲突）；元素/形态可以说但必须等于键上那一格。三族共同：都不许带层名
#: （G37 对 648 条一体适用）；这三族讲的是**次限**，次限一格走一年——`这段日子`/`这一格` 合法，
#: `这几天`/`今天`/`今年` 是假话（日历词廿六串只挡得住已列的部分，写任何日/月尺度先按口径
#: 裁定第 16 条自问次限层读到是否仍为真）。
#: 三条标准件（T2 门验里已过门的样例，计划 Task 22 Step 2，逐字节照抄）＝
#: `progressed_moon_sign.Gemini`、`progressed_moon_house.9`、`progressed_axis.MC.Virgo`。
TRANSIT_PROGRESSION_READINGS: dict[str, str] = {
    # 推运月亮落座（12，`SIGNS` 序；主语「月亮」＋键上那一座，无元素/形态词）
    "transit.progressed_moon_sign.Aries": "月亮走到白羊座这一格，你想要的先于想清楚的冒出来，话赶着话往外出，慢半拍的那点思量只能事后补。",
    "transit.progressed_moon_sign.Taurus": "月亮走到金牛座这一格，你守着的那份安稳比新机会更实，动起来要先把脚下踩实，踩实了才肯挪下一步。",
    "transit.progressed_moon_sign.Gemini": "月亮走到双子座这一格，你想说的与想听的都多起来，一件事还没讲完，另一件已经顺口带出来，冷掉的场子到你嘴里能重新转起来。",
    "transit.progressed_moon_sign.Cancer": "月亮走到巨蟹座这一格，你心里那口旧的井比往日更深，亲近的人一句顶外面十句，说开的事转头又想捡回来。",
    "transit.progressed_moon_sign.Leo": "月亮走到狮子座这一格，你站出来的时刻比躲着的时刻多，场面越大越拿得出样子，一个人的时候反倒歇得住。",
    "transit.progressed_moon_sign.Virgo": "月亮走到处女座这一格，你经手的事都要过一遍细处，过了眼才放心往外递，递出去之后又回头核一遍。",
    "transit.progressed_moon_sign.Libra": "月亮走到天秤座这一格，你两头掂量的劲比往日足，先把话说平了才肯落定，落定前又替别人想一遍。",
    "transit.progressed_moon_sign.Scorpio": "月亮走到天蝎座这一格，你放进心里的话比说出口的多，深浅自己知道，旁人问到也只肯露一半。",
    "transit.progressed_moon_sign.Sagittarius": "月亮走到射手座这一格，你望向远处的劲比守在近处足，路一开就想着往前，近处的琐碎先放一放。",
    "transit.progressed_moon_sign.Capricorn": "月亮走到摩羯座这一格，你按部就班的稳比临时起意更靠得住，事情要一层一层码上去，码上去的才作数。",
    "transit.progressed_moon_sign.Aquarius": "月亮走到水瓶座这一格，你离人群半步站着更自在，合群那套自己会做，做的时候心里仍留着一段距离。",
    "transit.progressed_moon_sign.Pisces": "月亮走到双鱼座这一格，你听人说话时容易听出弦外那层，接话慢半拍，慢下来的那半拍恰好接得住。",
    # 推运月亮落本命宫（12，1→12；宫号中文恰好＝键上那一宫，无星座/元素/形态词）
    "transit.progressed_moon_house.1": "月亮移进本命第一宫，你这段日子把自己摆在头里，先顾自己那口气，顾完了才轮得到外头的事。",
    "transit.progressed_moon_house.2": "月亮移进本命第二宫，你手头的东西开始算得清，进出的数自己心里有本账，账面上的安稳让你踏实。",
    "transit.progressed_moon_house.3": "月亮移进本命第三宫，你开口的次数比往日多，路上遇见的、书里读到的都往话里带，说完了还想再说一遍。",
    "transit.progressed_moon_house.4": "月亮移进本命第四宫，你往家里待的劲比出门足，屋里那点熟惯的声响让你安心，外头的热闹反倒隔了一层。",
    "transit.progressed_moon_house.5": "月亮移进本命第五宫，你爱玩爱闹的心劲又舒展开来，玩的时候图个痛快，收场也干脆利落。",
    "transit.progressed_moon_house.6": "月亮移进本命第六宫，你手上的活计比先前更细，几样事并着做，条理一点不乱，收工再回头看看哪里漏了。",
    "transit.progressed_moon_house.7": "月亮移进本命第七宫，你与人往来时把对方摆得平，先听人把话说完，自己那半句等人家讲完才接。",
    "transit.progressed_moon_house.8": "月亮移进本命第八宫，你心里那层深的自己不太往外翻，翻也只翻一半，另一半留着等真正信的人。",
    "transit.progressed_moon_house.9": "月亮移进本命第九宫，你注意力的落点挪到远处，路、学问与陌生场合这几样在这段日子里变得亲近，日常琐事反倒容易放一放。",
    "transit.progressed_moon_house.10": "月亮移进本命第十宫，你露在人前的样子要紧起来，做事先把收尾想清楚，办出来的模样人人都看在眼里。",
    "transit.progressed_moon_house.11": "月亮移进本命第十一宫，你合得来的人多起来，话说到半路有人接，接住的那头让你觉得不是自己一个人。",
    "transit.progressed_moon_house.12": "月亮移进本命第十二宫，你愿意收着的那部分比往日多，有些话不说出来，留在心里反而更稳当。",
    # 次限两轴落座（24，ASC 十二座然后 MC 十二座；自己的轴名在文中，无别的点名）
    "transit.progressed_axis.ASC.Aries": "上升挪到白羊座这一格，你起念和抬脚是一回事，先走半步再回头找理由，找到的常是事后补上的那层。",
    "transit.progressed_axis.ASC.Taurus": "上升挪到金牛座这一格，你站到人群里话不多，先把姿态放稳，慢慢来才肯动手，旁边看着的反而把你当回事。",
    "transit.progressed_axis.ASC.Gemini": "上升挪到双子座这一格，几样话头在你嘴里一起开着，中途换了话题你也顺势拐回去，末了把它们接成一句。",
    "transit.progressed_axis.ASC.Cancer": "上升挪到巨蟹座这一格，你先顾眼前的人，再腾出耳朵听外头的动静，听见的事过一遍，让它落回地上去。",
    "transit.progressed_axis.ASC.Leo": "上升挪到狮子座这一格，时候到了你往前站半步，气先沉住再开口，声音一路敞开铺出去，站住的位置占满半场。",
    "transit.progressed_axis.ASC.Virgo": "上升挪到处女座这一格，你先把屋里屋外归置齐整，齐整了才去管大事，管完再抽身回来清点漏子。",
    "transit.progressed_axis.ASC.Libra": "上升挪到天秤座这一格，开口之前先替人求个平字，话不往急处说，气头上你先咽下去，缓一缓再讲。",
    "transit.progressed_axis.ASC.Scorpio": "上升挪到天蝎座这一格，话到嘴边你先掂轻重，掂轻了的顺嘴说走，掂重的压在舌根底下不往外翻。",
    "transit.progressed_axis.ASC.Sagittarius": "上升挪到射手座这一格，你绕开的话直着说，说完也不回头补，补的工夫不如省下来往前走。",
    "transit.progressed_axis.ASC.Capricorn": "上升挪到摩羯座这一格，手里的活计你先码齐在案头，上头一桩收完了，手才伸向底下的第二桩。",
    "transit.progressed_axis.ASC.Aquarius": "上升挪到水瓶座这一格，你跟人之间有空当，多熟的人都不往跟前挤，旁人摸不准你，却愿意信你。",
    "transit.progressed_axis.ASC.Pisces": "上升挪到双鱼座这一格，你把话锋放缓，遇着迎面顶回来的事，你先由着它软一会儿再轻轻接住。",
    "transit.progressed_axis.MC.Aries": "天顶挪到白羊座这一格，你对外那条路往快处走，先起头再补周全，旁人看着你觉得风风火火。",
    "transit.progressed_axis.MC.Taurus": "天顶挪到金牛座这一格，你对外立住的那副样子是稳的，一件事做到实在处才肯拿出去，急不来。",
    "transit.progressed_axis.MC.Gemini": "天顶挪到双子座这一格，你对外讲的东西活泛起来，见着什么人讲什么话，腔调也跟着人变。",
    "transit.progressed_axis.MC.Cancer": "天顶挪到巨蟹座这一格，你对外呈现的那面带着护，把身边的人顾好了才谈别的，旁人觉得你有心。",
    "transit.progressed_axis.MC.Leo": "天顶挪到狮子座这一格，你对外拿出来的样子带了分量，走到台前不怯，旁人认你这副担当。",
    "transit.progressed_axis.MC.Virgo": "天顶挪到处女座这一格，你对外呈现的那条方向变得仔细，把流程理顺再往外走成了默认做法，急功近利反倒不像你。",
    "transit.progressed_axis.MC.Libra": "天顶挪到天秤座这一格，你对外那条路先求两边都过得去，话摆平了才往前走，旁人觉得你公道。",
    "transit.progressed_axis.MC.Scorpio": "天顶挪到天蝎座这一格，你把对外的深浅往下压，要紧的东西攥在手里不松，旁人只见你护着它的架势。",
    "transit.progressed_axis.MC.Sagittarius": "天顶挪到射手座这一格，你对外指的方向往远处，先画大处再落细处，旁人跟着你往前看。",
    "transit.progressed_axis.MC.Capricorn": "天顶挪到摩羯座这一格，你对外立的那副样子一层一层往上码，不图快，旁人看着觉得你沉得住。",
    "transit.progressed_axis.MC.Aquarius": "天顶挪到水瓶座这一格，你对外走的路带点独，别人画好的圈你绕着走，一时看不明白，他们也愿意等你。",
    "transit.progressed_axis.MC.Pisces": "天顶挪到双鱼座这一格，你对外露出的边带着软，方向说到哪儿都不钉死，跟你来往的人不至于碰硬。",
}

#: 648 条的唯一聚合面（工厂与 `build_plain` 都只吃这一张）。两张分表按族拆开是为了给 21 个
#: 语料批各自的编辑边界与可读的评审 diff；**`dict` 合并会静默覆盖同名键**，所以覆盖的代价由
#: `test_transit_plain_corpus.py::test_no_key_and_no_sentence_are_said_twice` 逐字节兜住，不靠人记。
TRANSIT_READINGS: dict[str, str] = {
    **transit_plain_aspect.TRANSIT_ASPECT_READINGS,
    **TRANSIT_PROGRESSION_READINGS,
}
