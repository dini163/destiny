"""合婚规则表不变量（spec §10.2）。

锁的是计数、族序、键形、每一条的分值、正负两侧与出处口径。措辞不锁，但**自造与
引书的分界锁**（§6.3）—— 那是能被机器读出来的那一半，所以它在这里是一条红而不是
评审时的一句提醒。
"""

import pytest

from app.content.bazi_hehun_rules import (
    HEHUN_BASE,
    HEHUN_BORROWED_FROM,
    HEHUN_FAMILIES,
    HEHUN_GROUP_KEYS,
    HEHUN_MODEL_SOURCE,
    HEHUN_NAYIN_KEYS,
    HEHUN_PALACE_KEYS,
    HEHUN_RELATION_KEYS,
    HEHUN_RULE_COUNT,
    HEHUN_RULE_SOURCE,
    HEHUN_RULES,
    HEHUN_TOP_CUT,
    STRONG_RATIO,
    WEAK_RATIO,
    hehun_rule,
)
from app.content.bazi_relations import RELATION_TABLES
from app.core.provenance import MODEL_PARAM_SOURCE

FAMILY_COUNTS = {"relation": 12, "group": 3, "yongshen": 4, "nayin": 5, "palace": 5}


def test_the_five_families_have_the_count_the_design_promises() -> None:
    assert HEHUN_RULE_COUNT == len(HEHUN_RULES) == 29
    per_family = {family: 0 for family in HEHUN_FAMILIES}
    for rule in HEHUN_RULES.values():
        per_family[rule.family] += 1
    assert per_family == FAMILY_COUNTS


def test_the_five_families_are_stacked_in_the_order_the_ledger_uses() -> None:
    """族序即账本序 —— 模块 docstring 与 spec §6.1 都作了这个许诺，此前却没人测。

    评审把原来那条 `test_every_key_is_prefixed_by_its_own_family` 判为**空断言**：
    `family` 在 `_borrowed`/`_own` 里就是从键第二段 `split(".")[1]` 现算的，两处按
    构造恒等，不是"没测到"而是"测不出东西"。这条改测真会被改坏的东西：新增一族忘了
    排进 `HEHUN_FAMILIES`、或把 婚姻宫 那五行插到 互济 中间 —— 两者都让账本族序失真，
    却都不越任何分值带。
    """
    seen = [rule.family for rule in HEHUN_RULES.values()]
    assert list(dict.fromkeys(seen)) == list(HEHUN_FAMILIES), seen  # 族不重、不漏、序合
    assert seen == sorted(seen, key=HEHUN_FAMILIES.index), seen  # 同族行必须相邻


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


#: 29 条的实测分值，按 `_RULE_LIST` 的族序抄录。带（`DELTA_BANDS`）拦越界，这张表拦
#: **手滑** —— 生我 与 我生 互换符号、日支战 写成 +10，都还在自己的带里，只有字面量看得住。
MEASURED_DELTAS: dict[str, list[float]] = {
    "relation": [8.0, -6.0, -10.0, 8.0, -5.0, -3.0, -6.0, -6.0, -6.0, -4.0, -5.0, -8.0],
    "group": [8.0, 4.0, 6.0],
    "yongshen": [6.0, -5.0, -7.0, 3.0],
    "nayin": [6.0, 4.0, 2.0, -4.0, -6.0],  # §7.2 五价，我克 那枚 +2 就是 Task 1 的争议点
    "palace": [10.0, 8.0, -10.0, 3.0, -8.0],
}


def test_every_delta_is_the_one_the_design_priced() -> None:
    """五族 29 价逐字钉住（spec §2.9 的预算、§7.2 的年命五价）。

    这条是本任务真正的交付物：后面八个任务全都按这些数拼账本，Task 4 的 对拍 夹具
    直接引它们。评审实测过：只写带不写字面量时，把 我克 改成 3.0、生我 改成 −6、
    日支战 改成 +10，全表依然绿。
    """
    for family, expected in MEASURED_DELTAS.items():
        actual = [rule.delta for rule in HEHUN_RULES.values() if rule.family == family]
        assert actual == expected, (family, actual)
    assert [len(v) for v in MEASURED_DELTAS.values()] == [12, 3, 4, 5, 5]


