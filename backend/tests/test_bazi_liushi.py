"""流时引擎：§9.1 历法对拍、十二格形状、四段账本自洽、§9.2 与流日矩阵逐字相等、§9.3 污染红线。

直调引擎必须 `gender=Gender.MALE`（传字符串不报错但 `dayun` 族判不出，段基准 58.0 → 54.0）。
"""

from datetime import date, time, timedelta
from functools import cache

import pytest
from lunar_python import Solar

from app.content import CONTENT_VERSION
from app.content.bazi_changsheng import CHANG_SHENG_ORDER
from app.core.errors import TransitRangeError
from app.engines.bazi import compute_bazi_chart
from app.engines.bazi_liuri import compute_liuri_matrix
from app.engines.bazi_liushi import HOUR_ZHI, compute_liushi_day, liushi_hour_moments
from app.schemas.bazi_liushi import BaziLiushiResult
from app.schemas.bazi_liuri import TransitDayDetail
from app.schemas.common import CalendarType, Gender

_BIRTH = (date(1988, 2, 15), time(23, 30))
_NATAL_KWARGS = {
    "birth_date": _BIRTH[0],
    "birth_time": _BIRTH[1],
    "gender": Gender.MALE,
    "calendar": CalendarType.SOLAR,
    "longitude": 104.07,
    "apply_true_solar_time": True,
}
_DAY = date(2028, 1, 26)
_REFERENCE = date(2028, 1, 20)

_MATRIX_KWARGS = {
    **_NATAL_KWARGS,
    "anchor_date": _DAY,
    "focus_date": _DAY,
    "reference_date": _REFERENCE,
}


@cache
def _focused() -> BaziLiushiResult:
    """整页共用一次实算：十二格 + 辰时详批，13 份账本只装配一遍。"""
    return compute_liushi_day(
        **_NATAL_KWARGS, solar_date=_DAY, focus_hour_zhi="辰", reference_date=_REFERENCE
    )


@cache
def _bare() -> BaziLiushiResult:
    return compute_liushi_day(**_NATAL_KWARGS, reference_date=_REFERENCE)


@cache
def _same_day() -> TransitDayDetail | None:
    """§9.2 那三条红线的另一端：流日矩阵在这一天的聚焦格。"""
    return compute_liuri_matrix(**_MATRIX_KWARGS).focused


def test_the_hour_moments_span_one_bazi_day_and_answer_the_library_zhi() -> None:
    """§9.1 对拍：365 天 × 12 个采样点，`getTime().getZhi()` 按序轮完十二支，且整日 `…Exact()` 同柱。

    第二行是"十二格共用一根日柱"这条决定的全部证据（决策 1）；它一红，四段账本里日段恒定就
    不再成立，本模块的全部省事都作废。
    """
    day = date(2027, 3, 1)
    for _ in range(365):
        moments = liushi_hour_moments(day)
        assert len(moments) == 12
        pillars = [Solar.fromYmdHms(*m.timetuple()[:5], m.second).getLunar().getTime() for m in moments]
        assert [p.getZhi() for p in pillars] == list(HOUR_ZHI)
        exacts = {
            Solar.fromYmdHms(*m.timetuple()[:5], m.second).getLunar().getDayInGanZhiExact() for m in moments
        }
        noon = Solar.fromYmd(day.year, day.month, day.day).getLunar().getDayInGanZhi()
        assert exacts == {noon}, day
        day = day + timedelta(days=1)


def test_the_day_has_twelve_cells_in_branch_order_with_the_measured_clock_faces() -> None:
    result = _focused()
    assert [cell.index for cell in result.hours] == list(range(12))
    assert [cell.zhi for cell in result.hours] == list(HOUR_ZHI)
    assert [cell.ganzhi for cell in result.hours] == [
        "丙子", "丁丑", "戊寅", "己卯", "庚辰", "辛巳", "壬午", "癸未", "甲申", "乙酉", "丙戌", "丁亥",
    ]
    assert [(cell.start_clock, cell.end_clock) for cell in result.hours] == [
        ("23:00", "23:59"), ("01:00", "02:59"), ("03:00", "04:59"), ("05:00", "06:59"),
        ("07:00", "08:59"), ("09:00", "10:59"), ("11:00", "12:59"), ("13:00", "14:59"),
        ("15:00", "16:59"), ("17:00", "18:59"), ("19:00", "20:59"), ("21:00", "22:59"),
    ]


