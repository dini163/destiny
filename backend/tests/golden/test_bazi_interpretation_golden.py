"""Golden pairing for the rebuilt judgment core (spec §9.2).

Every expected value below is transcribed from the plan section
"基准命与对拍命例", which carries the arithmetic for each figure. The four
pillars themselves come from lunar-python through the production engine, so a
calendar drift can never hide behind a rule change.
"""

from datetime import date, time

import pytest

from app.content.bazi_dimensions import (
    DIMENSION_ORDER, DIMENSION_RULES, DIMENSION_RULE_COUNT, dim_rule,
)
from app.content.bazi_geju import GEJU_COUNT, GEJU_RULES
from app.content.bazi_nayin import NAYIN_COUNT, NAYIN_MEANING
from app.content.bazi_plain import DIMENSION_OPENERS, PLAIN_READINGS, TIER_CLOSERS
from app.content.bazi_relations import RELATION_COUNT, RELATION_TABLES
from app.content.bazi_shensha import SHENSHA_COUNT, SHENSHA_RULES
from app.content.bazi_shishen import TEN_GOD_COUNT, TEN_GOD_MEANING
from app.core.provenance import MODEL_PARAM_SOURCE
from app.engines.bazi import compute_bazi_chart
from app.engines.bazi_interpret import TEN_GOD_GROUPS, interpret_chart
from app.engines.bazi_rules import derive_branch_groups, derive_relations, derive_shensha
from app.engines.bazi_strength import assess_strength, detect_geju, element_weight_scores
from app.engines.bazi_yongshen import select_yongshen
from app.schemas.common import Gender

BOOKS = ("《渊海子平", "《三命通会", "《滴天髓", "《协纪辨方书")  # 出处到章，故只比书名前缀
CITABLE_TABLES = {
    "十神": list(TEN_GOD_MEANING.values()),
    "纳音": list(NAYIN_MEANING.values()),
    "神煞": list(SHENSHA_RULES.values()),
    "关系": list(RELATION_TABLES.values()),
    "格局": list(GEJU_RULES.values()),
}


def _chart(case: dict):
    return compute_bazi_chart(
        birth_date=case["birth_date"], birth_time=case["birth_time"],
        longitude=case["longitude"], gender=case["gender"], apply_true_solar_time=True,
    )


def _bundle(case: dict):
    """API 装配的同一串调用，golden 直接走引擎，绕开 HTTP 层。"""
    chart = _chart(case)
    pillars = chart.pillars
    strength = assess_strength(pillars)
    geju = detect_geju(pillars)
    yongshen = select_yongshen(
        level=strength.level, day_master_element=pillars[2].gan_element,
        month_zhi=pillars[1].zhi, element_scores=element_weight_scores(pillars),
    )
    shensha = derive_shensha(pillars, day_master=chart.day_master)
    relations = derive_relations(pillars)
    groups = derive_branch_groups(pillars)
    return {
        "strength": strength,
        "geju": geju,
        "yongshen": yongshen,
        "shensha": shensha,
        "relations": relations,
        "groups": groups,
        "interpretation": interpret_chart(
            pillars, gender=case["gender"], strength=strength, geju=geju, yongshen=yongshen,
            shensha=shensha, relations=relations, branch_groups=groups,
        ),
    }


