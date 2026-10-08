"""行运三层白话表的本地门（Plan G spec §7、§10；T2 建骨架与九道门，T3-T22 逐批追加语料）。

为什么这张测在批次期必须自己跑全套而不靠工厂：`TRANSIT` 从 T2 就定义在 `engines/plain_corpora.py`
里，但**登记行归 T23**（全局约束「批次期定义而不登记」：`universe()` 是全量 648 算的，语料是一批批
建的，提前登记会让工厂的 `set(entries) == universe()` 从 T2 红到 T22）。那二十一批里工厂的参数化
用例看不到这张表，所以「登记表里没有这一家」期间的所有口径由本文件逐条守着。

为什么本计划要在 Plan F 的七道之外再加两道（G37 层名、G38 同对尾段互异 + 反向不复制）：Plan E/F
的偏差表 9/12/13/14/22 行记着同一类失败——**计划与实施者写的散文里有假事实，而关键字筛看不见**。
行运这张表最容易说的四类谎话恰好是：把方向写反（`本命太阳与水星`）、把层名写进共享条目（同一句
在次限小节就是假话）、镜像复制（`X→本命Y` 抄给 `Y→本命X`）、主张键上没有的星座属性。四类全部
做成门，不留「由评审员人核」的口子（那一句在 Plan E 里连续五批写出了假事实）。

措辞四口径（≥40 字 / 恰一「。」 / 含你 / 禁字）与戊组两组增量禁串（G31 时态十七串、G36 决策名词
八串）住在 `tests/plain_wording.py`，本文件只调不改（口径单一正主，AGENTS.md §1）。G37/G38 只服务
这一张表，所以住在这里而不进 `plain_wording.py`（那是甲–丁戊共用层，塞进只对一张表成立的规矩就是
让别的系统吃上与自己无关的闸）。

复测：`cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m pytest tests/content/test_transit_plain_corpus.py -o addopts=""`。
用例数 = **7×已落地条数 + 9**（每条键七道：共享契约、命名对账、结构事实、禁数字、越界具名、建议词、
层名与日历词——两族同住第七道，整改轮 1 A2 折进门内而不开新 parametrize；另加九条单例）。
T2 落地 30 条 ⇒ 219；T22 收尾 648 条 ⇒ 4545；T23 登记后 ⇒ 4549（那四条
是本文件 `test_the_corpus_is_not_registered_while_batches_land` 换成登记钉之后新增的工厂侧用例，
见该条 docstring）。
"""

import re

import pytest

from app.content import transit_plain, transit_plain_aspect
from app.engines.plain_corpora import PLAIN_CORPORA, TRANSIT
from app.engines.western import PLANETS, SIGN_ELEMENT, SIGN_MODALITY, SIGNS, SIGNS_ZH
from tests.plain_wording import (
    PREDICTION_GATED_SYSTEMS,
    advice_hits,
    frame_violations,
    wording_violations,
)

PLANET_NAMES = [name for name, *_ in PLANETS]
PLANET_ZH = [zh for _name, _glyph, zh, _swe in PLANETS]

#: 两轴的中文名。字面与 `engines/transit.py:62` 的 `_AXIS_ZH` 同值（复测：`cd backend && grep -n "_AXIS_ZH = " app/engines/transit.py`）。
#: 对账钉住在本文件 `test_the_key_builders_are_the_only_key_source`（整改轮 1 B1 补上）：测试为对账
#: 而 import 引擎私有量与生产模块的依赖方向（AGENTS §1）无关，`plain_corpora.py` 因此仍不引它。
#: 整改前这里写的「一致性由 `tests/golden/test_transit_golden.py` 已有的轴对账钉守住」是假话——该文件
#: 今天没有任何一条轴测（复测：`cd backend && grep -nEi "axis|上升|天顶" tests/golden/test_transit_golden.py` → 空输出）。
AXIS_ZH = {"ASC": "上升", "MC": "天顶"}

#: 行运一侧的「点名」全集 = 十星 + 两轴 = `_natal_points` 的十二枚（`app/engines/transit.py:108-114`：
#: 十个行星点位再并上 `axis.name in _AXIS_ZH` 的两枚）。命名对账门吃这张表，移动侧与本命侧同表。
POINT_ZH = [*PLANET_ZH, *AXIS_ZH.values()]

#: 五个相位词的字面 = 前端已经印在 `AspectLegend` 上的那五个词（`frontend/src/lib/astro.ts:39-43`）。
#: 不另立一套：白话说「四分相」而图例写「刑相」，用户读到的是两个东西。
ASPECT_ZH = {
    "conjunction": "合相",
    "sextile": "六合",
    "square": "刑相",
    "trine": "拱相",
    "opposition": "冲相",
}

ELEMENT_ZH = {"fire": "火象", "earth": "土象", "air": "风象", "water": "水象"}
#: 形态词必须写三字形（`基本宫/固定宫/变动宫`）：裸写「基本」「固定」「变动」是本族最常见的
#: 假红源，因为门只认这张表里的三个字串，而「变动」在描述张力时太容易顺手写出来。
MODALITY_ZH = {"cardinal": "基本宫", "fixed": "固定宫", "mutable": "变动宫"}
SIGN_TO_ELEMENT = dict(zip(SIGNS, SIGN_ELEMENT))
SIGN_TO_MODALITY = dict(zip(SIGNS, SIGN_MODALITY))

