"""Golden tests for the 雷诺曼 (Lenormand) deck and combination-draw engine.

The deck is the fixed 36-card Petit Lenormand; the draw uses :mod:`secrets` (CSPRNG,
PRD 4.4), so exact cards are not pinned. Instead the tests assert the structural
guarantees: spread sizes and layouts, card uniqueness within a spread, that the Grand
Tableau lays all 36 distinct cards, that the polarity tally accounts for every card,
that line spreads read N-1 adjacent 组合直读 pairs, and that the significator is the
correct 指示牌 (男人 28 / 女人 29).
"""

import pytest
from fastapi.testclient import TestClient

from app.core.errors import UnsupportedMethodError
from app.engines.lenormand import draw_lenormand

SPREAD_SIZES = {"single": 1, "three_card": 3, "five_card": 5, "nine_card": 9, "grand_tableau": 36}
SPREAD_LAYOUTS = {
    "single": "line",
    "three_card": "line",
    "five_card": "line",
    "nine_card": "box",
    "grand_tableau": "tableau",
}


def test_grand_tableau_lays_all_thirty_six_distinct_cards() -> None:
    reading = draw_lenormand(spread_id="grand_tableau")
    assert len(reading.cards) == 36
    assert len(set(reading.drawn_ids)) == 36
    assert sorted(c.number for c in reading.cards) == list(range(1, 37))


def test_spread_sizes_and_layouts() -> None:
    for spread_id, size in SPREAD_SIZES.items():
        reading = draw_lenormand(spread_id=spread_id)
        assert reading.spread_id == spread_id
        assert reading.layout == SPREAD_LAYOUTS[spread_id]
        assert len(reading.cards) == size
        assert len(set(reading.drawn_ids)) == size


def test_positions_are_ordered_and_unique() -> None:
    reading = draw_lenormand(spread_id="five_card")
    assert [c.position_index for c in reading.cards] == list(range(5))
    assert len({c.position_key for c in reading.cards}) == 5


def test_polarity_tally_accounts_for_every_card() -> None:
    for spread_id, size in SPREAD_SIZES.items():
        reading = draw_lenormand(spread_id=spread_id)
        assert reading.positive_count + reading.neutral_count + reading.negative_count == size
        for card in reading.cards:
            assert card.polarity in {1, 0, -1}
            assert card.polarity_label in {"积极", "中性", "消极"}


def test_line_spreads_read_adjacent_combinations() -> None:
    # A line of N cards yields N-1 adjacent 组合直读 pairs.
    assert len(draw_lenormand(spread_id="single").combinations) == 0
    assert len(draw_lenormand(spread_id="three_card").combinations) == 2
    assert len(draw_lenormand(spread_id="five_card").combinations) == 4


def test_combination_phrase_is_composed_from_a_distinct_pair() -> None:
    reading = draw_lenormand(spread_id="three_card")
    assert reading.combinations
    for combo in reading.combinations:
        assert combo.phrase.strip()
        assert combo.left.number != combo.right.number


def test_significator_is_the_correct_card() -> None:
    male = draw_lenormand(spread_id="grand_tableau", significator="male")
    assert male.significator is not None
    assert male.significator.number == 28
    assert male.significator.name_zh == "男人"
    female = draw_lenormand(spread_id="grand_tableau", significator="female")
    assert female.significator is not None
    assert female.significator.number == 29
    assert female.significator.name_zh == "女人"
    assert draw_lenormand(spread_id="grand_tableau").significator is None


def test_draws_are_varied_not_deterministic() -> None:
    first = draw_lenormand(spread_id="five_card").drawn_ids
    second = draw_lenormand(spread_id="five_card").drawn_ids
    assert first != second


def test_rng_and_engine_are_declared() -> None:
    reading = draw_lenormand(spread_id="three_card")
    assert reading.rng == "secrets"
    assert reading.engine == "lenormand-combination"
    assert reading.synthesis.strip()


def test_unknown_spread_raises() -> None:
    with pytest.raises(UnsupportedMethodError):
        draw_lenormand(spread_id="not_a_spread")


def test_lenormand_endpoint(client: TestClient) -> None:
    response = client.post("/api/v1/lenormand/draw", json={"spread_id": "three_card"})
    assert response.status_code == 200
    body = response.json()
    assert body["spread_id"] == "three_card"
    assert len(body["cards"]) == 3
    assert len(set(body["drawn_ids"])) == 3
    assert body["rng"] == "secrets"


def test_lenormand_endpoint_rejects_unknown_spread(client: TestClient) -> None:
    response = client.post("/api/v1/lenormand/draw", json={"spread_id": "nope"})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "unsupported_method"
