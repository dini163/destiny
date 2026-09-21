"""岁运引擎的六条测线：区间解析、排盘时刻共用件、命中判定、账本装配、流月、总装。

区间一条线（spec §7.2）：缺省补齐 + 四道校验（倒序 / 过宽 / 越出大运窗 / focus 越
界），错误走 `TransitRangeError` 的 422 而不是 pydantic 的 422 —— 前者是"这个命盘
推不出这段岁运"，后者是"你少填了一个字段"，两件事的文案与机器码不该混在同一个
`code` 下。

排盘时刻一条线：`resolve_natal_moment` 是从 `compute_bazi_chart` 里原样搬出来的，
所以它的测法是"搬完仍等价" —— 拿它复现主命盘已经对外承诺的那几个字段，而不是另
造一套断言。

命中判定一条线（spec §6.2）：谓词只读 `_Judgement`，不回头查历法，所以这里的上下
文是手搭的。手搭也要搭得真 —— `_pair` 的字对从 `RELATION_TABLES` 里取，`_group`
的释义与出处也是，测试指给它们的只有柱位。判定这一层认的是 `kind` 与柱位，字对是
什么它看都不看，所以假字对写进测里，测的就成了"我抄的那个 kind 恰好对得上"。

装配一条线（spec §6.3 / §4 决策 3）：这里测的是"账本自洽"与"命局不脏"两件事。前者
由 Σ `delta == value`、`fired` 与账本行一一对应来钉，不需要任何具体分值（分值的
对错在 golden 里对拍）；后者只在装配层才测得动 —— 判定层的谓词拿到的是手搭上下文，
真扫描会不会把命局内部的关系灌进岁运账本，得让引擎真跑一次才知道。

流月一条线（spec §6.4）：月界不来自 lunar-python（`LiuYue` 一个日期都不给），是引擎
自己从 `getJieQiTable()` 的滚动窗口里采十二节推出来的，所以这里两头都要测 —— 一头钉
月界自己成形（首尾相接、覆盖整年），另一头钉它和历法给的月序对得上。中间那条最重要
的不变式是"年段行是月段行的前缀"：一份月账本读起来就是"今年的账 + 这个月加减的账"。

总装一条线（spec §7.4）：`compute_transit` 把前面四段接成一次真排盘，所以这里的断言
全是**契约形状**的 —— 区间回显、哪些字段该空、哪些字段必须等于语料里的那一份，而不是
某个具体分数（分数在 golden 里对拍）。唯一一处数值断言是命局摘要那几行，因为它逐字取自
主命盘，主命盘一变这里就该红。
"""

from dataclasses import replace
from datetime import date, datetime, time, timedelta
from functools import cache

import pytest

from app.content import CONTENT_SOURCES, CONTENT_VERSION, TRANSIT_CONTENT_SOURCES
from app.content.bazi_changsheng import CHANG_SHENG_ORDER
from app.content.bazi_relations import RELATION_TABLES, transforming_element
from app.content.bazi_shishen import ten_god_meaning
from app.content.bazi_transit_rules import TRANSIT_BASE, TRANSIT_RULES, transit_rule
from app.core.errors import TransitRangeError
from app.engines.bazi import compute_bazi_chart
from app.engines.bazi_moment import resolve_natal_moment
from app.engines.bazi_strength import STRONG_CUT, WEAK_CUT
from app.engines.bazi_transit import (
    _TRANSIT_SLOT,
    TransitRange,
    _Judgement,
    _Natal,
    _PREDICATES,
    _PUNISH_KINDS,
    _AnnualLuck,
    _annual_luck_by_year,
    _fired,
    _hit_keys,
    _hit_rows,
    _jieqi_boundaries,
    _ledger,
    _narrative,
    _natal_projection,
    _tier,
    _transit_months,
    _transit_year,
    _year_scan,
    compute_transit,
    resolve_transit_range,
)
from app.schemas.bazi import BaziChart
from app.schemas.bazi_rules import BranchGroup, BranchMember, RelationPair
from app.schemas.bazi_transit import BaziTransitResult, TransitMonth, TransitYear
from app.schemas.common import CalendarType, Gender
from app.schemas.scoring import ScoreFactor, ScoreValue

_WINDOW = {"supported_from": 1988, "supported_to": 2083}


def _range(**overrides: object) -> TransitRange:
    args: dict[str, object] = {
        "start_year": None,
        "end_year": None,
        "focus_year": None,
        "reference_year": 2026,
        **_WINDOW,
    }
    args.update(overrides)
    return resolve_transit_range(**args)  # type: ignore[arg-type]


def test_missing_bounds_default_to_five_years_from_the_reference() -> None:
    span = _range()
    assert (span.start_year, span.end_year, span.focus_year) == (2026, 2030, None)


def test_only_one_bound_supplies_the_other_by_the_default_span() -> None:
    from_start = _range(start_year=2000)
    from_end = _range(end_year=2000)
    assert (from_start.start_year, from_start.end_year) == (2000, 2004)
    assert (from_end.start_year, from_end.end_year) == (1996, 2000)


def test_ten_years_is_allowed_and_eleven_is_not() -> None:
    assert _range(start_year=2000, end_year=2009).end_year == 2009
    with pytest.raises(TransitRangeError) as excinfo:
        _range(start_year=2000, end_year=2010)
    assert excinfo.value.code == "transit_range_too_wide"
    assert excinfo.value.context == {"max_years": 10, "requested": 11}


