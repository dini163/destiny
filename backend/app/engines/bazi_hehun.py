"""八字合婚引擎（spec §2、§6）：两造同屏，关系第一次要跨两张盘算。

历法、排盘、关系表、合局表、纳音表、账本、流年扫描全是现成件，本模块只做四件事：
① 把两造各排一次盘，并把错误归到是哪一造（§9.2）；② 以乾四柱为体、坤四柱为 `extra`
扫一次跨造关系，按"恰好一侧是 extra"过滤（§2.1）；③ 按 §6.2 的归属规则把每个事实
收进五族里的一族一条（对称、成局、互济、年命、婚姻宫五族全在账）；
④ 交 `build_ledger` 出一份自解释的总分。

**跨造不算十神**（决策 2）：十神是命局内部的坐标（切片 0 §7.5 已把 `_god()` 对外来柱
定为空串），把它伸到另一张盘上是本系统没有资格立的第五种命理学说。同理两造的喜忌一律
直接取各自本命盘（决策 3），本模块不重判。

`strength`（紧临/隔位/远位）在这里不存在：那是同一张盘里两根柱相隔几位，跨造时退化成
"打到了对方第几根柱"，与实际关系无关（§2.2）。契约带的是真语义的柱位对。
"""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date

from app.content.bazi_hehun_rules import (
    HEHUN_BASE,
    HEHUN_GROUP_KEYS,
    HEHUN_NAYIN_KEYS,
    HEHUN_NAYIN_NOTE,
    HEHUN_RELATION_KEYS,
    HEHUN_RULE_SOURCE,
    HEHUN_TOP_CUT,
    STRONG_RATIO,
    WEAK_RATIO,
    hehun_rule,
)
from app.content.bazi_nayin import nayin_meaning
from app.content.bazi_relations import RELATION_TABLES
from app.content.wuxing import CONTROLS, GENERATES
from app.core.errors import DestinyError
from app.engines.bazi import compute_bazi_chart
from app.engines.bazi_rules import POSITIONS, derive_branch_groups, derive_relations, is_fanyin
from app.engines.bazi_strength import STRONG_CUT, WEAK_CUT, element_weight_scores
from app.schemas.bazi import BaziChart, BaziPillar
from app.schemas.bazi_hehun import (
    HehunCell,
    HehunCellHit,
    HehunComplement,
    HehunComplementCell,
    HehunComplementElement,
    HehunComplementView,
    HehunFired,
    HehunNayin,
    HehunNayinSide,
    HehunProfile,
    PartnerSide,
    Vigor,
)
from app.schemas.common import Gender
from app.schemas.scoring import ScoreFactor, ScoreValue, build_ledger
from app.solar.geo import resolve_longitude
from app.solar.true_solar_time import STANDARD_MERIDIAN_CN

#: 矩阵的枚举序，与 `derive_relations` 的柱序同词（§2.4 的 `extra{n}` 映射靠它）。
POSITION_ORDER: tuple[str, ...] = POSITIONS

#: 关系 kind → 账本键的三张倒表。键表本身在 `content/bazi_hehun_rules.py`，这里只倒转，
#: 不再抄一遍中文名 —— 抄一次就多一处会与规则表走岔的地方。
RELATION_RULE_OF: dict[str, str] = dict(HEHUN_RELATION_KEYS)
GROUP_RULE_OF: dict[str, str] = dict(HEHUN_GROUP_KEYS)
NAYIN_RULE_OF: dict[str, str] = dict(HEHUN_NAYIN_KEYS)

#: 账本短名里的两字柱名。与 `BaziPillar.label` 同词（测见 `test_..._charts_carry`），
#: 那里是"年柱"，这里要的是「乾年×坤时」那种紧凑对位。
PILLAR_NAME: dict[str, str] = {"year": "年", "month": "月", "day": "日", "hour": "时"}

# --- 婚姻宫族五个键（§6.2 的三级归属各对应一个）---
PALACE_STEM_MERGE = "hh.palace.stem_merge"
PALACE_BRANCH_MERGE = "hh.palace.branch_merge"
PALACE_BRANCH_CLASH = "hh.palace.branch_clash"
PALACE_BRANCH_HARMONY = "hh.palace.branch_harmony"
PALACE_PILLAR_REVERSE = "hh.palace.pillar_reverse"

