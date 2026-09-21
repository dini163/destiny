"""神煞命中集与干支关系按查表手算锁定，防止表与引擎两处同时漂移。

期望值以计划开头"基准命 A"（戊辰 甲寅 庚子 丁亥）为主，逐条对应；其余各条
另引基准命（B 阴干、D 魁罡在非日柱、H 三合齐见、I 年月异局），命盘干支写在
各条 docstring 里，实施者可据此复核，而不是照抄一个数字。
"""

from datetime import date, time

from app.content.bazi_relations import transforming_element
from app.engines.bazi import compute_bazi_chart
from app.engines.bazi_rules import derive_branch_groups, derive_relations, derive_shensha
from app.schemas.common import Gender

CHART = compute_bazi_chart(
    birth_date=date(1988, 2, 15),
    birth_time=time(23, 30),
    longitude=104.1,
    gender=Gender.MALE,
    apply_true_solar_time=True,
)  # 戊辰 甲寅 庚子 丁亥


def _hits() -> list:
    return derive_shensha(CHART.pillars, day_master=CHART.day_master)


def _hit(name: str):
    return next(h for h in _hits() if h.name == name)


def test_yin_day_master_has_no_blade_to_look_up() -> None:
    """基准命 B（癸酉 癸亥 癸巳 丁巳）：五阴干无刃，羊刃表里没有癸这一键，不是漏查。"""
    chart_b = compute_bazi_chart(
        birth_date=date(1993, 11, 8),
        birth_time=time(9, 15),
        longitude=116.4,
        gender=Gender.MALE,
        apply_true_solar_time=True,
    )
    names = {h.name for h in derive_shensha(chart_b.pillars, day_master=chart_b.day_master)}
    assert "羊刃" not in names
    assert "天乙贵人" in names  # 癸→卯巳，命中日支巳；同一张表里的键不能一起少


def test_kuigang_looks_at_the_day_pillar_only() -> None:
    """基准命 D（庚午 戊寅 丙寅 壬辰）：时柱壬辰虽是魁罡四组之一，魁罡只论日柱。"""
    chart_d = compute_bazi_chart(
        birth_date=date(1990, 3, 2),
        birth_time=time(7, 40),
        longitude=113.3,
        gender=Gender.FEMALE,
        apply_true_solar_time=True,
    )
    names = {h.name for h in derive_shensha(chart_d.pillars, day_master=chart_d.day_master)}
    assert chart_d.pillars[3].gan + chart_d.pillars[3].zhi == "壬辰"
    assert "魁罡" not in names
    assert "月德贵人" in names  # 寅月属寅午戌局→丙，命中日干丙；收窄魁罡不该伤到别条


def test_eight_shensha_hit_the_base_chart() -> None:
    assert {h.name for h in _hits()} == {
        "天德贵人",
        "太极贵人",
        "文昌贵人",
        "华盖",
        "将星",
        "驿马",
        "亡神",
        "空亡",
    }
    # 全不命中：天乙(庚→丑未)、建禄(庚→申)、羊刃(庚→酉)、金舆(庚→戌)、
    # 咸池(申子辰→酉)、劫煞(申子辰→巳)、月德(寅午戌→丙，四干无丙)、魁罡(日柱庚子不在四组)。


def test_life_stage_is_not_repeated_as_a_shensha_row() -> None:
    """十二长生已经住在 BaziPillar.di_shi 里，神煞列表不再复读一遍。"""
    assert all(h.name != "十二长生" for h in _hits())
    assert CHART.pillars[1].di_shi  # 数据仍在柱上，只是不双份输出


def test_san_he_shensha_deduplicate_when_year_and_day_share_a_group() -> None:
    """华盖：年支辰与日支子同属申子辰局 → 目标辰，落点只剩年支辰一处。"""
    huagai = _hit("华盖")
    assert huagai.checked_from == "申子辰局"
    assert [(m.position, m.character, m.at) for m in huagai.matches] == [("year", "辰", "zhi")]


def test_tiande_matches_a_stem_and_records_which_side_it_hit() -> None:
    """寅月天德在丁；时干正是丁，故落点记到 (hour, gan)。"""
    tide = _hit("天德贵人")
    assert [(m.position, m.character, m.at) for m in tide.matches] == [("hour", "丁", "gan")]


