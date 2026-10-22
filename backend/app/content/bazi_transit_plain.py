"""岁运·流日·流时三页共用的整体白话：三句档位散文 + 九句报事实的框架句（批次二 spec §7）。

三页共用一份语料是刻意的：它们回答的是同一个问题（这一段时间的气分档如何），用的是同一把尺
（`engines/bazi_strength.STRONG_CUT` 与 `WEAK_CUT` 两道分界，经 `engines/bazi_transit._tier`），
凭的是同一张规则表（`content/bazi_transit_rules.py`，`bazi_liuri.py` 与 `bazi_liushi.py` 都从
`bazi_transit.py` 引 `transit_ledger`，档位串因此逐字同出一处）。拆成三张表就是三份迟早分家的档位句。

档位名复测：`cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "from app.engines.bazi_transit import _tier; print(_tier(80.0), _tier(50.0), _tier(20.0))"` → `顺 平 滞`。
规则表条数与族数复测：`cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "from app.content.bazi_transit_rules import TRANSIT_RULES; r=list(TRANSIT_RULES.values()); print(len(r), len({x.family for x in r}))"` → `46 9`。

**四条口径写在门面上**：
① 档位名 `顺 / 平 / 滞` 只出现在键表左列与 `_tier` 的返回值里，**永不进句子**（spec §4.2）。
   按**整串零命中**扫，不玩边沿形：「平顺」「平常」这一类词形因此一并出局（spec §7.1 括注的口径）。
   代价写在这里：本文件十二句一个新字都不许用这三个单字，句子改用「高分界那一条线」「低分界」
   「起点那一笔」这些可核对的尺名说话。
② 禁插清单（spec §4.2 的实测那五条，本表逐条核过，不是照抄）：`fired[].label`（岁运规则短名，
   `LEDGER_WORDS` 收着的十七串里有五串就是它的取值，复测见 `tests/plain_wording.py::LEDGER_WORDS`
   与 `tests/content/test_bazi_transit_plain_corpus.py::test_no_frame_slot_value_carries_a_banned_token`）、
   `TransitFired.reading`（它的取值就是 `content/bazi_transit_rules.TRANSIT_RULES` 里那 46 条
   `reading`：46 条里 37 条含 `（《`，即 `FORBIDDEN` 三串之一；`；` 那串不在单条判语里，它出现在
   `engines/bazi_transit.transit_narrative` 把判语连缀成 `narrative` 的那一步。复测（整串统计，
   避开中文字面量进 shell）：`cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "from app.content.bazi_transit_rules import TRANSIT_RULES as T; v=[r.reading for r in T.values()]; print(sum(chr(65371) in x for x in v), sum(chr(65288)+chr(12298) in x for x in v), len(v))"` → `0 37 46`；
   `chr(65371)` 是全角分号、`chr(65288)+chr(12298)` 是全角左括号加书名号）、
   `score.tier`（就是 ① 那三个单字）、`qi_strength`（十二长生名，实测本夹具 2026-06-15 庚申
   那一日的十二格里确有 `死` / `墓` / `绝` 三名，读起来像判词。复测（三个 `chr` 码点依次是
   死 / 墓 / 绝，避开中文字面量进 shell）：`cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "import tests.test_bazi_liushi as L; from datetime import date; r=L.compute_liushi_day(**L._NATAL_KWARGS, solar_date=date(2026,6,15), reference_date=date(2026,6,15)); qi={h.qi_strength for h in r.hours}; print(len(r.hours), len(qi), all(chr(c) in qi for c in (0x6B7B,0x5893,0x7EDD)))"` → `12 12 True`）、`YiJiKind` 的六个组名（全含 `宜` 或 `忌`，
   `advice_hits` 六字表拦着）。
③ 岁运那一节的档位取的是**五年账本的均值再过 `_tier`**（spec §4.3 第二行），流日取月段账本的
   `tier`、流时取日段账本的 `tier`。所以三条档位句的主语一律是「这一段」，不许指定是年、月、
   日还是时；涉及「叠」与「抵」的比较一律按**摊下来**说，因为岁运那一页说的本来就是平均数。
   摊下来的算术根据（一页一本账时也逐字成立）：`value = 起点那一笔 + Σ(正行) − Σ(负行)`，
   起点那一笔恒为 `TRANSIT_BASE = 50.0`（`content/bazi_transit_rules.py`），它就是 `build_ledger`
   放进账本的**第一行**（`schemas/scoring.py` 的 `ScoreFactor` 注着 "factors[0] carries the base
   term"）。**本门面里「正行」只指起点之外那些 delta 为正的行**；含起点那一笔的那个合计一律另写作
   「加的一边」，两个数不共用一个名字。于是 `value >= 65` 蕴含正行摊下来厚过负行，
   `value < 45` 蕴含负行厚过正行加上五分之差——两条都是 `50 + 正行 − 负行 = value` 的变形。
   反例摆在这里，防止有人把 ③ 写成方向错觉：`value < 45` **不**蕴含「抵掉的比加进来的多」——
   按符号求和时起点那一笔算在加的一边，所以加的一边永远不小于抵的一边（实测：本夹具 2026 年那一页
   `value 29.0`，加的一边含起点那一笔共 `58.0`，其中起点之外的正行只有 `8.0`，抵的一边 `29.0`
   ⇒ `29 > 8 + 5` 立，而 `29 > 58 + 5` 破不了。五个数依次是年、分、加的一边、起点之外的正行、
   抵的一边；剥掉 `factors[0]` 就是剥掉起点那一笔，复测：
   `cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "import tests.test_bazi_transit as T; y=min(T._transit().years, key=lambda v: v.score.value); g=y.score.factors; print(y.year, y.score.value, sum(f.delta for f in g if f.delta > 0), sum(f.delta for f in g[1:] if f.delta > 0), sum(-f.delta for f in g if f.delta < 0))"` → `2026 29.0 58.0 8.0 29.0`）。
   于是 `滞` 那一句只许说「负行摊下来厚过起点之外的正行」，不许说「抵掉的压过加进来的」。
   这条主语口径的机械版在
   `tests/content/test_bazi_transit_plain_corpus.py::test_the_three_sentences_never_name_a_calendar_unit`：
   三句都得含「这一段」，且「年 / 月 / 日 / 时 / 岁」五个单字整串零命中（口径同 ① 对档位名的
   单字扫描，「本月」「流年」这类写法因此在射程内）——九句框架各归一页，不受这条管。
④ 九句框架里的数字槽一律由 `num()` 出串，两句极值框架不许在槽外手搭第二个数：
   `{span}` 的正主是 `round(高分 − 低分, 2)`，`{strong}` / `{weak}` 的正主是逐格数 `tier`，
   第二处重算就是第二把尺（spec §4.3）。极值并列一律取排在最前那一格（`max` / `min` 在升序表上
   取第一个），所以句子里那句「并列取最前」是尺本身的话，不是修辞。

边界页清单（每句框架的真值都要在这些页上成立，门测 `tests/content/test_bazi_transit_plain_corpus.py`
按这些形状喂样例句；标「实测」的都在本文件某条注释里给了跑出它的复测命令，标「契约一形」的只由
schema 的字段类型与字段说明承认、不宣称今天存在这样一页，所以它们只进门测的样例句——两句 FOCUS 框架句**只许以条件形**
提到「一条也没有」那一形（「一条也没有也照样是这一格的形状」不宣称存在这样一页），别的写法一律不许）：
单流年页（`start_year == end_year`，实测年表只出一格 ⇒ `{count}` 为 1、`{best_*}` 与 `{worst_*}`
同一年同一分，复测见下面「单流年页的复测」那条）、未起运页（实测
`_transit(start_year=1990, end_year=1992).dayun_covered` 的 `ganzhi` 是 `['']`，`{dayun}` 落
`尚未起运`）、月极值并列页（实测 `focus_year=2026` 的 癸巳 / 甲午 同为 0.0）、整段无一格够得着
高分界的月段页（实测 2026-06 段 `32 格 / 顺 0 / 滞 32`、`{value}` 为 0.0，四个数都出自流日第一节
那条命令）、零命中页（`day_hits` / `hour_hits` 为空数组 ⇒ `{hits}` 为 0：契约一形，本清单不宣称
今天存在这样一页，扫过多少格也不在这里报——那类格数没有能跑出它的命令）、十二格同分页（⇒ `{top_zhi}` 即 `{low_zhi}`、
`{span}` 为 0：契约一形、同上不作存在宣称；时辰表每天恒出 12 格，扫几天都只得到 12 的整倍数，格数本身
不是判据）。
未起运页的复测：`cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "import tests.test_bazi_transit as T; print([s.ganzhi for s in T._transit(start_year=1990, end_year=1992).dayun_covered])"` → `['']`。
单流年页的复测：`cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "import tests.test_bazi_transit as T; y=T._transit(start_year=2029, end_year=2029).years; print(len(y), y[0].year, y[0].score.value)"` → `1 2029 74.0`（年表就一格，`max` 与 `min` 打在单格年表上必然是同一年同一个分）。
"""

