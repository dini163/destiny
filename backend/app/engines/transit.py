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

from app.content import CONTENT_VERSION, TRANSIT_OVERLAY_CONTENT_SOURCES
from app.content.aspects_nature import ASPECT_NATURE
from app.content.transit_plain import (
    TRANSIT_NONE_BRANCHES,
    TRANSIT_SECTION_TITLES,
    aspect_key,
    progressed_axis_key,
    progressed_moon_house_key,
    progressed_moon_sign_key,
)
from app.core.errors import EphemerisError, UnsupportedMethodError
from app.engines.plain_compose import compose
from app.engines.plain_corpora import TRANSIT
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
from app.schemas.common import PlainSection, ProvenanceTable
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
    "并仅以合相=融合、六合与拱=和谐、刑与冲=挑战的标准属性归类。"
    "页面下方的白话逐条转述以上已经算出的相位与推运标志位，句子全部预先写在平台自撰的语料表里，"
    "不署任何书名，不构成医疗、法律或财务建议，也不预测具体事件。"
    "移动层的落宫指该行运/推运/太阳弧之星落入本命十二宫的哪一宫。"
)

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
                    nature, nature_zh = ASPECT_NATURE[aspect_name]
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


def build_plain(
    *,
    transit_aspects: list[CrossAspect],
    progression_aspects: list[CrossAspect],
    arc_aspects: list[CrossAspect],
    moon_sign: str,
    moon_house: int,
    prog_angles: list[AnglePoint],
) -> list[PlainSection]:
    """按三层盘面已经算出的相位与次限标志位逐条选句，拼成页尾「白话详解」的五段。

    只选句，不现编（`plain_compose.compose` 的立身规矩，也是 `TRANSIT_PLAIN_NOTE` 那句
    「请求时不生成任何中文」的唯一兑现点）。段的次序是产品决定，由
    `tests/golden/test_transit_golden.py::test_the_plain_block_is_five_sections_in_the_declared_order`
    钉成字面量。

    六个入参全是关键字：`plain` 是 `TransitChart` 的字段，装配时那个对象还没造出来
    （spec §8 的原签名 `build_plain(chart)` 在这一点上不成立，Plan F 偏差 10 的同一裁定）。
    """

    def emit(section: str, keys: list[str]) -> PlainSection:
        # `keep` 分组不看符号（`plain_compose.py:70-71`），符号位一律传 0；传 0 而不是省略
        # 是为了保住 `compose` 的签名形状，与其余九个系统的调用一致（F 的同一段注释）。
        if not keys and section not in TRANSIT_NONE_BRANCHES:
            # 崩而不静默：一张恒非空的段收不到键是编程错误，不是用户输入。理由与钉名见
            # `engines/western.py:211-217` 的同一段注释（F 的 `999db61` 那颗钉的同类）。
            raise ValueError(
                f"transit 段 {section!r} 收不到任何键，"
                f"且它不在 TRANSIT_NONE_BRANCHES 里：{TRANSIT_NONE_BRANCHES}"
            )
        opener = TRANSIT_NONE_BRANCHES[section] if not keys else section
        return PlainSection(
            title=TRANSIT_SECTION_TITLES[section],
            text=compose(TRANSIT, opener, [(key, 0) for key in keys]),
        )

    return [
        emit("transit_aspect", [aspect_key(a.moving, a.natal, a.type) for a in transit_aspects]),
        emit("progressed_aspect", [aspect_key(a.moving, a.natal, a.type) for a in progression_aspects]),
        emit("directed_aspect", [aspect_key(a.moving, a.natal, a.type) for a in arc_aspects]),
        emit("progressed_moon", [progressed_moon_sign_key(moon_sign), progressed_moon_house_key(moon_house)]),
        # 页面印这两根轴，白话按 `AnglePoint.name`（`ASC`/`MC`）各取一句；次序即 `prog_angles` 的序。
        emit("progressed_axis", [progressed_axis_key(angle.name, angle.sign) for angle in prog_angles]),
    ]


def _transit_tables() -> list[ProvenanceTable]:
    """`TRANSIT_OVERLAY_CONTENT_SOURCES` 的第一次被消费（AGENTS §7「读了就列」）。

    复测（行号随本注一起漂，改动常量后重跑这条即得）：
    `cd backend && grep -rn "TRANSIT_OVERLAY_CONTENT_SOURCES" app/ tests/ --include=*.py` → 定义在
    `content/__init__.py:59`、本模块 import 一处（`:26`）、消费一处（本函数 `:219`），
    测侧只有 `tests/content/test_transit_plain_corpus.py` 两颗钉与
    `tests/test_transit_api.py` 的 `tables` 三行断言。
    **golden 里刻意零命中**：它钉的是字面量清单（三个模块名逐字 + `len(tables) == 3`），
    不 import 这个常量——否则登记表加行时测与被测同动，钉的只是「引擎如实复现登记」。
    登记表自身那一半由上面那颗逐字钉负责。
    引擎不在此另列表名、不抄书名（照 `engines/western.py:244-259` 的写法）。
    """
    return [
        ProvenanceTable(name=module, version=CONTENT_VERSION, source=source)
        for module, source in TRANSIT_OVERLAY_CONTENT_SOURCES
    ]


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
    arc_aspects = _cross_aspects(directed_positions, natal_points)
    solar_arc = SolarArcBlock(
        arc_degrees=round(arc, 4),
        arc_text=_format_absolute(arc),
        positions=directed_positions,
        aspects=arc_aspects,
    )

    plain = build_plain(
        transit_aspects=transit_aspects,
        progression_aspects=prog_aspects,
        arc_aspects=arc_aspects,
        moon_sign=prog_moon.sign,
        moon_house=prog_moon.natal_house,
        prog_angles=prog_angles,
    )

    return TransitChart(
        natal=natal,
        target_date=target_date.strftime("%Y-%m-%d"),
        target_julian_day=round(target_jd, 5),
        transit_positions=transit_positions,
        transit_aspects=transit_aspects,
        progression=progression,
        solar_arc=solar_arc,
        plain=plain,
        provenance=TransitProvenance(engine="pyswisseph", note=NOTE, tables=_transit_tables()),
    )
