"""Corpus invariants: the BaZi interpretive text is curated reference data, never generated.

Counts are pinned so a dropped or invented entry fails loudly, in the same spirit
as the Zhouyi 卦辞/爻辞 counts in tests/golden/test_zhouyi_golden.py.
"""

import pytest

from app.content.bazi_nayin import NAYIN_MEANING, NAYIN_COUNT, nayin_meaning
from app.content.bazi_shishen import TEN_GOD_MEANING, TEN_GOD_COUNT, ten_god_meaning

# 出处写到章（《渊海子平·论劫财》），所以前缀不含右书名号 —— 只认得书。
SOURCES = ("《渊海子平", "《三命通会", "《滴天髓", "《协纪辨方书")


def test_ten_god_corpus_covers_exactly_ten_gods() -> None:
    assert TEN_GOD_COUNT == 10
    assert set(TEN_GOD_MEANING) == {
        "比肩", "劫财", "食神", "伤官", "偏财", "正财", "七杀", "正官", "偏印", "正印",
    }


def test_nayin_corpus_covers_thirty_pairs() -> None:
    assert NAYIN_COUNT == 30
    assert {item.element for item in NAYIN_MEANING.values()} == {"木", "火", "土", "金", "水"}


def test_every_corpus_entry_is_citable() -> None:
    for item in [*TEN_GOD_MEANING.values(), *NAYIN_MEANING.values()]:
        assert any(item.source.startswith(prefix) for prefix in SOURCES), item


def test_ten_god_meaning_unknown_god_raises() -> None:
    with pytest.raises(KeyError):
        ten_god_meaning("不存在的神")


def test_nayin_meaning_resolves_full_pair_text() -> None:
    assert nayin_meaning("戊辰己巳").nayin == "大林木"
    assert nayin_meaning("庚子辛丑").element == "土"


def test_nayin_meaning_resolves_a_single_pillar() -> None:
    """The engine hands over one pillar (戊辰), so either half must resolve to the pair."""
    assert nayin_meaning("戊辰") is nayin_meaning("己巳") is nayin_meaning("戊辰己巳")


def test_ten_god_meaning_is_not_a_placeholder() -> None:
    """Every 释义 must survive the transcription procedure, template text must not leak in."""
    for item in TEN_GOD_MEANING.values():
        assert "本计划" not in item.meaning, item.ten_god
        assert "此处放" not in item.meaning, item.ten_god
        assert len(item.meaning) >= 8, item.ten_god


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


def test_each_ten_god_is_cited_to_its_own_chapter() -> None:
    """Sources are the ten 渊海子平 chapters, not a generic 赋.

    比肩 and 偏印 have no dedicated chapter in either allowed classic, so they are
    cited to 论兄弟姊妹 and 论倒食 —— the chapters that do define them.
    """
    sources = {item.source for item in TEN_GOD_MEANING.values()}
    assert sources == TEN_GOD_CHAPTERS
    assert TEN_GOD_MEANING["正印"].source.endswith("论印绶》")


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


def test_nayin_keys_are_the_thirty_ganzhi_pairs_in_order() -> None:
    """Keys are the fixed 甲子 pair texts so the engine's own pillar text looks them up."""
    first, last = next(iter(NAYIN_MEANING)), list(NAYIN_MEANING)[-1]
    assert first == "甲子乙丑" and last == "壬戌癸亥"
    assert all(len(key) == 4 for key in NAYIN_MEANING)
    assert nayin_meaning("甲辰乙巳").nayin == "覆灯火"


def test_nayin_corpus_matches_the_engine_that_supplies_the_text() -> None:
    """Task 10 looks the corpus up with lunar-python's own pillar text.

    If the library renames a 纳音 (金泊金 vs 金箔金 is already a live variant), the
    lookup silently misses; this test turns that into a failure at the boundary.
    """
    from lunar_python.util import LunarUtil

    for ganzhi, name in LunarUtil.NAYIN.items():
        assert nayin_meaning(ganzhi).nayin == name
        assert nayin_meaning(ganzhi).element == name[-1]
