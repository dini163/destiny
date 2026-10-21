"""Six-dimension readings: a pure map from earlier verdicts onto one ledger per axis.

本模块不判命、不组句：命是前序引擎的结论（旺衰、格局、喜忌、神煞、关系、合局），
句子是 `content/bazi_dimensions` 的署名条目。这里只做四件事 —— 把结论收成
`ChartSignals`、按 39 条（`DIMENSION_RULE_COUNT`）命中条件挑出因子、把因子交给
`build_ledger`、给每个维度按同一批命中键拼白话段（`build_plain`）。白话与判语同属
逐字搬运受控表（`content/bazi_plain` 与 `content/bazi_dimensions`），本模块不现编中文。
所有阈值（`STAR_PRESENT` 等）都是模型参数，判语里凡涉喜忌之处一律署"本系统"。
2026-10-21 verdict-card spec：结论卡片（档位 + 星级 + 结论句 + 分项 + 建议）的档位
由六维账本均值经 `app/engines/verdict.grade_for` 派生，四段文案由 `bazi_plain` 的
框架句 + 槽位语料装配，本模块只排装配、不写新句。
"""

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from statistics import mean

from app.content.bazi_dimensions import DIMENSION_BASE, DIMENSION_ORDER, DIMENSION_RULES, dim_rule
from app.content.bazi_plain import (
    PLAIN_SUMMARY_FRAME,
    TIER_ADVICE,
    VERDICT_ADVICE_FRAME,
    VERDICT_OUTLOOK,
)
from app.content.bazi_relations import RELATION_TABLES
from app.content.wuxing import CONTROLS, CONTROLLED_BY, ELEMENT_ORDER, GENERATED_BY, GENERATES
from app.core.provenance import MODEL_PARAM_SOURCE
from app.engines.bazi_strength import StrengthAssessment, element_weight_scores, hidden_stem_weight
from app.engines.plain_compose import compose, overview
from app.engines.plain_corpora import BAZI
from app.engines.verdict import grade_for
from app.schemas.bazi import BaziPillar
from app.schemas.bazi_interpret import BaziInterpretation, DimensionReading
from app.schemas.bazi_rules import BranchGroup, RelationPair, ShenShaEntry
from app.schemas.bazi_strength import GeJu, Yongshen
from app.schemas.common import Gender, Verdict
from app.schemas.scoring import ScoreFactor, build_ledger

TRANSPARENT_STEM_WEIGHT = 1.0  # 模型参数：天干一字一力，无藏干权重（§6.4 得势同款）
STAR_PRESENT = 1.0  # 阈值：1.0 = 一字透干，是最小可读单位，不是古籍赋分
STAR_ABUNDANT = 2.0
OFFICER_TRACE = 0.3
OFFICER_CEILING = 3.0
ROOT_STURDY = 2.0
ELEMENT_EXCESS = 0.35
ELEMENT_FLOW = 0.3
DEDI_FIRM = 50.0

TEN_GOD_GROUPS: dict[str, tuple[str, ...]] = {
    "officer": ("正官", "七杀"), "wealth": ("正财", "偏财"), "seal": ("正印", "偏印"),
    "output": ("食神", "伤官"), "parallel": ("比肩", "劫财"),
}
TEN_GODS = tuple(god for group in TEN_GOD_GROUPS.values() for god in group)
PALACE_BREAKING = frozenset(
    {"地支六冲", "地支六害", "无恩之刑", "恃势之刑", "无礼之刑", "自刑"}
)


def ten_god_strength(pillars: list[BaziPillar]) -> dict[str, float]:
    """十神分力：透干各 1.0 + 藏干按本/中/余气；日主本身不计入比劫。"""
    scores = dict.fromkeys(TEN_GODS, 0.0)
    for pillar in pillars:
        if pillar.position != "day":
            scores[pillar.shishen_gan] += TRANSPARENT_STEM_WEIGHT
        for index, god in enumerate(pillar.shishen_zhi):
            scores[god] += hidden_stem_weight(index, len(pillar.hidden_stem_elements))
    return scores


