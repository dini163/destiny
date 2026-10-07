"""西洋合盘 (Western Synastry & Composite) engine — two natals, their cross-aspects,
the midpoint composite, and a deterministic compatibility score.

All celestial mechanics come from Swiss Ephemeris via the shared natal engine; this
module never computes positions itself (PRD 10.2). It layers two standard, deterministic
relationship techniques on a pair of natal charts:

* **Synastry (合盘)** — the person-to-person aspects: every point of chart A against
  every point of chart B (ten planets plus ASC and MC), keeping the tightest orb per
  pair and labelling it with the standard harmony taxonomy.
* **Composite (组合盘)** — the midpoint chart: each composite planet and house cusp is
  the shorter-arc midpoint of the two natal longitudes. This is pure geometry, so the
  composite needs no ephemeris of its own and is exactly reproducible.

The tropical tables, degree/house helpers, aspect orbs, axis builder and aspect detection
are *imported* from :mod:`app.engines.western` rather than duplicated, so the two engines
can never drift; ``western`` owns them as the golden-tested base chart. The compatibility
score is a self-explaining ledger whose weights are curated in :mod:`app.content.synastry`
— every figure carries its own arithmetic, nothing is mocked.
"""

from collections.abc import Sequence

from app.content import CONTENT_VERSION, SYNASTRY_CONTENT_SOURCES, synastry_plain
from app.content.aspects_nature import ASPECT_NATURE
from app.content.synastry import (
    SYNASTRY_ASPECT_DELTA,
    SYNASTRY_ASPECT_ZH,
    SYNASTRY_BASE,
    SYNASTRY_CORE_BONDS,
    SYNASTRY_CORE_EMPHASIS,
    SYNASTRY_METHOD,
    SYNASTRY_ORB_DECAY,
    SYNASTRY_PERSONAL_POINTS,
    SYNASTRY_SOURCE,
    synastry_tier,
)
from app.engines.plain_compose import compose, compose_template, dedupe, reading
from app.engines.plain_corpora import SYNASTRY
from app.engines.western import (  # shared, golden-tested astrology primitives
    ASPECTS,
    SIGNS,
    SIGNS_ZH,
    SIGN_ELEMENT,
    SIGN_GLYPHS,
    SIGN_MODALITY,
    _compute_aspects,
    _degree_in_sign,
    _format_degree,
    _house_of,
    _make_axis,
    _normalize_longitude,
    _sign_index,
    compute_western_chart,
)
from app.schemas.common import ProvenanceTable
from app.schemas.scoring import ScoreFactor, ScoreValue, build_ledger
from app.schemas.synastry import (
    CompositeChart,
    SynastryAspect,
    SynastryChart,
    SynastryPerson,
    SynastryProvenance,
)
from app.schemas.western import HouseCusp, PlanetPlacement, WesternChart
from app.solar.geo import resolve_coordinates

NOTE = (
    "合盘（Synastry）取两造本命盘的每一个点（十大行星加上升、中天）两两相比，"
    "按经典容许度（合 8°/六合 6°/刑 7°/拱 8°/冲 8°）检测人对人相位，每对只留最紧的一个，"
    "并以合相=融合、六合与拱=和谐、刑与冲=挑战的标准属性归类；"
    "组合盘（Composite）取两造同名行星与十二宫头各自的「短弧中点」，纯几何、可复算，"
    "组合上升取两造上升中点、组合中天取两造中天中点，其余行星按中点黄经落入组合宫。"
    "行星黄经、四轴与宫头皆由瑞士星历实时计算，未作任何主观吉凶或个人运势的虚构演绎；"
    "相契度只由「人对人」的合盘相位按模型参数加权累加，账本逐条可核（口径详见 method）。"
)

#: Only ASC and MC are taken from the axes: DES and IC are their exact opposites and so
#: would duplicate every aspect. The name doubles as the point's glyph (no classic symbol).
_AXIS_ZH = {"ASC": "上升", "MC": "天顶"}

#: Aspect type → its maximum orb, for the score's orb-tightness weight.
_ORB_LIMIT_BY_TYPE = {name: orb_limit for name, _glyph, _angle, orb_limit in ASPECTS}

_DEFAULT_NAME_A = "甲方"
_DEFAULT_NAME_B = "乙方"