BAZI_TRANSIT_PLAIN_SOURCE = (
    "本系统自撰白话 · 档位分界逐字取 engines/bazi_strength 的 STRONG_CUT 与 WEAK_CUT，"
    "句子不引古籍 · 三页（岁运 / 流日 / 流时）共用本表"
)

#: 岁运三档 → 键。左列逐字取 `engines/bazi_transit._tier` 的三个返回值（档位名复测见模块头注 ①）。
#: 右列是本表唯一的键式；它们是账本词，不进散文（spec §4.2）。
BAZI_TRANSIT_TONE_KEYS: dict[str, str] = {
    "顺": "bazi_transit.tone.shun",
    "平": "bazi_transit.tone.ping",
    "滞": "bazi_transit.tone.zhi",
}

#: 三页的节标题：序即页面上的阅读序，条件节排最后（装配、页级测与前端挂载测共用这一份名单，
#: 别处不再写第二遍）。每页三个标题恒长 3，第三节只在给了 focus 时才装配。
BAZI_TRANSIT_TITLES: dict[str, tuple[str, ...]] = {
    "transit": ("区间总览", "岁运主线", "流年十二个月"),
    "liuri": ("本月总览", "逐日分布", "聚焦之日"),
    "liushi": ("本日总览", "十二时辰", "聚焦时辰"),
}

