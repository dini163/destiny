"""Golden tests for the tarot deck content and draw engine.

The deck count (78 = 22 Major + 56 Minor) and card uniqueness are content
invariants enforced here per PRD 4.4. Draw behaviour asserts uniqueness within a
spread, that reversals honour the flag, and that spread sizes match the layout.
Randomness comes from :mod:`secrets` (CSPRNG), so exact cards are not pinned;
instead the tests assert structural guarantees and, where useful, variety.
"""

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.content.tarot_cards import SUIT_ELEMENT
from app.content.tarot_deck import DECK, MAJOR_SIZE, MINOR_SIZE, SPREADS, get_card
from app.core.errors import UnsupportedMethodError
from app.engines.tarot import draw_spread
from app.schemas.tarot import DrawnCard, TarotSpreadResponse

SPREAD_SIZES = {
    "single": 1,
    "three_card": 3,
    "celtic_cross": 10,
    "relationship": 5,
    "career": 5,
    "decision": 5,
}


# --- Deck content invariants ------------------------------------------------


def test_deck_has_seventy_eight_unique_cards() -> None:
    assert len(DECK) == 78
    ids = [card.id for card in DECK]
    assert len(set(ids)) == 78


def test_deck_splits_into_major_and_minor() -> None:
    majors = [c for c in DECK if c.arcana == "major"]
    minors = [c for c in DECK if c.arcana == "minor"]
    assert len(majors) == MAJOR_SIZE == 22
    assert len(minors) == MINOR_SIZE == 56


def test_major_arcana_numbers_are_zero_through_twenty_one() -> None:
    numbers = sorted(c.number for c in DECK if c.arcana == "major")
    assert numbers == list(range(22))


def test_minor_arcana_cover_four_suits_of_fourteen() -> None:
    minors = [c for c in DECK if c.arcana == "minor"]
    for suit in SUIT_ELEMENT:
        suit_cards = sorted(c.number for c in minors if c.suit == suit)
        assert suit_cards == list(range(1, 15))


def test_court_cards_carry_ranks_and_numbered_cards_do_not() -> None:
    court_numbers = {11, 12, 13, 14}
    for card in DECK:
        if card.arcana == "minor" and card.number in court_numbers:
            assert card.rank in {"Page", "Knight", "Queen", "King"}
        elif card.arcana == "minor":
            assert card.rank is None


def test_major_arcana_have_no_suit_or_element() -> None:
    for card in DECK:
        if card.arcana == "major":
            assert card.suit is None
            assert card.element is None


def test_every_card_has_meanings_and_keywords_both_orientations() -> None:
    for card in DECK:
        assert card.upright_meaning.strip()
        assert card.reversed_meaning.strip()
        assert len(card.upright_keywords) >= 3
        assert len(card.reversed_keywords) >= 3


def test_get_card_round_trips_by_id() -> None:
    assert get_card("major-00").name == "The Fool"
    assert get_card("wands-14").rank == "King"
    with pytest.raises(KeyError):
        get_card("does-not-exist")


# --- Spread library ---------------------------------------------------------


def test_spread_library_matches_expected_sizes() -> None:
    assert set(SPREADS) == set(SPREAD_SIZES)
    for spread_id, size in SPREAD_SIZES.items():
        assert SPREADS[spread_id].size == size


def test_spread_positions_have_unique_keys_and_bilingual_labels() -> None:
    for spread in SPREADS.values():
        keys = [p.key for p in spread.positions]
        assert len(set(keys)) == len(keys)
        for position in spread.positions:
            assert position.label.strip()
            assert position.label_zh.strip()
            assert position.meaning.strip()


# --- Draw behaviour ---------------------------------------------------------


def test_celtic_cross_draws_ten_unique_cards_in_position_order() -> None:
    result = draw_spread(spread_id="celtic_cross")
    assert len(result.cards) == 10
    assert len(set(result.drawn_ids)) == 10
    assert [c.position_index for c in result.cards] == list(range(10))
    assert [c.position_key for c in result.cards] == [p.key for p in SPREADS["celtic_cross"].positions]


def test_reversals_disabled_yields_all_upright() -> None:
    result = draw_spread(spread_id="celtic_cross", allow_reversed=False)
    assert all(c.orientation == "upright" for c in result.cards)
    assert result.reversed_count == 0
    assert result.allow_reversed is False


def test_reversals_enabled_produce_both_orientations_over_many_draws() -> None:
    seen: set[str] = set()
    for _ in range(40):
        result = draw_spread(spread_id="celtic_cross", allow_reversed=True)
        seen.update(c.orientation for c in result.cards)
        if seen == {"upright", "reversed"}:
            break
    assert seen == {"upright", "reversed"}