CASES: dict[str, dict] = {
    "A_yang_male_forward": dict(
        birth_date=date(1988, 2, 15), birth_time=time(23, 30), longitude=104.1,
        gender=Gender.MALE,
        pillars="戊辰 甲寅 庚子 丁亥", level="weak", score=25.85,
        factors=(30.0, 17.95, 33.33), geju=("偏财格", True),
        favourable=["土", "金"], unfavourable=["木", "水", "火"],
        shensha={"天德贵人", "太极贵人", "文昌贵人", "华盖", "将星", "驿马", "亡神", "空亡"},
        relations={("天干相冲", "month", "day"), ("地支六合", "month", "hour")},
        groups={("半合", False)},
    ),
    "B_yin_male_backward": dict(
        birth_date=date(1993, 11, 8), birth_time=time(9, 15), longitude=116.4,
        gender=Gender.MALE,
        pillars="癸酉 癸亥 癸巳 丁巳", level="strong", score=75.90,
        factors=(100.0, 56.41, 66.67), geju=("伤官格", True),
        favourable=["火", "木", "土"], unfavourable=["水", "金"],
        shensha={"天乙贵人", "太极贵人", "将星", "驿马"},
        relations={("天干相冲", "day", "hour"), ("天干相冲", "month", "hour"),
                   ("天干相冲", "year", "hour"), ("地支六冲", "month", "day"),
                   ("地支六冲", "month", "hour"), ("反吟", "month", "hour")},
        groups={("半合", False)},
    ),
    "C_chen_month_mixed_qi": dict(
        birth_date=date(1988, 4, 20), birth_time=time(14, 0), longitude=121.5,
        gender=Gender.MALE,
        pillars="戊辰 丙辰 乙巳 癸未", level="weak", score=27.67,
        factors=(30.0, 22.50, 33.33), geju=("正财格", False),  # 丙是伤官，不在正财格的食神/正官之助里
        favourable=["木", "水"], unfavourable=["土", "火", "金"],
        shensha={"华盖", "劫煞", "金舆"},
        relations={("自刑", "year", "month"), ("天干五合", "year", "hour")},
        groups=set(),
    ),
    "D_yang_female_backward": dict(
        birth_date=date(1990, 3, 2), birth_time=time(7, 40), longitude=113.3,
        gender=Gender.FEMALE,
        pillars="庚午 戊寅 丙寅 壬辰", level="balanced", score=57.69,
        factors=(75.0, 69.23, 0.0), geju=("偏印格", False),
        favourable=[], unfavourable=[],
        shensha={"月德贵人", "羊刃", "将星"},
        relations={("天干相冲", "day", "hour")},
        groups={("半合", False)},
    ),
    "E_chou_month_tongguan": dict(
        birth_date=date(1979, 1, 15), birth_time=time(6, 30), longitude=104.1,
        gender=Gender.MALE,
        pillars="戊午 乙丑 壬午 癸卯", level="weak", score=16.88,
        factors=(15.0, 10.53, 33.33), geju=("正官格", False),
        favourable=["水", "金"], unfavourable=["土", "木", "火"],
        shensha={"天乙贵人", "咸池", "金舆", "将星"},
        relations={("地支六害", "year", "month"), ("地支六害", "month", "day"),
                   ("地支六破", "day", "hour"), ("地支六破", "year", "hour"),
                   ("自刑", "year", "day"), ("天干五合", "year", "hour")},
        groups=set(),
    ),
    "F_mao_month_yang_ren": dict(
        birth_date=date(1988, 3, 10), birth_time=time(10, 0), longitude=120.0,
        gender=Gender.MALE,
        pillars="戊辰 乙卯 甲子 己巳", level="strong", score=70.67,
        factors=(100.0, 60.0, 33.33), geju=("月刃格", False),
        favourable=["土", "火", "金"], unfavourable=["木", "水"],
        shensha={"月德贵人", "羊刃", "太极贵人", "文昌贵人", "金舆", "华盖", "将星", "劫煞"},
        relations={("地支六害", "year", "month"), ("无礼之刑", "month", "day"),
                   ("天干五合", "day", "hour")},
        groups={("半合", False)},
    ),
}


@pytest.mark.parametrize("name", sorted(CASES))
def test_four_pillars_match_lunar_python(name: str) -> None:
    assert _chart(CASES[name]).four_pillars == CASES[name]["pillars"]


@pytest.mark.parametrize("name", sorted(CASES))
def test_strength_ledger_and_band(name: str) -> None:
    case, bundle = CASES[name], _bundle(CASES[name])
    strength = bundle["strength"]
    assert (strength.level, round(strength.score.value, 2)) == (case["level"], case["score"])
    assert (round(strength.deling, 2), round(strength.dedi, 2),
            round(strength.deshi, 2)) == case["factors"]
    # 账本闭合：value 是 Σ delta 四舍五入到"分"的结果，故差不得超过半个分。
    assert sum(f.delta for f in strength.score.factors) == pytest.approx(
        strength.score.value, abs=0.005
    )


@pytest.mark.parametrize("name", sorted(CASES))
def test_structure_and_verdict(name: str) -> None:
    case, bundle = CASES[name], _bundle(CASES[name])
    assert (bundle["geju"].name, bundle["geju"].is_success) == case["geju"]
    assert all("《" in note for note in bundle["geju"].notes)   # 判语逐条带出处


@pytest.mark.parametrize("name", sorted(CASES))
def test_useful_god_merge_is_reproducible(name: str) -> None:
    case, yongshen = CASES[name], _bundle(CASES[name])["yongshen"]
    assert yongshen.favorable_elements == case["favourable"]
    assert yongshen.unfavorable_elements == case["unfavourable"]
    assert yongshen.conflict is None            # 六例都不产生冲突（§基准命 已说明）
    assert [m.method for m in yongshen.methods] == ["扶抑", "通关", "调候"]   # 三法恒有记录


