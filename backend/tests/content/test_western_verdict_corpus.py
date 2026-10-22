"""西洋本命综合结论卡片（verdict）装配语料的自守门（2026-10-22 verdict-card spec §2b/§4）。

`WESTERN_VERDICT_FRAME` / `WESTERN_VERDICT_OUTLOOK` / `WESTERN_VERDICT_ADVICE_FRAME` /
`WESTERN_VERDICT_ADVICE` 不进 `WESTERN_READINGS`（工厂键全集不变），工厂措辞门扫不到它们，
故在此自守：档位词对齐 `verdict.GRADE_BANDS`，框架句过 `frame_violations`（本命页属预测门，
另过预测禁词与戊组决策禁词），槽位词条不成句、不带禁字、不带建议词。
"""

import pytest

from app.content.western_plain import (
    WESTERN_VERDICT_ADVICE,
    WESTERN_VERDICT_ADVICE_FRAME,
    WESTERN_VERDICT_FRAME,
    WESTERN_VERDICT_OUTLOOK,
)
from app.engines.verdict import GRADE_BANDS
from tests.plain_wording import (
    FORBIDDEN,
    NON_ADVICE_FORMS,
    PREDICTION_FORBIDDEN,
    WU_DECISION_FORBIDDEN,
    advice_hits,
    frame_slots,
    frame_violations,
)

GRADE_WORDS: list[str] = [word for _lower, word, _stars in GRADE_BANDS]


def test_outlook_keys_match_the_five_grade_bands() -> None:
    assert set(WESTERN_VERDICT_OUTLOOK) == set(GRADE_WORDS)


@pytest.mark.parametrize("grade", GRADE_WORDS)
def test_outlook_slot_words_are_clean(grade: str) -> None:
    word = WESTERN_VERDICT_OUTLOOK[grade]
    assert word and "。" not in word
    for token in (*FORBIDDEN, *PREDICTION_FORBIDDEN, *WU_DECISION_FORBIDDEN):
        assert token not in word
    assert advice_hits(word, masks=NON_ADVICE_FORMS) == [], (grade, word)


def test_advice_covers_favorable_and_adverse() -> None:
    assert set(WESTERN_VERDICT_ADVICE) == {"favorable", "adverse"}


@pytest.mark.parametrize("branch", sorted(WESTERN_VERDICT_ADVICE))
def test_advice_slot_words_are_clean(branch: str) -> None:
    word = WESTERN_VERDICT_ADVICE[branch]
    assert word and "。" not in word
    for token in (*FORBIDDEN, *PREDICTION_FORBIDDEN, *WU_DECISION_FORBIDDEN):
        assert token not in word
    assert advice_hits(word, masks=NON_ADVICE_FORMS) == [], (branch, word)


@pytest.mark.parametrize("frame", [WESTERN_VERDICT_FRAME, WESTERN_VERDICT_ADVICE_FRAME])
def test_frames_pass_the_frame_contract(frame: str) -> None:
    assert frame_violations("western", frame) == [], frame


def test_frame_slots_match_the_engine_assembly() -> None:
    assert frame_slots(WESTERN_VERDICT_FRAME) == [
        "grade",
        "harmonious",
        "challenging",
        "fusion",
        "outlook",
    ]
    assert frame_slots(WESTERN_VERDICT_ADVICE_FRAME) == ["advice"]