def _midpoint(lon_a: float, lon_b: float) -> float:
    """Shorter-arc midpoint of two ecliptic longitudes, normalized to [0, 360).

    Takes the *short* way round: when the two points are more than 180° apart the arc is
    measured through 0°, so the midpoint never lands on the far side of the wheel.
    """
    delta = (lon_b - lon_a) % 360.0
    if delta > 180.0:
        delta -= 360.0
    return _normalize_longitude(lon_a + delta / 2.0)


def _chart_points(chart: WesternChart) -> list[tuple[str, str, str, float]]:
    """The points one chart offers the other: ten planets plus ASC and MC.

    Each is ``(name, name_zh, glyph, longitude)``.
    """
    points = [(p.name, p.name_zh, p.glyph, p.longitude) for p in chart.planets]
    for axis in chart.axes:
        if axis.name in _AXIS_ZH:
            points.append((axis.name, _AXIS_ZH[axis.name], axis.name, axis.longitude))
    return points


def _aspect_plain(point_a: str, point_b: str, aspect_type: str) -> str:
    """一条相位一句白话：受控 frame + 两端受控点义，逐字填槽，不现编任何连接词。

    `{a}` 恒为甲方、`{b}` 恒为乙方——方向就是这一行的读法，前端那行也按同一次序排。
    """
    return compose_template(
        reading(SYNASTRY, synastry_plain.aspect_frame_key(aspect_type)),
        {
            "a": reading(SYNASTRY, synastry_plain.point_key(point_a)),
            "b": reading(SYNASTRY, synastry_plain.point_key(point_b)),
        },
    )


def synastry_plain_summary(aspects: Sequence[SynastryAspect], tier: str) -> str:
    """响应级总论：只重排已经命中的核心羁绊，顺逆次序由赋分表自己的基准分定。

    「命中」与开篇句的「账本里」是同一个口径：`core_bond` 且 `counted`（`counted` 即
    两端皆为个人点、真的进了相契度账本，`_synastry_score` 的同一道门）。今天五对核心羁绊
    两端全在 `SYNASTRY_PERSONAL_POINTS` 里，所以这两个条件给出同一批行、输出一字不变；
    守的是万一——有人给 `SYNASTRY_CORE_BONDS` 添一条含外行星的轴时，账本不记它，白话也不得
    替账本把它说进总论（开篇句那句「把账本里命中的核心羁绊合起来看」才不会变成假话）。

    同一组星名在两个方向上各检出一次是合盘的常态（`_synastry_aspects` 按 A×B **有序**遍历，
    本页那对 Greenwich 实盘 56 行只对应 47 个无序对，复测：对
    `tests/golden/test_synastry_golden.py::_chart` 的 `synastry_aspects`
    数一次 `len(rows)` 与 `len({tuple(sorted((p.point_a, p.point_b)))})` → `56 47`），
    所以一条核心轴可能被命中两回。`dedupe` 留第一次，而 `aspects` 按容许度升序排过——
    被留下的那次是更紧的那个相位（裁定 R12）。

    零命中的盘走 `openers["summary_none"]`（终审 C1）：不拿一句「下面按两侧重排一遍」去承诺一次空重排。
    """
    bonds = dedupe(
        [
            (
                synastry_plain.bond_key(aspect.point_a, aspect.point_b),
                SYNASTRY_ASPECT_DELTA[aspect.type],
            )
            for aspect in aspects
            if aspect.core_bond and aspect.counted
        ]
    )
    return compose(SYNASTRY, "summary" if bonds else "summary_none", bonds, tier)


