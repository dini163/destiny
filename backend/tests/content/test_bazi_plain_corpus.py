"""白话转述表的不变式：键与判语表严格同源，措辞过四条铁律（白话 spec §3）。

键集合相等是唯一那道防漂移的闸：`bazi_dimensions` 将来增删判语而忘了这张表，
少键会在运行时抛 KeyError、多键在 `tests/test_plain_corpora.py` 的键全集闸即红。
措辞与框架句的机检同样住工厂（本文件不再断第二份，AGENTS.md §2），这里只留
工厂不掌握的四件事：分带符号、开篇句覆盖面、档位词表、总论框架的占位符。
"""

from app.content.bazi_dimensions import DIMENSION_RULES, dim_rule
from app.content.bazi_plain import DIMENSION_OPENERS, PLAIN_SUMMARY_FRAME, TIER_CLOSERS

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


def test_summary_frame_carries_the_placeholder_only() -> None:
    assert "{summary}" in PLAIN_SUMMARY_FRAME