def test_borrowed_readings_quote_the_classic_verbatim() -> None:
    """§6.3 第 1 条的机器形态：前半句逐字、source 逐字，反查得回去。

    两条断言都是**双向**的：`startswith` 管古典那半句不许被改写，`endswith` 管自造那
    半句不许把自己伪装成引书 —— 评审实测过，只留前者时把 `（本系统依〈天干五合〉义理
    演绎）` 换成 `（依古义）` 整表仍绿，而 §6.3 第 2 条要拦的正是这一种。前半句逐字
    是 `_borrowed` 用 f-string 拼出来的，构造上就成立，所以那条是**回归护栏**而非发现器。
    """
    assert len(HEHUN_BORROWED_FROM) == FAMILY_COUNTS["relation"] + FAMILY_COUNTS["group"]
    for key, origin_kind in HEHUN_BORROWED_FROM.items():
        origin = RELATION_TABLES[origin_kind]
        rule = HEHUN_RULES[key]
        assert rule.reading.startswith(origin.reading), key
        assert rule.reading.endswith(f"（本系统依〈{origin_kind}〉义理演绎）"), key
        assert rule.source == origin.source, key


def test_self_composed_rows_cite_the_system_and_only_the_system() -> None:
    """§6.3 第 2 条：没有对应卷次的话不能安在古书头上。

    原来这条只做减法（不许出现 `《`、不许等于 `MODEL_PARAM_SOURCE`），评审实测出一个
    洞：把 我克 的 `source` 换成任意一句不含书名号的自造话，它照样绿 —— 出处口径
    其实要求**逐字等于** `HEHUN_MODEL_SOURCE`。补齐正向断言顺带覆盖 `reading`：书名号
    若出现在判语正文里，同样是把自造的话借古书的势。
    """
    own = [rule for key, rule in HEHUN_RULES.items() if key not in HEHUN_BORROWED_FROM]
    assert len(own) == 29 - len(HEHUN_BORROWED_FROM) == 14
    for rule in own:
        assert rule.source == HEHUN_MODEL_SOURCE, rule.key
        assert "《" not in rule.reading, rule.key
        assert rule.source != MODEL_PARAM_SOURCE, (
            f"{rule.key}：这是判语的出处，不是赋分的出处（赋分那一处由账本写 MODEL_PARAM_SOURCE）"
        )


def test_the_five_nayin_rows_are_the_five_relations_and_each_says_its_own_thing() -> None:
    """§7.2：五个关系名一个不许换、五条判语各写一句、五价照 §7.2 抄（Task 1 的争议点在此）。"""
    assert set(HEHUN_NAYIN_KEYS) == {"生我", "比和", "我克", "我生", "克我"}
    readings = [HEHUN_RULES[key].reading for key in HEHUN_NAYIN_KEYS.values()]
    assert len(set(readings)) == 5


def test_the_marriage_palace_rows_are_the_five_the_design_named() -> None:
    """§6.1 婚姻宫族那五种归属 —— 键名是账本与前端共用的合同，此前无人核对。

    评审实测：把 `hh.palace.branch_harmony` 改成 `..._x` 之前全表仍绿（族计数与分值带
    都不认具体键名），而 T10 的 TS 镜像与 T11 的卡片都按这五个键取值。
    """
    palace = [key for key, rule in HEHUN_RULES.items() if rule.family == "palace"]
    assert set(palace) == set(HEHUN_PALACE_KEYS)
    assert len(palace) == 5


def test_the_numeric_provenance_is_the_shared_sentence_not_a_paraphrase() -> None:
    """§6.3 第 3 条：赋分口径只能复用 `MODEL_PARAM_SOURCE` 原句，不许各模块自行改写。"""
    assert MODEL_PARAM_SOURCE in HEHUN_RULE_SOURCE


def test_hehun_rule_looks_up_by_key_and_names_the_whole_table_on_a_miss() -> None:
    assert hehun_rule("hh.nayin.wo_ke").delta == 2.0
    with pytest.raises(KeyError) as excinfo:
        hehun_rule("hh.palace.nope")
    assert "hh.relation.stem_merge" in str(excinfo.value)  # 打全表，别让人猜哪个字少了


def test_the_rulers_are_the_ones_the_design_named() -> None:
    assert (HEHUN_BASE, HEHUN_TOP_CUT, STRONG_RATIO, WEAK_RATIO) == (50.0, 80.0, 1.25, 0.75)


def test_the_relation_and_group_keys_cover_every_chinese_kind_once() -> None:
    assert set(HEHUN_RELATION_KEYS) == set(RELATION_TABLES) - {"三合", "半合", "三会"}
    assert set(HEHUN_GROUP_KEYS) == {"三合", "半合", "三会"}
    assert len(set(HEHUN_RELATION_KEYS.values()) | set(HEHUN_GROUP_KEYS.values())) == 15