@dataclass(frozen=True)
class ChartSignals:
    """六维映射的全部输入；一次构建，逐维只读不算。"""

    gender: Gender | None
    level: str
    day_master_element: str
    element_scores: dict[str, float]
    gods: dict[str, float]
    groups: dict[str, float]
    favourable: frozenset[str]
    unfavourable: frozenset[str]
    geju_success: bool
    shensha: frozenset[str]
    relation_kinds: frozenset[str]
    day_branch_relations: frozenset[str]
    day_group_count: int
    dedi: float

    def group(self, name: str) -> float:
        return self.groups[name]

    def group_element(self, name: str) -> str:
        dm = self.day_master_element
        return {  # 克我=官杀、我克=财、生我=印、我生=食伤
            "officer": CONTROLLED_BY[dm], "wealth": CONTROLS[dm], "seal": GENERATED_BY[dm],
            "output": GENERATES[dm], "parallel": dm,
        }[name]

    def spouse_group(self) -> str:
        return "officer" if self.gender == Gender.FEMALE else "wealth"

    def is_favourable(self, name: str) -> bool:
        return self.group_element(name) in self.favourable

    def is_unfavourable(self, name: str) -> bool:
        return self.group_element(name) in self.unfavourable

    def star(self, name: str) -> bool:
        return name in self.shensha


def collect_signals(
    pillars: list[BaziPillar], *, gender: Gender | None, strength: StrengthAssessment,
    geju: GeJu, yongshen: Yongshen, shensha: Sequence[ShenShaEntry],
    relations: Sequence[RelationPair], branch_groups: Sequence[BranchGroup],
) -> ChartSignals:
    """Fold Tasks 5-8's verdicts into the one read-only object every dimension maps from."""
    day = next(pillar for pillar in pillars if pillar.position == "day")
    gods = ten_god_strength(pillars)
    day_relations = {
        relation.kind
        for relation in relations
        # 配偶宫只看支系关系：伏吟/反吟比的是整柱、干冲比的是干，都不动宫位。
        if "day" in (relation.pillar_a, relation.pillar_b)
        and RELATION_TABLES[relation.kind].side == "zhi"
    }
    return ChartSignals(
        gender=gender, level=strength.level, day_master_element=day.gan_element,
        element_scores=element_weight_scores(pillars), gods=gods,
        groups={
            name: sum(gods[god] for god in members) for name, members in TEN_GOD_GROUPS.items()
        },
        favourable=frozenset(yongshen.favorable_elements),
        unfavourable=frozenset(yongshen.unfavorable_elements),
        geju_success=geju.is_success,
        shensha=frozenset(entry.name for entry in shensha),
        relation_kinds=frozenset(relation.kind for relation in relations),
        day_branch_relations=frozenset(day_relations),
        day_group_count=sum(
            1 for group in branch_groups
            if any(member.pillar == "day" for member in group.members)
        ),
        dedi=strength.dedi,
    )


def _career(s: ChartSignals) -> list[tuple[str, bool]]:
    officer, output, killing = s.group("officer"), s.group("output"), s.gods["七杀"]
    return [
        ("career.officer.present", officer >= STAR_PRESENT),
        ("career.officer.favourable", officer >= STAR_PRESENT and s.is_favourable("officer")),
        ("career.officer.unfavourable", officer >= STAR_PRESENT and s.is_unfavourable("officer")),
        ("career.officer.restrained", killing > 0 and output >= killing),
        ("career.structure.success", s.geju_success),
        ("career.star.jiangxing", s.star("将星")),
        ("career.star.wenchang", s.star("文昌贵人")),
        ("career.body.weak-under-officer", s.level == "weak" and officer >= STAR_PRESENT),
    ]