#: 三会不撑婚姻宫：§6.1 的支级只列"六合 / 三合 / 半合"，三会那种"共一方专气"
#: 跨的是整片月气而不是两个人的宫位。
PALACE_GROUP_KINDS: frozenset[str] = frozenset({"三合", "半合"})
#: 婚姻宫的支级只分两堆：六合算"合"，其余支级关系一律算"战"（冲/刑/害/破，含自刑）。
#: 第二堆从关系表里现推，免得将来添一条支级关系时这里静默漏记账。
PALACE_BRANCH_MERGE_KINDS: frozenset[str] = frozenset({"地支六合"})
PALACE_BRANCH_CLASH_KINDS: frozenset[str] = (
    frozenset(rule.kind for rule in RELATION_TABLES.values() if rule.scope == "branch")
    - PALACE_BRANCH_MERGE_KINDS
)
#: (乾日, 坤日) 那一格里会被婚姻宫族收编的 kind。**天干相冲不在其内** ——
#: 婚姻宫族只立五合不立冲（§6.1），日干相冲没有归宿，所以它留在对称族，不构成双计。
SEALED_DAY_CELL_KINDS: frozenset[str] = (
    frozenset({"天干五合", "伏吟", "反吟"})
    | PALACE_BRANCH_MERGE_KINDS
    | PALACE_BRANCH_CLASH_KINDS
)


@dataclass(frozen=True)
class HehunChartPair:
    """一次合婚的两张命盘：乾为体、坤为用，`cross_relations` 只扫这一次。"""

    male: BaziChart
    female: BaziChart


@dataclass(frozen=True)
class CrossHit:
    """一条跨造事实。柱位对取代了 `RelationPair.strength`（§2.2）。"""

    kind: str
    rule: str
    male_position: str
    female_position: str
    male_character: str
    female_character: str


@dataclass(frozen=True)
class HehunRow:
    """账本的一行未折入前的形：键、短名、族、视角、分值。"""

    rule: str
    label: str
    family: str
    direction: str
    delta: float


def profile_longitude(profile: HehunProfile) -> float:
    """一造的经线：校正开启时城市或显式经度必须定下来，关闭时取标准经线。

    与 `api/v1/bazi.py::_chart_longitude` 同一条判断，但合婚有两造、各带一份
    `apply_true_solar_time`（§5.1），所以在引擎里按 profile 走一次而不是在路由里
    走两次 —— 路由要保持薄，而"这条经线是谁定的"这件事只该有一处实现。
    """
    if profile.apply_true_solar_time:
        return resolve_longitude(profile.city, profile.longitude)
    return profile.longitude if profile.longitude is not None else STANDARD_MERIDIAN_CN


def compute_partner_charts(
    male: HehunProfile, female: HehunProfile, reference: date
) -> HehunChartPair:
    """两造各排一次盘。一造非法即整请求失败，绝不回半张合婚盘（§9.1）。"""
    return HehunChartPair(
        male=_chart_for(male, Gender.MALE, reference),
        female=_chart_for(female, Gender.FEMALE, reference),
    )


def _chart_for(profile: HehunProfile, gender: Gender, reference: date) -> BaziChart:
    """排一造的盘，出错时把"是哪一造"记进 `context` 再原样抛出。

    code、message、status_code 一字不动：既有的错误链不必为合婚开第二份，`context.partner`
    随那份错误一同出去，归属在后端这一侧就已经定下了（§9.2）。把它说给读者还差前端一步 ——
    `TransitErrorNote` 目前只在 `transit_*`/`liuri_*`/`liushi_*` 前缀族上渲染 `context`，
    `invalid_birth_data` 落不进那道门，于是只回显 message（Task 11 接线）。`partner` 是唯一
    新增的一项 context，取 `Gender` 的值即是乾/坤的键名，不必再造一张映射表。
    只拦 `DestinyError`：非域错误原样上抛，不塞归属，免得把一个 bug 伪装成"某造生辰有误"。
    """
    try:
        return compute_bazi_chart(
            birth_date=profile.birth_date,
            birth_time=profile.birth_time,
            calendar=profile.calendar,
            longitude=profile_longitude(profile),
            gender=gender,
            apply_true_solar_time=profile.apply_true_solar_time,
            reference_date=reference,
            name=profile.name,
        )
    except DestinyError as error:
        error.context = {**(error.context or {}), "partner": gender.value}
        raise


