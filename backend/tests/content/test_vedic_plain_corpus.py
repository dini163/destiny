"""吠陀白话表的本地门（Plan H spec §5/§7/§10；T1 建骨架与七道门，T2-T7 逐批追加语料）。

为什么这张测在批次期必须自己跑全套而不靠工厂：`VEDIC` 从 T1 就定义在
`engines/plain_corpora.py` 里，但**登记行归 T8**（全局约束「批次期定义而不登记」：
`universe()` 是全量 252 算的，语料是一批批建的，提前登记会让工厂的
`set(entries) == universe()` 从 T1 红到 T7）。那七批里工厂的参数化用例看不到这张表，
所以「登记表里没有这一家」期间的所有口径由本文件逐条守着。

七道每键门里，吠陀这一家与行运的差别有三处（都是「一张表服务多行」的直接后果）：
①**宿条目不许点名任何曜**——`vedic.nakshatra.{宿}` 一宿服务九曜与命度十行（A 手 9 行、
B 手 10 行），点一颗就替另外九行说了话；②**主事星条目不写角色词**——
`vedic.dasha_lord.{曜}` 同时服务大运与小运，写「大运」就把小运那一行说假了；
③**落座/落宫条目只点自己的曜**，星座名/宫号逐项对账。

措辞四口径（≥40 字 / 恰一「。」 / 含你 / 禁字）与戊组两组增量禁串（G31 十七串、G36 八串）
住在 `tests/plain_wording.py`，本文件只调不改（口径单一正主，AGENTS.md §1）。
G36 的 `百药` 掩码也住在那里（`NON_DECISION_FORMS`），本文件只吃它的结果。

复测：`cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m pytest tests/content/test_vedic_plain_corpus.py -o addopts=""`。
用例数 = **7×已落地条数 + 7**（T1-T7）；T8 删一条、加三条 ⇒ +2；T10 加一条 ⇒ 终态
**1774 = 7×252 + 10**。
"""

import re

import pytest

from app.content import vedic_plain, vedic_plain_gruha
from app.content.vedic import GRAHAS, NAKSHATRAS, SIGNS_EN, SIGNS_ZH
from app.engines.plain_corpora import PLAIN_CORPORA, VEDIC
from app.engines.western import SIGN_ELEMENT, SIGN_MODALITY
from tests.plain_wording import (
    PREDICTION_GATED_SYSTEMS,
    advice_hits,
    frame_violations,
    wording_violations,
)

GRAHA_ZH = {graha.name: graha.name_zh for graha in GRAHAS}
NAK_ZH = {nak.name_en: nak.name_zh for nak in NAKSHATRAS}
SIGN_ZH = dict(zip(SIGNS_EN, SIGNS_ZH))

CN_HOUSE = {
    "一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6,
    "七": 7, "八": 8, "九": 9, "十": 10, "十一": 11, "十二": 12,
}
REV_CN_HOUSE = {value: name for name, value in CN_HOUSE.items()}
HOUSE_RE = re.compile(r"第([一二三四五六七八九十]{1,2})宫")

ELEMENT_ZH = {"fire": "火象", "earth": "土象", "air": "风象", "water": "水象"}
MODALITY_ZH = {"cardinal": "基本宫", "fixed": "固定宫", "mutable": "变动宫"}
SIGN_TO_ELEMENT = dict(zip(SIGNS_EN, SIGN_ELEMENT))
SIGN_TO_MODALITY = dict(zip(SIGNS_EN, SIGN_MODALITY))

#: 页面没有的曜、点、轴与状态名。`月亮` 是西洋页的九曜名（本页用「太阴」）；
#: `上升` 只许住在开篇句（宿条目服务九曜 + 命度十行，见头注①）；`逆行/退行`、
#: `四足/pada`、`度数` 是页面印了而键式刻意不讲的形状（偏差 6），白话不讲也不点名；
#: `庙旺/入庙/落陷/旺相/失势` 是吠陀判断术语，本表不承担。
OUT_OF_SCOPE_WORDS = (
    "天王", "海王", "冥王", "北交", "南交", "上升", "下降", "中天", "天顶", "天底",
    "宫头", "逆行", "退行", "相位", "本命", "庙旺", "入庙", "落陷", "旺相", "失势",
    "四足", "pada", "分盘", "navamsa", "小行星", "福点", "宿命点", "命度", "初度",
    "末度", "度数", "月亮",
)

#: 一张表服务多行：主事星键同时服务大运与小运（头注②）。角色词对本表**四族全部条目**
#: 生效——键上没有任何一族带角色，任何一条条目写角色都是错位。
ROLE_WORDS = ("大运", "小运", "安塔尔", "bhukti", "值年", "流年")