def test_the_day_echoes_the_resolved_segment_and_almanac() -> None:
    result = _focused()
    assert (result.solar_date, result.day_ganzhi, result.weekday, result.lunar_day) == (
        "2028-01-26", "庚戌", 2, "正初一"
    )
    assert (result.year, result.year_ganzhi, result.year_age, result.dayun_index, result.dayun_ganzhi) == (
        2027, "丁未", 40, 4, "戊午"
    )
    assert (result.month_index, result.month_in_chinese, result.month_ganzhi) == (11, "腊", "癸丑")
    assert (result.month_start_solar, result.month_end_solar) == ("2028-01-06", "2028-02-03")
    assert (result.day_score.value, result.day_score.tier) == (73.0, "顺")
    assert result.day_almanac.yi[0] == "嫁娶"
    assert result.day_almanac.ji == ["开市", "安床", "安葬", "修坟"]


def test_the_twelve_cells_match_the_measured_ledger_exactly() -> None:
    """整张十二格表逐字钉死：这是"同表同价"扩到时辰的唯一证据。"""
    assert [
        (cell.zhi, cell.ganzhi, cell.qi_strength, cell.value, cell.tier) for cell in _focused().hours
    ] == [
        ("子", "丙子", "死", 54.0, "平"),
        ("丑", "丁丑", "墓", 74.0, "顺"),
        ("寅", "戊寅", "绝", 72.0, "顺"),
        ("卯", "己卯", "胎", 66.0, "顺"),
        ("辰", "庚辰", "养", 92.0, "顺"),
        ("巳", "辛巳", "长生", 65.0, "顺"),
        ("午", "壬午", "沐浴", 44.0, "滞"),
        ("未", "癸未", "冠带", 76.0, "顺"),
        ("申", "甲申", "临官", 54.0, "平"),
        ("酉", "乙酉", "帝旺", 77.0, "顺"),
        ("戌", "丙戌", "衰", 72.0, "顺"),
        ("亥", "丁亥", "病", 54.0, "平"),
    ]


def test_qi_strength_is_the_named_twelve_stage_never_a_price() -> None:
    """`qi_strength` 只能取自那张长生表：它出现在纵轴之外才算描述，出现数字即越界。"""
    for cell in _focused().hours:
        assert cell.qi_strength in CHANG_SHENG_ORDER
        assert not any(char.isdigit() for char in cell.qi_strength)


def test_each_cell_value_is_its_own_ledger_sum() -> None:
    """§9.2 的算术红线：日头分 + 该格 `shi.` 各行 == 该格 value（本盘十二格无截断）。"""
    day = _same_day()
    assert day is not None
    for cell in _focused().hours:
        assert round(day.score.value + sum(hit.delta for hit in cell.hour_hits), 2) == cell.value, cell.zhi


def test_the_eleven_year_only_rules_never_book_in_an_hour_row() -> None:
    """太岁 6 + 大运 5 只论年：时段前缀里出现它们就是换轴换错了。"""
    for cell in _focused().hours:
        assert all(
            not hit.key.startswith(("shi.taisui.", "shi.dayun.")) for hit in cell.hour_hits
        ), cell.zhi


def test_the_peak_is_the_chen_hour_and_the_hit_counts_are_as_measured() -> None:
    cells = _focused().hours
    best = max(cells, key=lambda cell: cell.value)
    assert (best.index, best.value) == (4, 92.0)
    assert [len(cell.hour_hits) for cell in cells] == [6, 7, 4, 6, 4, 6, 4, 5, 7, 5, 5, 9]


def test_an_hour_page_and_a_day_page_agree_on_the_same_day() -> None:
    """§9.2 第 1 条：日头那三段与流日矩阵同日同分，逐字（不是"约等"）。"""
    day, result = _same_day(), _focused()
    assert day is not None
    assert result.day_score == day.score
    assert [f.model_dump() for f in result.day_fired] == [f.model_dump() for f in day.fired]
    assert (result.solar_date, result.day_ganzhi, result.lunar_day, result.weekday) == (
        day.solar_date, day.ganzhi, day.lunar_day, day.weekday
    )
    assert result.day_almanac == day.almanac


