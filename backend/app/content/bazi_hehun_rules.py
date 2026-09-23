"""合婚规则表（spec §6）：五族 29 条，只定价与断语，不含命中逻辑。

条件是别处已经推出来的事实：`derive_relations` 的跨造 12 种关系（§2.1 的过滤）、
`derive_branch_groups` 的三合/半合/三会（§2.3 的两道判据）、`element_weight_scores`
对两造喜忌集的旺弱比值（§2.6）、两造年柱纳音的五行生克（§7.2）、以及 (乾日, 坤日)
那一格的三级归属（§6.2）。本表不碰历法，也不把命盘再算一遍（契约模型在 `app/schemas`、
命中逻辑在 `app/engines`），所以它不需要第二处真值来源。

族序即账本序：`HEHUN_FAMILIES` 的顺序就是 `engines/bazi_hehun.hehun_rows()`（Task 4 落地）
拼账本的顺序，两处同序是为了让"这一行属于哪一族"在 ledger 里读得出来，而不是靠键名前缀现推
—— 这条许诺由 `tests/content/test_bazi_hehun_rules.py` 的族序测钉住。

出处三句（spec §6.3，逐条落在下面的 `_borrowed` / `_own` 两个构造器里）：
① 对称族与成局族的判语**前半句逐字**是 `RELATION_TABLES[kind].reading`，`source` 逐字同取；
② "合婚主…"那半句是本系统演绎，写法固定为 `本系统依〈｛kind｝〉义理演绎`，不署卷次；
③ 29 条 delta、基准 50、80 那条分界、1.25/0.75 两条比值，赋分口径一律是
   `MODEL_PARAM_SOURCE` 那一句现成措辞 —— 账本行写它，本表的 `source` 写判语的出处。
"""

from pydantic import BaseModel, ConfigDict, Field

from app.content.bazi_relations import RELATION_TABLES
from app.schemas.scoring import MODEL_PARAM_SOURCE

#: 合婚基准分，含义同 `TRANSIT_BASE`：中性的起评，不是"及格"。
HEHUN_BASE = 50.0
#: 本轮唯一新增的一条分界（决策 5）：中间两道直接引 `bazi_strength.STRONG_CUT` / `WEAK_CUT`。
HEHUN_TOP_CUT = 80.0
#: 旺弱比值：以该造自己的五行均值为基准（spec §2.6）。基准只能是盘内比较 ——
#: 跨盘比原始分值没有意义，两造的总量本来就接近。
STRONG_RATIO = 1.25
WEAK_RATIO = 0.75

#: 判语为本系统命名与演绎时的出处口径。与 `MODEL_PARAM_SOURCE` 是两件事：那一句说的是
#: "这个数是本系统赋的"，这一句说的是"这句话是本系统写的"，混用会让一条判语看起来在
#: 声称古籍给过分数。
HEHUN_MODEL_SOURCE = "本系统命名与演绎（不引具体卷次）"

#: 书级出处，随 `provenance.tables` 回显（`app/content/__init__.py::HEHUN_CONTENT_SOURCES`，Task 8 接线）。
HEHUN_RULE_SOURCE = (
    "对称族与成局族判语逐字引各条自己的古籍出处（见条内 source）；"
    "婚义后缀句与互济、年命、婚姻宫三族为本系统演绎 · " + MODEL_PARAM_SOURCE
)

HEHUN_FAMILIES: tuple[str, ...] = ("relation", "group", "yongshen", "nayin", "palace")


class HehunRule(BaseModel):
    model_config = ConfigDict(frozen=True)

    key: str = Field(description="机器可读规则键，同时是 ScoreFactor.rule；前缀即族名。")
    label: str = Field(description="账本行短名，如 两造干合、我喜彼旺、日干五合。")
    family: str = Field(description="五族之一，必须与键的第二段一致。")
    delta: float = Field(description="分值增减，本系统模型参数（古籍只给喜忌序，从不给数）；幅度按族给定，见 spec §6.1。")
    reading: str = Field(description="单句判语；借古籍的那半句逐字，自造的那半句自署本系统。")
    source: str = Field(description="判语的出处。逐字引书者给书名，自造者给 HEHUN_MODEL_SOURCE。")


