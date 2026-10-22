"""雷诺曼综合结论卡片（verdict）装配语料的自守门（2026-10-22 verdict-card spec §2b/§4）。

`LENORMAND_VERDICT_FRAME` / `LENORMAND_VERDICT_OUTLOOK` / `LENORMAND_VERDICT_ADVICE_FRAME` /
`LENORMAND_VERDICT_ADVICE` 这几组常量**不进** `LENORMAND_READINGS`（工厂键全集仍为 36），
`tests/test_plain_corpora.py` 的条目/开篇句措辞门扫不到它们，故在这里自守：档位词对齐
`verdict.GRADE_BANDS`，框架句过 `frame_violations`，槽位词条不成句、不带禁字、不带建议词。
"""

import pytest

from app.content.lenormand_plain import (
    LENORMAND_VERDICT_ADVICE,
    LENORMAND_VERDICT_ADVICE_FRAME,
    LENORMAND_VERDICT_FRAME,
    LENORMAND_VERDICT_OUTLOOK,
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
    """各档位取向的键必须就是 `grade_for` 的五档档位词，缺一档装配即 KeyError。"""
    assert set(LENORMAND_VERDICT_OUTLOOK) == set(GRADE_WORDS)


@pytest.mark.parametrize("grade", GRADE_WORDS)
def test_outlook_slot_words_are_clean(grade: str) -> None:
    """取向词条：非空、不带「。」、不带禁字、不带建议词（档位词本身由 {grade} 槽注入）。"""
    word = LENORMAND_VERDICT_OUTLOOK[grade]
    assert word and "。" not in word
    for token in FORBIDDEN:
        assert token not in word
    assert advice_hits(word, masks=NON_ADVICE_FORMS) == [], (grade, word)


def test_advice_covers_favorable_and_adverse() -> None:
    """建议词键 = 净计数非负 / 净计数为负两个分支；漏一个，对应分支装配即 KeyError。"""
    assert set(LENORMAND_VERDICT_ADVICE) == {"favorable", "adverse"}


@pytest.mark.parametrize("branch", sorted(LENORMAND_VERDICT_ADVICE))
def test_advice_slot_words_are_clean(branch: str) -> None:
    """建议词条：非空、不带「。」、不带禁字、无建议词命中。"""
    word = LENORMAND_VERDICT_ADVICE[branch]
    assert word and "。" not in word
    for token in FORBIDDEN:
        assert token not in word
    assert advice_hits(word, masks=NON_ADVICE_FORMS) == [], (branch, word)


@pytest.mark.parametrize("frame", [LENORMAND_VERDICT_FRAME, LENORMAND_VERDICT_ADVICE_FRAME])
def test_frames_pass_the_frame_contract(frame: str) -> None:
    """两条框架句同过 frame_violations：≥20 字 / 恰一「。」/ 含「你」/ 无禁字。"""
    assert frame_violations("lenormand", frame) == [], frame


def test_frame_slots_match_the_engine_assembly() -> None:
    """槽名序与引擎 `overview()` 传入的字典键一致，错一个装配即 KeyError。"""
    assert frame_slots(LENORMAND_VERDICT_FRAME) == ["grade", "positive", "negative", "neutral", "outlook"]
    assert frame_slots(LENORMAND_VERDICT_ADVICE_FRAME) == ["advice"]