def test_void_follows_the_day_pillar_cycle() -> None:
    """日柱庚子属甲午旬 → 空亡辰巳；命中年支辰。"""
    void = _hit("空亡")
    assert void.checked_from == "日柱庚子·甲午旬"
    assert [(m.position, m.character) for m in void.matches] == [("year", "辰")]


def test_binary_relations_of_the_base_chart() -> None:
    got = [(r.kind, r.pillar_a, r.pillar_b, r.strength) for r in derive_relations(CHART.pillars)]
    # 甲(月干)庚(日干) 天干相冲，柱距 1 → 紧临；寅亥六合为月支-时支（距 2 → 隔位）。
    # 寅亥 不报六破：破只取古籍四对，一对支不许既合又破（Task 4 实施记录）。
    assert got == [
        ("天干相冲", "month", "day", "紧临"),
        ("地支六合", "month", "hour", "隔位"),
    ]


def test_only_wuhe_carries_a_transforming_element() -> None:
    """六合在允许语料里没有化气五行，字段留空而不是补一个没出处的值。"""
    liuhe = next(r for r in derive_relations(CHART.pillars) if r.kind == "地支六合")
    assert liuhe.transforming_element is None
    assert transforming_element("天干五合", "甲", "己") == "土"  # 五合的化气有《论十干化气》


def test_half_combination_is_a_group_not_a_pair() -> None:
    """申子辰局见辰(年)、子(日)，含旺支子 → 半合水，is_complete=false。"""
    groups = derive_branch_groups(CHART.pillars)
    assert [(g.kind, g.element, g.is_complete) for g in groups] == [("半合", "水", False)]
    assert [(m.pillar, m.branch) for m in groups[0].members] == [("year", "辰"), ("day", "子")]
    assert [m.ten_god for m in groups[0].members] == ["偏印", "伤官"]  # 辰本气戊、子本气癸对庚
    assert "旺支" in groups[0].reading


def test_complete_group_suppresses_the_half_combination() -> None:
    """基准命 H（己巳 丁丑 癸酉 戊午）：巳酉丑三支齐见 → 只出三合，不再重复出半合。"""
    chart_h = compute_bazi_chart(
        birth_date=date(1990, 1, 8),
        birth_time=time(12, 0),
        longitude=116.4,
        gender=Gender.MALE,
        apply_true_solar_time=True,
    )
    groups = derive_branch_groups(chart_h.pillars)
    assert [(g.kind, g.element, g.is_complete) for g in groups] == [("三合", "金", True)]
    assert [m.branch for m in groups[0].members] == ["巳", "丑", "酉"]


def test_year_and_day_groups_are_both_recorded_in_checked_from() -> None:
    """基准命 I（己巳 丁丑 辛未 甲午）：年支起巳酉丑、日支起亥卯未，两局都要留在溯源里。"""
    chart_i = compute_bazi_chart(
        birth_date=date(1990, 1, 6),
        birth_time=time(12, 0),
        longitude=116.4,
        gender=Gender.MALE,
        apply_true_solar_time=True,
    )
    huagai = next(
        h
        for h in derive_shensha(chart_i.pillars, day_master=chart_i.day_master)
        if h.name == "华盖"
    )
    assert huagai.checked_from == "巳酉丑局、亥卯未局"
    # 巳酉丑之华盖在丑、亥卯未之华盖在未，两个落点各归一处，不合并成一团。
    assert [(m.position, m.character) for m in huagai.matches] == [("month", "丑"), ("day", "未")]
    san_hui = derive_branch_groups(chart_i.pillars)
    assert [(g.kind, g.element, [m.branch for m in g.members]) for g in san_hui] == [
        ("三会", "火", ["巳", "未", "午"])
    ]


def test_luck_pillar_joins_the_scan_for_fu_yin() -> None:
    """伏吟只有把大运干支喂进来才看得见（与年柱戊辰全同）。"""
    hits = derive_relations(CHART.pillars, extra_ganzhi=["戊辰"])
    fuyin = [r for r in hits if r.kind == "伏吟"]
    assert [(r.pillar_a, r.pillar_b, r.character_a) for r in fuyin] == [
        ("year", "extra0", "戊辰")
    ]
    # 柱位距离只有三档，大运落在四柱之外，比"远位"更远就是"远位"，不另立第四档。
    assert fuyin[0].strength == "远位"
