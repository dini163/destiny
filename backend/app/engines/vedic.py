"""吠陀占星 (Jyotish) engine — sidereal chart, nakshatras and Vimshottari dasha.

All celestial mechanics come from Swiss Ephemeris with the Lahiri (Chitrapaksha)
ayanamsa; this module never computes positions itself (PRD 10.2). On top of the raw
sidereal longitudes it performs standard, deterministic Jyotish post-processing:

* **Sidereal zodiac** — tropical longitudes minus the Lahiri ayanamsa.
* **Whole-sign houses** — one sign per house, counted from the Lagna (ascendant).
* **Nakshatra / pada** — each graha's lunar mansion (27 × 13°20') and quarter.
* **Vimshottari dasha** — the 120-year period timeline started from the natal Moon's
  nakshatra, its balance at birth, mahadashas and their nine antardashas.

The Navagraha are the Sun, Moon, five classical planets and the two lunar nodes
(Rahu / Ketu); the outer planets Uranus–Pluto are *not* part of classical Jyotish.
Sign/degree geometry helpers are imported from :mod:`app.engines.western` (they are
pure longitude math, zodiac-independent) so the two engines can never drift. No
personalised fortune is invented at runtime.
"""

from datetime import date, datetime, time, timedelta

import swisseph as swe

from app.content import CONTENT_VERSION, vedic_plain
from app.content.vedic import (
    DASHA_ORDER,
    DASHA_SPANS_BY_ORDER,
    GRAHAS,
    GRAHA_BY_NAME,
    NAKSHATRA_SPAN,
    NAKSHATRAS,
    SIGN_GLYPHS,
    SIGNS_EN,
    SIGNS_ZH,
    VEDIC_SOURCE,
    VIMSHOTTARI_TOTAL,
    nakshatra_of,
    pada_of,
)
from app.core.errors import EphemerisError
from app.engines.plain_compose import compose
from app.engines.plain_corpora import VEDIC
from app.engines.western import _degree_in_sign, _format_degree, _normalize_longitude, _sign_index
from app.schemas.common import PlainSection
from app.schemas.vedic import (
    Antardasha,
    CurrentDasha,
    Mahadasha,
    RashiCell,
    VedicChart,
    VedicPlanet,
    VedicProvenance,
    Vimshottari,
)

NOTE = (
    "吠陀占星用恒星黄道（Sidereal），以 Lahiri（Chitrapaksha）岁差把热带黄经减去约 23–24° 得恒星黄经；"
    "分宫采整宫制（一星座即一宫），以命度（Lagna，恒星上升点）所在星座为第一宫顺布十二宫。"
    "九曜（Navagraha）为日、月、火、水、木、金、土，加罗睺（北交点）与计都（南交点，罗睺对冲 180°），"
    "不含天王、海王、冥王三王星。每曜定其所在 27 宿（Nakshatra，各 13°20'）与四足（pada）。"
    "Vimshottari 大运以太阴（月亮）所在宿起运：该宿守护曜为第一大运主，其于出生时的剩余年数按太阴已行过该宿的比例折算，"
    "此后九曜依固定序（计都·金星·太阳·太阴·火星·罗睺·木星·土星·水星）值年，共 120 年；每大运再分九个安塔尔大运（bhukti）。"
    "行星黄经、命度与岁差皆由瑞士星历实时计算，大运按标准值年数确定性排布，未作任何主观吉凶或个人运势的虚构演绎。"
)

_AYANAMSA_NAME = "Lahiri (Chitrapaksha)"

#: Mean tropical year in days, for dasha date arithmetic.
_YEAR_DAYS = 365.24219

#: Swiss Ephemeris body constants for the grahas that have one; Ketu is derived.
_GRAHA_BODY = {
    "Sun": swe.SUN,
    "Moon": swe.MOON,
    "Mars": swe.MARS,
    "Mercury": swe.MERCURY,
    "Jupiter": swe.JUPITER,
    "Venus": swe.VENUS,
    "Saturn": swe.SATURN,
    "Rahu": swe.MEAN_NODE,
}


def _sidereal_flags(ephemeris_path: str | None) -> int:
    """Select the Lahiri sidereal mode and return calc flags for the ephemeris."""
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    if ephemeris_path:
        swe.set_ephe_path(ephemeris_path)
        return swe.FLG_SPEED | swe.FLG_SWIEPH | swe.FLG_SIDEREAL
    return swe.FLG_SPEED | swe.FLG_MOSEPH | swe.FLG_SIDEREAL


