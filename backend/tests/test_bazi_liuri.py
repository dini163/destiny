"""流日引擎：月段定位、逐日三段账本、日柱口径。

期望值全部来自 2026-09-22 的实机测量（spec §2.4、§2.5 与本计划"实测基准"一节）。
"""

from datetime import date, time, timedelta
from functools import cache

import pytest
from lunar_python import Solar

from app.content import CONTENT_VERSION
from app.content.bazi_transit_plain import (
    BAZI_LIURI_DAYS_FRAME,
    BAZI_LIURI_FOCUS_FRAME,
    BAZI_LIURI_MONTH_FRAME,
    BAZI_TRANSIT_PLAIN_SOURCE,
    BAZI_TRANSIT_TITLES,
    BAZI_TRANSIT_TONE_KEYS,
)
from app.core.errors import TransitRangeError
from app.engines.bazi import compute_bazi_chart
from app.engines.bazi_liuri import (
    compute_liuri_matrix,
    liuri_days,
    month_base,
    resolve_liuri_month,
)
from app.engines.bazi_moment import resolve_natal_moment
from app.engines.bazi_transit import annual_luck_by_year, natal_projection
from app.engines.plain_compose import num, reading
from app.engines.plain_corpora import BAZI_TRANSIT
from app.schemas.bazi_liuri import BaziLiuriResult
from app.schemas.common import CalendarType, Gender
from tests.plain_wording import (
    FORBIDDEN,
    LEDGER_WORDS,
    PREDICTION_FORBIDDEN,
    TIER_WORDS,
    WU_DECISION_FORBIDDEN,
    advice_hits,
    slot_value,
)

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


@cache
def _matrix() -> BaziLiuriResult:
    """缺省请求：只给参考日，段自动落 2028 年小寒月（癸丑，2028-01-06 → 2028-02-03，29 格）。"""
    return compute_liuri_matrix(**_NATAL_KWARGS, reference_date=date(2028, 1, 15))


@cache
def _matrix_focused() -> BaziLiuriResult:
    return compute_liuri_matrix(
        **_NATAL_KWARGS,
        anchor_date=date(2028, 1, 15),
        focus_date=date(2028, 1, 15),
        reference_date=date(2028, 1, 15),
    )


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


def test_the_summary_mirrors_the_transit_result_field_for_field() -> None:
    """摘要九件不抽公共基类（spec §7.3 的取舍），漂移由这条字段级断言拦。"""
    from app.schemas.bazi_liuri import BaziLiuriResult
    from app.schemas.bazi_transit import BaziTransitResult

    shared = [
        "four_pillars", "pillars", "day_master", "day_master_element",
        "favorable_elements", "unfavorable_elements", "true_solar_time", "tst_applied", "longitude",
    ]
    assert [
        (name, BaziLiuriResult.model_fields[name].annotation) for name in shared
    ] == [
        (name, BaziTransitResult.model_fields[name].annotation) for name in shared
    ]


def test_the_matrix_echoes_the_reference_date_segment_by_default() -> None:
    result = compute_liuri_matrix(**_NATAL_KWARGS, reference_date=date(2028, 1, 15))
    assert (result.anchor_date, result.month_ganzhi, result.year) == ("2028-01-15", "癸丑", 2027)
    assert (result.month_start_solar, result.month_end_solar) == ("2028-01-06", "2028-02-03")
    assert (result.year_ganzhi, result.year_age) == ("丁未", 40)
    assert (result.dayun_index, result.dayun_ganzhi) == (4, "戊午")
    assert (result.month_index, result.month_in_chinese) == (11, "腊")
    assert (result.month_score.value, result.month_score.tier) == (58.0, "平")
    assert len(result.month_fired) == 13 and len(result.days) == 29
    assert result.focused is None


def test_a_cell_value_and_tier_come_from_its_own_ledger() -> None:
    """格子上的那两个数取自那一段账本、四件命中取自日段命中，全部实测量（spec §2.5 表）。"""
    result = compute_liuri_matrix(**_NATAL_KWARGS, anchor_date=date(2028, 1, 15), reference_date=date(2028, 1, 15))
    cell = next(item for item in result.days if item.solar_date == "2028-01-25")
    assert (cell.value, cell.tier) == (77.0, "顺")
    assert [(hit.key, hit.label, hit.family, hit.delta) for hit in cell.day_hits] == [
        ("ri.yongshen.gan_favourable", "运干入喜用（流日）", "yongshen", 10.0),
        ("ri.yongshen.zhi_favourable", "运支主气入喜用（流日）", "yongshen", 8.0),
        ("ri.dishi.prosperous", "日主临官帝旺（流日）", "dishi", 7.0),
        ("ri.shensha.yangren", "羊刃（流日）", "shensha", -6.0),
    ]


