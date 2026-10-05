"""西洋本命白话表的本地门（戊组 spec §7、§10；Plan F T1-T19）。

为什么这张测在批次期必须自己跑全套而不靠工厂：`WESTERN` 从 T1 存在但登记归 T15，工厂的
参数化用例这十四批看不到它。为什么戊组要比甲–丁多四道门（命名对账、结构事实、禁数字、
越界具名）：Plan E 的偏差表 9/12/13/14/22 行记着同一类失败——**计划与实施者写的散文里
有假事实，而关键字筛看不见**。那四类谎话恰好就是自撰表最容易说的四件事，所以本文件把它们
做成门，而不是留给「评审员人核」（那一句在 Plan E 里连续五批写出了假事实）。

措辞四口径（≥40 字 / 恰一「。」 / 含你 / 禁字）与戊组两组增量禁串（G31 时态、G36 决策名词）
住在 `tests/plain_wording.py`，本文件只调不改（口径单一正主，AGENTS §1）。

复测：`cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m pytest tests/content/test_western_plain_corpus.py -o addopts=""`。
用例数 = 6×键数 + 结构测条数（每条键六道：共享契约、命名对账、结构事实、禁数字、
越界具名、建议词）。T1 落地 36 键；T14 收尾 542 键。
"""

import re
from itertools import combinations

import pytest

from app.content import western_plain, western_plain_aspect, western_plain_placement
from app.engines.plain_corpora import WESTERN
from app.engines.western import ASPECTS, PLANETS, SIGN_ELEMENT, SIGN_MODALITY, SIGNS, SIGNS_ZH
from tests.plain_wording import advice_hits, frame_violations, wording_violations

PLANET_NAMES = [name for name, *_ in PLANETS]
PLANET_ZH = [zh for _name, _glyph, zh, _swe in PLANETS]
ASPECT_NAMES = [aspect[0] for aspect in ASPECTS]

#: 五个相位词的字面 = 前端已经印在 `AspectLegend` 上的那五个词（`src/lib/astro.ts:39-43`）。
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

#: 页面没有的轴、点与星体。spec §2 刻意不建这些键族，白话里也不许出现它们的名字——
#: 否则一句话在讲响应里没有的事实（R47 的覆盖面纪律反过来用在这里）。
OUT_OF_SCOPE_WORDS = ("南交", "下降", "天底", "小行星", "真交点", "福点", "宿命点", "宫头")

CN_HOUSE = {
    "一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6,
    "七": 7, "八": 8, "九": 9, "十": 10, "十一": 11, "十二": 12,
}
REV_CN_HOUSE = {value: name for name, value in CN_HOUSE.items()}
#: 正则含两位，所以「第十一宫」不会被切读成「第一宫」（这条若不成立，宫号对账门会误放）。
HOUSE_RE = re.compile(r"第([一二三四五六七八九十]{1,2})宫")

#: 标题只服务 `test_sections_and_openers_cover_the_declared_shape` 的标题门：`<h3>` 里的一格
#: 名字不能带分句符号与括号，`、` 禁掉是为了拦住「上升与天顶、北交点」这种把两格并成一格
#: 写。不复用 `FORBIDDEN`，因为标题合法地含「与」，也不管戊组禁串（标题不是判语）。
_FORBIDDEN_FOR_TITLES = ("；", "（《", "』", "（", "）", "、")

#: 批次花名册：各族**已建**条数。T2-T14 每批只把本族那一行的数字改大，一条也不许多。
#: 这道门的作用是把「少建」和「多建」在同一天分开报：工厂那条 `set == universe` 只有 T15
#: 之后才存在，而多建出来的键会漂到引擎永远不触发的位置上（spec §5.3），没人校对得到。
ROSTER_TARGETS: dict[str, int] = {
    "planet_sign": 120,
    "planet_house": 120,
    "aspect": 135,
    "axis_sign": 24,
    "node_sign": 12,
    "node_house": 12,
    "house_theme": 12,
    "element": 4,
    "modality": 3,
    "retrograde": 10,
}


def built_keys() -> list[str]:
    return sorted(WESTERN.entries)