def test_reversed_bounds_report_both_years() -> None:
    with pytest.raises(TransitRangeError) as excinfo:
        _range(start_year=2030, end_year=2029)
    assert excinfo.value.code == "transit_range_reversed"
    assert excinfo.value.context == {"start_year": 2030, "end_year": 2029}


def test_years_outside_the_luck_pillar_window_are_rejected() -> None:
    for start, end in ((1980, 1984), (2084, 2088)):
        with pytest.raises(TransitRangeError) as excinfo:
            _range(start_year=start, end_year=end)
        assert excinfo.value.code == "transit_range_unsupported"
        assert excinfo.value.context == {
            "supported_from": 1988,
            "supported_to": 2083,
            "requested_from": start,
            "requested_to": end,
        }


def test_focus_year_must_sit_inside_the_span() -> None:
    with pytest.raises(TransitRangeError) as excinfo:
        _range(start_year=2024, end_year=2028, focus_year=2030)
    assert excinfo.value.code == "transit_focus_out_of_range"
    assert excinfo.value.context == {"focus_year": 2030, "start_year": 2024, "end_year": 2028}


def test_error_status_is_422() -> None:
    with pytest.raises(TransitRangeError) as excinfo:
        _range(start_year=2030, end_year=2029)
    assert excinfo.value.status_code == 422


_BIRTH = (date(1988, 2, 15), time(23, 30))


def test_corrected_moment_matches_what_the_natal_chart_reports() -> None:
    """共用出口的第一条承诺：校正过的时刻就是主命盘已经对外给出的那几个字段。"""
    moment = resolve_natal_moment(
        birth_date=_BIRTH[0],
        birth_time=_BIRTH[1],
        calendar=CalendarType.SOLAR,
        longitude=104.1,
        apply_true_solar_time=True,
    )
    chart = compute_bazi_chart(
        birth_date=_BIRTH[0],
        birth_time=_BIRTH[1],
        calendar=CalendarType.SOLAR,
        longitude=104.1,
        gender="MALE",
        apply_true_solar_time=True,
    )
    assert moment.standard_datetime == datetime(1988, 2, 15, 23, 30)
    assert moment.true_solar_time_text == chart.true_solar_time == "1988-02-15 22:12"
    assert moment.offset_minutes == chart.tst_offset_minutes == -77.84
    assert moment.longitude_used == chart.longitude == 104.1
    assert moment.eight_char.toString() == chart.four_pillars
    assert moment.lunar.toString() == chart.lunar_date


def test_uncorrected_moment_carries_no_correction_to_invent() -> None:
    """关掉校正时不留"0 分钟"这种假事实：字段为空，且柱与主命盘的关闭路径同源。"""
    moment = resolve_natal_moment(
        birth_date=_BIRTH[0],
        birth_time=_BIRTH[1],
        calendar=CalendarType.SOLAR,
        longitude=104.1,
        apply_true_solar_time=False,
    )
    chart = compute_bazi_chart(
        birth_date=_BIRTH[0],
        birth_time=_BIRTH[1],
        calendar=CalendarType.SOLAR,
        longitude=104.1,
        gender="MALE",
        apply_true_solar_time=False,
    )
    assert moment.chart_datetime == moment.standard_datetime
    assert moment.true_solar_time_text is None
    assert moment.offset_minutes is None
    assert moment.eight_char.toString() == chart.four_pillars == "戊辰 甲寅 庚子 戊子"


# ---------------------------------------------------------------- 命中判定（spec §6.2）
#: 这三个族的命中不由关系 / 合局驱动，本任务的 28 键测先让开它们（Task 7 收口）。
_NOT_RELATION_DRIVEN = frozenset({"dayun", "dishi", "shensha"})


def _pair(kind: str, pillar_a: str, pillar_b: str) -> RelationPair:
    """一条真关系：字对由 `RELATION_TABLES` 自己给，测试只指定它落在哪两柱。"""
    rule = RELATION_TABLES[kind]
    char_a, char_b = sorted(rule.pairs)[0]
    return RelationPair(
        kind=rule.kind,
        pillar_a=pillar_a,
        pillar_b=pillar_b,
        character_a=char_a,
        character_b=char_b,
        strength="紧临",
        transforming_element=transforming_element(rule.kind, char_a, char_b),
        reading=rule.reading,
        source=rule.source,
    )


def _pillar_pair(kind: str, pillar_a: str, a: str, pillar_b: str, b: str) -> RelationPair:
    """伏吟 / 反吟这类"整柱比对"的关系：表里没有字对可取，两柱由测试给全。"""
    rule = RELATION_TABLES[kind]
    return RelationPair(
        kind=rule.kind,
        pillar_a=pillar_a,
        pillar_b=pillar_b,
        character_a=a,
        character_b=b,
        strength="紧临",
        reading=rule.reading,
        source=rule.source,
    )


def _group(
    kind: str, element: str, members: tuple[tuple[str, str], ...], *, complete: bool
) -> BranchGroup:
    """一局：种类、五行与柱位由测试指定，释义与出处取自同一张关系表。"""
    rule = RELATION_TABLES[kind]
    return BranchGroup(
        kind=rule.kind,
        element=element,
        is_complete=complete,
        members=[
            BranchMember(pillar=pillar, branch=branch, ten_god="") for pillar, branch in members
        ],
        reading=rule.reading,
        source=rule.source,
    )


