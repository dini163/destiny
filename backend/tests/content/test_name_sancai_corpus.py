"""三才只报生克关系：五个键、图来自五行、断语非空且署名诚实（spec 决策四、§9.1）。"""

import pytest

from app.content.name_sancai import SANCAI_RELATIONS, SANCAI_SOURCE, relation_between
from app.content.wuxing import ELEMENT_ORDER


def test_exactly_the_five_relations_exist() -> None:
    assert set(SANCAI_RELATIONS) == {"生我", "我生", "克我", "我克", "比和"}


@pytest.mark.parametrize("relation", sorted(SANCAI_RELATIONS))
def test_every_relation_carries_text_and_a_source(relation: str) -> None:
    item = SANCAI_RELATIONS[relation]
    assert item.sentence.strip() and item.source.strip()


def test_relation_covers_every_ordered_element_pair() -> None:
    seen: set[str] = set()
    for a in ELEMENT_ORDER:
        for b in ELEMENT_ORDER:
            seen.add(relation_between(a, b))
    assert seen == set(SANCAI_RELATIONS)


def test_same_element_is_harmony() -> None:
    assert relation_between("木", "木") == "比和"


def test_generation_and_control_read_from_the_shared_graph() -> None:
    """木生火：从木看是"我生"，从火看是"生我"。图在 wuxing.py，这里只取名。"""
    assert relation_between("木", "火") == "我生"
    assert relation_between("火", "木") == "生我"
    assert relation_between("木", "土") == "我克"
    assert relation_between("木", "金") == "克我"


def test_source_does_not_claim_a_book_it_cites_nothing_of() -> None:
    assert "生克" in SANCAI_SOURCE