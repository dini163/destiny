"""Corpus invariants: the BaZi interpretive text is curated reference data, never generated.

Counts are pinned so a dropped or invented entry fails loudly, in the same spirit
as the Zhouyi 卦辞/爻辞 counts in tests/golden/test_zhouyi_golden.py.
"""

import pytest

from app.content.bazi_shishen import TEN_GOD_MEANING, TEN_GOD_COUNT, ten_god_meaning

# 出处写到章（《渊海子平·论劫财》），所以前缀不含右书名号 —— 只认得书。
SOURCES = ("《渊海子平", "《三命通会", "《滴天髓", "《协纪辨方书")

TEN_GOD_CHAPTERS = {
    "《渊海子平·论兄弟姊妹》",  # 比肩
    "《渊海子平·论劫财》",
    "《渊海子平·论食神》",
    "《渊海子平·论伤官》",
    "《渊海子平·论偏财》",
    "《渊海子平·论正财》",
    "《渊海子平·论七杀》",
    "《渊海子平·正官论》",
    "《渊海子平·论倒食》",  # 偏印
    "《渊海子平·论印绶》",  # 正印
}


def test_ten_god_corpus_covers_exactly_ten_gods() -> None:
    assert TEN_GOD_COUNT == 10
    assert set(TEN_GOD_MEANING) == {
        "比肩", "劫财", "食神", "伤官", "偏财", "正财", "七杀", "正官", "偏印", "正印",
    }


def test_every_corpus_entry_is_citable() -> None:
    for item in TEN_GOD_MEANING.values():
        assert any(item.source.startswith(prefix) for prefix in SOURCES), item


def test_each_ten_god_is_cited_to_its_own_chapter() -> None:
    """Sources are the ten 渊海子平 chapters, not a generic 赋.

    比肩 and 偏印 have no dedicated chapter in either allowed classic, so they are
    cited to 论兄弟姊妹 and 论倒食 —— the chapters that do define them.
    """
    sources = {item.source for item in TEN_GOD_MEANING.values()}
    assert sources == TEN_GOD_CHAPTERS
    assert TEN_GOD_MEANING["正印"].source.endswith("论印绶》")


def test_ten_god_meaning_is_not_a_placeholder() -> None:
    """Every 释义 must survive the transcription procedure, template text must not leak in."""
    for item in TEN_GOD_MEANING.values():
        assert "本计划" not in item.meaning, item.ten_god
        assert "此处放" not in item.meaning, item.ten_god
        assert len(item.meaning) >= 8, item.ten_god


def test_six_relations_only_use_the_documented_cells() -> None:
    """《渊海子平·六亲总篇》states 男命 for nine gods and 女命 for four; nothing else.

    A key outside that vocabulary means someone filled a gap from general knowledge,
    which spec §3 决策二 forbids.
    """
    for item in TEN_GOD_MEANING.values():
        assert set(item.six_relations) <= {"男命", "女命"}, item.ten_god
        for value in item.six_relations.values():
            assert len(value) >= 3, item.ten_god
    assert TEN_GOD_MEANING["劫财"].six_relations == {}


def test_ten_god_meaning_unknown_god_raises() -> None:
    with pytest.raises(KeyError):
        ten_god_meaning("不存在的神")
