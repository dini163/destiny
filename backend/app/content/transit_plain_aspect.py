"""行运三层：移动点与本命点之间 600 条相位的白话判语表（T2-T21 按移动星二十批填入）。

键由 `transit_plain.aspect_key` 拼，所以本文件只有句子，没有键式；已落地**三颗移动星**——
Sun（T2 前半批 30 + T3 后半批 30）与 Moon（T4 六个内点 30 + T5 六个外点含上升/天顶 30）与
Mercury（T6-A 本命 Sun/Moon/Mercury 15 + T6-B 本命 Venus/Mars/Jupiter 15 + T7-A 本命
Saturn/Uranus/Neptune 15 + T7-B 本命 Pluto/上升/天顶 15）= **180 条**，
其余 420 条归 T8-T21 的**十四批**（其余七颗移动星各两批，每批 30 条 = 两个 15 句派）。
**自 T6 起一批分两派落地**（每派 15 句 = 三个本命点 × 五相，见计划口径裁定第 27 条）：ROSTER 与本地门
停在真实落地数，两派合成一个语料批，头注这一支笔在两派之间不落。
复测：`cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "from app.engines.plain_corpora import TRANSIT as C; k=[x for x in C.universe() if '.aspect.' in x]; l=[x for x in C.entries if '.aspect.' in x]; print(len(k), len(l), len(k)-len(l))"` → `600 180 420`。
**已落地的行一字不改**（改一行就等于改动别批已评审过的内容，那要走裁定）。
复测：`cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "from app.content import transit_plain_aspect as t; print(len(t.TRANSIT_ASPECT_READINGS))"` → 180。

一张表同时被三层读：同一个键会在同一份响应里被印到行运、次限、太阳弧三个小节，所以句子
**不许含层名**（`行运/次限/太阳弧/推运` 四字由 G37 判红），也不许含日历词与频率副词——
「今天」「这周」在次限层是假话（次限一格走一年），层名与日期都由开篇句给。日历词廿六串——原十四串自整改
轮 1（A2）有机检，序数日那十二串由口径裁定第 39 条在 T8-A 整改轮进门——`CALENDAR_WORDS` 与层名同住一条门
`test_no_layer_word_and_no_calendar_word_inside_an_entry`，上一轮头注写的「机检没有日历词门、
本批唯一的例外」在那一轮作废——钦定标准件的第四拍按控制器裁定（A1）改写，例外不复存在。
复测：`cd backend && grep -n "CALENDAR_WORDS = (" tests/content/test_transit_plain_corpus.py` → 定义行在场。

**导入次序的陷阱**：本文件引 `transit_plain` 的 `aspect_key`，而 `transit_plain` 的聚合面
又在它自己的底部引回本模块，两模块构成刻意的环。环里只有一个可行次序：**本模块必须在
`transit_plain` 的四个构造器定义之后才被执行**，所以消费方（`engines/plain_corpora.py` 的
content import 段与 `tests/content/test_transit_plain_corpus.py`）都从聚合面那一个模块进门。
把 `transit_plain.py` 里的 `from app.content import transit_plain_aspect` 提到构造器之前，
红法是 `ImportError: cannot import name 'aspect_key' from partially initialized module
'app.content.transit_plain'`（2026-10-07 实测的串，不是设想；Plan F 同处头注写的
`AttributeError` 与「先 import 分表就红」两句在本仓今天**复测不成立**——`app/content/__init__.py`
自己也 import 聚合面模块，包初始化先把环走完，所以直接 import 分表是绿的（2026-10-07 逐条复测）。
这段理由在 `transit_plain.py` 的 import 行上方另有一份（Plan F 的同一处也是两份：
`content/western_plain.py:74-78` 与 `content/western_plain_placement.py:7-13`）。
复测：`cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "from app.content import transit_plain, transit_plain_aspect; print(len(transit_plain.TRANSIT_READINGS))"` → 180（Sun/Moon/Mercury 各十二个本命点已落齐；聚合面与本表同数，因为今天 `TRANSIT_READINGS` 里只有相位列，三族推运归 T22）。
"""

from app.content.transit_plain import aspect_key

