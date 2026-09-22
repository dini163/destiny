"""流日引擎：月段定位、逐日三段账本、日柱口径。

期望值全部来自 2026-09-22 的实机测量（spec §2.4、§2.5 与本计划"实测基准"一节）。
"""

from datetime import date, time, timedelta
from functools import cache

import pytest
from lunar_python import Solar

from app.core.errors import TransitRangeError
from app.engines.bazi import compute_bazi_chart
from app.engines.bazi_liuri import (
    liuri_days,
    month_base,
    resolve_liuri_month,
)
from app.engines.bazi_moment import resolve_natal_moment
from app.engines.bazi_transit import annual_luck_by_year, natal_projection
from app.schemas.common import CalendarType, Gender

_BIRTH = (date(1988, 2, 15), time(23, 30))
_NATAL_KWARGS: dict[str, object] = {
    "birth_date": _BIRTH[0],
    "birth_time": _BIRTH[1],
    "gender": Gender.MALE,
    "longitude": 104.07,
    "calendar": CalendarType.SOLAR,
    "apply_true_solar_time": True,
}


@cache
def _luck() -> dict[int, object]:
    moment = resolve_natal_moment(
        birth_date=_BIRTH[0],
        birth_time=_BIRTH[1],
        calendar=CalendarType.SOLAR,
        longitude=104.07,
        apply_true_solar_time=True,
    )
    return annual_luck_by_year(moment.eight_char, Gender.MALE)


def _fixture(anchor: date):
    """锚点 → (命局投影, 段, 段所属流年)，三个测试都要这一套。"""
    chart = compute_bazi_chart(reference_date=anchor, **_NATAL_KWARGS)
    natal = natal_projection(chart)
    luck = _luck()
    segment = resolve_liuri_month(anchor, luck)
    return natal, segment, luck[segment.owner_year]


def test_an_anchor_after_li_chun_resolves_inside_that_years_boundary_list() -> None:
    _, segment, annual = _fixture(date(2028, 12, 20))
    assert (segment.owner_year, segment.index) == (2028, 10)
    assert (segment.month_ganzhi, segment.month_in_chinese) == ("甲子", "冬")
    assert (segment.start, segment.end) == (date(2028, 12, 6), date(2029, 1, 4))
    assert annual.ganzhi == "戊申"


def test_an_anchor_before_li_chun_belongs_to_the_previous_liunian() -> None:
    """立春本身是"节"，所以 2028-01-15 属 2027 年的尾段，不是 2028 年任何一段（spec §2.4）。"""
    _, segment, annual = _fixture(date(2028, 1, 15))
    assert (segment.owner_year, segment.index) == (2027, 11)
    assert (segment.month_ganzhi, segment.month_in_chinese) == ("癸丑", "腊")
    assert (segment.start, segment.end) == (date(2028, 1, 6), date(2028, 2, 3))
    assert (annual.ganzhi, annual.age, annual.dayun_index, annual.dayun_ganzhi) == (
        "丁未",
        40,
        4,
        "戊午",
    )


def test_an_anchor_outside_the_luck_window_is_a_domain_error() -> None:
    with pytest.raises(TransitRangeError) as excinfo:
        resolve_liuri_month(date(1980, 6, 1), _luck())
    assert excinfo.value.code == "liuri_month_unsupported"
    assert excinfo.value.context == {
        "requested": "1980-06-01",
        "supported_from": 1988,
        "supported_to": 2083,
    }


def test_the_segment_days_are_contiguous_and_bounded_by_the_jieqi_edges() -> None:
    natal, segment, annual = _fixture(date(2028, 1, 15))
    days = liuri_days(natal, month_base(natal, annual, segment), segment)
    assert [row.solar_date for row in days[:3]] == ["2028-01-06", "2028-01-07", "2028-01-08"]
    assert days[0].solar_date == segment.start.isoformat()
    assert days[-1].solar_date == segment.end.isoformat()
    assert len(days) == 29


def test_the_weekday_starts_at_monday_and_rolls_seven_by_seven() -> None:
    """前导空格数由这个数决定，所以它必须是周一为 0（`Solar.getWeek()` 以 0 为周日）。"""
    natal, segment, annual = _fixture(date(2028, 1, 15))
    days = liuri_days(natal, month_base(natal, annual, segment), segment)
    assert days[0].weekday == 3
    assert [row.weekday for row in days[1:9]] == [4, 5, 6, 0, 1, 2, 3, 4]