def _judgement(**overrides: object) -> _Judgement:
    """一条中性流年（乙丑：干木支土、坐沐浴）+ 空扫描集，单测只改它要断言的那几项。

    `di_shi` 取沐浴是"中性"的另一半：十二长生里只有沐浴不定价（既是败地又是桃花，
    一书两说），换成衰就会让下面每一条精确断言里混进一行 `dishi.decaying`。
    """
    base: dict[str, object] = {
        "scope": "sui",
        "ganzhi": "乙丑",
        "gan": "乙",
        "zhi": "丑",
        "gan_element": "木",
        "ben_qi_element": "土",
        "di_shi": "沐浴",
        "dayun_ganzhi": None,
        "year_zhi": "辰",
        "relations": (),
        "groups": (),
        "shensha_names": frozenset(),
        "favourable": frozenset({"土", "金"}),
        "unfavourable": frozenset({"木", "水", "火"}),
    }
    return _Judgement(**{**base, **overrides})


def test_favourable_and_unfavourable_gods_fire_from_the_five_elements() -> None:
    """干看干本身、支看支本气，两条各自独立；输出序即规则表序（账本序）。"""
    assert _hit_keys(_judgement()) == ["yongshen.gan_unfavourable", "yongshen.zhi_favourable"]
    assert _hit_keys(_judgement(gan_element="金", ben_qi_element="火")) == [
        "yongshen.gan_favourable",
        "yongshen.zhi_unfavourable",
    ]


def test_taisui_rows_all_read_the_year_branch() -> None:
    """太岁六条：五条形（冲 / 害 / 破 / 合 / 刑）+ 值太岁 —— 表里本无"值"这一行，单判。"""
    for kind, key in (
        ("地支六冲", "taisui.chong"),
        ("地支六害", "taisui.harm"),
        ("地支六破", "taisui.break"),
        ("地支六合", "taisui.combine"),
        ("无恩之刑", "taisui.punish"),
    ):
        keys = _hit_keys(_judgement(relations=(_pair(kind, "year", "extra0"),)))
        assert key in keys, kind
    assert "taisui.value" in _hit_keys(_judgement(zhi="辰"))
    assert "taisui.value" not in _hit_keys(_judgement(zhi="戌"))


def test_natal_relations_do_not_enter_the_transit_ledger() -> None:
    """污染红线（spec §4 决策 3）：同一种冲，双方都是命局柱 → 岁运一行都不许多出。"""
    natal = _pair("地支六冲", "year", "month")
    assert _hit_keys(_judgement(relations=(natal,))) == [
        "yongshen.gan_unfavourable",
        "yongshen.zhi_favourable",
    ]


def test_all_four_punishment_tables_count_as_a_single_row() -> None:
    """刑有四张表（无恩 / 恃势 / 无礼 / 自刑）：漏任何一张就是漏一条凶。"""
    for kind in _PUNISH_KINDS:
        keys = _hit_keys(_judgement(relations=(_pair(kind, "month", "extra0"),)))
        assert "palace.punish_month" in keys, kind
        assert "taisui.punish" not in keys, kind  # 月支受刑不是太岁受刑


def test_palace_and_stem_rows_read_their_own_palace() -> None:
    """提纲（月支）与夫妻宫（日支）各自成行；天干两行只认日主那一柱。"""
    branches = _hit_keys(
        _judgement(
            relations=(
                _pair("地支六冲", "month", "extra0"),
                _pair("地支六合", "day", "extra0"),
            )
        )
    )
    assert {"palace.chong_month", "palace.combine_day"} <= set(branches)
    assert "palace.chong_day" not in branches and "palace.combine_month" not in branches
    year_stem = _hit_keys(_judgement(relations=(_pair("天干相冲", "year", "extra0"),)))
    assert not any(key.startswith("ganzhi") for key in year_stem), year_stem
    day_stem = _hit_keys(_judgement(relations=(_pair("天干五合", "day", "extra0"),)))
    assert "ganzhi.combine_day_master" in day_stem


def test_transit_only_groups_count() -> None:
    """局里没有岁运成员就不算岁运的账；向背由合出的五行定，不由局的种类定。"""
    natal_only = _group("半合", "水", (("year", "辰"), ("day", "子")), complete=False)
    assert not any(key.startswith("heyue") for key in _hit_keys(_judgement(groups=(natal_only,))))
    triad_water = _group(
        "三合", "水", (("year", "辰"), ("day", "子"), ("extra0", "申")), complete=True
    )
    assert "heyue.sanhe_unfavourable" in _hit_keys(_judgement(groups=(triad_water,)))
    triad_metal = _group(
        "三合", "金", (("year", "巳"), ("month", "酉"), ("extra0", "丑")), complete=True
    )
    assert "heyue.sanhe_favourable" in _hit_keys(_judgement(groups=(triad_metal,)))
    half = _group("半合", "火", (("month", "寅"), ("extra0", "午")), complete=False)
    assert "heyue.anhe_unfavourable" in _hit_keys(_judgement(groups=(half,)))
    meeting = _group(
        "三会", "木", (("year", "寅"), ("month", "卯"), ("extra0", "辰")), complete=True
    )
    assert "heyue.sanhui_unfavourable" in _hit_keys(_judgement(groups=(meeting,)))


