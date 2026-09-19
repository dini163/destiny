"""Western (tropical) natal-astrology engine built on pyswisseph.

All planetary longitudes, house cusps and chart angles come from Swiss
Ephemeris; this module never computes celestial mechanics itself (PRD 10.2).
On top of the raw positions it performs standard, deterministic astrology
post-processing: sign and house assignment, aspect detection with classical
orbs, and element / modality balance.

By default it uses the analytical Moshier ephemeris (``SEFLG_MOSEPH``), which
requires no data files and yields real positions accurate to well under an
arcsecond for the classical planets. When an ephemeris path is configured the
engine switches to the compressed Swiss Ephemeris files (``SEFLG_SWIEPH``, e.g.
DE431) for full precision.
"""

from datetime import date, datetime, time, timedelta

import swisseph as swe

from app.core.errors import EphemerisError, UnsupportedMethodError
from app.schemas.western import (
    Aspect,
    AxisPoint,
    HouseCusp,
    NodeInfo,
    PlanetPlacement,
    WesternChart,
)

# --- Fixed reference tables (standard Western astrology) ---------------------

SIGNS = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)
SIGNS_ZH = (
    "白羊", "金牛", "双子", "巨蟹", "狮子", "处女",
    "天秤", "天蝎", "射手", "摩羯", "水瓶", "双鱼",
)
SIGN_GLYPHS = ("♈", "♉", "♊", "♋", "♌", "♍", "♎", "♏", "♐", "♑", "♒", "♓")
# Element and modality repeat every four / three signs respectively.
SIGN_ELEMENT = ("fire", "earth", "air", "water") * 3
SIGN_MODALITY = ("cardinal", "fixed", "mutable") * 4

# (name, glyph, Chinese name, Swiss Ephemeris body constant).
PLANETS = (
    ("Sun", "☉", "太阳", swe.SUN),
    ("Moon", "☽", "月亮", swe.MOON),
    ("Mercury", "☿", "水星", swe.MERCURY),
    ("Venus", "♀", "金星", swe.VENUS),
    ("Mars", "♂", "火星", swe.MARS),
    ("Jupiter", "♃", "木星", swe.JUPITER),
    ("Saturn", "♄", "土星", swe.SATURN),
    ("Uranus", "♅", "天王星", swe.URANUS),
    ("Neptune", "♆", "海王星", swe.NEPTUNE),
    ("Pluto", "♇", "冥王星", swe.PLUTO),
)

# (name, glyph, exact angle, maximum orb) — classical major-aspect orbs.
ASPECTS = (
    ("conjunction", "☌", 0.0, 8.0),
    ("sextile", "⚹", 60.0, 6.0),
    ("square", "□", 90.0, 7.0),
    ("trine", "△", 120.0, 8.0),
    ("opposition", "☍", 180.0, 8.0),
)

ALLOWED_HOUSE_SYSTEMS = frozenset({"P", "K", "R", "C", "E", "W", "M", "G"})


def _normalize_longitude(value: float) -> float:
    """Wrap an ecliptic longitude into [0, 360)."""
    return value % 360.0


