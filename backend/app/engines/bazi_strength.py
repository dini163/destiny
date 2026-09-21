"""三因子日主旺衰（得令/得地/得势）+ 月令定格 + 藏干权重账本 + 扶抑喜忌，逐项留账。

本模块是 spec §6.1/§6.4/§6.5 第 1 法的直译：权重、阈值、间距都在下面显式声明为
模型参数，`source` 一律引用 ``MODEL_PARAM_SOURCE``。引擎不产中文明细文案，只产
规则键与数字（spec §5）；账本 `label` 里带上算式，使每个数都能就地复核。
格局判语（`GeJu.notes`）是从 `content/bazi_geju` 的署名条目里**整句选出**，
引擎只做十神查表与选择，不组句、不改写。
"""

from collections.abc import Sequence

from app.content.bazi_geju import GejuRule, geju_rule
from app.content.bazi_shensha import shen_sha_rule
from app.content.bazi_wangshuai import WANG_SHUAI_VALUE, wang_shuai
from app.content.wuxing import (
    CONTROLLED_BY,
    CONTROLS,
    ELEMENT_ORDER,
    GENERATED_BY,
    GENERATES,
    ZHI_ELEMENT,
)
from app.schemas.bazi import BaziPillar
from app.schemas.bazi_strength import GeJu, HiddenStemWeight
from app.schemas.scoring import MODEL_PARAM_SOURCE, ScoreFactor, ScoreValue, build_ledger
from pydantic import BaseModel, Field

# 藏干本/中/余气权重（spec §6.1）；单藏干支的本气即整支，取 1.0。
HIDDEN_STEM_WEIGHTS: tuple[float, float, float] = (0.6, 0.3, 0.1)
SINGLE_HIDDEN_STEM_WEIGHT: float = 1.0
STEM_WEIGHT = 1.0
HIDDEN_STEM_ROLES = ("本气", "中气", "余气")
# 比劫不分取用：月支本气是比劫时，该支不 alone 成格，退藏干次层或落禄刃（spec §6.4）。
PARALLEL_GODS = frozenset({"比肩", "劫财"})
# 三因子权重与档位分界（spec §6.4，模型参数）。
FACTOR_WEIGHTS: tuple[float, float, float] = (0.4, 0.4, 0.2)
STRONG_CUT = 65.0
WEAK_CUT = 45.0
BORDERLINE_BAND = 3.0


class StrengthAssessment(BaseModel):
    """A band label plus the ledger that produced it; ``level`` feeds ``fuyin_choices``.

    三因子的原值（0-100，未乘权重）同时以标量给出：§6.6 的学业维要看"得地"一项，
    从 `factors` 里按 `rule` 字符串反抓数值会把计算层与展示层焊死（换个 label 就断）。
    `score` 仍由这三个值经 `build_ledger` 构造，同一次计算不留第二处口径。
    """

    score: ScoreValue
    level: str = Field(description="weak | balanced | strong")
    label: str = Field(description="身弱 | 中和 | 身强")
    borderline: bool = Field(description="距最近分界 < BORDERLINE_BAND。")
    deling: float = Field(description="得令：日主五行在月令的旺相休囚死等第（0-100）。")
    dedi: float = Field(description="得地：通根权重占四支藏干满分之比（0-100）。")
    deshi: float = Field(description="得势：年/月/时三干中生扶者占比（0-100）。")


def hidden_stem_weight(index: int, stem_count: int) -> float:
    """Weight of the ``index``-th hidden stem of a branch holding ``stem_count`` stems."""
    if stem_count == 1:
        return SINGLE_HIDDEN_STEM_WEIGHT
    return HIDDEN_STEM_WEIGHTS[min(index, len(HIDDEN_STEM_WEIGHTS) - 1)]


def element_weight_scores(pillars: list[BaziPillar]) -> dict[str, float]:
    """Weighted presence per element: four stems at 1.0 plus each hidden stem by its role."""
    scores = {element: 0.0 for element in ELEMENT_ORDER}
    for pillar in pillars:
        scores[pillar.gan_element] += STEM_WEIGHT
        for index, element in enumerate(pillar.hidden_stem_elements):
            scores[element] += hidden_stem_weight(index, len(pillar.hidden_stem_elements))
    return scores


