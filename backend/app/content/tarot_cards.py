"""Tarot card model and construction helpers.

The 78-card Rider-Waite-Smith (RWS) deck is split into the 22 Major Arcana and
the 56 Minor Arcana (four suits of Ace-Ten plus four court cards). Card data is
authored in :mod:`app.content.tarot_major` and :mod:`app.content.tarot_minor`
and assembled into the full deck by :mod:`app.content.tarot_deck`. Meanings
follow standard RWS interpretation; nothing is generated at runtime.
The Chinese half of every text field is paired on the same row of the same table
(丁组 spec §6.1「补配对」), and the Chinese keywords are assembled from
:mod:`app.content.tarot_keywords_zh`.
"""

from dataclasses import dataclass
from typing import Sequence

from app.content.tarot_keywords_zh import KEYWORD_ZH

# Suit -> classical element (unambiguous for the Minor Arcana).
SUIT_ELEMENT = {
    "wands": "fire",
    "cups": "water",
    "swords": "air",
    "pentacles": "earth",
}

SUIT_NAME_ZH = {
    "wands": "权杖",
    "cups": "圣杯",
    "swords": "宝剑",
    "pentacles": "星币",
}

# Court-card ranks occupy minor numbers 11-14.
COURT_RANKS = {11: "Page", 12: "Knight", 13: "Queen", 14: "King"}


@dataclass(frozen=True)
class TarotCard:
    """A single tarot card with upright and reversed interpretations."""

    id: str
    arcana: str                    # "major" | "minor"
    number: int                    # major: 0-21; minor: 1-14 (11-14 are court)
    name: str
    name_zh: str
    suit: str | None               # None for the Major Arcana
    rank: str | None               # Page/Knight/Queen/King, else None
    element: str | None
    upright_keywords: tuple[str, ...]
    upright_keywords_zh: tuple[str, ...]
    reversed_keywords: tuple[str, ...]
    reversed_keywords_zh: tuple[str, ...]
    upright_meaning: str
    upright_meaning_zh: str
    reversed_meaning: str
    reversed_meaning_zh: str

    def keywords(self, orientation: str) -> tuple[str, ...]:
        """Return the keyword tuple for an orientation (upright/reversed)."""
        return self.reversed_keywords if orientation == "reversed" else self.upright_keywords

    def keywords_zh(self, orientation: str) -> tuple[str, ...]:
        """Return the Chinese keyword tuple for an orientation."""
        return self.reversed_keywords_zh if orientation == "reversed" else self.upright_keywords_zh

    def meaning(self, orientation: str) -> str:
        """Return the meaning text for an orientation (upright/reversed)."""
        return self.reversed_meaning if orientation == "reversed" else self.upright_meaning

    def meaning_zh(self, orientation: str) -> str:
        """Return the Chinese meaning text for an orientation."""
        return self.reversed_meaning_zh if orientation == "reversed" else self.upright_meaning_zh


def _keywords_zh(words: Sequence[str]) -> tuple[str, ...]:
    """Translate one orientation's keyword tuple through the single table.

    缺席的英文词在这里抛 `KeyError`，是刻意的：译表漏一行的后果是「这张牌起不来」，
    而不是「响应里少一个中文词」——前者 collect 阶段就红，后者会一路绿到页面。
    """
    return tuple(KEYWORD_ZH[word] for word in words)


def major(
    number: int,
    name: str,
    name_zh: str,
    upright_keywords: Sequence[str],
    reversed_keywords: Sequence[str],
    upright_meaning: str,
    reversed_meaning: str,
    upright_meaning_zh: str,
    reversed_meaning_zh: str,
) -> TarotCard:
    """Build a Major Arcana card (id ``major-NN``)."""
    return TarotCard(
        id=f"major-{number:02d}",
        arcana="major",
        number=number,
        name=name,
        name_zh=name_zh,
        suit=None,
        rank=None,
        element=None,
        upright_keywords=tuple(upright_keywords),
        upright_keywords_zh=_keywords_zh(upright_keywords),
        reversed_keywords=tuple(reversed_keywords),
        reversed_keywords_zh=_keywords_zh(reversed_keywords),
        upright_meaning=upright_meaning,
        upright_meaning_zh=upright_meaning_zh,
        reversed_meaning=reversed_meaning,
        reversed_meaning_zh=reversed_meaning_zh,
    )


def minor(
    suit: str,
    number: int,
    name: str,
    name_zh: str,
    upright_keywords: Sequence[str],
    reversed_keywords: Sequence[str],
    upright_meaning: str,
    reversed_meaning: str,
    upright_meaning_zh: str,
    reversed_meaning_zh: str,
) -> TarotCard:
    """Build a Minor Arcana card (id ``<suit>-NN``); court ranks come from number."""
    return TarotCard(
        id=f"{suit}-{number:02d}",
        arcana="minor",
        number=number,
        name=name,
        name_zh=name_zh,
        suit=suit,
        rank=COURT_RANKS.get(number),
        element=SUIT_ELEMENT[suit],
        upright_keywords=tuple(upright_keywords),
        upright_keywords_zh=_keywords_zh(upright_keywords),
        reversed_keywords=tuple(reversed_keywords),
        reversed_keywords_zh=_keywords_zh(reversed_keywords),
        upright_meaning=upright_meaning,
        upright_meaning_zh=upright_meaning_zh,
        reversed_meaning=reversed_meaning,
        reversed_meaning_zh=reversed_meaning_zh,
    )
