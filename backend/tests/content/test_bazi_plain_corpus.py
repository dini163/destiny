"""白话转述表：工厂看不到的那半截不变式（白话 spec §3）。

键集合相等是唯一那道防漂移的闸：`bazi_dimensions` 将来增删判语而忘了这张表，
少键会在运行时抛 KeyError、多键在 `tests/test_plain_corpora.py` 的键全集闸即红。
措辞与开篇/收尾框架句的机检同样住工厂（本文件不再断第二份，AGENTS.md §2），这里只留
工厂不掌握的四件事：分带符号、开篇句覆盖面、档位词表、总论框架句的占位符与禁字。
"""

from app.content.bazi_dimensions import DIMENSION_RULES, dim_rule
from app.content.bazi_plain import DIMENSION_OPENERS, PLAIN_SUMMARY_FRAME, TIER_CLOSERS

ALL_KEYS = {rule.key for rules in DIMENSION_RULES.values() for rule in rules}
PREFIXES = {rules[0].key.split(".", maxsplit=1)[0] for rules in DIMENSION_RULES.values()}
# 机检集合逐字取自 spec §3 第 2 条：「（《」与「』」是出处引用标记，「；」是拼接残留。
# 「则」「之」同条只列为**风格**要求（白话不得有文言句式），不进机检——单字黑名单会连带
# 打死「规则」「之前」「之后」这类现代词，红得一派无辜（控制器 pre-flight 裁定 R3）。
# 文言句式的实际防线是人审 + 本表文案已避开「X之物」「随之」这类属格构造。
# 口径正主是 `tests/test_plain_corpora.py` 的 FORBIDDEN，这里是被迫切的第二份：
# PLAIN_SUMMARY_FRAME 不在工厂 openers/closers 的遍历里，参数化工厂看不见它。
FORBIDDEN = ("；", "（《", "』")


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
    for token in FORBIDDEN:
        assert token not in PLAIN_SUMMARY_FRAME, token