#: 页面没印的轴、点、相位词与状态名。`逆行/退行` 是 spec 偏差 5 的代价补偿：移动层的逆行状态
#: 不在 648 的键式里（页面 `MovingPointTable` 印了它），白话不讲也不点名，于是读者不会
#: 遇到「表格印了而白话漏了」的裂缝（与 Plan F 偏差 17 处理「宫头」同法）。
#: `三合/对冲` 是另派的相位词，页面图例只有五个词（`src/lib/astro.ts:39-43`）；
#: `中天` 是 `TransitPage.tsx:268` 那处待统一的说法，语料一律采 `AXIS_ZH` 的「天顶」。
#: `计都/罗睺` 是吠陀交点名，防止把 H 的词汇提前写进 G。
#: 复测条数：`cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "import ast,pathlib; m=ast.parse(pathlib.Path('tests/content/test_transit_plain_corpus.py').read_text(encoding='utf-8')); print([len(n.value.elts) for n in m.body if isinstance(n,ast.Assign) and getattr(n.targets[0],'id','')=='OUT_OF_SCOPE_WORDS'])"` → [15]。
OUT_OF_SCOPE_WORDS = (
    "南交", "下降", "天底", "小行星", "真交点", "福点", "宿命点", "宫头",
    "逆行", "退行", "三合", "对冲", "计都", "罗睺", "中天",
)

CN_HOUSE = {
    "一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6,
    "七": 7, "八": 8, "九": 9, "十": 10, "十一": 11, "十二": 12,
}
#: 反查表给 T22 的月亮落宫族（那批要按键上的宫号往句子里写「第九宫」，正查容易写错字）。
REV_CN_HOUSE = {value: name for name, value in CN_HOUSE.items()}
#: 正则含两位，所以「第十一宫」不会被切读成「第一宫」（这条若不成立，宫号对账门会误放）。
HOUSE_RE = re.compile(r"第([一二三四五六七八九十]{1,2})宫")

#: 标题只服务 `test_sections_and_openers_cover_the_declared_shape` 的标题门：`<h3>` 里的一格
#: 名字不能带分句符号与括号，`、` 禁掉是为了拦住「次限月亮、次限四轴」这种把两格并成一格
#: 写。不复用 `FORBIDDEN`，因为标题合法地含「与」，也不管戊组禁串（标题不是判语）。
_FORBIDDEN_FOR_TITLES = ("；", "（《", "』", "（", "）", "、")

#: 一张表三层共用，所以层名是**开篇句的词**而不是条目的词（本文头注第一段与 spec 全局约束第二条）。
#: 这四个串出现在任何一条条目里即红（G37）。第四个 `推运` 也禁：它是次限层在页面上的用户可见
#: 总称（`frontend/src/pages/TransitPage.tsx:252`「次限推运要点」、`:256`「推运太阴」、`:268`
#: 「推运上升/中天」——2026-10-07 按内容复测，派单引的 `schemas/transit.py:96` 那句 field description
#: 实为英文且不含「推运」，见本报告），条目写「推运月亮」就把次限层的名字偷带进了共享句。
LAYER_WORDS = ("行运", "次限", "太阳弧", "推运")

#: 日历词十四串（整改轮 1 A2 进门，与层名同住第七道 `test_no_layer_word_and_no_calendar_word_inside_an_entry`，
#: 不开新 parametrize——用例数 `7×条数+9` 是 T3-T22 二十批的既定数字）。一张表被三层读，次限一格走一年、
#: 太阳弧按弧长推，「今天」「这周」对任何非当日的目标日都是假话（页面允许选日期，`TransitPage.tsx` 的
#: maxYear=now+30 与「目标日 {chart.target_date}」）；日期只许住在开篇句里，且开篇句同样不吃这十四串（B3）。
#: **不禁** `这段时间`、`这段日子`、`这一格`——对任意目标日区间为真（计划口径裁定 1 明写合法）；
#: `此刻` 也不禁（指快照那一刻，对任意目标日成立，成文理由见 task-2 报告整改轮 §B3）。
#: 复测条数：`cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "import ast,pathlib; m=ast.parse(pathlib.Path('tests/content/test_transit_plain_corpus.py').read_text(encoding='utf-8')); print([len(n.value.elts) for n in m.body if isinstance(n,ast.Assign) and getattr(n.targets[0],'id','')=='CALENDAR_WORDS'])"` → [14]。
CALENDAR_WORDS = (
    "今天", "明天", "昨天", "今晚", "这周", "本周", "下周",
    "这个月", "本月", "这几天", "一整天", "天天", "时辰", "钟点",
)

