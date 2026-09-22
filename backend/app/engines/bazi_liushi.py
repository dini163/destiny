"""流时（一个八字日的十二时辰）引擎：采样枚举、时段扫描、四段账本与单日总装。

与 `bazi_liuri` 的关系是**复用而非平行**：段定位、段基准、逐日装配（含那根日柱）全部
跨模块取流日的那一份，本模块只多两件事——把一天切成十二个采样点，和给每格加 `shi.`
那一段账（spec §5.1/§5.3）。依赖方向单向 `bazi_liushi → bazi_liuri → bazi_transit`；
切片 2 因为反向 import 撞过环，这条不再商量。

时柱、钟面区间、十二长生一律取 lunar-python 与已对拍钉住的那张长生表。流时柱**不进**
旺衰、格局、用神与命局 39 条（spec §2.7，§9.3 红线跑的是本模块的函数）。
"""

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from lunar_python import Solar

from app.content.bazi_shishen import ten_god_meaning
from app.core.errors import TransitRangeError
from app.engines.bazi import compute_bazi_chart
from app.engines.bazi_liuri import (
    LiuriDayRow,
    LiuriMonthBase,
    LiuriMonthSegment,
    liuri_day_row,
    liuri_provenance,
    month_base,
    resolve_liuri_month,
)
from app.engines.bazi_moment import resolve_natal_moment
from app.engines.bazi_transit import (
    AnnualLuck,
    TransitNatal,
    TransitScan,
    annual_luck_by_year,
    hit_rows,
    natal_projection,
    scan_transit_pillar,
    transit_fired,
    transit_hit_keys,
    transit_ledger,
    transit_narrative,
)
from app.schemas.bazi_liushi import (
    BaziLiushiResult,
    TransitHourCell,
    TransitHourDetail,
    TransitHourHit,
)
from app.schemas.bazi_liuri import AlmanacYiJi
from app.schemas.bazi_transit import TransitFired, TransitTenGod
from app.schemas.common import CalendarType, Gender
from app.schemas.scoring import ScoreValue
from app.solar.true_solar_time import STANDARD_MERIDIAN_CN

HOUR_ZHI = "子丑寅卯辰巳午未申酉戌亥"


def liushi_hour_moments(day: date) -> list[datetime]:
    """一个八字日的十二个采样点：当日 00:00 回拨 1 小时，再每 2 小时一格。

    首格因此落在**前一日 23:00**（决策 2）—— 23:00 起属次日的那一日子时，取当日 00:00
    那格会整日漏掉亥末子初。§9.1 的对拍钉的就是这组坐标，所以它导出、不私有。
    """
    start = datetime(day.year, day.month, day.day) - timedelta(hours=1)
    return [start + timedelta(hours=2 * index) for index in range(12)]


@dataclass(frozen=True)
class _HourRow:
    """一格的全部内部事实：简表与聚焦卡都由下面两个 `_hour_*` 读出，不另算第二遍。"""

    index: int
    zhi: str
    ganzhi: str
    start_clock: str
    end_clock: str
    scan: TransitScan
    score: ScoreValue
    fired: list[TransitFired]
    narrative: str


def _hour_row(
    natal: TransitNatal,
    base: LiuriMonthBase,
    day_keys: list[str],
    index: int,
    moment: datetime,
) -> _HourRow:
    """一根时柱：以命局四柱为体重扫，再与恒定的年/月/日三段一起装四段账。"""
    time_pillar = Solar.fromYmdHms(
        moment.year, moment.month, moment.day, moment.hour, moment.minute, moment.second
    ).getLunar().getTime()
    scan = scan_transit_pillar(
        natal,
        time_pillar.getGanZhi(),
        position="transit_hour",
        label="流时",
        scope="shi",
        dayun_ganzhi=None,
    )
    rows = hit_rows(base.year_keys, base.month_keys, day_keys, transit_hit_keys(scan.judgement))
    return _HourRow(
        index=index,
        zhi=time_pillar.getZhi(),
        ganzhi=time_pillar.getGanZhi(),
        start_clock=time_pillar.getMinHm(),
        end_clock=time_pillar.getMaxHm(),
        scan=scan,
        score=transit_ledger(rows),
        fired=transit_fired(rows),
        narrative=transit_narrative(rows),
    )


def liushi_hours(
    natal: TransitNatal, base: LiuriMonthBase, day_row: LiuriDayRow, day: date
) -> list[_HourRow]:
    """十二格枚举。日段命中取自 `day_row`，不重算 —— 一根日柱下的同一份判定（决策 1）。"""
    day_keys = transit_hit_keys(day_row.scan.judgement)
    return [
        _hour_row(natal, base, day_keys, index, moment)
        for index, moment in enumerate(liushi_hour_moments(day))
    ]


def _hour_fields(row: _HourRow) -> dict[str, object]:
    """简表那八件，聚焦卡与十二格共用一次构造 —— 同一时辰的两组事实不各算一遍。"""
    return {
        "index": row.index,
        "zhi": row.zhi,
        "ganzhi": row.ganzhi,
        "start_clock": row.start_clock,
        "end_clock": row.end_clock,
        "value": row.score.value,
        "tier": row.score.tier,
        "qi_strength": row.scan.pillar.di_shi,
        "hour_hits": [
            TransitHourHit(key=fired.key, label=fired.label, family=fired.family, delta=fired.delta)
            for fired in row.fired
            if fired.key.startswith("shi.")
        ],
    }