def _supporting_elements(day_master_element: str) -> set[str]:
    """同我（比劫）+ 生我（印）。取的是 GENERATED_BY，不是 GENERATES。"""
    return {day_master_element, GENERATED_BY[day_master_element]}


def _root_weights(pillars: list[BaziPillar]) -> list[tuple[str, float]]:
    """四支藏干的 (五行, 权重) 清单，顺序为柱序再为本/中/余气。"""
    return [
        (element, hidden_stem_weight(index, len(pillar.hidden_stem_elements)))
        for pillar in pillars
        for index, element in enumerate(pillar.hidden_stem_elements)
    ]


def _de_ling(day_master_element: str, month_zhi: str) -> tuple[float, str, str]:
    """得令：日主五行在该月令的旺相休囚死等第（spec §6.4 第 1 因子）。"""
    month_element = ZHI_ELEMENT[month_zhi]
    grade = wang_shuai(day_master_element, month_element)
    return (
        WANG_SHUAI_VALUE[grade],
        f"strength.deling.{grade}",
        f"得令 · 月令{month_zhi}（{month_element}）· 日主{day_master_element}处{grade}",
    )


def _de_di(pillars: list[BaziPillar], day_master_element: str) -> tuple[float, str]:
    """得地：通根权重占四支藏干满分之比，归一到 0-100（spec §6.4 第 2 因子）。"""
    supporting = _supporting_elements(day_master_element)
    roots = _root_weights(pillars)
    full_weight = sum(weight for _, weight in roots)
    if not full_weight:
        return 0.0, "得地 · 四支无藏干"
    rooted = sum(weight for element, weight in roots if element in supporting)
    share = rooted / full_weight * 100.0
    return share, f"得地 · 通根 {rooted:.2f}/{full_weight:.2f} × 100"


def _de_shi(pillars: list[BaziPillar], day_master_element: str) -> tuple[float, str]:
    """得势：年/月/时三干的生扶占比，天干无藏干权重、权重恒 1（spec §6.4 第 3 因子）。"""
    supporting = _supporting_elements(day_master_element)
    others = [pillar for pillar in pillars if pillar.position != "day"]
    hits = [pillar for pillar in others if pillar.gan_element in supporting]
    share = len(hits) / len(others) * 100.0 if others else 0.0
    listed = "、".join(f"{pillar.label}干{pillar.gan}" for pillar in hits) or "无"
    return share, f"得势 · 生扶 {len(hits)}/{len(others)} 干（{listed}）"


def _band(score: float) -> tuple[str, str]:
    if score >= STRONG_CUT:
        return "strong", "身强"
    if score >= WEAK_CUT:
        return "balanced", "中和"
    return "weak", "身弱"


def _is_borderline(score: float) -> bool:
    return min(abs(score - STRONG_CUT), abs(score - WEAK_CUT)) < BORDERLINE_BAND


def assess_strength(pillars: list[BaziPillar]) -> StrengthAssessment:
    """Score 得令/得地/得势 on one 0-100 axis and return the band with its ledger."""
    day_pillar = next(p for p in pillars if p.position == "day")
    month_pillar = next(p for p in pillars if p.position == "month")
    day_master_element = day_pillar.gan_element

    deling_value, deling_rule, deling_label = _de_ling(day_master_element, month_pillar.zhi)
    dedi_value, dedi_label = _de_di(pillars, day_master_element)
    deshi_value, deshi_label = _de_shi(pillars, day_master_element)

    contributions = (
        (deling_rule, deling_label, FACTOR_WEIGHTS[0], deling_value),
        ("strength.dedi.share", dedi_label, FACTOR_WEIGHTS[1], dedi_value),
        ("strength.deshi.share", deshi_label, FACTOR_WEIGHTS[2], deshi_value),
    )
    deltas = [round(weight * value, 4) for _, _, weight, value in contributions]
    # 三因子各 0-100、权重和为 1，故合计必在 0-100 内、不会被 build_ledger 截断；
    # 档位因此按它取整后的同一个数判定，不留两处口径。
    level, label = _band(round(sum(deltas), 2))
    ledger = build_ledger(
        base=0.0,
        base_rule="strength.base",
        tier=label,
        contributions=[
            ScoreFactor(
                rule=rule,
                label=f"{factor_label} × {weight} = {delta:.2f}",
                delta=delta,
                source=MODEL_PARAM_SOURCE,
            )
            for (rule, factor_label, weight, _), delta in zip(contributions, deltas)
        ],
    )
    return StrengthAssessment(
        score=ledger, level=level, label=label, borderline=_is_borderline(ledger.value),
        deling=deling_value, dedi=dedi_value, deshi=deshi_value,
    )


