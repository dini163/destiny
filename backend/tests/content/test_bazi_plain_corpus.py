"""白话转述表的不变式：键与判语表严格同源，措辞过四条铁律（白话 spec §3）。

键集合相等是唯一那道防漂移的闸：`bazi_dimensions` 将来增删判语而忘了这张表，
少键会在运行时抛 KeyError、多键在本文件第一条测试即红。
"""

import pytest

from app.content.bazi_dimensions import DIMENSION_RULES
from app.content.bazi_plain import (
    DIMENSION_OPENERS,
    PLAIN_READINGS,
    PLAIN_SUMMARY_FRAME,
    TIER_CLOSERS,
)

ALL_KEYS = {rule.key for rules in DIMENSION_RULES.values() for rule in rules}
PREFIXES = {rules[0].key.split(".", maxsplit=1)[0] for rules in DIMENSION_RULES.values()}
# 机检集合逐字取自 spec §3 第 2 条：「（《」与「』」是出处引用标记，「；」是拼接残留。
# 「则」「之」同条只列为**风格**要求（白话不得有文言句式），不进机检——单字黑名单会连带
# 打死「规则」「之前」「之后」这类现代词，红得一派无辜（控制器 pre-flight 裁定 R3）。
# 文言句式的实际防线是人审 + 本表文案已避开「X之物」「随之」这类属格构造。
FORBIDDEN = ("；", "（《", "』")


def test_plain_keys_mirror_the_judgment_corpus_exactly() -> None:
    assert set(PLAIN_READINGS) == ALL_KEYS


def test_openers_cover_every_dimension_prefix() -> None:
    assert set(DIMENSION_OPENERS) == PREFIXES


def test_closers_cover_exactly_the_three_tiers() -> None:
    assert set(TIER_CLOSERS) == {"顺", "平", "滞"}


@pytest.mark.parametrize("key", sorted(ALL_KEYS))
def test_every_plain_reading_meets_the_wording_contract(key: str) -> None:
    text = PLAIN_READINGS[key]
    assert len(text) >= 40, key
    assert text.endswith("。") and text.count("。") == 1, key
    assert "你" in text, key
    for token in FORBIDDEN:
        assert token not in text, (key, token)


@pytest.mark.parametrize(
    "text", sorted([*DIMENSION_OPENERS.values(), *TIER_CLOSERS.values()])
)
def test_frame_sentences_meet_the_same_contract(text: str) -> None:
    assert len(text) >= 20, text
    assert text.endswith("。") and text.count("。") == 1, text
    assert "你" in text, text
    for token in FORBIDDEN:
        assert token not in text, (text, token)


def test_summary_frame_carries_the_placeholder_only() -> None:
    assert "{summary}" in PLAIN_SUMMARY_FRAME
    for token in FORBIDDEN:
        assert token not in PLAIN_SUMMARY_FRAME
