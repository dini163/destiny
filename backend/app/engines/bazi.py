"""BaZi (八字) natal-chart engine.

All calendrical and sexagenary computation is delegated to ``lunar-python`` (the
authoritative library named in PRD Appendix A); this module never derives stems,
branches, solar terms or luck pillars itself. On top of the library output it
adds two deterministic, fully documented analyses:

* a weighted five-element distribution (五行分布), and
* a day-master strength / useful-god assessment (日主旺衰 / 用神喜忌) based on
  the library-provided ten-gods (十神) and classical support-vs-drain theory.

True Solar Time (PRD 7) is applied *before* constructing ``Solar(...)`` because
``lunar-python`` uses the supplied wall-clock time verbatim with no astronomical
or geographic correction.
"""

from datetime import date, datetime, time

from lunar_python import Lunar, Solar

from app.content.wuxing import (
    CONTROLS,
    CONTROLLED_BY,
    ELEMENT_ORDER,
    GAN_ELEMENT,
    GENERATES,
    GENERATED_BY,
)
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

# Ten-gods that strengthen the day master (同党: 印 + 比劫).
SHISHEN_SUPPORT = frozenset({"比肩", "劫财", "正印", "偏印"})
# Ten-gods that weaken the day master (异党: 食伤 + 财 + 官杀).
SHISHEN_DRAIN = frozenset({"食神", "伤官", "正财", "偏财", "正官", "七杀"})

# Weighting for the strength tally (transparent, documented heuristic).
STEM_WEIGHT = 1.0                       # each visible heavenly stem
HIDDEN_STEM_WEIGHTS = (1.0, 0.5, 0.2)   # 本气 / 中气 / 余气 within a branch
MONTH_BRANCH_FACTOR = 1.5               # 月令 (seasonal command) emphasis

# Strength classification thresholds on support / (support + drain).
STRONG_THRESHOLD = 0.55
WEAK_THRESHOLD = 0.45

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


def _tally_elements(pillars: list[BaziPillar]) -> tuple[dict[str, int], dict[str, float]]:
    """Return (headcount, weighted score) per element across the chart.

    The headcount covers the eight primary characters (four stems + four branch
    main elements). The weighted score additionally folds in each branch's
    hidden stems, with the month branch emphasised (月令司令).
    """
    counts = {element: 0 for element in ELEMENT_ORDER}
    scores = {element: 0.0 for element in ELEMENT_ORDER}
    for pillar in pillars:
        counts[pillar.gan_element] += 1
        counts[pillar.zhi_element] += 1

        scores[pillar.gan_element] += STEM_WEIGHT
        factor = MONTH_BRANCH_FACTOR if pillar.position == "month" else 1.0
        for index, hidden_element in enumerate(pillar.hidden_stem_elements):
            weight = HIDDEN_STEM_WEIGHTS[min(index, len(HIDDEN_STEM_WEIGHTS) - 1)] * factor
            scores[hidden_element] += weight
    return counts, scores


def _analyze_day_master(ec: object, day_master: str, day_master_element: str, month_zhi: str) -> DayMasterAnalysis:
    """Assess day-master strength and derive the useful / unfavourable gods.

    Support and drain are tallied from the library-provided ten-gods, weighting
    visible stems and branch hidden stems, with the month branch emphasised. The
    day stem itself is the reference point and is excluded from the tally.
    """
    support = 0.0
    drain = 0.0
    for _position, method, _label in _PILLARS:
        if method != "Day":  # the day stem is the anchor, not a supporter
            shishen = getattr(ec, f"get{method}ShiShenGan")()
            if shishen in SHISHEN_SUPPORT:
                support += STEM_WEIGHT
            elif shishen in SHISHEN_DRAIN:
                drain += STEM_WEIGHT
        factor = MONTH_BRANCH_FACTOR if method == "Month" else 1.0
        for index, shishen in enumerate(getattr(ec, f"get{method}ShiShenZhi")()):
            weight = HIDDEN_STEM_WEIGHTS[min(index, len(HIDDEN_STEM_WEIGHTS) - 1)] * factor
            if shishen in SHISHEN_SUPPORT:
                support += weight
            elif shishen in SHISHEN_DRAIN:
                drain += weight

    total = support + drain
    ratio = support / total if total else 0.0
    if ratio >= STRONG_THRESHOLD:
        level, label = "strong", "身强"
    elif ratio <= WEAK_THRESHOLD:
        level, label = "weak", "身弱"
    else:
        level, label = "balanced", "中和"

    if ratio > 0.5:  # strong-leaning: favour the draining gods (食伤/财/官杀)
        favorable = [GENERATES[day_master_element], CONTROLS[day_master_element], CONTROLLED_BY[day_master_element]]
    else:            # weak-leaning: favour the supporting gods (印/比劫)
        favorable = [GENERATED_BY[day_master_element], day_master_element]
    unfavorable = [element for element in ELEMENT_ORDER if element not in favorable]

    summary = (
        f"日主{day_master}（{day_master_element}）生于{month_zhi}月，"
        f"生扶{support:.2f} / 克泄{drain:.2f}（{ratio:.0%}），判为{label}；"
        f"喜用{'、'.join(favorable)}，忌{'、'.join(unfavorable)}。"
    )
    return DayMasterAnalysis(
        day_master=day_master,
        day_master_element=day_master_element,
        support_score=round(support, 2),
        drain_score=round(drain, 2),
        strength_ratio=round(ratio, 4),
        level=level,
        label=label,
        favorable_elements=favorable,
        unfavorable_elements=unfavorable,
        summary=summary,
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
    counts, scores = _tally_elements(pillars)

    day_master = eight_char.getDayGan()
    day_master_element = eight_char.getDayWuXing()[0]
    analysis = _analyze_day_master(eight_char, day_master, day_master_element, eight_char.getMonthZhi())
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
            WuxingScore(element=element, count=counts[element], score=round(scores[element], 2))
            for element in ELEMENT_ORDER
        ],
        missing_elements=[element for element in ELEMENT_ORDER if counts[element] == 0],
        analysis=analysis,
        dayun_direction=dayun_direction,
        dayun_start_solar=dayun_start,
        dayun=dayun_steps,
        current_liunian=current_liunian,
    )