def _graha_positions(julian_day: float, flags: int) -> dict[str, list[float]]:
    """Sidereal ``[lon, lat, dist, speed]`` for all nine grahas (Ketu = Rahu + 180°)."""
    positions = {name: swe.calc_ut(julian_day, body, flags)[0] for name, body in _GRAHA_BODY.items()}
    rahu = positions["Rahu"]
    positions["Ketu"] = [_normalize_longitude(rahu[0] + 180.0), rahu[1], rahu[2], rahu[3]]
    return positions


def _whole_sign_house(sign_index: int, lagna_index: int) -> int:
    """House (1-12) of a sign under the whole-sign system counted from the Lagna."""
    return ((sign_index - lagna_index) % 12) + 1


def _years_to_timedelta(years: float) -> timedelta:
    return timedelta(days=years * _YEAR_DAYS)


def _contains(start: datetime, end: datetime, moment: datetime) -> bool:
    return start <= moment < end


def _antardashas(
    md_order_index: int, md_start: datetime, md_end: datetime,
    md_full_span: float, elapsed_fraction: float, target_dt: datetime,
) -> list[Antardasha]:
    """The nine sub-periods of a mahadasha, clipped to the mahadasha's real window.

    ``elapsed_fraction`` is non-zero only for the birth mahadasha, where the timeline
    is joined part-way through: the notional full-mahadasha start ``t0`` lies before
    birth, so sub-periods already elapsed are dropped and the running one starts at
    birth. Later mahadashas pass ``0.0`` and run their full nine sub-periods.
    """
    t0 = md_start - _years_to_timedelta(md_full_span * elapsed_fraction)
    durations = [
        md_full_span * DASHA_SPANS_BY_ORDER[(md_order_index + j) % 9] / float(VIMSHOTTARI_TOTAL)
        for j in range(9)
    ]
    result: list[Antardasha] = []
    cumulative = 0.0
    for j in range(9):
        ad_start_abs = t0 + _years_to_timedelta(cumulative)
        cumulative += durations[j]
        ad_end_abs = t0 + _years_to_timedelta(cumulative)
        start = max(ad_start_abs, md_start)
        end = min(ad_end_abs, md_end)
        if end <= start:
            continue
        lord = DASHA_ORDER[(md_order_index + j) % 9]
        graha = GRAHA_BY_NAME[lord]
        years = (end - start).total_seconds() / (86400.0 * _YEAR_DAYS)
        result.append(
            Antardasha(
                lord=lord, lord_zh=graha.name_zh, glyph=graha.glyph,
                start_date=start.strftime("%Y-%m-%d"), end_date=end.strftime("%Y-%m-%d"),
                years=round(years, 4), is_current=_contains(start, end, target_dt),
            )
        )
    return result


