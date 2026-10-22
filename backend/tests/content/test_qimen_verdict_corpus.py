"""奇门综合结论卡片（verdict）装配语料的自守门（2026-10-22 verdict-card spec §2b/§4）。

`QIMEN_VERDICT_FRAME` / `QIMEN_VERDICT_OUTLOOK` / `QIMEN_VERDICT_ADVICE_FRAME` /
`QIMEN_VERDICT_ADVICE` 这几组常量**不进** `QIMEN_READINGS`（工厂键全集仍为 29），
`tests/test_plain_corpora.py` 的条目/开篇句措辞门扫不到它们，故在这里自守：档位词对齐
`verdict.GRADE_BANDS`，框架句过 `frame_violations`，槽位词条不成句、不带禁字、不带建议词。
"""

import pytest

from app.content.qimen_plain import (
    QIMEN_VERDICT_ADVICE,
    QIMEN_VERDICT_ADVICE_FRAME,
    QIMEN_VERDICT_FRAME,
    QIMEN_VERDICT_OUTLOOK,
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


def test_outlook_keys_match_the_five_grade_bands() -> None:
    assert set(QIMEN_VERDICT_OUTLOOK) == set(GRADE_WORDS)


@pytest.mark.parametrize("grade", GRADE_WORDS)
def test_outlook_slot_words_are_clean(grade: str) -> None:
    word = QIMEN_VERDICT_OUTLOOK[grade]
    assert word and "。" not in word
    for token in FORBIDDEN:
        assert token not in word
    assert advice_hits(word, masks=NON_ADVICE_FORMS) == [], (grade, word)


def test_advice_covers_favorable_and_adverse() -> None:
    assert set(QIMEN_VERDICT_ADVICE) == {"favorable", "adverse"}


@pytest.mark.parametrize("branch", sorted(QIMEN_VERDICT_ADVICE))
def test_advice_slot_words_are_clean(branch: str) -> None:
    word = QIMEN_VERDICT_ADVICE[branch]
    assert word and "。" not in word
    for token in FORBIDDEN:
        assert token not in word
    assert advice_hits(word, masks=NON_ADVICE_FORMS) == [], (branch, word)


@pytest.mark.parametrize("frame", [QIMEN_VERDICT_FRAME, QIMEN_VERDICT_ADVICE_FRAME])
def test_frames_pass_the_frame_contract(frame: str) -> None:
    assert frame_violations("qimen", frame) == [], frame


def test_frame_slots_match_the_engine_assembly() -> None:
    assert frame_slots(QIMEN_VERDICT_FRAME) == ["grade", "zhi", "shi", "outlook"]
    assert frame_slots(QIMEN_VERDICT_ADVICE_FRAME) == ["advice"]
