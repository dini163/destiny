"""塔罗极性表与 verdict 装配语料的自守门（2026-10-22 verdict-card spec §2b/§4）。

`TAROT_POLARITY` 78 张全覆盖（正逆两列各 ∈ {-1,0,1}），`TAROT_VERDICT_FRAME` /
`TAROT_VERDICT_OUTLOOK` / `TAROT_VERDICT_ADVICE_FRAME` / `TAROT_VERDICT_ADVICE` 这几组
常量**不进** `PlainCorpus`（丁组 spec §11 拒绝项⑤），`tests/test_plain_corpora.py` 的
条目/开篇句措辞门扫不到它们，故在这里自守：极性表对满 78 张牌，档位词对齐
`verdict.GRADE_BANDS`，框架句过 `frame_violations`，槽位词条不成句、不带禁字、不带建议词。
"""

from app.content.tarot_deck import DECK
from app.content.tarot_polarity import (
    TAROT_POLARITY,
    TAROT_VERDICT_ADVICE,
    TAROT_VERDICT_ADVICE_FRAME,
    TAROT_VERDICT_FRAME,
    TAROT_VERDICT_OUTLOOK,
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


def test_polarity_table_covers_every_deck_card_exactly() -> None:
    """78 张全覆盖：牌库每张牌都有正逆两列，不多不少；两列各 ∈ {-1, 0, 1}。"""
    deck_ids = {card.id for card in DECK}
    assert set(TAROT_POLARITY) == deck_ids
    assert len(TAROT_POLARITY) == 78
    for card_id, (upright, reversed_polarity, chapter) in TAROT_POLARITY.items():
        assert upright in (-1, 0, 1), card_id
        assert reversed_polarity in (-1, 0, 1), card_id
        assert chapter, card_id


def test_outlook_keys_match_the_five_grade_bands() -> None:
    """各档位取向的键必须就是 `grade_for` 的五档档位词，缺一档装配即 KeyError。"""
    assert set(TAROT_VERDICT_OUTLOOK) == set(GRADE_WORDS)


def test_outlook_slot_words_are_clean() -> None:
    """取向词条：非空、不带「。」、不带禁字、不带建议词（档位词本身由 {grade} 槽注入）。"""
    for grade in GRADE_WORDS:
        word = TAROT_VERDICT_OUTLOOK[grade]
        assert word and "。" not in word
        for token in FORBIDDEN:
            assert token not in word
        assert advice_hits(word, masks=NON_ADVICE_FORMS) == [], (grade, word)


def test_advice_covers_favorable_and_adverse() -> None:
    """建议词键 = 净计数非负 / 净计数为负两个分支；漏一个，对应分支装配即 KeyError。"""
    assert set(TAROT_VERDICT_ADVICE) == {"favorable", "adverse"}


def test_advice_slot_words_are_clean() -> None:
    """建议词条：非空、不带「。」、不带禁字、无建议词命中。"""
    for branch, word in TAROT_VERDICT_ADVICE.items():
        assert word and "。" not in word
        for token in FORBIDDEN:
            assert token not in word
        assert advice_hits(word, masks=NON_ADVICE_FORMS) == [], (branch, word)


def test_frames_pass_the_frame_contract() -> None:
    """两条框架句同过 frame_violations：≥20 字 / 恰一「。」/ 含「你」/ 无禁字。"""
    for frame in (TAROT_VERDICT_FRAME, TAROT_VERDICT_ADVICE_FRAME):
        assert frame_violations("tarot", frame) == [], frame


def test_frame_slots_match_the_engine_assembly() -> None:
    """槽名序与引擎 `overview()` 传入的字典键一致，错一个装配即 KeyError。"""
    assert frame_slots(TAROT_VERDICT_FRAME) == [
        "grade", "positive", "negative", "neutral", "major", "reversed", "outlook",
    ]
    assert frame_slots(TAROT_VERDICT_ADVICE_FRAME) == ["advice"]
