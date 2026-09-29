"""流日（全月逐日）引擎：月段定位、段基准、逐日三段账本与整页总装。

本模块**不重复**任何判定：命中过滤、账本装配、合成柱、月界全部跨模块取
`bazi_transit` 的那一份（spec §5.4）。依赖方向单向 —— `bazi_liuri → bazi_transit`；
切片 2 已经因为反向 import 撞过一次环，这条不再商量。

它也不自己算月：段界来自 `jieqi_boundaries`，月柱与月名来自 lunar-python 的 `LiuYue`，
日柱来自 `Solar → Lunar.getDayInGanZhi()`（平柱，spec §2.2）。本模块只负责"哪一天属
哪一段"与"这一天的账怎么装"，历法事实一个都不自造。

四个内核心（`LiuriMonthSegment` / `LiuriMonthBase` / `LiuriDayRow` / `liuri_day_row`）
与 `liuri_provenance` 是模块级的：切片 4 的 `bazi_liushi` 要拿"日所在的段、段的基准、
那一日的三段账本与十二长生、以及那 12 行溯源"，而跨模块传私有名等于把切片 3 §5.4 的
纪律作废。
"""

from dataclasses import dataclass
from datetime import date, time, timedelta

from lunar_python import Solar

from app.content import (
    ALMANAC_CONTENT_SOURCES,
    ALMANAC_CONTENT_VERSION,
    CONTENT_SOURCES,
    CONTENT_VERSION,
    TRANSIT_CONTENT_SOURCES,
)
from app.content.bazi_shishen import ten_god_meaning
from app.core.errors import TransitRangeError
from app.engines.bazi import compute_bazi_chart
from app.engines.bazi_moment import resolve_natal_moment
from app.engines.bazi_transit import (
    AnnualLuck,
    TransitNatal,
    TransitScan,
    annual_luck_by_year,
    hit_rows,
    jieqi_boundaries,
    natal_projection,
    scan_transit_pillar,
    transit_fired,
    transit_hit_keys,
    transit_ledger,
    transit_narrative,
    year_scan,
)
from app.schemas.bazi_breakdown import Provenance, ProvenanceTable
from app.schemas.bazi_liuri import (
    AlmanacYiJi,
    BaziLiuriResult,
    TransitDayCell,
    TransitDayDetail,
    TransitDayHit,
)
from app.schemas.bazi_transit import TransitFired, TransitTenGod
from app.schemas.common import CalendarType, Gender
from app.schemas.scoring import ScoreValue
from app.solar.true_solar_time import STANDARD_MERIDIAN_CN


@dataclass(frozen=True)
class LiuriMonthSegment:
    """一个节气月段：起止、月柱，与它所从出的那个流年对象。

    `owner_year` 是段所属的**流年**年，段尾跨年时它与 `end` 的公历年不同（实测
    2027 年壬子月 = 2027-12-07~2028-01-05）。整段的年段命中以它为准（spec §2.4）。
    `liunian` 留着是为了让 `month_base` 能按 `index` 回头拿那一根的 `LiuYue` 上下文，
    而不必把整年十二段都扫一遍。
    """

    owner_year: int
    index: int
    month_ganzhi: str
    month_in_chinese: str
    start: date
    end: date
    liunian: object  # lunar_python.LiunianYear


def resolve_liuri_month(anchor: date, luck: dict[int, AnnualLuck]) -> LiuriMonthSegment:
    """把锚点日定位到一个节气月段 —— 探两次月界，不是一次。

    `jieqi_boundaries(y)` 的第 0 段起于本年立春，所以 `anchor ≥ 立春` 必落在
    `anchor.year` 的十二段里；否则它属上一年的尾段。两探都落空即那一年根本没有摊出来的
    流年（早于出生年、或超出 `Yun.getDaYun()` 覆盖），矩阵无从谈起，抛域错误而不是
    给一个"大概这个月"（spec §7.2）。
    """
    for probe_year in (anchor.year, anchor.year - 1):
        annual = luck.get(probe_year)
        if annual is None:
            continue
        for index, (start, end) in enumerate(jieqi_boundaries(probe_year)):
            if start <= anchor <= end:
                liu_yue = annual.liunian.getLiuYue()[index]
                return LiuriMonthSegment(
                    owner_year=probe_year,
                    index=index,
                    month_ganzhi=liu_yue.getGanZhi(),
                    month_in_chinese=liu_yue.getMonthInChinese(),
                    start=start,
                    end=end,
                    liunian=annual.liunian,
                )
    raise TransitRangeError(
        "liuri_month_unsupported",
        f"{anchor.isoformat()} 所在的节气月推不出：本命盘可推年份 "
        f"{min(luck)}—{max(luck)}。",
        {
            "requested": anchor.isoformat(),
            "supported_from": min(luck),
            "supported_to": max(luck),
        },
    )