def test_fu_yin_rows_read_whatever_the_scan_reported() -> None:
    """伏吟 / 反吟由 `derive_relations` 逐柱判字，判定这一层只认 kind 与柱位。"""
    assert "fuyin.fuyin" in _hit_keys(
        _judgement(relations=(_pillar_pair("伏吟", "day", "庚子", "extra0", "庚子"),))
    )
    assert "fuyin.fanyin" in _hit_keys(
        _judgement(relations=(_pillar_pair("反吟", "month", "甲寅", "extra0", "庚申"),))
    )


def test_year_only_families_vanish_in_the_month_scope() -> None:
    """scopes 过滤在 `_hit_keys` 里做：同一个太岁上下文，月段一行都不出。"""
    year = _judgement(zhi="戌", relations=(_pair("地支六冲", "year", "extra0"),))
    assert "taisui.chong" in _hit_keys(year)
    assert _hit_keys(replace(year, scope="yue")) == [
        "yongshen.gan_unfavourable",
        "yongshen.zhi_favourable",
    ]


def test_the_28_relation_keys_are_all_present() -> None:
    """六个关系族 28 键与规则表同名同数：谓词表少一行，账本就永远少一行。"""
    consumed = {key for key, _ in _PREDICATES}
    relation_driven = {
        rule.key for rule in TRANSIT_RULES.values() if rule.family not in _NOT_RELATION_DRIVEN
    }
    assert relation_driven <= consumed
    assert len(relation_driven) == 28


# --------------------------------------------------------- 大运 / 地势 / 神煞（Task 7）
#: 十二长生里定价的三档。沐浴不在此列：它既是败地又是桃花，一书两说，不给它定价。
_STAGE_BANDS = {
    "dishi.prosperous": ("临官", "帝旺"),
    "dishi.supportive": ("长生", "冠带", "胎", "养"),
    "dishi.decaying": ("衰", "病", "死", "墓", "绝"),
}


def test_childhood_span_and_month_scope_suppress_the_whole_dayun_family() -> None:
    """大运族的两道闸：童年段无运可论（spec §2.1），月段不带大运的账（`scopes`）。"""
    fired = _judgement(dayun_ganzhi="甲辰", ganzhi="甲辰", gan="甲", zhi="辰", gan_element="木")
    assert "dayun.binglin" in _hit_keys(fired)
    for blanked in (replace(fired, dayun_ganzhi=None), replace(fired, scope="yue")):
        assert not any(key.startswith("dayun") for key in _hit_keys(blanked))


def test_dayun_bing_lin_and_fanyin_compare_the_whole_pillars() -> None:
    """并临是全同，反吟是干支两冲 —— 都与合成柱的干支字符串直接比，不走关系扫描。"""
    same = _hit_keys(
        _judgement(dayun_ganzhi="甲辰", ganzhi="甲辰", gan="甲", zhi="辰", gan_element="木")
    )
    assert "dayun.binglin" in same
    assert "dayun.fanyin" not in same and "dayun.gan_he" not in same
    opposed = _hit_keys(
        _judgement(dayun_ganzhi="甲子", ganzhi="庚午", gan="庚", zhi="午", gan_element="金")
    )
    assert "dayun.fanyin" in opposed and "dayun.binglin" not in opposed


def test_dayun_relationships_are_read_from_the_five_element_cycle() -> None:
    """生克以干论（支藏多气，一支之内不止一行）；顺逆两条互斥，合又是独立一问。"""
    sui_sheng = _hit_keys(
        _judgement(dayun_ganzhi="戊午", ganzhi="丁未", gan="丁", zhi="未", gan_element="火")
    )
    assert "dayun.sui_sheng_yun" in sui_sheng  # 火生土
    assert "dayun.yun_sheng_sui" not in sui_sheng
    yun_sheng = _hit_keys(
        _judgement(dayun_ganzhi="甲子", ganzhi="丁卯", gan="丁", zhi="卯", gan_element="火")
    )
    assert "dayun.yun_sheng_sui" in yun_sheng  # 木生火
    assert "dayun.sui_sheng_yun" not in yun_sheng
    combined = _hit_keys(
        _judgement(dayun_ganzhi="己未", ganzhi="甲子", gan="甲", zhi="子", gan_element="木")
    )
    assert "dayun.gan_he" in combined  # 甲己合，且木与土无先后
    assert not {"dayun.sui_sheng_yun", "dayun.yun_sheng_sui"} & set(combined)


def test_life_stage_bands_partition_the_eleven_priced_stages() -> None:
    """三档分完 12 位里定价的 11 位：漏一格是漏一行，重一格是同一柱计两次分。"""
    priced = [stage for band in _STAGE_BANDS.values() for stage in band]
    assert sorted([*priced, "沐浴"]) == sorted(CHANG_SHENG_ORDER)
    assert len(priced) == 11
    for key, stages in _STAGE_BANDS.items():
        for stage in stages:
            hits = [k for k in _hit_keys(_judgement(di_shi=stage)) if k.startswith("dishi")]
            assert hits == [key], stage
    assert not any(k.startswith("dishi") for k in _hit_keys(_judgement(di_shi="沐浴")))


def test_shensha_rows_fire_by_name_and_neutral_stays_unpriced() -> None:
    """华盖在 `SHENSHA_RULES` 里是中性：岁运落成华盖不加分，也不该出现在账本里。"""
    keys = _hit_keys(_judgement(shensha_names=frozenset({"羊刃", "华盖"})))
    assert [key for key in keys if key.startswith("shensha")] == ["shensha.yangren"]


