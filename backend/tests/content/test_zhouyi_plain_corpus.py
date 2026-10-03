"""周易今译的本地门（丁组 spec §4.2、§4.4、§8）。

这些门**不走 `PLAIN_CORPORA`**：语料分 12 批建，登记行要到 T13 才进工厂，而每一批都
要在落地当次就跑共享口径，所以这里用一张测试侧自造的 `PlainCorpus` 吃
`tests.plain_wording.wording_violations`（同 `tests/test_plain_compose.py` 给闸自造
输入的口径，AGENTS §9 不拦这个——那是闸的输入样例，不是假命盘、不是假响应）。
"""

import re

import pytest

from app.content import zhouyi_text
from app.content.zhouyi_guaci import YONG_CI
from app.content.zhouyi_hexagrams import HEXAGRAM_BY_NUMBER
from app.content.zhouyi_plain import (
    ZHOUYI_ANCHORS,
    ZHOUYI_PLAIN_SOURCE,
    ZHOUYI_READINGS,
    gua_ci_key,
    yao_ci_key,
    yong_ci_key,
)
from app.engines.plain_compose import PlainCorpus
from tests.plain_wording import advice_hits, wording_violations

#: 本批已覆盖的卦号。T2-T12 每批往里加自己那 5-6 卦，一条也不许多。
COVERED: tuple[int, ...] = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64,)

#: 原文的六个断词与八个升格串（spec §4.4）。
VERDICT_WORDS = ("吉", "凶", "厉", "悔", "吝", "咎")
ESCALATION = ("大吉", "小吉", "凶险", "注定", "必然", "一定", "天意", "命定")
_QUOTED = re.compile(r"「[^」]*」")


def _plain_corpus() -> PlainCorpus:
    return PlainCorpus(
        system="zhouyi",
        entries=ZHOUYI_READINGS,
        openers={},
        closers=None,
        grouping="keep",
        universe=lambda: set(ZHOUYI_READINGS),
    )


def _built_keys() -> list[str]:
    return sorted(ZHOUYI_READINGS)


def test_the_three_key_builders_are_the_only_key_source() -> None:
    """键构造器不补零、带卦号（spec §4.3 三条判据里的两条）。"""
    assert gua_ci_key(1) == "zhouyi.gua.1"
    assert yao_ci_key(1, 6) == "zhouyi.yao.1.6"
    assert yong_ci_key(2) == "zhouyi.yong.2"


def test_every_built_anchor_equals_the_live_source_text() -> None:
    """spec §4.2 门 1：源表改一个字，这里就红。逐键报。"""
    for key in _built_keys():
        assert key in ZHOUYI_ANCHORS, f"{key} 有今译却没 anchor"
        kind, rest = key[len("zhouyi."):].split(".", 1)
        if kind == "gua":
            assert ZHOUYI_ANCHORS[key] == zhouyi_text.gua_ci(int(rest)), key
        elif kind == "yong":
            assert ZHOUYI_ANCHORS[key] == zhouyi_text.yong_ci(int(rest))[1], key
        else:
            number, position = (int(x) for x in rest.split("."))
            assert ZHOUYI_ANCHORS[key] == zhouyi_text.yao_ci(number, position), key


def test_covered_hexagrams_are_complete_no_row_missing() -> None:
    """批次花名册：`COVERED` 里的每一卦必须卦辞 + 六爻（乾坤再加用）齐。"""
    expected = set()
    for number in COVERED:
        expected.add(gua_ci_key(number))
        expected |= {yao_ci_key(number, p) for p in range(1, 7)}
        if number in YONG_CI:
            expected.add(yong_ci_key(number))
    assert set(ZHOUYI_READINGS) == expected
    assert set(ZHOUYI_ANCHORS) == expected


@pytest.mark.parametrize("key", _built_keys())
def test_every_plain_text_meets_the_shared_factory_contract(key) -> None:
    """≥40 字 / 恰一「。」 / 含「你」/ 无「；」（spec §4.1 的契约来源是工厂，不是本文件）。"""
    assert wording_violations(_plain_corpus(), key) == []


