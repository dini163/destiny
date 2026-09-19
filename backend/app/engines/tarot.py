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
                meaning=card.meaning(orientation),
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
        question=question,
        cards=cards,
        drawn_ids=[c.card_id for c in cards],
        allow_reversed=allow_reversed,
        synthesis=synthesis,
        major_arcana_count=major_count,
        reversed_count=reversed_count,
    )


def _lead_keywords(card: DrawnCard, limit: int = 3) -> str:
    """Join a card's leading keywords for the drawn orientation."""
    return ", ".join(card.keywords[:limit]) if card.keywords else card.name


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
        sentences.append(f"Reading the {spread.name} ({spread.name_zh}) for: {question.strip()}")
    else:
        sentences.append(f"Reading the {spread.name} ({spread.name_zh}).")

    for card in cards:
        orientation_phrase = "reversed" if card.orientation == "reversed" else "upright"
        sentences.append(
            f"{card.position_label} ({card.position_label_zh}) draws {card.name} "
            f"({card.name_zh}) {orientation_phrase}, highlighting {_lead_keywords(card)}."
        )

    total = len(cards)
    if major_count == 0:
        sentences.append(
            "No Major Arcana appeared, so the reading turns on everyday, practical "
            "forces you can act on directly rather than on larger destiny-level themes."
        )
    elif major_count * 2 >= total:
        sentences.append(
            f"With {major_count} of {total} cards being Major Arcana, powerful life "
            "themes and forces beyond your immediate control are strongly at work."
        )
    else:
        sentences.append(
            f"{major_count} Major Arcana card(s) mark the significant, fated threads "
            "running through an otherwise everyday situation."
        )

    if allow_reversed:
        if reversed_count == 0:
            sentences.append("Every card fell upright, suggesting these energies express themselves clearly and without obstruction.")
        else:
            sentences.append(
                f"{reversed_count} reversed card(s) point to energies that are blocked, "
                "internalised or delayed, and ask to be examined rather than forced."
            )

    return " ".join(sentences)
