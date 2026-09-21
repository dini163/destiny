"""格局判定与藏干权重账本（spec §6.1、§6.4）。

判格条件全部来自 `app/content/bazi_geju.py` 的署名条目，因此本文件锁的是
"哪一格、成不成、引用了哪一句"，而不是措辞；每句判语的署名都必须在 `GEJU_SOURCES`
白名单内（引他章可以、自造章名不行），每格至少署一次自己的主章（spec §3 决策二）。
"""

import re
from datetime import date, time

from app.content.bazi_geju import GEJU_COUNT, GEJU_RULES, GEJU_SOURCES, geju_rule
from app.engines.bazi import compute_bazi_chart
from app.engines.bazi_strength import detect_geju, geju_verdict, hidden_stem_ledger
from app.schemas.common import Gender
from app.schemas.scoring import MODEL_PARAM_SOURCE


def _chart(y, m, d, hh, mm, longitude, gender=Gender.MALE):
    return compute_bazi_chart(
        birth_date=date(y, m, d), birth_time=time(hh, mm), longitude=longitude,
        gender=gender, apply_true_solar_time=True,
    )


# 基准命 A：戊辰 甲寅 庚子 丁亥（1988-02-15 23:30 @104.1E）
CHART_A = _chart(1988, 2, 15, 23, 30, 104.1)
# 基准命 D：庚午 戊寅 丙寅 壬辰（1990-03-02 07:40 @113.3E，坤造·偏印格·财透破印）
CHART_D = _chart(1990, 3, 2, 7, 40, 113.3, Gender.FEMALE)
# 基准命 F：戊辰 乙卯 甲子 己巳（1988-03-10 10:00 @120E，阳干卯月）
CHART_F = _chart(1988, 3, 10, 10, 0, 120.0)
# 对拍命 G：戊辰 乙卯 乙丑 辛巳（1988-03-11 10:00 @120E，阴干卯月）
CHART_G = _chart(1988, 3, 11, 10, 0, 120.0)


def test_month_branch_main_qi_sets_the_structure() -> None:
    """寅 hides 甲丙戊; 甲 is 庚's 偏财 → 偏财格, 时干丁(正官)为成格之助."""
    geju = detect_geju(CHART_A.pillars)
    assert (geju.name, geju.ten_god, geju.from_pillar) == ("偏财格", "偏财", "month")
    assert geju.is_success is True
    assert geju.notes == [geju_rule("偏财格").supporting["正官"]]
    assert geju.source == geju_rule("偏财格").source


def test_parallel_main_qi_falls_through_to_the_next_layer() -> None:
    """基准命 B 亥藏壬甲; 壬是癸的劫财 → 退取中气甲（伤官）→ 伤官格."""
    chart_b = _chart(1993, 11, 8, 9, 15, 116.4)
    assert detect_geju(chart_b.pillars).name == "伤官格"


def test_yang_day_master_in_its_blade_branch_is_yue_ren() -> None:
    """甲 day in 卯 month: 卯 only hides 乙(劫财), 卯是甲之刃（甲禄在寅、刃在卯）→ 月刃格."""
    assert detect_geju(CHART_F.pillars).name == "月刃格"


def test_yin_day_master_in_its_lu_branch_is_jian_lu() -> None:
    """乙 day in 卯 month: 阴干无刃, 卯是乙之禄 → 建禄格. 与上一例只差日干阴阳."""
    assert detect_geju(CHART_G.pillars).name == "建禄格"


def test_breaking_outweighs_supporting_in_the_same_chart() -> None:
    """基准命 D 偏印格：壬(七杀)是成格之助，庚(偏财)是破格之由 → 记破，notes 只留破格句."""
    rule = geju_rule("偏印格")
    assert "七杀" in rule.supporting and "偏财" in rule.breaking
    geju = detect_geju(CHART_D.pillars)
    assert (geju.name, geju.is_success) == ("偏印格", False)
    assert geju.notes == [rule.breaking["偏财"]]
    assert set(geju.notes).isdisjoint(rule.supporting.values())


def test_breaking_notes_follow_pillar_order() -> None:
    """基准命 F 月刃格：年戊(偏财)、时己(正财)皆破刃之财 → 两条并按柱序，不合并."""
    rule = geju_rule("月刃格")
    geju = detect_geju(CHART_F.pillars)
    assert geju.is_success is False
    assert geju.notes == [rule.breaking["偏财"], rule.breaking["正财"]]