@pytest.mark.parametrize("key", _built_keys())
def test_verdict_words_are_quoted_and_never_escalated(key) -> None:
    """spec §4.4 三条一次判完：引用、不漏译、不升格。"""
    text = ZHOUYI_READINGS[key]
    naked = _QUOTED.sub("", text)
    for word in VERDICT_WORDS:
        assert word not in naked, f"{key} 的今译在引号外写了断词「{word}」"
        source = ZHOUYI_ANCHORS[key]
        if word in source:
            assert f"「{word}」" in text, f"{key} 源文有「{word}」而今译没引用它"
    for word in ESCALATION:
        assert word not in text, f"{key} 升格了断词：{word}"


@pytest.mark.parametrize("key", _built_keys())
def test_advice_caliber_runs_on_the_text_outside_quotes(key) -> None:
    """spec §4.4 末段：剥掉 `「…」` 才跑既有建议词口径，不改工厂、不改表。"""
    naked = _QUOTED.sub("", ZHOUYI_READINGS[key])
    assert advice_hits(naked) == []


def test_the_plain_table_never_leaks_the_source_text_into_entries() -> None:
    """spec §4.2 门 2：`entries` 里只准有今译。源文既不满 40 字也不含「你」，
    混进去就是让闸去检查古文——这条用「anchor 与今译两两不等」把门 2 钉住。"""
    for key in _built_keys():
        assert ZHOUYI_READINGS[key] != ZHOUYI_ANCHORS[key], key
        assert not ZHOUYI_READINGS[key].startswith(ZHOUYI_ANCHORS[key][:6]), key


def test_every_line_reading_opens_with_its_own_yao_title() -> None:
    """spec §4.1 段② 的骨架：每一条爻辞今译都以本爻的爻题起头，题从卦画表现算，
    不写字面量清单（T2/T3 实测「上九」被写成「居奇位」这一类自相矛盾，就是这条钉住的）。"""
    for key in _built_keys():
        if not key.startswith("zhouyi.yao."):
            continue
        number, position = (int(x) for x in key[len("zhouyi.yao."):].split("."))
        expected = zhouyi_text.line_name(
            position, HEXAGRAM_BY_NUMBER[number].lines[position - 1] == 1
        )
        assert ZHOUYI_READINGS[key].startswith(expected), (
            f"{key} 的今译以 {ZHOUYI_READINGS[key][:2]} 起头，本爻的题是 {expected}"
        )


#: 段② 里能对卦画验算的句式。「阳位/阴位」是「奇位/偶位」的同一说法（阳位 = 奇位）；判语只认
#: 与这半句同一个小句里的「得正/失正」——很多行只报位置不下判，所以判语组是可缺的。
_POSITION_CLAIM = re.compile(r"([阳阴])爻居([奇偶阳阴])位")
_VERDICT = re.compile(r"(得正|失正)")


def test_every_stated_position_claim_matches_the_line_binary() -> None:
    """极性、位的奇偶、得正/失正三样都从 `Hexagram.lines` 现算对一遍（spec §4.1：段② 只许说
    卦画里**已有**的结构，说反了就是往用户眼前塞一条错的位置事实）。"""
    for key in _built_keys():
        if not key.startswith("zhouyi.yao."):
            continue
        number, position = (int(x) for x in key[len("zhouyi.yao."):].split("."))
        is_yang = HEXAGRAM_BY_NUMBER[number].lines[position - 1] == 1
        is_odd = position % 2 == 1
        expected_verdict = "得正" if is_yang == is_odd else "失正"
        for clause in ZHOUYI_READINGS[key].split("，"):
            match = _POSITION_CLAIM.search(clause)
            if match is None:
                continue
            polarity, parity = match.groups()
            assert polarity == ("阳" if is_yang else "阴"), (
                f"{key} 写成{polarity}爻，卦画这一爻是{'阳' if is_yang else '阴'}"
            )
            assert (parity in ("奇", "阳")) == is_odd, (
                f"{key} 把第 {position} 位（{'奇' if is_odd else '偶'}位）说成{parity}位"
            )
            stated = _VERDICT.search(clause)
            if stated:
                assert stated.group(1) == expected_verdict, (
                    f"{key} 说 {stated.group(1)}，按卦画应是 {expected_verdict}"
                )