def test_a_leap_month_day_carries_the_leap_prefix_from_the_library() -> None:
    """2028 有闰五月（29 天落在其中），农历日串由库自己带"闰"，引擎不加分支。"""
    natal, segment, annual = _fixture(date(2028, 6, 24))
    days = liuri_days(natal, month_base(natal, annual, segment), segment)
    assert [row.lunar_day for row in days if row.solar_date == "2028-06-24"] == ["闰五初二"]


def test_the_flat_day_pillar_matches_eight_char_for_365_days() -> None:
    """矩阵一格一天，格与格之间不存在"这格算今天还是明天"的分支，所以用平柱。

    这一条同时是口径的执行件：谁把 `getDayInGanZhi()` 换成 `…Exact()`（那是切片 4 才要
    回答的 23:00 归属问题），这里当场红（spec §2.2）。
    """
    for offset in range(365):
        day = date(2028, 1, 1) + timedelta(days=offset)
        expected = Solar.fromYmd(day.year, day.month, day.day).getLunar().getDayInGanZhi()
        for hour in (0, 12):
            eight_char = Solar.fromYmdHms(day.year, day.month, day.day, hour, 0, 0).getLunar().getEightChar()
            assert eight_char.getDayGan() + eight_char.getDayZhi() == expected, (day, hour)


_GUILIU_GOLDEN: tuple[tuple[str, str, float, str, int], ...] = (
    ("2028-01-06", "庚寅", 57.0, "平", 4), ("2028-01-07", "辛卯", 51.0, "平", 6),
    ("2028-01-08", "壬辰", 57.0, "平", 4), ("2028-01-09", "癸巳", 22.0, "滞", 7),
    ("2028-01-10", "甲午", 16.0, "滞", 6), ("2028-01-11", "乙未", 66.0, "顺", 6),
    ("2028-01-12", "丙申", 48.0, "平", 7), ("2028-01-13", "丁酉", 61.0, "平", 5),
    ("2028-01-14", "戊戌", 73.0, "顺", 4), ("2028-01-15", "己亥", 60.0, "平", 7),
    ("2028-01-16", "庚子", 50.0, "平", 6), ("2028-01-17", "辛丑", 75.0, "顺", 6),
    ("2028-01-18", "壬寅", 37.0, "滞", 4), ("2028-01-19", "癸卯", 31.0, "滞", 6),
    ("2028-01-20", "甲辰", 52.0, "平", 5), ("2028-01-21", "乙巳", 35.0, "滞", 7),
    ("2028-01-22", "丙午", 33.0, "滞", 5), ("2028-01-23", "丁未", 65.0, "顺", 6),
    ("2028-01-24", "戊申", 64.0, "平", 6), ("2028-01-25", "己酉", 77.0, "顺", 4),
    ("2028-01-26", "庚戌", 73.0, "顺", 4), ("2028-01-27", "辛亥", 60.0, "平", 7),
    ("2028-01-28", "壬子", 35.0, "滞", 5), ("2028-01-29", "癸丑", 55.0, "平", 6),
    ("2028-01-30", "甲寅", 27.0, "滞", 6), ("2028-01-31", "乙卯", 36.0, "滞", 7),
    ("2028-02-01", "丙辰", 61.0, "平", 5), ("2028-02-02", "丁巳", 34.0, "滞", 7),
    ("2028-02-03", "戊午", 49.0, "平", 4),
)


def test_a_whole_segment_pins_every_day_value() -> None:
    """29 行一起钉，比抽三天更能压住"月界错一天"。"""
    natal, segment, annual = _fixture(date(2028, 1, 15))
    days = liuri_days(natal, month_base(natal, annual, segment), segment)
    assert [
        (row.solar_date, row.ganzhi, row.score.value, row.score.tier,
         sum(1 for hit in row.fired if hit.key.startswith("ri.")))
        for row in days
    ] == list(_GUILIU_GOLDEN)


