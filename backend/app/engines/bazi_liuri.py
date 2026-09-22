"""流日（全月逐日）引擎：月段定位、段基准、逐日三段账本。

本模块**不重复**任何判定：命中过滤、账本装配、合成柱、月界全部跨模块取
`bazi_transit` 的那一份（spec §5.4）。依赖方向单向 —— `bazi_liuri → bazi_transit`；
切片 2 已经因为反向 import 撞过一次环，这条不再商量。

它也不自己算月：段界来自 `jieqi_boundaries`，月柱与月名来自 lunar-python 的 `LiuYue`，
日柱来自 `Solar → Lunar.getDayInGanZhi()`（平柱，spec §2.2）。本模块只负责"哪一天属
哪一段"与"这一天的账怎么装"，历法事实一个都不自造。
"""

from dataclasses import dataclass
from datetime import date, timedelta

from lunar_python import Solar

from app.core.errors import TransitRangeError
from app.engines.bazi_transit import (
    AnnualLuck,
    TransitNatal,
    TransitScan,
    hit_rows,
    jieqi_boundaries,
    scan_transit_pillar,
    transit_fired,
    transit_hit_keys,
    transit_ledger,
    transit_narrative,
    year_scan,
)
from app.schemas.bazi_transit import TransitFired
from app.schemas.scoring import ScoreValue


@dataclass(frozen=True)
class _MonthSegment:
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


def resolve_liuri_month(anchor: date, luck: dict[int, AnnualLuck]) -> _MonthSegment:
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
                return _MonthSegment(
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
class _MonthBase:
    """整段恒定的那半份账：流年命中键、月段命中键，与段基准的两段账本。

    一根段恒属一个流年（立春本身就是"节"，段界与年界重合），所以年段与月段在段内逐日
    不变 —— 只算这一次，30 天共用（spec §2.4）。段基准与岁运页同段月卡逐字相等，那条
    一致性红线见 `test_the_month_baseline_equals_the_transit_page_month_card`。
    """

    year_keys: list[str]
    month_keys: list[str]
    score: ScoreValue
    fired: list[TransitFired]


def month_base(natal: TransitNatal, annual: AnnualLuck, segment: _MonthSegment) -> _MonthBase:
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
    return _MonthBase(
        year_keys=year_keys,
        month_keys=month_keys,
        score=transit_ledger(rows),
        fired=transit_fired(rows),
    )


@dataclass(frozen=True)
class _DayRow:
    """一格的全部内部事实。schema 装配在 T5，本模块不依赖它。

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
    natal: TransitNatal, base: _MonthBase, segment: _MonthSegment
) -> list[_DayRow]:
    """段内逐日 +1 枚举（枚举的是段，不是公历月，所以没有"月末"分支）。"""
    return [
        _day_row(natal, base, day)
        for day in _enumerate_days(segment.start, segment.end)
    ]


def _enumerate_days(start: date, end: date) -> list[date]:
    return [start + timedelta(days=offset) for offset in range((end - start).days + 1)]


def _day_row(natal: TransitNatal, base: _MonthBase, day: date) -> _DayRow:
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
    return _DayRow(
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
