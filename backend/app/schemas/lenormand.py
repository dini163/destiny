"""Pydantic schemas for the 雷诺曼 (Lenormand) system.

Field names are snake_case end-to-end. Lenormand is a card-draw system like tarot
but reads by **combination** (first card = subject, second = modifier) and never
reverses a card. The draw itself uses :mod:`secrets` (CSPRNG, PRD 4.4); every
meaning, keyword and combination phrase is composed from the curated 36-card
library, never invented at runtime.
"""

from pydantic import BaseModel, Field

from app.schemas.common import ProvenanceTable


class LenormandRequest(BaseModel):
    """Input for a Lenormand draw.

    ``spread_id`` selects a layout: ``single``, ``three_card``, ``five_card``,
    ``nine_card`` or ``grand_tableau``. ``significator`` optionally marks the
    querent ('male' → 男人 28, 'female' → 女人 29) so the engine can read the
    cards around it, which matters most in the 大桌全景.
    """

    spread_id: str = Field(description="Spread layout id, e.g. grand_tableau.")
    question: str | None = Field(default=None, max_length=120, description="Optional question the reading addresses.")
    significator: str | None = Field(default=None, description="male | female | null — the querent's 指示牌.")


class CardRef(BaseModel):
    """A compact reference to a card, used inside combinations and significator neighbours."""

    number: int
    name_zh: str
    essence: str


class Combination(BaseModel):
    """One 组合直读 pair: ``left`` is the subject, ``right`` the modifier."""

    left: CardRef
    right: CardRef
    phrase: str = Field(description="The combined read, ``right.as_modifier + left.essence``.")
    context: str = Field(description="Where this pair sits, e.g. 线性相邻 / 指示牌之前.")


class SignificatorInfo(BaseModel):
    """Where the querent's 指示牌 landed and what surrounds it (same row/column)."""

    number: int
    name_zh: str
    position_index: int
    row: int
    col: int
    behind: list[CardRef] = Field(description="Same row, to the left — the past behind the querent.")
    ahead: list[CardRef] = Field(description="Same row, to the right — the future ahead of the querent.")
    above: list[CardRef] = Field(description="Same column, above — conscious / overhead influences.")
    below: list[CardRef] = Field(description="Same column, below — subconscious / underlying influences.")


class DrawnCard(BaseModel):
    """A single card drawn into one spread position (always upright)."""

    position_index: int = Field(description="Zero-based order of the position in the spread.")
    position_key: str
    position_label_zh: str
    position_meaning: str
    row: int = Field(description="Grid row (0-based) for box/tableau layouts; 0 for a line.")
    col: int = Field(description="Grid column (0-based).")

    card_id: str
    number: int = Field(description="Card number 1-36.")
    name: str = Field(description="English name, e.g. Rider.")
    name_zh: str = Field(description="Chinese name, e.g. 骑士.")
    polarity: int = Field(description="+1 积极 | 0 中性 | -1 消极.")
    polarity_label: str = Field(description="积极 | 中性 | 消极.")
    keywords: list[str]
    essence: str = Field(description="名词核心, used as the subject in a combination.")
    meaning: str = Field(description="One-line core meaning.")
    as_modifier: str = Field(description="形容词性修饰, applied to a preceding card.")
    is_significator: bool = Field(default=False, description="This card is the querent's 指示牌.")


class LenormandProvenance(BaseModel):
    """Reading provenance — engine, corpus version, source and the method note."""

    engine: str
    content_version: str
    source: str
    note: str = Field(description="抽牌/组合直读/不逆位口径说明。")
    tables: list[ProvenanceTable] = Field(
        description="本响应真正读过的语料表（AGENTS §7：读了就列，宁缺勿多）。"
    )


class LenormandReading(BaseModel):
    """Complete Lenormand reading produced by :mod:`app.engines.lenormand`."""

    spread_id: str
    spread_name_zh: str
    spread_name_en: str
    layout: str = Field(description="line | box | tableau.")
    description: str
    question: str | None

    cards: list[DrawnCard] = Field(description="Cards in spread-position order.")
    drawn_ids: list[str] = Field(description="Card ids in draw order (unique within the spread).")
    combinations: list[Combination] = Field(description="组合直读 pairs the engine derived for this layout.")
    significator: SignificatorInfo | None = Field(default=None, description="指示牌定位（当请求指定且牌面出现时）。")
    synthesis: str = Field(description="A reading composed from the real card meanings and combinations.")

    positive_count: int = Field(description="How many drawn cards are 积极.")
    neutral_count: int = Field(description="How many drawn cards are 中性.")
    negative_count: int = Field(description="How many drawn cards are 消极.")
    plain_summary: str = Field(description="整阵白话：牌阵开篇句 + 按位序逐张牌义，行以 \\n 分隔。")

    rng: str = Field(default="secrets", description="Randomness source: Python secrets (CSPRNG).")
    engine: str = Field(default="lenormand-combination")
    provenance: LenormandProvenance