def test_each_shensha_row_reads_exactly_its_own_rule_table_label() -> None:
    """一行一颗星：谓词里那颗星的名字必须就是规则表的 `label`，且不牵连同族余行。"""
    for key, rule in TRANSIT_RULES.items():
        if rule.family != "shensha":
            continue
        hits = [
            k
            for k in _hit_keys(_judgement(shensha_names=frozenset({rule.label})))
            if k.startswith("shensha")
        ]
        assert hits == [key], f"{key} 的 label {rule.label} 打中的是 {hits}"


def test_every_rule_row_is_consumed_by_exactly_one_predicate() -> None:
    """漂移门：谓词键序 == 规则表键序，46 行一行不多不少。漏一行、多一行、换序都红。"""
    assert [key for key, _ in _PREDICATES] == list(TRANSIT_RULES)
    assert len(_PREDICATES) == 46


# ---------------------------------------------------------------- 账本装配（spec §6.3）
_NATAL_KWARGS: dict[str, object] = {
    "birth_date": _BIRTH[0],
    "birth_time": _BIRTH[1],
    "calendar": CalendarType.SOLAR,
    "longitude": 104.1,
    "gender": Gender.MALE,
    "apply_true_solar_time": True,
}


def _natal() -> tuple[BaziChart, _Natal]:
    """基准命 A 的命盘，与岁运要读的那一份投影 —— 同源于同一次排盘。"""
    chart = compute_bazi_chart(**_NATAL_KWARGS)  # type: ignore[arg-type]
    return chart, _natal_projection(chart)


#: 摊平一次大运要走完十个流年段，比整张命盘还贵；这两份结果全程只读，故就地缓存。
@cache
def _luck() -> dict[int, _AnnualLuck]:
    """大运段摊平出来的逐年流年（童年段也在其中，`dayun_ganzhi` 为空）。"""
    moment = resolve_natal_moment(
        birth_date=_BIRTH[0],
        birth_time=_BIRTH[1],
        calendar=CalendarType.SOLAR,
        longitude=104.1,
        apply_true_solar_time=True,
    )
    return _annual_luck_by_year(moment.eight_char, Gender.MALE)


@cache
def _years() -> dict[int, TransitYear]:
    """基准命 A 的 2024–2028 五年装配 —— 自洽测与污染测共用的那一份输入。"""
    _, natal = _natal()
    luck = _luck()
    return {year: _transit_year(natal, luck[year]) for year in range(2024, 2029)}


def test_the_baseline_chart_is_what_every_transit_ledger_is_read_against() -> None:
    """装配段的地板：命 A 的四柱、强弱与喜忌集。它们变了，下面的分档全都不必再看。"""
    chart, natal = _natal()
    assert chart.four_pillars == "戊辰 甲寅 庚子 丁亥"
    assert chart.analysis.strength.value == pytest.approx(25.85, abs=0.01)
    assert (natal.day_master, natal.year_zhi) == ("庚", "辰")
    assert natal.favourable == frozenset({"土", "金"})
    assert natal.unfavourable == frozenset({"木", "水", "火"})


def test_the_transit_assembly_never_mutates_the_natal_chart() -> None:
    """污染红线：把命盘交给岁运跑完五年，它必须还是原来那份，逐字段相等（spec §2.4）。"""
    chart, natal = _natal()
    before = chart.model_dump()
    luck = _luck()
    for year in range(2024, 2029):
        _transit_year(natal, luck[year])
    assert chart.model_dump() == before


def test_a_transit_year_carries_only_details_that_land_on_the_transit_pillar() -> None:
    """污染红线的另一半：三张明细里不许混进命局自有的象 —— 那是命局的账。"""
    for transit in _years().values():
        assert all(
            _TRANSIT_SLOT in (relation.pillar_a, relation.pillar_b)
            for relation in transit.relations
        )
        assert all(
            any(match.position == _TRANSIT_SLOT for match in entry.matches)
            for entry in transit.shensha
        )
        assert all(
            any(member.pillar == _TRANSIT_SLOT for member in group.members)
            for group in transit.branch_groups
        )


def test_every_transit_ledger_adds_up_to_its_own_value() -> None:
    """账本可核对：Σ delta == value，且第一行永远是基准行（spec §3 的 no-mock 形态）。"""
    for transit in _years().values():
        factors = transit.score.factors
        assert factors[0].rule == "transit.base"
        assert factors[0].delta == TRANSIT_BASE
        assert sum(factor.delta for factor in factors) == pytest.approx(transit.score.value)


def test_the_fired_list_is_the_ledger_with_its_own_reading() -> None:
    """`fired` 是账本的镜像而非第二份结论：键、短名、分值逐行对齐，断语就是判语连缀。"""
    for transit in _years().values():
        rows = transit.score.factors[1:]
        assert [item.key for item in transit.fired] == [row.rule for row in rows]
        assert [item.label for item in transit.fired] == [row.label for row in rows]
        assert [item.delta for item in transit.fired] == [row.delta for row in rows]
        assert [item.family for item in transit.fired] == [
            row.rule.split(".", maxsplit=1)[0] for row in rows
        ]
        for item in transit.fired:
            assert item.reading == transit_rule(item.key.removeprefix("yue.")).reading
        assert transit.narrative == "；".join(item.reading for item in transit.fired) + "。"


