"""BaZi (八字) natal-chart engine.

All calendrical and sexagenary computation is delegated to ``lunar-python`` (the
authoritative library named in PRD Appendix A); this module never derives stems,
branches, solar terms or luck pillars itself. On top of the library output it
adds two deterministic computations:

* a weighted five-element distribution (五行分布), and
* a day-master strength / useful-god assessment (日主旺衰 / 用神喜忌).

The classical tables in play are lunar-python's: four pillars, ten-gods, hidden
stems, nayin and luck cycles. Everything this module adds on top of them is a
documented derivation with its own score ledger: the hidden-stem weights and the
three strength factors live in ``app.engines.bazi_strength``, and each score
there carries the arithmetic that produced it (spec §6.1/§6.4).

True Solar Time (PRD 7) is applied *before* constructing ``Solar(...)`` because
``lunar-python`` uses the supplied wall-clock time verbatim with no astronomical
or geographic correction.
"""

from datetime import date, datetime, time

from lunar_python import Lunar, Solar

from app.content.wuxing import ELEMENT_ORDER, GAN_ELEMENT
from app.engines.bazi_strength import assess_strength, element_weight_scores, fuyin_choices
from app.schemas.bazi import (
    BaziChart,
    BaziPillar,
    DayMasterAnalysis,
    DayunStep,
    LiunianYear,
    WuxingScore,
)
from app.schemas.common import CalendarType, Gender
from app.solar.true_solar_time import (
    STANDARD_MERIDIAN_CN,
    true_solar_offset_minutes,
    true_solar_time,
)

# --- Fixed classical reference tables (standard, not computed) ---------------
# The five-element cycles and stem/branch elements live in app.content.wuxing.
# The hidden-stem weights and the strength bands live in app.engines.bazi_strength,
# which keeps its own score ledger; this module only reads them.

# (schema position, lunar-python method fragment, Chinese label).
_PILLARS = (
    ("year", "Year", "年柱"),
    ("month", "Month", "月柱"),
    ("day", "Day", "日柱"),
    ("hour", "Time", "时柱"),
)


def _resolve_standard_datetime(birth_date: date, birth_time: time, calendar: CalendarType) -> datetime:
    """Return the civil standard-time datetime for the supplied birth data.

    A lunar-calendar date is converted to its Gregorian equivalent (preserving
    the wall-clock time) so that the True Solar Time correction and pillar
    derivation both operate on a standard civil datetime.
    """
    if calendar is CalendarType.LUNAR:
        lunar = Lunar.fromYmdHms(
            birth_date.year, birth_date.month, birth_date.day,
            birth_time.hour, birth_time.minute, birth_time.second,
        )
        solar = lunar.getSolar()
        return datetime(
            solar.getYear(), solar.getMonth(), solar.getDay(),
            solar.getHour(), solar.getMinute(), solar.getSecond(),
        )
    return datetime.combine(birth_date, birth_time)


def _build_pillar(ec: object, position: str, method: str, label: str) -> BaziPillar:
    """Extract one pillar's full detail from an ``EightChar`` instance."""
    wuxing = getattr(ec, f"get{method}WuXing")()          # e.g. "土土" (stem, branch)
    hidden_stems = list(getattr(ec, f"get{method}HideGan")())
    return BaziPillar(
        position=position,
        label=label,
        ganzhi=getattr(ec, f"get{method}")(),
        gan=getattr(ec, f"get{method}Gan")(),
        zhi=getattr(ec, f"get{method}Zhi")(),
        gan_element=wuxing[0],
        zhi_element=wuxing[1],
        nayin=getattr(ec, f"get{method}NaYin")(),
        hidden_stems=hidden_stems,
        hidden_stem_elements=[GAN_ELEMENT[stem] for stem in hidden_stems],
        shishen_gan=getattr(ec, f"get{method}ShiShenGan")(),
        shishen_zhi=list(getattr(ec, f"get{method}ShiShenZhi")()),
        di_shi=getattr(ec, f"get{method}DiShi")(),
        xun=getattr(ec, f"get{method}Xun")(),
        xun_kong=getattr(ec, f"get{method}XunKong")(),
    )


def _count_primary_characters(pillars: list[BaziPillar]) -> dict[str, int]:
    """Headcount of each element among the eight primary characters (四干 + 四支).

    Kept separate from the weighted tally on purpose: the two answer different
    questions and must not be merged. The count is the "五行分布" the PRD asks
    for, so a card labelled with a count keeps that meaning; the weighted figure
    beside it comes from ``bazi_strength.element_weight_scores`` — four stems at
    1.0 plus each hidden stem by its 本/中/余气 role.
    """
    counts = {element: 0 for element in ELEMENT_ORDER}
    for pillar in pillars:
        counts[pillar.gan_element] += 1
        counts[pillar.zhi_element] += 1
    return counts


