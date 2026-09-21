"""干支关系表的契约：基数、双向登记、合化目标的有无。

`pairs` 是无向表，引擎按 `(a, b) in pairs` 查，只写一个方向就会静默漏掉一半命中 ——
这是本轮最容易写错、也最难在页面上看出来的地方，所以用不变式守，而不是靠数。
"""

import pytest

from app.content.bazi_relations import (
    RELATION_COUNT,
    RELATION_TABLES,
    relation_pairs,
    transforming_element,
)

# 出处写到章，所以前缀不含右书名号 —— 只认得书。
SOURCES = ("《渊海子平", "《三命通会", "《滴天髓", "《协纪辨方书")
GROUP_KEYS = {"申子辰", "亥卯未", "寅午戌", "巳酉丑"}
SAN_HUI_KEYS = {"寅卯辰", "巳午未", "申酉戌", "亥子丑"}


def test_relation_table_has_the_declared_cardinality() -> None:
    assert RELATION_COUNT == 15
    assert {key for key, rule in RELATION_TABLES.items() if rule.kind != key} == set()


def test_every_relation_is_citable_to_the_allowed_corpus() -> None:
    for entry in RELATION_TABLES.values():
        assert any(entry.source.startswith(prefix) for prefix in SOURCES), entry


def test_relation_pairs_are_registered_in_both_directions() -> None:
    for key, rule in RELATION_TABLES.items():
        if rule.scope not in ("stem", "branch"):
            continue
        for a, b in rule.pairs:
            assert (b, a) in rule.pairs, f"{key} 缺反向 ({b}, {a})"


def test_zhi_chong_pairs_are_the_six_classical_pairs() -> None:
    assert relation_pairs("地支六冲") >= {("子", "午"), ("午", "子"), ("巳", "亥"), ("亥", "巳")}
    assert len({frozenset(pair) for pair in relation_pairs("地支六冲")}) == 6


def test_zhi_po_drops_the_pairs_the_classic_refuses() -> None:
    """《三命通会·卷三》只立四对，并明言寅申巳亥"原破，却三合，故不取"。"""
    assert relation_pairs("地支六破") == {
        ("卯", "午"), ("午", "卯"), ("丑", "辰"), ("辰", "丑"),
        ("子", "酉"), ("酉", "子"), ("未", "戌"), ("戌", "未"),
    }
    assert ("寅", "亥") not in relation_pairs("地支六破")   # 寅亥只算六合，不算破


def test_three_xing_groups_are_three_distinct_pair_sets() -> None:
    def unordered(key: str) -> set:
        return {frozenset(pair) for pair in relation_pairs(key)}

    assert unordered("无恩之刑") == {frozenset("寅巳"), frozenset("巳申"), frozenset("申寅")}
    assert unordered("恃势之刑") == {frozenset("丑戌"), frozenset("戌未"), frozenset("未丑")}
    assert unordered("无礼之刑") == {frozenset("子卯")}
    assert unordered("自刑") == {frozenset("辰"), frozenset("午"), frozenset("酉"), frozenset("亥")}
    assert len(unordered("地支六破")) == 4      # 四对，不是通行的六对


def test_only_wu_he_carries_a_transforming_element() -> None:
    assert RELATION_TABLES["天干五合"].element["甲己"] == "土"
    assert RELATION_TABLES["地支六冲"].element is None
    assert "非已化" in RELATION_TABLES["天干五合"].reading      # spec §6.3：只报合不判化
    # 地支六合的化气五行在允许语料里没有出处（论支元六合只给合与福轻重），故留空。
    assert RELATION_TABLES["地支六合"].element is None


def test_transforming_element_ignores_pair_order() -> None:
    assert transforming_element("天干五合", "己", "甲") == "土"
    assert transforming_element("天干五合", "癸", "戊") == "火"
    assert transforming_element("地支六冲", "子", "午") is None


def test_group_rules_use_the_classical_three_harmony_and_three_meeting_tables() -> None:
    for key in ("三合", "半合"):
        assert RELATION_TABLES[key].scope == "group" and RELATION_TABLES[key].side is None
        assert set(RELATION_TABLES[key].groups) == GROUP_KEYS
    assert RELATION_TABLES["三会"].scope == "group"
    assert set(RELATION_TABLES["三会"].groups) == SAN_HUI_KEYS
    assert RELATION_TABLES["三合"].peaks is None
    assert RELATION_TABLES["半合"].peaks["申子辰"] == "子"


def test_half_he_declares_it_does_not_judge_transformation() -> None:
    """《论支元三合》明言"三字缺一则化不成局"，本条只能标局势之半，不能顺嘴说它化了。"""
    assert "化不成局" in RELATION_TABLES["半合"].reading


def test_fan_yin_declares_its_narrow_scope() -> None:
    assert RELATION_TABLES["伏吟"].scope == "pillar" and RELATION_TABLES["反吟"].scope == "pillar"
    assert "窄口径" in RELATION_TABLES["反吟"].reading           # spec §6.3 要求写明
    for key in ("伏吟", "反吟"):
        assert RELATION_TABLES[key].pairs == frozenset()         # 柱类没有字表，判定在引擎


def test_each_xing_kind_has_its_own_reading() -> None:
    """无恩/恃势/无礼/自刑 四组各有独立 reading，不能合成一条泛说。"""
    kinds = [rule.kind for rule in RELATION_TABLES.values() if "刑" in rule.kind]
    assert len(kinds) == 4
    assert len({RELATION_TABLES[k].reading for k in kinds}) == 4


def test_stem_rules_scan_gan_and_branch_rules_scan_zhi() -> None:
    for key, rule in RELATION_TABLES.items():
        if rule.scope == "stem":
            assert rule.side == "gan", key
        elif rule.scope == "branch":
            assert rule.side == "zhi", key
        else:
            assert rule.side is None, key


def test_unknown_relation_raises() -> None:
    with pytest.raises(KeyError):
        relation_pairs("地支六合化气")