BAZI_TRANSIT_READINGS: dict[str, str] = {
    # 键逐字取 `BAZI_TRANSIT_TONE_KEYS.values()`；三句的主语一律是「这一段」（口径 ③），
    # 起止由框架句报。数字不进这三句，两道分界只用「高分界那一条线」「低分界那一条线」点名。
    "bazi_transit.tone.shun": (
        "这一段摊到尺上够得着高分界那一条线，起点之外叠上来的那几笔，摊下来厚过相互抵掉的那几笔，"
        "抵掉的那些就算也在账上也没能把它拽回线内，你读到的是这一段里往一处加的力量占了先。"
    ),
    "bazi_transit.tone.ping": (
        "这一段的分站在两道线之间，既没顶到高分界那一条线，也没跌破低分界那一条线，"
        "起点那一笔自己就落在这两道线中间，你读到的是这一段眼下摊下来的净额没被哪一边推出线外。"
    ),
    "bazi_transit.tone.zhi": (
        "这一段自己落在低分界那一条线之下，账上抵掉的那几笔确实在，而且摊下来厚过起点之外"
        "叠上来的那几笔，你读到的是这段账的净额被压到了起点那一笔以下，往后的事不由这张表替你定。"
    ),
}

#: 九句框架：三页各三句。槽位清单见 `tests/content/test_bazi_transit_plain_corpus.py`
#: 里那份与样例句键集逐字对账的测——写错一个槽名，页面上是 KeyError，测里是绿。
#: 岁运第一节：区间总览。`{strong}` 数的是 `value >= STRONG_CUT` 的年、`{weak}` 数的是
#: `value < WEAK_CUT` 的年，两道线之间的那些两个数都不算，所以句子必须把「其余年份」说出来，
#: 否则读者会把 `{strong}` 与 `{weak}` 相加当 `{count}`（实测缺省页 5 = 1 + 1 + 3）。
#: 单流年页（`start_year == end_year`）落在这里，`{count}` 为 1、两个数可同为 0。
BAZI_TRANSIT_RANGE_FRAME = (
    "{start} 到 {end} 这段年表一共 {count} 格，够得着 {strong_cut} 那道线的有 {strong} 格，"
    "落不到 {weak_cut} 那道线的有 {weak} 格，两道线之间的年份这两个数都不算，"
    "你看到的是这段区间的分怎么散开，不是其中某一年单独的说法。"
)