def test_verdict_reports_the_unsupported_reading_when_nothing_is_transparent() -> None:
    """无破亦无助时不成格，并给出该格自己的判语 —— 不默认成格."""
    is_success, notes = geju_verdict(geju_rule("正官格"), ["比肩"])
    assert is_success is False
    assert notes == [geju_rule("正官格").unsupported]


def _citations(sentence: str) -> list[str]:
    """句内署名（允许"引《篇》"式的次级出处），出处到章不到书。"""
    return re.findall(r"（(《[^》]+》[^（）]*)）", sentence)


def _chapter(citation: str) -> str:
    return citation.split("引")[0] if "引" in citation else citation


def test_every_structure_has_the_declared_verdict_shape() -> None:
    assert GEJU_COUNT == 10
    assert set(GEJU_RULES) == {
        "正官格", "七杀格", "正印格", "偏印格", "食神格",
        "伤官格", "正财格", "偏财格", "建禄格", "月刃格",
    }
    all_gods = {
        "比肩", "劫财", "食神", "伤官", "偏财", "正财", "七杀", "正官", "偏印", "正印",
    }
    for rule in GEJU_RULES.values():
        assert rule.reading and rule.source
        assert set(rule.supporting) | set(rule.breaking) <= all_gods
        assert set(rule.supporting) & set(rule.breaking) == set()
        # 判语整句来自语料：白话在前、原句在『』内、篇名署名在后，引擎不组句。
        for sentence in [*rule.supporting.values(), *rule.breaking.values(), rule.unsupported]:
            assert "『" in sentence and "』" in sentence, sentence
        # 署名一律在白名单内（引他章可以，凭空写一章不行），且该格至少署一次自己的主章。
        sentences = [
            rule.reading, rule.unsupported, *rule.supporting.values(), *rule.breaking.values()
        ]
        cited = {c for sentence in sentences for c in _citations(sentence)}
        assert cited, rule.name
        assert all(c in GEJU_SOURCES or _chapter(c) in GEJU_SOURCES for c in cited), (
            rule.name,
            cited - GEJU_SOURCES,
        )
        assert any(_chapter(c) == rule.source for c in cited), (rule.name, rule.source, cited)


def test_hidden_stem_ledger_uses_declared_weights() -> None:
    """辰 hides 戊乙癸 -> 0.6 / 0.3 / 0.1, tagged 本气/中气/余气."""
    rows = [row for row in hidden_stem_ledger(CHART_A.pillars) if row.position == "year"]
    assert [(row.stem, row.role, row.weight) for row in rows] == [
        ("戊", "本气", 0.6), ("乙", "中气", 0.3), ("癸", "余气", 0.1),
    ]
    assert [row.ten_god for row in rows] == ["偏印", "正财", "伤官"]
    assert all(row.source == MODEL_PARAM_SOURCE for row in rows)


def test_two_stem_branch_has_no_residual_qi() -> None:
    """亥 hides 壬甲 only -> 本气/中气, weights 0.6/0.3（余气位在两支藏干里不存在）."""
    rows = [row for row in hidden_stem_ledger(CHART_A.pillars) if row.position == "hour"]
    assert [(row.stem, row.role, row.weight) for row in rows] == [
        ("壬", "本气", 0.6), ("甲", "中气", 0.3),
    ]


def test_single_hidden_stem_is_recorded_as_main_qi() -> None:
    rows = [row for row in hidden_stem_ledger(CHART_A.pillars) if row.position == "day"]
    assert [(row.stem, row.role, row.weight) for row in rows] == [("癸", "本气", 1.0)]


def test_ledger_covers_every_branch_of_the_chart() -> None:
    """四柱共 11 个藏干（寅3 辰3 子1 亥2 加…）—— 行数即藏干总数，不重不漏."""
    rows = hidden_stem_ledger(CHART_A.pillars)
    total = sum(len(pillar.hidden_stems) for pillar in CHART_A.pillars)
    assert len(rows) == total == 9
    assert [row.position for row in rows][:3] == ["year", "year", "year"]