#: 反向义务：每条开篇句必须含**自己那一层**的层名词。这里的值是三个层名（不含 `推运`，它是
#: 次限层的用户可见总称，合法地出现在 `progressed_*` 两句的「推运盘」里），门判两半：自己的
#: 那个必须在，另外两个不许在。复测条数（`grep -c` 量的是提到这个词的行数，不是表条数）：`cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "import ast,pathlib; m=ast.parse(pathlib.Path('tests/content/test_transit_plain_corpus.py').read_text(encoding='utf-8')); print([len(n.value.keys) for n in m.body if isinstance(n,ast.Assign) and getattr(n.targets[0],'id','')=='LAYER_IN_OPENER'])"` → [8]。
LAYER_IN_OPENER = {
    "transit_aspect": "行运",
    "transit_aspect_none": "行运",
    "progressed_aspect": "次限",
    "progressed_aspect_none": "次限",
    "directed_aspect": "太阳弧",
    "directed_aspect_none": "太阳弧",
    "progressed_moon": "次限",
    "progressed_axis": "次限",
}

#: 批次花名册：各族**已建**条数。T3-T21 每批只把 `aspect` 那一行的数字改大 30，T22 改后面三行
#: （12/12/24），一条也不许多。这道门的作用是把「少建」和「多建」在同一天分开报：工厂那条
#: `set == universe` 只有 T23 之后才存在，而多建出来的键会漂到引擎永远不触发的位置上
#: （spec §5.3），没人校对得到。
ROSTER_TARGETS: dict[str, int] = {
    "aspect": 120,
    "progressed_moon_sign": 0,
    "progressed_moon_house": 0,
    "progressed_axis": 0,
}


def built_keys() -> list[str]:
    return sorted(TRANSIT.entries)


def key_parts(key: str) -> tuple[str, dict[str, object]]:
    """键 → (族名, 参数)。族的次序与 spec §5.3 的键式表逐字同序。"""
    bits = key[len("transit.") :].split(".")
    family = bits[0]
    if family == "aspect":
        return family, {"moving": bits[1], "natal": bits[2], "type": bits[3]}
    if family == "progressed_moon_sign":
        return family, {"sign": bits[1]}
    if family == "progressed_moon_house":
        return family, {"house": int(bits[1])}
    if family == "progressed_axis":
        return family, {"axis": bits[1], "sign": bits[2]}
    raise AssertionError(f"未知族：{key}")


def point_zh(name: str) -> str:
    """键上的英文点名 → 中文点名。移动侧与本命侧同用这张表（十星 + ASC/MC）。"""
    if name in PLANET_NAMES:
        return PLANET_ZH[PLANET_NAMES.index(name)]
    return AXIS_ZH[name]


@pytest.mark.parametrize("key", built_keys())
def test_every_plain_text_meets_the_shared_factory_contract(key) -> None:
    """≥40 字 / 恰一「。」 / 含「你」/ 四串 `FORBIDDEN` / 戊组两组禁串（G31、G36）。

    工厂的 `test_every_entry_meets_the_wording_contract[transit:*]` 在 T23 登记后会对同一个对象
    跑同一条谓词；这份重复是**刻意留的**：登记归 T23，而本条从 T2 起逐条跑，所以它是「登记表里没有
    这一家时仍然存在的独立验证」（Plan E T13 评审实测：un-register 只让工厂那一侧的用例静默消失，
    不红）。`TRANSIT.system == "transit"` 已在 `PREDICTION_GATED_SYSTEMS` 里，所以 G31 的十七串与
    G36 的八串今天就在生效——「本家在名单里」这一件本身由
    `test_the_corpus_is_not_registered_while_batches_land` 钉。
    """
    assert wording_violations(TRANSIT, key) == []