def cross_relations(pair: HehunChartPair) -> list[CrossHit]:
    """乾四柱 × 坤四柱：扫一次，只留恰好一端是坤造的命中（§2.1）。

    这条过滤不是清洁工作 —— 少它一步，两张盘各自命盘里已经报过的关系会在合婚总分里
    第二次加分。`_slots()` 把 `extra_ganzhi` 接在四柱之后、扫描又是 i<j，所以跨造那一
    行的 `pillar_a` 恒属乾、`pillar_b` 恒属坤；两端同侧（皆 extra）即坤造自己的账。
    坤造的 `extra{n}` 按年→月→日→时展开，所以 `extra2` 就是坤日柱（§2.4）。
    """
    female_ganzhi = [pillar.ganzhi for pillar in pair.female.pillars]
    hits: list[CrossHit] = []
    for relation in derive_relations(pair.male.pillars, female_ganzhi):
        if _is_extra(relation.pillar_a) or not _is_extra(relation.pillar_b):
            continue
        hits.append(
            CrossHit(
                kind=relation.kind,
                rule=RELATION_RULE_OF[relation.kind],
                male_position=relation.pillar_a,
                female_position=_position_of(relation.pillar_b),
                male_character=relation.character_a,
                female_character=relation.character_b,
            )
        )
    return hits


def _is_extra(pillar: str) -> bool:
    return pillar.startswith("extra")


def _position_of(pillar: str) -> str:
    """`extra{n}` → 坤造第 n 根柱的位置名；`n` 就是 `POSITIONS` 的下标（§2.4）。

    本命四柱那一侧原样返回，所以调用方不必先判断它是哪一侧 —— 两侧的柱位在账本与
    矩阵里必须是同一套词，否则 (乾日, 坤日) 这种对位就没法比。
    """
    return POSITIONS[int(pillar[len("extra") :])] if _is_extra(pillar) else pillar


@dataclass(frozen=True)
class GroupMember:
    """局的一个成员：哪一造、第几根柱、哪个支。"""

    side: str
    position: str
    branch: str


@dataclass(frozen=True)
class CrossGroup:
    """`derive_branch_groups` 的一局，成员已翻回 (造, 柱位) 的坐标。

    原样搬 `BranchMember` 不行：它的 `pillar` 是 `extra{n}` 那种扫描槽位名，
    而账本与矩阵要的柱位必须与乾侧同词（§2.4）。`ten_god` 不带 —— 跨造不算十神（决策 2）。
    """

    kind: str
    rule: str
    element: str
    members: tuple[GroupMember, ...]


def _side_of(pillar: str) -> str:
    """扫描槽位属于哪一造。关系行的 `pillar_a` 恒为乾（§2.1 的 i<j），合局的成员则两侧都有。"""
    return "female" if _is_extra(pillar) else "male"


def _pillar(chart: BaziChart, position: str) -> BaziPillar:
    """按位置名取一造的那根柱；`POSITION_ORDER` 即 `BaziChart.pillars` 的排布序。"""
    return chart.pillars[POSITION_ORDER.index(position)]


def scanned_groups(pair: HehunChartPair) -> list[CrossGroup]:
    """两造合看的全部局，**未过 §2.3 两道判据**。

    单独开这一层不是为了复用，是为了让两道判据各能被指名测试：只看
    `cross_groups()` 的输出，"被第一道滤掉"和"被第二道滤掉"长得一模一样。
    """
    female_ganzhi = [pillar.ganzhi for pillar in pair.female.pillars]
    return [
        CrossGroup(
            kind=group.kind,
            rule=GROUP_RULE_OF[group.kind],
            element=group.element,
            members=tuple(
                GroupMember(
                    side=_side_of(member.pillar),
                    position=_position_of(member.pillar),
                    branch=member.branch,
                )
                for member in group.members
            ),
        )
        for group in derive_branch_groups(pair.male.pillars, female_ganzhi)
    ]


def _forms_group(kind: str, element: str, branches: frozenset[str]) -> bool:
    """这些支单独立不立得起同 kind 同五行的局（§2.3 第二道判据的判据）。

    半合与三合/三会的成局条件不一样：半合要**二字且含旺支**（申子辰局里必须见 子），
    三合与三会要三支齐见。两张字模式表都在 `RELATION_TABLES` 里，这里只按 kind 分支。
    只有 `scope == "group"` 的三条会进这个函数（调用方是 `GROUP_RULE_OF` 的键表），
    它们的 `groups` 必不为 `None`。
    """
    rule = RELATION_TABLES[kind]
    for pattern, pattern_element in rule.groups.items():
        if pattern_element != element:
            continue
        if kind == "半合":
            peak = rule.peaks[pattern]
            if len(branches) == 2 and branches <= frozenset(pattern) and peak in branches:
                return True
        elif branches == frozenset(pattern):
            return True
    return False