#: 岁运第二节：`{dayun}` 的正主是 `"、".join(非空干支) or "尚未起运"`，所以这一栏有两种长相；
#: `{best_*}` / `{worst_*}` 是 `max` / `min` 打在升序年表上，并列取最早那一年——单流年页上
#: 两头是同一年同一个分，句子里那句「排在最前的那一年」因此不会假。不许写「最好 / 最差」。
BAZI_TRANSIT_THREAD_FRAME = (
    "这一段的大运那一栏写作 {dayun}，年表里分最高的那一年是 {best_year} 年的 {best_ganzhi}，"
    "{best_value} 分，分最低的那一年是 {worst_year} 年的 {worst_ganzhi}，{worst_value} 分，"
    "两头并列时都按排在最前的那一年报，你读到的是这段岁的最高与最低各自落在哪一年上。"
)

#: 岁运第三节：只在给了 `focus_year` 时装配。复测（并列页真实存在）：
#: `cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "import tests.test_bazi_transit as T; r=T._transit(start_year=2026, end_year=2030, focus_year=2026); m=next(y.months for y in r.years if y.months); print([(x.index, x.ganzhi, x.score.value) for x in m])"`
#: → 癸巳（index 3）与 甲午（index 4）同为 0.0，`min` 取排在最前的癸巳。节气名一律不进这句。
BAZI_TRANSIT_MONTH_FRAME = (
    "聚焦到 {year} 那一年排出的月表，分最高的一格是 {top_ganzhi}，{top_value} 分，"
    "分最低的一格是 {low_ganzhi}，{low_value} 分，并列时取月表里排在最前那一格，"
    "你看的是同一年内月和月之间的高低。"
)

#: 流日第一节：`{value}` 是月段账本自己的分（页面月卡同一个数，不重算均值），
#: `{strong}` / `{weak}` 数的是这一月各日的 `tier`。整段无高分格的那一页真实存在：
#: 复测 `cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "import tests.test_bazi_liuri as L; from datetime import date; from tests.plain_wording import TIER_WORDS as W; r=L.compute_liuri_matrix(**L._NATAL_KWARGS, anchor_date=date(2026,6,15), reference_date=date(2026,6,15)); print(len(r.days), sum(1 for d in r.days if d.tier == W[0]), sum(1 for d in r.days if d.tier == W[2]), r.month_score.value)"`
#: → `32 0 32 0.0`（四个数依次是段长、够得着高分界的格数、落不到低分界的格数、`{value}` 的正主；
#: 档位名走 `TIER_WORDS` 的下标而不是字面量，为的是这条命令能原样贴进 shell）。
#: 起止两串只从槽里来，句子不做第二个日期推算。
BAZI_LIURI_MONTH_FRAME = (
    "{ganzhi} 这一段从 {start_solar} 管到 {end_solar}，月段自己的分记作 {value}，"
    "摊进这段日子时够得着高分界那一条线的有 {strong} 格、落不到低分界那一条线的有 {weak} 格，"
    "其余的日子这两个数都不算，你看到的是这一月的账压在日上怎么散开。"
)

#: 流日第二节：`{high}` / `{low}` 是日柱干支串。「干支在一个月段里不重格」是一条结构事实，
#: 不需要扫描背书：一年只排十二个月柱，段界就是相邻两个「节」的交界（`engines/bazi_liuri.py`
#: 的节气月段），一段三十天上下，恒在日柱 60 甲子那个循环的长度之下 ⇒ 同一段里日柱不可能重格，
#: 「哪一格」因此指得准。留下一个可复现的锚点：本夹具 `anchor_date=2026-06-15` 那一段的段长是 32
#: （复测即流日第一节那条命令的第一个数 `len(r.days)` → `32`）。
#: 整段同分那一形里 `max` 与 `min` 都落回排在最前的那一格，句子已经先说了并列取最前。
BAZI_LIURI_DAYS_FRAME = (
    "这一月摊开成 {count} 个日子，日分最高的是 {high} 那一格，{high_value} 分，"
    "最低的是 {low} 那一格，{low_value} 分，并列时取排在最前的那一天，"
    "你读到的是这一月的日头高低各落在哪一格上。"
)