@pytest.mark.parametrize("key", built_keys())
def test_the_naming_reconciliation_holds(key) -> None:
    """命名对账（本文件的主门）：键带的名字必须齐、键没有的名字一个不许有、方向不许写反。

    这一条同时管五件事，因为它们都是「键 vs 句子」的同一类谎言：
    ①点名（十星 + 两轴共十二枚）出现与否必须等于键所载——移动侧与本命侧**同表**，这是行运版
      与本命版的第一个不同：`_natal_points` 的十二枚都能做本命点（`app/engines/transit.py:108-114`）；
    ②星座中文名（十二个）：相位族与月亮落宫族键上没有，出现即红；
    ③宫号（`HOUSE_RE` 抓到的每一个）必须恰好是键上那一个——只有 `progressed_moon_house` 键上有；
    ④相位词恰好只等于键上那一个（五个词互相不是子串，所以能逐词判）；
    ⑤**方向诚实件**（本计划独有，替代 Plan F 的 G32 行星序钉：行运的相位是**有方向的**，
      移动点压向本命点，而本命盘那一家是两颗星互成，没有「谁压谁」可写反）。
      本命侧必须以 `本命{natal_zh}` 的带前缀形状出现，移动侧必须以**不带**前缀的形状至少出现一次，
      且整条至少含一处「本命」——少了前缀就是把两边并成一句「太阳与水星」，多了前缀（全文只有
      `本命太阳`）就是把方向写反了。
    """
    family, arg = key_parts(key)
    text = TRANSIT.entries[key]
    problems: list[str] = []

    named_points: set[str] = set()
    if family == "aspect":
        named_points = {point_zh(str(arg["moving"])), point_zh(str(arg["natal"]))}
    for zh in POINT_ZH:
        if (zh in text) != (zh in named_points):
            problems.append(f"点名「{zh}」在文中={zh in text}，键上={zh in named_points}")

    if family == "aspect":
        words = [word for word in ASPECT_ZH.values() if word in text]
        if words != [ASPECT_ZH[arg["type"]]]:
            problems.append(f"相位词应当只有「{ASPECT_ZH[arg['type']]}」，实为 {words}")
        moving_zh, natal_zh = point_zh(str(arg["moving"])), point_zh(str(arg["natal"]))
        if f"本命{natal_zh}" not in text:
            problems.append(f"本命点名缺「本命」前缀：{natal_zh}")
        if text.replace(f"本命{natal_zh}", "").count(moving_zh) < 1:
            problems.append(f"移动点名「{moving_zh}」没有一次不带「本命」前缀的出现（方向被写反）")
        if "本命" not in text:
            problems.append("相位条目不含「本命」二字（整句没交代压向的是本命盘）")
    elif family in ("progressed_moon_sign", "progressed_moon_house"):
        # 月亮两族讲的就是月亮：通用「点名必须恰好等于键上那几个」会把它自己的主语判成越界
        # 点名（计划阶段门验的第三轮自撞，见 Plan G 计划正文），所以这一族改成「主语必须是
        # 『月亮』+ 只禁别的点名」。
        if "月亮" not in text:
            problems.append("次限月亮条目没写主语「月亮」")
        for zh in POINT_ZH:
            if zh != "月亮" and zh in text:
                problems.append(f"月亮条目里出现别的点名「{zh}」")
    else:
        axis_zh = point_zh(str(arg["axis"]))
        if axis_zh not in text:
            problems.append(f"没写自己的轴名「{axis_zh}」")
        for zh in POINT_ZH:
            if zh != axis_zh and zh in text:
                problems.append(f"四轴条目里出现别的点名「{zh}」")

    named_signs = {arg["sign"]} if "sign" in arg else set()
    for index, zh in enumerate(SIGNS_ZH):
        if (zh in text) != (SIGNS[index] in named_signs):
            problems.append(f"星座「{zh}」在文中={zh in text}，键上={SIGNS[index] in named_signs}")

    houses_said = [CN_HOUSE[matched] for matched in HOUSE_RE.findall(text)]
    house_on_key = arg.get("house")
    if house_on_key is None:
        if houses_said:
            problems.append(f"键里没有宫位，文中却写了宫号 {houses_said}")
    else:
        if houses_said != [house_on_key]:
            problems.append(f"键是第{house_on_key}宫，文中写 {houses_said}")
    assert not problems, f"{key}: {problems}"


@pytest.mark.parametrize("key", built_keys())
def test_the_structural_fact_matches_the_table(key) -> None:
    """G34：元素/形态的说法必须等于 `SIGN_ELEMENT`/`SIGN_MODALITY`；键上没有星座就不许主张。

    自撰表最容易漂的地方正是「顺手补一句星座属性」，而这句话的真假不需要读古籍，查两张
    平行数组就够（`app/engines/western.py:61-62`），所以没有放过它的理由。行运这一家的形状
    差别是：**只有 `progressed_moon_sign` 与 `progressed_axis` 两族的键上有星座**，相位族与
    月亮落宫族的键上没有——那两族主张任何元素/形态就是替页面说了它没算过的话。
    """
    family, arg = key_parts(key)
    text = TRANSIT.entries[key]
    said_elements = [word for word in ELEMENT_ZH.values() if word in text]
    said_modalities = [word for word in MODALITY_ZH.values() if word in text]
    problems: list[str] = []
    if len(said_elements) > 1:
        problems.append(f"一句里出现两个元素词 {said_elements}")
    if len(said_modalities) > 1:
        problems.append(f"一句里出现两个形态词 {said_modalities}")
    if "sign" in arg:
        sign = str(arg["sign"])
        want_element = ELEMENT_ZH[SIGN_TO_ELEMENT[sign]]
        want_modality = MODALITY_ZH[SIGN_TO_MODALITY[sign]]
        if said_elements and said_elements != [want_element]:
            problems.append(f"{sign} 的元素是「{want_element}」，文中说 {said_elements}")
        if said_modalities and said_modalities != [want_modality]:
            problems.append(f"{sign} 的形态是「{want_modality}」，文中说 {said_modalities}")
    elif said_elements or said_modalities:
        problems.append("键上没有星座，不许主张元素/形态")
    assert not problems, f"{key}: {problems}"


@pytest.mark.parametrize("key", built_keys())
def test_no_arabic_digits(key) -> None:
    """G35：宫号必须中文；度数、日期、编号一律不进白话。

    行运页比本命页更容易写出这一类谎，因为三层每格都带度数与日期（`degree_text`、`target_date`、
    `arc_text`），而 648 条里没有一条的键带度数——把「7°」或「10月4日」写进句子就是把一个键上
    没有的事实说成有，还会让同一句在三层里只有一层为真。报错串形状 `['含阿拉伯数字']` 由整改轮 1
    B4 钉死（与计划「计划阶段的门验」第 6 类的引用逐字一致）。
    """
    violations = ['含阿拉伯数字'] if re.search(r"\d", TRANSIT.entries[key]) else []
    assert not violations, f"条目 {key}: {violations}"