def group_spans_both_charts(group: CrossGroup) -> bool:
    """第一道判据：成员里乾、坤各至少有一个 —— 光"有 extra 成员"不够（§2.3）。"""
    return {member.side for member in group.members} == {"male", "female"}


def group_is_new_between_charts(group: CrossGroup) -> bool:
    """第二道判据：摘掉对方之后，任一造自己都不能再立起同一局（§2.3）。"""
    male = frozenset(m.branch for m in group.members if m.side == "male")
    female = frozenset(m.branch for m in group.members if m.side == "female")
    return not (
        _forms_group(group.kind, group.element, male)
        or _forms_group(group.kind, group.element, female)
    )


def cross_groups(pair: HehunChartPair) -> list[CrossGroup]:
    """跨造成局：两道判据都过的那几局。"""
    return [
        group
        for group in scanned_groups(pair)
        if group_spans_both_charts(group) and group_is_new_between_charts(group)
    ]


def group_bonds_both_day_pillars(group: CrossGroup) -> bool:
    """这一局是否把两人的日支拴在了一起（§6.2 支级的第三条路）。"""
    seats = {(member.side, member.position) for member in group.members}
    return {("male", "day"), ("female", "day")} <= seats


def group_is_a_palace_fact(group: CrossGroup) -> bool:
    return group.kind in PALACE_GROUP_KINDS and group_bonds_both_day_pillars(group)


def group_rows(pair: HehunChartPair) -> list[HehunRow]:
    """成局族：跨造局每局一行；被婚姻宫**收走**的那局不在这里出账（§6.2 与成局族的交接）。

    收走的判据是两道，缺一不可：`group_is_a_palace_fact` 说出"这一局撑的是婚姻宫支级"，
    `PALACE_BRANCH_MERGE in palace_keys(pair)` 说出"婚姻宫确实记了它"。柱级成立时后者为假
    （`palace_keys` 直接 `return` 在 `pillar_reverse` 上），此时丢掉前者就是让那局的分值
    两头不记 —— "只记一次"不等于"一次都不记"。
    """
    sealed_by_palace = PALACE_BRANCH_MERGE in palace_keys(pair)
    return [
        _to_row(group.rule, "mutual", f"（{group.element}）")
        for group in cross_groups(pair)
        if not (sealed_by_palace and group_is_a_palace_fact(group))
    ]


def _nayin_elements(pair: HehunChartPair) -> tuple[str, str]:
    """两造年命的五行（乾, 坤）。

    纳音五行取自 `nayin_meaning()`：`BaziPillar` 上只有纳音**名**（`nayin` 字段），没有
    五行字段，所以两边各现查一次。关系与短名后缀都要读这一对，故只查在这一处。
    """
    return (
        nayin_meaning(_pillar(pair.male, "year").ganzhi).element,
        nayin_meaning(_pillar(pair.female, "year").ganzhi).element,
    )


def nayin_relation(pair: HehunChartPair) -> str:
    """两造年命纳音的五行关系，**主语固定为乾**（§6.2）。

    五行之间的关系只有 比和/生我/我生/我克/克我 五种，前四条判完剩下的那一条必然是
    克我（`CONTROLS[theirs] == mine`），所以不必再判一次 —— 五个分支穷尽。
    乾火坤木 → 木生火 → 生我，绝不同时再记一行我生。
    """
    mine, theirs = _nayin_elements(pair)
    if mine == theirs:
        return "比和"
    if GENERATES[theirs] == mine:
        return "生我"
    if GENERATES[mine] == theirs:
        return "我生"
    if CONTROLS[mine] == theirs:
        return "我克"
    return "克我"


def nayin_key(pair: HehunChartPair) -> str:
    return NAYIN_RULE_OF[nayin_relation(pair)]


def nayin_row(pair: HehunChartPair) -> HehunRow:
    """年命族恒一行（§6.1）：短名带两造纳音五行的那半句，读得出"从谁看谁"。"""
    mine, theirs = _nayin_elements(pair)
    return _to_row(nayin_key(pair), "mutual", f"（乾{mine}·坤{theirs}）")


def _day_cell_kinds(pair: HehunChartPair, hits: Sequence[CrossHit]) -> frozenset[str]:
    """(乾日, 坤日) 那一格里扫到的全部关系 kind。用柱位对而不扫 `extra2`：
    `CrossHit` 已经把槽位翻回了两造同词的柱位（§2.4）。
    """
    return frozenset(
        hit.kind for hit in hits if (hit.male_position, hit.female_position) == ("day", "day")
    )


