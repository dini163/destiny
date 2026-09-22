"""岁运规则表不变式（spec §9.3）：数量、键序、符号与语义一致、粒度域、署名。"""

import pytest

from app.content.bazi_shensha import SHENSHA_RULES
from app.content.bazi_transit_rules import (
    TRANSIT_BASE,
    TRANSIT_FAMILIES,
    TRANSIT_RULES,
    TRANSIT_RULE_COUNT,
    TRANSIT_RULE_SOURCE,
    transit_rule,
)

_COUNTS_BY_FAMILY = {
    "yongshen": 4,
    "taisui": 6,
    "palace": 8,
    "heyue": 6,
    "ganzhi": 2,
    "fuyin": 2,
    "dayun": 5,
    "dishi": 3,
    "shensha": 10,
}
#: 太岁只论年支、大运只与流年论生克，这两族不参与流月（spec §6.2）。
_YEAR_ONLY = frozenset({"taisui", "dayun"})


def test_the_table_has_46_rows_in_9_families() -> None:
    assert TRANSIT_RULE_COUNT == 46 == len(TRANSIT_RULES)
    assert sum(_COUNTS_BY_FAMILY.values()) == TRANSIT_RULE_COUNT  # 族计数不许自相矛盾
    assert {rule.family for rule in TRANSIT_RULES.values()} == set(_COUNTS_BY_FAMILY)
    assert TRANSIT_FAMILIES == tuple(_COUNTS_BY_FAMILY)


def test_keys_are_unique_and_prefixed_by_their_family() -> None:
    for key, rule in TRANSIT_RULES.items():
        assert key == rule.key
        assert key.split(".")[0] == rule.family, key


def test_every_family_row_count_matches_the_table() -> None:
    for family, expected in _COUNTS_BY_FAMILY.items():
        assert len([r for r in TRANSIT_RULES.values() if r.family == family]) == expected, family


def test_deltas_are_nonzero_and_within_the_band() -> None:
    for rule in TRANSIT_RULES.values():
        assert rule.delta != 0.0, rule.key
        assert -10.0 <= rule.delta <= 10.0, rule.key


def test_both_signs_are_represented() -> None:
    assert any(r.delta > 0 for r in TRANSIT_RULES.values())
    assert any(r.delta < 0 for r in TRANSIT_RULES.values())


def test_signs_follow_the_cited_quality_and_semantics() -> None:
    """符号与语义一致：防"手滑填反"。逐族按各自的命名规矩核，不靠整表一个式子糊过去。"""
    for rule in TRANSIT_RULES.values():
        tail = rule.key.split(".")[1]
        if rule.family == "shensha":
            quality = SHENSHA_RULES[rule.label].quality  # label 即神煞名，两处同源
            assert (rule.delta > 0) is (quality == "吉"), f"{rule.key} 标 {quality}"
        elif rule.family == "taisui":
            assert (rule.delta > 0) is (tail == "combine"), rule.key
        elif rule.family == "palace":
            assert (rule.delta > 0) is tail.startswith("combine_"), rule.key
        elif rule.family in {"yongshen", "heyue"}:
            # `unfavourable` 自身以 `favourable` 结尾，只能反向判。
            assert (rule.delta > 0) is not tail.endswith("_unfavourable"), rule.key
        elif rule.family == "ganzhi":
            assert (rule.delta > 0) is (tail == "combine_day_master"), rule.key
        else:  # fuyin / dayun / dishi 的向背各自成组，见下面三条
            continue


def test_fuyin_and_dayun_signs_match_their_meaning() -> None:
    """这两族的名词是音译（伏吟/反吟/并临本无英文对应），键随术语而非风格。"""
    assert TRANSIT_RULES["fuyin.fuyin"].delta < 0  # 伏吟
    assert TRANSIT_RULES["fuyin.fanyin"].delta < 0  # 反吟
    assert TRANSIT_RULES["dayun.binglin"].delta < 0  # 岁运并临
    assert TRANSIT_RULES["dayun.fanyin"].delta < 0  # 运年反吟
    assert TRANSIT_RULES["dayun.yun_sheng_sui"].delta > 0
    assert TRANSIT_RULES["dayun.sui_sheng_yun"].delta > 0
    assert TRANSIT_RULES["dayun.gan_he"].delta > 0


def test_dishi_family_has_exactly_one_row_per_band() -> None:
    """旺、生、衰三段各一行，沐浴不定价（一书两说，只在 di_shi 呈现）。"""
    rows = [r for r in TRANSIT_RULES.values() if r.family == "dishi"]
    assert [r.key for r in rows] == ["dishi.prosperous", "dishi.supportive", "dishi.decaying"]
    assert [r.delta for r in rows] == [7.0, 4.0, -6.0]