def test_drawn_card_fields_agree_with_orientation() -> None:
    result = draw_spread(spread_id="three_card")
    for card in result.cards:
        source = get_card(card.card_id)
        assert card.name == source.name
        assert card.arcana == source.arcana
        assert card.keywords == list(source.keywords(card.orientation))
        assert card.meaning == source.meaning(card.orientation)
        # 配对的另一半：中文侧必须由**同一个 orientation** 决定，接反了读起来完全通顺。
        # 变异复核的形状：把引擎那格的 `card.meaning_zh(orientation)` 改成 `meaning_zh("upright")`
        # 之后，只有**本张牌是逆位**时断言才会红，而三张全正位的概率是 1/8（复测：
        # `cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "print(0.5**3)"` →
        # `0.125`）。实测该变异跑 20 轮红 19 / 绿 1 —— 所以单轮看见绿**不等于门是空的**，要多跑几轮。
        assert card.keywords_zh == list(source.keywords_zh(card.orientation))
        assert card.meaning_zh == source.meaning_zh(card.orientation)
        assert card.position_meaning_zh != card.position_meaning


def test_synthesis_references_question_and_spread() -> None:
    result = draw_spread(spread_id="single", question="Should I take the offer?")
    assert result.question == "Should I take the offer?"
    assert "Celtic Cross" not in result.synthesis
    assert result.synthesis.strip()


def test_major_and_reversed_counts_match_cards() -> None:
    result = draw_spread(spread_id="celtic_cross")
    assert result.major_arcana_count == sum(1 for c in result.cards if c.arcana == "major")
    assert result.reversed_count == sum(1 for c in result.cards if c.orientation == "reversed")


def test_draws_are_varied_not_deterministic() -> None:
    first = draw_spread(spread_id="celtic_cross").drawn_ids
    second = draw_spread(spread_id="celtic_cross").drawn_ids
    assert first != second


def test_unknown_spread_raises() -> None:
    with pytest.raises(UnsupportedMethodError):
        draw_spread(spread_id="not_a_spread")


def test_the_chinese_half_of_every_text_field_is_required() -> None:
    """新字段是契约不是装饰：从真实响应里删掉任一格，模型必须拒绝。

    为什么不用「少字段仍然 200」那种写法：那证明的是 pydantic 容许缺席，而本期要的正好相反
    （G12）。这里先拿真响应 `model_dump()` 再逐格删，删的是**这一次真实抽取**的字段，
    所以证明的是「这条 JSON 契约少一格就立不住」（spec §8「字段自身归 pydantic」那一支，
    AGENTS.md §4）。
    """
    result = draw_spread(spread_id="three_card", question="required fields?")
    payload = result.model_dump()

    for field in ("position_meaning_zh", "keywords_zh", "meaning_zh"):
        broken_card = {k: v for k, v in payload["cards"][0].items() if k != field}
        with pytest.raises(ValidationError) as excinfo:
            DrawnCard.model_validate(broken_card)
        assert field in str(excinfo.value)

    for field in ("spread_description_zh", "cards"):
        broken_response = {k: v for k, v in payload.items() if k != field}
        with pytest.raises(ValidationError) as excinfo:
            TarotSpreadResponse.model_validate(broken_response)
        assert field in str(excinfo.value)


# --- HTTP adapter -----------------------------------------------------------


def test_tarot_spread_endpoint(client: TestClient) -> None:
    response = client.post(
        "/api/v1/tarot/spread",
        json={"spread_id": "three_card", "allow_reversed": True, "question": "test"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["spread_id"] == "three_card"
    assert len(body["cards"]) == 3
    assert len(set(body["drawn_ids"])) == 3
    assert body["rng"] == "secrets"
    assert body["engine"] == "content-library"


def test_tarot_endpoint_returns_both_halves_of_every_text_field(client: TestClient) -> None:
    """端点侧的配对凭据：四对字段两两成对（牌阵描述 1 对 + 每张牌 3 对），且中文侧非空、与英文侧不同串。

    内容层的不重复/长度/措辞门在 `tests/content/test_tarot_zh_corpus.py`，这里只钉
    「装配发生了、方向没接反、契约字段一个都没少」——同一件事两处断言就两份口径（AGENTS.md §2
    的那条精神在 backend 内部同样适用）。
    """
    body = client.post(
        "/api/v1/tarot/spread",
        json={"spread_id": "celtic_cross", "allow_reversed": True, "question": "both halves"},
    ).json()
    assert body["spread_description_zh"] and body["spread_description_zh"] != body["spread_description"]
    assert len(body["cards"]) == 10
    for card in body["cards"]:
        assert card["meaning_zh"] and card["meaning_zh"] != card["meaning"]
        assert card["position_meaning_zh"] and card["position_meaning_zh"] != card["position_meaning"]
        assert len(card["keywords_zh"]) == len(card["keywords"]) > 0
        assert card["keywords_zh"] != card["keywords"]


def test_tarot_spread_endpoint_rejects_unknown_spread(client: TestClient) -> None:
    response = client.post("/api/v1/tarot/spread", json={"spread_id": "nope"})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "unsupported_method"
