"""断占辞受控词表的本地门（verdict 判定层的锚，`content/zhouyi_duanci.py`）。

词表是结论卡片唯一的吉凶来源：九个受控词分四正五负，每个条目带章属出处；
「无咎」必须排在正向首位先剔，否则被裸「咎」双记。本门钉词集、极性与出处三件，
词频折算在引擎，由 golden 对账。

复测：`cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m pytest tests/content/test_zhouyi_duanci.py -v`
"""

from app.content.zhouyi_duanci import (
    NEGATIVE_DUANCI,
    NEGATIVE_WORDS,
    POSITIVE_DUANCI,
    POSITIVE_WORDS,
)


def test_nine_controlled_words_split_into_four_positive_five_negative() -> None:
    """四正（无咎/吉/亨/利）五负（凶/吝/悔/咎/厉），两集不交。"""
    assert POSITIVE_WORDS == ("无咎", "吉", "亨", "利")
    assert NEGATIVE_WORDS == ("凶", "吝", "悔", "咎", "厉")
    assert set(POSITIVE_WORDS).isdisjoint(NEGATIVE_WORDS)
    assert len(POSITIVE_DUANCI) == 4 and len(NEGATIVE_DUANCI) == 5


def test_every_entry_carries_a_chapter_level_source() -> None:
    """每条词都带章属出处（到章不到书，R46），极性只取两值。"""
    for entry in (*POSITIVE_DUANCI, *NEGATIVE_DUANCI):
        assert entry.word
        assert entry.polarity in ("positive", "negative")
        assert entry.source
        assert "周易" in entry.source


def test_wujiu_is_the_first_positive_word_so_it_is_removed_before_bare_jiu() -> None:
    """「无咎」是完整占辞：先数先剔，裸「咎」才归负向，顺序错了无咎被双记。"""
    assert POSITIVE_DUANCI[0].word == "无咎"
    assert "无咎" not in NEGATIVE_WORDS