def test_shensha_rows_are_the_priced_ten_and_no_neutral_one() -> None:
    priced = {r.label for r in TRANSIT_RULES.values() if r.family == "shensha"}
    assert priced <= set(SHENSHA_RULES)
    assert {
        name for name, rule in SHENSHA_RULES.items() if rule.quality in {"吉", "凶"}
    } == priced, "中性神煞不许出现在账本里，吉凶则一条不能漏"


def test_the_hour_scope_shadows_the_day_scope_exactly() -> None:
    """粒度取值只能来自受控词表，而「论月者必论日、论日者必论时、只论年者三者不论」是切片 4 换的轴。

    末行是换轴后新增的、更严的一条：谁给某条偷偷只加 `"shi"`（想让某个时辰单走一条规则），
    当场红。
    """
    for rule in TRANSIT_RULES.values():
        assert set(rule.scopes) <= {"sui", "yue", "ri", "shi"}, rule.key
        assert ("yue" in rule.scopes) is (rule.family not in _YEAR_ONLY), rule.key
        assert ("ri" in rule.scopes) == ("yue" in rule.scopes), rule.key
        assert ("shi" in rule.scopes) == ("ri" in rule.scopes), rule.key


def test_the_shi_scope_covers_the_same_rows_as_the_ri_scope() -> None:
    """35 条可落时段，且可落时段者与可落日段者是同一批键（spec §6.2）。

    与下面那条计数测的分工：那条钉"日"的 35/11 划分，这条钉"时 == 日"的集合相等，
    于是太岁 6 + 大运 5 不论时不需要再数一遍（切片 4 spec §9.4）。
    """
    with_shi = {rule.key for rule in TRANSIT_RULES.values() if "shi" in rule.scopes}
    with_ri = {rule.key for rule in TRANSIT_RULES.values() if "ri" in rule.scopes}
    assert len(with_shi) == 35
    assert with_shi == with_ri


def test_the_ri_scope_covers_exactly_the_thirty_five_portable_rows() -> None:
    """35 条岁、月、日通用，11 条（太岁 6 + 大运 5）只论年（spec §6.2）。"""
    with_ri = [rule for rule in TRANSIT_RULES.values() if "ri" in rule.scopes]
    assert len(with_ri) == 35
    assert {rule.family for rule in with_ri} == {
        "yongshen", "palace", "heyue", "ganzhi", "fuyin", "dishi", "shensha",
    }
    assert [rule.family for rule in TRANSIT_RULES.values() if "ri" not in rule.scopes] == [
        "taisui", "taisui", "taisui", "taisui", "taisui", "taisui",
        "dayun", "dayun", "dayun", "dayun", "dayun",
    ]


def test_readings_carry_a_single_clause_and_a_signature() -> None:
    for rule in TRANSIT_RULES.values():
        assert rule.reading.endswith("）"), rule.key
        assert not rule.reading.rstrip("）").endswith(("。", "；")), rule.key
        assert "《" in rule.reading or "本系统" in rule.reading, rule.key


def test_labels_are_non_empty_and_distinct_within_a_family() -> None:
    for rule in TRANSIT_RULES.values():
        assert rule.label, rule.key
    for family in TRANSIT_FAMILIES:
        labels = [r.label for r in TRANSIT_RULES.values() if r.family == family]
        assert len(labels) == len(set(labels)), family


def test_transit_rule_looks_up_by_key_and_rejects_strangers() -> None:
    assert transit_rule("taisui.chong") is TRANSIT_RULES["taisui.chong"]
    with pytest.raises(KeyError, match="Unknown transit rule"):
        transit_rule("taisui.不存在")


def test_pricing_is_declared_as_model_parameters() -> None:
    assert "模型参数" in TRANSIT_RULE_SOURCE
    assert TRANSIT_BASE == 50.0


def test_transit_sources_stay_out_of_the_natal_provenance() -> None:
    """`CONTENT_SOURCES` 被八字引擎整表回显进每一个 `/natal` 响应；岁运两表必须分列。"""
    from app.content import CONTENT_SOURCES, TRANSIT_CONTENT_SOURCES

    assert [name for name, _ in TRANSIT_CONTENT_SOURCES] == [
        "bazi_changsheng",
        "bazi_transit_rules",
    ]
    assert {name for name, _ in TRANSIT_CONTENT_SOURCES}.isdisjoint(
        {name for name, _ in CONTENT_SOURCES}
    )