def test_a_transit_with_nothing_fired_is_still_a_base_only_ledger() -> None:
    """一条未中不是"没有结论"：账本剩基准 50 分 / 档"平"，断语是空串而不是一个句号。"""
    rows = _hit_rows([], [])
    score = _ledger(rows)
    assert (score.value, score.tier) == (50.0, "平")
    assert [factor.rule for factor in score.factors] == ["transit.base"]
    assert _fired(rows) == []
    assert _narrative(rows) == ""


def test_the_same_rule_is_priced_once_in_the_year_row_and_once_in_the_month_row() -> None:
    """两段账本里同一条规则各记一行，月段带 `yue.` 前缀与"（流月）"后缀，分值同源。"""
    rows = _hit_rows(["palace.chong_day"], ["palace.chong_day"])
    year_row, month_row = rows
    rule = TRANSIT_RULES["palace.chong_day"]
    assert year_row[0].rule == "palace.chong_day"
    assert month_row[0].rule == "yue.palace.chong_day"
    assert month_row[0].label == f"{rule.label}（流月）"
    assert year_row[0].label == rule.label
    assert {year_row[0].delta, month_row[0].delta} == {rule.delta}


def test_the_score_bands_use_the_same_cuts_as_the_strength_ledger() -> None:
    """分档不另立阈值：65 / 45 两道线由旺衰那两处常量供给（spec §6.3）。"""
    assert _tier(STRONG_CUT) == "顺"
    assert _tier(STRONG_CUT - 0.01) == "平"
    assert _tier(WEAK_CUT) == "平"
    assert _tier(WEAK_CUT - 0.01) == "滞"


def test_each_year_carries_the_luck_pillar_it_belongs_to() -> None:
    """2024–2028 俱在戊午运内：运段序号与干支来自摊平的那一步，不是再查一次历法。"""
    assert {transit.dayun_index for transit in _years().values()} == {4}
    assert {transit.dayun_ganzhi for transit in _years().values()} == {"戊午"}


def test_the_pre_luck_childhood_span_has_no_luck_pillar_to_reason_from() -> None:
    """未起运之年：`dayun_ganzhi` 为 None，整个大运族一行都不记账（不是记 0 分）。"""
    _, natal = _natal()
    transit = _transit_year(natal, _luck()[1990])
    assert transit.dayun_ganzhi is None
    assert [item.key for item in transit.fired if item.key.startswith("dayun.")] == []


def test_the_ten_god_block_quotes_the_corpus_for_the_transit_stem() -> None:
    """十神只作释义：名字就是合成柱的干十神，句子逐字来自《渊海子平》，引擎不组句。"""
    for transit in _years().values():
        corpus = ten_god_meaning(transit.pillar.shishen_gan)
        assert transit.ten_god.god == transit.pillar.shishen_gan != "日主"
        assert transit.ten_god.meaning == corpus.meaning
        assert transit.ten_god.source == corpus.source


# ---------------------------------------------------------------- 流月（spec §6.4）
def _iso(day: str) -> date:
    return date.fromisoformat(day)


def _contributions(score: ScoreValue) -> list[ScoreFactor]:
    """账本里的命中行：基准行与截断行都不算 —— 前者每份账本都有，后者是账本的收尾。

    两段账本要比的正是"命中了什么、按什么次序"，把这两行留在里面就成了比格式。
    """
    excluded = {"transit.base", "score.clamped"}
    return [factor for factor in score.factors if factor.rule not in excluded]


@cache
def _months() -> list[TransitMonth]:
    """2026（丙午）的 12 节气月：年段键先查出来，月段账本要接着它往下记。"""
    _, natal = _natal()
    luck = _luck()[2026]
    return _transit_months(natal, luck, _hit_keys(_year_scan(natal, luck).judgement))


def test_the_twelve_jieqi_months_are_contiguous_and_span_one_whole_solar_year() -> None:
    """月界无重叠无空洞：立春起、次年立春前一日止，逐段首尾相接（spec §9.4）。"""
    months = _months()
    assert [month.index for month in months] == list(range(12))
    assert [month.month_in_chinese for month in months] == [
        "正", "二", "三", "四", "五", "六", "七", "八", "九", "十", "冬", "腊",
    ]
    assert months[0].start_solar == "2026-02-04"  # 立春
    assert months[-1].end_solar == "2027-02-03"  # 次年立春前一日
    for earlier, later in zip(months, months[1:], strict=False):  # 12 段 → 11 个接缝
        assert _iso(earlier.end_solar) + timedelta(days=1) == _iso(later.start_solar)


@pytest.mark.parametrize("year", [1988, 2000, 2026, 2027, 2083])
def test_the_jieqi_window_holds_all_twelve_nodes_in_every_reachable_year(year: int) -> None:
    """`getJieQiTable()` 是滚动窗口，窄一节就少一段月界。探针年份取大运可及的首尾与闰年附近。"""
    spans = _jieqi_boundaries(year)
    assert len(spans) == 12
    for index, (start, end) in enumerate(spans):
        assert start <= end, f"{year} 年第 {index} 段月界倒挂"
        if index:
            assert spans[index - 1][1] + timedelta(days=1) == start
    assert date(year, 2, 3) <= spans[0][0] <= date(year, 2, 5)  # 立春只在 2/3—2/5 之间交节
    assert date(year + 1, 2, 2) <= spans[-1][1] + timedelta(days=1) <= date(year + 1, 2, 5)


