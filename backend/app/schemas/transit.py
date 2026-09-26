"""Pydantic schemas for the 行运推运 (Transit & Progression) system.

Field names are snake_case end-to-end. This system layers three predictive
techniques over a Western natal chart, all computed from Swiss Ephemeris:

* **Transits (行运)** — where the planets actually are on a target date, and the
  aspects they make to the natal chart.
* **Secondary progressions (次限)** — the "day-for-a-year" progressed chart, its
  angles and its aspects to the natal.
* **Solar arc (太阳弧)** — every natal point advanced by the arc the progressed Sun
  has travelled, and the aspects those directed points make to the natal.

The embedded ``natal`` chart is the real :class:`WesternChart` (no mock); aspects
are geometric detections with classical orbs plus a standard nature taxonomy — no
personalised fortune is invented at runtime.
"""

from datetime import date, time

from pydantic import BaseModel, Field

from app.schemas.western import WesternChart


class TransitRequest(BaseModel):
    """Birth data (as for the natal chart) plus the target date to project onto."""

    birth_date: date = Field(description="Gregorian birth date.")
    birth_time: time = Field(description="Local clock birth time.")
    city: str | None = Field(default=None, description="City name for geocoding.")
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    utc_offset_hours: float | None = Field(default=None, ge=-14, le=14)
    house_system: str = Field(default="P", description="House system code (P=Placidus, K=Koch, R, E, W…).")
    target_date: date = Field(description="The date transits/progressions are projected onto (must not precede birth).")


class MovingPoint(BaseModel):
    """A planet's position in a *moving* layer (transit / progressed / directed)."""

    name: str
    glyph: str
    name_zh: str
    longitude: float = Field(description="Tropical ecliptic longitude, 0-360.")
    sign: str
    sign_zh: str
    sign_glyph: str
    sign_index: int = Field(ge=0, le=11)
    degree_in_sign: float
    degree_text: str
    natal_house: int = Field(ge=1, le=12, description="Which *natal* house this moving body falls in.")
    retrograde: bool
    speed: float


class AnglePoint(BaseModel):
    """A progressed chart angle (ASC / MC), which has no natal-house meaning of its own."""

    name: str = Field(description="ASC | MC")
    label: str
    longitude: float
    sign: str
    sign_zh: str
    sign_index: int
    degree_in_sign: float
    degree_text: str


class CrossAspect(BaseModel):
    """An aspect from a moving-layer body to a natal point."""

    moving: str = Field(description="Moving body's English name, e.g. Saturn.")
    moving_zh: str
    moving_glyph: str
    natal: str = Field(description="Natal point's English name (a planet or ASC/MC).")
    natal_zh: str
    type: str = Field(description="conjunction | sextile | square | trine | opposition")
    glyph: str
    angle: float
    orb: float
    nature: str = Field(description="fusion | harmonious | challenging")
    nature_zh: str


class ProgressionBlock(BaseModel):
    """Secondary-progression results for the target date."""

    progressed_date: str = Field(description="The 'day-for-a-year' chart date (birth + age in days).")
    progressed_julian_day: float
    age_years: float = Field(description="Decimal years from birth to the target date.")
    positions: list[MovingPoint] = Field(description="Progressed planets.")
    angles: list[AnglePoint] = Field(description="Progressed ASC and MC.")
    aspects: list[CrossAspect] = Field(description="Progressed-to-natal aspects, tightest first.")
    moon_sign_zh: str = Field(description="Progressed Moon's sign — the key progression marker.")
    moon_natal_house: int = Field(description="Natal house the progressed Moon now transits.")


class SolarArcBlock(BaseModel):
    """Solar-arc direction results for the target date."""

    arc_degrees: float = Field(description="Progressed Sun's travel from the natal Sun (≈ 1°/year).")
    arc_text: str = Field(description="The arc as degrees/minutes, e.g. 30°12'.")
    positions: list[MovingPoint] = Field(description="Natal points directed forward by the arc.")
    aspects: list[CrossAspect] = Field(description="Directed-to-natal aspects, tightest first.")


class TransitProvenance(BaseModel):
    """Provenance + the method note explaining all three techniques."""

    engine: str
    note: str


class TransitChart(BaseModel):
    """Complete transit / progression reading over the natal chart."""

    natal: WesternChart = Field(description="The embedded real natal chart (base of the overlay).")
    target_date: str
    target_julian_day: float

    transit_positions: list[MovingPoint] = Field(description="Where the planets are on the target date (noon UT).")
    transit_aspects: list[CrossAspect] = Field(description="Transit-to-natal aspects, tightest first.")

    progression: ProgressionBlock
    solar_arc: SolarArcBlock

    provenance: TransitProvenance
    engine: str = Field(default="pyswisseph")