def fuyin_choices(
    level: str, day_master_element: str, element_scores: dict[str, float]
) -> tuple[list[str], list[str]]:
    """扶抑：身弱取生扶、身强取克洩耗、中和不取。集合按命局加权分降序输出。

    排序规则可核对（spec §6.5 只给合并口径、不给次序，这里锁定"加权分降序"一种），
    前端因此不需要再排一次。
    """
    if level == "balanced":
        return [], []

    def rank(elements: set[str]) -> list[str]:
        return sorted(elements, key=lambda e: (-element_scores[e], ELEMENT_ORDER.index(e)))

    support = _supporting_elements(day_master_element)
    # 扶抑忌神集 = 克我（官杀）+ 我克（财）+ 我生（食伤）；生扶集 = 同我 + 生我。
    drain = {CONTROLLED_BY[day_master_element], CONTROLS[day_master_element],
             GENERATES[day_master_element]}
    if level == "weak":
        return rank(support), rank(drain)
    return rank(drain), rank(support)


def detect_geju(pillars: list[BaziPillar]) -> GeJu:
    """Month-branch hidden stems set the structure, main qi first (spec §6.4)."""
    month = next(pillar for pillar in pillars if pillar.position == "month")
    day = next(pillar for pillar in pillars if pillar.position == "day")
    ten_god = next((g for g in month.shishen_zhi if g not in PARALLEL_GODS), None)
    if ten_god is None:
        # 整支皆比劫的月支只可能是日干之禄或刃：阳干见刃支为月刃，阴干无刃、其支即禄。
        name = "月刃格" if month.zhi in shen_sha_rule("羊刃").table.get(day.gan, ()) else "建禄格"
        ten_god = "比肩"
    else:
        name = f"{ten_god}格"
    rule = geju_rule(name)
    is_success, notes = geju_verdict(rule, _transparent_gods(pillars))
    return GeJu(
        name=name,
        from_pillar="month",
        ten_god=ten_god,
        is_success=is_success,
        notes=notes,
        source=rule.source,
    )


def _transparent_gods(pillars: list[BaziPillar]) -> list[str]:
    """年/月/时三天干的十神，去重保柱序 —— 古法所谓"透干"，藏干不参与判格。"""
    gods: list[str] = []
    for pillar in pillars:
        if pillar.position != "day" and pillar.shishen_gan not in gods:
            gods.append(pillar.shishen_gan)
    return gods


def geju_verdict(rule: GejuRule, transparent_gods: Sequence[str]) -> tuple[bool, list[str]]:
    """破格优先于成格之助；两不命中记 unsupported，不默认成格（spec §6.4）。"""
    broken = [rule.breaking[god] for god in transparent_gods if god in rule.breaking]
    if broken:
        return False, broken
    supported = [rule.supporting[god] for god in transparent_gods if god in rule.supporting]
    if supported:
        return True, supported
    return False, [rule.unsupported]


def hidden_stem_ledger(pillars: list[BaziPillar]) -> list[HiddenStemWeight]:
    """One row per hidden stem with its role, weight and ten-god (spec §6.1, §7)."""
    return [
        HiddenStemWeight(
            position=pillar.position,
            branch=pillar.zhi,
            stem=stem,
            role=HIDDEN_STEM_ROLES[index],
            weight=hidden_stem_weight(index, len(pillar.hidden_stems)),
            ten_god=ten_god,
            source=MODEL_PARAM_SOURCE,
        )
        for pillar in pillars
        for index, (stem, ten_god) in enumerate(
            zip(pillar.hidden_stems, pillar.shishen_zhi, strict=True)
        )
    ]