@pytest.mark.parametrize("key", built_keys())
def test_out_of_scope_names_are_absent(key) -> None:
    """G33：页面没印的轴、点、相位词与状态名不许出现在句子里（十五串见 `OUT_OF_SCOPE_WORDS`）。

    报错串按整改轮 1 B4 的形状 `['越界具名「…」']` 点名命中的是哪一串（计划门验第 4 类引用逐字对）。
    """
    hits = [word for word in OUT_OF_SCOPE_WORDS if word in TRANSIT.entries[key]]
    assert not hits, f"条目 {key}: {['越界具名「%s」' % word for word in hits]}"


@pytest.mark.parametrize("key", built_keys())
def test_verdict_and_advice_words_are_absent(key) -> None:
    """结论/建议词六字表（R26 口径）：自撰表不代读者下断词，也不给「需要/应该」这类指令。

    `advice_hits` 先抹 `NON_ADVICE_FORMS` 三个具名词形。行运这一家**今天不需要**任何新增词形
    豁免；如果某一批被迫加豁免，那是裁定而不是修句子，须停下列进偏差表。
    """
    assert advice_hits(TRANSIT.entries[key]) == [], key


@pytest.mark.parametrize("key", built_keys())
def test_no_layer_word_and_no_calendar_word_inside_an_entry(key) -> None:
    """一张表服务三层，所以层名与日历词两族都只能住在开篇句（本文头注第一段与 spec 全局约束第二条）。

    这一道门不是风格：键式 `transit.aspect.{moving}.{natal}.{type}` 不含层名，引擎会把同一个键
    在三层各印一次（fixture 那手实测 7 次跨层复用、长盘 13 次）。层名一进句子，
    「行运火星合本命土星」在次限小节里就是一句假话，而唯一的修法是把 648 条复制成 1944 条。
    日历词是整改轮 1（A2）折进同一条门的第二族，判的是同一类谎的另一半：次限一格走一年、
    太阳弧按弧长推，「今天」「这周」对任何非当日的目标日都是假话——日期与层名一样，只许开篇句说。
    报错串按族点名：`['层名「…」进了条目']` 与 `['日历词「…」进了条目']`（整改轮 1 B4 定的形状，
    19 份下游 brief 的变异期望串照它逐字对）。
    """
    text = TRANSIT.entries[key]
    problems = [f'层名「{word}」进了条目' for word in LAYER_WORDS if word in text]
    problems += [f'日历词「{word}」进了条目' for word in CALENDAR_WORDS if word in text]
    assert not problems, f"条目 {key}: {problems}"


def test_a_fully_landed_pair_keeps_five_distinct_tails() -> None:
    """五条相位句共用一副骨架，句尾是最容易共用成品的地方。

    只对**五条都已落地**的块判（批次期半块不许红——Plan F 偏差 23 的「不足整族按块长折半」同法）。
    复测（构造一个只改相位字的块，本门必须红）：见 Plan G 计划文档「计划阶段的门验」第 9 行输出，
    与本报告里 T2 变异 2 的真实报错串。
    """
    tails: dict[tuple[str, str], list[tuple[str, str]]] = {}
    for key in TRANSIT.entries:
        family, arg = key_parts(key)
        if family != "aspect":
            continue
        pair = (str(arg["moving"]), str(arg["natal"]))
        tails.setdefault(pair, []).append((key, TRANSIT.entries[key][-12:]))
    for pair, rows in tails.items():
        if len(rows) < 5:
            continue
        seen = [tail for _key, tail in rows]
        assert len(set(seen)) == 5, f"{pair[0]}×{pair[1]} 五句的末十二字有重复"


def _is_self_pair(key: str) -> bool:
    """G38(b) 唯一的跳过谓词：相位族键上移动侧与本命侧是同一枚点。

    整改轮 1 B2 把它从 `test_a_reversed_key_is_not_a_copy` 的 `continue` 里提成模块级 helper：
    G38(b) 与 `test_the_self_pair_is_the_only_skipped_shape` 共用这一个谓词，而钉的另一侧用
    「反向键逐字等于自己」**独立**算出自反对集并断言两者相等——谓词被顺手多长一根手指
    （扩大跳过名单）或收窄，两条里必有一条红。只对相位族调用（月亮三族的键上没有 `moving`）。
    """
    _family, arg = key_parts(key)
    return arg["moving"] == arg["natal"]