def test_a_focused_day_and_its_matrix_cell_are_the_same_facts() -> None:
    """§9.2 第 3 条：比的是**两次独立请求**，不是同一份内存里的两个视图。

    一次不带 `focus_date`、一次带，于是这条断言同时钉住两件事：格子与明细同字，以及
    "请求与否聚焦日"不改变任何一格的数字。
    """
    plain = compute_liuri_matrix(
        **_NATAL_KWARGS, anchor_date=date(2028, 1, 15), reference_date=date(2028, 1, 15)
    )
    result = compute_liuri_matrix(
        **_NATAL_KWARGS, anchor_date=date(2028, 1, 15), focus_date=date(2028, 1, 25),
        reference_date=date(2028, 1, 15),
    )
    focused = result.focused
    assert focused is not None
    cell = next(item for item in plain.days if item.solar_date == "2028-01-25")
    assert [(hit.key, hit.label, hit.family, hit.delta) for hit in cell.day_hits] == [
        (fired.key, fired.label, fired.family, fired.delta)
        for fired in focused.fired
        if fired.key.startswith("ri.")
    ]
    assert (focused.value, focused.tier, focused.ganzhi, focused.lunar_day) == (
        cell.value, cell.tier, cell.ganzhi, cell.lunar_day
    )
    assert focused.almanac == cell.almanac


def test_the_almanac_is_passed_through_without_invention() -> None:
    """宜忌逐字取自库；`馀事勿取` 是库自己写的，服务端不代填也不挪位置（决策 6）。

    取的是段内最疏的一天（甲辰，宜只有两条），所以"库里写了几条就是几条"看得见。
    """
    result = compute_liuri_matrix(**_NATAL_KWARGS, anchor_date=date(2028, 1, 15), reference_date=date(2028, 1, 15))
    by_date = {cell.solar_date: cell for cell in result.days}
    assert by_date["2028-01-20"].almanac.yi == ["平治道涂", "馀事勿取"]
    assert by_date["2028-01-20"].almanac.ji == [
        "开光", "嫁娶", "开仓", "出货财", "造船", "安葬", "探病"
    ]
    assert len(by_date["2028-01-15"].almanac.yi) == 17
    assert len(by_date["2028-01-15"].almanac.ji) == 5
    for cell in result.days:
        assert all(item and item.strip() for item in (*cell.almanac.yi, *cell.almanac.ji))
        assert len(set(cell.almanac.yi)) == len(cell.almanac.yi)


def test_the_provenance_carries_thirteen_tables_and_the_library_version() -> None:
    """历注那行的版本取自依赖元数据，不是本仓语料的 `CONTENT_VERSION`（spec §7.5）。

    十三行表名逐字列在这里，不照引擎那样 `*` 展开四份常量（J-T5 评审轮 F-01 的账）：只数张数的钉
    管不住**身份**——把白话那份展开换成 `*ALMANAC_CONTENT_SOURCES,` 之后张数仍是 13，`bazi_transit_plain`
    被声称 0 次而 `almanac_yiji` 被声称 2 次，`{table.name: table}` 后者覆盖前者，连版本断言都照绿，
    三点选测全绿（评审席实测 `3 passed, 51 deselected`）。同一类盲区在岁运页由 `tests/test_bazi_transit.py`
    的十二行逐字名单管着，本行与流时那条是它在流日/流时两页的对应物。名字之外的正文只钉白话与历注两行。

    条数复测：`cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "from datetime import date; from app.engines.bazi_liuri import liuri_provenance; print(len(liuri_provenance(date(2028, 1, 15)).tables))"` → 13。
    """
    from importlib.metadata import version

    result = compute_liuri_matrix(**_NATAL_KWARGS, reference_date=date(2028, 1, 15))
    tables = result.provenance.tables
    assert [table.name for table in tables] == [
        "bazi_shishen",
        "bazi_nayin",
        "bazi_wangshuai",
        "bazi_geju",
        "bazi_tiaohou",
        "bazi_shensha",
        "bazi_relations",
        "bazi_dimensions",
        "bazi_plain",
        "bazi_changsheng",
        "bazi_transit_rules",
        "bazi_transit_plain",
        "almanac_yiji",
    ]
    assert tables[11].source == BAZI_TRANSIT_PLAIN_SOURCE
    assert tables[12].version == version("lunar-python") == "1.4.8"
    assert "外部历法库" in tables[12].source
    assert tables[10].version == CONTENT_VERSION
    assert result.provenance.engine == "lunar-python"


