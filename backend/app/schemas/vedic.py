"""Pydantic schemas for the 吠陀占星 (Vedic / Jyotish) system.

Field names are snake_case end-to-end. The chart is computed on the *sidereal*
zodiac (Lahiri ayanamsa) with whole-sign houses reckoned from the Lagna, carries
each graha's nakshatra and pada, and derives the Vimshottari dasha timeline from
the natal Moon. All positions are real (Swiss Ephemeris); the dasha is a standard
deterministic period system — no personalised fortune is invented at runtime.
"""

from datetime import date, time

from pydantic import BaseModel, Field

#: How the UTC offset was resolved (shared convention with the Western chart).
UtcOffsetSource = str


class VedicNatalRequest(BaseModel):
    """Birth data for a Vedic chart; ``target_date`` marks the live dasha period."""

    birth_date: date = Field(description="Gregorian birth date.")
    birth_time: time = Field(description="Local clock birth time.")
    city: str | None = Field(default=None, description="City name for geocoding.")
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    utc_offset_hours: float | None = Field(default=None, ge=-14, le=14)
    target_date: date | None = Field(
        default=None, description="Date whose Vimshottari period to mark current; defaults to today."
    )


class VedicPlanet(BaseModel):
    """A graha's sidereal position, sign, whole-sign house and nakshatra."""

    name: str
    glyph: str
    name_zh: str
    name_sa: str = Field(description="Sanskrit name, e.g. Surya.")
    longitude: float = Field(description="Sidereal ecliptic longitude, 0-360.")
    sign: str
    sign_zh: str
    sign_glyph: str
    sign_index: int = Field(ge=0, le=11)
    degree_in_sign: float
    degree_text: str
    house: int = Field(ge=1, le=12, description="Whole-sign house counted from the Lagna.")
    nakshatra: str
    nakshatra_zh: str
    nakshatra_devanagari: str
    nakshatra_lord: str = Field(description="Vimshottari lord graha of this nakshatra.")
    nakshatra_lord_zh: str
    pada: int = Field(ge=1, le=4, description="Nakshatra quarter (1-4).")
    retrograde: bool
    speed: float


class RashiCell(BaseModel):
    """One sign (rashi) of the chart, with the grahas occupying it."""

    sign_index: int = Field(ge=0, le=11)
    sign: str
    sign_zh: str
    sign_glyph: str
    house: int = Field(ge=1, le=12, description="Whole-sign house counted from the Lagna.")
    is_lagna: bool = Field(description="True when this sign holds the Ascendant (house 1).")
    planet_names: list[str] = Field(description="Grahas in this sign, in Navagraha order.")


class Antardasha(BaseModel):
    """A sub-period (bhukti) within a mahadasha."""

    lord: str
    lord_zh: str
    glyph: str
    start_date: str
    end_date: str
    years: float
    is_current: bool = False


class Mahadasha(BaseModel):
    """A major Vimshottari period with its nine antardashas."""

    lord: str
    lord_zh: str
    glyph: str
    start_date: str
    end_date: str
    years: float = Field(description="Actual span from birth (the first is the balance).")
    is_current: bool = False
    antardashas: list[Antardasha] = Field(description="Nine sub-periods, clipped to this mahadasha.")


class CurrentDasha(BaseModel):
    """The Vimshottari period active on the target date."""

    target_date: str
    mahadasha_lord: str
    mahadasha_lord_zh: str
    antardasha_lord: str | None = None
    antardasha_lord_zh: str | None = None


class Vimshottari(BaseModel):
    """The full 120-year Vimshottari dasha timeline from the natal Moon."""

    total_years: int = Field(default=120)
    balance_at_birth_years: float = Field(description="Remaining years of the birth mahadasha at birth.")
    moon_elapsed_fraction: float = Field(description="Fraction of the birth nakshatra already passed at birth.")
    birth_nakshatra: str
    birth_nakshatra_zh: str
    birth_lord: str = Field(description="Graha ruling the birth nakshatra; the first mahadasha lord.")
    birth_lord_zh: str
    mahadashas: list[Mahadasha]
    current: CurrentDasha | None = None


class VedicProvenance(BaseModel):
    engine: str
    ayanamsa_name: str
    content_version: str
    source: str
    note: str


class VedicChart(BaseModel):
    """Complete Vedic (sidereal) natal chart with the Vimshottari timeline."""

    local_datetime: str
    utc_datetime: str
    julian_day: float
    latitude: float
    longitude: float
    utc_offset_hours: float
    utc_offset_source: UtcOffsetSource
    zodiac: str = Field(default="sidereal")

    ayanamsa: float = Field(description="Lahiri ayanamsa in degrees applied to tropical longitudes.")
    ayanamsa_name: str

    lagna_sign: str
    lagna_sign_zh: str
    lagna_sign_glyph: str
    lagna_index: int = Field(ge=0, le=11)
    lagna_degree_text: str
    lagna_nakshatra: str
    lagna_nakshatra_zh: str

    moon_sign: str
    moon_sign_zh: str
    moon_nakshatra: str
    moon_nakshatra_zh: str
    moon_nakshatra_lord: str
    moon_nakshatra_lord_zh: str
    moon_pada: int

    planets: list[VedicPlanet] = Field(description="Nine grahas (Navagraha), sidereal.")
    rashis: list[RashiCell] = Field(description="Twelve signs in zodiac order, with occupants and house.")
    vimshottari: Vimshottari

    provenance: VedicProvenance
    engine: str = Field(default="pyswisseph")
