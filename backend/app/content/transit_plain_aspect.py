"""行运三层：移动点与本命点之间 600 条相位的白话判语表（T2-T21 按移动星二十批填入）。

键由 `transit_plain.aspect_key` 拼，所以本文件只有句子，没有键式；本批 T2 起填移动星 Sun
的前六个本命点 30 条，其余 570 条归 T3-T21。**已落地的行一字不改**（改一行就等于改动别批
已评审过的内容，那要走裁定）。

一张表同时被三层读：同一个键会在同一份响应里被印到行运、次限、太阳弧三个小节，所以句子
**不许含层名**（`行运/次限/太阳弧/推运` 四字由 G37 判红），也不许含日历词与频率副词——
「今天」「这周」在次限层是假话（次限一格走一年），层名与日期都由开篇句给。日历词十四串
从整改轮 1（A2）起**有机检**：`CALENDAR_WORDS` 与层名同住一条门
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
自己也 import 聚合面模块，包初始化先把环走完，所以直接 import 分表是绿的，见本报告）。
这段理由在 `transit_plain.py` 的 import 行上方另有一份（Plan F 的同一处也是两份：
`content/western_plain.py:74-78` 与 `content/western_plain_placement.py:7-13`）。
复测：`cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "from app.content import transit_plain, transit_plain_aspect; print(len(transit_plain.TRANSIT_READINGS))"` → 本批 30。
"""

from app.content.transit_plain import aspect_key

#: 键序 = 本命点序（`_natal_points`：十星按 `PLANETS` 序，ASC/MC 由 T5-T21 的批接在后面）×
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
    aspect_key("Sun", "Mercury", "trine"): "太阳与本命水星成拱相，心里的事与说出来的话之间没有门槛，你随口一讲就把这盘棋摆给外人看，摆出来也不显摆。",
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
}