def _wealth(s: ChartSignals) -> list[tuple[str, bool]]:
    wealth, officer, parallel = s.group("wealth"), s.group("officer"), s.group("parallel")
    return [
        ("wealth.star.present", wealth >= STAR_PRESENT),
        ("wealth.star.favourable", wealth >= STAR_PRESENT and s.is_favourable("wealth")),
        ("wealth.body.carries", s.level == "strong" and wealth >= STAR_PRESENT),
        ("wealth.body.overloaded", s.level == "weak" and wealth >= STAR_ABUNDANT),
        ("wealth.source.output", s.group("output") >= STAR_PRESENT),
        ("wealth.robbing.parallel", parallel >= STAR_PRESENT and parallel > wealth),
        ("wealth.guarded.officer", wealth >= STAR_PRESENT and officer >= STAR_PRESENT),
    ]


def _marriage(s: ChartSignals) -> list[tuple[str, bool]]:
    spouse = s.spouse_group()
    return [
        ("marriage.star.present", s.group(spouse) >= STAR_PRESENT),
        ("marriage.star.favourable", s.group(spouse) >= STAR_PRESENT and s.is_favourable(spouse)),
        ("marriage.palace.intact", not s.day_branch_relations & PALACE_BREAKING),
        ("marriage.palace.clashed", "地支六冲" in s.day_branch_relations),
        ("marriage.palace.bound", "地支六合" in s.day_branch_relations or s.day_group_count > 0),
        ("marriage.peachy.pool", s.star("咸池")),
        ("marriage.output-hurts-officer", s.gender == Gender.FEMALE
            and s.group("officer") >= OFFICER_TRACE and s.group("output") > s.group("officer")),
    ]


def _health(s: ChartSignals) -> list[tuple[str, bool]]:
    total = sum(s.element_scores.values())
    lowest = min(s.element_scores[element] for element in ELEMENT_ORDER)
    highest = max(s.element_scores[element] for element in ELEMENT_ORDER)
    return [
        ("health.balance.peaceful", s.level == "balanced"),
        ("health.root.sturdy", s.group("seal") + s.group("parallel") >= ROOT_STURDY),
        ("health.element.excessive", total > 0 and highest / total >= ELEMENT_EXCESS),
        ("health.element.lacking", lowest == 0.0),
        ("health.void.branch", s.star("空亡")),
        ("health.flow.unobstructed", lowest >= ELEMENT_FLOW),
    ]


def _study(s: ChartSignals) -> list[tuple[str, bool]]:
    seal = s.group("seal")
    return [
        ("study.seal.present", seal >= STAR_PRESENT),
        ("study.seal.favourable", seal >= STAR_PRESENT and s.is_favourable("seal")),
        ("study.output.present", s.group("output") >= STAR_PRESENT),
        ("study.wenchang", s.star("文昌贵人")),
        ("study.dedi.firm", s.dedi >= DEDI_FIRM),
    ]


def _social(s: ChartSignals) -> list[tuple[str, bool]]:
    parallel, officer = s.group("parallel"), s.group("officer")
    return [
        ("social.noble.tianyi", s.star("天乙贵人")),
        ("social.noble.taiji", s.star("太极贵人")),
        ("social.parallel.wide", parallel >= STAR_PRESENT),
        ("social.parallel.unchecked", parallel >= STAR_ABUNDANT and officer < STAR_PRESENT),
        ("social.officer.moderate", STAR_PRESENT <= officer <= OFFICER_CEILING),
        ("social.harm.branch", "地支六害" in s.relation_kinds),
    ]


DIMENSION_PREDICATES: dict[str, Callable[[ChartSignals], list[tuple[str, bool]]]] = {
    "事业": _career, "财运": _wealth, "婚姻": _marriage,
    "健康": _health, "学业": _study, "人际": _social,
}


def _tier(value: float) -> str:
    """顺/平/滞，沿用 §6.4 的 65/45 分界：同一套模型参数，不另立第二套阈值。"""
    if value >= 65.0:
        return "顺"
    return "平" if value >= 45.0 else "滞"


def build_plain(dimension: str, keys: Sequence[str], tier: str) -> str:
    """命中键 → 白话长文，装配住在 `engines/plain_compose.py`（多系统白话 spec §3）。

    本函数只干一件事：把「分带符号」算好交给 `compose`。第一期这里有一份和装配器
    重复的正负分带逻辑，抽层之后它必须删掉——两处排同一件事的次序，就是两处会漂。
    """
    prefix = DIMENSION_RULES[dimension][0].key.split(".", maxsplit=1)[0]
    return compose(BAZI, prefix, [(key, dim_rule(key).delta) for key in keys], tier)