def test_no_liuri_day_row_pollutes_the_natal_chart() -> None:
    """污染红线（spec §2.7 沿用切片 2）：同进程内先快照、跑矩阵、再快照，两次逐字相等。"""
    chart = compute_bazi_chart(reference_date=date(2028, 1, 15), **_NATAL_KWARGS)
    before = chart.model_dump()
    compute_liuri_matrix(
        **_NATAL_KWARGS, anchor_date=date(2028, 1, 15), focus_date=date(2028, 1, 10),
        reference_date=date(2028, 1, 15),
    )
    assert chart.model_dump() == before


def test_a_conflicting_favorable_set_books_both_sides_rather_than_choosing() -> None:
    """喜忌并列同一五行时两侧都进账：`+10` 与 `−10` 同屏、净额 0，不做静默取舍。

    命 A 每日恰中两条 `yongshen` 是它喜忌铺满且不相交的巧合，不是一条不变式（spec §2.5
    第 2 条）。所以本测不去数"恰两条"，只问干侧那两行是否都进了日段账本。
    """
    from dataclasses import replace

    from app.engines.bazi_transit import hit_rows, scan_transit_pillar, transit_hit_keys

    natal, _segment, _annual = _fixture(date(2028, 1, 15))
    clashing = replace(natal, favourable=frozenset({"木"}), unfavourable=frozenset({"木"}))
    scan = scan_transit_pillar(
        clashing,
        "甲子",
        position="transit_day",
        label="流日",
        scope="ri",
        dayun_ganzhi=None,
    )
    day_rows = [
        (factor.rule, factor.delta) for factor, _ in hit_rows((), (), transit_hit_keys(scan.judgement))
    ]
    assert ("ri.yongshen.gan_favourable", 10.0) in day_rows
    assert ("ri.yongshen.gan_unfavourable", -10.0) in day_rows
    gan_only = [delta for rule, delta in day_rows if rule.endswith((".gan_favourable", ".gan_unfavourable"))]
    assert sum(gan_only) == 0.0


def test_the_plain_block_is_two_sections_without_a_focus_date() -> None:
    """无 `focus_date` 恒两节，第一节两行、第二节一行；`focused` 为 None 时第三节连标题都不出现。"""
    result = _matrix()
    assert result.focused is None
    assert [section.title for section in result.plain] == list(BAZI_TRANSIT_TITLES["liuri"][:2])
    assert result.plain[0].text.count("\n") == 1 and result.plain[1].text.count("\n") == 0


def test_the_plain_block_gains_the_focus_day_section_when_a_focus_date_is_given() -> None:
    """聚焦日三件套（ISO 日 / 干支 / 分）与命中条数逐字取自 `focused` 那一格，不另算。

    实测：focus 2028-01-15 = 己亥 60.0，`day_hits` 7 条（同一天的那一行也在本文件
    `_GUILIU_GOLDEN` 里，它钉的是分值与 `ri.` 命中条数，这一条钉的是白话槽位）。
    四个数一律按槽读：`num(7)` 与 `num(60)` 整句里独一份，换成整段扫描却认不出
    「命中条数被印到分值槽上」这类互换（J-T4 评审轮 F-1 的同一条理由）。
    """
    result = _matrix_focused()
    focused = result.focused
    assert focused is not None
    assert [section.title for section in result.plain] == list(BAZI_TRANSIT_TITLES["liuri"])
    third = result.plain[2].text
    assert third.count("\n") == 0
    assert slot_value(third, BAZI_LIURI_FOCUS_FRAME, "date") == focused.solar_date
    assert slot_value(third, BAZI_LIURI_FOCUS_FRAME, "ganzhi") == focused.ganzhi
    assert slot_value(third, BAZI_LIURI_FOCUS_FRAME, "value") == num(focused.value)
    assert slot_value(third, BAZI_LIURI_FOCUS_FRAME, "hits") == num(len(focused.day_hits))
    assert (focused.solar_date, focused.ganzhi, focused.value, len(focused.day_hits)) == (
        "2028-01-15",
        "己亥",
        60.0,
        7,
    )