#: 批次花名册：各族**已建**条数。T1 落座 36；T2 宿 27 + 主事星 9；T3/T4 落座到 108；
#: T5-T7 落宫到 108。只许改这一行（通用循环 Step 3）。
ROSTER_TARGETS: dict[str, int] = {
    "gruha_sign": 36,
    "gruha_house": 0,
    "nakshatra": 27,
    "dasha_lord": 9,
}

_FORBIDDEN_FOR_TITLES = ("；", "（《", "』", "（", "）", "、")


def built_keys() -> list[str]:
    return sorted(VEDIC.entries)


def key_parts(key: str) -> tuple[str, dict[str, object]]:
    """键 → (族名, 参数)。族的次序与 spec §5.3 的键式表逐字同序。"""
    bits = key[len("vedic.") :].split(".")
    family = bits[0]
    if family == "gruha_sign":
        return family, {"graha": bits[1], "sign": bits[2]}
    if family == "gruha_house":
        return family, {"graha": bits[1], "house": int(bits[2])}
    if family == "nakshatra":
        return family, {"nakshatra": ".".join(bits[1:])}
    if family == "dasha_lord":
        return family, {"graha": bits[1]}
    raise AssertionError(f"未知族：{key}")


@pytest.mark.parametrize("key", built_keys())
def test_every_plain_text_meets_the_shared_factory_contract(key) -> None:
    """≥40 字 / 恰一「。」 / 含「你」/ 四串 `FORBIDDEN` / 戊组两组禁串（G31、G36）。

    工厂的 `test_every_entry_meets_the_wording_contract[vedic:*]` 在 T8 登记后会对同一个
    对象跑同一条谓词；这份重复是**刻意留的**：登记归 T8，而本条从 T1 起逐条跑，所以它是
    「登记表里没有这一家时仍然存在的独立验证」。`vedic` 已在 `PREDICTION_GATED_SYSTEMS`
    里，所以 G31 与 G36 今天就在生效；`百药` 的掩码在 `wording_violations` 内部，
    本门不另抄一份。
    """
    assert wording_violations(VEDIC, key) == []


@pytest.mark.parametrize("key", built_keys())
def test_the_naming_reconciliation_holds(key) -> None:
    """命名对账（本文件的主门）：键带的名字必须齐、键没有的名字一个不许有。

    ①九曜名：`gruha_sign` / `gruha_house` / `dasha_lord` 三族**恰好**出现键上那一颗
      （其余八颗一个不许出现）；`nakshatra` 族**一颗都不许出现**（一宿服务九曜 + 命度）；
    ②星座名：只有 `gruha_sign` 族键上有，出现与否必须等于键上那一座；
      其余三族一个星座名都不许出现；
    ③宫号：只有 `gruha_house` 族键上有，`HOUSE_RE` 抓到的每一个都必须等于键上的数；
    ④宿名：只有 `nakshatra` 族键上有，出现与否必须等于键上那一宿（别的宿名一个不许有）；
    ⑤主事星族不许出现任何宿名——它只服务值年主星。
    """
    family, arg = key_parts(key)
    text = VEDIC.entries[key]
    problems: list[str] = []

    own_graha = GRAHA_ZH[str(arg["graha"])] if "graha" in arg else None
    for zh in GRAHA_ZH.values():
        want = own_graha is not None and zh == own_graha
        if (zh in text) != want:
            problems.append(f"点名「{zh}」在文中={zh in text}，键上={want}")

    own_sign = SIGN_ZH[str(arg["sign"])] if "sign" in arg else None
    for zh in SIGN_ZH.values():
        want = own_sign is not None and zh == own_sign
        if (zh in text) != want:
            problems.append(f"星座「{zh}」在文中={zh in text}，键上={want}")

    houses_said = [CN_HOUSE[matched] for matched in HOUSE_RE.findall(text)]
    house_on_key = arg.get("house")
    if house_on_key is None:
        if houses_said:
            problems.append(f"键里没有宫位，文中却写了宫号 {houses_said}")
    elif houses_said != [house_on_key]:
        problems.append(f"键是第{house_on_key}宫，文中写 {houses_said}")

    own_nak = NAK_ZH[str(arg["nakshatra"])] if "nakshatra" in arg else None
    for zh in NAK_ZH.values():
        want = own_nak is not None and zh == own_nak
        if (zh in text) != want:
            problems.append(f"宿名「{zh}」在文中={zh in text}，键上={want}")

    assert not problems, f"{key}: {problems}"