def test_a_reversed_key_is_not_a_copy() -> None:
    """`X→本命Y` 与 `Y→本命X` 是两个键、两个事实（行运水星压本命太阳 ≠ 行运太阳压本命水星）。

    剥掉「本命」二字与全部 12 个点名后逐字相同即判复制。**自反对跳过**（`Moon×本命Moon`
    就是自己的镜像，一比必红）——跳过条件住在 `_is_self_pair`（整改轮 1 B2 提出），这个 `continue`
    本身是一条无人守的放宽，所以下面那条 `test_the_self_pair_is_the_only_skipped_shape` 把
    「被跳过的恰好只有自反对」钉成断言。

    批次期形状：本门从 **T4** 起才有第一个真对手可撞（`Moon×本命Sun` 对上本批的 `Sun×本命Moon`），
    T2-T3 它是空转的绿。不许为了「门全证」把本批的键改成反向已存在的键。
    """
    stripped: dict[str, str] = {}
    for key, text in TRANSIT.entries.items():
        family, _arg = key_parts(key)
        if family != "aspect":
            continue
        if _is_self_pair(key):
            continue
        body = text.replace("本命", "")
        for zh in POINT_ZH:
            body = body.replace(zh, "")
        stripped[key] = body
    for key, body in stripped.items():
        _family, arg = key_parts(key)
        reverse = transit_plain.aspect_key(str(arg["natal"]), str(arg["moving"]), str(arg["type"]))
        if reverse in stripped:
            assert stripped[reverse] != body, f"{key} 与反向键 {reverse} 去掉点名后逐字相同"


def test_the_self_pair_is_the_only_skipped_shape() -> None:
    """把上一门那句 `continue` 从「无人守的放宽」变成断言（整改轮 1 B2 重写判据）。

    计划阶段自撞过一次的第三轮（Plan G 计划正文「计划阶段的门验」第 3 节第二条）：`Moon×本命Moon`
    这类自反对的反向键**就是它自己**，一比必红，所以门必须跳过它。跳过一旦写成习惯，下一批完全可能
    顺手多跳一个「不太像自反」的对，而机器不会报。旧版对分堆后的两堆各断一句 `key == reverse` /
    `key != reverse`，两行都在重述分堆谓词本身（同义反复），判不住「扩大跳过名单」——整改轮 1 起
    改为**两次独立计算必须相等**：① `_is_self_pair` 为真的键集（= G38(b) 的 `continue` 实际跳过的
    那批，共用同一谓词所以钉得住实现）；② 用「反向键 == 自己」独立算出的自反对集（钉得住意图）。
    谓词多跳一对 ⇒ ①⊋② 红；谓词少跳一对 ⇒ ①⊊② 红且上一门自己撞上镜像对比红。另断今天表里
    确实有自反对，否则 `continue` 是一条无人到达的死支路。
    """
    aspect_keys = [key for key in TRANSIT.entries if key_parts(key)[0] == "aspect"]
    skipped = {key for key in aspect_keys if _is_self_pair(key)}
    mirrored: set[str] = set()
    for key in aspect_keys:
        _family, arg = key_parts(key)
        if transit_plain.aspect_key(str(arg["natal"]), str(arg["moving"]), str(arg["type"])) == key:
            mirrored.add(key)
    assert mirrored, "表里没有一条自反对：G38(b) 的 `continue` 成了一条无人到达的死支路"
    assert skipped == mirrored, sorted(skipped ^ mirrored)


def test_the_corpus_is_not_registered_while_batches_land() -> None:
    """`TRANSIT` 今天**不许**在 `PLAIN_CORPORA` 里，而戊组的措辞闸今天就已经吃得到它。

    两半合一条是有原因的，它们是同一处形状的两侧：登记行若在 T2-T22 之间被顺手加上，工厂的
    `set(entries) == universe()` 立刻红（语料还只建了一部分），于是有人会把**语料**改成假满用以
    让工厂绿；而 `transit` 若从 `PREDICTION_GATED_SYSTEMS`（`tests/plain_wording.py:66`）里丢了，
    本文件 `test_every_plain_text_meets_the_shared_factory_contract` 的 30 例会继续全绿而**一条
    时态禁串也没查过**——那是这套东西最省事的假绿。两颗钉同进同退，才既拦早登记也拦漏分流。

    T23 的处置：删掉第一半（`assert "transit" not in PLAIN_CORPORA`），换成 Plan F 那一对登记钉
    （`"western" in PLAIN_CORPORA` 与 `PLAIN_CORPORA["western"] is WESTERN` 的行运版），并把
    `test_western_plain_corpus.py:405-417` 那条「另两家未登记」的钉改写成只指 `vedic`。
    """
    assert "transit" not in PLAIN_CORPORA, "登记行提前出现了：工厂的 set==universe 会从 T2 红到 T22"
    assert "transit" in PREDICTION_GATED_SYSTEMS, "分流丢了：G31 十七串与 G36 八串会静默不查这 648 条"
    assert TRANSIT.system == "transit", TRANSIT.system


