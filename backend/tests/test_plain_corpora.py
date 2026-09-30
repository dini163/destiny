"""白话语料的参数化机检工厂（多系统白话 spec §4、§11）。

工厂只吃 `PLAIN_CORPORA`，所以新系统登记一行就多跑一张表，测试本身不改。两种口径
（spec 裁定 R6）：槽位词表查禁字与非空，其余条目查 G1 全契约——把「≥40 字 + 含你 +
恰一。」套在「自我与生命方向」这种名词短语上是把词表当判语检查，假红之后人会把整条
闸放松，那是更坏的失败。

键全集闸管三个方向的漏法：少建（上线后命中缺键才 KeyError）、多建（漂到引擎永远
不触发的键上，是没人校对得到的死字）、以及「键在表里但进不了输出」——最后那一类
工厂不越权猜各系统的分带语义，由各系统自己的装配测试钉（spec §4 第 3 条）。

条目口径住在 `wording_violations` 而不是测试体里：`BAZI.slot_prefixes` 是默认空集，
槽位分支在参数化用例里今天一条也没被执行过（Task 2 评审裁定 R21），抽成可调用物才让本文件
末尾那几条自测真走这条分支。自测吃的是本文件自造的最小 corpus（同
`tests/test_plain_compose.py` 的夹具做法——那是闸自己的输入样例，不是假命盘或假响应，
AGENTS.md §9 不拦这个），而不是把分支体抄第二遍。
"""

import re
import pytest

from app.engines.plain_compose import PlainCorpus, is_slot_key
from app.engines.plain_corpora import PLAIN_CORPORA

CORPORA = list(PLAIN_CORPORA.values())
SYSTEMS = [corpus.system for corpus in CORPORA]

#: 机检禁字集逐字取自第一期 spec §3 第 2 条：「（《」与「』」是出处引用标记，「；」是
#: 拼接残留。「则」「之」同条只列为**风格**要求，不进机检——单字黑名单会连带打死
#: 「规则」「之前」，红得一派无辜（第一期控制器裁定 R3，本表沿用同一口径）。
FORBIDDEN = ("；", "（《", "』")

#: 槽位词条是名词短语，不许自带结论（spec §5 规则 5：判断只能来自词条自身之外的
#: 档位收尾句，而槽位词条不参与收尾）。「。」同禁：槽位文本是被嵌在句子中间的，
#: 自带句号会把一句白话劈成两句，正好破坏装配器唯一的标点契约。
SLOT_FORBIDDEN = (*FORBIDDEN, "吉", "凶", "宜", "忌", "你", "{", "}", "\n", "。")

_PLACEHOLDER = re.compile(r"\{[a-z][a-z0-9_]*\}")

ENTRY_IDS = [f"{corpus.system}:{key}" for corpus in CORPORA for key in sorted(corpus.entries)]
ENTRY_KEYS = [(corpus, key) for corpus in CORPORA for key in sorted(corpus.entries)]
#: 框架句用例按 (系统, 小节, 句子) 三元组参数化：`frame{i}` 那种位置编号在 T4/T6 往
#: openers/closers 里追加句子后会整体位移，红的那条报的不再是它自己。
FRAME_SENTENCES = [
    (corpus.system, section, text)
    for corpus in CORPORA
    for section, text in [*corpus.openers.items(), *(corpus.closers or {}).items()]
]


def test_at_least_one_corpus_is_registered() -> None:
    """登记处不许空跑：空 dict 会让下面每条参数化测试全绿而什么也没检查。"""
    assert CORPORA, "PLAIN_CORPORA 是空的，工厂在假绿"
    assert len(CORPORA) == len(set(SYSTEMS)), "同一系统登记了两个 corpus"
    # 真失败模式不是「数出两个同系统」而是**键覆盖**：登记形状是字典字面量里的
    # `X.system: X`，两行 system 相同时 Python 静默留最后一行，前一张表就此掉出闸外，
    # 而上一条「计数 == 去重计数」照样成立。故键必须逐个等于它所指向 corpus 的 system。
    assert all(key == corpus.system for key, corpus in PLAIN_CORPORA.items())


@pytest.mark.parametrize("corpus", CORPORA, ids=SYSTEMS)
def test_entry_keys_mirror_the_source_tables_exactly(corpus) -> None:
    assert set(corpus.entries) == corpus.universe()


@pytest.mark.parametrize("corpus", CORPORA, ids=SYSTEMS)
def test_universe_is_reproducible_and_non_empty(corpus) -> None:
    assert corpus.universe() == corpus.universe()
    assert corpus.universe(), f"{corpus.system} 的键全集算出来是空表，多半是源表改名了"


@pytest.mark.parametrize("corpus", CORPORA, ids=SYSTEMS)
def test_openers_are_non_empty_and_never_slot_keys(corpus) -> None:
    """名字即判据：这条只钉「有开篇句」与「开篇句的键不落在槽位词表上」，不查覆盖面。
    「覆盖面」在这里无从查起——小节名单由各系统的装配测试钉（spec §4 第 3 条）。"""
    assert corpus.openers, f"{corpus.system} 没有开篇句"
    for section in corpus.openers:
        assert not is_slot_key(corpus, section)