@dataclass(frozen=True)
class LiuriMonthBase:
    """整段恒定的那半份账：流年命中键、月段命中键，与段基准的两段账本。

    一根段恒属一个流年（立春本身就是"节"，段界与年界重合），所以年段与月段在段内逐日
    不变 —— 只算这一次，30 天共用（spec §2.4）。段基准与岁运页同段月卡逐字相等，那条
    一致性红线见 `test_the_month_baseline_equals_the_transit_page_month_card`。
    """

    year_keys: list[str]
    month_keys: list[str]
    score: ScoreValue
    fired: list[TransitFired]


def month_base(
    natal: TransitNatal, annual: AnnualLuck, segment: LiuriMonthSegment
) -> LiuriMonthBase:
    """段基准 = 流年那一柱的命中 + 该月那一柱的命中，两段账（与切片 2 的月卡同一装配）。"""
    year_keys = transit_hit_keys(year_scan(natal, annual).judgement)
    month_keys = transit_hit_keys(
        scan_transit_pillar(
            natal,
            segment.month_ganzhi,
            position="transit_month",
            label="流月",
            scope="yue",
            dayun_ganzhi=None,
        ).judgement
    )
    rows = hit_rows(year_keys, month_keys)
    return LiuriMonthBase(
        year_keys=year_keys,
        month_keys=month_keys,
        score=transit_ledger(rows),
        fired=transit_fired(rows),
    )


@dataclass(frozen=True)
class LiuriDayRow:
    """一格的全部内部事实：简表与聚焦卡都由 `_cell_fields` 从这一份读，不另算第二遍。

    `scan` 带着合成柱与三张已按 `extra0` 筛过的明细 —— 聚焦日卡要的就是这一份，
    简表格里则只取 `score` 的 `value`/`tier` 与 `fired` 的 `ri.` 四条（spec §2.5：
    判语全文不进简表，29 份重复是体积的唯一来源）。
    """

    solar_date: str
    weekday: int
    lunar_day: str
    ganzhi: str
    scan: TransitScan
    score: ScoreValue
    fired: list[TransitFired]
    narrative: str
    yi: list[str]
    ji: list[str]


def liuri_days(
    natal: TransitNatal, base: LiuriMonthBase, segment: LiuriMonthSegment
) -> list[LiuriDayRow]:
    """段内逐日 +1 枚举（枚举的是段，不是公历月，所以没有"月末"分支）。"""
    return [
        liuri_day_row(natal, base, day)
        for day in _enumerate_days(segment.start, segment.end)
    ]


def _enumerate_days(start: date, end: date) -> list[date]:
    return [start + timedelta(days=offset) for offset in range((end - start).days + 1)]


def liuri_day_row(natal: TransitNatal, base: LiuriMonthBase, day: date) -> LiuriDayRow:
    solar = Solar.fromYmd(day.year, day.month, day.day)
    lunar = solar.getLunar()
    ganzhi = lunar.getDayInGanZhi()
    scan = scan_transit_pillar(
        natal,
        ganzhi,
        position="transit_day",
        label="流日",
        scope="ri",
        dayun_ganzhi=None,
    )
    rows = hit_rows(base.year_keys, base.month_keys, transit_hit_keys(scan.judgement))
    return LiuriDayRow(
        solar_date=day.isoformat(),
        weekday=(solar.getWeek() + 6) % 7,
        lunar_day=f"{lunar.getMonthInChinese()}{lunar.getDayInChinese()}",
        ganzhi=ganzhi,
        scan=scan,
        score=transit_ledger(rows),
        fired=transit_fired(rows),
        narrative=transit_narrative(rows),
        yi=list(lunar.getDayYi()),
        ji=list(lunar.getDayJi()),
    )


# ---------------------------------------------------------------- 总装（spec §7.3 / §7.4）
def _cell_fields(row: LiuriDayRow) -> dict[str, object]:
    """简表那六件，聚焦卡与格子共用一次构造 —— 同一天的两组事实不各算一遍。"""
    return {
        "solar_date": row.solar_date,
        "weekday": row.weekday,
        "lunar_day": row.lunar_day,
        "ganzhi": row.ganzhi,
        "value": row.score.value,
        "tier": row.score.tier,
        "day_hits": [
            TransitDayHit(key=fired.key, label=fired.label, family=fired.family, delta=fired.delta)
            for fired in row.fired
            if fired.key.startswith("ri.")
        ],
        "almanac": AlmanacYiJi(yi=row.yi, ji=row.ji),
    }