def test_the_focused_cell_books_all_four_segments() -> None:
    """聚焦格四段俱在（年段无前缀 / `yue.` / `ri.` / `shi.`），且 `hour_hits` 全是 `shi.` 前缀。

    缺一段的症状是装配时漏传一个键元组 —— 它不改别的段的分，所以只有"在场"这条能红。
    """
    focused = _focused().focused
    assert focused is not None
    rules = [factor.rule for factor in focused.score.factors]
    for prefix in ("yue.", "ri.", "shi."):
        assert any(rule.startswith(prefix) for rule in rules), prefix
    assert all(hit.key.startswith("shi.") for hit in focused.hour_hits)


def test_the_focused_chen_hour_carries_those_four_rows_in_ledger_order() -> None:
    """§9.2 第 3 条：聚焦格的 `shi.` 四行键序与分值逐字。"""
    focused = _focused().focused
    assert focused is not None and focused.zhi == "辰"
    assert [hit.key for hit in focused.hour_hits] == [
        "shi.yongshen.gan_favourable",
        "shi.yongshen.zhi_favourable",
        "shi.heyue.anhe_unfavourable",
        "shi.dishi.supportive",
    ]
    assert [hit.delta for hit in focused.hour_hits] == [10.0, 8.0, -3.0, 4.0]


def test_removing_the_hour_rows_leaves_the_day_page_fired_list() -> None:
    """§9.2 第 2 条：聚焦格 `fired` 去掉 `shi.` 前缀那些，逐字等于同日 `day_fired`。"""
    focused = _focused().focused
    assert focused is not None
    assert [f.model_dump() for f in focused.fired if not f.key.startswith("shi.")] == [
        f.model_dump() for f in _focused().day_fired
    ]


def test_a_date_before_the_luck_window_relabels_the_code_and_keeps_the_shape() -> None:
    """决策 5：改码不改形状 —— message 与 context 三件原样透传。"""
    with pytest.raises(TransitRangeError) as raised:
        compute_liushi_day(**_NATAL_KWARGS, solar_date=date(1980, 6, 1), reference_date=_REFERENCE)
    error = raised.value
    assert error.code == "liushi_date_unsupported"
    assert error.message == "1980-06-01 所在的节气月推不出：本命盘可推年份 1988—2083。"
    assert error.context == {"requested": "1980-06-01", "supported_from": 1988, "supported_to": 2083}


def test_an_unknown_branch_answers_with_a_machine_code() -> None:
    """`巽` 是八卦不是十二支：域错误，而不是静默回落子时。"""
    with pytest.raises(TransitRangeError) as raised:
        compute_liushi_day(**_NATAL_KWARGS, solar_date=_DAY, focus_hour_zhi="巽", reference_date=_REFERENCE)
    assert raised.value.code == "liushi_hour_out_of_day"
    assert raised.value.context == {"requested": "巽", "supported": HOUR_ZHI}


def test_an_absent_day_falls_back_to_the_reference_segment() -> None:
    result = _bare()
    assert (result.solar_date, result.day_ganzhi, result.month_ganzhi, result.year) == (
        "2028-01-20", "甲辰", "癸丑", 2027
    )
    assert result.focused is None and len(result.hours) == 12


def test_the_provenance_is_the_same_eleven_tables_as_the_liuri_page() -> None:
    """11 张表只有一处产出（决策 7）：两张表名逐字，条数钉死，多一行少一行都算谎。"""
    tables = {table.name: table for table in _focused().provenance.tables}
    assert len(_focused().provenance.tables) == 11
    assert tables["almanac_yiji"].version == "1.4.8"
    assert tables["bazi_transit_rules"].version == CONTENT_VERSION
    assert _focused().provenance.engine == "lunar-python"


def test_no_hour_row_pollutes_the_natal_chart() -> None:
    """§9.3 污染红线：同进程先快照、跑十二格、再快照，两次逐字相等。"""
    chart = compute_bazi_chart(reference_date=_REFERENCE, **_NATAL_KWARGS)
    before = chart.model_dump()
    compute_liushi_day(**_NATAL_KWARGS, solar_date=_DAY, focus_hour_zhi="辰", reference_date=_REFERENCE)
    assert chart.model_dump() == before


def test_the_result_round_trips_through_its_own_schema() -> None:
    parsed = BaziLiushiResult.model_validate(_focused().model_dump())
    assert parsed == BaziLiushiResult.model_validate(parsed.model_dump())