def palace_keys(pair: HehunChartPair) -> list[str]:
    """(乾日, 坤日) 那一格按 §6.2 的三级归属收成的一条（至多两条）键。

    归属次序即代码次序：**柱级 → 干级 → 支级**。柱级先行且直接 `return`，因为伏吟与
    反吟的两半本来就是"干同/干冲 + 支同/支冲"，再往下走就是把一件事记三遍。干级只认
    五合（婚姻宫族不立日干冲），支级三条分支互斥：合 > 战 > 比和。
    干级与支级不互斥，所以一格可以同时出 `stem_merge` 与 `branch_merge` 两行 ——
    那是两回事（心意的合与居处的合），不是把一格记了两次。
    柱级那一支的 `return` 另有一层意思：**它没有收下任何支级事实**，所以成局族那一边
    的交接（`group_rows` 只看 `PALACE_BRANCH_MERGE` 是否真在这里出现）于是不成立。
    """
    male_day = _pillar(pair.male, "day")
    female_day = _pillar(pair.female, "day")
    if male_day.ganzhi == female_day.ganzhi or is_fanyin(male_day.ganzhi, female_day.ganzhi):
        return [PALACE_PILLAR_REVERSE]
    kinds = _day_cell_kinds(pair, cross_relations(pair))
    keys: list[str] = []
    if (male_day.gan, female_day.gan) in RELATION_TABLES["天干五合"].pairs:
        keys.append(PALACE_STEM_MERGE)
    if kinds & PALACE_BRANCH_MERGE_KINDS or any(
        group_is_a_palace_fact(group) for group in cross_groups(pair)
    ):
        keys.append(PALACE_BRANCH_MERGE)
    elif kinds & PALACE_BRANCH_CLASH_KINDS:
        keys.append(PALACE_BRANCH_CLASH)
    elif male_day.zhi == female_day.zhi:
        keys.append(PALACE_BRANCH_HARMONY)
    return keys


def palace_rows(pair: HehunChartPair) -> list[HehunRow]:
    """婚姻宫族：一格至多两条，短名自带格位（"日干五合"），所以不需要后缀。"""
    return [_to_row(key, "mutual") for key in palace_keys(pair)]


def _to_row(rule_key: str, direction: str, suffix: str = "") -> HehunRow:
    """账本的一行未折入前的形。短名带后缀：同一个键在一份账本里可以出现三次
    （乾月×坤年、乾日×坤年、乾时×坤时），不带格位就读不出那一行是谁加的分 ——
    与岁运 `hit_rows` 的（流月）后缀是同一条纪律（`bazi_transit.py:436`）。
    """
    rule = hehun_rule(rule_key)
    return HehunRow(
        rule=rule.key,
        label=rule.label + suffix,
        family=rule.family,
        direction=direction,
        delta=rule.delta,
    )


def _cell_suffix(hit: CrossHit) -> str:
    return f"（乾{PILLAR_NAME[hit.male_position]}×坤{PILLAR_NAME[hit.female_position]}）"


def relation_rows(pair: HehunChartPair) -> list[HehunRow]:
    """对称族：跨造关系每条一行，`(乾日, 坤日)` 那一格里被婚姻宫收编的除外（§6.2）。

    柱级成立时整格封口（该格的干、支两级全部不再各记一条）；否则只按层收编 ——
    日干五合收干级那一条、日支六合或三合半合收支级那一条。日干相冲没有婚姻宫键，
    所以它既不被收编也不算双计（`SEALED_DAY_CELL_KINDS` 里没有它就是这个意思）。
    矩阵不受影响：它是呈现层的完整视图，那一格照样显示扫到的一切。
    """
    palace = palace_keys(pair)
    sealed_whole_cell = PALACE_PILLAR_REVERSE in palace
    rows: list[HehunRow] = []
    for hit in cross_relations(pair):
        in_palace = (hit.male_position, hit.female_position) == ("day", "day")
        if in_palace and (sealed_whole_cell or hit.kind in SEALED_DAY_CELL_KINDS):
            continue
        rows.append(_to_row(hit.rule, "mutual", _cell_suffix(hit)))
    return rows


