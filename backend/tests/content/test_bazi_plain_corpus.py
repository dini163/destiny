"""白话转述表：工厂看不到的那半截不变式（白话 spec §3）。

键集合相等是唯一那道防漂移的闸：`bazi_dimensions` 将来增删判语而忘了这张表，
少键会在运行时抛 KeyError、多键在 `tests/test_plain_corpora.py` 的键全集闸即红。
措辞与开篇/收尾框架句的机检同样住工厂（本文件不再断第二份，AGENTS.md §2），这里只留
工厂不掌握的五件事：分带符号、开篇句覆盖面、档位词表、总论框架句的占位符与禁字、登记身份。
"""

from app.content.bazi_dimensions import DIMENSION_RULES, dim_rule
from app.content.bazi_plain import (
    DIMENSION_OPENERS,
    PLAIN_SUMMARY_FRAME,
    TIER_ADVICE,
    TIER_CLOSERS,
    VERDICT_ADVICE_FRAME,
    VERDICT_OUTLOOK,
)
from app.engines.plain_corpora import BAZI, PLAIN_CORPORA
from tests.plain_wording import FORBIDDEN, frame_slots

ALL_KEYS = {rule.key for rules in DIMENSION_RULES.values() for rule in rules}
PREFIXES = {rules[0].key.split(".", maxsplit=1)[0] for rules in DIMENSION_RULES.values()}


def test_every_rule_has_a_non_zero_delta_so_no_plain_line_is_dropped() -> None:
    """`build_plain` 用 delta 的正负分带，delta 为 0 的键会两头都不进——静默少一条白话。

    条数复测：`cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "from app.content.bazi_dimensions import DIMENSION_RULES; print(sum(1 for rs in DIMENSION_RULES.values() for r in rs if r.delta == 0))"` → 0。
    """
    assert all(dim_rule(key).delta != 0 for key in ALL_KEYS)


def test_openers_cover_every_dimension_prefix() -> None:
    assert set(DIMENSION_OPENERS) == PREFIXES


def test_closers_cover_exactly_the_three_tiers() -> None:
    assert set(TIER_CLOSERS) == {"顺", "平", "滞"}


def test_summary_frame_carries_its_placeholders_only() -> None:
    # 段落框架句（PLAIN_SUMMARY_FRAME）不在工厂 openers/closers 的遍历里，参数化工厂看不见它，
    # 所以禁字这一半由本文件自守；口径正主在 tests/plain_wording.py。
    # 2026-10-21 verdict-card spec §4：总论框架改为「档位 + 六维计数 + 取向」，
    # 槽位从 {summary} 扩为 {grade}/{shun}/{ping}/{zhi}/{outlook}，共五槽、次序即出现序。
    assert frame_slots(PLAIN_SUMMARY_FRAME) == ["grade", "shun", "ping", "zhi", "outlook"]
    for token in FORBIDDEN:
        assert token not in PLAIN_SUMMARY_FRAME, token


def test_verdict_frames_and_slot_words_meet_the_same_contract() -> None:
    # 结论卡片的框架句与槽位语料同样不在工厂遍历里（verdict-card spec §4），由本文件自守：
    # 建议框架句走全句口径（≥20 字、恰一「。」、含「你」、禁字）；
    # 两套槽位语料（VERDICT_OUTLOOK / TIER_ADVICE）不成句：非空、无「。」、禁字。
    assert len(VERDICT_ADVICE_FRAME) >= 20
    assert VERDICT_ADVICE_FRAME.count("。") == 1
    assert "你" in VERDICT_ADVICE_FRAME
    for token in FORBIDDEN:
        assert token not in VERDICT_ADVICE_FRAME, token
    for words in (VERDICT_OUTLOOK, TIER_ADVICE):
        for word in words.values():
            assert word.strip() and "。" not in word
            for token in FORBIDDEN:
                assert token not in word, token


def test_bazi_corpus_is_the_row_the_factory_iterates() -> None:
    """登记表里 `"bazi"` 这一行必须仍指向八字那张表。

    `PLAIN_CORPORA` 是字典字面量：同名两行时 Python 静默留后一行，前一张表就此掉出机检闸外，
    而工厂的「键数 == 去重键数」与「键 == corpus.system」两条照样绿（复测：
    `cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m pytest tests/test_plain_corpora.py -o addopts="" -k registered`）。
    逐系统的 `PLAIN_CORPORA[X] is X` 才是那第三道钉，姓名学/合盘/梅花各有，八字缺。
    """
    assert PLAIN_CORPORA["bazi"] is BAZI