def _analyze_day_master(
    pillars: list[BaziPillar],
    element_scores: dict[str, float],
    day_master: str,
    day_master_element: str,
    month_zhi: str,
) -> DayMasterAnalysis:
    """Assess day-master strength and derive the useful / unfavourable gods.

    The three factors (得令/得地/得势) and the 扶抑 choice live in
    ``app.engines.bazi_strength``, which returns a score ledger; this function only
    assembles the response and the summary sentence. ``element_scores`` is the same
    weighted tally the 五行分布 bars are drawn from, so the chart computes it once.
    """
    strength = assess_strength(pillars)
    favourable, unfavourable = fuyin_choices(strength.level, day_master_element, element_scores)

    summary = (
        f"日主{day_master}（{day_master_element}）生于{month_zhi}月，"
        f"三因子合分{strength.score.value:.2f}，判为{strength.label}"
        f"{'（临界）' if strength.borderline else ''}；"
        f"喜用{'、'.join(favourable) or '无所偏取'}，忌{'、'.join(unfavourable) or '无所偏忌'}。"
    )
    return DayMasterAnalysis(
        day_master=day_master,
        day_master_element=day_master_element,
        # 旧口径的加权和没有出处，已随三因子账本一起作废；字段此时仍是必填，
        # 只能如实留空，Task 10 连同字段一并删除。
        support_score=0.0,
        drain_score=0.0,
        strength_ratio=round(strength.score.value / 100.0, 4),
        level=strength.level,
        label=strength.label,
        favorable_elements=favourable,
        unfavorable_elements=unfavourable,
        summary=summary,
        strength=strength.score,
        borderline=strength.borderline,
    )


def _build_dayun(
    ec: object, gender: Gender | None, reference_date: date | None
) -> tuple[str | None, str | None, list[DayunStep], list[LiunianYear]]:
    """Build the luck-pillar (大运) sequence and the current year's 流年.

    Returns ``(direction, start_solar, steps, current_liunian)``. Without a
    gender the luck pillars are undefined, so empty results are returned.
    """
    if gender is None:
        return None, None, [], []

    yun = ec.getYun(1 if gender is Gender.MALE else 0)
    direction = "forward" if yun.isForward() else "backward"
    start_solar = yun.getStartSolar().toString()

    raw_dayun = yun.getDaYun()
    steps = [
        DayunStep(
            index=item.getIndex(),
            ganzhi=item.getGanZhi(),
            start_age=item.getStartAge(),
            end_age=item.getEndAge(),
            start_year=item.getStartYear(),
            end_year=item.getEndYear(),
            xun=item.getXun(),
            xun_kong=item.getXunKong(),
        )
        for item in raw_dayun
    ]

    current_liunian: list[LiunianYear] = []
    if reference_date is not None:
        for position, step in enumerate(steps):
            if step.start_year <= reference_date.year <= step.end_year:
                step.is_current = True
                current_liunian = [
                    LiunianYear(year=item.getYear(), age=item.getAge(), ganzhi=item.getGanZhi())
                    for item in raw_dayun[position].getLiuNian()
                ]
                break
    return direction, start_solar, steps, current_liunian


def compute_bazi_chart(
    *,
    birth_date: date,
    birth_time: time,
    calendar: CalendarType = CalendarType.SOLAR,
    longitude: float = STANDARD_MERIDIAN_CN,
    gender: Gender | None = None,
    apply_true_solar_time: bool = True,
    reference_date: date | None = None,
) -> BaziChart:
    """Compute a complete BaZi natal chart from validated birth data.

    Pure function: no HTTP, no I/O. ``longitude`` drives the True Solar Time
    correction (PRD 7); ``reference_date`` (optional) marks the current luck
    pillar and its annual fortunes, keeping the core chart deterministic.
    """
    standard_dt = _resolve_standard_datetime(birth_date, birth_time, calendar)

    if apply_true_solar_time:
        chart_dt = true_solar_time(standard_dt, longitude)
        offset_minutes: float | None = round(true_solar_offset_minutes(standard_dt, longitude), 2)
        tst_text: str | None = chart_dt.strftime("%Y-%m-%d %H:%M")
    else:
        chart_dt = standard_dt
        offset_minutes = None
        tst_text = None

    solar = Solar.fromYmdHms(
        chart_dt.year, chart_dt.month, chart_dt.day, chart_dt.hour, chart_dt.minute, chart_dt.second
    )
    lunar = solar.getLunar()
    eight_char = lunar.getEightChar()

    pillars = [_build_pillar(eight_char, position, method, label) for position, method, label in _PILLARS]
    counts = _count_primary_characters(pillars)
    element_scores = element_weight_scores(pillars)

    day_master = eight_char.getDayGan()
    day_master_element = eight_char.getDayWuXing()[0]
    analysis = _analyze_day_master(
        pillars, element_scores, day_master, day_master_element, eight_char.getMonthZhi()
    )
    dayun_direction, dayun_start, dayun_steps, current_liunian = _build_dayun(eight_char, gender, reference_date)

    return BaziChart(
        standard_datetime=standard_dt.strftime("%Y-%m-%d %H:%M"),
        calendar=calendar.value,
        true_solar_time=tst_text,
        tst_applied=apply_true_solar_time,
        tst_offset_minutes=offset_minutes,
        longitude=longitude,
        lunar_date=lunar.toString(),
        four_pillars=eight_char.toString(),
        pillars=pillars,
        zodiac=lunar.getYearShengXiaoByLiChun(),
        day_master=day_master,
        day_master_element=day_master_element,
        ming_gong=eight_char.getMingGong(),
        ming_gong_nayin=eight_char.getMingGongNaYin(),
        tai_yuan=eight_char.getTaiYuan(),
        tai_yuan_nayin=eight_char.getTaiYuanNaYin(),
        wuxing=[
            WuxingScore(element=element, count=counts[element], score=round(element_scores[element], 2))
            for element in ELEMENT_ORDER
        ],
        missing_elements=[element for element in ELEMENT_ORDER if counts[element] == 0],
        analysis=analysis,
        dayun_direction=dayun_direction,
        dayun_start_solar=dayun_start,
        dayun=dayun_steps,
        current_liunian=current_liunian,
    )