def pair_matrix(pair: HehunChartPair) -> list[HehunCell]:
    """乾四柱 × 坤四柱 = 恒 16 格；空格是 `hits: []`，前端渲染成「无」（§10.6）。

    矩阵是呈现层的完整视图：(乾日, 坤日) 那一格里被婚姻宫族收编的关系**照样显示**，
    只是不再进账本 —— 账本与矩阵的分歧是 §6.2 那条归属规则的必然结果，不是 bug。
    """
    hits = cross_relations(pair)
    return [
        HehunCell(
            male_position=male,
            female_position=female,
            hits=[
                HehunCellHit(
                    kind=hit.kind,
                    male_character=hit.male_character,
                    female_character=hit.female_character,
                    rule=hit.rule,
                )
                for hit in hits
                if (hit.male_position, hit.female_position) == (male, female)
            ],
        )
        for male in POSITION_ORDER
        for female in POSITION_ORDER
    ]


# ---------------------------------------------------------------- 互济族（spec §2.6、§7.1）

#: 四象限的表：(账本键, 单字格名, 纵轴, 横轴)。序即 §7.1 那张表的阅读序，
#: 也是响应里 `cells` 的恒定长度与顺序。`平` 不在横轴里 ——
#: §7.1 那句"平既不落象限也不入账本"就是这么落进数据结构的。
YONGSHEN_QUADRANTS: tuple[tuple[str, str, str, str], ...] = (
    ("hh.yongshen.supply", "补", "favorable", "旺"),
    ("hh.yongshen.shortfall", "阙", "favorable", "弱"),
    ("hh.yongshen.clash", "冲", "unfavorable", "旺"),
    ("hh.yongshen.harmless", "安", "unfavorable", "弱"),
)

#: (该行是不是我的喜用, 彼造这一行的旺弱) → 账本键。由上面那张表倒推，
#: 于是"加一格象限"与"加一条账本键"在代码里是同一处改动，不可能只改一半。
YONGSHEN_QUADRANT: dict[tuple[bool, Vigor], str] = {
    (mine == "favorable", theirs): rule for rule, _name, mine, theirs in YONGSHEN_QUADRANTS
}


@dataclass(frozen=True)
class YongshenView:
    """一个视角的身份三件套，三件写在一处。

    `viewer` 是响应里的字段、`direction` 是账本行的字段、`label` 同时进账本短名与图。
    分成三处写就是三份真相：账上写「乾视坤」而图上写「坤视乾」这种事，只有同源才防得住。
    """

    viewer: PartnerSide
    direction: str
    label: str


#: 互济族的两个视角（§6.2：五族里唯一天生有向的一族）。互补图按 `direction` **等值**分桶，
#: 不靠前缀猜 —— `HehunDirection` 是三个值的闭集（另有 `mutual`），等值才读得出"就是那一向"。
YONGSHEN_VIEWS: tuple[YongshenView, ...] = (
    YongshenView(viewer="male", direction="male_to_female", label="乾视坤"),
    YongshenView(viewer="female", direction="female_to_male", label="坤视乾"),
)


@dataclass(frozen=True)
class YongshenFact:
    """互济族的一次命中：账本行 + 它在互补图里的坐标。

    图与账本同源（§7.1）：同一个对象既出那一行账，也出图上的那一格，
    两处不可能一个有分、一个有格。`ratio` 直接引 `element_ratios` 的四位读数：图上写的
    数与判档用的数是同一个数，所以看图永远推得出账。
    """

    row: HehunRow
    element: str
    vigor: Vigor
    ratio: float


def element_ratios(chart: BaziChart) -> dict[str, float]:
    """该造五行各自对其自身五行均值的比值，取四位 —— §2.6 那把尺的读数，还没贴标签。

    单独一处是因为互补图要把比值本身给出去（"这一行为什么算旺"得当场可核），而图与
    标签必须出自同一个数：让图去重算一遍，两边迟早分家。取四位同时是为了让边界不落在
    浮点尾差上：权重是累加出来的，`1.2 / 1.6` 给的是 `0.7500000000000001`，不取整就会
    把一条数学上正好压界（§2.6 归"弱"）的比值判成"平"。页面上看到的数与被判定的数，
    从此是同一个数。
    """
    scores = element_weight_scores(chart.pillars)
    mean = sum(scores.values()) / len(scores)
    return {element: round(score / mean, 4) for element, score in scores.items()}