def _sign_index(longitude: float) -> int:
    return int(_normalize_longitude(longitude) // 30)


def _degree_in_sign(longitude: float) -> float:
    return round(_normalize_longitude(longitude) % 30, 4)


def _format_degree(longitude: float) -> str:
    """Format the within-sign position as degrees and minutes, e.g. 10°22'."""
    within = _normalize_longitude(longitude) % 30
    degrees = int(within)
    minutes = int(round((within - degrees) * 60))
    if minutes == 60:  # rounding pushed into the next degree
        degrees += 1
        minutes = 0
    return f"{degrees}°{minutes:02d}'"


def _house_of(longitude: float, cusps: list[float]) -> int:
    """Return the 1-based house containing a longitude, given ascending cusps."""
    lon = _normalize_longitude(longitude)
    for index in range(12):
        start = cusps[index]
        end = cusps[(index + 1) % 12]
        if start <= end:
            if start <= lon < end:
                return index + 1
        elif lon >= start or lon < end:  # cusp interval wraps through 0 degrees
            return index + 1
    return 12


def _calculation_flags(ephemeris_path: str | None) -> int:
    if ephemeris_path:
        swe.set_ephe_path(ephemeris_path)
        return swe.FLG_SPEED | swe.FLG_SWIEPH
    return swe.FLG_SPEED | swe.FLG_MOSEPH


def _make_axis(name: str, label: str, longitude: float, house: int) -> AxisPoint:
    index = _sign_index(longitude)
    return AxisPoint(
        name=name,
        label=label,
        longitude=round(longitude, 4),
        sign=SIGNS[index],
        sign_zh=SIGNS_ZH[index],
        sign_index=index,
        degree_in_sign=_degree_in_sign(longitude),
        degree_text=_format_degree(longitude),
        house=house,
    )


def _compute_aspects(planets: list[PlanetPlacement]) -> list[Aspect]:
    """Detect major aspects among all planet pairs, keeping the tightest orb."""
    aspects: list[Aspect] = []
    count = len(planets)
    for i in range(count):
        for j in range(i + 1, count):
            delta = abs(planets[i].longitude - planets[j].longitude) % 360.0
            if delta > 180.0:
                delta = 360.0 - delta
            best: Aspect | None = None
            for name, glyph, angle, orb_limit in ASPECTS:
                orb = abs(delta - angle)
                if orb <= orb_limit and (best is None or orb < best.orb):
                    best = Aspect(
                        planet1=planets[i].name,
                        planet2=planets[j].name,
                        type=name,
                        glyph=glyph,
                        angle=angle,
                        orb=round(orb, 2),
                    )
            if best is not None:
                aspects.append(best)
    aspects.sort(key=lambda aspect: aspect.orb)
    return aspects


def compute_western_chart(
    *,
    birth_date: date,
    birth_time: time,
    latitude: float,
    longitude: float,
    utc_offset_hours: float | None = None,
    house_system: str = "P",
    ephemeris_path: str | None = None,
) -> WesternChart:
    """Compute a Western natal chart from birth data and location.

    Pure function: no HTTP, no I/O beyond the in-process ephemeris. The local
    birth time is converted to Universal Time using ``utc_offset_hours`` (or a
    longitude-derived theoretical zone when omitted) before evaluating positions.
    """
    if house_system not in ALLOWED_HOUSE_SYSTEMS:
        raise UnsupportedMethodError(
            f"Unsupported house system '{house_system}'. Allowed: {', '.join(sorted(ALLOWED_HOUSE_SYSTEMS))}."
        )

    if utc_offset_hours is None:
        offset = float(round(longitude / 15.0))
        offset_source = "longitude_approximation"
    else:
        offset = float(utc_offset_hours)
        offset_source = "explicit"

    local_dt = datetime.combine(birth_date, birth_time)
    ut_dt = local_dt - timedelta(hours=offset)
    hour_decimal = ut_dt.hour + ut_dt.minute / 60.0 + ut_dt.second / 3600.0

    try:
        julian_day = swe.julday(ut_dt.year, ut_dt.month, ut_dt.day, hour_decimal)
        flags = _calculation_flags(ephemeris_path)
        raw_cusps, ascmc = swe.houses(julian_day, latitude, longitude, house_system.encode())
        positions = {name: swe.calc_ut(julian_day, body, flags)[0] for name, _g, _zh, body in PLANETS}
        north_position = swe.calc_ut(julian_day, swe.MEAN_NODE, flags)[0]
    except swe.Error as exc:  # pragma: no cover - defensive ephemeris failure
        raise EphemerisError(f"Swiss Ephemeris computation failed: {exc}") from exc

    cusps = [_normalize_longitude(cusp) for cusp in raw_cusps]
    ascendant = _normalize_longitude(ascmc[0])
    midheaven = _normalize_longitude(ascmc[1])
    descendant = _normalize_longitude(ascendant + 180.0)
    nadir = _normalize_longitude(midheaven + 180.0)

    planets = [
        PlanetPlacement(
            name=name,
            glyph=glyph,
            name_zh=name_zh,
            longitude=round(_normalize_longitude(positions[name][0]), 4),
            sign=SIGNS[_sign_index(positions[name][0])],
            sign_zh=SIGNS_ZH[_sign_index(positions[name][0])],
            sign_glyph=SIGN_GLYPHS[_sign_index(positions[name][0])],
            sign_index=_sign_index(positions[name][0]),
            degree_in_sign=_degree_in_sign(positions[name][0]),
            degree_text=_format_degree(positions[name][0]),
            house=_house_of(positions[name][0], cusps),
            retrograde=positions[name][3] < 0,
            speed=round(positions[name][3], 6),
        )
        for name, glyph, name_zh, _body in PLANETS
    ]

    axes = [
        _make_axis("ASC", "Ascendant", ascendant, 1),
        _make_axis("DES", "Descendant", descendant, 7),
        _make_axis("MC", "Midheaven", midheaven, 10),
        _make_axis("IC", "Nadir", nadir, 4),
    ]

    houses = [
        HouseCusp(
            house=index + 1,
            longitude=round(cusps[index], 4),
            sign=SIGNS[_sign_index(cusps[index])],
            sign_zh=SIGNS_ZH[_sign_index(cusps[index])],
            degree_in_sign=_degree_in_sign(cusps[index]),
            degree_text=_format_degree(cusps[index]),
        )
        for index in range(12)
    ]

    north_longitude = _normalize_longitude(north_position[0])
    south_longitude = _normalize_longitude(north_longitude + 180.0)
    nodes = NodeInfo(
        north_node_longitude=round(north_longitude, 4),
        north_node_sign=SIGNS[_sign_index(north_longitude)],
        north_node_sign_zh=SIGNS_ZH[_sign_index(north_longitude)],
        north_node_house=_house_of(north_longitude, cusps),
        south_node_longitude=round(south_longitude, 4),
        south_node_sign=SIGNS[_sign_index(south_longitude)],
        south_node_sign_zh=SIGNS_ZH[_sign_index(south_longitude)],
        south_node_house=_house_of(south_longitude, cusps),
    )

    element_balance = {"fire": 0, "earth": 0, "air": 0, "water": 0}
    modality_balance = {"cardinal": 0, "fixed": 0, "mutable": 0}
    for planet in planets:
        element_balance[SIGN_ELEMENT[planet.sign_index]] += 1
        modality_balance[SIGN_MODALITY[planet.sign_index]] += 1

    sun = next(planet for planet in planets if planet.name == "Sun")
    moon = next(planet for planet in planets if planet.name == "Moon")

    return WesternChart(
        local_datetime=local_dt.strftime("%Y-%m-%d %H:%M"),
        utc_datetime=ut_dt.strftime("%Y-%m-%d %H:%M"),
        julian_day=round(julian_day, 5),
        latitude=latitude,
        longitude=longitude,
        utc_offset_hours=offset,
        utc_offset_source=offset_source,
        house_system=house_system,
        sun_sign=sun.sign,
        sun_sign_zh=sun.sign_zh,
        moon_sign=moon.sign,
        moon_sign_zh=moon.sign_zh,
        ascendant_sign=SIGNS[_sign_index(ascendant)],
        ascendant_sign_zh=SIGNS_ZH[_sign_index(ascendant)],
        planets=planets,
        axes=axes,
        houses=houses,
        aspects=_compute_aspects(planets),
        nodes=nodes,
        element_balance=element_balance,
        modality_balance=modality_balance,
    )