def _base_rule(dimension: str) -> str:
    """账本基准行的键取该维规则键的前缀（career/wealth/…），不另立一套名字。"""
    return DIMENSION_RULES[dimension][0].key.split(".", maxsplit=1)[0] + ".base"


def _dimension_reading(s: ChartSignals, dimension: str) -> DimensionReading:
    """命中集 → 账本 → 文案，全部由 content 的 reading/label 组成，本函数不产中文句。"""
    fired = [
        ScoreFactor(rule=key, label=dim_rule(key).label, delta=dim_rule(key).delta,
                    source=MODEL_PARAM_SOURCE)
        for key, hit in DIMENSION_PREDICATES[dimension](s) if hit
    ]
    total = min(100.0, max(0.0, DIMENSION_BASE + sum(factor.delta for factor in fired)))
    keys = [factor.rule for factor in fired]
    tier = _tier(total)
    return DimensionReading(
        dimension=dimension,
        score=build_ledger(base=DIMENSION_BASE, tier=tier, contributions=fired,
                           base_rule=_base_rule(dimension)),
        strengths=[dim_rule(key).label for key in keys if dim_rule(key).delta > 0],
        cautions=[dim_rule(key).label for key in keys if dim_rule(key).delta < 0],
        narrative="；".join(dim_rule(key).reading for key in keys) + "。",
        plain=build_plain(dimension, keys, tier),
        source=MODEL_PARAM_SOURCE,
    )


def interpret_chart(
    pillars: list[BaziPillar], *, gender: Gender | None, strength: StrengthAssessment, geju: GeJu,
    yongshen: Yongshen, shensha: Sequence[ShenShaEntry], relations: Sequence[RelationPair],
    branch_groups: Sequence[BranchGroup],
) -> BaziInterpretation:
    """装配六维详批；只读前序结论，不重新判命（spec §6.6）。

    婚姻维的配偶星按性别取（女命官杀、男命财），性别未知时整维不输出，而不是
    默认按男命判 —— 前端对缺失的区整块隐藏（spec §8.4）。
    """
    signals = collect_signals(
        pillars, gender=gender, strength=strength, geju=geju, yongshen=yongshen,
        shensha=shensha, relations=relations, branch_groups=branch_groups,
    )
    dimensions = [name for name in DIMENSION_ORDER if name != "婚姻" or gender is not None]
    readings = [_dimension_reading(signals, name) for name in dimensions]
    summary = "、".join(f"{r.dimension}{r.score.tier}" for r in readings)
    # 结论卡片（verdict-card spec §3/§4）：档位从六维账本均值派生（不许拍脑袋），
    # 四段文案全部来自 `bazi_plain` 的框架句 + 槽位语料，本函数不现编中文。
    grade, stars = grade_for(mean(r.score.value for r in readings))
    counts = {tier: sum(1 for r in readings if r.score.tier == tier) for tier in ("顺", "平", "滞")}
    headline = overview(PLAIN_SUMMARY_FRAME, {
        "grade": grade,
        "shun": str(counts["顺"]),
        "ping": str(counts["平"]),
        "zhi": str(counts["滞"]),
        "outlook": VERDICT_OUTLOOK[grade],
    })
    weakest = min(readings, key=lambda r: r.score.value)
    advice = overview(VERDICT_ADVICE_FRAME, {
        "dimension": weakest.dimension,
        "tier_advice": TIER_ADVICE[weakest.score.tier],
    })
    return BaziInterpretation(
        six_dimensions=readings,
        summary=summary,
        plain_summary=headline,
        verdict=Verdict(
            grade=grade,
            stars=stars,
            headline=headline,
            points=[f"{r.dimension}：{r.score.tier}" for r in readings],
            advice=advice,
        ),
    )
