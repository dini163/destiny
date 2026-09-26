"""行运推运 (Transit & Progression) engine — three predictive layers over a natal chart.

All celestial mechanics come from Swiss Ephemeris via the shared natal engine; this
module never computes positions itself (PRD 10.2). It layers three standard,
deterministic techniques on the natal chart:

* **Transits (行运)** — the planets' real longitudes on the target date (evaluated at
  noon UT, the usual daily convention) and the aspects they cast onto the natal.
* **Secondary progressions (次限)** — the "day-for-a-year" chart: the natal moment
  advanced by the querent's age in days, giving progressed planets, angles and their
  aspects to the natal.
* **Solar arc (太阳弧)** — every natal planet advanced by the arc the progressed Sun
  has travelled from the natal Sun (≈1°/year), and those directed points' aspects.

The tropical tables, degree/house helpers and aspect orbs are *imported* from
:mod:`app.engines.western` rather than duplicated, so the two engines can never
drift; ``western`` owns them as the golden-tested base chart. Aspects are geometric
detections labelled with the standard harmony taxonomy — no personalised fortune is
invented at runtime.
"""

from datetime import date, time

import swisseph as swe

from app.core.errors import EphemerisError, UnsupportedMethodError
from app.engines.western import (  # shared, golden-tested astrology primitives
    ASPECTS,
    PLANETS,
    SIGNS,
    SIGNS_ZH,
    SIGN_GLYPHS,
    _calculation_flags,
    _degree_in_sign,
    _format_degree,
    _house_of,
    _normalize_longitude,
    _sign_index,
    compute_western_chart,
)
from app.schemas.transit import (
    AnglePoint,
    CrossAspect,
    MovingPoint,
    ProgressionBlock,
    SolarArcBlock,
    TransitChart,
    TransitProvenance,
)
from app.schemas.western import WesternChart

NOTE = (
    "行运（Transits）取目标日正午世界时（12:00 UT）的真实行星黄经，看其对本命所成之相位；"
    "次限（Secondary Progressions）依「一日当一年」，把本命时刻按周岁天数推进得推运盘，含推运行星与推运上升/中天；"
    "太阳弧（Solar Arc）以次限太阳相对本命太阳行过的弧度（约每年 1°）推进本命诸星，再看其与本命的相位。"
    "行星黄经、四轴与宫头皆由瑞士星历实时计算，相位按经典容许度（合 8°/六合 6°/刑 7°/拱 8°/冲 8°）检测，"
    "并仅以合相=融合、六合与拱=和谐、刑与冲=挑战的标准属性归类，未作任何主观吉凶或个人运势的虚构演绎。"
    "移动层的落宫指该行运/推运/太阳弧之星落入本命十二宫的哪一宫。"
)

#: Aspect type → (nature key, Chinese label). Standard harmony taxonomy.
_NATURE = {
    "conjunction": ("fusion", "融合"),
    "sextile": ("harmonious", "和谐"),
    "trine": ("harmonious", "和谐"),
    "square": ("challenging", "挑战"),
    "opposition": ("challenging", "挑战"),
}

_AXIS_ZH = {"ASC": "上升", "MC": "天顶"}

#: Mean tropical year in days, for the day-for-a-year progression.
_TROPICAL_YEAR_DAYS = 365.24219


def _format_absolute(degrees: float) -> str:
    """Format an absolute angle as degrees/minutes, e.g. 30°12' (not within-sign)."""
    whole = int(degrees)
    minutes = int(round((degrees - whole) * 60))
    if minutes == 60:
        whole += 1
        minutes = 0
    return f"{whole}°{minutes:02d}'"


def _moving(
    name: str, glyph: str, name_zh: str, longitude: float,
    natal_cusps: list[float], retrograde: bool, speed: float,
) -> MovingPoint:
    index = _sign_index(longitude)
    return MovingPoint(
        name=name, glyph=glyph, name_zh=name_zh,
        longitude=round(longitude, 4),
        sign=SIGNS[index], sign_zh=SIGNS_ZH[index], sign_glyph=SIGN_GLYPHS[index], sign_index=index,
        degree_in_sign=_degree_in_sign(longitude), degree_text=_format_degree(longitude),
        natal_house=_house_of(longitude, natal_cusps),
        retrograde=retrograde, speed=speed,
    )


def _moving_from_pos(name: str, glyph: str, name_zh: str, pos: list[float], natal_cusps: list[float]) -> MovingPoint:
    """Build a MovingPoint from a ``swe.calc_ut`` result row ``[lon, lat, dist, speed]``."""
    return _moving(name, glyph, name_zh, _normalize_longitude(pos[0]), natal_cusps, pos[3] < 0, round(pos[3], 6))


def _angle(name: str, label: str, longitude_raw: float) -> AnglePoint:
    longitude = _normalize_longitude(longitude_raw)
    index = _sign_index(longitude)
    return AnglePoint(
        name=name, label=label, longitude=round(longitude, 4),
        sign=SIGNS[index], sign_zh=SIGNS_ZH[index], sign_index=index,
        degree_in_sign=_degree_in_sign(longitude), degree_text=_format_degree(longitude),
    )


def _natal_points(natal: WesternChart) -> list[tuple[str, str, float]]:
    """The natal targets a moving body can aspect: ten planets plus ASC and MC."""
    points = [(p.name, p.name_zh, p.longitude) for p in natal.planets]
    for axis in natal.axes:
        if axis.name in _AXIS_ZH:
            points.append((axis.name, _AXIS_ZH[axis.name], axis.longitude))
    return points


