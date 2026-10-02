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
from app.engines.tarot import _synthesize, draw_spread
from app.schemas.tarot import DrawnCard, TarotSpreadResponse
from tests.plain_wording import FORBIDDEN, advice_hits

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
    """整段 synthesis 里出现的是**本次那个阵**的中英双名，别的阵名一个都不串。

    改前的写法是 `assert "Celtic Cross" not in result.synthesis`（现 `:157`，T5 动手前的复测：
    `cd backend && grep -n "Celtic Cross\" not in" tests/golden/test_tarot_golden.py`），而那次抽的是
    `single`——`celtic_cross` 的英文名当时**根本没可能**出现在句子里，这条断言恒真
    （spec §8 明令要消灭的那一类「看着像测过」）。中文框架句里阵名是真插值，所以现在
    可以钉「在位」与「不串台」两件事。
    """
    result = draw_spread(spread_id="single", question="Should I take the offer?")
    assert result.question == "Should I take the offer?"
    assert "本次以 单张牌（Single Card）为这个问题布阵：Should I take the offer?" in result.synthesis
    for other in ("凯尔特十字", "时间之流三张", "关系牌阵", "事业牌阵", "是非抉择牌阵"):
        assert other not in result.synthesis
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


# --- Synthesis frames -------------------------------------------------------


def _card_into(card_id: str, position, index: int, orientation: str) -> DrawnCard:
    """从真表装一张真牌到真位次上，只为把 `_synthesize` 的计数分支钉到可复现。"""
    source = get_card(card_id)
    return DrawnCard(
        position_index=index,
        position_key=position.key,
        position_label=position.label,
        position_label_zh=position.label_zh,
        position_meaning=position.meaning,
        position_meaning_zh=position.meaning_zh,
        card_id=source.id,
        name=source.name,
        name_zh=source.name_zh,
        arcana=source.arcana,
        number=source.number,
        suit=source.suit,
        rank=source.rank,
        element=source.element,
        orientation=orientation,
        keywords=list(source.keywords(orientation)),
        keywords_zh=list(source.keywords_zh(orientation)),
        meaning=source.meaning(orientation),
        meaning_zh=source.meaning_zh(orientation),
    )


def test_synthesis_frames_are_pinned_verbatim_question_major_many_all_upright() -> None:
    """框架钉 ①：`lead_question` + `per_card`（正位）+ `major_many` + `all_upright`。

    四句合成**一整串**逐字对账，句与句之间那个空格就是引擎的 `join`，所以「句子本身对但
    拼接变了形状」也红。为什么不用「`overview(引擎的 frame, parts) == result.synthesis`」
    那种写法：见 `tests/golden/test_kabbalah_golden.py:414-436` 那段理由（拿唯一正主自己
    拼再跟自己比是恒等式，什么也没钉）。
    """
    spread = SPREADS["single"]
    cards = [_card_into("major-00", spread.positions[0], 0, "upright")]
    assert _synthesize(spread, cards, "Should I take the offer?", 1, 0, True) == " ".join(
        [
            "本次以 单张牌（Single Card）为这个问题布阵：Should I take the offer?",
            "指引（Guidance）抽出 愚人（The Fool），正位，取的是 开端、纯真、随性。",
            "1 张牌里有 1 张大牌，那些超出你当下掌控的人生主题与力量正明显起作用。",
            "所有牌都落正位，这些能量表达得清楚，没有被挡。",
        ]
    )


def test_synthesis_frames_are_pinned_verbatim_plain_minor_reversed_no_major() -> None:
    """框架钉 ②：`lead_plain` + `per_card`（逆位）+ `no_major` + `some_reversed`。"""
    spread = SPREADS["three_card"]
    cards = [_card_into("pentacles-05", spread.positions[0], 0, "reversed")]
    assert _synthesize(spread, cards, None, 0, 1, True) == " ".join(
        [
            "本次以 时间之流三张（Three Card）布阵。",
            "过去（Past）抽出 星币五（Five of Pentacles），逆位，取的是 从损失里回血、灵性上的贫瘠、重新燃起的希望。",
            "一张大牌也没有出现，所以这次讲的是日常的、你能直接上手的现实力量，而不是更大的人生主题。",
            "1 张逆位，指向被阻滞、被内收或被延迟的能量，它们要的是被看清，不是被硬推。",
        ]
    )


def test_synthesis_frames_are_pinned_verbatim_major_some_and_the_reversal_skip() -> None:
    """框架钉 ③：`major_some`，以及 `allow_reversed=False` 时**不出现**取向那一句。

    三张牌里 1 张大牌（`1 * 2 >= 3` 为假）走 `major_some`；`allow_reversed=False` 走的是
    引擎里 `if allow_reversed:` 那个分支的假侧——今天没有任何一条测钉过「不该出现的句子
    确实没出现」，而 `total`/`major` 两个插值都来自调用参数，`major_arcana_count` 那格由
    `test_major_and_reversed_counts_match_cards` 另行对账，所以这里写死数字不是自证。
    """
    spread = SPREADS["three_card"]
    cards = [
        _card_into("major-00", spread.positions[0], 0, "upright"),
        _card_into("wands-03", spread.positions[1], 1, "upright"),
        _card_into("cups-06", spread.positions[2], 2, "upright"),
    ]
    assert _synthesize(spread, cards, None, 1, 0, False) == " ".join(
        [
            "本次以 时间之流三张（Three Card）布阵。",
            "过去（Past）抽出 愚人（The Fool），正位，取的是 开端、纯真、随性。",
            "现在（Present）抽出 权杖三（Three of Wands），正位，取的是 准备、先见、事业开创。",
            "未来（Future）抽出 圣杯六（Six of Cups），正位，取的是 重访旧日、童年记忆、纯真。",
            "1 张大牌在这份日常处境里标出分量更重、由不得你选的线索。",
        ]
    )


def test_an_assembled_synthesis_passes_the_wording_gates() -> None:
    """六个阵各抽一次（正逆位两种开关），装配后的整段 `synthesis` 过禁串与建议词门。

    `assert "布阵" in text` 那一句是**必要**的，不是装饰：没有它，这条测在改前的英文模板上
    照样全绿（英文里既没有「；」也没有六个建议字），那条门就成了一条恒真断言——spec §8
    警告的正是这种「看着像测过」。
    """
    for spread_id in SPREADS:
        for allow_reversed in (True, False):
            text = draw_spread(spread_id=spread_id, allow_reversed=allow_reversed).synthesis
            assert "布阵" in text, spread_id
            for banned in FORBIDDEN:
                assert banned not in text, f"{spread_id}: {banned!r}"
            assert advice_hits(text) == [], (spread_id, advice_hits(text))