#: 流日第三节：`{hits}` 是 `ri.` 段命中行数，不是判语；命中行的 `label` 与 `reading` 都不进槽
#: （禁插清单，口径 ②）。`day_hits` 为空数组那一形由 `TransitDayCell.day_hits` 的字段说明承认
#: （「一条未中为 []」）——它的凭据是字段类型与字段说明，不是某次扫描的格数，所以它只进门测样例句；
#: 句子那一侧只许以条件形提到它，口径见门面边界清单的前言。
BAZI_LIURI_FOCUS_FRAME = (
    "聚焦的 {date} 是 {ganzhi} 这一格，日分记到 {value}，落在它身上的流日规则命中 {hits} 条，"
    "条数是账本行数不是判语，一条也没有也照样是这一格的形状，你读到的是这一天在表里占的位置。"
)

#: 流时第一节：只报日段那一段的账，十二格各自的分归第二节那句。
#: `{value}` 可以为 0.0（实测 2026-06-15 那一天的日段就是 0.0，日柱 庚申；它有自己的复测，
#: 与流日那条各数各的账，别混为一谈：
#: `cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "import tests.test_bazi_liushi as L; from datetime import date; r=L.compute_liushi_day(**L._NATAL_KWARGS, solar_date=date(2026,6,15), reference_date=date(2026,6,15)); print(r.day_ganzhi, r.day_score.value)"` → `庚申 0.0`）。
BAZI_LIUSHI_DAY_FRAME = (
    "{date} 这一天的日柱是 {ganzhi}，日段自己的分记到 {value}，"
    "这一句只报当日那一段的账，不报它下面每一格各自的分，"
    "你读到的是时辰那张表要往哪一格上看。"
)

#: 流时第二节：`{span}` 的正主是 `round(高分 − 低分, 2)`，句子不许在槽外再算一次差
#: （口径 ④）。十二格同分那一形由 `TransitHourCell.hour_hits` 的字段说明承认
#: （「时段一条未中为 []，此时本格分值等于日头分」⇒ 十二格同分、`{span}` 落 0、
#: `max` 与 `min` 都取时辰序首格）；这一形同样只进样例句——时辰表每天恒出十二格
#: （`engines/bazi_liushi.py` 的 `HOUR_ZHI` 十二支），扫几天都只得到 12 的整倍数，
#: 所以这里不报「扫过几日共几格」那种没有命令能跑出的数。
#: 钟面只报 `{*_clock}` 起点：23:00 那一格的起点钟面属于前一日，句子不提日界。
BAZI_LIUSHI_HOURS_FRAME = (
    "时辰那张表里分最高的一格是 {top_zhi} 时，钟面 {top_clock} 起，{top_value} 分，"
    "分最低的一格是 {low_zhi} 时，钟面 {low_clock} 起，{low_value} 分，"
    "这一栏与那一栏之差记作 {span}，并列时都取排在最前那一格，"
    "你读到的是这一天里分最高与分最低的两栏各占哪个时辰。"
)

#: 流时第三节：同流日第三节，`{hits}` 是 `shi.` 段行数；时支逐字传，不改写成「几点到几点」。
BAZI_LIUSHI_FOCUS_FRAME = (
    "聚焦的时辰是 {zhi} 时，钟面 {clock} 起，这一格的分记到 {value}，"
    "落在它身上的流时规则命中 {hits} 条，条数是账本行数不是判语，"
    "一条也没有也照样是这一格的形状，你读到的是这一格在时辰表上占的位置。"
)

# ---------------------------------------------------------------- 结论卡片（verdict-card spec §4）
#: 页级结论卡与上面三条档位句是两把尺：逐年/逐日/逐格层仍用 `_tier` 的顺/平/滞，页级
#: 结论一律把锚点分交给 `engines/verdict.grade_for` 换五档词（大吉/吉/平/小凶/凶）。框架句、
#: 取向词条与建议词条都住本表，引擎只填槽位，不现编中文。这一节不进上面九句框架的门测
#: （档位词 吉/凶 由 `{grade}` 槽在运行时带入，与九句的禁插清单口径不同），键集由各系统
#: 装配测自守。

