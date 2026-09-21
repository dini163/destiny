"""神煞与干支关系的推导：只查 `content/bazi_shensha`、`content/bazi_relations` 两张表。

本模块不产文案、不硬编码古籍字：释义与出处一律随表走（spec §5 的分层）。表里
`lookup`/`target` 两轴（拿什么去查 / 查到的字匹配干还是支）在这里被翻译成一次
扫描；表若新增一轴取值，本模块会明确落到 `else` 分支报错，而不是静默少查一类。
"""

from collections.abc import Collection, Sequence
from dataclasses import dataclass

from app.content.bazi_relations import RELATION_TABLES, RelationRule, transforming_element
from app.content.bazi_shensha import SHENSHA_RULES, ShenShaRule, san_he_group
from app.schemas.bazi import BaziPillar
from app.schemas.bazi_rules import (
    BranchGroup,
    BranchMember,
    RelationPair,
    ShenShaEntry,
    ShenShaMatch,
)

POSITIONS: tuple[str, ...] = ("year", "month", "day", "hour")
# 柱位距离 -> 力量标注（spec §6.3：相邻 > 隔位 > 远位，是可核对的位置规则而非赋分）。
# 只有三档：大运、流年在四柱之外，距离再远也不另立第四档。
STRENGTH_BY_DISTANCE = {1: "紧临", 2: "隔位"}
FARTHEST = "远位"
# 反吟判定复用相冲两张表，不另立常数（同一事实只留一处）。
_GAN_CHONG = RELATION_TABLES["天干相冲"].pairs
_ZHI_CHONG = RELATION_TABLES["地支六冲"].pairs


@dataclass(frozen=True)
class _Slot:
    """一柱（或一个外来干支）在扫描中的可查投影。"""

    position: str
    gan: str
    zhi: str
    index: int
    xun: str = ""
    xun_kong: tuple[str, ...] = ()


def _slots(pillars: list[BaziPillar], extra_ganzhi: Sequence[str] = ()) -> list[_Slot]:
    slots = [
        _Slot(p.position, p.gan, p.zhi, i, p.xun, tuple(p.xun_kong))
        for i, p in enumerate(pillars)
    ]
    for n, ganzhi in enumerate(extra_ganzhi):  # 大运/流年参与伏吟·反吟扫描
        slots.append(_Slot(f"extra{n}", ganzhi[0], ganzhi[1], len(pillars) + n))
    return slots


def _order(position: str) -> int:
    return POSITIONS.index(position) if position in POSITIONS else len(POSITIONS)


def _strength(distance: int) -> str:
    return STRENGTH_BY_DISTANCE.get(distance, FARTHEST)


# ---------------------------------------------------------------- 神煞（spec §6.2）
def _shensha_base_and_targets(
    rule: ShenShaRule, slots: list[_Slot], day_master: str
) -> tuple[str, Collection[str], str]:
    """Resolve a rule into the (checked_from, targets, side) it looks up by."""
    if rule.lookup == "day_gan":
        # 羊刃表只有五阳干（五阴无刃），日干查无此键即"本无是煞"，与"查了没落点"同归空集。
        return f"日干{day_master}", rule.table.get(day_master, ()), "zhi"
    if rule.lookup == "month_zhi":  # 天德：月支 → 干或支
        return f"月支{slots[1].zhi}", rule.table[slots[1].zhi], rule.target
    if rule.lookup == "month_zhi_group":  # 月德：月支三合局 → 干
        group = san_he_group(slots[1].zhi)
        return f"{group}局", rule.table[group], "gan"
    if rule.lookup == "year_and_day_group":  # 咸池/驿马/华盖…：年支、日支各起一局
        # 基准两字不同就有两局，合并目标但把两局都记进 checked_from，
        # 否则读者分不清"查过两局都落空"与"只查过一局"。
        groups = list(
            dict.fromkeys(g for g in (san_he_group(s.zhi) for s in (slots[0], slots[2])) if g)
        )
        targets = {t for group in groups for t in rule.table[group]}
        return "、".join(f"{group}局" for group in groups), targets, "zhi"
    if rule.lookup == "void":  # 空亡：日柱旬空，查四支
        day = slots[2]
        return f"日柱{day.gan}{day.zhi}·{day.xun}旬", day.xun_kong, "zhi"
    if rule.lookup == "day_pillar":  # 魁罡：整柱比对，无键
        return f"日柱{slots[2].gan}{slots[2].zhi}", rule.table, "pillar"
    raise ValueError(f"未知神煞基准：{rule.lookup}（{rule.name}）")


def derive_shensha(
    pillars: list[BaziPillar],
    *,
    day_master: str,
    extra_ganzhi: Sequence[str] = (),
) -> list[ShenShaEntry]:
    """Return every 神煞 that actually hits; a rule with no match is omitted (spec §6.2).

    `extra_ganzhi` 是岁运之柱（流年、流月、大运）：煞以命立、应期在岁运，所以神煞
    的落点要连同它们一起扫。两个例外按各自的定义域收窄 —— 魁罡只论日柱、空亡以
    日柱旬空查命局四支，岁运之字落在里头也不算命中（spec §7.5）。默认不传时输出
    与命局扫描逐字相等（spec §9.2）。
    """
    slots = _slots(pillars, extra_ganzhi)
    entries: list[ShenShaEntry] = []
    for rule in SHENSHA_RULES.values():
        if rule.lookup == "life_stage":
            continue  # 十二长生只在 pillar.di_shi 呈现一次，不在神煞行复读
        checked_from, targets, side = _shensha_base_and_targets(rule, slots, day_master)
        if side == "pillar":
            scope = [slots[2]]  # 魁罡只看日柱：若也扫四柱，时柱壬辰会被报成魁罡，
            # 而 checked_from 说的是日柱，两处口径就打架了。
        elif rule.lookup == "void":
            scope = slots[: len(POSITIONS)]  # 空亡的查法是"命局四支"，不落岁运。
        else:
            scope = slots  # 命局四柱 + 岁运之柱。
        matches = _shensha_matches(scope, targets, side)
        if matches:
            entries.append(
                ShenShaEntry(
                    name=rule.name,
                    quality=rule.quality,
                    checked_from=checked_from,
                    matches=matches,
                    meaning=rule.meaning,
                    source=rule.source,
                )
            )
    return entries