@pytest.mark.parametrize("key", built_keys())
def test_the_structural_fact_matches_the_table(key) -> None:
    """G34：元素/形态只许出现在落座族，且必须等于键上星座的 `SIGN_ELEMENT`/`SIGN_MODALITY`。

    吠陀与西洋共用同一组十二星座的 EN 名，所以元素/形态表可以逐字复用
    `app/engines/western.py` 的两张平行数组（复测：
    `cd backend && python -c "from app.engines.western import SIGN_ELEMENT; print(len(SIGN_ELEMENT))"` → 12）。
    落宫、宿、主事星三族的键上**没有星座**，主张任何元素/形态就是替页面说了它没算过的话。
    """
    family, arg = key_parts(key)
    text = VEDIC.entries[key]
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
    """G35：宫号必须中文；度数、日期、编号一律不进白话。"""
    violations = ["含阿拉伯数字"] if re.search(r"\d", VEDIC.entries[key]) else []
    assert not violations, f"条目 {key}: {violations}"


@pytest.mark.parametrize("key", built_keys())
def test_out_of_scope_names_are_absent(key) -> None:
    """G33：页面没印的曜、点、轴与状态名不许出现在句子里（名单见 `OUT_OF_SCOPE_WORDS`）。"""
    hits = [word for word in OUT_OF_SCOPE_WORDS if word in VEDIC.entries[key]]
    assert not hits, f"条目 {key}: {['越界具名「%s」' % word for word in hits]}"


@pytest.mark.parametrize("key", built_keys())
def test_verdict_and_advice_words_are_absent(key) -> None:
    """结论/建议词六字表（R26 口径）：自撰表不代读者下断词，也不给指令。"""
    assert advice_hits(VEDIC.entries[key]) == [], key


@pytest.mark.parametrize("key", built_keys())
def test_no_role_word_inside_an_entry(key) -> None:
    """角色词只许住在开篇句（H3）：主事星键同时服务大运与小运，写死一层就是替另一层说谎。

    对**四族全部条目**生效：键上没有任何一族带角色，任何条目写「大运/小运」都是错位。
    报错串按族点名，形状与行运的层名门同款。
    """
    text = VEDIC.entries[key]
    problems = [f"角色词「{word}」进了条目" for word in ROLE_WORDS if word in text]
    assert not problems, f"条目 {key}: {problems}"


def test_the_corpus_is_not_registered_while_batches_land() -> None:
    """T1-T7 刻意不登记；提前登记会让工厂的全等闸从第一批红到第七批。

    `VEDIC` 对象与本地门吃的必须是同一个；登记行归 T8，届时本条删除、换成三颗登记钉。
    """
    assert "vedic" not in PLAIN_CORPORA, "登记行提前落地了：工厂会在语料建完前全等红"
    assert VEDIC.system == "vedic", VEDIC.system


def test_roster_counts_and_no_key_outside_universe() -> None:
    """批次花名册（族内不许多建）+ 键不外溢（族名拼错、参数越界当场红）。"""
    from collections import Counter

    counts = Counter(key_parts(key)[0] for key in VEDIC.entries)
    assert {family: counts.get(family, 0) for family in ROSTER_TARGETS} == ROSTER_TARGETS, counts
    assert set(VEDIC.entries) <= VEDIC.universe(), sorted(set(VEDIC.entries) - VEDIC.universe())


def test_sections_and_openers_cover_the_declared_shape() -> None:
    """四个小节标题、五条开篇句、一条空态分支三者的对账（spec §6 的 G15 续用 + R53）。

    ①`VEDIC_OPENERS` 的键必须恰好是 `VEDIC_SECTION_TITLES` 的四个键并上
      `VEDIC_NONE_BRANCHES` 的一个值；②`dasha_none` 必须是键名而不是句子文本；
    ③标题字面与次序逐字钉，且 ≤8 字、不含「你」「。」与 `_FORBIDDEN_FOR_TITLES`；
    ④五条开篇句全部过 `frame_violations`（含 G31/G36 与「；」）。
    """
    expected_openers = set(vedic_plain.VEDIC_SECTION_TITLES) | set(
        vedic_plain.VEDIC_NONE_BRANCHES.values()
    )
    assert set(vedic_plain.VEDIC_OPENERS) == expected_openers
    assert list(vedic_plain.VEDIC_NONE_BRANCHES) == ["dasha"]
    assert vedic_plain.VEDIC_NONE_BRANCHES == {"dasha": "dasha_none"}
    for section, opener_key in vedic_plain.VEDIC_NONE_BRANCHES.items():
        assert opener_key in vedic_plain.VEDIC_OPENERS, (section, opener_key)
        assert opener_key not in vedic_plain.VEDIC_SECTION_TITLES, opener_key

    assert list(vedic_plain.VEDIC_SECTION_TITLES) == [
        "gruha_sign", "gruha_house", "nakshatra", "dasha"
    ]
    assert list(vedic_plain.VEDIC_SECTION_TITLES.values()) == [
        "九曜落座", "九曜落宫", "星宿落点", "现行大运与小运"
    ]
    for section, title in vedic_plain.VEDIC_SECTION_TITLES.items():
        assert 0 < len(title) <= 8, (section, title)
        assert "你" not in title and "。" not in title, (section, title)
        assert not [token for token in _FORBIDDEN_FOR_TITLES if token in title], (section, title)

    for section, text in vedic_plain.VEDIC_OPENERS.items():
        assert frame_violations("vedic", text) == [], (section, text)