#: 今译里自称世/应的句式全站只有两种（T6/T7 实跑 67 条：33 世、34 应），所以能逐条对列复算。
_SHI_YING_CLAIM = re.compile(r"它是这一卦的(世爻|「应爻」)")


def test_every_stated_shi_ying_claim_matches_the_najia_columns() -> None:
    """段② 剩下那一半：京房世应住在 `Hexagram.shi` / `.ying`（`zhouyi_hexagrams.py:123-124`，由
    `SHI_BY_GENERATION` × `_ying_of` 现算），所以「它是这一卦的世爻」这句话是**可机检的事实**，
    不是只能人读的语气。说错一格就是往用户眼前塞一条错的卦位身份。"""
    for key in _built_keys():
        if not key.startswith("zhouyi.yao."):
            continue
        number, position = (int(x) for x in key[len("zhouyi.yao."):].split("."))
        hexagram = HEXAGRAM_BY_NUMBER[number]
        for claimed in _SHI_YING_CLAIM.findall(ZHOUYI_READINGS[key]):
            if claimed == "世爻":
                assert position == hexagram.shi, (
                    f"{key} 自称世爻，这一卦（{hexagram.name_zh}·{hexagram.generation}）世在 {hexagram.shi}"
                )
            else:
                assert position == hexagram.ying, (
                    f"{key} 自称「应爻」，这一卦（{hexagram.name_zh}·{hexagram.generation}）应在 {hexagram.ying}"
                )


#: 断词清点句的五种写法，全站实测覆盖得完（415 键 = 计数 54 / 零自述 3 / 单断词 15 /
#: 不下断词 50 / 点名句 200，共 322 条断言）。口径同 `VERDICT_WORDS`：只数那六个字在
#: anchor 里的**出现次数**（`无咎` 记 1、`贞吉` 记 1、`悔厉吉` 记 3）。
#: 钉不住的两种写法有意留在门外：「它给的不是断词而是……」（与 `不给断词` 不同形，
#: 强并会把「不是」读成否定式清点）与裸量词「它两处给顺路」（宾语是利字，不是断词）。
_VERDICT_COUNT = re.compile(r"([一两二三四五六])个断词")
_VERDICT_ZERO = re.compile(r"一个断词也不[给说]")
_VERDICT_SINGLE = re.compile(r"断词只(?:有|出现|那|这)[^，。]{0,6}一[个处次]")
_VERDICT_NONE = re.compile(r"不[下给]断词|没有断词")
_VERDICT_NAMED = re.compile(r"断词[^，。「」]{0,6}「([吉凶厉悔吝咎])」")
_CN_COUNT = {"一": 1, "两": 2, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6}


def _verdict_tally(anchor: str) -> int:
    return sum(anchor.count(word) for word in VERDICT_WORDS)


def test_every_stated_verdict_count_matches_the_anchor() -> None:
    """「这一爻两个断词」是**可验算的清点句**：数错就是当着用户的面数错原文，把亨称作
    断词就是替原文多下一句判词（T8/T9 评审揪出的正是这一类）。零自述、单断词、不下断词
    三种写法在这里各自独立钉一次实数——先前的门只把零自述当计数的豁免，自己一条也不主张，
    所以一行满口断词照样可以自称「一个断词也不给」（T10/T11 评审 I-3）。"""
    for key in _built_keys():
        anchor = ZHOUYI_ANCHORS[key]
        reading = ZHOUYI_READINGS[key]
        real = _verdict_tally(anchor)
        zero_spans = [m.span() for m in _VERDICT_ZERO.finditer(reading)]
        for m in _VERDICT_COUNT.finditer(reading):
            claimed = (
                0 if any(s <= m.start() < e for s, e in zero_spans) else _CN_COUNT[m.group(1)]
            )
            assert claimed == real, (
                f"{key} 说「{m.group(0)}」，anchor「{anchor}」里断词实数 {real}"
            )
        for rx, want, label in (
            (_VERDICT_ZERO, 0, "零自述"),
            (_VERDICT_SINGLE, 1, "单断词自述"),
            (_VERDICT_NONE, 0, "不下断词"),
        ):
            for m in rx.finditer(reading):
                assert real == want, (
                    f"{key} 的{label}「{m.group(0)}」，anchor「{anchor}」里断词实数 {real}"
                )