def test_the_key_builders_are_the_only_key_source() -> None:
    """四个构造器不补零、带族名（spec §5.3 的键式），且族名与 `key_parts` 的四族一一对应。

    这一条看着像样板，其实它是这张表唯一的形式契约：语料侧与 `universe()` 两侧都吃这同一个
    函数，构造器一改（族名换字、宫位补零），两侧同时改变而 `set(entries) <= universe()` 照样
    绿——键式静默改名是这一族唯一不会被内容门看见的失败。宫位那枚特意用 `9`（一位数）而不是
    `11`：补零的写法（`{house:02d}`）在这里才会露出来。

    整改轮 1 B1 又把这颗单例收留为**轴对账钉**的家：`AXIS_ZH` 与引擎私有量 `_AXIS_ZH` 必须逐字
    相等。此前两处注释都说这条钉「已由 `tests/golden/test_transit_golden.py` 守住」，实测该文件
    一条轴测都没有（复测：`cd backend && grep -nEi "axis|上升|天顶" tests/golden/test_transit_golden.py` → 空）。
    测试为对账而 import 引擎私有量与生产模块的依赖方向无关（AGENTS §1 管的是 `app/`，
    `plain_corpora.py` 因此继续不引它）；T5-T21 写「本命上升/本命天顶」的句子吃的就是这张表。
    """
    assert transit_plain.aspect_key("Sun", "Mercury", "conjunction") == "transit.aspect.Sun.Mercury.conjunction"
    assert transit_plain.progressed_moon_sign_key("Gemini") == "transit.progressed_moon_sign.Gemini"
    assert transit_plain.progressed_moon_house_key(9) == "transit.progressed_moon_house.9"
    assert transit_plain.progressed_axis_key("MC", "Virgo") == "transit.progressed_axis.MC.Virgo"
    assert {key_parts(key)[0] for key in TRANSIT.universe()} == {
        "aspect", "progressed_moon_sign", "progressed_moon_house", "progressed_axis"
    }
    from app.engines.transit import _AXIS_ZH
    assert AXIS_ZH == _AXIS_ZH, (AXIS_ZH, _AXIS_ZH)


def test_no_key_and_no_sentence_are_said_twice() -> None:
    """同一张表里两格不许说同一件事，两个方向各一半：跨族键重复与逐字句子重复。

    ①`TRANSIT_READINGS` 是 `{**分表, **推运表}` 的合并，`dict` 合并会**静默覆盖同名键**，失败
      形状是聚合条数变小而 `universe()` 不动。本条实际判的两半：两张分表的键集不相交、聚合条数
      恰等于两表条数之和——跨族撞键在任一半上露形。诚实交代（整改轮 1 C2）：**同一个 dict 字面量
      内部的重复键在 Python 解析时就被折叠，进不了本门的视野**，旧 docstring 那句「本条把根因
      直接说出来」是这条门做不到的承诺，已删；族内字面量重复由逐字句子重复那半兜住形状相同的
      最坏情况，其余靠命题对照表人读。
    ②同一个 `{moving}×{natal}` 的五句不许共用逐字相同的句子，两颗不同的移动星也不许。只判逐字
      相同，不判「语义相近」——后者是形状盲的正则做不到的事（spec §7 已承认措辞筛是形状盲的），
      强行机检会把合法的同族句式误红。同义重复由命题对照表读（口径裁定第 9 条）。
    """
    from collections import Counter

    aspect_keys = set(transit_plain_aspect.TRANSIT_ASPECT_READINGS)
    progression_keys = set(transit_plain.TRANSIT_PROGRESSION_READINGS)
    assert not (aspect_keys & progression_keys), sorted(aspect_keys & progression_keys)
    assert len(TRANSIT.entries) == len(aspect_keys) + len(progression_keys)
    duplicated = [text for text, count in Counter(TRANSIT.entries.values()).items() if count > 1]
    assert not duplicated, duplicated


def test_roster_counts_and_no_key_outside_universe() -> None:
    """批次花名册（族内不许多建）+ 键不外溢（族名拼错、参数越界当场红）。

    两道并一条是有意的：它们判的是同一件事的两面——多建的键一定落在 `universe()` 里或外面，
    只数数量会放过「族数对但键写歪」，只比全集会放过「全集内多建一条同族的键」。
    当前数 = `aspect` **120 条**（移动星 Sun 与 Moon 各十二个本命点，各 60 条），
    三族推运归 T22，所以是 0；`ROSTER_TARGETS` 只许改那一行的数字（通用循环 Step 3，本 docstring 跟着数走）。
    """
    from collections import Counter

    counts = Counter(key_parts(key)[0] for key in TRANSIT.entries)
    assert {family: counts.get(family, 0) for family in ROSTER_TARGETS} == ROSTER_TARGETS, counts
    assert set(TRANSIT.entries) <= TRANSIT.universe(), sorted(set(TRANSIT.entries) - TRANSIT.universe())


