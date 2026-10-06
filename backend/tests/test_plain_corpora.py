"""白话语料的参数化机检工厂（多系统白话 spec §4、§11）。

工厂只吃 `PLAIN_CORPORA`，所以新系统登记一行就多跑一张表，测试本身不改——除登记在
`SECTIONLESS` 里的形状例外（无小节系统必须 `openers == {}`）。两种口径
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

import pytest

from app.engines.plain_compose import PlainCorpus, is_slot_key
from app.engines.plain_corpora import PLAIN_CORPORA
from tests.plain_wording import SLOT_FORBIDDEN, frame_violations, wording_violations

CORPORA = list(PLAIN_CORPORA.values())
SYSTEMS = [corpus.system for corpus in CORPORA]

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
    assert all(
        key == corpus.system for key, corpus in PLAIN_CORPORA.items()
    ), "登记键与 corpus.system 不一致，被覆盖的那张表会静默掉出闸外"


@pytest.mark.parametrize("corpus", CORPORA, ids=SYSTEMS)
def test_entry_keys_mirror_the_source_tables_exactly(corpus) -> None:
    assert set(corpus.entries) == corpus.universe()


@pytest.mark.parametrize("corpus", CORPORA, ids=SYSTEMS)
def test_universe_is_reproducible_and_non_empty(corpus) -> None:
    assert corpus.universe() == corpus.universe()
    assert corpus.universe(), f"{corpus.system} 的键全集算出来是空表，多半是源表改名了"


#: 无小节系统名单：白话挂在条目自身、页面上不存在段落容器，因此刻意没有开篇句。
#: 例外必须登记（机制同 `test_architecture.py::CONTENT_STEM_ALIAS` / `BASELINE`：
#: 「例外要写得出名字」才是接口，「放松断言」不是）。名单内要求 `openers == {}`，
#: 两个方向都钉——今天多写一句开篇句也红，因为没人会去渲染它。
#: 复测：`cd backend && grep -n "SECTIONLESS" tests/test_plain_corpora.py`。
SECTIONLESS = {"kabbalah", "zhouyi"}


def test_sectionless_roster_is_the_two_named_exceptions_verbatim() -> None:
    """名单逐字钉（丁组 spec §5：「登记表与名单是两处编辑，忘一处会假绿」）。

    新系统要进名单，必须在这里改一行、把名字留下——静默加进来就是那张表永远没有开篇句
    也没有人问一句为什么。spec 把这条钉放在周易的 corpus 测里，实测搬不过来：`tests/`
    没有 `__init__.py`（复测：`cd backend && ls tests/__init__.py` → 不存在），
    别处 `from tests.test_plain_corpora import SECTIONLESS` 会把 pytest 已经以顶层名
    `test_plain_corpora` 导入过的同一个文件再导入一遍，参数化用例在两个模块名下各跑一次。
    **常量住在哪个文件，逐字钉就住在哪个文件**；周易那一侧的另一半（`ZHOUYI.openers == {}`）
    由 `tests/content/test_zhouyi_plain_corpus.py::test_the_registered_shape_is_sectionless_unclosed_and_unsorted`
    钉。见计划偏差表第 7 行。
    """
    assert SECTIONLESS == {"kabbalah", "zhouyi"}


@pytest.mark.parametrize("corpus", CORPORA, ids=SYSTEMS)
def test_openers_are_non_empty_and_never_slot_keys(corpus) -> None:
    """名字即判据：这条只钉「有小节的公司有开篇句」与「开篇句的键不落在槽位词表上」，不查覆盖面。

    「覆盖面」在这里无从查起——小节名单由各系统的装配测试钉（spec §4 第 3 条）。
    无小节的两家是卡巴拉与周易（卡巴拉 T2 裁定，见多系统计划 G19 表行 7；周易依丁组 spec §5，
    它的今译挂在卦辞行与六条爻行上，页面没有段落容器）。
    """
    if corpus.system in SECTIONLESS:
        assert corpus.openers == {}, f"{corpus.system} 登记为无小节却不空"
    else:
        assert corpus.openers, f"{corpus.system} 没有开篇句"
    for section in corpus.openers:
        assert not is_slot_key(corpus, section)


@pytest.mark.parametrize("corpus, key", ENTRY_KEYS, ids=ENTRY_IDS)
def test_every_entry_meets_the_wording_contract(corpus, key) -> None:
    assert wording_violations(corpus, key) == []


@pytest.mark.parametrize(
    "system, section, text",
    FRAME_SENTENCES,
    ids=[f"{system}:{section}" for system, section, _text in FRAME_SENTENCES],
)
def test_frame_sentences_meet_the_same_contract(system, section, text) -> None:
    """四项口径逐字搬进 `tests.plain_wording.frame_violations`（唯一正主），本条只调它。

    抽取的理由见那份函数自己的 docstring：戊组增量禁串也要管框架句，而 `WESTERN` 在 T1-T14
    刻意不登记（登记行归 T15，2026-10-06 已补），那十四批里工厂的参数化用例看不到它——
    本地门必须能吃同一份口径，抄第二遍就会有
    一处忘记加。用例数与结果对既有登记表逐字节不变（本文件只换了判定住的地方）。
    """
    assert frame_violations(system, text) == [], (section, text)


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
    SLOT_PREFIX + "empty": "",
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


def test_slot_caliber_reports_an_empty_slot_entry() -> None:
    """非空契约（R21 四条判据之一）：槽位文本被嵌在句子里，空词等于装配出一个残句。"""
    text = GATE_DEMO.entries[SLOT_PREFIX + "empty"]
    assert not text.strip(), "夹具本身非空才算在测闸，否则这条红了是在测字符串"
    assert wording_violations(GATE_DEMO, SLOT_PREFIX + "empty") == ["槽位词条非空契约破"]


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