def _borrowed(kind: str, key: str, label: str, delta: float, marital: str) -> HehunRule:
    """古典断语逐字在前，婚义后缀自标在后 —— 两半句的出处不同，必须写在一条里。"""
    origin = RELATION_TABLES[kind]
    family = key.split(".")[1]
    return HehunRule(
        key=key,
        label=label,
        family=family,
        delta=delta,
        reading=f"{origin.reading}；合婚主{marital}（本系统依〈{kind}〉义理演绎）",
        source=origin.source,
    )


def _own(key: str, label: str, delta: float, reading: str) -> HehunRule:
    return HehunRule(
        key=key,
        label=label,
        family=key.split(".")[1],
        delta=delta,
        reading=reading,
        source=HEHUN_MODEL_SOURCE,
    )


# --- 对称族 12 条：与 RELATION_TABLES 的 12 条二元关系一一对应（spec §6.1）---
HEHUN_RELATION_KEYS: dict[str, str] = {
    "天干五合": "hh.relation.stem_merge",
    "天干相冲": "hh.relation.stem_clash",
    "地支六冲": "hh.relation.branch_clash",
    "地支六合": "hh.relation.branch_merge",
    "地支六害": "hh.relation.branch_harm",
    "地支六破": "hh.relation.branch_break",
    "无恩之刑": "hh.relation.punishment_insult",
    "恃势之刑": "hh.relation.punishment_power",
    "无礼之刑": "hh.relation.punishment_impolite",
    "自刑": "hh.relation.self_punishment",
    "伏吟": "hh.relation.repeat",
    "反吟": "hh.relation.reverse",
}

# --- 成局族 3 条：成员须跨两造且摘掉对方后本造立不起同一局（spec §2.3 两道判据）---
HEHUN_GROUP_KEYS: dict[str, str] = {
    "三合": "hh.group.three_harmony",
    "半合": "hh.group.half_harmony",
    "三会": "hh.group.three_meeting",
}

# --- 年命族 5 条：主语固定为乾（spec §6.2），一对纳音只有一个关系、只出一行账 ---
HEHUN_NAYIN_KEYS: dict[str, str] = {
    "生我": "hh.nayin.sheng_wo",
    "比和": "hh.nayin.bi_he",
    "我克": "hh.nayin.wo_ke",
    "我生": "hh.nayin.wo_sheng",
    "克我": "hh.nayin.ke_wo",
}

# --- 婚姻宫族 5 条：(乾日, 坤日) 那一格按 §6.2 的三级归属收成 ---
HEHUN_PALACE_KEYS: tuple[str, ...] = (
    "hh.palace.stem_merge",
    "hh.palace.branch_merge",
    "hh.palace.branch_clash",
    "hh.palace.branch_harmony",
    "hh.palace.pillar_reverse",
)

