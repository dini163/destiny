"""Pydantic schemas for the Tarot (塔罗) spread system.

Field names are snake_case end-to-end (the JSON contract mirrors these models)
so the frontend can consume responses without a mapping layer.
"""

from pydantic import BaseModel, Field

from app.schemas.common import ProvenanceTable


class TarotSpreadRequest(BaseModel):
    """Input for a tarot spread draw.

    ``spread_id`` selects a layout from the spread library (see PRD 6.7):
    ``single``, ``three_card``, ``celtic_cross``, ``relationship``, ``career``
    or ``decision``. When ``allow_reversed`` is true each drawn card is
    independently oriented upright or reversed by a cryptographically secure
    draw.
    """

    spread_id: str = Field(description="Spread layout id, e.g. celtic_cross.")
    allow_reversed: bool = Field(default=True, description="Whether cards may land reversed.")
    question: str | None = Field(default=None, description="Optional question the reading addresses.")


class TarotProvenance(BaseModel):
    """Reading provenance — engine, corpus version, source, method note and tables."""

    engine: str
    content_version: str
    source: str
    note: str = Field(description="洗牌/牌义取处/中英配对口径说明。")
    tables: list[ProvenanceTable] = Field(
        description="本响应真正读过的语料表（AGENTS §7：读了就列，宁缺勿多）。"
    )


class DrawnCard(BaseModel):
    """A single card drawn into one spread position."""

    position_index: int = Field(description="Zero-based order of the position in the spread.")
    position_key: str = Field(description="Stable position identifier, e.g. past.")
    position_label: str = Field(description="English position label, e.g. Recent Past.")
    position_label_zh: str = Field(description="Chinese position label, e.g. 近期过去.")
    position_meaning: str = Field(description="What this position reveals.")
    position_meaning_zh: str = Field(description="What this position reveals, in Chinese.")

    card_id: str = Field(description="Deck card id, e.g. major-00 or wands-07.")
    name: str
    name_zh: str
    arcana: str = Field(description="major | minor")
    number: int = Field(description="Major 0-21; minor 1-14 (11-14 are court).")
    suit: str | None = Field(description="wands | cups | swords | pentacles; null for majors.")
    rank: str | None = Field(description="Page | Knight | Queen | King; else null.")
    element: str | None = Field(description="fire | water | air | earth; null for majors.")
    orientation: str = Field(description="upright | reversed")
    keywords: list[str] = Field(description="Keywords for the drawn orientation.")
    keywords_zh: list[str] = Field(description="Chinese keywords for the drawn orientation.")
    meaning: str = Field(description="Interpretation text for the drawn orientation.")
    meaning_zh: str = Field(description="Interpretation text in Chinese for the drawn orientation.")


class TarotSpreadResponse(BaseModel):
    """Complete tarot spread produced by :mod:`app.engines.tarot`."""

    # Spread identity
    spread_id: str
    spread_name: str
    spread_name_zh: str
    spread_description: str
    spread_description_zh: str
    question: str | None = Field(description="The question echoed back, if provided.")

    # Draw
    cards: list[DrawnCard] = Field(description="Cards in spread-position order.")
    drawn_ids: list[str] = Field(description="Card ids in draw order (unique within the spread).")
    allow_reversed: bool = Field(description="Whether reversals were enabled for this draw.")
    synthesis: str = Field(description="A reading that connects the drawn cards and positions.")

    # Derived emphasis
    major_arcana_count: int = Field(description="How many drawn cards are Major Arcana.")
    reversed_count: int = Field(description="How many drawn cards landed reversed.")

    provenance: TarotProvenance

    rng: str = Field(default="secrets", description="Randomness source: Python secrets (CSPRNG).")
    engine: str = Field(default="content-library", description="Interpretations come from the curated deck.")