def _day_detail(row: LiuriDayRow) -> TransitDayDetail:
    corpus = ten_god_meaning(row.scan.pillar.shishen_gan)
    return TransitDayDetail(
        **_cell_fields(row),
        pillar=row.scan.pillar,
        ten_god=TransitTenGod(god=corpus.ten_god, meaning=corpus.meaning, source=corpus.source),
        score=row.score,
        fired=row.fired,
        narrative=row.narrative,
        relations=row.scan.relations,
        shensha=row.scan.shensha,
        branch_groups=row.scan.branch_groups,
    )


def _focused_row(
    rows: list[LiuriDayRow], focus_date: date | None, segment: LiuriMonthSegment
) -> LiuriDayRow | None:
    """聚焦日必须落在解析出的段内。判序即依赖序：段已经定完，才轮到它（spec §7.2）。"""
    if focus_date is None:
        return None
    target = focus_date.isoformat()
    for row in rows:
        if row.solar_date == target:
            return row
    raise TransitRangeError(
        "liuri_focus_out_of_month",
        f"{target} 不在 {segment.start.isoformat()} ~ {segment.end.isoformat()} 这一段里。",
        {
            "focus_date": target,
            "month_start_solar": segment.start.isoformat(),
            "month_end_solar": segment.end.isoformat(),
        },
    )


def liuri_provenance(reference: date) -> Provenance:
    """溯源那 12 行：主命盘 9 + 岁运 2 + 历注 1（切片 3 spec §7.4 定的是「三份清单相接」
    这个口径，行数随清单长度走 —— 主命盘那张清单刚收进 `bazi_plain`，这里就跟着到 12）。

    条数复测：`cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "from
    app.content import CONTENT_SOURCES as c, TRANSIT_CONTENT_SOURCES as t,
    ALMANAC_CONTENT_SOURCES as a; print(len(c) + len(t) + len(a))"` → 12。

    提到模块级是流时那一轮的事：一页 = 一日十二时，用的是同一批表、同一个版本口径，
    而再复制一份 `tables` 清单等于给"多一行是谎称引用、少一行是不认账"这条纪律开出
    第二个执行点。
    """
    return Provenance(
        reference_date=reference.isoformat(),
        engine="lunar-python",
        tables=[
            *(
                ProvenanceTable(name=module, version=CONTENT_VERSION, source=source)
                for module, source in (*CONTENT_SOURCES, *TRANSIT_CONTENT_SOURCES)
            ),
            *(
                ProvenanceTable(name=module, version=ALMANAC_CONTENT_VERSION, source=source)
                for module, source in ALMANAC_CONTENT_SOURCES
            ),
        ],
    )


def compute_liuri_matrix(
    *,
    birth_date: date,
    birth_time: time,
    gender: Gender,
    calendar: CalendarType = CalendarType.SOLAR,
    longitude: float = STANDARD_MERIDIAN_CN,
    apply_true_solar_time: bool = True,
    anchor_date: date | None = None,
    focus_date: date | None = None,
    reference_date: date | None = None,
    name: str | None = None,
) -> BaziLiuriResult:
    """从生辰与锚点日装配一整段节气月的逐日矩阵（spec §7.4）。

    无 HTTP、无 I/O。排盘走两次同一个入口（`compute_bazi_chart` 出命局摘要与喜忌，
    `resolve_natal_moment` 出 `EightChar` 供摊平流年），两次过同一个校正函数 —— 与
    `compute_transit` 同一条纪律，不会出现"命盘用 23:30、矩阵用 23:26"的两个口径。

    整页纯计算量 = 一次年扫描 + 一次月扫描 + 最多 32 次日扫描，都落在切片 2 每次请求
    已经跑过十几遍的那套 `derive_*` 上；不做缓存（spec §7.4）。
    """
    reference = reference_date or date.today()
    anchor = anchor_date or reference
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
    segment = resolve_liuri_month(anchor, luck)
    annual = luck[segment.owner_year]
    natal = natal_projection(chart)
    base = month_base(natal, annual, segment)
    rows = liuri_days(natal, base, segment)
    focused = _focused_row(rows, focus_date, segment)
    return BaziLiuriResult(
        four_pillars=chart.four_pillars,
        pillars=list(chart.pillars),
        day_master=chart.day_master,
        day_master_element=chart.day_master_element,
        favorable_elements=list(chart.analysis.favorable_elements),
        unfavorable_elements=list(chart.analysis.unfavorable_elements),
        true_solar_time=chart.true_solar_time,
        tst_applied=chart.tst_applied,
        longitude=chart.longitude,
        anchor_date=anchor.isoformat(),
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
        month_score=base.score,
        month_fired=base.fired,
        days=[TransitDayCell(**_cell_fields(row)) for row in rows],
        focused=None if focused is None else _day_detail(focused),
        provenance=liuri_provenance(reference),
    )