_RULE_LIST: tuple[HehunRule, ...] = (
    # --- relation：干、支、柱三级；分值只看那一格是不是婚姻宫（spec §6.1、§2.2）---
    _borrowed("天干五合", "hh.relation.stem_merge", "两造干合", 8.0, "彼此情意和合、同气相求"),
    _borrowed("天干相冲", "hh.relation.stem_clash", "两造干冲", -6.0, "两心相违、谋为各出"),
    _borrowed("地支六冲", "hh.relation.branch_clash", "两造支冲", -10.0, "居家动躁、聚少离多"),
    _borrowed("地支六合", "hh.relation.branch_merge", "两造支合", 8.0, "行事相契、难分难解"),
    _borrowed("地支六害", "hh.relation.branch_harm", "两造支害", -5.0, "六亲参商、亲族生隙"),
    _borrowed("地支六破", "hh.relation.branch_break", "两造支破", -3.0, "财用耗散、小事见缺"),
    _borrowed("无恩之刑", "hh.relation.punishment_insult", "无恩之刑", -6.0, "恩反成怨、少恩寡愧"),
    _borrowed("恃势之刑", "hh.relation.punishment_power", "恃势之刑", -6.0, "各恃其强、相持不让"),
    _borrowed("无礼之刑", "hh.relation.punishment_impolite", "无礼之刑", -6.0, "长幼失序、面目有亏"),
    _borrowed("自刑", "hh.relation.self_punishment", "两造自刑", -4.0, "各怀其郁、自生枝节"),
    _borrowed("伏吟", "hh.relation.repeat", "两造伏吟", -5.0, "同气重叠、进退两难"),
    _borrowed("反吟", "hh.relation.reverse", "两造反吟", -8.0, "干支相对、聚散不宁"),
    # --- group：同气相求的那一层，局成在两人之间而不是一个人之内 ---
    _borrowed("三合", "hh.group.three_harmony", "跨造三合", 8.0, "两造合成一气、其势相连"),
    _borrowed("半合", "hh.group.half_harmony", "跨造半合", 4.0, "两造半成一气、需时令撑持"),
    _borrowed("三会", "hh.group.three_meeting", "跨造三会", 6.0, "两造共一方专气"),
    # --- yongshen：四象限 × 两视角，天生两向，每视角各一行（spec §6.2）---
    _own(
        "hh.yongshen.supply", "我喜彼旺", 6.0,
        "我喜用之神行，于彼造之盘旺相有余，是名为补：其所缺者我有余，吾得所助（比值 ≥ 1.25 方论旺，本系统盘内均值作尺）",
    ),
    _own(
        "hh.yongshen.shortfall", "我喜彼弱", -5.0,
        "我喜用之神行，于彼造之盘退弱不足，是名为阙：同欲此气而两造皆薄，欲助无力的那一面（比值 ≤ 0.75 方论弱）",
    ),
    _own(
        "hh.yongshen.clash", "我忌彼旺", -7.0,
        "我忌神之五行，于彼造之盘旺相有力，是名为冲：彼愈旺则我之忌愈炽，最耗精神的一格",
    ),
    _own(
        "hh.yongshen.harmless", "我忌彼弱", 3.0,
        "我忌神之五行，于彼造之盘衰弱无力，是名为安：所畏者不起，虽同气而不相害",
    ),
    # --- nayin：两造年命纳音五行，主语固定为乾 ---
    _own(
        "hh.nayin.sheng_wo", "生我", 6.0,
        "彼之来生我，其气长养，凡事宜受、宜进、宜生",
    ),
    _own(
        "hh.nayin.bi_he", "比和", 4.0,
        "两家同气，其情相安，无高低之辨",
    ),
    _own(
        "hh.nayin.wo_ke", "我克", 2.0,
        "我去克彼，我居其长，凡事宜主不宜客",
    ),
    _own(
        "hh.nayin.wo_sheng", "我生", -4.0,
        "我去生彼，泄我之气，凡事宜守不宜耗",
    ),
    _own(
        "hh.nayin.ke_wo", "克我", -6.0,
        "彼来克我，我居其短，凡事宜和不宜争",
    ),
    # --- palace：(乾日, 坤日) 那一格，权重最高的一格，故分值幅度也最大 ---
    _own(
        "hh.palace.stem_merge", "日干五合", 10.0,
        "两造日干相合，如男女相合而成夫妇之道；干为婚之主，故婚姻宫族以合干为最上（本系统以日干为婚姻宫之干）",
    ),
    _own(
        "hh.palace.branch_merge", "日支相合", 8.0,
        "两造日支六合、三合或半合，宫位相合；支为婚之据，主同居处而难分离",
    ),
    _own(
        "hh.palace.branch_clash", "日支战", -10.0,
        "两造日支值冲、刑、害、破或自刑，婚姻宫不安，主宅内动荡、聚处生波",
    ),
    _own(
        "hh.palace.branch_harmony", "日支比和", 3.0,
        "两造日支同字比和，无冲无合，其气相守；比和不为喜亦不为患，故分最薄",
    ),
    _own(
        "hh.palace.pillar_reverse", "日柱伏反吟", -8.0,
        "两造日柱干支全同（伏吟）或干冲支冲（反吟）；本系统以柱级为最重，一经成立则该格干支两级不再各记一条（spec §6.2）",
    ),
)

HEHUN_RULES: dict[str, HehunRule] = {rule.key: rule for rule in _RULE_LIST}
HEHUN_RULE_COUNT = len(HEHUN_RULES)

#: 合婚键 → 所引的关系表 `kind`。这张倒查表就是 §6.3 第 1 条的机器形态：
#: 凡在此表之内的条目，其判语前半句与 `source` 都必须逐字等于 `RELATION_TABLES[kind]`。
HEHUN_BORROWED_FROM: dict[str, str] = {
    **{key: kind for kind, key in HEHUN_RELATION_KEYS.items()},
    **{key: kind for kind, key in HEHUN_GROUP_KEYS.items()},
}


def hehun_rule(key: str) -> HehunRule:
    """取一条合婚规则；键写错时把整张表的键打出来，比猜哪一个少了个字便宜。"""
    try:
        return HEHUN_RULES[key]
    except KeyError:
        raise KeyError(f"Unknown hehun rule: {key}. Known: {sorted(HEHUN_RULES)}") from None
