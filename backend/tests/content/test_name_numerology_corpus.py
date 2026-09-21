"""81 数理表的不变式：定义域、档位词汇、非空文本、出处诚实（spec §9.1）。"""

import pytest

from app.content.name_numerology import (
    FORTUNE_LEVELS,
    NUMBERS,
    NUMEROLOGY_SOURCE,
    NameFortune,
    numerology_entry,
)


def test_domain_is_exactly_one_to_eighty_one() -> None:
    assert set(NUMBERS) == set(range(1, 82))
    assert len(NUMBERS) == 81


def test_fortune_vocabulary_is_closed_and_driven_by_the_table() -> None:
    """双向锁死：枚举成员 == 表内实际出现的等级集合，防表与枚举各自漂移。"""
    in_table = {entry.fortune for entry in NUMBERS.values()}
    assert in_table == {level for level in FORTUNE_LEVELS}
    assert {member.value for member in NameFortune} == in_table


def test_tiers_are_the_four_printed_in_the_design_mockup() -> None:
    assert set(FORTUNE_LEVELS) <= {"大吉", "吉", "半吉", "凶"}


@pytest.mark.parametrize("number", sorted(NUMBERS))
def test_every_row_is_fully_cited(number: int) -> None:
    entry = NUMBERS[number]
    assert entry.pattern_name.strip() and entry.verdict.strip()
    assert "非古籍" in entry.source, "81 数理是通行表整理，出处必须自认不是古籍"


def test_lookup_rejects_out_of_range_number() -> None:
    with pytest.raises(KeyError):
        numerology_entry(0)
    with pytest.raises(KeyError):
        numerology_entry(82)


def test_table_source_declares_provenance() -> None:
    assert "熊崎" in NUMEROLOGY_SOURCE and "非古籍" in NUMEROLOGY_SOURCE
