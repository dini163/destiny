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

from app.content import CONTENT_VERSION, WESTERN_CONTENT_SOURCES
from app.content.western_plain import (
    WESTERN_NONE_BRANCHES,
    WESTERN_PLAIN_NOTE,
    WESTERN_SECTION_TITLES,
    aspect_key,
    axis_sign_key,
    element_key,
    house_theme_key,
    modality_key,
    node_house_key,
    node_sign_key,
    planet_house_key,
    planet_sign_key,
    retrograde_key,
)
from app.core.errors import EphemerisError, UnsupportedMethodError
from app.engines.plain_compose import compose
from app.schemas.common import PlainSection, ProvenanceTable
from app.schemas.western import (
    Aspect,
    AxisPoint,
    HouseCusp,
    NodeInfo,
    PlanetPlacement,
    WesternChart,
    WesternProvenance,
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


def build_plain(
    *,
    planets: list[PlanetPlacement],
    axes: list[AxisPoint],
    aspects: list[Aspect],
    nodes: NodeInfo,
    element_balance: dict[str, int],
    modality_balance: dict[str, int],
) -> list[PlainSection]:
    """按盘面已经算出的位置逐条选句，拼成页尾「白话详解」的八段。

    **只选句，不现编**：每个键都是盘面上一个已印事实的中文名（`plain_compose.compose` 的立身
    规矩，戊组 spec §1.1 R50 的支点）。八段的发射序是产品决定，由
    `tests/golden/test_western_golden.py::test_the_plain_block_is_eight_sections_in_the_declared_order`
    钉成字面量；每段行数 == 该段实发键数 + 1 由同文件那条行数测钉。

    入参是六个关键字而不是一个 `chart`：`plain` 是 `WesternChart` 的字段，装配时那个对象还
    没造出来（spec §8 的原签名 `build_plain(chart)` 在这一点上不成立，见偏差表第 10 行）。

    `plain_corpora` 的 import 在**函数内**，这是 `app/engines/` 里唯一一处函数级 import：
    `engines/plain_corpora.py:46` 顶层 `from app.engines.western import ...`，
    本模块若在顶层回引它就是 `ImportError: cannot import name ...（circular import）`。
    两条边不能同时是顶层，而登记表引引擎是既有的、九个系统共用的形状，所以断的是这一侧。
    复测（本函数落地后全目录恰好一行命中，就是下面这行）：
    `cd backend && grep -rn "^    from app" app/engines/ --include=*.py`。
    同形状的第二处在 `tests/golden/test_western_golden.py` 的 `test_an_empty_aspect_list_fires_the_none_opener_and_nothing_else`
    （那里为的是让 T16 Step 1 的 RED 能逐条报出6 failed 而不是收集期就中断），不在本条纪律的射程内。
    """
    from app.engines.plain_corpora import WESTERN  # 循环边在本函数内断，理由见 docstring

    def emit(section: str, keys: list[str]) -> PlainSection:
        # `keep` 分组不看符号（`plain_compose.py:64-71`：`band` 在 64-69、`keep` 在 70-71），符号位一律传 0；
        # 传 0 而不是省略是为了保住 `compose` 的签名形状，与其他九个系统的调用一致。
        if not keys and section not in WESTERN_NONE_BRANCHES:
            # 崩而不静默：一张恒非空的段收不到键，是编程错误（该段的名字漏了、过滤写错了、
            # 或者调用方传错了入参），不是用户输入。若放过去，装配器会拿 section 自己的开篇句
            # 拼出一段只有开篇句的「白话」，页面上读起来像「这一段今天没什么可说」——那正是
            # `plain_compose` 开篇那句「宁崩不漏」的同一条纪律，本条把它落到八段装配的每一段上。
            # 钉：`tests/golden/test_western_golden.py::test_a_section_that_goes_empty_without_a_declared_none_branch_crashes`
            # （复测：删掉本条这七行，同文件 `pytest` 出一条 FAILED；条数随该文件增删变，
            # 数字不复述——重跑这条命令即得现值）。
            raise ValueError(f"west 段 {section!r} 收不到任何键，且它不在 WESTERN_NONE_BRANCHES 里：{WESTERN_NONE_BRANCHES}")
        opener = WESTERN_NONE_BRANCHES[section] if not keys else section
        return PlainSection(
            title=WESTERN_SECTION_TITLES[section],
            text=compose(WESTERN, opener, [(key, 0) for key in keys]),
        )

    return [
        emit("planet_sign", [planet_sign_key(p.name, p.sign) for p in planets]),
        emit("planet_house", [planet_house_key(p.name, p.house) for p in planets]),
        emit("aspect", [aspect_key(a.planet1, a.planet2, a.type) for a in aspects]),
        emit("retrograde", [retrograde_key(p.name) for p in planets if p.retrograde]),
        # 页面印四轴，白话只讲 ASC/MC：`axes` 里过滤这两个是 spec §2 排除表的实现面（偏差 17）。
        emit("axis", [axis_sign_key(a.name, a.sign) for a in axes if a.name in ("ASC", "MC")]),
        # 只取北交点：南交点在页面上有格子（`NodeInfo` 带 south_*），但 spec §2 不建它的键族，
        # 而 G33 把「南交」列进禁字，所以这一段恒两句。
        emit("nodes", [node_sign_key(nodes.north_node_sign), node_house_key(nodes.north_node_house)]),
        emit("house_theme", [house_theme_key(house) for house in range(1, 13)]),
        emit(
            "balance",
            [element_key(name) for name, count in element_balance.items() if count > 0]
            + [modality_key(name) for name, count in modality_balance.items() if count > 0],
        ),
    ]


def _western_tables() -> list[ProvenanceTable]:
    """`WESTERN_CONTENT_SOURCES` 的第一次被消费（AGENTS §7「读了就列」）。

    复测（行号随本注一起漂，改动常量后重跑这条即得）：
    `cd backend && grep -rn "WESTERN_CONTENT_SOURCES" app/ tests/ --include=*.py` → 定义在
    `content/__init__.py:165`、本模块 import 一处（`:20`）、消费一处（本函数 `:257`），
    测侧只有 `tests/content/test_western_plain_corpus.py:411` 一处。
    **golden 里刻意零命中**：它钉的是字面量清单（三个模块名逐字 + `len(tables) == 3`），
    不 import 这个常量——否则登记表加行时测与被测同动，钉的只是「引擎如实复现登记」。
    登记表自身那一半由上面那条逐字钉负责。
    引擎不在此另列表名、不抄书名（照 `engines/ziwei.py:239-252` 的写法）。
    """
    return [
        ProvenanceTable(name=module, version=CONTENT_VERSION, source=source)
        for module, source in WESTERN_CONTENT_SOURCES
    ]


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

    aspects = _compute_aspects(planets)
    plain = build_plain(
        planets=planets,
        axes=axes,
        aspects=aspects,
        nodes=nodes,
        element_balance=element_balance,
        modality_balance=modality_balance,
    )

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
        aspects=aspects,
        nodes=nodes,
        element_balance=element_balance,
        modality_balance=modality_balance,
        plain=plain,
        provenance=WesternProvenance(note=WESTERN_PLAIN_NOTE, tables=_western_tables()),
    )