def _vimshottari(base_dt: datetime, moon_longitude: float, target_date: date) -> Vimshottari:
    """Build the 120-year Vimshottari timeline from the natal Moon's sidereal longitude."""
    lon = moon_longitude % 360.0
    nak_index = int(lon // NAKSHATRA_SPAN)
    fraction = (lon % NAKSHATRA_SPAN) / NAKSHATRA_SPAN
    first_index = nak_index % 9
    balance = DASHA_SPANS_BY_ORDER[first_index] * (1.0 - fraction)
    birth_nak = NAKSHATRAS[nak_index]
    birth_lord = DASHA_ORDER[first_index]
    target_dt = datetime.combine(target_date, time(12, 0))

    mahadashas: list[Mahadasha] = []
    cursor = base_dt
    remaining = float(VIMSHOTTARI_TOTAL)
    k = 0
    while remaining > 1e-9:
        order_index = (first_index + k) % 9
        lord = DASHA_ORDER[order_index]
        graha = GRAHA_BY_NAME[lord]
        full_span = float(DASHA_SPANS_BY_ORDER[order_index])
        years = min(balance if k == 0 else full_span, remaining)
        md_start = cursor
        md_end = cursor + _years_to_timedelta(years)
        antardashas = _antardashas(
            order_index, md_start, md_end, full_span, fraction if k == 0 else 0.0, target_dt
        )
        mahadashas.append(
            Mahadasha(
                lord=lord, lord_zh=graha.name_zh, glyph=graha.glyph,
                start_date=md_start.strftime("%Y-%m-%d"), end_date=md_end.strftime("%Y-%m-%d"),
                years=round(years, 4), is_current=_contains(md_start, md_end, target_dt),
                antardashas=antardashas,
            )
        )
        cursor = md_end
        remaining -= years
        k += 1

    current_md = next((m for m in mahadashas if m.is_current), None)
    current: CurrentDasha | None = None
    if current_md is not None:
        current_ad = next((a for a in current_md.antardashas if a.is_current), None)
        current = CurrentDasha(
            target_date=target_date.strftime("%Y-%m-%d"),
            mahadasha_lord=current_md.lord,
            mahadasha_lord_zh=current_md.lord_zh,
            antardasha_lord=current_ad.lord if current_ad else None,
            antardasha_lord_zh=current_ad.lord_zh if current_ad else None,
        )

    return Vimshottari(
        balance_at_birth_years=round(balance, 4),
        moon_elapsed_fraction=round(fraction, 6),
        birth_nakshatra=birth_nak.name_en,
        birth_nakshatra_zh=birth_nak.name_zh,
        birth_lord=birth_lord,
        birth_lord_zh=GRAHA_BY_NAME[birth_lord].name_zh,
        mahadashas=mahadashas,
        current=current,
    )


def build_plain(
    *,
    planets: list[VedicPlanet],
    lagna_nakshatra: str,
    current: CurrentDasha | None,
) -> list[PlainSection]:
    """按已经算出的九曜位置、宿位与现行主事星逐条选句，拼成页尾「白话详解」的四段。

    只选句，不现编（`plain_compose.compose` 的立身规矩，也是 `VEDIC_PLAIN_NOTE` 那句
    「请求时不生成任何中文」的唯一兑现点）。段的次序是产品决定，由
    `tests/golden/test_vedic_golden.py::test_the_plain_block_is_four_sections_in_the_declared_order`
    钉成字面量。

    三个入参全是关键字：`plain` 是 `VedicChart` 的字段，装配时那个对象还没造出来
    （与 `engines/transit.py::build_plain` 同形）。

    去重只压**重复**不压内容：九曜可能落在同一宿（C 手实测 Krittika 两颗、D 手 Jyeshtha
    与 Purva Ashadha 各两颗），大运与小运可能是同一颗主事星；逐条搬运会让同一句在同一段
    里连说两三遍。命度宿与九曜宿取并集（A 手 9、B 手 10）。
    """

    def emit(section: str, keys: list[str]) -> PlainSection:
        if not keys and section not in vedic_plain.VEDIC_NONE_BRANCHES:
            # 崩而不静默：一张恒非空的段收不到键是编程错误。`dasha` 是唯一可达的空态。
            raise ValueError(
                f"vedic 段 {section!r} 收不到任何键，"
                f"且它不在 VEDIC_NONE_BRANCHES 里：{vedic_plain.VEDIC_NONE_BRANCHES}"
            )
        opener = vedic_plain.VEDIC_NONE_BRANCHES[section] if not keys else section
        return PlainSection(
            title=vedic_plain.VEDIC_SECTION_TITLES[section],
            text=compose(VEDIC, opener, [(key, 0) for key in keys]),
        )

    dasha_keys: list[str] = []
    if current is not None:
        dasha_keys.append(vedic_plain.dasha_lord_key(current.mahadasha_lord))
        if current.antardasha_lord is not None:
            dasha_keys.append(vedic_plain.dasha_lord_key(current.antardasha_lord))
        dasha_keys = list(dict.fromkeys(dasha_keys))

    nakshatras = list(
        dict.fromkeys([planet.nakshatra for planet in planets] + [lagna_nakshatra])
    )
    return [
        emit(
            "gruha_sign",
            [vedic_plain.gruha_sign_key(planet.name, planet.sign) for planet in planets],
        ),
        emit(
            "gruha_house",
            [vedic_plain.gruha_house_key(planet.name, planet.house) for planet in planets],
        ),
        emit("nakshatra", [vedic_plain.nakshatra_key(nakshatra) for nakshatra in nakshatras]),
        emit("dasha", dasha_keys),
    ]


def compute_vedic_chart(
    *,
    birth_date: date,
    birth_time: time,
    latitude: float,
    longitude: float,
    utc_offset_hours: float | None = None,
    target_date: date,
    ephemeris_path: str | None = None,
) -> VedicChart:
    """Compute a Vedic (sidereal) natal chart and its Vimshottari dasha timeline.

    Pure apart from the in-process ephemeris: no HTTP, no I/O. The local birth time
    is converted to Universal Time using ``utc_offset_hours`` (or a longitude-derived
    theoretical zone when omitted) before evaluating sidereal positions.
    """
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
        flags = _sidereal_flags(ephemeris_path)  # sets Lahiri mode before any read
        ayanamsa = swe.get_ayanamsa_ut(julian_day)
        positions = _graha_positions(julian_day, flags)
        _cusps, ascmc = swe.houses(julian_day, latitude, longitude, b"W")
    except swe.Error as exc:  # pragma: no cover - defensive ephemeris failure
        raise EphemerisError(f"Swiss Ephemeris computation failed: {exc}") from exc

    lagna = _normalize_longitude(ascmc[0] - ayanamsa)
    lagna_index = _sign_index(lagna)
    lagna_nak = nakshatra_of(lagna)

    planets: list[VedicPlanet] = []
    for graha in GRAHAS:
        pos = positions[graha.name]
        lon = _normalize_longitude(pos[0])
        index = _sign_index(lon)
        nak = nakshatra_of(lon)
        planets.append(
            VedicPlanet(
                name=graha.name, glyph=graha.glyph, name_zh=graha.name_zh, name_sa=graha.name_sa,
                longitude=round(lon, 4), sign=SIGNS_EN[index], sign_zh=SIGNS_ZH[index],
                sign_glyph=SIGN_GLYPHS[index], sign_index=index,
                degree_in_sign=_degree_in_sign(lon), degree_text=_format_degree(lon),
                house=_whole_sign_house(index, lagna_index),
                nakshatra=nak.name_en, nakshatra_zh=nak.name_zh, nakshatra_devanagari=nak.name_devanagari,
                nakshatra_lord=nak.lord, nakshatra_lord_zh=GRAHA_BY_NAME[nak.lord].name_zh,
                pada=pada_of(lon), retrograde=pos[3] < 0, speed=round(pos[3], 6),
            )
        )

    rashis = [
        RashiCell(
            sign_index=index, sign=SIGNS_EN[index], sign_zh=SIGNS_ZH[index], sign_glyph=SIGN_GLYPHS[index],
            house=_whole_sign_house(index, lagna_index), is_lagna=(index == lagna_index),
            planet_names=[p.name for p in planets if p.sign_index == index],
        )
        for index in range(12)
    ]

    moon = next(p for p in planets if p.name == "Moon")
    vimshottari = _vimshottari(local_dt, moon.longitude, target_date)
    plain = build_plain(
        planets=planets,
        lagna_nakshatra=lagna_nak.name_en,
        current=vimshottari.current,
    )

    return VedicChart(
        local_datetime=local_dt.strftime("%Y-%m-%d %H:%M"),
        utc_datetime=ut_dt.strftime("%Y-%m-%d %H:%M"),
        julian_day=round(julian_day, 5),
        latitude=latitude,
        longitude=longitude,
        utc_offset_hours=offset,
        utc_offset_source=offset_source,
        ayanamsa=round(ayanamsa, 4),
        ayanamsa_name=_AYANAMSA_NAME,
        lagna_sign=SIGNS_EN[lagna_index],
        lagna_sign_zh=SIGNS_ZH[lagna_index],
        lagna_sign_glyph=SIGN_GLYPHS[lagna_index],
        lagna_index=lagna_index,
        lagna_degree_text=_format_degree(lagna),
        lagna_nakshatra=lagna_nak.name_en,
        lagna_nakshatra_zh=lagna_nak.name_zh,
        moon_sign=moon.sign,
        moon_sign_zh=moon.sign_zh,
        moon_nakshatra=moon.nakshatra,
        moon_nakshatra_zh=moon.nakshatra_zh,
        moon_nakshatra_lord=moon.nakshatra_lord,
        moon_nakshatra_lord_zh=moon.nakshatra_lord_zh,
        moon_pada=moon.pada,
        planets=planets,
        rashis=rashis,
        vimshottari=vimshottari,
        plain=plain,
        provenance=VedicProvenance(
            engine="pyswisseph", ayanamsa_name=_AYANAMSA_NAME,
            content_version=CONTENT_VERSION, source=VEDIC_SOURCE, note=NOTE,
        ),
    )