def element_vigor(chart: BaziChart) -> dict[str, Vigor]:
    """该造五行的旺/弱/平标签（§2.6）。

    站里给得出的是**量**（`element_weight_scores`：四干各 1.0 加藏干本中余 0.6/0.3/0.1），
    没有任何一处给过"某行旺不旺"的标签，所以这一把尺本轮由本系统立，且只立在这一处：
    基准是**该造自己的五行均值**，比值 ≥1.25 为旺、≤0.75 为弱、其余为平。
    拿盘内均值当基准是因为"在这个人的盘里这一行算不算多"本来就是盘内比较 ——
    跨盘比原始分值没有意义，两造的总量本来就接近（§2.6）。
    均值恒为正（四柱八个小干与藏干必有权重），所以这里不设除零分支。
    """
    return {
        element: "旺" if ratio >= STRONG_RATIO else "弱" if ratio <= WEAK_RATIO else "平"
        for element, ratio in element_ratios(chart).items()
    }


def _one_view_facts(me: BaziChart, other: BaziChart, direction: str, where: str) -> list[YongshenFact]:
    """一个视角的四象限：先喜用（补/阙）后忌神（冲/安），组内按该造喜忌集的序。

    `where` 是短名里的"乾视坤/坤视乾" —— 两个视角的行同键同 delta，
    不带这一处就分不出是谁的喜用在说话（§6.1：一条账本行的身份是 (族, 视角, 五行)）。
    """
    theirs = element_vigor(other)
    ratios = element_ratios(other)
    facts: list[YongshenFact] = []
    for favorable, elements in (
        (True, me.analysis.favorable_elements),
        (False, me.analysis.unfavorable_elements),
    ):
        for element in elements:
            vigor = theirs[element]
            rule_key = YONGSHEN_QUADRANT.get((favorable, vigor))
            if rule_key:
                facts.append(
                    YongshenFact(
                        row=_to_row(rule_key, direction, f"（{where}·{element}{vigor}）"),
                        element=element,
                        vigor=vigor,
                        ratio=ratios[element],
                    )
                )
    return facts


def yongshen_facts(pair: HehunChartPair) -> list[YongshenFact]:
    """互济族的全部事实：两向各一组（§6.2，五族里唯一天生有向的一族）。

    这是账本与互补图共同的唯一来源。两造的喜忌一律直接取各自本命盘，合婚不重判（决策 3）。
    """
    male_view, female_view = YONGSHEN_VIEWS
    return [
        *_one_view_facts(pair.male, pair.female, male_view.direction, male_view.label),
        *_one_view_facts(pair.female, pair.male, female_view.direction, female_view.label),
    ]


def yongshen_rows(pair: HehunChartPair) -> list[HehunRow]:
    return [fact.row for fact in yongshen_facts(pair)]


def complement(pair: HehunChartPair) -> HehunComplement:
    """五行互补图（§7.1）：把同一批事实按 (视角, 象限) 分桶，一格不漏也不增。

    分桶靠 `row.rule` 与 `row.direction` 这两个已有字段，不看 element 也不看 vigor ——
    图的结构是账本的投影，不是第二次判定。视角与 direction 之间是**等值**关系（表里那一个值），
    不靠前缀相似：`HehunDirection` 另有 `mutual`，等值才读得出"就是那一向"。
    空格的 `elements` 为空列表（§10.6），前端才敢把"无"渲染出来。
    """
    facts = yongshen_facts(pair)
    return HehunComplement(
        views=[
            HehunComplementView(
                viewer=view.viewer,
                label=view.label,
                cells=[
                    HehunComplementCell(
                        rule=rule,
                        name=name,
                        mine=mine,  # pydantic 的 Literal 校验挡得住：表里只有这两个值
                        theirs=theirs,
                        delta=hehun_rule(rule).delta,
                        elements=[
                            HehunComplementElement(element=fact.element, ratio=fact.ratio)
                            for fact in facts
                            if fact.row.direction == view.direction and fact.row.rule == rule
                        ],
                    )
                    for rule, name, mine, theirs in YONGSHEN_QUADRANTS
                ],
            )
            for view in YONGSHEN_VIEWS
        ]
    )


# ---------------------------------------------------------------- 年命纳音（spec §7.2）
def nayin_phrase(mine: str, theirs: str, relation: str) -> str:
    """三字生克句：`生我` → 水生木、`比和` → 木与木同气。

    句式而非表：五行只有五对生克，写成一张 5×5 表就是四处要维护的字符串。
    主语固定为乾（`mine` 即乾的年命五行，§6.2），所以 `生我` 的"生者"是彼造。
    """
    if relation == "比和":
        return f"{mine}与{mine}同气"
    if relation == "生我":
        return f"{theirs}生{mine}"
    if relation == "我生":
        return f"{mine}生{theirs}"
    if relation == "我克":
        return f"{mine}克{theirs}"
    return f"{theirs}克{mine}"