def test_the_extreme_days_of_the_golden_segment() -> None:
    """同一段里 16 与 77 分差 61：矩阵要的对比度成立，日粒度不另立阈值（spec §2.5）。"""
    natal, segment, annual = _fixture(date(2028, 1, 15))
    rows = {
        row.solar_date: row for row in liuri_days(natal, month_base(natal, annual, segment), segment)
    }
    assert [(hit.key, hit.label, hit.family, hit.delta) for hit in rows["2028-01-10"].fired if hit.key.startswith("ri.")] == [
        ("ri.yongshen.gan_unfavourable", "运干入忌（流日）", "yongshen", -10.0),
        ("ri.yongshen.zhi_unfavourable", "运支主气入忌（流日）", "yongshen", -8.0),
        ("ri.palace.chong_day", "冲本身宫（流日）", "palace", -8.0),
        ("ri.heyue.anhe_unfavourable", "半合忌（流日）", "heyue", -3.0),
        ("ri.ganzhi.chong_day_master", "运干冲日主（流日）", "ganzhi", -5.0),
        ("ri.fuyin.fanyin", "反吟（流日）", "fuyin", -8.0),
    ]
    assert [(hit.key, hit.delta) for hit in rows["2028-01-25"].fired if hit.key.startswith("ri.")] == [
        ("ri.yongshen.gan_favourable", 10.0),
        ("ri.yongshen.zhi_favourable", 8.0),
        ("ri.dishi.prosperous", 7.0),
        ("ri.shensha.yangren", -6.0),
    ]


def test_a_clamped_day_records_its_clamp_as_its_own_row() -> None:
    """甲子月段基准 28，最凶的一天原始和 −14：截断是账本自己的一行，不是偷偷丢掉。"""
    natal, segment, annual = _fixture(date(2028, 12, 20))
    rows = {row.solar_date: row for row in liuri_days(natal, month_base(natal, annual, segment), segment)}
    worst = rows["2029-01-04"]
    assert worst.score.value == 0.0 and worst.score.tier == "滞"
    assert worst.score.factors[-1].rule == "score.clamped"
    assert worst.score.factors[-1].delta == 14.0
    assert sum(factor.delta for factor in worst.score.factors) == 0.0
    assert [
        (row.solar_date, row.score.value)
        for row in sorted(rows.values(), key=lambda item: item.solar_date)
        if row.score.factors[-1].rule == "score.clamped"
    ] == [("2028-12-23", 0.0), ("2029-01-03", 0.0), ("2029-01-04", 0.0)]


def test_a_hostile_segment_can_be_all_celldays_weak() -> None:
    """段基准决定中位：甲子月 30 天里 0 顺 / 3 平 / 27 滞（spec §11.2，本轮不为此另立尺）。"""
    natal, segment, annual = _fixture(date(2028, 12, 20))
    days = liuri_days(natal, month_base(natal, annual, segment), segment)
    tiers = {tier: sum(1 for row in days if row.score.tier == tier) for tier in ("顺", "平", "滞")}
    assert tiers == {"顺": 0, "平": 3, "滞": 27}


def test_the_month_baseline_equals_the_transit_page_month_card() -> None:
    """免费的跨切片红线：矩阵的段基准 == 岁运页同段月卡，逐字段逐字。

    两侧各自跑一次 `compute_bazi_chart`，没有共享内存可漂，所以这条真在比算法。
    """
    from app.engines.bazi_transit import compute_transit

    transit = compute_transit(
        birth_date=_BIRTH[0], birth_time=_BIRTH[1], gender=Gender.MALE, longitude=104.07,
        start_year=2027, end_year=2027, focus_year=2027, reference_date=date(2028, 1, 15),
    )
    card = transit.years[0].months[11]
    natal, segment, annual = _fixture(date(2028, 1, 15))
    base = month_base(natal, annual, segment)
    assert (base.score.value, base.score.tier) == (card.score.value, card.score.tier)
    assert [(f.rule, f.label, f.delta) for f in base.score.factors] == [
        (f.rule, f.label, f.delta) for f in card.score.factors
    ]
    assert [(f.key, f.label, f.delta) for f in base.fired] == [
        (f.key, f.label, f.delta) for f in card.fired
    ]


def test_a_day_ledger_reuses_the_year_rows_verbatim_and_appends_its_own() -> None:
    """年段行在年卡、月卡、日账本里是同一批字（无前缀），改了当场红（§9.2 第 2 条）。"""
    natal, segment, annual = _fixture(date(2028, 1, 15))
    base = month_base(natal, annual, segment)
    days = liuri_days(natal, base, segment)
    year_rows = [hit.key for hit in base.fired if not hit.key.startswith("yue.")]
    assert year_rows == [hit.key for hit in days[0].fired[: len(year_rows)]]
    for row in days:
        rules = [factor.rule for factor in row.score.factors]
        assert rules[0] == "transit.base"
        # 基准行之外，账本行与 fired 逐字同源、同序
        assert rules[1:] == [hit.key for hit in row.fired]
        # 头几条就是年段那一批，无前缀，与月卡/年卡同一份字
        assert rules[1 : 1 + len(year_rows)] == year_rows
        assert sum(factor.delta for factor in row.score.factors) == row.score.value
