"""卢恩极性表与 verdict 装配语料的自守门（2026-10-22 verdict-card spec §2b/§4）。

`RUNE_POLARITY` 24 枚全覆盖（值 ∈ {-1,0,1}，只按符文本身、不看朝向），
`RUNE_VERDICT_FRAME` / `RUNE_VERDICT_OUTLOOK` / `RUNE_VERDICT_ADVICE_FRAME` /
`RUNE_VERDICT_ADVICE` 这几组常量**不进** `PlainCorpus`，`tests/test_plain_corpora.py`
的条目/开篇句措辞门扫不到它们，故在这里自守：极性表对满 24 枚真符文（Wyrd 不在内），
档位词对齐 `verdict.GRADE_BANDS`，框架句过 `frame_violations`，槽位词条不成句、
不带禁字、不带建议词。
"""

from app.content.rune_futhark import DECK_24
from app.content.rune_polarity import (
    RUNE_POLARITY,
    RUNE_VERDICT_ADVICE,
    RUNE_VERDICT_ADVICE_FRAME,
    RUNE_VERDICT_FRAME,
    RUNE_VERDICT_OUTLOOK,
)
from app.engines.verdict import GRADE_BANDS
from tests.plain_wording import (
    FORBIDDEN,
    NON_ADVICE_FORMS,
    advice_hits,
    frame_slots,
    frame_violations,
)

GRADE_WORDS: list[str] = [word for _lower, word, _stars in GRADE_BANDS]


def test_polarity_table_covers_every_real_rune_exactly() -> None:
    """24 枚全覆盖：DECK_24 每枚都有极性，Wyrd 不在表内；值 ∈ {-1, 0, 1}。"""
    real_keys = {rune.key for rune in DECK_24}
    assert set(RUNE_POLARITY) == real_keys
    assert len(RUNE_POLARITY) == 24
    assert "wyrd" not in RUNE_POLARITY
    for key, polarity in RUNE_POLARITY.items():
        assert polarity in (-1, 0, 1), key


def test_outlook_keys_match_the_five_grade_bands() -> None:
    """各档位取向的键必须就是 `grade_for` 的五档档位词，缺一档装配即 KeyError。"""
    assert set(RUNE_VERDICT_OUTLOOK) == set(GRADE_WORDS)


def test_outlook_slot_words_are_clean() -> None:
    """取向词条：非空、不带「。」、不带禁字、不带建议词（档位词本身由 {grade} 槽注入）。"""
    for grade in GRADE_WORDS:
        word = RUNE_VERDICT_OUTLOOK[grade]
        assert word and "。" not in word
        for token in FORBIDDEN:
            assert token not in word
        assert advice_hits(word, masks=NON_ADVICE_FORMS) == [], (grade, word)


def test_advice_covers_favorable_and_adverse() -> None:
    """建议词键 = 净计数非负 / 净计数为负两个分支；漏一个，对应分支装配即 KeyError。"""
    assert set(RUNE_VERDICT_ADVICE) == {"favorable", "adverse"}


def test_advice_slot_words_are_clean() -> None:
    """建议词条：非空、不带「。」、不带禁字、无建议词命中。"""
    for branch, word in RUNE_VERDICT_ADVICE.items():
        assert word and "。" not in word
        for token in FORBIDDEN:
            assert token not in word
        assert advice_hits(word, masks=NON_ADVICE_FORMS) == [], (branch, word)


def test_frames_pass_the_frame_contract() -> None:
    """两条框架句同过 frame_violations：≥20 字 / 恰一「。」/ 含「你」/ 无禁字。"""
    for frame in (RUNE_VERDICT_FRAME, RUNE_VERDICT_ADVICE_FRAME):
        assert frame_violations("runes", frame) == [], frame


def test_frame_slots_match_the_engine_assembly() -> None:
    """槽名序与引擎 `overview()` 传入的字典键一致，错一个装配即 KeyError。"""
    assert frame_slots(RUNE_VERDICT_FRAME) == [
        "grade", "positive", "negative", "neutral", "outlook",
    ]
    assert frame_slots(RUNE_VERDICT_ADVICE_FRAME) == ["advice"]
