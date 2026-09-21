"""神煞查表的契约：基数、两轴取法与释义非空。

表的数值逐条转录自《三命通会》《渊海子平》；这里钉的是"漏一项、少一干、
把查表轴写反"这类错误，它们不会让排盘报错，只会让某条神煞静默不现。
"""

import pytest

from app.content.bazi_shensha import SHENSHA_COUNT, SHENSHA_RULES, san_he_group, shen_sha_rule

# 出处写到章，所以前缀不含右书名号 —— 只认得书。
SOURCES = ("《渊海子平", "《三命通会", "《滴天髓", "《协纪辨方书")
BRANCHES = "子丑寅卯辰巳午未申酉戌亥"

SAN_HE_KEYS = {"申子辰", "亥卯未", "寅午戌", "巳酉丑"}


def _advance(zhi: str, steps: int) -> str:
    return BRANCHES[(BRANCHES.index(zhi) + steps) % 12]


def test_shensha_table_has_the_declared_cardinality() -> None:
    assert SHENSHA_COUNT == 17
    assert {name for name, rule in SHENSHA_RULES.items() if not rule.meaning} == set()


def test_every_shensha_is_citable_to_the_allowed_corpus() -> None:
    for entry in SHENSHA_RULES.values():
        assert any(entry.source.startswith(prefix) for prefix in SOURCES), entry


def test_lookup_and_target_axes_are_declared_for_every_shensha() -> None:
    """天德以月支查、查出来是天干；咸池以三合局查、查出来是地支 —— 两轴必须各自明确。"""
    assert shen_sha_rule("天乙贵人").lookup == "day_gan"
    assert shen_sha_rule("天乙贵人").target == "zhi"
    assert shen_sha_rule("天德贵人").lookup == "month_zhi"
    assert shen_sha_rule("天德贵人").target == "gan_or_zhi"
    assert shen_sha_rule("月德贵人").lookup == "month_zhi_group"
    assert shen_sha_rule("月德贵人").target == "gan"
    assert shen_sha_rule("亡神").lookup == "year_and_day_group"
    assert shen_sha_rule("魁罡").lookup == "day_pillar" and shen_sha_rule("魁罡").target == "pillar"
    assert shen_sha_rule("空亡").lookup == "void"
    assert shen_sha_rule("十二长生").lookup == "life_stage"


def test_wen_chang_table_covers_all_ten_stems() -> None:
    assert len(shen_sha_rule("文昌贵人").table) == 10
    assert shen_sha_rule("文昌贵人").table["庚"] == ("亥",)


def test_yangren_only_has_yang_stems() -> None:
    assert set(shen_sha_rule("羊刃").table) == {"甲", "丙", "戊", "庚", "壬"}


def test_lu_qian_chen_shensha_share_the_lu_table() -> None:
    """建禄/羊刃/金舆/文昌都是"禄表 ± n 辰"，四表必须互相咬合，改一处就要一起改。"""
    lu = shen_sha_rule("建禄").table
    yang = set(shen_sha_rule("羊刃").table)
    for gan in lu:
        assert _advance(lu[gan][0], 2) == shen_sha_rule("金舆").table[gan][0]      # 禄前二辰
        assert _advance(lu[gan][0], 3) == shen_sha_rule("文昌贵人").table[gan][0]  # 禄前第三辰
        if gan in yang:                                                            # 五阴干无刃
            assert _advance(lu[gan][0], 1) == shen_sha_rule("羊刃").table[gan][0]  # 禄前一辰


def test_table_cardinalities_match_the_spec_inventory() -> None:
    """spec §9.1 逐项数过：十干表五张、十二月表一张、四局表七张、四柱表一张。"""
    for name in ("天乙贵人", "文昌贵人", "太极贵人", "建禄", "金舆"):
        assert len(shen_sha_rule(name).table) == 10, name
    assert len(shen_sha_rule("天德贵人").table) == 12
    for name in ("月德贵人", "咸池", "驿马", "华盖", "将星", "劫煞", "亡神"):
        assert set(shen_sha_rule(name).table) == SAN_HE_KEYS, name
    assert len(shen_sha_rule("魁罡").table) == 4
    # 空亡沿用 LunarUtil.XUN_KONG、十二长生沿用 BaziPillar.di_shi，两处都不自带表。
    assert shen_sha_rule("空亡").table == {} and shen_sha_rule("十二长生").table == {}


def test_life_stage_is_not_emitted_as_a_shensha_hit() -> None:
    """十二长生进表只为给 UI 一处取释义，命中行由 BaziPillar.di_shi 承担，不重复一遍。"""
    assert shen_sha_rule("十二长生").target == "none"
    assert "不作神煞命中" in shen_sha_rule("十二长生").meaning


def test_san_he_group_resolves_every_branch() -> None:
    assert san_he_group("子") == "申子辰"
    assert san_he_group("卯") == "亥卯未"
    assert {san_he_group(z) for z in BRANCHES} == SAN_HE_KEYS


def test_unknown_shensha_raises() -> None:
    with pytest.raises(KeyError):
        shen_sha_rule("天狗")