def _cross_aspects(
    moving: list[MovingPoint], natal_points: list[tuple[str, str, float]],
) -> list[CrossAspect]:
    """Aspects from each moving body to each natal point, keeping the tightest per pair."""
    aspects: list[CrossAspect] = []
    for body in moving:
        for name, name_zh, longitude in natal_points:
            delta = abs(body.longitude - longitude) % 360.0
            if delta > 180.0:
                delta = 360.0 - delta
            best: CrossAspect | None = None
            for aspect_name, glyph, angle, orb_limit in ASPECTS:
                orb = abs(delta - angle)
                if orb <= orb_limit and (best is None or orb < best.orb):
                    nature, nature_zh = _NATURE[aspect_name]
                    best = CrossAspect(
                        moving=body.name, moving_zh=body.name_zh, moving_glyph=body.glyph,
                        natal=name, natal_zh=name_zh,
                        type=aspect_name, glyph=glyph, angle=angle, orb=round(orb, 2),
                        nature=nature, nature_zh=nature_zh,
                    )
            if best is not None:
                aspects.append(best)
    aspects.sort(key=lambda aspect: aspect.orb)
    return aspects


def compute_transits(
    *,
    birth_date: date,
    birth_time: time,
    latitude: float,
    longitude: float,
    utc_offset_hours: float | None = None,
    house_system: str = "P",
    target_date: date,
    ephemeris_path: str | None = None,
) -> TransitChart:
    """Project transits, secondary progressions and solar arc onto a natal chart.

    Pure apart from the in-process ephemeris. Raises :class:`UnsupportedMethodError`
    when ``target_date`` precedes ``birth_date`` (progressions run forward from birth).
    """
    if target_date < birth_date:
        raise UnsupportedMethodError(
            "目标日期不得早于出生日期：次限与太阳弧推运皆以出生为起点向后推进。"
        )

    natal = compute_western_chart(
        birth_date=birth_date, birth_time=birth_time, latitude=latitude, longitude=longitude,
        utc_offset_hours=utc_offset_hours, house_system=house_system, ephemeris_path=ephemeris_path,
    )
    natal_cusps = [cusp.longitude for cusp in natal.houses]
    natal_points = _natal_points(natal)
    flags = _calculation_flags(ephemeris_path)

    age_years = (target_date - birth_date).days / _TROPICAL_YEAR_DAYS

    try:
        target_jd = swe.julday(target_date.year, target_date.month, target_date.day, 12.0)
        transit_positions = [
            _moving_from_pos(name, glyph, name_zh, swe.calc_ut(target_jd, body, flags)[0], natal_cusps)
            for name, glyph, name_zh, body in PLANETS
        ]

        progressed_jd = natal.julian_day + age_years
        prog_positions = [
            _moving_from_pos(name, glyph, name_zh, swe.calc_ut(progressed_jd, body, flags)[0], natal_cusps)
            for name, glyph, name_zh, body in PLANETS
        ]
        _prog_cusps, prog_ascmc = swe.houses(progressed_jd, latitude, longitude, house_system.encode())
    except swe.Error as exc:  # pragma: no cover - defensive ephemeris failure
        raise EphemerisError(f"Swiss Ephemeris computation failed: {exc}") from exc

    transit_aspects = _cross_aspects(transit_positions, natal_points)

    prog_angles = [_angle("ASC", "Ascendant", prog_ascmc[0]), _angle("MC", "Midheaven", prog_ascmc[1])]
    prog_aspects = _cross_aspects(prog_positions, natal_points)
    prog_moon = next(p for p in prog_positions if p.name == "Moon")
    prog_sun = next(p for p in prog_positions if p.name == "Sun")
    prog_year, prog_month, prog_day, _prog_hour = swe.revjul(progressed_jd)

    progression = ProgressionBlock(
        progressed_date=f"{prog_year:04d}-{prog_month:02d}-{prog_day:02d}",
        progressed_julian_day=round(progressed_jd, 5),
        age_years=round(age_years, 4),
        positions=prog_positions,
        angles=prog_angles,
        aspects=prog_aspects,
        moon_sign_zh=prog_moon.sign_zh,
        moon_natal_house=prog_moon.natal_house,
    )

    natal_sun_lon = next(p.longitude for p in natal.planets if p.name == "Sun")
    arc = _normalize_longitude(prog_sun.longitude - natal_sun_lon)
    directed_positions = [
        _moving(p.name, p.glyph, p.name_zh, _normalize_longitude(p.longitude + arc), natal_cusps, p.retrograde, 0.0)
        for p in natal.planets
    ]
    solar_arc = SolarArcBlock(
        arc_degrees=round(arc, 4),
        arc_text=_format_absolute(arc),
        positions=directed_positions,
        aspects=_cross_aspects(directed_positions, natal_points),
    )

    return TransitChart(
        natal=natal,
        target_date=target_date.strftime("%Y-%m-%d"),
        target_julian_day=round(target_jd, 5),
        transit_positions=transit_positions,
        transit_aspects=transit_aspects,
        progression=progression,
        solar_arc=solar_arc,
        provenance=TransitProvenance(engine="pyswisseph", note=NOTE),
    )
