"""Tarot draw engine: cryptographically secure draws over the curated 78-card deck.

This module is a pure function over :mod:`app.content.tarot_deck`. Card
selection and orientation use :mod:`secrets` (an OS-backed CSPRNG), never the
``random`` module, satisfying PRD 4.4. Interpretations are not generated: the
synthesis is composed deterministically from the real card meanings and spread
position texts, so every word returned traces back to the content library.
"""

import secrets

from app.content.tarot_deck import DECK, Spread, get_spread
from app.core.errors import UnsupportedMethodError
from app.schemas.tarot import DrawnCard, TarotSpreadResponse

# A single OS-backed generator; secrets.SystemRandom is stateless across calls
# (it draws from os.urandom), so a module-level instance is safe to reuse.
_RNG = secrets.SystemRandom()

_ORIENTATIONS = ("upright", "reversed")

#: 取向的中文说法只在框架句里出现；表里的 `orientation` 值仍是英文（`upright` | `reversed`）。
_ORIENTATION_ZH = {"upright": "正位", "reversed": "逆位"}


def draw_spread(
    *,
    spread_id: str,
    allow_reversed: bool = True,
    question: str | None = None,
) -> TarotSpreadResponse:
    """Draw and interpret a tarot spread.

    Raises :class:`UnsupportedMethodError` when ``spread_id`` is not a defined
    spread. Cards are drawn without replacement, so a spread never repeats a
    card; each card is then oriented upright or reversed (independently, by
    secure draw) when ``allow_reversed`` is set.
    """
    spread = get_spread(spread_id)
    if spread is None:
        raise UnsupportedMethodError(f"Unknown tarot spread: {spread_id!r}")

    # Sample without replacement: sample() guarantees unique elements.
    drawn_cards = _RNG.sample(DECK, spread.size)

    cards: list[DrawnCard] = []
    for index, (card, position) in enumerate(zip(drawn_cards, spread.positions)):
        orientation = _RNG.choice(_ORIENTATIONS) if allow_reversed else "upright"
        cards.append(
            DrawnCard(
                position_index=index,
                position_key=position.key,
                position_label=position.label,
                position_label_zh=position.label_zh,
                position_meaning=position.meaning,
                position_meaning_zh=position.meaning_zh,
                card_id=card.id,
                name=card.name,
                name_zh=card.name_zh,
                arcana=card.arcana,
                number=card.number,
                suit=card.suit,
                rank=card.rank,
                element=card.element,
                orientation=orientation,
                keywords=list(card.keywords(orientation)),
                keywords_zh=list(card.keywords_zh(orientation)),
                meaning=card.meaning(orientation),
                meaning_zh=card.meaning_zh(orientation),
            )
        )

    major_count = sum(1 for c in cards if c.arcana == "major")
    reversed_count = sum(1 for c in cards if c.orientation == "reversed")
    synthesis = _synthesize(spread, cards, question, major_count, reversed_count, allow_reversed)

    return TarotSpreadResponse(
        spread_id=spread.id,
        spread_name=spread.name,
        spread_name_zh=spread.name_zh,
        spread_description=spread.description,
        spread_description_zh=spread.description_zh,
        question=question,
        cards=cards,
        drawn_ids=[c.card_id for c in cards],
        allow_reversed=allow_reversed,
        synthesis=synthesis,
        major_arcana_count=major_count,
        reversed_count=reversed_count,
    )


def _lead_keywords_zh(card: DrawnCard, limit: int = 3) -> str:
    """Join a card's leading Chinese keywords for the drawn orientation."""
    return "、".join(card.keywords_zh[:limit]) if card.keywords_zh else card.name_zh


def _synthesize(
    spread: Spread,
    cards: list[DrawnCard],
    question: str | None,
    major_count: int,
    reversed_count: int,
    allow_reversed: bool,
) -> str:
    """Compose a reading from real card and position content (no fabrication)."""
    sentences: list[str] = []

    if question:
        sentences.append(
            f"本次以 {spread.name_zh}（{spread.name}）为这个问题布阵：{question.strip()}"
        )
    else:
        sentences.append(f"本次以 {spread.name_zh}（{spread.name}）布阵。")

    for card in cards:
        sentences.append(
            f"{card.position_label_zh}（{card.position_label}）抽出 {card.name_zh}（{card.name}），"
            f"{_ORIENTATION_ZH[card.orientation]}，取的是 {_lead_keywords_zh(card)}。"
        )

    total = len(cards)
    if major_count == 0:
        sentences.append(
            "一张大牌也没有出现，所以这次讲的是日常的、你能直接上手的现实力量，"
            "而不是更大的人生主题。"
        )
    elif major_count * 2 >= total:
        sentences.append(
            f"{total} 张牌里有 {major_count} 张大牌，"
            "那些超出你当下掌控的人生主题与力量正明显起作用。"
        )
    else:
        sentences.append(f"{major_count} 张大牌在这份日常处境里标出分量更重、由不得你选的线索。")

    if allow_reversed:
        if reversed_count == 0:
            sentences.append("所有牌都落正位，这些能量表达得清楚，没有被挡。")
        else:
            sentences.append(
                f"{reversed_count} 张逆位，指向被阻滞、被内收或被延迟的能量，"
                "它们要的是被看清，不是被硬推。"
            )

    return " ".join(sentences)
