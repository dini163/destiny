"""Pydantic schemas for the Western (tropical) natal-astrology system."""

from datetime import date, time

from pydantic import BaseModel, Field


class WesternNatalRequest(BaseModel):
    """Input for a Western natal chart.

    ``latitude``/``longitude`` may be supplied directly or resolved from a city
    name. ``utc_offset_hours`` is the offset of the *local* birth time from UTC;
    when omitted it is approximated from the longitude (a theoretical time zone)
    and the response flags this so clients can supply an exact offset for
    precise ascendant timing.
    """

    birth_date: date = Field(description="Gregorian birth date.")
    birth_time: time = Field(description="Local clock birth time.")
    city: str | None = Field(default=None, description="City name for geocoding.")
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    utc_offset_hours: float | None = Field(
        default=None, ge=-14, le=14, description="Local-time offset from UTC in hours."
    )
    house_system: str = Field(default="P", description="House system code (P=Placidus, K=Koch, R=Regiomontanus, W=Whole).")


class PlanetPlacement(BaseModel):
    """A planet's tropical position, sign and house."""

    name: str
    glyph: str
    name_zh: str
    longitude: float = Field(description="Tropical ecliptic longitude, 0-360 degrees")
    sign: str
    sign_zh: str
    sign_glyph: str
    sign_index: int = Field(ge=0, le=11)
    degree_in_sign: float
    degree_text: str = Field(description="Degrees/minutes within the sign, e.g. 10°22'")
    house: int = Field(ge=1, le=12)
    retrograde: bool
    speed: float = Field(description="Longitudinal speed in degrees/day (negative = retrograde)")


class HouseCusp(BaseModel):
    """A house cusp position."""

    house: int
    longitude: float
    sign: str
    sign_zh: str
    degree_in_sign: float
    degree_text: str


class AxisPoint(BaseModel):
    """One of the four chart angles (ASC / DES / MC / IC)."""

    name: str = Field(description="ASC | DES | MC | IC")
    label: str = Field(description="Human-readable name, e.g. Ascendant")
    longitude: float
    sign: str
    sign_zh: str
    sign_index: int
    degree_in_sign: float
    degree_text: str
    house: int = Field(description="House the axis rules: ASC=1, IC=4, DES=7, MC=10")


class Aspect(BaseModel):
    """A major aspect between two planets."""

    planet1: str
    planet2: str
    type: str = Field(description="conjunction | sextile | square | trine | opposition")
    glyph: str
    angle: float = Field(description="Exact aspect angle in degrees")
    orb: float = Field(description="Absolute deviation from the exact angle")


class NodeInfo(BaseModel):
    """Lunar node positions (North / South)."""

    north_node_longitude: float
    north_node_sign: str
    north_node_sign_zh: str
    north_node_house: int
    south_node_longitude: float
    south_node_sign: str
    south_node_sign_zh: str
    south_node_house: int


class WesternChart(BaseModel):
    """Complete Western natal chart produced by :mod:`app.engines.western`."""

    # Provenance
    local_datetime: str
    utc_datetime: str
    julian_day: float
    latitude: float
    longitude: float
    utc_offset_hours: float
    utc_offset_source: str = Field(description="explicit | longitude_approximation")
    house_system: str
    zodiac: str = Field(default="tropical")

    # Headline placements
    sun_sign: str
    sun_sign_zh: str
    moon_sign: str
    moon_sign_zh: str
    ascendant_sign: str
    ascendant_sign_zh: str

    # Chart data
    planets: list[PlanetPlacement] = Field(description="Ten major bodies: Sun..Pluto")
    axes: list[AxisPoint] = Field(description="ASC, DES, MC, IC")
    houses: list[HouseCusp] = Field(description="Twelve house cusps")
    aspects: list[Aspect] = Field(description="Major aspects among the planets")
    nodes: NodeInfo
    element_balance: dict[str, int] = Field(description="fire/earth/air/water counts among planets")
    modality_balance: dict[str, int] = Field(description="cardinal/fixed/mutable counts among planets")

    engine: str = Field(default="pyswisseph")