def key_parts(key: str) -> tuple[str, dict[str, object]]:
    """键 → (族名, 参数)。族的次序与 spec §5.3 的键式表逐字同序。"""
    bits = key[len("western.") :].split(".")
    family = bits[0]
    if family == "planet_sign":
        return family, {"planet": bits[1], "sign": bits[2]}
    if family == "planet_house":
        return family, {"planet": bits[1], "house": int(bits[2])}
    if family == "aspect":
        return family, {"planet": bits[1], "other": bits[2], "type": bits[3]}
    if family == "axis_sign":
        return family, {"axis": bits[1], "sign": bits[2]}
    if family == "node_sign":
        return family, {"sign": bits[1]}
    if family == "node_house":
        return family, {"house": int(bits[1])}
    if family == "house_theme":
        return family, {"house": int(bits[1])}
    if family == "element":
        return family, {"element": bits[1]}
    if family == "modality":
        return family, {"modality": bits[1]}
    if family == "retrograde":
        return family, {"planet": bits[1]}
    raise AssertionError(f"未知族：{key}")


def planet_zh(name: str) -> str:
    return PLANET_ZH[PLANET_NAMES.index(name)]


def sign_zh(sign: str) -> str:
    return SIGNS_ZH[SIGNS.index(sign)]


@pytest.mark.parametrize("key", built_keys())
def test_every_plain_text_meets_the_shared_factory_contract(key) -> None:
    """≥40 字 / 恰一「。」 / 含「你」/ 四串 `FORBIDDEN` / 戊组两组禁串（G31、G36）。

    工厂的 `test_every_entry_meets_the_wording_contract[western:*]` 登记后会对同一个对象跑
    同一条谓词；这份重复是**刻意留的**：登记在 T15，而本条从 T1 起逐条跑，所以它是
    「登记表里没有这一家时仍然存在的独立验证」（Plan E T13 评审实测：un-register 只让工厂
    那一侧的用例静默消失，不红）。
    """
    assert wording_violations(WESTERN, key) == []


@pytest.mark.parametrize("key", built_keys())
def test_no_arabic_digits(key) -> None:
    """G35：宫号必须中文；度数、日期、编号一律不进白话（spec §7 的「不得把区间复述成事件时间表」的最省事形状）。"""
    assert not re.search(r"\d", WESTERN.entries[key]), key


@pytest.mark.parametrize("key", built_keys())
def test_out_of_scope_names_are_absent(key) -> None:
    """G33：spec §2 不建的轴、点与星体不许出现在句子里。"""
    naked = WESTERN.entries[key]
    assert not [word for word in OUT_OF_SCOPE_WORDS if word in naked], key


@pytest.mark.parametrize("key", built_keys())
def test_verdict_and_advice_words_are_absent(key) -> None:
    """结论/建议词六字表（R26 口径）：自撰表不代读者下断词，也不给「需要/应该」这类指令。

    `advice_hits` 先抹 `NON_ADVICE_FORMS` 三个具名词形；本期目前**不需要**任何抹词形豁免
    （西洋的词表里没有「对应」这种结构性用法），如果某一批被迫加豁免，那是裁定而不是修句子，
    须停下列进偏差表。
    """
    assert advice_hits(WESTERN.entries[key]) == [], key


