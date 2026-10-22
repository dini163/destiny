"""紫微综合结论卡片（verdict）装配语料的自守门（2026-10-22 verdict-card spec §2b/§4）。

`ZIWEI_VERDICT_FRAME` / `ZIWEI_VERDICT_OUTLOOK` / `ZIWEI_VERDICT_ADVICE_FRAME` /
`ZIWEI_VERDICT_BALANCED_FRAME` / `ZIWEI_COMPONENT_ADVICE` 这几组常量**不进**
`ZIWEI_READINGS`（工厂键全集仍为 44），`tests/test_plain_corpora.py` 的条目/开篇句措辞门
扫不到它们，故在这里自守：档位词对齐 `verdict.GRADE_BANDS`，框架句过 `frame_violations`，
槽位词条不成句、不带禁字、不带建议词。
"""

import pytest

from app.content.ziwei_plain import (
    ZIWEI_COMPONENT_ADVICE,
    ZIWEI_VERDICT_ADVICE_FRAME,
    ZIWEI_VERDICT_BALANCED_FRAME,
    ZIWEI_VERDICT_FRAME,
    ZIWEI_VERDICT_OUTLOOK,
)
from app.engines.verdict import GRADE_BANDS
from tests.plain_wording import (
    FORBIDDEN,
    NON_ADVICE_FORMS,
    advice_hits,
    frame_slots,
    frame_violations,
)

#: 具名四化名相（同 `test_ziwei_plain_corpus.py` 的 SIHUA_FORMS 豁免口径），不算建议词。
SIHUA_FORMS: tuple[str, ...] = ("化禄", "化权", "化科", "化忌")

GRADE_WORDS: list[str] = [word for _lower, word, _stars in GRADE_BANDS]


def test_outlook_keys_match_the_five_grade_bands() -> None:
    """各档位取向的键必须就是 `grade_for` 的五档档位词，缺一档装配即 KeyError。"""
    assert set(ZIWEI_VERDICT_OUTLOOK) == set(GRADE_WORDS)


@pytest.mark.parametrize("grade", GRADE_WORDS)
def test_outlook_slot_words_are_clean(grade: str) -> None:
    """取向词条：非空、不带「。」、不带禁字、不带建议词（档位词本身由 {grade} 槽注入）。"""
    word = ZIWEI_VERDICT_OUTLOOK[grade]
    assert word and "。" not in word
    for token in FORBIDDEN:
        assert token not in word
    assert advice_hits(word, masks=NON_ADVICE_FORMS) == [], (grade, word)


def test_component_advice_covers_the_three_links_and_balanced() -> None:
    """建议词键 = 三环节名 + 全正的中性维护键；漏一个，对应分支装配即 KeyError。"""
    assert set(ZIWEI_COMPONENT_ADVICE) == {"主星格局", "辅佐煞曜", "生年四化", "整体"}


@pytest.mark.parametrize("component", sorted(ZIWEI_COMPONENT_ADVICE))
def test_component_advice_slot_words_are_clean(component: str) -> None:
    """建议词条：非空、不带「。」、不带禁字；「化忌」按具名相豁免后无建议词命中。"""
    word = ZIWEI_COMPONENT_ADVICE[component]
    assert word and "。" not in word
    for token in FORBIDDEN:
        assert token not in word
    masks = (*NON_ADVICE_FORMS, *SIHUA_FORMS)
    assert advice_hits(word, masks=masks) == [], (component, word)


@pytest.mark.parametrize(
    "frame",
    [ZIWEI_VERDICT_FRAME, ZIWEI_VERDICT_ADVICE_FRAME, ZIWEI_VERDICT_BALANCED_FRAME],
)
def test_frames_pass_the_frame_contract(frame: str) -> None:
    """三条框架句同过 frame_violations：≥20 字 / 恰一「。」/ 含「你」/ 无禁字。"""
    assert frame_violations("ziwei", frame) == [], frame


def test_frame_slots_match_the_engine_assembly() -> None:
    """槽名序与引擎 `overview()` 传入的字典键一致，错一个装配即 KeyError。"""
    assert frame_slots(ZIWEI_VERDICT_FRAME) == ["grade", "auspicious", "malefic", "outlook"]
    assert frame_slots(ZIWEI_VERDICT_ADVICE_FRAME) == ["component", "component_advice"]
    assert frame_slots(ZIWEI_VERDICT_BALANCED_FRAME) == ["component_advice"]
