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
COVERED: tuple[int, ...] = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13,)

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


#: 段② 里唯一能对卦画验算的句式：「阳爻居偶位算失正」。第三组可缺——有些行只说居中不说得正。
_POSITION_CLAIM = re.compile(r"([阳阴])爻居([奇偶])位(?:算(得正|失正))?")


def test_every_stated_position_claim_matches_the_line_binary() -> None:
    """极性、位的奇偶、得正/失正三样都从 `Hexagram.lines` 现算对一遍（spec §4.1：段② 只许说
    卦画里**已有**的结构，说反了就是往用户眼前塞一条错的位置事实）。"""
    for key in _built_keys():
        if not key.startswith("zhouyi.yao."):
            continue
        number, position = (int(x) for x in key[len("zhouyi.yao."):].split("."))
        is_yang = HEXAGRAM_BY_NUMBER[number].lines[position - 1] == 1
        for polarity, parity, verdict in _POSITION_CLAIM.findall(ZHOUYI_READINGS[key]):
            assert polarity == ("阳" if is_yang else "阴"), (
                f"{key} 写成{polarity}爻，卦画这一爻是{'阳' if is_yang else '阴'}"
            )
            assert parity == ("奇" if position % 2 else "偶"), (
                f"{key} 把第 {position} 位说成{parity}位"
            )
            if verdict:
                expected = "得正" if is_yang == (position % 2 == 1) else "失正"
                assert verdict == expected, f"{key} 说 {verdict}，按卦画应是 {expected}"


def test_plain_source_line_says_it_is_a_retelling_not_an_original() -> None:
    """出处串自述身份（同 `test_tarot_zh_corpus.py` 里那条译表自述的先例）。"""
    assert ZHOUYI_PLAIN_SOURCE
    assert "今译" in ZHOUYI_PLAIN_SOURCE, ZHOUYI_PLAIN_SOURCE
    for banned in ("；", "（《", "』"):
        assert banned not in ZHOUYI_PLAIN_SOURCE