@pytest.mark.parametrize("key", built_keys())
def test_the_naming_reconciliation_holds(key) -> None:
    """命名对账（本文件的主门）：键带的名字必须齐、键没有的名字一个不许有。

    这一条同时管四件事，因为它们都是「键 vs 句子」的同一类谎言：
    ①行星中文名（`PLANET_ZH` 十个）出现与否必须等于键所载；
    ②星座中文名（`SIGNS_ZH` 十二个）同理；
    ③宫号（`HOUSE_RE` 抓到的每一个）必须恰好是键上那一个，且键上那一个必须被写出来；
    ④相位条目还必须相位词恰好只等于键上那个类型（五个词互相不是子串，所以能逐词判）。
    """
    family, arg = key_parts(key)
    text = WESTERN.entries[key]
    problems: list[str] = []

    # 键上带的是英文名，而文中出现的是中文名，对账必须先过 `planet_zh()` 翻译——直接拿
    # 英文名表判 `zh in named_planets` 会把每一条都判成「键上没有」。两侧同用 planet_zh()：
    # 文中出现别的行星名时报的是「该名字在文中」而不是键的英文名。
    named_planets_zh = {planet_zh(arg["planet"])} if arg.get("planet") is not None else set()
    if family == "aspect":
        named_planets_zh |= {planet_zh(arg["other"])}  # type: ignore[arg-type]
    for zh in PLANET_ZH:
        if (zh in text) != (zh in named_planets_zh):
            problems.append(f"行星「{zh}」在文中={zh in text}，键上={zh in named_planets_zh}")
    if arg.get("planet") is not None and family != "aspect":
        if planet_zh(arg["planet"]) not in text:  # type: ignore[arg-type]
            problems.append(f"文中没写自己的行星名「{planet_zh(arg['planet'])}」")
    if family == "aspect":
        words = [word for word in ASPECT_ZH.values() if word in text]
        if words != [ASPECT_ZH[arg["type"]]]:
            problems.append(f"相位词应当只有「{ASPECT_ZH[arg['type']]}」，实为 {words}")
        if PLANET_NAMES.index(arg["planet"]) > PLANET_NAMES.index(arg["other"]):
            problems.append("相位键的行星次序与 PLANETS 相反（G32：引擎只按 planet1<planet2 出相位）")

    named_signs = ({arg["sign"]} if "sign" in arg else set()) | (
        {arg["sign"]} if family == "node_sign" else set()
    )
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
    平行数组就够（`engines/western.py:42-43`），所以没有放过它的理由。`element`/`modality`
    两族反过来：它们自己的键就是那格，必须正说自己那一格且不提另一类。
    """
    family, arg = key_parts(key)
    text = WESTERN.entries[key]
    said_elements = [word for word in ELEMENT_ZH.values() if word in text]
    said_modalities = [word for word in MODALITY_ZH.values() if word in text]
    problems: list[str] = []
    if len(said_elements) > 1:
        problems.append(f"一句里出现两个元素词 {said_elements}")
    if len(said_modalities) > 1:
        problems.append(f"一句里出现两个形态词 {said_modalities}")
    if family == "element":
        if said_elements != [ELEMENT_ZH[arg["element"]]]:
            problems.append(f"元素小节须正说「{ELEMENT_ZH[arg['element']]}」，实为 {said_elements}")
        if said_modalities:
            problems.append("元素小节不许说形态")
    elif family == "modality":
        if said_modalities != [MODALITY_ZH[arg["modality"]]]:
            problems.append(f"形态小节须正说「{MODALITY_ZH[arg['modality']]}」，实为 {said_modalities}")
        if said_elements:
            problems.append("形态小节不许说元素")
    elif "sign" in arg:
        sign = arg["sign"]
        want_element = ELEMENT_ZH[SIGN_TO_ELEMENT[sign]]
        want_modality = MODALITY_ZH[SIGN_TO_MODALITY[sign]]
        if said_elements and said_elements != [want_element]:
            problems.append(f"{sign} 的元素是「{want_element}」，文中说 {said_elements}")
        if said_modalities and said_modalities != [want_modality]:
            problems.append(f"{sign} 的形态是「{want_modality}」，文中说 {said_modalities}")
    elif said_elements or said_modalities:
        problems.append("键里没有星座，不许主张元素/形态")
    assert not problems, f"{key}: {problems}"


def test_roster_counts_and_no_key_outside_universe() -> None:
    """批次花名册（族内不许多建）+ 键不外溢（族名拼错、参数越界当场红）。

    两道并一条是有意的：它们判的是同一件事的两面——多建的键一定落在 `universe()` 里或外面，
    只数数量会放过「族数对但键写歪」，只比全集会放过「全集内多建一条同族的键」。
    """
    from collections import Counter

    counts = Counter(key_parts(key)[0] for key in WESTERN.entries)
    assert {family: counts.get(family, 0) for family in ROSTER_TARGETS} == ROSTER_TARGETS, counts
    assert set(WESTERN.entries) <= WESTERN.universe(), sorted(set(WESTERN.entries) - WESTERN.universe())


def test_the_aggregation_has_no_key_collision() -> None:
    """`{**a, **b, **c}` 静默覆盖：三张分表的键必须两两不相交，且合起来一条不许多一条不许少。

    覆盖后的失败形状是 `len(WESTERN_READINGS)` 变小而 `universe()` 不动，工厂那条只能报
    「缺某些键」，报不出「为什么缺」——本条把根因直接说出来。
    """
    placement = set(western_plain_placement.WESTERN_PLACEMENT_READINGS)
    small = set(western_plain.WESTERN_SMALL_READINGS)
    aspect = set(western_plain_aspect.WESTERN_ASPECT_READINGS)
    assert not (placement & small), sorted(placement & small)
    assert not (placement & aspect), sorted(placement & aspect)
    assert not (small & aspect), sorted(small & aspect)
    assert len(western_plain.WESTERN_READINGS) == len(placement) + len(small) + len(aspect)


def test_no_two_entries_share_the_same_sentence() -> None:
    """重复句门：两颗星落同一宫、两对行星成同一相位，不许共用逐字相同的句子。

    只判逐字相同，不判「语义相近」——后者是形状盲的正则做不到的事（spec §7 已承认措辞筛
    是形状盲的），强行机检会把合法的同族句式误红。同义重复由评审逐段读。
    """
    from collections import Counter

    duplicated = [text for text, count in Counter(WESTERN.entries.values()).items() if count > 1]
    assert not duplicated, duplicated


def test_the_key_builders_are_the_only_key_source() -> None:
    """十个构造器不补零、带族名（spec §5.3 的键式），且族名与 `key_parts` 的十族一一对应。"""
    assert western_plain.planet_sign_key("Sun", "Aries") == "western.planet_sign.Sun.Aries"
    assert western_plain.planet_house_key("Sun", 7) == "western.planet_house.Sun.7"
    assert western_plain.aspect_key("Sun", "Moon", "conjunction") == "western.aspect.Sun.Moon.conjunction"
    assert western_plain.axis_sign_key("MC", "Capricorn") == "western.axis_sign.MC.Capricorn"
    assert western_plain.node_sign_key("Aquarius") == "western.node_sign.Aquarius"
    assert western_plain.node_house_key(6) == "western.node_house.6"
    assert western_plain.house_theme_key(10) == "western.house_theme.10"
    assert western_plain.element_key("fire") == "western.element.fire"
    assert western_plain.modality_key("fixed") == "western.modality.fixed"
    assert western_plain.retrograde_key("Mercury") == "western.retrograde.Mercury"


def test_sections_and_openers_cover_the_declared_shape() -> None:
    """八个小节标题、十条开篇句、两条空态分支三者的对账（spec §6 的 G15 续用 + R53）。

    `WESTERN.openers` 的键必须恰好是 `WESTERN_SECTION_TITLES` 的八个键并上
    `WESTERN_NONE_BRANCHES` 的两个值——少一条，空触发的那段就承诺引擎给不出的话；
    多一条，就是永远印不出来的死字。标题另走一套口径：它是 `<h3>` 不是句子，
    所以要求「≤8 字、不含「你」、不含「。」、不含 `_FORBIDDEN_FOR_TITLES`」——那张表是
    `FORBIDDEN` 的超集（另加 `（` `）` `、`），与开篇句的四项口径分开。
    """
    expected_openers = set(western_plain.WESTERN_SECTION_TITLES) | set(western_plain.WESTERN_NONE_BRANCHES.values())
    assert set(western_plain.WESTERN_OPENERS) == expected_openers
    assert set(western_plain.WESTERN_NONE_BRANCHES) == {"aspect", "retrograde"}
    assert len(western_plain.WESTERN_SECTION_TITLES) == 8
    for section, title in western_plain.WESTERN_SECTION_TITLES.items():
        assert 0 < len(title) <= 8, (section, title)
        assert "你" not in title and "。" not in title, (section, title)
        assert not [token for token in _FORBIDDEN_FOR_TITLES if token in title], (section, title)
    for section, text in western_plain.WESTERN_OPENERS.items():
        assert frame_violations("western", text) == [], (section, text)


def test_the_source_string_is_a_provenance_string_not_a_sentence() -> None:
    """出处串不进工厂遍历（它不是白话句），所以禁字这一半由本文件自守（先例：卡巴拉同名门）。

    `FORBIDDEN` 含「；」，而 spec §4 给的草稿串里就有「；」——本计划按 spec §4 自己的口径
    「文案与门冲突时改文案」重写成两句（偏差表第 18 行）。第二道 `不出现宫头` 是把偏差 17 的
    冲突钉成机器：出处串不许声称转述了它没建的键族。
    """
    from tests.plain_wording import FORBIDDEN

    source = western_plain.WESTERN_PLAIN_SOURCE
    for token in FORBIDDEN:
        assert token not in source, token
    assert "《" not in source and "依" not in source, source
    assert "宫头" not in source and "南交" not in source, source
    assert source.startswith("平台自撰的通行教义转述表"), source
    assert source.endswith("。"), source