def nayin_side(chart: BaziChart) -> HehunNayinSide:
    """一造的年命纳音。取象原文与书名一律从 `NayinCorpus` 直取，本模块一个字都不写。"""
    corpus = nayin_meaning(_pillar(chart, "year").ganzhi)
    return HehunNayinSide(
        ganzhi=_pillar(chart, "year").ganzhi,
        nayin=corpus.nayin,
        element=corpus.element,
        imagery=corpus.imagery,
        source=corpus.source,
    )


def nayin_view(pair: HehunChartPair) -> HehunNayin:
    """纳音段：两造年命 + 一句判语，键与分值逐字取自年命族那一行账。

    判语按 §7.2 的固定句式装配（不是引擎自己组句子，是把三处现成件按同一顺序拼起来：
    纳音名、生克句、该键在规则表里的 `reading`），末尾的尾注与规则表的 source 同一口径。
    设计稿"乾坤双人档案"那一栏要的意象原文也由本段给出（Task 11 的档案组件读这里）。
    """
    male, female = nayin_side(pair.male), nayin_side(pair.female)
    relation = nayin_relation(pair)
    row = nayin_row(pair)
    phrase = nayin_phrase(male.element, female.element, relation)
    return HehunNayin(
        male=male,
        female=female,
        relation=relation,
        phrase=phrase,
        rule=row.rule,
        delta=row.delta,
        reading=(
            f"乾年命{male.nayin}、坤年命{female.nayin}，{phrase}为{relation}；"
            f"{hehun_rule(row.rule).reading}。{HEHUN_NAYIN_NOTE}"
        ),
    )


# ---------------------------------------------------------------- 总账本（spec §6.1、§6.4）
def hehun_rows(pair: HehunChartPair) -> list[HehunRow]:
    """五族装配成一份账本的行，序即 `HEHUN_FAMILIES`：对称→成局→互济→年命→婚姻宫。

    婚姻宫族排在最后不是凑顺序：它是唯一会**改写前面几族**的一族（§6.2 的封口），
    放在末尾读起来正是"前面记下的一切，到这一格按宫位归属重新收一次"。
    """
    return [
        *relation_rows(pair),
        *group_rows(pair),
        *yongshen_rows(pair),
        nayin_row(pair),
        *palace_rows(pair),
    ]


def hehun_tier(value: float) -> str:
    """四档（§6.4）。中间两道分界直接引旺衰那两条常量，只在上面加一条 80（决策 5）。

    最低档刻意不叫"待化解"：本轮不做任何化解物品与风水手段（§4.2），
    给一个暗示"有解法"的档位名就是在替页面上不存在的内容打广告。
    注意同一份响应里有两套档位词汇 —— 轴行里两造各自的档是岁运的 顺/平/滞（`_tier()`），
    两套不合并（它们回答的是"你们合不合"与"这一年他顺不顺"两个问题）。
    """
    if value >= HEHUN_TOP_CUT:
        return "天作之合"
    if value >= STRONG_CUT:
        return "相得益彰"
    return "中和可处" if value >= WEAK_CUT else "欠和宜慎"


def hehun_ledger(rows: Sequence[HehunRow]) -> ScoreValue:
    """行 → 自解释总分；截断由 `build_ledger` 记成它自己的一行（与 `transit_ledger` 同形）。

    档位取**截断后**的值：§6.4 说的是"页面显示的那个数落在哪一档"，
    让 `value == 99` 与 `value == 100` 分属两档是一个可读性 bug，不是精度问题。
    """
    raw_total = HEHUN_BASE + sum(row.delta for row in rows)
    return build_ledger(
        base=HEHUN_BASE,
        tier=hehun_tier(min(100.0, max(0.0, raw_total))),
        contributions=[
            ScoreFactor(rule=row.rule, label=row.label, delta=row.delta, source=HEHUN_RULE_SOURCE)
            for row in rows
        ],
        base_rule="hehun.base",
    )


def hehun_fired(rows: Sequence[HehunRow]) -> list[HehunFired]:
    """账本行的人类可读镜像：键、短名、族、视角、分值逐字取自那一行，判语取自规则表。

    `fired` 与 `score.factors` 按序一一对齐（§10.6 的"账本与判语不分家"），
    所以前端可以按行渲染，不必拿 `rule` 去两处之间做 join。
    """
    return [
        HehunFired(
            rule=row.rule,
            label=row.label,
            family=row.family,
            direction=row.direction,
            delta=row.delta,
            reading=hehun_rule(row.rule).reading,
        )
        for row in rows
    ]
