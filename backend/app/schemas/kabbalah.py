"""Pydantic schemas for the 卡巴拉生命之树 (Kabbalah Tree of Life) system.

Field names are snake_case end-to-end. Kabbalah is a *reference map* system, not a
random draw: the ten Sephiroth and twenty-two Paths are fixed Golden Dawn content,
served whole by ``GET /tree`` so the frontend can render and explore the Tree. The
optional ``POST /gematria`` endpoint folds a word's numerical value onto that fixed
map — the numbers are computed deterministically and every meaning is drawn from the
curated content, never invented at runtime.
"""

from pydantic import BaseModel, Field

from app.schemas.common import PlainSection, ProvenanceTable


class PillarInfo(BaseModel):
    """One of the three columns of the Tree (慈悲 / 严厉 / 平衡)."""

    id: str
    name_zh: str
    name_en: str
    side: str
    virtue: str


class SephirahNode(BaseModel):
    """A single emanation (原质), positioned for rendering."""

    number: int = Field(description="1-10; 0 marks the hidden Daath.")
    id: str
    name_hebrew: str
    name: str
    name_zh: str
    meaning: str
    plain_meaning: str = Field(
        description="逐条对应 `meaning` 的白话转述（`content/kabbalah_plain.py`），必填：缺白话即视为伪造响应（spec §9）。"
    )
    keywords: list[str]
    pillar: str
    pillar_name_zh: str
    world: str
    world_name_zh: str
    sphere: str = Field(description="Planetary / elemental sphere, e.g. 土星 Saturn.")
    color: str = Field(description="King-Scale hex, adapted for the dark ground.")
    archangel: str
    divine_name: str
    x: float = Field(description="Normalised 0-1 horizontal position.")
    y: float = Field(description="Normalised 0-1 vertical position (0 = crown).")
    is_hidden: bool = Field(default=False, description="True for Daath, the veiled node.")


class PathNode(BaseModel):
    """One of the 22 paths joining two Sephiroth (a Hebrew letter + Tarot trump)."""

    number: int = Field(description="Golden Dawn path number 11-32.")
    id: str
    from_sephirah: int
    to_sephirah: int
    from_name_zh: str
    to_name_zh: str
    letter: str
    letter_name: str
    letter_zh: str
    letter_value: int = Field(description="Gematria value of the Hebrew letter.")
    tarot: str
    tarot_zh: str
    tarot_numeral: str = Field(description="Golden Dawn numeral (力量 VIII / 正义 XI).")
    correspondence: str = Field(description="Planet / sign / element, e.g. 狮子座 Leo.")
    meaning: str
    plain_meaning: str = Field(
        description="逐条对应 `meaning` 的白话转述（`content/kabbalah_plain.py`），必填：缺白话即视为伪造响应（spec §9）。"
    )


class KabbalahProvenance(BaseModel):
    """Provenance — engine, corpus version, source, the tables actually read, and the method note."""

    engine: str
    content_version: str
    source: str
    note: str
    tables: list[ProvenanceTable] = Field(
        description="本响应真读到的语料表：原表 `kabbalah` 与其白话转述表 `kabbalah_plain`（G19：读了就列）。"
    )


class KabbalahTree(BaseModel):
    """The complete Tree of Life, served by ``GET /kabbalah/tree``."""

    pillars: list[PillarInfo]
    worlds: list[str] = Field(description="The four worlds, crown → root order.")
    sephiroth: list[SephirahNode] = Field(description="The ten Sephiroth, 1-10.")
    daath: SephirahNode | None = Field(default=None, description="The hidden Daath node (number 0).")
    paths: list[PathNode] = Field(description="The twenty-two paths, 11-32.")
    sephirah_count: int = Field(default=10)
    path_count: int = Field(default=22)
    plain: list[PlainSection] = Field(
        description="整树总论三节（静态）：全树读法、三柱与四界、光流与深渊（批次二 spec §6）。"
    )
    provenance: KabbalahProvenance


class GematriaRequest(BaseModel):
    """Input for the gematria fold: any word or name (Latin letters are read)."""

    text: str = Field(min_length=1, max_length=64, description="A word or name to weigh on the Tree.")


class LetterValue(BaseModel):
    """One Latin letter's contribution to the gematria total."""

    letter: str
    ordinal: int = Field(description="A=1 … Z=26.")
    reduction: int = Field(description="A=1 … I=9, J=1 … R=9, S=1 … Z=9.")


class GematriaReading(BaseModel):
    """A word's numerical essence folded onto the fixed Tree (``POST /gematria``)."""

    text: str
    normalized: str = Field(description="The Latin letters actually weighed, upper-cased.")
    breakdown: list[LetterValue]
    english_ordinal: int = Field(description="Sum of A=1…Z=26.")
    english_reduction: int = Field(description="Sum of the digit-reduced letter values.")
    digital_root: int = Field(description="Ordinal reduced to a single digit 1-9.")
    sephirah: SephirahNode = Field(description="The Sephirah the ordinal resonates with.")
    path: PathNode = Field(description="The Path the ordinal resonates with.")
    synthesis: str
    provenance: KabbalahProvenance