def _hour_detail(row: _HourRow) -> TransitHourDetail:
    corpus = ten_god_meaning(row.scan.pillar.shishen_gan)
    return TransitHourDetail(
        **_hour_fields(row),
        pillar=row.scan.pillar,
        ten_god=TransitTenGod(god=corpus.ten_god, meaning=corpus.meaning, source=corpus.source),
        score=row.score,
        fired=row.fired,
        narrative=row.narrative,
        relations=row.scan.relations,
        shensha=row.scan.shensha,
        branch_groups=row.scan.branch_groups,
    )


def _focused_hour(rows: list[_HourRow], focus_hour_zhi: str | None) -> _HourRow | None:
    """聚焦时辰那一支必须在这十二格里。与流日的 `_focused_row` 同一条判序：日定完才轮到它。"""
    if focus_hour_zhi is None:
        return None
    for row in rows:
        if row.zhi == focus_hour_zhi:
            return row
    raise TransitRangeError(
        "liushi_hour_out_of_day",
        f"「{focus_hour_zhi}」不是十二时辰之一，取{HOUR_ZHI}。",
        {"requested": focus_hour_zhi, "supported": HOUR_ZHI},
    )


def _resolve_segment(day: date, luck: dict[int, AnnualLuck]) -> LiuriMonthSegment:
    """段定位失败原样接住、只换机器码（决策 5）：`message` 与 `context` 三件透传。"""
    try:
        return resolve_liuri_month(day, luck)
    except TransitRangeError as error:
        raise TransitRangeError(
            "liushi_date_unsupported", error.message, error.context
        ) from None


def compute_liushi_day(
    *,
    birth_date: date,
    birth_time: time,
    gender: Gender,
    calendar: CalendarType = CalendarType.SOLAR,
    longitude: float = STANDARD_MERIDIAN_CN,
    apply_true_solar_time: bool = True,
    solar_date: date | None = None,
    focus_hour_zhi: str | None = None,
    reference_date: date | None = None,
    name: str | None = None,
) -> BaziLiushiResult:
    """从一个生辰与一个八字日装配十二格（spec §7.4）。

    无 HTTP、无 I/O。排盘两次过同一个校正入口，与 `compute_liuri_matrix` 同一条纪律。
    纯计算量 = 一次年扫描 + 一次月扫描 + 一次日扫描 + 十二次时扫描，比流日矩阵（最多 32
    次日扫描）更轻；不做缓存。
    """
    reference = reference_date or date.today()
    day = solar_date or reference
    chart = compute_bazi_chart(
        birth_date=birth_date,
        birth_time=birth_time,
        calendar=calendar,
        longitude=longitude,
        gender=gender,
        apply_true_solar_time=apply_true_solar_time,
        reference_date=reference,
        name=name,
    )
    moment = resolve_natal_moment(
        birth_date=birth_date,
        birth_time=birth_time,
        calendar=calendar,
        longitude=longitude,
        apply_true_solar_time=apply_true_solar_time,
    )
    luck = annual_luck_by_year(moment.eight_char, gender)
    segment = _resolve_segment(day, luck)
    annual = luck[segment.owner_year]
    natal = natal_projection(chart)
    base = month_base(natal, annual, segment)
    day_row = liuri_day_row(natal, base, day)
    rows = liushi_hours(natal, base, day_row, day)
    focused = _focused_hour(rows, focus_hour_zhi)
    return BaziLiushiResult(
        four_pillars=chart.four_pillars,
        pillars=list(chart.pillars),
        day_master=chart.day_master,
        day_master_element=chart.day_master_element,
        favorable_elements=list(chart.analysis.favorable_elements),
        unfavorable_elements=list(chart.analysis.unfavorable_elements),
        true_solar_time=chart.true_solar_time,
        tst_applied=chart.tst_applied,
        longitude=chart.longitude,
        solar_date=day_row.solar_date,
        weekday=day_row.weekday,
        lunar_day=day_row.lunar_day,
        day_ganzhi=day_row.ganzhi,
        year=segment.owner_year,
        year_ganzhi=annual.ganzhi,
        year_age=annual.age,
        dayun_index=annual.dayun_index,
        dayun_ganzhi=annual.dayun_ganzhi,
        month_index=segment.index,
        month_in_chinese=segment.month_in_chinese,
        month_ganzhi=segment.month_ganzhi,
        month_start_solar=segment.start.isoformat(),
        month_end_solar=segment.end.isoformat(),
        day_score=day_row.score,
        day_fired=day_row.fired,
        day_almanac=AlmanacYiJi(yi=day_row.yi, ji=day_row.ji),
        hours=[TransitHourCell(**_hour_fields(row)) for row in rows],
        focused=None if focused is None else _hour_detail(focused),
        provenance=liuri_provenance(reference),
    )