def test_the_month_stems_and_branches_come_from_lunar_python_not_from_a_renumbering() -> None:
    """月柱逐字取 `LiuYue.getGanZhi()`（五虎遁在历法手里），引擎只把它和序号、月名对齐。

    2026 是丙午年，丙辛之年以庚寅起首 —— 逐段差一位干，整张月表就跟着错一年。
    """
    raw = _luck()[2026].liunian.getLiuYue()
    assert [(m.index, m.ganzhi, m.month_in_chinese) for m in _months()] == [
        (lyue.getIndex(), lyue.getGanZhi(), lyue.getMonthInChinese()) for lyue in raw
    ]
    assert [m.ganzhi for m in _months()] == [
        "庚寅", "辛卯", "壬辰", "癸巳", "甲午", "乙未",
        "丙申", "丁酉", "戊戌", "己亥", "庚子", "辛丑",
    ]


def test_the_month_ledger_is_the_year_ledger_with_the_month_rows_appended() -> None:
    """两段账本不变式（spec §6.4）：年段行是月段行的前缀，月段行一律带 `yue.` 前缀。

    整表比不了 —— 一份月账本里同一条规则可以出现两次（年段一次、月段一次），那正是
    前缀要分辨的事；剥掉基准行之后，前 len(年段) 行必须逐行相等。
    """
    year_rows = _contributions(_years()[2026].score)
    for month in _months():
        rows = _contributions(month.score)
        assert rows[: len(year_rows)] == year_rows
        assert all(factor.rule.startswith("yue.") for factor in rows[len(year_rows) :])
        assert all("（流月）" in factor.label for factor in rows[len(year_rows) :])
        assert sum(factor.delta for factor in month.score.factors) == pytest.approx(
            month.score.value
        )
        assert [item.key for item in month.fired] == [factor.rule for factor in rows]


def test_no_month_segment_reprices_a_year_only_family() -> None:
    """太岁与大运两族的 `scopes` 不含 `yue`：月账本里它们一行都不该出现（spec §6.2）。"""
    month_rows = [
        factor.rule[len("yue.") :]
        for month in _months()
        for factor in _contributions(month.score)
        if factor.rule.startswith("yue.")
    ]
    assert [row for row in month_rows if row.split(".", maxsplit=1)[0] in ("taisui", "dayun")] == []


def test_a_month_pillar_is_synthesised_as_a_transit_month() -> None:
    """月柱与年柱同一条合成路：`position` 为 transit_month、`label` 为 流月，宫位不套。"""
    for month in _months():
        assert month.pillar.position == "transit_month"
        assert month.pillar.label == "流月"
        assert month.pillar.ganzhi == month.ganzhi


def test_the_focused_year_carries_its_months_and_the_others_carry_none() -> None:
    """`focus` 是逐年开关：聚焦年给 12 段，其余年为 None，前端整块不渲染而非十二个空月。"""
    _, natal = _natal()
    assert _transit_year(natal, _luck()[2026], focus=True).months is not None
    assert [t.months for t in _years().values()].count(None) == 5


# ---------------------------------------------------------------- 总装（spec §7.3 / §7.4）
_REFERENCE = date(2026, 9, 21)  # 钉死参考日：当前大运档与缺省区间都跟着它走


def _transit(**overrides: object) -> BaziTransitResult:
    """真走一遍引擎的岁运结果；参考日固定，于是"今年是哪一年"在测里也是可复现的。"""
    args: dict[str, object] = {**_NATAL_KWARGS, "reference_date": _REFERENCE}
    args.update(overrides)
    return compute_transit(**args)  # type: ignore[arg-type]


@cache
def _default() -> BaziTransitResult:
    """缺省请求（什么都不给）—— 一条断言都不改它，只从各个角度读它。"""
    return _transit()


def test_the_default_request_spans_five_years_from_the_reference_year() -> None:
    """缺省补齐只在引擎里做一次，回显即最终事实（spec §7.1"前端不必二次推算"）。"""
    result = _default()
    assert (result.start_year, result.end_year, result.focus_year) == (2026, 2030, None)
    assert [year.year for year in result.years] == [2026, 2027, 2028, 2029, 2030]
    assert [year.pillar.ganzhi for year in result.years] == ["丙午", "丁未", "戊申", "己酉", "庚戌"]


def test_an_explicit_span_is_echoed_back_unchanged() -> None:
    result = _transit(start_year=2030, end_year=2036)
    assert (result.start_year, result.end_year) == (2030, 2036)
    assert [year.year for year in result.years] == list(range(2030, 2037))


def test_a_span_wider_than_the_cap_or_before_the_chart_is_refused_with_its_own_code() -> None:
    """区间三道校验在总装里照样是域错误，不是 500 也不是 pydantic 的 validation_error。"""
    with pytest.raises(TransitRangeError) as too_wide:
        _transit(start_year=2020, end_year=2031)
    assert too_wide.value.code == "transit_range_too_wide"
    with pytest.raises(TransitRangeError) as outside:
        _transit(start_year=1900, end_year=1904)
    assert outside.value.code == "transit_range_unsupported"
    assert outside.value.context["supported_from"] == 1988  # 出生年，大运窗之始
    assert outside.value.context["supported_to"] == 2083  # lunar-python 摊出来的最末年