def _synastry_aspects(
    points_a: list[tuple[str, str, str, float]],
    points_b: list[tuple[str, str, str, float]],
) -> list[SynastryAspect]:
    """Person-to-person aspects: every point of A against every point of B.

    Keeps the tightest aspect per pair and sorts by orb, so the strongest bonds lead.
    Each aspect records whether it is a core relationship bond and whether it counts
    toward the score (both endpoints are personal points).
    """
    aspects: list[SynastryAspect] = []
    for name_a, zh_a, glyph_a, lon_a in points_a:
        for name_b, zh_b, glyph_b, lon_b in points_b:
            delta = abs(lon_a - lon_b) % 360.0
            if delta > 180.0:
                delta = 360.0 - delta
            best: SynastryAspect | None = None
            for aspect_name, glyph, angle, orb_limit in ASPECTS:
                orb = abs(delta - angle)
                if orb <= orb_limit and (best is None or orb < best.orb):
                    nature, nature_zh = ASPECT_NATURE[aspect_name]
                    bond = tuple(sorted((name_a, name_b)))
                    best = SynastryAspect(
                        point_a=name_a, point_a_zh=zh_a, point_a_glyph=glyph_a,
                        point_b=name_b, point_b_zh=zh_b, point_b_glyph=glyph_b,
                        type=aspect_name, glyph=glyph, angle=angle, orb=round(orb, 2),
                        nature=nature, nature_zh=nature_zh,
                        core_bond=bond in SYNASTRY_CORE_BONDS,
                        counted=(name_a in SYNASTRY_PERSONAL_POINTS)
                        and (name_b in SYNASTRY_PERSONAL_POINTS),
                        plain=_aspect_plain(name_a, name_b, aspect_name),
                    )
            if best is not None:
                aspects.append(best)
    aspects.sort(key=lambda aspect: aspect.orb)
    return aspects


def _synastry_score(aspects: list[SynastryAspect]) -> ScoreValue:
    """Fold the counted synastry aspects into a self-explaining 相契度 ledger.

    Each counted aspect contributes one row: base delta × orb weight (tighter = higher,
    floor at ``1 - SYNASTRY_ORB_DECAY``) × core-bond emphasis. The tier is read from the
    clamped total; ``build_ledger`` re-derives the same clamp as its own row so
    ``Σ factors[].delta == value`` holds by construction.
    """
    contributions: list[ScoreFactor] = []
    for aspect in aspects:
        if not aspect.counted:
            continue
        base_delta = SYNASTRY_ASPECT_DELTA[aspect.type]
        orb_limit = _ORB_LIMIT_BY_TYPE[aspect.type]
        orb_weight = 1.0 - SYNASTRY_ORB_DECAY * min(1.0, aspect.orb / orb_limit)
        emphasis = SYNASTRY_CORE_EMPHASIS if aspect.core_bond else 1.0
        delta = round(base_delta * orb_weight * emphasis, 2)
        label = f"{aspect.point_a_zh}{SYNASTRY_ASPECT_ZH[aspect.type]}{aspect.point_b_zh}"
        if aspect.core_bond:
            label += "·核心"
        contributions.append(
            ScoreFactor(
                rule=f"synastry.{aspect.point_a}.{aspect.point_b}.{aspect.type}",
                label=label,
                delta=delta,
                source=SYNASTRY_SOURCE,
            )
        )
    raw = SYNASTRY_BASE + sum(factor.delta for factor in contributions)
    tier = synastry_tier(min(100.0, max(0.0, raw)))
    return build_ledger(
        base=SYNASTRY_BASE, tier=tier, contributions=contributions, base_rule="synastry.base"
    )


def _axis_longitude(chart: WesternChart, name: str) -> float:
    return next(axis.longitude for axis in chart.axes if axis.name == name)