def _shensha_matches(
    slots: list[_Slot], targets: Collection[str], side: str
) -> list[ShenShaMatch]:
    """Report hits down to (柱位, 字, 干/支侧) so the UI can mark them on the chart."""
    found: list[ShenShaMatch] = []
    for slot in slots:
        if side in ("gan", "gan_or_zhi") and slot.gan in targets:
            found.append(ShenShaMatch(position=slot.position, character=slot.gan, at="gan"))
        if side in ("zhi", "gan_or_zhi") and slot.zhi in targets:
            found.append(ShenShaMatch(position=slot.position, character=slot.zhi, at="zhi"))
        if side == "pillar" and slot.gan + slot.zhi in targets:
            found.append(
                ShenShaMatch(
                    position=slot.position, character=slot.gan + slot.zhi, at="pillar"
                )
            )
    return found


# ---------------------------------------------------------------- 二元关系（spec §6.3）
def _pair_hit(rule: RelationRule, a: _Slot, b: _Slot) -> RelationPair | None:
    """Match one binary rule against one slot pair (pairs are unordered by construction)."""
    if rule.scope == "pillar":
        left, right = a.gan + a.zhi, b.gan + b.zhi
        if rule.kind == "伏吟":
            hit = left == right
        else:  # 反吟：天干相冲 且 地支六冲（表里 reading 已写明这个窄口径）
            hit = (left[0], right[0]) in _GAN_CHONG and (left[1], right[1]) in _ZHI_CHONG
    else:
        side = rule.side or ("gan" if rule.scope == "stem" else "zhi")
        left, right = (a.gan, b.gan) if side == "gan" else (a.zhi, b.zhi)
        hit = (left, right) in rule.pairs or (right, left) in rule.pairs
    if not hit:
        return None
    return RelationPair(
        kind=rule.kind,
        pillar_a=a.position,
        pillar_b=b.position,
        character_a=left,
        character_b=right,
        strength=_strength(abs(a.index - b.index)),
        # rule.element 是"字对 -> 五行"的字典，不是单个五行；只有 天干五合 带表，
        # 命中哪一对才取哪一行的值（六合 无表 → None）。
        transforming_element=transforming_element(rule.kind, left, right),
        reading=rule.reading,
        source=rule.source,
    )


def derive_relations(
    pillars: list[BaziPillar], extra_ganzhi: Sequence[str] = ()
) -> list[RelationPair]:
    """Scan every *binary* relation: stem pairs, branch pairs, 伏吟·反吟."""
    binary = [rule for rule in RELATION_TABLES.values() if rule.scope != "group"]
    slots = _slots(pillars, extra_ganzhi)
    hits: list[RelationPair] = []
    for i in range(len(slots)):  # 柱序在外 → 输出天然按位置排好
        for j in range(i + 1, len(slots)):
            hits.extend(
                hit
                for hit in (_pair_hit(rule, slots[i], slots[j]) for rule in binary)
                if hit
            )
    return hits


# ---------------------------------------------------------------- 合局（spec §6.3）
def derive_branch_groups(
    pillars: list[BaziPillar], extra_ganzhi: Sequence[str] = ()
) -> list[BranchGroup]:
    """Three-harmony / half-combination / three-meeting, as *groups* with their members.

    `extra_ganzhi` 参与成局：岁支可以是三合局的第三支（申子辰只缺申，流年补申即
    成局）。成员落在岁运柱上时 `ten_god` 仍为空串 —— 十神是命局内部的坐标，
    不给四柱之外的柱立十神（spec §7.5）。
    """
    slots = _slots(pillars, extra_ganzhi)
    groups: list[BranchGroup] = []
    for rule in RELATION_TABLES.values():
        if rule.scope != "group":
            continue
        for pattern, element in rule.groups.items():  # {"申子辰": "水", ...}
            present = [slot for slot in slots if slot.zhi in pattern]
            branches = {slot.zhi for slot in present}
            complete = branches == set(pattern)
            if rule.kind == "半合":
                # 半合 = 三合局见二字且含旺支；三支齐见时归三合那条，不重复出。
                if complete or len(branches) != 2 or rule.peaks[pattern] not in branches:
                    continue
            elif not complete:
                continue  # 三合、三会都要三支齐见
            groups.append(
                BranchGroup(
                    kind=rule.kind,
                    element=element,
                    is_complete=complete,
                    members=[
                        BranchMember(
                            pillar=slot.position, branch=slot.zhi, ten_god=_god(pillars, slot)
                        )
                        for slot in present
                    ],
                    reading=rule.reading,
                    source=rule.source,
                )
            )
    return sorted(groups, key=lambda group: _order(group.members[0].pillar))


def _god(pillars: list[BaziPillar], slot: _Slot) -> str:
    """该支本气藏干对日主的十神；外来干支（extra）不参与，返回空串。"""
    pillar = next((p for p in pillars if p.position == slot.position), None)
    return pillar.shishen_zhi[0] if pillar and pillar.shishen_zhi else ""
