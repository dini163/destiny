"""Pydantic schemas for the 西洋合盘 (Western Synastry & Composite) system.

Field names are snake_case end-to-end. This system compares two Western natal
charts and produces three things, all from Swiss Ephemeris (no mock):

* **Synastry aspects (合盘相位)** — the person-to-person aspects between every
  point of chart A and every point of chart B (ten planets plus ASC and MC),
  keeping the tightest orb per pair and labelling it with the standard harmony
  taxonomy (conjunction=fusion, sextile/trine=harmonious, square/opposition=
  challenging).
* **Composite chart (组合盘)** — the midpoint chart: each composite planet and
  house cusp is the shorter-arc midpoint of the two natal longitudes, a fully
  deterministic geometric construction that needs no ephemeris of its own.
* **Compatibility score (相契度)** — a self-explaining ledger over the counted
  synastry aspects (``Σ factors[].delta == value``).

The two natal charts are embedded verbatim as real :class:`WesternChart`s.
"""

from datetime import date, time

from pydantic import BaseModel, Field

from app.schemas.common import ProvenanceTable
from app.schemas.scoring import ScoreValue
from app.schemas.western import (
    Aspect,
    AxisPoint,
    HouseCusp,
    PlanetPlacement,
    WesternChart,
)


class SynastryPerson(BaseModel):
    """One person's birth data for the comparison.

    ``latitude``/``longitude`` may be supplied directly or resolved from ``city``.
    ``utc_offset_hours`` is the offset of the *local* birth time from UTC; when
    omitted it is approximated from the longitude (as for the natal chart).
    """

    birth_date: date = Field(description="Gregorian birth date.")
    birth_time: time = Field(description="Local clock birth time.")
    city: str | None = Field(default=None, description="City name for geocoding.")
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    utc_offset_hours: float | None = Field(
        default=None, ge=-14, le=14, description="Local-time offset from UTC in hours."
    )
    name: str | None = Field(default=None, max_length=40, description="称谓，仅回显，不进计算。")


class SynastryRequest(BaseModel):
    """Two birth profiles plus a house system shared by both charts and the composite."""

    person_a: SynastryPerson
    person_b: SynastryPerson
    house_system: str = Field(
        default="P", description="House system code (P=Placidus, K=Koch, R=Regiomontanus, W=Whole…)."
    )


class SynastryAspect(BaseModel):
    """A person-to-person aspect between one point of A and one point of B."""

    point_a: str = Field(description="Person A's point English name (a planet or ASC/MC).")
    point_a_zh: str
    point_a_glyph: str
    point_b: str = Field(description="Person B's point English name (a planet or ASC/MC).")
    point_b_zh: str
    point_b_glyph: str
    type: str = Field(description="conjunction | sextile | square | trine | opposition")
    glyph: str
    angle: float = Field(description="Exact aspect angle in degrees.")
    orb: float = Field(description="Absolute deviation from the exact angle.")
    nature: str = Field(description="fusion | harmonious | challenging")
    nature_zh: str
    core_bond: bool = Field(
        description="Whether this pair is one of the classic relationship axes (scored with emphasis)."
    )
    counted: bool = Field(
        description="Whether this aspect contributes to the score (both endpoints are personal points)."
    )


class CompositeChart(BaseModel):
    """The midpoint (composite) chart of the two natals.

    Every longitude is the shorter-arc midpoint of the two natal longitudes, so the
    chart is a deterministic geometric construction. Composite planets carry
    ``retrograde=False`` and ``speed=0.0``: a midpoint is not a moving body, so its
    speed is meaningless (mirrors the solar-arc layer's directed points).
    """

    method: str = Field(
        default="midpoint",
        description="Construction method: shorter-arc midpoint of the two natal longitudes.",
    )
    sun_sign: str
    sun_sign_zh: str
    moon_sign: str
    moon_sign_zh: str
    ascendant_sign: str
    ascendant_sign_zh: str
    planets: list[PlanetPlacement] = Field(description="Ten composite bodies: Sun..Pluto (midpoints).")
    axes: list[AxisPoint] = Field(description="Composite ASC, DES, MC, IC.")
    houses: list[HouseCusp] = Field(description="Twelve composite house cusps (cusp midpoints).")
    aspects: list[Aspect] = Field(description="Major aspects among the composite planets.")
    element_balance: dict[str, int] = Field(description="fire/earth/air/water counts among composite planets.")
    modality_balance: dict[str, int] = Field(description="cardinal/fixed/mutable counts among composite planets.")


class SynastryProvenance(BaseModel):
    """Provenance + the method note explaining synastry, composite and the score."""

    engine: str
    note: str
    method: str
    tables: list[ProvenanceTable] = Field(description="本页真正读到的表，来自 SYNASTRY_CONTENT_SOURCES。")


class SynastryChart(BaseModel):
    """Complete synastry / composite reading for two people."""

    person_a_name: str = Field(description="Person A's display name (or a default label).")
    person_b_name: str = Field(description="Person B's display name (or a default label).")
    person_a: WesternChart = Field(description="Person A's real natal chart.")
    person_b: WesternChart = Field(description="Person B's real natal chart.")
    synastry_aspects: list[SynastryAspect] = Field(description="Person-to-person aspects, tightest first.")
    composite: CompositeChart
    score: ScoreValue = Field(description="相契度总分与逐条账本（Σ factors[].delta == value）。")
    provenance: SynastryProvenance
    engine: str = Field(default="pyswisseph")