def _composite_chart(chart_a: WesternChart, chart_b: WesternChart) -> CompositeChart:
    """Build the midpoint (composite) chart from two natal charts.

    Pure geometry: every composite longitude is the shorter-arc midpoint of the two natal
    longitudes. House cusps are paired cusp-by-cusp; the composite angles come from the
    two natal ASC/MC midpoints. Composite planets are then placed into the composite
    houses, and aspects among them are detected with the shared orbs.
    """
    cusp_longitudes = [
        _midpoint(cusp_a.longitude, cusp_b.longitude)
        for cusp_a, cusp_b in zip(chart_a.houses, chart_b.houses)
    ]

    planets: list[PlanetPlacement] = []
    for body_a, body_b in zip(chart_a.planets, chart_b.planets):
        longitude = _midpoint(body_a.longitude, body_b.longitude)
        index = _sign_index(longitude)
        planets.append(
            PlanetPlacement(
                name=body_a.name,
                glyph=body_a.glyph,
                name_zh=body_a.name_zh,
                longitude=round(longitude, 4),
                sign=SIGNS[index],
                sign_zh=SIGNS_ZH[index],
                sign_glyph=SIGN_GLYPHS[index],
                sign_index=index,
                degree_in_sign=_degree_in_sign(longitude),
                degree_text=_format_degree(longitude),
                house=_house_of(longitude, cusp_longitudes),
                retrograde=False,
                speed=0.0,
            )
        )

    houses = [
        HouseCusp(
            house=index + 1,
            longitude=round(cusp_longitudes[index], 4),
            sign=SIGNS[_sign_index(cusp_longitudes[index])],
            sign_zh=SIGNS_ZH[_sign_index(cusp_longitudes[index])],
            degree_in_sign=_degree_in_sign(cusp_longitudes[index]),
            degree_text=_format_degree(cusp_longitudes[index]),
        )
        for index in range(12)
    ]

    ascendant = _midpoint(_axis_longitude(chart_a, "ASC"), _axis_longitude(chart_b, "ASC"))
    midheaven = _midpoint(_axis_longitude(chart_a, "MC"), _axis_longitude(chart_b, "MC"))
    descendant = _normalize_longitude(ascendant + 180.0)
    nadir = _normalize_longitude(midheaven + 180.0)
    axes = [
        _make_axis("ASC", "Ascendant", ascendant, 1),
        _make_axis("DES", "Descendant", descendant, 7),
        _make_axis("MC", "Midheaven", midheaven, 10),
        _make_axis("IC", "Nadir", nadir, 4),
    ]

    element_balance = {"fire": 0, "earth": 0, "air": 0, "water": 0}
    modality_balance = {"cardinal": 0, "fixed": 0, "mutable": 0}
    for planet in planets:
        element_balance[SIGN_ELEMENT[planet.sign_index]] += 1
        modality_balance[SIGN_MODALITY[planet.sign_index]] += 1

    sun = next(planet for planet in planets if planet.name == "Sun")
    moon = next(planet for planet in planets if planet.name == "Moon")

    return CompositeChart(
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
        element_balance=element_balance,
        modality_balance=modality_balance,
    )


def compute_synastry(
    *,
    person_a: SynastryPerson,
    person_b: SynastryPerson,
    house_system: str = "P",
    ephemeris_path: str | None = None,
) -> SynastryChart:
    """Compare two natal charts: synastry aspects, composite midpoints, and a score.

    Pure apart from the in-process ephemeris and the cached city lookup. Both people need
    a full geographic position (city or latitude/longitude) because the ascendant and house
    cusps — which feed both the synastry angles and the composite — depend on it. Raises
    :class:`InvalidBirthDataError` (via ``resolve_coordinates``) when a location is missing,
    and :class:`UnsupportedMethodError` (via ``compute_western_chart``) for an unknown house
    system.
    """
    lat_a, lon_a = resolve_coordinates(person_a.city, person_a.latitude, person_a.longitude)
    lat_b, lon_b = resolve_coordinates(person_b.city, person_b.latitude, person_b.longitude)

    chart_a = compute_western_chart(
        birth_date=person_a.birth_date, birth_time=person_a.birth_time,
        latitude=lat_a, longitude=lon_a,
        utc_offset_hours=person_a.utc_offset_hours, house_system=house_system,
        ephemeris_path=ephemeris_path,
    )
    chart_b = compute_western_chart(
        birth_date=person_b.birth_date, birth_time=person_b.birth_time,
        latitude=lat_b, longitude=lon_b,
        utc_offset_hours=person_b.utc_offset_hours, house_system=house_system,
        ephemeris_path=ephemeris_path,
    )

    aspects = _synastry_aspects(_chart_points(chart_a), _chart_points(chart_b))
    composite = _composite_chart(chart_a, chart_b)
    score = _synastry_score(aspects)

    tables = [
        ProvenanceTable(name=name, version=CONTENT_VERSION, source=source)
        for name, source in SYNASTRY_CONTENT_SOURCES
    ]

    return SynastryChart(
        person_a_name=person_a.name or _DEFAULT_NAME_A,
        person_b_name=person_b.name or _DEFAULT_NAME_B,
        person_a=chart_a,
        person_b=chart_b,
        synastry_aspects=aspects,
        composite=composite,
        score=score,
        plain_summary=synastry_plain_summary(aspects, score.tier),
        provenance=SynastryProvenance(
            engine="pyswisseph", note=NOTE, method=SYNASTRY_METHOD, tables=tables
        ),
    )