def test_sections_and_openers_cover_the_declared_shape() -> None:
    """五个小节标题、八条开篇句、三条空态分支三者的对账 + 层名词义务（spec §6 的 G15 续用 + R53）。

    四件并一条，因为它们判的是同一张「页面形状」的四个方向：
    ①`TRANSIT_OPENERS` 的键必须恰好是 `TRANSIT_SECTION_TITLES` 的五个键并上
      `TRANSIT_NONE_BRANCHES` 的三个值——少一条，空触发的那段就承诺引擎给不出的话；
      多一条，就是永远印不出来的死字。
    ②`TRANSIT_NONE_BRANCHES` 恰三条、键序就是三个相位小节，且**每一条的值都能在 `TRANSIT_OPENERS`
      里查到**。值必须是**键名**而不是句子文本：装配那行走的是 `compose(TRANSIT, opener, …)`，
      `opener` 进 `openers` 查文本（`app/engines/western.py:219-222` 同形）。写成文本会让装配
      查不到开篇句而崩——本任务不让它崩在实施者手上。
    ③标题字面与次序逐字钉（三个相位小节一律带「对本命」，那是 spec 偏差 5 那条代价的唯一落点）。
      标题另走一套口径：它是 `<h3>` 不是句子，所以要求「≤8 字、不含「你」、不含「。」、不含
      `_FORBIDDEN_FOR_TITLES`」——那张表是 `FORBIDDEN` 的超集（另加 `（` `）` `、`）。
    ④层名词义务（G37 的反向半件）：每条开篇句必须含自己那一层的层名词，且不许含**另外两层**的
      层名词。`transit_aspect` 那句合法地写「本命盘」而不写「次限」；`progressed_*` 两句里的
      「推运盘」合法（`推运` 不是第三层的名字，它是次限层的用户可见总称，见 `LAYER_IN_OPENER` 注）。
      开篇句同时吃 `CALENDAR_WORDS` 十四串（整改轮 1 B3）：页面允许任选目标日（`TransitPage.tsx`
      的 maxYear=now+30 与「目标日 {chart.target_date}」），所以开篇句里的「今天」对任何非当日
      目标日同样是假话——日期要说也只许说「目标日」这类日期中立的形状。
    """
    expected_openers = set(transit_plain.TRANSIT_SECTION_TITLES) | set(transit_plain.TRANSIT_NONE_BRANCHES.values())
    assert set(transit_plain.TRANSIT_OPENERS) == expected_openers
    assert list(transit_plain.TRANSIT_NONE_BRANCHES) == ["transit_aspect", "progressed_aspect", "directed_aspect"]
    assert len(transit_plain.TRANSIT_NONE_BRANCHES) == 3
    for section, opener_key in transit_plain.TRANSIT_NONE_BRANCHES.items():
        assert opener_key in transit_plain.TRANSIT_OPENERS, (section, opener_key)
        assert opener_key not in transit_plain.TRANSIT_SECTION_TITLES, opener_key

    assert list(transit_plain.TRANSIT_SECTION_TITLES) == [
        "transit_aspect", "progressed_aspect", "directed_aspect", "progressed_moon", "progressed_axis"
    ]
    assert list(transit_plain.TRANSIT_SECTION_TITLES.values()) == [
        "行运对本命相位", "次限对本命相位", "太阳弧对本命相位", "次限月亮", "次限上升与天顶"
    ]
    for section, title in transit_plain.TRANSIT_SECTION_TITLES.items():
        assert 0 < len(title) <= 8, (section, title)
        assert "你" not in title and "。" not in title, (section, title)
        assert not [token for token in _FORBIDDEN_FOR_TITLES if token in title], (section, title)

    other_layers = {word for word in LAYER_IN_OPENER.values()}
    for section, text in transit_plain.TRANSIT_OPENERS.items():
        assert frame_violations("transit", text) == [], (section, text)
        own = LAYER_IN_OPENER[section]
        assert own in text, f"框架 {section}: {['开篇句缺自己的层名词「%s」' % own]}"
        foreign = [word for word in other_layers if word != own and word in text]
        assert not foreign, (section, "开篇句带了别的层的层名词", foreign)
        calendar = [word for word in CALENDAR_WORDS if word in text]
        assert not calendar, f"框架 {section}: {['日历词「%s」进了开篇句' % word for word in calendar]}"


def test_the_source_string_is_a_provenance_string_not_a_sentence() -> None:
    """出处串与自撰声明都不进工厂遍历（它们不是白话句），所以禁字这一半由本文件自守。

    先例：卡巴拉同名门与 Plan F 的 `test_the_source_string_is_a_provenance_string_not_a_sentence`
    / `test_the_note_is_the_self_authored_declaration` —— 行运这一家把两条并成一条，因为两份
    判的是同一件事：「不出现在遍历里的串，谁用谁自守」，而本批的用例数由 `7×条数 + 9` 钉死，
    不留两条同义单例的位置。
    「；」也禁：note 不是判语，门本来管不到它，但它要与 648 条判语**同屏印在同一个 `<p>` 里**，
    读者无法知道哪一句走哪套口径，两套口径在这里并成一套（这是裁定，不是抄近路）。
    禁 `中天` 与 `逆行` 是行运版特有的：这两处都是页面上有、而 648 的键式刻意不讲的形状，
    声明句不许声称转述了它没转述的东西（AGENTS.md §7「只列真读过的表」同一条纪律）。
    关键词逐件钉而不是整串逐字：整串逐字在 golden 里钉（归 T25），本条要的是「日后有人改写
    这句时，诚实的那三点不许被改掉」。
    """
    from tests.plain_wording import FORBIDDEN

    source = transit_plain.TRANSIT_PLAIN_SOURCE
    note = transit_plain.TRANSIT_PLAIN_NOTE
    for token in FORBIDDEN:
        assert token not in source, token
        assert token not in note, token
    for token in ("；", "《", "依", "中天", "逆行", "退行", "宫头", "南交"):
        assert token not in source, source
        assert token not in note, note
    assert source.startswith("平台自撰的行运白话转述表"), source
    assert source.endswith("。"), source
    assert note.endswith("。"), note
    assert "自撰" in note, note
    assert "请求时不生成" in note, note
    assert "不预测具体事件" in note, note
