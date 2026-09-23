"""八字合婚引擎（spec §2、§6）：两造同屏，关系第一次要跨两张盘算。

历法、排盘、关系表、合局表、纳音表、账本、流年扫描全是现成件，本模块只做四件事：
① 把两造各排一次盘，并把错误归到是哪一造（§9.2）；② 以乾四柱为体、坤四柱为 `extra`
扫一次跨造关系，按"恰好一侧是 extra"过滤（§2.1）；③ 按 §6.2 的归属规则把每个事实
收进五族里的一族一条；④ 交 `build_ledger` 出一份自解释的总分。

**跨造不算十神**（决策 2）：十神是命局内部的坐标（切片 0 §7.5 已把 `_god()` 对外来柱
定为空串），把它伸到另一张盘上是本系统没有资格立的第五种命理学说。同理两造的喜忌一律
直接取各自本命盘（决策 3），本模块不重判。

`strength`（紧临/隔位/远位）在这里不存在：那是同一张盘里两根柱相隔几位，跨造时退化成
"打到了对方第几根柱"，与实际关系无关（§2.2）。契约带的是真语义的柱位对。
"""

from dataclasses import dataclass
from datetime import date

from app.content.bazi_hehun_rules import HEHUN_RELATION_KEYS, hehun_rule
from app.core.errors import DestinyError
from app.engines.bazi import compute_bazi_chart
from app.engines.bazi_rules import POSITIONS, derive_relations
from app.schemas.bazi import BaziChart
from app.schemas.bazi_hehun import HehunCell, HehunCellHit, HehunProfile
from app.schemas.common import Gender
from app.solar.geo import resolve_longitude
from app.solar.true_solar_time import STANDARD_MERIDIAN_CN

#: 矩阵的枚举序，与 `derive_relations` 的柱序同词（§2.4 的 `extra{n}` 映射靠它）。
POSITION_ORDER: tuple[str, ...] = POSITIONS

#: 关系 kind → 该 kind 在合婚账本里的键，倒转一次规则表的键表即可。
RELATION_RULE_OF: dict[str, str] = dict(HEHUN_RELATION_KEYS)


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

    code、message、status_code 一字不动：`TransitErrorNote` 于是自动说出是谁的生辰有问题
    （§9.2），而既有的错误链不必为合婚开第二份。`partner` 是唯一新增的一项 context，
    取 `Gender` 的值即是乾/坤的键名，不必再造一张映射表。
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


def _to_row(rule_key: str, direction: str) -> HehunRow:
    rule = hehun_rule(rule_key)
    return HehunRow(
        rule=rule.key,
        label=rule.label,
        family=rule.family,
        direction=direction,
        delta=rule.delta,
    )


def relation_rows(pair: HehunChartPair) -> list[HehunRow]:
    """对称族：每条跨造关系一行，`mutual`（Task 3 才加婚姻宫封口，§6.2）。"""
    return [_to_row(hit.rule, "mutual") for hit in cross_relations(pair)]


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