@pytest.mark.parametrize(
    ("span", "expected"),
    [
        ((2026, 2030), [("戊午", True)]),  # 整段都在第四步运里
        ((2030, 2036), [("戊午", True), ("己未", False)]),  # 跨段：两段都给出
        ((1988, 1993), [("", False)]),  # 起运前的童年段：运干为空串，也不是当前运
    ],
)
def test_the_covered_dayun_steps_are_the_ones_the_span_actually_runs_through(
    span: tuple[int, int], expected: list[tuple[str, bool]]
) -> None:
    """`dayun_covered` 是区间与运程的交集，`is_current` 沿用主命盘的旗标而非另判一次。"""
    result = _transit(start_year=span[0], end_year=span[1])
    assert [(step.ganzhi, step.is_current) for step in result.dayun_covered] == expected


def test_the_childhood_span_reports_no_dayun_yet_still_scores_every_year() -> None:
    """未起运的六年：`dayun_ganzhi` 逐年为 None，但大运族一行都不进账本，分数照常可核对。"""
    result = _transit(start_year=1990, end_year=1992)
    assert [year.dayun_index for year in result.years] == [0, 0, 0]
    assert [year.dayun_ganzhi for year in result.years] == [None, None, None]
    for year in result.years:
        assert [row.family for row in year.fired].count("dayun") == 0


def test_only_the_focus_year_carries_twelve_months() -> None:
    """`months` 为 None 是结构性的：没请求流月就没有十二个空月（spec §7.3）。"""
    assert all(year.months is None for year in _default().years)
    focused = _transit(start_year=2026, end_year=2030, focus_year=2027)
    assert focused.focus_year == 2027
    assert [year.year for year in focused.years if year.months is not None] == [2027]
    assert [month.index for month in focused.years[1].months] == list(range(12))


def test_a_focus_year_outside_the_span_is_refused_before_any_work() -> None:
    with pytest.raises(TransitRangeError) as excinfo:
        _transit(start_year=2026, end_year=2030, focus_year=2035)
    assert excinfo.value.code == "transit_focus_out_of_range"


def test_the_natal_summary_is_the_projection_the_page_shows_and_nothing_else() -> None:
    """命局摘要逐字取自同一次排盘的主命盘：口径分家时这里先红。"""
    chart, _ = _natal()
    result = _default()
    assert result.four_pillars == "戊辰 甲寅 庚子 丁亥"
    assert [pillar.position for pillar in result.pillars] == ["year", "month", "day", "hour"]
    assert (result.day_master, result.day_master_element) == ("庚", "金")
    assert result.favorable_elements == chart.analysis.favorable_elements
    assert result.unfavorable_elements == chart.analysis.unfavorable_elements
    assert result.longitude == 104.1


def test_the_true_solar_time_echo_follows_the_correction_switch() -> None:
    """开着校正给时刻，关着校正给 None；经度两种情况下都照实回显，缺省是东八区标准经线。"""
    on = _default()
    assert on.tst_applied is True and on.true_solar_time is not None
    off = _transit(apply_true_solar_time=False)
    assert (off.tst_applied, off.true_solar_time) == (False, None)
    assert off.longitude == 104.1  # 校正关了，但用的经度仍是同一份，回显不该变成 0
    bare = compute_transit(
        birth_date=_BIRTH[0],
        birth_time=_BIRTH[1],
        gender=Gender.MALE,
        apply_true_solar_time=False,
    )
    assert bare.longitude == 120.0  # 不给经度 → 东经 120°，与 `/natal` 同口径


def test_every_detail_on_a_year_card_involves_the_transit_pillar() -> None:
    """三张扫描明细只留岁运落点：命局自有之象留在命局页（spec §4 决策 3）。"""
    for year in _default().years:
        assert all(_TRANSIT_SLOT in (item.pillar_a, item.pillar_b) for item in year.relations)
        assert all(
            any(match.position == _TRANSIT_SLOT for match in item.matches) for item in year.shensha
        )
        assert all(
            any(member.pillar == _TRANSIT_SLOT for member in group.members)
            for group in year.branch_groups
        )


def test_the_ten_god_block_quotes_the_corpus_verbatim() -> None:
    """引擎不组句：释义与出处逐字等于 `ten_god_meaning` 里的那一条。"""
    for year in _default().years:
        corpus = ten_god_meaning(year.pillar.shishen_gan)
        assert (year.ten_god.god, year.ten_god.meaning, year.ten_god.source) == (
            corpus.ten_god,
            corpus.meaning,
            corpus.source,
        )


def test_the_provenance_lists_the_natal_tables_plus_the_two_transit_ones() -> None:
    """溯源=真用过的表：主命盘八张在前、岁运两张在后，一张不多一张不少（spec §7.3）。"""
    tables = _default().provenance.tables
    assert [(table.name, table.source) for table in tables] == [
        *CONTENT_SOURCES,
        *TRANSIT_CONTENT_SOURCES,
    ]
    assert {table.version for table in tables} == {CONTENT_VERSION}
    assert _default().provenance.reference_date == _REFERENCE.isoformat()


def test_every_ledger_in_the_response_adds_up_to_its_own_value() -> None:
    """自洽门：从流年到账本、从流月到两层账本，Σ delta 都等于自己的 value。"""
    result = _transit(start_year=2026, end_year=2030, focus_year=2026)
    ledgers = [year.score for year in result.years] + [
        month.score for year in result.years if year.months for month in year.months
    ]
    assert len(ledgers) == 17  # 5 份年账本 + 聚焦年的 12 份月账本
    for score in ledgers:
        assert score.factors[0].rule == "transit.base"
        assert sum(factor.delta for factor in score.factors) == pytest.approx(score.value)