def test_the_key_builders_are_the_only_key_source() -> None:
    """四个构造器不补零、带族名；字面键集合必须**全部落在** `universe()` 里。

    落座/落宫的键是字面量（`vedic_plain_gruha` 不能反向 import 构造器，否则成环），
    所以拼错一个键不会被「键构造器一致」抓住；抓它的是这条 ⊆ 判据：拼错的键不在
    `universe()` 里，当场红。宫位那枚特意用 `9`（一位数）：补零写法才会露出来。
    """
    assert vedic_plain.gruha_sign_key("Sun", "Mesha") == "vedic.gruha_sign.Sun.Mesha"
    assert vedic_plain.gruha_house_key("Moon", 9) == "vedic.gruha_house.Moon.9"
    assert vedic_plain.nakshatra_key("Purva Ashadha") == "vedic.nakshatra.Purva Ashadha"
    assert vedic_plain.dasha_lord_key("Rahu") == "vedic.dasha_lord.Rahu"

    universe = VEDIC.universe()
    literals = {
        **vedic_plain_gruha.GRUHA_SIGN_READINGS,
        **vedic_plain_gruha.GRUHA_HOUSE_READINGS,
        **vedic_plain.NAKSHATRA_READINGS,
        **vedic_plain.DASHA_LORD_READINGS,
    }
    assert set(literals) <= universe, sorted(set(literals) - universe)
    assert {key_parts(key)[0] for key in universe} == {
        "gruha_sign", "gruha_house", "nakshatra", "dasha_lord"
    }


def test_no_key_and_no_sentence_are_said_twice() -> None:
    """两张分表不许撞键；聚合面不许静默覆盖；逐字相同的句子一个都不许有。

    `VEDIC_READINGS` 是四个 dict 的合并，`dict` 合并会**静默覆盖**同名键，失败形状是
    聚合条数变小而 `universe()` 不动——本条用「四表键集两两不相交 + 聚合条数等于四表
    之和」两半把它露形。同一个 dict 字面量内部的重复键在 Python 解析时就被折叠，
    本门看不到；那一种的最坏形状（同键同句）由逐字句子重复那一半兜住。
    """
    from collections import Counter

    parts = [
        vedic_plain_gruha.GRUHA_SIGN_READINGS,
        vedic_plain_gruha.GRUHA_HOUSE_READINGS,
        vedic_plain.NAKSHATRA_READINGS,
        vedic_plain.DASHA_LORD_READINGS,
    ]
    keys = [set(part) for part in parts]
    for index in range(len(keys)):
        for other in range(index + 1, len(keys)):
            assert not (keys[index] & keys[other]), sorted(keys[index] & keys[other])
    assert len(VEDIC.entries) == sum(len(part) for part in parts)

    duplicated = [
        text for text, count in Counter(VEDIC.entries.values()).items() if count > 1
    ]
    assert not duplicated, duplicated


def test_the_source_string_and_the_note_are_provenance_declarations() -> None:
    """出处串与自撰声明不进工厂遍历（它们不是白话句），所以禁字这一半由本文件自守。

    `VEDIC_PLAIN_NOTE` 是用户看见的「这些中文从哪来」那一句：三句、句间「。」、无「；」。
    关键词逐件钉而不是整串逐字：整串逐字在 API 与 golden 里钉（T10），本条要的是
    「日后有人改写这句时，诚实的那几点不许被改掉」。
    """
    from tests.plain_wording import FORBIDDEN

    source = vedic_plain.VEDIC_PLAIN_SOURCE
    note = vedic_plain.VEDIC_PLAIN_NOTE
    for token in FORBIDDEN:
        assert token not in source, token
        assert token not in note, token
    for token in ("；", "《", "依", "月亮", "逆行", "pada"):
        assert token not in source, source
        assert token not in note, note
    assert source.startswith("平台自撰的吠陀白话转述表"), source
    assert source.endswith("。"), source
    assert "自撰" in note, note
    assert "请求时不生成" in note, note
    assert "不预测具体事件" in note, note
    assert note.count("。") == 3, note
    assert note.endswith("。"), note


def test_the_assembly_shape_is_keep_unclosed_and_unsorted() -> None:
    """`keep` + `closers=None`（裁定 R48）：不分带、不重排、不由合成器补结论句。"""
    assert VEDIC.grouping == "keep", VEDIC.grouping
    assert VEDIC.closers is None, VEDIC.closers