def test_every_named_verdict_word_appears_in_the_anchor() -> None:
    """点名句（「原断词是「吉」」「断词只有一个「凶」」）报出的那个字必须真在原文里。
    它只查**存在**，不查唯一性——唯一性归上一条的「单断词自述」；这一条管更硬的那错：
    报一个原文里根本没有的断词，等于替原文凭空造一句判词。"""
    for key in _built_keys():
        anchor = ZHOUYI_ANCHORS[key]
        for m in _VERDICT_NAMED.finditer(ZHOUYI_READINGS[key]):
            assert m.group(1) in anchor, (
                f"{key} 点名「{m.group(0)}」，anchor「{anchor}」里没有 {m.group(1)} 字"
            )


#: 「N个字」只钉主语是整条的那一式（卦辞/这一爻 + 只 + 数词）。「末尾多给两个字」
#: 「只留一个字说可以食」数的是末句那半条，基准不同，硬并会误红——它们由评审员人核。
_CHAR_COUNT = re.compile(r"(?:卦辞|这一爻)只[有留]?([一两二三四五六])个字")
#: 卦辞行里的结构清点句：数量词紧跟得正/失正/失位，基准是全卦六爻（`lines` 底向上，
#: 阳居奇位、阴居偶位为得正）。这是段② 唯一能对整卦复算的句式，也是 T10/T11 评审 I-2
#: 那条「两处失位」（归妹实为四处）唯一的机器兜底。
_POSITION_TALLY = re.compile(r"([一两二三四五六])处(得正|失正|失位)")
_PUNCTUATION = ("，", "。", "：", "；", "、")


def test_every_stated_character_count_matches_the_anchor_length() -> None:
    """「兑卦的卦辞只有四个字」是可点数的：原文去掉标点剩几个字就是几个。句数复测 =
    `cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "import re
    from app.content.zhouyi_plain import ZHOUYI_READINGS as R;print(sum(len(re.findall(
    r'(?:卦辞|这一爻)只[有留]?[一两二三四五六]个字', v)) for v in R.values()))"`。
    T10/T11 评审实跑数出 2 句点错（`gua.58` 亨，利贞。= 三、`yao.6.5` 讼，元吉。= 三），
    而旧的清点门只看断词，看不见它。"""
    for key in _built_keys():
        anchor = ZHOUYI_ANCHORS[key]
        for m in _CHAR_COUNT.finditer(ZHOUYI_READINGS[key]):
            real = len([c for c in anchor if c not in _PUNCTUATION])
            assert _CN_COUNT[m.group(1)] == real, (
                f"{key} 说「{m.group(0)}」，anchor「{anchor}」去掉标点是 {real} 字"
            )


def test_every_stated_position_tally_matches_the_line_binaries() -> None:
    """「N处失位／得正」数的是全卦六爻里站错与站对的位置，能从 `Hexagram.lines` 现算，
    所以这句话同样是事实句而非评述。基准只有一处含糊不得：整卦，不是下卦也不是某爻
    上下——本门按整卦钉，别的读法不许用这个句式写。"""
    for key in _built_keys():
        number = int(key.split(".")[2])
        hexagram = HEXAGRAM_BY_NUMBER[number]
        misplaced = sum(
            1
            for position in range(1, 7)
            if bool(hexagram.lines[position - 1]) != (position % 2 == 1)
        )
        for m in _POSITION_TALLY.finditer(ZHOUYI_READINGS[key]):
            real = misplaced if m.group(2) != "得正" else 6 - misplaced
            assert _CN_COUNT[m.group(1)] == real, (
                f"{key} 说「{m.group(0)}」，{hexagram.name_zh} 卦画里失位 {misplaced} 爻、"
                f"得正 {6 - misplaced} 爻"
            )


def test_plain_source_line_says_it_is_a_retelling_not_an_original() -> None:
    """出处串自述身份（同 `test_tarot_zh_corpus.py` 里那条译表自述的先例）。"""
    assert ZHOUYI_PLAIN_SOURCE
    assert "今译" in ZHOUYI_PLAIN_SOURCE, ZHOUYI_PLAIN_SOURCE
    for banned in ("；", "（《", "』"):
        assert banned not in ZHOUYI_PLAIN_SOURCE