#: 键序 = 本命点序（`_natal_points`，`app/engines/transit.py:108`：十星按 `PLANETS` 序，ASC/MC 排在最后；
#: 每颗移动星的后半批各接它那五句轴点，Sun 的已由 T3 落地）×
#: `ASPECTS` 序（合相→六合→刑相→拱相→冲相），同一本命点的五句连续——这条序不是排版偏好：
#: G38(a) 的「同对五句」切片与花名册的族计数都按它读，批次追加也按它接在后面。
TRANSIT_ASPECT_READINGS: dict[str, str] = {
    # 移动星 Sun × 本命 {Sun,Moon,Mercury,Venus,Mars,Jupiter} × 五相（30 条，T2 建）
    # 本命太阳（自反对：反向键就是它自己，G38(b) 的 continue 由本地测的独立断言守着）
    aspect_key("Sun", "Sun", "conjunction"): "太阳与本命太阳成合相，两处其实是同一盏灯，想立的方向与已经在做的事对上，你手上不再有两套账，力气不从中间漏走。",
    aspect_key("Sun", "Sun", "sextile"): "太阳与本命太阳成六合，这条线自己给自己搭了个小台阶，你想往前挪一步时手上正好有可扶的地方，勇气在迈出去的那一下才长出来。",
    aspect_key("Sun", "Sun", "square"): "太阳与本命太阳成刑相，一股劲在内部拧出两个朝向，你急着表现时先跟自己较劲，力气花在调头而不是前进。",
    aspect_key("Sun", "Sun", "trine"): "太阳与本命太阳成拱相，这条线走得顺，你的光彩摆在明面上，靠的不是刻意端着，别人眼里的你与自己的感觉对得上。",
    aspect_key("Sun", "Sun", "opposition"): "太阳与本命太阳成冲相，两端指的是同一件事，你向外找一个证人时证的还是自己，认下的方向带着反驳，剩下的只是把它说出口。",
    # 本命月亮
    aspect_key("Sun", "Moon", "conjunction"): "太阳与本命月亮成合相，要立的与要守的落在同一杆秤上，你在两间屋子之间来回的路短，外头的路与心里的家是一条。",
    aspect_key("Sun", "Moon", "sextile"): "太阳与本命月亮成六合，亮的那面与软的那面互相递了个把手，你累的时候仍能把手上的事做完，做完也不觉得被掏空。",
    aspect_key("Sun", "Moon", "square"): "太阳与本命月亮成刑相，想被看见与想缩回去同时按住了你，你多半要把一头先放凉，两头都硬撑时最耗人。",
    aspect_key("Sun", "Moon", "trine"): "太阳与本命月亮成拱相，外头立的与心里安的听得进彼此，你安放情绪的地方正好也容得下你的计划，坚定用不着硬撑来证明。",
    aspect_key("Sun", "Moon", "opposition"): "太阳与本命月亮成冲相，一头朝着人前，一头朝着安静，你很难两样都不选，硬选一样时另一样会一直在门外等。",
    # 本命水星
    #: 派单钦定标准件（`task-2-brief.md:87`）的**第四拍经控制器裁定改写**（T2 整改轮 1 A1）：
    #: 句尾「今天」撞计划口径裁定 16（一张表被三层读，日期词在次限/太阳弧读法下是假话），裁定
    #: 撤下钦定句的这一拍；前三拍逐字节未动。改写后的句尾由同轮进门的日历词机检（`CALENDAR_WORDS`）
    #: 守着，不再是「机检看不见的例外」。复测（不写 grep 引串，因为注释自己就含那个串会自匹配；点名跑那道两族门，一落地键一例）：`cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m pytest "tests/content/test_transit_plain_corpus.py::test_no_layer_word_and_no_calendar_word_inside_an_entry" -o addopts="" -q` → 30 passed。
    aspect_key("Sun", "Mercury", "conjunction"): "太阳与本命水星成合相，想的事与说的话走在同一个方向，你开口前已经知道要讲哪一句，绕弯的那部分不在话里。",
    aspect_key("Sun", "Mercury", "sextile"): "太阳与本命水星成六合，心里攒着的意思肯借你的嘴出来走走，你写几行就能把散开的东西收拢，收拢也不觉得勉强。",
    aspect_key("Sun", "Mercury", "square"): "太阳与本命水星成刑相，认真的那面与嘴上轻的那面对不上，你落话前多半要慢半拍，快起来时留下的常是一个壳。",
    aspect_key("Sun", "Mercury", "trine"): "太阳与本命水星成拱相，心里的事和说出来的话之间没有门槛，你想说的自己就走到嘴边，外人听着也不费劲。",
    aspect_key("Sun", "Mercury", "opposition"): "太阳与本命水星成冲相，心里明白与嘴上说的隔着一条街口，你越想让两边对齐越容易先说错，说漏出口的部分反倒更接近真话。",
    # 本命金星
    aspect_key("Sun", "Venus", "conjunction"): "太阳与本命金星成合相，好看的和想立起来的那一面长在一处，你一动手就把事做成别人愿意看的样式，解释的话留在后头。",
    aspect_key("Sun", "Venus", "sextile"): "太阳与本命金星成六合，肯出力与讨人欢喜这两样互相帮衬，你把一件事做得顺手时，旁边的人自然愿意靠近一点。",
    aspect_key("Sun", "Venus", "square"): "太阳与本命金星成刑相，要出彩的一面与想被讨好的面互相拉，你分不出先后时两边都不得劲，一分出先后反倒松快。",
    aspect_key("Sun", "Venus", "trine"): "太阳与本命金星成拱相，你用劲的地方也受用，日子过出样子靠的不是硬撑，好看的那部分不费力气。",
    aspect_key("Sun", "Venus", "opposition"): "太阳与本命金星成冲相，一边要把事做成，一边要把人留住，两头各拽住你的一只手，先顾哪头都觉得欠着另一头。",
    # 本命火星
    aspect_key("Sun", "Mars", "conjunction"): "太阳与本命火星成合相，要立的方向和手上的劲是同一路，你一起身就在做事，心情跟在动作后头才顺。",
    aspect_key("Sun", "Mars", "sextile"): "太阳与本命火星成六合，敢上前的那一点随时借得到力，你想推进时脚下不空，推一把就有一段实路。",
    aspect_key("Sun", "Mars", "square"): "太阳与本命火星成刑相，想快与正在慢的两头一起拽，你先松开一只手才谈得上推进，否则两边都拽不动。",
    aspect_key("Sun", "Mars", "trine"): "太阳与本命火星成拱相，方向和油门合得来，你把力气花在推进上而不是花在说服自己上，走一段就有一段的样子。",
    aspect_key("Sun", "Mars", "opposition"): "太阳与本命火星成冲相，一头要领头，一头要抢着上，你身上像有两副引擎，一副启动时另一副并不服气。",
    # 本命木星
    aspect_key("Sun", "Jupiter", "conjunction"): "太阳与本命木星成合相，要立的那一面正好摊得开，你做多事时不太觉得是在硬撑，撑的那部分自己让路。",
    aspect_key("Sun", "Jupiter", "sextile"): "太阳与本命木星成六合，胆子与机会之间搭着一座小桥，你想多要一点的时候它就在手边，小声开口也接得住。",
    aspect_key("Sun", "Jupiter", "square"): "太阳与本命木星成刑相，摊得太大与守得住的家底互相拽，你两头都要顾时先分得出轻重，分不出就两边一起松。",
    aspect_key("Sun", "Jupiter", "trine"): "太阳与本命木星成拱相，想把事扩开时心里那个反对的声音没来，你胆子跟着壮，一步迈出去还能再迈第二步，路在脚前自己让。",
    aspect_key("Sun", "Jupiter", "opposition"): "太阳与本命木星成冲相，一边嫌太小一边怕太多，你在两处之间来回量，量久了才看清真正的卡点是怕。",
    # 本命土星（5 条，T3 建）
    aspect_key("Sun", "Saturn", "conjunction"): "太阳与本命土星成合相，要立起来的事正压在你本就肯扛的肩头，做出的东西自带分量，虚话挂在上头也挂不稳。",
    aspect_key("Sun", "Saturn", "sextile"): "太阳与本命土星成六合，规矩替你让出一小块落脚的空地，次序一顺，人在明处也就站得住。",
    #: 派单钦定标准件（`task-3-brief.md:19`），逐字节照抄，属口径裁定 13 的不许改写项。
    aspect_key("Sun", "Saturn", "square"): "太阳与本命土星成刑相，往前冲的那股劲与要守的规矩互相拽着，你容易先慢后猛，把长路切成小段比一口气跑完更省劲。",
    aspect_key("Sun", "Saturn", "trine"): "太阳与本命土星成拱相，扛与显这两下并不打架，你走得慢的那一段正好在垫底，看着没动的时候底也在往上加。",
    aspect_key("Sun", "Saturn", "opposition"): "太阳与本命土星成冲相，一头急着亮相，一头死守着关口，两台秤架在你身上，哪台先定，另一台就跟着再称一遍。",
    # 本命天王星（5 条，T3 建）
    aspect_key("Sun", "Uranus", "conjunction"): "太阳与本命天王星成合相，亮出来那一下正踩在你坐不住的地方，一出手套路已经换了，念头还落在后半截。",
    aspect_key("Sun", "Uranus", "sextile"): "太阳与本命天王星成六合，你身上那点不对劲有人接得住，想换走法时手边总有现成的缝，钻过去也不惊动谁。",
    aspect_key("Sun", "Uranus", "square"): "太阳与本命天王星成刑相，把现状按稳与一把掀开的冲动互相撞，你越想按住，越有东西在别处裂开，按着的手掌也跟着发麻。",
    aspect_key("Sun", "Uranus", "trine"): "太阳与本命天王星成拱相，你想走的新路跟骨子里带的反常同向，变化上门时接得不吃力，接住还能顺手归位。",
    aspect_key("Sun", "Uranus", "opposition"): "太阳与本命天王星成冲相，你日子照旧过着，心里想拆的劲一直没停，等它真拆掉一回，原先那种过法就再也拼不回原样。",
    # 本命海王星（5 条，T3 建）
    aspect_key("Sun", "Neptune", "conjunction"): "太阳与本命海王星成合相，显出来的那层带着毛边，事还没定形，你心里先有了轮廓，讲出口又差半步。",
    aspect_key("Sun", "Neptune", "sextile"): "太阳与本命海王星成六合，说不清的想象正好派上手上的用场，你照着感觉做一步，做完才看清它本来是有道理的。",
    aspect_key("Sun", "Neptune", "square"): "太阳与本命海王星成刑相，把事做实与把事想美两股力彼此稀释，你站在哪边都觉得隔着一层雾，越描越淡。",
    aspect_key("Sun", "Neptune", "trine"): "太阳与本命海王星成拱相，想象与手边的活共用一副水性，你埋头做事时，感觉自己漫进了缝里。",
    aspect_key("Sun", "Neptune", "opposition"): "太阳与本命海王星成冲相，你把界限划清楚，它跟着又把这条边泡软，每样都只做得到一半，剩下那半还在慢慢散开。",
    # 本命冥王星（5 条，T3 建）
    aspect_key("Sun", "Pluto", "conjunction"): "太阳与本命冥王星成合相，出头的那处正连着你心底最深的执，做事不肯只做半截，一做就连根翻起。",
    aspect_key("Sun", "Pluto", "sextile"): "太阳与本命冥王星成六合，那股狠劲有个能松动的缺口，你往一件事里钻得深，钻到后来反倒松开手。",
    aspect_key("Sun", "Pluto", "square"): "太阳与本命冥王星成刑相，想全部握住与想一把烧掉轮流上阵，你在自己身上用重手，用过又收不回。",
    aspect_key("Sun", "Pluto", "trine"): "太阳与本命冥王星成拱相，沉在底下的狠劲与摆在明处的作为接得上，你一投入就连心带人下去，出来时讲的话比进去前重。",
    aspect_key("Sun", "Pluto", "opposition"): "太阳与本命冥王星成冲相，你心里想要的是干脆到底，手边却总留着一条没关上的退路，两股劲一起上手，拧到掌心全是汗，最后谁也没让谁。",
    # 本命上升（轴点，5 条，T3 建；点名一律 `上升`，英文名与 `中天` 都不许进句子）
    aspect_key("Sun", "ASC", "conjunction"): "太阳与本命上升成合相，要站出来的样子与你平时那副样子叠成同一张，你手上一动，脸上的神情就跟着动了。",
    aspect_key("Sun", "ASC", "sextile"): "太阳与本命上升成六合，你想出的头与惯常的门面对得上，一露面就有人接住话，你顺着听两句，话头也会回到你手里。",
    aspect_key("Sun", "ASC", "square"): "太阳与本命上升成刑相，心里认定的方向与脸上那层习惯互相绊，你往前迈一步，神情反倒先跟不上。",
    aspect_key("Sun", "ASC", "trine"): "太阳与本命上升成拱相，你想显的与天生带的走同一条道，人一进场，位置自己就站端正了。",
    aspect_key("Sun", "ASC", "opposition"): "太阳与本命上升成冲相，一头想站到明处，一头想缩回暗处，你在门槛内外来回挪，挪久了才分得出哪头是真想。",
    # 本命天顶（轴点，5 条，T3 建；`本命天顶` 四字是移动侧为太阳时的合法形状）
    aspect_key("Sun", "MC", "conjunction"): "太阳与本命天顶成合相，出面做的那件事正是你被认下的那一件，两头并成一个说法，自证那道工序就省下了。",
    aspect_key("Sun", "MC", "sextile"): "太阳与本命天顶成六合，往上走的路上留着一处落脚的平台，你想试一步时脚下有处可踩，踩实了方向才清楚。",
    aspect_key("Sun", "MC", "square"): "太阳与本命天顶成刑相，你想亮的与位置上扛着的互相拽，越使劲往上够，脚下那根桩子越往土里沉。",
    aspect_key("Sun", "MC", "trine"): "太阳与本命天顶成拱相，你走的与外头认的那条线自己对齐，抬脚就在正路上，走到第几步你心里都有底。",
    aspect_key("Sun", "MC", "opposition"): "太阳与本命天顶成冲相，一头要把样子做出来，一头要守住本分，你在两头之间换姿势，换到哪儿都觉得站歪了。",
    # 移动星 Moon × 本命 {Sun,Moon,Mercury,Venus,Mars,Jupiter} × 五相（30 条，T4 建）
    # 本命太阳（反向键 Sun×本命Moon 的五句已在 T2 落地：这里是「情绪压到志向上」，不是「志向压到情绪上」）
    aspect_key("Moon", "Sun", "conjunction"): "月亮与本命太阳成合相，心里的冷暖与站出来那副主张并成一股，你开口讲的既是想法也是情绪，拆不出哪半句只属于脑子。",
    aspect_key("Moon", "Sun", "sextile"): "月亮与本命太阳成六合，心口的起伏肯往主张那边靠半步，你讲心里话一开口就到点上，说完想法还在原处，人也没跟着跑偏。",
    aspect_key("Moon", "Sun", "square"): "月亮与本命太阳成刑相，你心里的热还没散尽，人已经站到要交代清楚的地方，越想装作没事，动作里越带着委屈。",
    aspect_key("Moon", "Sun", "trine"): "月亮与本命太阳成拱相，情绪跟心意同踩一副步子，你起念时手上不空，做出来的东西自带一层活气。",
    aspect_key("Moon", "Sun", "opposition"): "月亮与本命太阳成冲相，胸口的潮性与立住的志向各走半程，你在前头把道理讲完，心里听见的却是另一句。",
    # 本命月亮（自反对：反向键就是它自己，G38(b) 的 continue 由独立断言守着；五句尾必须五样）
    aspect_key("Moon", "Moon", "conjunction"): "月亮与本命月亮成合相，两头的感受叠在同一片水上，你心里翻一下，脸上就起波纹，怎么按都按不平。",
    aspect_key("Moon", "Moon", "sextile"): "月亮与本命月亮成六合，起落的波澜认得你做事的节奏，情绪上来那阵你没有整个散开，活还留在手头。",
    aspect_key("Moon", "Moon", "square"): "月亮与本命月亮成刑相，一层情绪压住另一层，你在心里跟自己绕个死结，外头那桩事反倒退成了背景。",
    aspect_key("Moon", "Moon", "trine"): "月亮与本命月亮成拱相，起落的两层水自己通着，你难过完还能说出难过前的心气，省下一趟从头试探。",
    aspect_key("Moon", "Moon", "opposition"): "月亮与本命月亮成冲相，两桩心事一起在场，谁也不肯让谁先讲，你一开口其中一件，另一件就在底下把声调抬高。",
    # 本命水星
    aspect_key("Moon", "Mercury", "conjunction"): "月亮与本命水星成合相，嘴上的调门跟着心里的滋味一起走，你讲出口的话总多带一层情绪，自己听着也分得清。",
    aspect_key("Moon", "Mercury", "sextile"): "月亮与本命水星成六合，情绪愿意往话里来，你随口讲出的那一句正好对上思路，讲完人也跟着清醒些。",
    aspect_key("Moon", "Mercury", "square"): "月亮与本命水星成刑相，火气横在思路中间，你越想把话讲平，出口的那一句就越带尖，回头还要再补一遍。",
    aspect_key("Moon", "Mercury", "trine"): "月亮与本命水星成拱相，心的起伏与脑的线路合着同一副拍子，你想到哪一层就能讲到哪一层，中间不打绊。",
    aspect_key("Moon", "Mercury", "opposition"): "月亮与本命水星成冲相，心口讲的一套与脑子讲的一套互相抢话，你听着哪边都有理，落笔才发现两层话没落在同一处。",
    # 本命金星
    aspect_key("Moon", "Venus", "conjunction"): "月亮与本命金星成合相，心里的喜好与手上的温柔缠成一团，你对谁热起来时连样子都省了，冷下去也利索。",
    aspect_key("Moon", "Venus", "sextile"): "月亮与本命金星成六合，你肯为一点小东西让出个位置，喜欢先亮一小截，心气也跟着松一寸。",
    aspect_key("Moon", "Venus", "square"): "月亮与本命金星成刑相，想被领的那点心气与端着的分寸彼此绊着，你示好的动作一出口变了味，收也收不回来。",
    aspect_key("Moon", "Venus", "trine"): "月亮与本命金星成拱相，你看见顺眼的东西，心里那根弦自己跟着调好，再添什么都不像是外来的。",
    aspect_key("Moon", "Venus", "opposition"): "月亮与本命金星成冲相，你给出去的那份好总想听个回音，回音迟了一步，那只手就自己往回收。",
    # 本命火星
    aspect_key("Moon", "Mars", "conjunction"): "月亮与本命火星成合相，情绪直接落在动作上，你先按着心情做，事反倒推得快，做完才认出刚才使力的是谁。",
    aspect_key("Moon", "Mars", "sextile"): "月亮与本命火星成六合，劲头上来时正好推得动手上的活，你顺着它使半把力，事情就走稳了。",
    aspect_key("Moon", "Mars", "square"): "月亮与本命火星成刑相，想冲的劲与想缓的劲彼此拖着，你脚下一步没迈出去，手上的火已经先烧到别处。",
    aspect_key("Moon", "Mars", "trine"): "月亮与本命火星成拱相，胸中的热与身上的劲对上一个步调，你用力时手上是平的，用完也就松手。",
    aspect_key("Moon", "Mars", "opposition"): "月亮与本命火星成冲相，咽下去的和顶上去的分开各处发作，你面上这一处还平静，指节那一处已经捏紧了。",
    # 本命木星
    aspect_key("Moon", "Jupiter", "conjunction"): "月亮与本命木星成合相，心底的余量随潮水涨开，你高兴时松得彻底，闷起来也把什么都看得大。",
    aspect_key("Moon", "Jupiter", "sextile"): "月亮与本命木星成六合，情绪松一分，眼前的余地跟着宽一分，你顺嘴安慰别人时自己也退了一步。",
    aspect_key("Moon", "Jupiter", "square"): "月亮与本命木星成刑相，一热就想摊开，转头就想收回来，你前脚揽下好几摊，后脚又把门带上。",
    aspect_key("Moon", "Jupiter", "trine"): "月亮与本命木星成拱相，心里的宽与眼下的局面彼此成全，你容得下人也容得下自己，情绪来了也淹不掉场子。",
    aspect_key("Moon", "Jupiter", "opposition"): "月亮与本命木星成冲相，心里那面想放宽，分寸这面想收紧，你在明处退了一步，暗处就多堵一阵。",
    # 移动星 Moon × 本命 {Saturn,Uranus,Neptune,Pluto,ASC,MC} × 五相（30 条，T5 建）
    # 本命土星（5 条，T5 建；反向键 Saturn×本命Moon 归 T14，今日未落地；拱相句是派单钦定标准件，逐字节照抄）
    aspect_key("Moon", "Saturn", "conjunction"): "月亮与本命土星成合相，心气一上来先在规矩跟前站一站，你想说什么先把场合掂一遍，热劲要走两步才看得见。",
    aspect_key("Moon", "Saturn", "sextile"): "月亮与本命土星成六合，你心里的委屈有处可以慢慢消化，情绪掉下去还能自己回到手上这摊活。",
    aspect_key("Moon", "Saturn", "square"): "月亮与本命土星成刑相，肩上扛着的分量压住了想靠近的念头，你想挪半步，脚却又退回去。",
    aspect_key("Moon", "Saturn", "trine"): "月亮与本命土星成拱相，情绪与承担之间有一条顺的通道，你在要紧的场合哭不出来也能把事情稳住，这不算冷。",
    aspect_key("Moon", "Saturn", "opposition"): "月亮与本命土星成冲相，身子想靠过去，嘴上先把距离摆明，你越急着被懂，出口的话越硬。",
    # 本命天王星（5 条，T5 建；反向键 Uranus×本命Moon 归 T16，今日未落地）
    aspect_key("Moon", "Uranus", "conjunction"): "月亮与本命天王星成合相，身上的开关拨过去从不预告，你刚还挨着人说话，扭头就想一个人待着。",
    aspect_key("Moon", "Uranus", "sextile"): "月亮与本命天王星成六合，心思转得急也转得干净，你上一句还在别扭，下一句已经松了口。",
    aspect_key("Moon", "Uranus", "square"): "月亮与本命天王星成刑相，人刚坐定，绷着的那根筋又蹦起来，你想稳一稳，脾气偏要从旁边岔出去。",
    aspect_key("Moon", "Uranus", "trine"): "月亮与本命天王星成拱相，变化一来心情就跟着转弯，你从别扭到松开中间没隔几步，脸上先透出来。",
    aspect_key("Moon", "Uranus", "opposition"): "月亮与本命天王星成冲相，一头想贴着人，一头想抽身走开，两样轮着上手，谁赢了你都不落定。",
    # 本命海王星（5 条，T5 建；反向键 Neptune×本命Moon 归 T18，今日未落地）
    aspect_key("Moon", "Neptune", "conjunction"): "月亮与本命海王星成合相，新起的滋味先成了画面才成了话，你还没开口，眼眶已经有点热。",
    aspect_key("Moon", "Neptune", "sextile"): "月亮与本命海王星成六合，模糊的心事有处化成软话，你替人想的时候，自己那块也松开一点。",
    aspect_key("Moon", "Neptune", "square"): "月亮与本命海王星成刑相，你把没发生过的事先在心上过了一遍，事到眼前，气反倒先弱了。",
    aspect_key("Moon", "Neptune", "trine"): "月亮与本命海王星成拱相，没来由的感觉会走到手上，你交出去的那件活，边缘跟起初想的不是一回事。",
    aspect_key("Moon", "Neptune", "opposition"): "月亮与本命海王星成冲相，你想被什么打动，又想把那东西看清楚，看与动之间总差着一点火候。",
    # 本命冥王星（5 条，T5 建；反向键 Pluto×本命Moon 归 T20，今日未落地）
    aspect_key("Moon", "Pluto", "conjunction"): "月亮与本命冥王星成合相，心里的动静一起来就不肯停在浅处，你受不住淡淡的来往，客套的那点热一碰就凉掉了。",
    aspect_key("Moon", "Pluto", "sextile"): "月亮与本命冥王星成六合，心往深处走时总有个能歇脚的弯，你在下头也还有话说，不至于去了没声。",
    aspect_key("Moon", "Pluto", "square"): "月亮与本命冥王星成刑相，你把一句委屈翻来覆去地焐着，事情其实早过去了，里头还发着烫。",
    aspect_key("Moon", "Pluto", "trine"): "月亮与本命冥王星成拱相，那些平时压着不放的劲自己往上托，你投入时不缩手，退出来还是满的。",
    aspect_key("Moon", "Pluto", "opposition"): "月亮与本命冥王星成冲相，想要个干脆的了断，又留着没说完的那半句，你两头都不放，手上就一直发紧。",
    # 本命上升（轴点，5 条，T5 建；轴在本表只做本命点，永远没有反向键；点名一律「上升」，别的轴名都不许进句子）
    aspect_key("Moon", "ASC", "conjunction"): "月亮与本命上升成合相，别人先瞧见的那处正被心情牵着，你才进门，第一步就已经带着那点温度。",
    aspect_key("Moon", "ASC", "sextile"): "月亮与本命上升成六合，你的起伏才露出一点点，对面已经先猜着了七八分，话到嘴边就少走一段。",
    aspect_key("Moon", "ASC", "square"): "月亮与本命上升成刑相，你心里沉了下去，外头的平稳还端着，话一出口两边对不齐，模样显得别扭。",
    aspect_key("Moon", "ASC", "trine"): "月亮与本命上升成拱相，心里怎么想，人就怎么显出来，你省下一道整理表情的功夫，看着也自在。",
    aspect_key("Moon", "ASC", "opposition"): "月亮与本命上升成冲相，你想让人看清，又想把人挡在门外，人真到了跟前，你反倒去拧门闩。",
    # 本命天顶（轴点，5 条，T5 建；同上，轴不做移动点所以无反向键；点名一律「天顶」）
    aspect_key("Moon", "MC", "conjunction"): "月亮与本命天顶成合相，你出面担的那份差事里也掺着心情，成绩里还有一块不全是练出来的功夫。",
    aspect_key("Moon", "MC", "sextile"): "月亮与本命天顶成六合，胸口的波澜退到后头，手上的分寸反倒更清楚，你把场面撑着，里头也不乱。",
    aspect_key("Moon", "MC", "square"): "月亮与本命天顶成刑相，脸上的平静绷得住，心里的火却没有真的灭，两样一起摊在你手上，哪样都不肯收。",
    aspect_key("Moon", "MC", "trine"): "月亮与本命天顶成拱相，起落挡不住手上的路，你人前做得稳当，人后也还能自己慢慢缓回来。",
    aspect_key("Moon", "MC", "opposition"): "月亮与本命天顶成冲相，心里想随性去做，位置又不许你随性，你把两头各让一步，让步的样子谁都骗不了。",
    # 移动星 Mercury × 本命 {Sun,Moon,Mercury} × 五相（15 条，T6-A 建；本命点序的前三格，后三格见下面三族）
    # 本命太阳（5 条，T6-A 建；反向键 Sun×本命水星 的五句 T2 已进表——这里是思路压到主张上，不是主张压到思路上）
    aspect_key("Mercury", "Sun", "conjunction"): "水星与本命太阳成合相，商量的路跟你立起来的方向是同一条，话讲到哪一步，事情就往哪一步收紧。",
    aspect_key("Mercury", "Sun", "sextile"): "水星与本命太阳成六合，你先能把想站的立场讲出个轮廓，讲完它就从嘴边挪到明处，形状是自己长出来的。",
    aspect_key("Mercury", "Sun", "square"): "水星与本命太阳成刑相，打听与追问先缠住你想立的那个架子，问到后来，连原本的主张都松了扣。",
    aspect_key("Mercury", "Sun", "trine"): "水星与本命太阳成拱相，嘴上的话替主张开路，你一面说一面看清自己站在哪一处，立场跟着水落石出。",
    aspect_key("Mercury", "Sun", "opposition"): "水星与本命太阳成冲相，外头问来的跟你所立的总差一步，你答得再顺，那句到底要什么反而听不见。",
    # 本命月亮（5 条，T6-A 建；反向键 Moon×本命水星 的五句 T4 已进表——这里是问答压到心情上，不是心情渗到话里）
    aspect_key("Mercury", "Moon", "conjunction"): "水星与本命月亮成合相，问一句答一句都贴着你心口一阵跳动，边讲边摸到情绪的形状，说得慢，摸得也细。",
    aspect_key("Mercury", "Moon", "sextile"): "水星与本命月亮成六合，心里打的结经你自问自答就松了小半，你再往下梳，才看清自己真正在意的是什么。",
    aspect_key("Mercury", "Moon", "square"): "水星与本命月亮成刑相，一句追一句直往软的地方戳，你被问得心里发紧，答出来的仍旧是客气话。",
    aspect_key("Mercury", "Moon", "trine"): "水星与本命月亮成拱相，胸中一团说不清的话自己会找词，你顺着往下说，说着说着根由就露出来一半。",
    aspect_key("Mercury", "Moon", "opposition"): "水星与本命月亮成冲相，讲给人听的一套和留下来自己消化的一套各走各路，你答得爽快，里头那块仍旧发软。",
    # 本命水星（5 条，T6-A 建；自反对：反向键就是它自己，G38(b) 的 continue 由独立断言守着；五句尾必须五样）
    aspect_key("Mercury", "Mercury", "conjunction"): "水星与本命水星成合相，念头跟着念头往外冒，你问一句还剩三句候着，收不住尾，话一路往上叠。",
    aspect_key("Mercury", "Mercury", "sextile"): "水星与本命水星成六合，卡住的那截思路肯给自己让一步，你先把它放一放，回头再想它自己会顺。",
    aspect_key("Mercury", "Mercury", "square"): "水星与本命水星成刑相，一条理推到半路分作两样，两样底下是同一份前提，一句说法因此改了又改，顶住的正是你最熟的一节。",
    aspect_key("Mercury", "Mercury", "trine"): "水星与本命水星成拱相，念头转得顺也说得圆，你自己跟自己商量的那条路，起头和收尾合得上，商量过就等于定过。",
    aspect_key("Mercury", "Mercury", "opposition"): "水星与本命水星成冲相，明处想把底细辩明白，暗处想把来龙去脉摸清楚，两头各拽着你的一句话，接了这头就丢那头。",
    # 本命金星（5 条，T6-B 建；本派镜子 = 已落地的 Sun×本命金星 五句与 Moon×本命金星 五句；反向键 Venus×本命水星 归 T8）
    aspect_key("Mercury", "Venus", "conjunction"): "水星与本命金星成合相，喜好要在纸上过一遍才成形，你还没落笔的时候，其实说不准自己中意哪样。",
    aspect_key("Mercury", "Venus", "sextile"): "水星与本命金星成六合，谈得拢与谈得动是同一件事，你愿意把喜好直接讲出口，商量时少了一层来回的试探。",
    aspect_key("Mercury", "Venus", "square"): "水星与本命金星成刑相，想先问明白到底喜欢什么，手上却已经在挑，你问的节奏总比挑的节奏慢半拍。",
    aspect_key("Mercury", "Venus", "trine"): "水星与本命金星成拱相，一句喜好说到位便停住，你很少把喜欢铺到第二句，省下来的劲还留在身上。",
    aspect_key("Mercury", "Venus", "opposition"): "水星与本命金星成冲相，一句要把喜欢往前推，一句又把它往后拽，你跟着前一句走，后一句自己在半路停住。",
    # 本命火星（5 条，T6-B 建；镜子 = 已落地的 Sun×本命火星 五句与 Moon×本命火星 五句；反向键 Mars×本命水星 归 T10）
    aspect_key("Mercury", "Mars", "conjunction"): "水星与本命火星成合相，想问与想动几乎同时起身，你话还没说尽，次序跟着就理顺了，两拍并成了一拍。",
    aspect_key("Mercury", "Mars", "sextile"): "水星与本命火星成六合，三句要说的只讲两句，你少说一句也不觉得缺了什么，劲仍然完整地留着。",
    aspect_key("Mercury", "Mars", "square"): "水星与本命火星成刑相，心里认下的理一落到字面上就变硬，你写了又删，删了又写，指头比嘴先急。",
    aspect_key("Mercury", "Mars", "trine"): "水星与本命火星成拱相，说出口的安排与手上的动作咬成一处，你报出的是哪一串步骤，做完摆出来的就是那一串。",
    aspect_key("Mercury", "Mars", "opposition"): "水星与本命火星成冲相，话递到一半又被按住，往外递与往里收分头使力，你只用上一头，另一头仍在原地憋着。",
    # 本命木星（5 条，T6-B 建；镜子 = 已落地的 Sun×本命木星 五句与 Moon×本命木星 五句；反向键 Jupiter×本命水星 归 T12）
    aspect_key("Mercury", "Jupiter", "conjunction"): "水星与本命木星成合相，本可以收住的话，你偏要一路铺开，铺到第五句才觉出自己绕出了好远。",
    aspect_key("Mercury", "Jupiter", "sextile"): "水星与本命木星成六合，散着的想法愿意在你笔下理出头绪，你看着它们一行一行摆稳，口气也跟着放缓。",
    aspect_key("Mercury", "Jupiter", "square"): "水星与本命木星成刑相，正说得兴起，胸口另有半句在拦，你哪头都不肯放下，话因此走得磕绊。",
    aspect_key("Mercury", "Jupiter", "trine"): "水星与本命木星成拱相，话头一来，你的语速自己就提了上去，话头与话头中间几乎留不出空档。",
    aspect_key("Mercury", "Jupiter", "opposition"): "水星与本命木星成冲相，话想讲得响，又想整个收进最里头，你朝外走一步，里头的声音矮了半截。",
    # 本命土星（5 条，T7-A 建；本派镜子 = 已落地的 Sun×本命土星 五句与 Moon×本命土星 五句；反向键 Saturn×本命水星 归 T14）
    aspect_key("Mercury", "Saturn", "conjunction"): "水星与本命土星成合相，想到的事要落成字才显出形状，你写一句停一停，写下的总比原先想讲的短一截。",
    aspect_key("Mercury", "Saturn", "sextile"): "水星与本命土星成六合，先讲哪样后讲哪样，你伸手理一理就顺了，讲完之后前后还连着，也没散。",
    aspect_key("Mercury", "Saturn", "square"): "水星与本命土星成刑相，理是通的那一头，口却先关上半扇，你把整句硬讲完，听着像从隔壁传过来。",
    aspect_key("Mercury", "Saturn", "trine"): "水星与本命土星成拱相，问与答中间自己让出一段空，你不抢着去填，话便一句压着一句地落稳。",
    aspect_key("Mercury", "Saturn", "opposition"): "水星与本命土星成冲相，想把话讲透，转头又想把嘴闭上，你特意说慢些，落下来的字反倒更响。",
    # 本命天王星（5 条，T7-A 建；本派镜子 = 已落地的 Sun×本命天王星 五句与 Moon×本命天王星 五句；反向键 Uranus×本命水星 归 T16）
    aspect_key("Mercury", "Uranus", "conjunction"): "水星与本命天王星成合相，讲到中途调子忽然换掉，不经过你点头，等你往下接，话已经走到了没打算去的地方。",
    aspect_key("Mercury", "Uranus", "sextile"): "水星与本命天王星成六合，你脑筋转得快那一截肯带你一段，思路一拐到别处，另一头自己跟了上来。",
    aspect_key("Mercury", "Uranus", "square"): "水星与本命天王星成刑相，你想按原样开口，嗓子却先自己变了调，后半句的舌头有点跟不上。",
    aspect_key("Mercury", "Uranus", "trine"): "水星与本命天王星成拱相，对方话还没说完，你已经答到了他要问的意思上，走的却是条没人走过的岔路。",
    aspect_key("Mercury", "Uranus", "opposition"): "水星与本命天王星成冲相，一句要说得稳，一句要说得怪，两者错开半步，你先抓住哪一句，另一句就迟到一截。",
    # 本命海王星（5 条，T7-A 建；本派镜子 = 已落地的 Sun×本命海王星 五句与 Moon×本命海王星 五句；反向键 Neptune×本命水星 归 T18）
    aspect_key("Mercury", "Neptune", "conjunction"): "水星与本命海王星成合相，意思走到笔尖时自己成了另一句，你回头再对，两句已经对不到一处。",
    aspect_key("Mercury", "Neptune", "sextile"): "水星与本命海王星成六合，追问一松手，答案自己浮了上来，等你重新开口时，它已经站到明处。",
    aspect_key("Mercury", "Neptune", "square"): "水星与本命海王星成刑相，一句问到要紧处，胸口先空了一下，剩下的半句你换了口气才问完。",
    aspect_key("Mercury", "Neptune", "trine"): "水星与本命海王星成拱相，你跟着感觉往下讲，讲出来的比事情本身宽一些，宽的那点正是你想捎上的。",
    aspect_key("Mercury", "Neptune", "opposition"): "水星与本命海王星成冲相，问出来的与咽回去的分住两头，前头那句你追到很细，后头的自己在底下变轻。",
    # 本命冥王星（5 条，T7-B 建；本派镜子 = 已落地的 Sun×本命冥王星 五句与 Moon×本命冥王星 五句；反向键 Pluto×本命水星 归 T20，今日未落地）
    aspect_key("Mercury", "Pluto", "conjunction"): "水星与本命冥王星成合相，先出口的话不由你挑，压在里头的意思自己挤到前头，你不过是顺着把它讲完。",
    aspect_key("Mercury", "Pluto", "sextile"): "水星与本命冥王星成六合，你压着没讲的那块并不散，话说到旁边时，它又占回你嘴里半分分量。",
    aspect_key("Mercury", "Pluto", "square"): "水星与本命冥王星成刑相，你想把这桩轻轻带过去，话却自己绕回旧地方，本来要讲的反而没轮到。",
    aspect_key("Mercury", "Pluto", "trine"): "水星与本命冥王星成拱相，那块的事你从头到尾只讲一遍，讲过的不回头重说，讲到后面也没把它再拎出来。",
    aspect_key("Mercury", "Pluto", "opposition"): "水星与本命冥王星成冲相，人家问的是眼前这件，你答的却是底下那件，答完两边都不肯再往下追。",
    # 本命上升（轴点，5 条，T7-B 建；本派镜子 = 已落地的 Sun×本命上升 五句与 Moon×本命上升 五句；轴在本表只做本命点，永远没有反向键；点名一律「上升」，别的轴名都不许进句子）
    aspect_key("Mercury", "ASC", "conjunction"): "水星与本命上升成合相，你人还在后头，开口的头一句已经先到场子里，等你站定，讲的已是第二遍。",
    aspect_key("Mercury", "ASC", "sextile"): "水星与本命上升成六合，来意一句就交代完，对方到嘴边又把要问的收回去，你备好的答话就没了下文。",
    aspect_key("Mercury", "ASC", "square"): "水星与本命上升成刑相，你把开场说得太满，轮到自己站出时反而没有空位，人只能跟在话后头走。",
    aspect_key("Mercury", "ASC", "trine"): "水星与本命上升成拱相，你把头一句讲稳当，后面的话自己就短了，同一场照面不再要你露第二回。",
    aspect_key("Mercury", "ASC", "opposition"): "水星与本命上升成冲相，你越按着的那句越先出了口，你还在最前面打转，屋里人已经听见它在响。",
    # 本命天顶（轴点，5 条，T7-B 建；本派镜子 = 已落地的 Sun×本命天顶 五句与 Moon×本命天顶 五句；轴不做移动点所以无反向键；点名一律「天顶」，`中天` 不许进句子；合相句是派单钦定标准件，逐字节照抄）
    aspect_key("Mercury", "MC", "conjunction"): "水星与本命天顶成合相，想到的与摆在明面上的几乎是一回事，你写下的说明就是你的立场，两套说法在这里合在一处。",
    aspect_key("Mercury", "MC", "sextile"): "水星与本命天顶成六合，你起头的说法宽过实际要做的活，等真上手，多出的那一层刚好接住你。",
    aspect_key("Mercury", "MC", "square"): "水星与本命天顶成刑相，你先讲难处，把结论押到最后才开口，听的人得倒回来对一遍才对得上。",
    aspect_key("Mercury", "MC", "trine"): "水星与本命天顶成拱相，你出面讲那几句时声音是开着的，字字都落得下去，讲完喉咙还是松的。",
    aspect_key("Mercury", "MC", "opposition"): "水星与本命天顶成冲相，你想先把结论递出去，又想先把缘由讲完，两句挤在同一拍上，反倒前后都排不开。",
    # 本命太阳（5 条，T8-A 建；本派镜子 = 已落地的 Sun×本命太阳 五句与 Moon×本命太阳 五句；反向键 Sun×本命金星 的五句 T2 已落地——本派 15 个键的反向件全部在场，G38(b) 自本派起是活门；这里是喜好蹭到被认下的那副主张上，不是主张直接走到喜好上）
    aspect_key("Venus", "Sun", "conjunction"): "金星与本命太阳成合相，你想被人认下的那副样子外头裹着一层修饰，旁人夸的是这层，挑的也是这层，你都当作有人在说你。",
    aspect_key("Venus", "Sun", "sextile"): "金星与本命太阳成六合，你肯在有些人面前多花一点心思，开场那几句修得圆润些，修过之后话里的意思没换。",
    aspect_key("Venus", "Sun", "square"): "金星与本命太阳成刑相，想把话说透与想把人拉近这两套动作都在你嘴边打转，换了三四回，哪一回都差着一点。",
    aspect_key("Venus", "Sun", "trine"): "金星与本命太阳成拱相，你出面时旁人记住的头一件是你把话说得多好听，事情本身要到第二遍才被想起。",
    aspect_key("Venus", "Sun", "opposition"): "金星与本命太阳成冲相，你把场面话说得越妥帖，想争的那件就越往后缩，缩到后来连它本来的样子都淡了，翻出来先愣一下。",
    # 本命月亮（5 条，T8-A 建；本派镜子 = 已落地的 Sun×本命月亮 五句与 Moon×本命月亮 五句；反向键 Moon×本命金星 的五句 T4 已落地，同属活门；这里改的是你觉得省力与费力的亲近方式与喜好阈值，不是喜好被情绪缠成一团）
    aspect_key("Venus", "Moon", "conjunction"): "金星与本命月亮成合相，你肯不肯在一个地方待住，先看身上松不松，肩头一放下来，人就愿意多坐一会儿。",
    aspect_key("Venus", "Moon", "sextile"): "金星与本命月亮成六合，你与人坐着的位置会自己挑个省力的摆法，偏要并排坐，说话的声音也跟着放轻。",
    aspect_key("Venus", "Moon", "square"): "金星与本命月亮成刑相，旁人递来的舒服你总要先改一改才肯受，改到最后，那双手不知往哪儿放。",
    aspect_key("Venus", "Moon", "trine"): "金星与本命月亮成拱相，送到你手边的那份心意你接得不迟疑，接住之后做事的劲还在，动作也没跟着慢下来。",
    aspect_key("Venus", "Moon", "opposition"): "金星与本命月亮成冲相，一件想痛快受用，一件想留着不受，你把受用的那半讲到一半就收住，没受的那半在底下一直发烫。",
    # 本命水星（5 条，T8-A 建；本派镜子 = 已落地的 Sun×本命水星 五句与 Moon×本命水星 五句；反向键 Mercury×本命金星 的五句 T6-B 已落地，同属活门；这里改的是谈吐的顺与讨——拣字、把话修圆、绕不绕开冲的地方，不是话与念同不同向；按 §7 本切片不借 `讲/开口/出口` 撑句子）
    aspect_key("Venus", "Mercury", "conjunction"): "金星与本命水星成合相，你先按合不合耳来挑字眼，顺耳的几个自己就排到前头，意思也跟着换了个说法。",
    aspect_key("Venus", "Mercury", "sextile"): "金星与本命水星成六合，你把刺耳那几个字换成不扎人的，换完那句仍在原处站着，谁也没替你删掉什么。",
    aspect_key("Venus", "Mercury", "square"): "金星与本命水星成刑相，你想让话听着体面，思路便绕了个弯，绕过去的那段没进字面，留在你换气的那点上。",
    aspect_key("Venus", "Mercury", "trine"): "金星与本命水星成拱相，你把话修圆的工夫都用在听的一侧，说的人省力，听的人也省力，意思一样没少。",
    aspect_key("Venus", "Mercury", "opposition"): "金星与本命水星成冲相，要说透与要说顺这两下各占你一半，你顺着顺的那半说完，透的那半还差一小截没落地。",
}