def wording_violations(corpus, key: str) -> list[str]:
    """一条白话条目的措辞违例清单，空表即合规；判定次序：先禁字，再按槽位/整句分流。

    返回违例而不是直接 assert，是为了让参数化用例与本文件末尾的槽位自测走同一份代码
    （R21）：口径分流那条分支在生产登记表上今天无人触发，把分支体抄第二遍来「补覆盖」
    只会多出一个会漂的副本。
    """
    text = corpus.entries[key]
    violations: list[str] = []
    for token in FORBIDDEN:
        if token in text:
            violations.append(f"FORBIDDEN 禁字「{token}」")
    if is_slot_key(corpus, key):
        if not text.strip():
            violations.append("槽位词条非空契约破")
        for token in SLOT_FORBIDDEN:
            if token in text:
                violations.append(f"SLOT_FORBIDDEN 禁字「{token}」")
        if len(text) > 20:
            violations.append(f"槽位词条 {len(text)} 字，超过 20 字上限")
        return violations
    # 条目可以合法携带 `{slot}`（T6 的 5 条相位框架句就带 {a}/{b}），所以长度按剥掉占位符的
    # 正体算，而标点契约按原文算。
    body = _PLACEHOLDER.sub("", text)
    if len(body) < 40:
        violations.append(f"剥掉占位符后正体 {len(body)} 字，不足 40 字")
    if not (text.endswith("。") and text.count("。") == 1):
        violations.append("整句须以唯一一个「。」收尾")
    if "你" not in text:
        violations.append("整句缺「你」")
    return violations


@pytest.mark.parametrize("corpus, key", ENTRY_KEYS, ids=ENTRY_IDS)
def test_every_entry_meets_the_wording_contract(corpus, key) -> None:
    assert wording_violations(corpus, key) == []


@pytest.mark.parametrize(
    "system, section, text",
    FRAME_SENTENCES,
    ids=[f"{system}:{section}" for system, section, _text in FRAME_SENTENCES],
)
def test_frame_sentences_meet_the_same_contract(system, section, text) -> None:
    assert len(text) >= 20, text
    assert text.endswith("。") and text.count("。") == 1, text
    assert "你" in text, text
    for token in FORBIDDEN:
        assert token not in text, (text, token)


@pytest.mark.parametrize("corpus", CORPORA, ids=SYSTEMS)
def test_no_corpus_declares_both_groupings_and_no_closer_vocabulary_is_shared(corpus) -> None:
    assert corpus.grouping in ("band", "keep")
    if corpus.closers is not None:
        assert not (set(corpus.closers) & set(corpus.entries)), f"{corpus.system} 的档位句混进条目表了"


#: 闸自身的夹具：一张声明了 slot_prefixes 的最小 corpus。它不进 `PLAIN_CORPORA`（不进生产
#: 口径），只让 `wording_violations` 的槽位分支被真的执行过一遍——这是闸的输入样例，不是
#: 假命盘、不是假响应，与 `tests/test_plain_compose.py` 那两张自造 corpus 同一条路子。
SLOT_PREFIX = "demo.axis."
GATE_ENTRIES = {
    SLOT_PREFIX + "core": "自我与生命方向",
    SLOT_PREFIX + "verdict": "自我与生命方向呈吉象",
    SLOT_PREFIX + "long": "自我与生命方向在这一段上呈现出的是一种缓慢而稳定的",
    SLOT_PREFIX + "sentence": "你在这一段上先感到的是顺。",
    "demo.plain.short": "你在这一段上面的顺很短。",
}
GATE_DEMO = PlainCorpus(
    system="gate_demo",
    entries=GATE_ENTRIES,
    openers={},
    closers=None,
    grouping="keep",
    universe=lambda: set(GATE_ENTRIES),
    slot_prefixes=frozenset({SLOT_PREFIX}),
)


def test_slot_caliber_passes_a_clean_noun_phrase() -> None:
    """R6 换口径要放过的正是这个形状：名词短语、无标点、无结论。"""
    assert wording_violations(GATE_DEMO, SLOT_PREFIX + "core") == []


def test_slot_caliber_reports_a_noun_phrase_that_carries_its_own_verdict() -> None:
    assert wording_violations(GATE_DEMO, SLOT_PREFIX + "verdict") == ["SLOT_FORBIDDEN 禁字「吉」"]


def test_slot_caliber_reports_a_noun_phrase_over_the_twenty_character_cap() -> None:
    text = GATE_DEMO.entries[SLOT_PREFIX + "long"]
    assert len(text) == 25, "夹具本身越界才算在测闸，否则这条红了是在测字符串"
    assert wording_violations(GATE_DEMO, SLOT_PREFIX + "long") == [f"槽位词条 {len(text)} 字，超过 20 字上限"]


def test_slot_caliber_reports_a_sentence_as_forbidden_tokens_not_as_a_short_entry() -> None:
    """槽位口径不许放过整句：含「你」与自带「。」都是 SLOT_FORBIDDEN，而不是「太短」。"""
    assert wording_violations(GATE_DEMO, SLOT_PREFIX + "sentence") == [
        "SLOT_FORBIDDEN 禁字「你」",
        "SLOT_FORBIDDEN 禁字「。」",
    ]


def test_sentence_caliber_still_bites_on_an_entry_that_is_too_short() -> None:
    text = GATE_DEMO.entries["demo.plain.short"]
    assert len(text) == 12, "夹具本身越界才算在测闸，否则这条红了是在测字符串"
    assert wording_violations(GATE_DEMO, "demo.plain.short") == [
        f"剥掉占位符后正体 {len(text)} 字，不足 40 字"
    ]