#: 五档收束取向，键 = `engines/verdict.GRADE_BANDS` 的五个档位词（与 `bazi_plain.VERDICT_OUTLOOK`
#: 同键，缺一档即 KeyError）。槽位词条不成句、不带「。」，自身不含建议词与档位字。
BAZI_TRANSIT_VERDICT_OUTLOOK: dict[str, str] = {
    "大吉": "势头正旺，想推的事放手去做",
    "吉": "向上的一面占优，值得把握",
    "平": "好坏大致相抵，稳中求进",
    "小凶": "吃力的一面更多，先补薄弱处",
    "凶": "先把基本盘守住，别急着出手",
}

#: 三档（顺/平/滞）一句口语建议，键 = `bazi_transit._tier` 的三个返回值；建议句 `{tier_advice}`
#: 槽按最弱那一格的档位取词。槽位词条不成句、不带「。」。
BAZI_TRANSIT_TIER_ADVICE: dict[str, str] = {
    "顺": "这一处势头正好，有想推进的事落在它身上更省力",
    "平": "这一处不上不下，按部就班走，别在它身上硬求突破",
    "滞": "这一处吃力的账更多，先把手头稳住，别在它身上铺新摊子",
}

#: 岁运页总论框架：`{grade}` 五档词，`{shun}/{ping}/{zhi}` 是逐年账本的三档计数，
#: `{outlook}` 取 `BAZI_TRANSIT_VERDICT_OUTLOOK[grade]`；计数由引擎算术给出，本表不写死数字。
BAZI_TRANSIT_RANGE_VERDICT_FRAME = (
    "你这一段年表整体属{grade}：{shun} 年够得着高分界，{ping} 年落在两道线之间，"
    "{zhi} 年落不到低分界，{outlook}。"
)

#: 岁运建议句框架：指向区间内分最低的那一年（`min` 打在升序年表上，并列取最早）。
BAZI_TRANSIT_VERDICT_ADVICE_FRAME = (
    "综合建议：你这一段里分最低的是 {year} 年（{ganzhi}，{value} 分），{tier_advice}。"
)

#: 流日页总论框架：`{anchor_fact}` 是引擎按「有无聚焦日」二选一装配好的锚点事实短语。
BAZI_LIURI_VERDICT_FRAME = "你看的这一段整体属{grade}：{anchor_fact}，{outlook}。"

#: 流日锚点事实两形：给了聚焦日用 FOCUS（聚焦日自己的账），没给用 MONTH（月段自己的账）。
BAZI_LIURI_ANCHOR_MONTH = "月段 {ganzhi} 自己记到 {value} 分"
BAZI_LIURI_ANCHOR_FOCUS = "聚焦的 {date}（{ganzhi}）记到 {value} 分"

#: 流日建议句框架：指向月内分最低的那一天（`min` 打在日表自然序上，并列取最早）。
BAZI_LIURI_VERDICT_ADVICE_FRAME = (
    "综合建议：你这一月里分最低的是 {date}（{ganzhi}，{value} 分），{tier_advice}。"
)

#: 流时页总论框架：`{anchor_fact}` 按「有无聚焦时辰」二选一，口径同流日。
BAZI_LIUSHI_VERDICT_FRAME = "你看的这一天整体属{grade}：{anchor_fact}，{outlook}。"

BAZI_LIUSHI_ANCHOR_DAY = "日段 {ganzhi} 自己记到 {value} 分"
BAZI_LIUSHI_ANCHOR_FOCUS = "聚焦的 {zhi} 时（钟面 {clock} 起）记到 {value} 分"

#: 流时建议句框架：指向十二格里分最低的那一格（并列取时辰序首格）。
BAZI_LIUSHI_VERDICT_ADVICE_FRAME = (
    "综合建议：你这一天里分最低的是 {zhi} 时（钟面 {clock} 起，{value} 分），{tier_advice}。"
)