def test_the_plain_block_uses_the_month_ledgers_own_tier() -> None:
    """第一节第二行取 `month_score.tier` 这把现成的尺（实测 58.0 → 平），不重算均值。

    老实说一句：29 格均值实测 50.34，同落平档，所以第二行本身分辨不出两种取法；
    能分辨的是首行里的 `{value}` 槽——它印的是 58.0（月账本那个数），不是 50.3
    （spec §4.3 首行）。四个槽值与那两组数都出自 `_matrix()` 那一页，复测：
    `cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "import tests.test_bazi_liuri as L; r=L._matrix(); print(r.month_score.value, round(sum(d.value for d in r.days)/len(r.days), 2))"` → `58.0 50.34`。
    """
    result = _matrix()
    assert (result.month_score.value, result.month_score.tier) == (58.0, "平")
    first = result.plain[0].text
    line = first.split("\n")[1]
    assert line == reading(BAZI_TRANSIT, BAZI_TRANSIT_TONE_KEYS[result.month_score.tier])
    overview = first.split("\n")[0]
    printed = {
        "ganzhi": result.month_ganzhi,
        "start_solar": result.month_start_solar,
        "end_solar": result.month_end_solar,
        "value": num(result.month_score.value),
    }
    for name, value in printed.items():
        assert slot_value(overview, BAZI_LIURI_MONTH_FRAME, name) == value
    assert num(round(sum(cell.value for cell in result.days) / len(result.days), 2)) not in first
    assert (result.month_ganzhi, result.month_start_solar, result.month_end_solar) == (
        "癸丑",
        "2028-01-06",
        "2028-02-03",
    )


def test_the_plain_block_extremes_and_counts_match_the_day_table() -> None:
    """极值与两档日数都从 `days` 来：实测 29 格里 顺 6 / 滞 10，最高 己酉 77.0（2028-01-25）、
    最低 甲午 16.0（2028-01-10）——四个数都在本文件 `_GUILIU_GOLDEN` 那 29 行里。
    简表格只有 `value` / `tier`，**没有 `score`**——写 `cell.score.value` 是 AttributeError。
    两档计数复测（`chr(0x987A)`=顺、`chr(0x6EDE)`=滞，命令保持 ASCII 才贴得进 GBK 控制台）：
    `cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "import tests.test_bazi_liuri as L; from tests.plain_wording import TIER_WORDS as W; r=L._matrix(); print(len(r.days), sum(1 for d in r.days if d.tier == W[0]), sum(1 for d in r.days if d.tier == W[2]))"` → `29 6 10`。
    """
    result = _matrix()
    hi = max(result.days, key=lambda cell: cell.value)
    lo = min(result.days, key=lambda cell: cell.value)
    assert (hi.ganzhi, hi.value, len(result.days)) == ("己酉", 77.0, 29)
    assert (lo.ganzhi, lo.value) == ("甲午", 16.0)
    strong = sum(1 for cell in result.days if cell.tier == "顺")
    weak = sum(1 for cell in result.days if cell.tier == "滞")
    assert (strong, weak) == (6, 10)

    overview = result.plain[0].text.split("\n")[0]
    assert slot_value(overview, BAZI_LIURI_MONTH_FRAME, "strong") == num(strong)
    assert slot_value(overview, BAZI_LIURI_MONTH_FRAME, "weak") == num(weak)
    days_line = result.plain[1].text
    frame = BAZI_LIURI_DAYS_FRAME
    assert slot_value(days_line, frame, "count") == num(len(result.days))
    for slot, cell in (("high", hi), ("low", lo)):
        assert slot_value(days_line, frame, slot) == cell.ganzhi
        assert slot_value(days_line, frame, f"{slot}_value") == num(cell.value)
    for section in result.plain:
        assert advice_hits(section.text) == []


def test_the_plain_block_carries_no_tier_name_and_no_advice() -> None:
    """两个流日 fixture 各扫一遍装配出的整段：单字档名、`FORBIDDEN` 三条、建议词全零
    （同 J-T4 Step 1 第六条口径，也同 `tests/test_bazi_liushi.py` 那条流时侧姊妹钉）。

    J-T5 评审轮 F-03 的账：流时那条 docstring 写着「两页各扫一遍」，循环的却是 `_bare()` 与
    `_focused()` 两个**流时** fixture，流日装配文本里灌进 `tier` 或 `fired[].label` 时
    流日侧一条都不红。扫的是**装配产物**（框架句 + 档位句 + 槽值），不是语料表自己——
    语料那半边由 `tests/content/test_bazi_transit_plain_corpus.py` 管。
    """
    forbidden = (
        *PREDICTION_FORBIDDEN, *WU_DECISION_FORBIDDEN, *LEDGER_WORDS, *TIER_WORDS, *FORBIDDEN
    )
    for result in (_matrix(), _matrix_focused()):
        for section in result.plain:
            assert advice_hits(section.text) == []
            for token in forbidden:
                assert token not in section.text
