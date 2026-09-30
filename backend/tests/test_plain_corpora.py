"""白话语料的参数化机检工厂（多系统白话 spec §4、§11）。

工厂只吃 `PLAIN_CORPORA`，所以新系统登记一行就多跑一张表，测试本身不改。两种口径
（spec 裁定 R6）：槽位词表查禁字与非空，其余条目查 G1 全契约——把「≥40 字 + 含你 +
恰一。」套在「自我与生命方向」这种名词短语上是把词表当判语检查，假红之后人会把整条
闸放松，那是更坏的失败。

键全集闸管三个方向的漏法：少建（上线后命中缺键才 KeyError）、多建（漂到引擎永远
不触发的键上，是没人校对得到的死字）、以及「键在表里但进不了输出」——最后那一类
工厂不越权猜各系统的分带语义，由各系统自己的装配测试钉（spec §4 第 3 条）。
"""

import re
import pytest

from app.engines.plain_compose import is_slot_key
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
FRAME_SENTENCES = [
    text
    for corpus in CORPORA
    for text in [*corpus.openers.values(), *(corpus.closers or {}).values()]
]


def test_at_least_one_corpus_is_registered() -> None:
    """登记处不许空跑：空 dict 会让下面每条参数化测试全绿而什么也没检查。"""
    assert CORPORA, "PLAIN_CORPORA 是空的，工厂在假绿"
    assert len(CORPORA) == len(set(SYSTEMS)), "同一系统登记了两个 corpus"


@pytest.mark.parametrize("corpus", CORPORA, ids=SYSTEMS)
def test_entry_keys_mirror_the_source_tables_exactly(corpus) -> None:
    assert set(corpus.entries) == corpus.universe()


@pytest.mark.parametrize("corpus", CORPORA, ids=SYSTEMS)
def test_universe_is_reproducible_and_non_empty(corpus) -> None:
    assert corpus.universe() == corpus.universe()
    assert corpus.universe(), f"{corpus.system} 的键全集算出来是空表，多半是源表改名了"


@pytest.mark.parametrize("corpus", CORPORA, ids=SYSTEMS)
def test_openers_cover_the_sections_the_corpus_names(corpus) -> None:
    assert corpus.openers, f"{corpus.system} 没有开篇句"
    for section in corpus.openers:
        assert not is_slot_key(corpus, section)


@pytest.mark.parametrize("corpus, key", ENTRY_KEYS, ids=ENTRY_IDS)
def test_every_entry_meets_the_wording_contract(corpus, key) -> None:
    text = corpus.entries[key]
    for token in FORBIDDEN:
        assert token not in text, (key, token)
    if is_slot_key(corpus, key):
        assert text.strip(), key
        for token in SLOT_FORBIDDEN:
            assert token not in text, (key, token)
        assert len(text) <= 20, (key, len(text))
        return
    body = _PLACEHOLDER.sub("", text)
    assert len(body) >= 40, (key, len(body))
    assert text.endswith("。") and text.count("。") == 1, key
    assert "你" in text, key
    assert not _PLACEHOLDER.search(text[len(text) - 1]), key


@pytest.mark.parametrize("text", FRAME_SENTENCES, ids=[f"frame{i}" for i in range(len(FRAME_SENTENCES))])
def test_frame_sentences_meet_the_same_contract(text) -> None:
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
