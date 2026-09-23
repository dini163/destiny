"""合婚规则表不变量（spec §10.2）。

锁的是计数、键形、幅度、正负两侧与出处口径，不锁措辞 —— 出处纪律（§6.3）是
能被机器读出来的那一半，所以它在这里是一条红而不是评审时的一句提醒。
"""

from app.content.bazi_hehun_rules import (
    HEHUN_BASE,
    HEHUN_BORROWED_FROM,
    HEHUN_FAMILIES,
    HEHUN_GROUP_KEYS,
    HEHUN_NAYIN_KEYS,
    HEHUN_RELATION_KEYS,
    HEHUN_RULE_COUNT,
    HEHUN_RULES,
    HEHUN_TOP_CUT,
    STRONG_RATIO,
    WEAK_RATIO,
)
from app.content.bazi_relations import RELATION_TABLES
from app.schemas.scoring import MODEL_PARAM_SOURCE

FAMILY_COUNTS = {"relation": 12, "group": 3, "yongshen": 4, "nayin": 5, "palace": 5}


def test_the_five_families_have_the_count_the_design_promises() -> None:
    assert HEHUN_RULE_COUNT == len(HEHUN_RULES) == 29
    per_family = {family: 0 for family in HEHUN_FAMILIES}
    for rule in HEHUN_RULES.values():
        per_family[rule.family] += 1
    assert per_family == FAMILY_COUNTS


def test_every_key_is_prefixed_by_its_own_family() -> None:
    for key, rule in HEHUN_RULES.items():
        assert key.startswith(f"hh.{rule.family}."), key
        assert rule.family in HEHUN_FAMILIES


#: §6.1 的幅度是**分族**给的，不是一张大带子。这张表就是那句话的机器形态：
#: `(下界, 上界, 量级下限)`，量级下限只有对称族有（§6.1 的"±3…±10"说的是量级）。
DELTA_BANDS: dict[str, tuple[float, float, float]] = {
    "relation": (-10.0, 10.0, 3.0),
    "group": (4.0, 8.0, 0.0),  # 成局族只加：三合成局不为患
    "yongshen": (-7.0, 6.0, 0.0),
    "nayin": (-6.0, 6.0, 0.0),  # §7.2 的 我克 +2 落在这一族的带内
    "palace": (-10.0, 10.0, 0.0),
}


def test_deltas_stay_in_the_band_their_own_family_was_given() -> None:
    """分族幅度带是"一张账本在两个页面上读起来是同一把尺"的那个约束（spec §6.1、§10.2）。

    原本这里是一条全局 `3.0 <= abs(delta)`，Task 1 第一次跑就红了：±3…±10 是 §6.1 给
    **对称族**的量级带，被抄成了五族共用，于是 §7.2 明定的 我克 `+2`（年命族，带内 −6…+6）
    反倒成了违规。分族断言比原来的全局带更贴 spec，也更严 —— 成局族若掉到 +2、互济族
    若掉到 +8，全局带一声不响，这里立刻红。
    """
    for family, (low, high, min_abs) in DELTA_BANDS.items():
        deltas = [rule.delta for rule in HEHUN_RULES.values() if rule.family == family]
        assert deltas, family  # 族名写错时不让上面的循环空过
        assert all(low <= delta <= high for delta in deltas), (family, deltas)
        assert all(abs(delta) >= min_abs for delta in deltas), (family, deltas)
    assert all(rule.delta != 0.0 for rule in HEHUN_RULES.values())  # 0 分行进账本却不改总分
    positives = [r.delta for r in HEHUN_RULES.values() if r.delta > 0]
    negatives = [r.delta for r in HEHUN_RULES.values() if r.delta < 0]
    assert positives and negatives


def test_borrowed_readings_quote_the_classic_verbatim() -> None:
    """§6.3 第 1 条的机器形态：前半句逐字、source 逐字，反查得回去。"""
    assert len(HEHUN_BORROWED_FROM) == FAMILY_COUNTS["relation"] + FAMILY_COUNTS["group"]
    for key, origin_kind in HEHUN_BORROWED_FROM.items():
        origin = RELATION_TABLES[origin_kind]
        rule = HEHUN_RULES[key]
        assert rule.reading.startswith(origin.reading), key
        assert rule.source == origin.source, key


def test_self_composed_rows_never_cite_a_book() -> None:
    """§6.3 第 2 条：没有对应卷次的话不能安在古书头上。"""
    own = [rule for key, rule in HEHUN_RULES.items() if key not in HEHUN_BORROWED_FROM]
    assert len(own) == 29 - len(HEHUN_BORROWED_FROM) == 14
    for rule in own:
        assert "《" not in rule.source, rule.key
        assert rule.source != MODEL_PARAM_SOURCE, (
            f"{rule.key}：这是判语的出处，不是赋分的出处（赋分那一处由账本写 MODEL_PARAM_SOURCE）"
        )


def test_the_five_nayin_rows_each_say_their_own_thing() -> None:
    """§7.2：五条各写一句、不共用同一句。"""
    readings = [HEHUN_RULES[key].reading for key in HEHUN_NAYIN_KEYS.values()]
    assert len(set(readings)) == 5


def test_the_rulers_are_the_ones_the_design_named() -> None:
    assert (HEHUN_BASE, HEHUN_TOP_CUT, STRONG_RATIO, WEAK_RATIO) == (50.0, 80.0, 1.25, 0.75)


def test_the_relation_and_group_keys_cover_every_chinese_kind_once() -> None:
    assert set(HEHUN_RELATION_KEYS) == set(RELATION_TABLES) - {"三合", "半合", "三会"}
    assert set(HEHUN_GROUP_KEYS) == {"三合", "半合", "三会"}
    assert len(set(HEHUN_RELATION_KEYS.values()) | set(HEHUN_GROUP_KEYS.values())) == 15
