"""用神三法：扶抑定基准，通关与调候只增不减，冲突如实并列（spec §6.5）。

三法的输入只是"档位 + 日主五行 + 月支 + 加权分"四个标量，不读格局（`GeJu` 在响应顶层
出现一次即可）；标量入参因此能让每一条分支都直接注入测，不必为测试伪造整本账。

分层与 `bazi_strength` 一致：命理断语在 `content/`，这里只产取舍键、五行与口径说明；
``reason`` 记的是本系统的合并规则，不是古籍判语。
"""

from app.content.bazi_tiaohou import (
    SEASON_BY_MONTH_ZHI,
    TIAOHOU_PRESCRIPTION,
    TIAOHOU_SOURCE,
)
from app.content.wuxing import CONTROLS, ELEMENT_ORDER, GENERATES
from app.core.provenance import MODEL_PARAM_SOURCE
from app.engines.bazi_strength import fuyin_choices
from app.schemas.bazi_strength import Yongshen, YongshenConflict, YongshenMethod

# 力量前二行的比值：≥0.8 才算"对峙"，才轮到通关说话（模型参数，spec §6.5）。
TONGGUAN_MIN_RATIO = 0.8
# 对治五行已占全命加权分的该比例时，视为命局自带，调候不再重复补（模型参数）。
TIAOHOU_ALREADY_PRESENT = 0.15

FUYI_SOURCE = "《渊海子平》强弱扶抑之简化（档位取值见 bazi_strength 模型参数）"
FUYI_RULE = {
    "weak": "weak.take-resource-and-parallel",
    "strong": "strong.take-control-drain-output",
    "balanced": "balanced.no-preference",
}


def _clash_pair(first: str, second: str) -> tuple[str, str] | None:
    """Return ``(attacker, defender)`` when the two elements clash, else ``None``."""
    if CONTROLS[first] == second:
        return first, second
    if CONTROLS[second] == first:
        return second, first
    return None


def _mediating_element(attacker: str, defender: str) -> str:
    """通关神 X：attacker 生 X，X 生 defender。"""
    return next(x for x in ELEMENT_ORDER if GENERATES[attacker] == x and GENERATES[x] == defender)


def _ranked(elements: list[str], scores: dict[str, float]) -> list[str]:
    """加权分降序、同分按五行序；去重，确保同一行不会在喜用集里出现两次。"""
    unique = list(dict.fromkeys(elements))
    return sorted(unique, key=lambda e: (-scores[e], ELEMENT_ORDER.index(e)))


def _strongest_pair(scores: dict[str, float]) -> list[str]:
    """力量前两行；同分按五行序，不跟字典序（否则前二名并列时结果随入参顺序漂）。"""
    return sorted(scores, key=lambda e: (-scores[e], ELEMENT_ORDER.index(e)))[:2]


def select_yongshen(
    *,
    level: str,
    day_master_element: str,
    month_zhi: str,
    element_scores: dict[str, float],
) -> Yongshen:
    """Evaluate all three methods, merge them, and report every decision."""
    total = sum(element_scores.values())
    favourable, unfavourable = fuyin_choices(level, day_master_element, element_scores)
    conflict: YongshenConflict | None = None

    def adopt(element: str | None, *, method: str, source: str) -> bool:
        """Merge one pick into the favourable set; True when it was newly added."""
        nonlocal conflict, favourable
        if element is None or element in favourable:
            return False
        favourable = _ranked([*favourable, element], element_scores)
        if element in unfavourable and conflict is None:
            conflict = YongshenConflict(
                element=element,
                suppressed_by="扶抑",
                reason=f"{method}取{element}为用，扶抑以{element}为忌，两法口径相左；"
                "本系统按「后法只增不减」并列呈现，不做静默取舍。",
                source=source,
            )
        return True

    # 扶抑：基准集合，先记下来再让后两法增补（list() 复制，防后续 rebind 影响）。
    methods = [
        YongshenMethod(
            method="扶抑",
            fired_rule=FUYI_RULE[level],
            chosen_elements=list(favourable),
            already_present=False,
            source=FUYI_SOURCE,
        )
    ]

    # 通关：只对"力量前二且相持"的克战说话。
    top_two = _strongest_pair(element_scores)
    clash = _clash_pair(*top_two)
    mediator: str | None = None
    if clash is None:
        tongguan_rule = "top-two.no-clash"
    else:
        weaker, stronger = sorted(element_scores[element] for element in top_two)
        if weaker / stronger < TONGGUAN_MIN_RATIO:
            tongguan_rule = "clash-too-uneven"
        else:
            mediator = _mediating_element(*clash)
            tongguan_rule = f"mediates.{clash[0]}生{mediator}"
    added = adopt(mediator, method="通关", source=MODEL_PARAM_SOURCE)
    methods.append(
        YongshenMethod(
            method="通关",
            fired_rule=tongguan_rule,
            chosen_elements=[] if mediator is None else [mediator],
            already_present=mediator is not None and not added,
            source=MODEL_PARAM_SOURCE,
        )
    )

    # 调候：季节纲要；已够旺的对治行不重复补，但要把"为何没补"记下来。
    season = SEASON_BY_MONTH_ZHI[month_zhi]
    prescribed = TIAOHOU_PRESCRIPTION[season]
    cure_present = prescribed is not None and (
        element_scores[prescribed] / total >= TIAOHOU_ALREADY_PRESENT
    )
    added = adopt(None if cure_present else prescribed, method="调候", source=TIAOHOU_SOURCE)
    methods.append(
        YongshenMethod(
            method="调候",
            fired_rule="season-balanced" if prescribed is None else f"{season}.take-{prescribed}",
            chosen_elements=[] if prescribed is None else [prescribed],
            already_present=prescribed is not None and (cure_present or not added),
            source=TIAOHOU_SOURCE,
        )
    )

    return Yongshen(
        favorable_elements=favourable,
        unfavorable_elements=unfavourable,  # 后两法只增喜，绝不移忌
        methods=methods,
        conflict=conflict,
    )