@pytest.mark.parametrize("name", sorted(CASES))
def test_shensha_relation_and_group_hits(name: str) -> None:
    case, bundle = CASES[name], _bundle(CASES[name])
    assert {entry.name for entry in bundle["shensha"]} == case["shensha"]
    assert {(r.kind, r.pillar_a, r.pillar_b) for r in bundle["relations"]} == case["relations"]
    assert {(g.kind, g.is_complete) for g in bundle["groups"]} == case["groups"]


_KEYS_BY_DIMENSION = {name: {rule.key for rule in rules} for name, rules in DIMENSION_RULES.items()}


def _fired_keys(reading) -> list[str]:
    """账本里属于该维规则表的键（基准项 `.base` 与 `score.clamped` 不在表内）。"""
    known = _KEYS_BY_DIMENSION[reading.dimension]
    return [factor.rule for factor in reading.score.factors if factor.rule in known]


@pytest.mark.parametrize("name", sorted(CASES))
def test_six_dimensions_stay_self_consistent(name: str) -> None:
    bundle = _bundle(CASES[name])
    readings = bundle["interpretation"].six_dimensions
    assert [r.dimension for r in readings] == list(DIMENSION_ORDER)
    for reading in readings:
        deltas = [factor.delta for factor in reading.score.factors]
        assert sum(deltas) == pytest.approx(reading.score.value, abs=0.05)
        assert reading.score.factors[0].rule.endswith(".base")   # 账本首项恒为基准项
        value = reading.score.value
        expected = "顺" if value >= 65 else "平" if value >= 45 else "滞"   # 独立复算 §6.4 分界
        assert reading.score.tier == expected, (name, reading.dimension, value)
        fired = [dim_rule(k).reading for k in _fired_keys(reading)]
        assert reading.narrative == "；".join(fired) + "。"
        prefix = DIMENSION_RULES[reading.dimension][0].key.split(".", maxsplit=1)[0]
        fired = _fired_keys(reading)
        assert reading.plain == "\n".join(
            [DIMENSION_OPENERS[prefix],
             *[PLAIN_READINGS[k] for k in fired if dim_rule(k).delta > 0],
             *[PLAIN_READINGS[k] for k in fired if dim_rule(k).delta < 0],
             TIER_CLOSERS[reading.score.tier]]
        )
        assert reading.source == MODEL_PARAM_SOURCE          # 六维 delta 不许伪装成古籍赋分
        assert all(factor.source == MODEL_PARAM_SOURCE for factor in reading.score.factors)
    assert bundle["interpretation"].summary == "、".join(
        f"{r.dimension}{r.score.tier}" for r in readings
    )


def test_mutually_exclusive_rules_never_both_fire() -> None:
    """同一维度的互斥对（如 事业 的喜/忌两侧、婚姻 宫位的成/破）不得同时命中。"""
    for name in sorted(CASES):
        readings = _bundle(CASES[name])["interpretation"].six_dimensions
        keys = {reading.dimension: set(_fired_keys(reading)) for reading in readings}
        assert not ({"career.officer.favourable", "career.officer.unfavourable"} <= keys["事业"])
        assert not ({"marriage.palace.intact", "marriage.palace.clashed"} <= keys["婚姻"])


def test_ten_god_groups_cover_the_corpus() -> None:
    """Task 9 的英文分组必须与十神语料同源：少一个神，六维就漏判一类星。"""
    assert {god for members in TEN_GOD_GROUPS.values() for god in members} == set(TEN_GOD_MEANING)


def test_corpus_cardinality_is_frozen() -> None:
    """spec §9.1 的固定条数：改表必须同时改这里，否则 CI 红。"""
    assert TEN_GOD_COUNT == 10
    assert NAYIN_COUNT == 30          # 60 个纳音名 → 30 组释义
    assert SHENSHA_COUNT == 17
    assert RELATION_COUNT == 15       # 三刑算四条、三合/半合/三会各一条（spec §9.1）
    assert GEJU_COUNT == 10           # 八正格 + 建禄 + 月刃
    assert DIMENSION_RULE_COUNT == 39
    assert len(DIMENSION_RULES) == len(DIMENSION_ORDER) == 6


def test_every_citable_entry_names_an_allowed_source() -> None:
    """四本公版书之外不许有出处：一处扫完，改表时只红一个测试。"""
    for table, entries in CITABLE_TABLES.items():
        assert entries, table
        for entry in entries:
            assert any(entry.source.startswith(book) for book in BOOKS), (table, entry)


def test_plain_summary_restates_the_tiers_without_new_verdicts() -> None:
    """总论只许是 `summary` 的套壳：白话层不借总论偷偷加判断。"""
    for name in sorted(CASES):
        interp = _bundle(CASES[name])["interpretation"]
        assert interp.summary in interp.plain_summary
        assert interp.plain_summary.count("\n") == 0
