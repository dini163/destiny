"""岁运（流年 / 流月）引擎：区间解析、命中判定、账本装配，与最后的总装。

本模块**不重复**任何命局推导：喜忌取自 `select_yongshen` 的合并结果，关系、合局、
神煞由 `bazi_rules` 的三个 derive 函数带上岁运之柱重扫一遍，柱的十神 / 地势 / 纳音
由 `bazi_pillar.build_transit_pillar` 合成。计分是岁运自己的一张表
（`content/bazi_transit_rules`，46 条），命局的 39 条判语、旺衰三因子与用神都不参
与，也不被改写（spec §4 决策 3）。

排盘时刻走 `bazi_moment.resolve_natal_moment`：岁运要再走一次 `getYun()` 才拿得到流年
与流月对象，而那一刻必须和主命盘用同一个真太阳时校正 —— 校正逻辑有两份，迟早分出两个
口径。它不住在本模块里，因为本模块还要消费主命盘（`compute_bazi_chart`），谁住着都得一
个模块反向 import 另一个。

节气月界（`jieqi_boundaries`）则确实住在这里：`LiuYue` 只给干支、序号与月名，一个日期都
不给，十二段起止得自己从 `getJieQiTable()` 的滚动窗口里采十二节推出来。切片 3 的流日
要的是同一份采集，写在装配里它就只能重写一遍。
"""

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import date, time, timedelta

from lunar_python import Solar

from app.content import CONTENT_SOURCES, CONTENT_VERSION, TRANSIT_CONTENT_SOURCES
from app.content.bazi_relations import relation_pairs
from app.content.bazi_shishen import ten_god_meaning
from app.content.bazi_transit_rules import (
    TRANSIT_BASE,
    TRANSIT_RULE_SOURCE,
    TransitRule,
    transit_rule,
)
from app.content.wuxing import GAN_ELEMENT, GENERATES
from app.core.errors import TransitRangeError
from app.engines.bazi import compute_bazi_chart
from app.engines.bazi_moment import resolve_natal_moment
from app.engines.bazi_pillar import build_transit_pillar
from app.engines.bazi_rules import (
    derive_branch_groups,
    derive_relations,
    derive_shensha,
    is_fanyin,
)
from app.engines.bazi_strength import STRONG_CUT, WEAK_CUT
from app.schemas.bazi import BaziChart, BaziPillar, DayunStep
from app.schemas.bazi_breakdown import Provenance, ProvenanceTable
from app.schemas.bazi_rules import BranchGroup, RelationPair, ShenShaEntry
from app.schemas.bazi_transit import (
    BaziTransitResult,
    TransitFired,
    TransitMonth,
    TransitTenGod,
    TransitYear,
)
from app.schemas.common import CalendarType, Gender
from app.schemas.scoring import ScoreFactor, ScoreValue, build_ledger
from app.solar.true_solar_time import STANDARD_MERIDIAN_CN

#: 缺省区间长度与上限（spec §7.2）：一年一秒都不多给，越线即 422，不做静默裁剪。
TRANSIT_DEFAULT_YEARS = 5
TRANSIT_MAX_YEARS = 10


@dataclass(frozen=True)
class TransitRange:
    """请求区间被补齐之后的样子：`focus_year` 为空表示只出年表、不展开流月。"""

    start_year: int
    end_year: int
    focus_year: int | None


def resolve_transit_range(
    *,
    start_year: int | None,
    end_year: int | None,
    focus_year: int | None,
    reference_year: int,
    supported_from: int,
    supported_to: int,
) -> TransitRange:
    """补齐缺省、再做四道校验，产出实际要推演的年份区间。

    校验次序即依赖次序：先确认区间自身成形（倒序），再确认它不太宽，再确认它落在
    这个命盘推得出的年份里，最后才看 focus 年 —— 顺序换了，同一份入参报出来的码就
    换了，而调用方要的是一个能据以改表单的码。
    """
    span_start = start_year
    span_end = end_year
    if span_start is None and span_end is None:
        span_start = reference_year
    if span_end is None:
        span_end = span_start + TRANSIT_DEFAULT_YEARS - 1
    if span_start is None:
        span_start = span_end - TRANSIT_DEFAULT_YEARS + 1

    if span_end < span_start:
        raise TransitRangeError(
            "transit_range_reversed",
            f"起始年 {span_start} 晚于结束年 {span_end}，区间无从推起。",
            {"start_year": span_start, "end_year": span_end},
        )
    requested = span_end - span_start + 1
    if requested > TRANSIT_MAX_YEARS:
        raise TransitRangeError(
            "transit_range_too_wide",
            f"区间跨度 {requested} 年，超出 {TRANSIT_MAX_YEARS} 年上限。",
            {"max_years": TRANSIT_MAX_YEARS, "requested": requested},
        )
    if span_start < supported_from or span_end > supported_to:
        raise TransitRangeError(
            "transit_range_unsupported",
            f"本命盘的大运覆盖 {supported_from}—{supported_to} 年，"
            f"请求的 {span_start}—{span_end} 年在其之外。",
            {
                "supported_from": supported_from,
                "supported_to": supported_to,
                "requested_from": span_start,
                "requested_to": span_end,
            },
        )
    if focus_year is not None and not span_start <= focus_year <= span_end:
        raise TransitRangeError(
            "transit_focus_out_of_range",
            f"聚焦年 {focus_year} 不在 {span_start}—{span_end} 年区间内。",
            {"focus_year": focus_year, "start_year": span_start, "end_year": span_end},
        )
    return TransitRange(start_year=span_start, end_year=span_end, focus_year=focus_year)


# ------------------------------------------------------------------ 命中判定（spec §6.2）
#: 岁运之柱在 `bazi_rules._slots` 里的槽位名：extras 从 `extra0` 起追加在四柱之后。
#: 判定层认的就是这个名字 —— 命局内部两柱之间的关系不属于岁运的账（决策 3）。
_TRANSIT_SLOT = "extra0"
#: 刑有四张表，岁运只问"这一柱受不受刑"，不给四张表分凶序。
_PUNISH_KINDS: tuple[str, ...] = ("无恩之刑", "恃势之刑", "无礼之刑", "自刑")
#: 运岁干合的查表入口（表里两向俱存，故只查一个方向）。
_GAN_HE = relation_pairs("天干五合")
#: 十二长生分三档定价，沐浴不在任何一档：它既是败地又是桃花，一书两说（spec §6.2）。
#: 三档合起来覆盖余下 11 位，由测 `test_life_stage_bands_partition_the_eleven_priced_stages`
#: 与 `content.bazi_changsheng.CHANG_SHENG_ORDER` 对拍钉住。
_PROSPEROUS: tuple[str, ...] = ("临官", "帝旺")
_SUPPORTIVE: tuple[str, ...] = ("长生", "冠带", "胎", "养")
_DECAYING: tuple[str, ...] = ("衰", "病", "死", "墓", "绝")


@dataclass(frozen=True)
class TransitJudgement:
    """一条岁运干支在打分前需要知道的全部事实，由装配段（Task 8/9/10）填好。

    谓词只看它，不回查历法，也不回头调 `derive_relations`。这样"命中什么"与"什么时候
    算出来的"两件事分开：同一个上下文在单测里手搭即可，装配段换法不影响判定。
    """

    scope: str  # sui | yue
    ganzhi: str
    gan: str
    zhi: str
    gan_element: str
    ben_qi_element: str  # 支主气（本气藏干）的五行
    di_shi: str
    dayun_ganzhi: str | None  # 童年段（未起运）为空：整个 dayun 族不评估，见 `_on_dayun`
    year_zhi: str  # 本命年支 —— 太岁以此为准，不是当岁之支
    relations: tuple[RelationPair, ...]
    groups: tuple[BranchGroup, ...]
    shensha_names: frozenset[str]
    favourable: frozenset[str]
    unfavourable: frozenset[str]

    def kinds_with(self, position: str) -> frozenset[str]:
        """该柱与岁运之柱之间成了哪几种象（两端无序，柱位对上了才算）。"""
        return frozenset(
            relation.kind
            for relation in self.relations
            if {relation.pillar_a, relation.pillar_b} == {position, _TRANSIT_SLOT}
        )

    def has(self, kind: str) -> bool:
        """岁运之柱与命局任一柱成此象 —— 伏吟、反吟论整柱，不限定落在哪一柱。"""
        return any(
            relation.kind == kind and _TRANSIT_SLOT in (relation.pillar_a, relation.pillar_b)
            for relation in self.relations
        )

    def punishes(self, position: str) -> bool:
        return bool(self.kinds_with(position) & frozenset(_PUNISH_KINDS))

    def group_elements(self, kind: str) -> frozenset[str]:
        """岁运参与合出的局的五行；不含岁运成员的局是命局自己的账。"""
        return frozenset(
            group.element
            for group in self.groups
            if group.kind == kind
            and any(member.pillar == _TRANSIT_SLOT for member in group.members)
        )

    def has_star(self, name: str) -> bool:
        return name in self.shensha_names


def _group_faces(j: TransitJudgement, kind: str, *, favourable: bool) -> bool:
    """局本身不论吉凶：合出的五行落进喜用集才算顺、落进忌神集才算逆（spec §6.2）。"""
    elements = j.group_elements(kind)
    return bool(elements & (j.favourable if favourable else j.unfavourable))


Predicate = Callable[[TransitJudgement], bool]
#: 大运谓词多收一个参数：过闸之后的大运干支。谓词因此不必各自判空。
DayunPredicate = Callable[[TransitJudgement, str], bool]


def _gan_element(ganzhi: str) -> str:
    """干之五行。运岁生克只以干论：一支藏多气，论支就有一支两种向背。"""
    return GAN_ELEMENT[ganzhi[0]]


def _on_dayun(predicate: DayunPredicate) -> Predicate:
    """大运族的总闸：童年段 `DaYun.getGanZhi()` 为空串，无运可论则整族不评估。

    闸写在谓词上而不是写在装配段，因为"空串"与"这条岁运没有对应大运"是同一件事的两
    种说法，装配段以后换法时判定层不该跟着改。
    """

    def gated(judgement: TransitJudgement) -> bool:
        ganzhi = judgement.dayun_ganzhi
        if not ganzhi:
            return False
        return predicate(judgement, ganzhi)

    return gated


def _on_star(name: str) -> Predicate:
    """神煞族的谓词工厂：命中条件只有一句"这颗星落在岁运之柱上"。

    星名与 `TRANSIT_RULES[key].label` 同源（即 `SHENSHA_RULES` 的神煞名）；两处一旦
    分家，`test_each_shensha_row_reads_exactly_its_own_rule_table_label` 判红。
    """
    return lambda judgement: judgement.has_star(name)


#: 键序 == `TRANSIT_RULES` 的表序 == 账本行序；一键一谓词，由
#: `test_every_rule_row_is_consumed_by_exactly_one_predicate` 钉住。谓词本身不含古籍
#: 字 —— 文案在 `reading` 里，分数在 `delta` 里。
_PREDICATES: tuple[tuple[str, Predicate], ...] = (
    # --- yongshen（4）：喜忌集来自 `select_yongshen`，此处只问落不落在里头
    ("yongshen.gan_favourable", lambda j: j.gan_element in j.favourable),
    ("yongshen.gan_unfavourable", lambda j: j.gan_element in j.unfavourable),
    ("yongshen.zhi_favourable", lambda j: j.ben_qi_element in j.favourable),
    ("yongshen.zhi_unfavourable", lambda j: j.ben_qi_element in j.unfavourable),
    # --- taisui（6）：只论年支，岁专属
    ("taisui.chong", lambda j: "地支六冲" in j.kinds_with("year")),
    ("taisui.value", lambda j: j.zhi == j.year_zhi),
    ("taisui.harm", lambda j: "地支六害" in j.kinds_with("year")),
    ("taisui.punish", lambda j: j.punishes("year")),
    ("taisui.break", lambda j: "地支六破" in j.kinds_with("year")),
    ("taisui.combine", lambda j: "地支六合" in j.kinds_with("year")),
    # --- palace（8）：提纲与日支为至近之地，两宫各四行
    ("palace.chong_month", lambda j: "地支六冲" in j.kinds_with("month")),
    ("palace.chong_day", lambda j: "地支六冲" in j.kinds_with("day")),
    ("palace.punish_month", lambda j: j.punishes("month")),
    ("palace.punish_day", lambda j: j.punishes("day")),
    ("palace.combine_month", lambda j: "地支六合" in j.kinds_with("month")),
    ("palace.combine_day", lambda j: "地支六合" in j.kinds_with("day")),
    ("palace.harm_month", lambda j: "地支六害" in j.kinds_with("month")),
    ("palace.harm_day", lambda j: "地支六害" in j.kinds_with("day")),
    # --- heyue（6）：三合 / 半合 / 三会 × 向背
    ("heyue.sanhe_favourable", lambda j: _group_faces(j, "三合", favourable=True)),
    ("heyue.sanhe_unfavourable", lambda j: _group_faces(j, "三合", favourable=False)),
    ("heyue.anhe_favourable", lambda j: _group_faces(j, "半合", favourable=True)),
    ("heyue.anhe_unfavourable", lambda j: _group_faces(j, "半合", favourable=False)),
    ("heyue.sanhui_favourable", lambda j: _group_faces(j, "三会", favourable=True)),
    ("heyue.sanhui_unfavourable", lambda j: _group_faces(j, "三会", favourable=False)),
    # --- ganzhi（2）：天干只论日主一柱
    ("ganzhi.combine_day_master", lambda j: "天干五合" in j.kinds_with("day")),
    ("ganzhi.chong_day_master", lambda j: "天干相冲" in j.kinds_with("day")),
    # --- fuyin（2）：整柱比对由 `derive_relations` 判，这里只认它报了什么
    ("fuyin.fuyin", lambda j: j.has("伏吟")),
    ("fuyin.fanyin", lambda j: j.has("反吟")),
    # --- dayun（5）：大运只与流年论，读的是两柱干支本身，不是关系扫描的产物 ---
    ("dayun.binglin", _on_dayun(lambda j, dayun: j.ganzhi == dayun)),
    ("dayun.fanyin", _on_dayun(lambda j, dayun: is_fanyin(dayun, j.ganzhi))),
    (
        "dayun.yun_sheng_sui",
        _on_dayun(lambda j, dayun: GENERATES[_gan_element(dayun)] == j.gan_element),
    ),
    (
        "dayun.sui_sheng_yun",
        _on_dayun(lambda j, dayun: GENERATES[j.gan_element] == _gan_element(dayun)),
    ),
    ("dayun.gan_he", _on_dayun(lambda j, dayun: (j.gan, dayun[0]) in _GAN_HE)),
    # --- dishi（3）：岁运之支对日主的十二长生位次，沐浴室外 ---
    ("dishi.prosperous", lambda j: j.di_shi in _PROSPEROUS),
    ("dishi.supportive", lambda j: j.di_shi in _SUPPORTIVE),
    ("dishi.decaying", lambda j: j.di_shi in _DECAYING),
    # --- shensha（10）：吉 7 凶 3，中性者不在表里，也就不在这张谓词表里 ---
    ("shensha.tianyi", _on_star("天乙贵人")),
    ("shensha.jiangxing", _on_star("将星")),
    ("shensha.wenchang", _on_star("文昌贵人")),
    ("shensha.tiande", _on_star("天德贵人")),
    ("shensha.yuede", _on_star("月德贵人")),
    ("shensha.jinyu", _on_star("金舆")),
    ("shensha.taiji", _on_star("太极贵人")),
    ("shensha.yangren", _on_star("羊刃")),
    ("shensha.jiesha", _on_star("劫煞")),
    ("shensha.wangshen", _on_star("亡神")),
)


def transit_hit_keys(judgement: TransitJudgement) -> list[str]:
    """这条岁运命中了哪些规则 —— 顺序即账本顺序，`scopes` 过滤也在这里。

    月段拿到的上下文带着整年的关系扫描结果，但 `taisui` 与 `dayun` 两族的 `scopes`
    不含 `yue`，于是它们不会在流月里重复计价；过滤放在这一处而不是放在装配段，是
    为了"什么算命中"只有一种问法。
    """
    return [
        key
        for key, predicate in _PREDICATES
        if judgement.scope in transit_rule(key).scopes and predicate(judgement)
    ]


# ---------------------------------------------------------------- 命局投影（spec §4 决策 3）
@dataclass(frozen=True)
class TransitNatal:
    """命局交给岁运读的那五件事：四柱、日主、本命年支、喜用集、忌神集。

    它是一次**投影**而不是第二次排盘：喜忌取 `select_yongshen` 三法合出来的结果，
    岁运只照用，不重判（spec §6.6）。`pillars` 复制成一份新列表，为的是岁运扫描
    哪怕改到列表本身也碰不到命盘对象。
    """

    pillars: list[BaziPillar]
    day_master: str
    year_zhi: str
    favourable: frozenset[str]
    unfavourable: frozenset[str]


def natal_projection(chart: BaziChart) -> TransitNatal:
    """从已算好的命盘里取出岁运要读的字段。"""
    return TransitNatal(
        pillars=list(chart.pillars),
        day_master=chart.day_master,
        year_zhi=chart.pillars[0].zhi,  # 年柱之支即本命，太岁以此为准
        favourable=frozenset(chart.analysis.favorable_elements),
        unfavourable=frozenset(chart.analysis.unfavorable_elements),
    )


# ---------------------------------------------------------------- 岁运扫描（spec §7.3）
@dataclass(frozen=True)
class TransitScan:
    """一根岁运柱扫完的结果：合成柱、打分上下文，与随响应发出的三张明细。

    三张明细都只留一端落在 `_TRANSIT_SLOT` 的条目。命局四柱内部本来就有的象是命局
    自己的账（决策 3），灌进岁运账本会重复计价，前端也会把同一条象显示两遍。
    """

    pillar: BaziPillar
    judgement: TransitJudgement
    relations: list[RelationPair]
    shensha: list[ShenShaEntry]
    branch_groups: list[BranchGroup]


def scan_transit_pillar(
    natal: TransitNatal,
    ganzhi: str,
    *,
    position: str,
    label: str,
    scope: str,
    dayun_ganzhi: str | None,
) -> TransitScan:
    """以命局四柱为体、岁运一柱为用，重扫关系 / 合局 / 神煞，并留下岁运落点。

    `scope` 决定这根柱按岁、月还是日计价（`transit_hit_keys` 用规则的 `scopes` 过滤）；
    `dayun_ganzhi` 只有流年给得出，流月与流日留 None —— 大运只与流年论（spec §6.2）。
    """
    pillar = build_transit_pillar(
        ganzhi, position=position, label=label, day_master=natal.day_master
    )
    relations = [
        relation
        for relation in derive_relations(natal.pillars, [ganzhi])
        if _TRANSIT_SLOT in (relation.pillar_a, relation.pillar_b)
    ]
    shensha = [
        entry
        for entry in derive_shensha(
            natal.pillars, day_master=natal.day_master, extra_ganzhi=[ganzhi]
        )
        if any(match.position == _TRANSIT_SLOT for match in entry.matches)
    ]
    branch_groups = [
        group
        for group in derive_branch_groups(natal.pillars, [ganzhi])
        if any(member.pillar == _TRANSIT_SLOT for member in group.members)
    ]
    judgement = TransitJudgement(
        scope=scope,
        ganzhi=ganzhi,
        gan=pillar.gan,
        zhi=pillar.zhi,
        gan_element=pillar.gan_element,
        ben_qi_element=pillar.hidden_stem_elements[0],  # 支以本气（藏干首位）为主
        di_shi=pillar.di_shi,
        dayun_ganzhi=dayun_ganzhi,
        year_zhi=natal.year_zhi,
        relations=tuple(relations),
        groups=tuple(branch_groups),
        shensha_names=frozenset(entry.name for entry in shensha),
        favourable=natal.favourable,
        unfavourable=natal.unfavourable,
    )
    return TransitScan(
        pillar=pillar,
        judgement=judgement,
        relations=relations,
        shensha=shensha,
        branch_groups=branch_groups,
    )


# ---------------------------------------------------------------- 账本装配（spec §6.3）
def _tier(value: float) -> str:
    """顺 / 平 / 滞。两道分界与旺衰档位同引 `bazi_strength` 的常量，不另立一套阈值。"""
    if value >= STRONG_CUT:
        return "顺"
    return "平" if value >= WEAK_CUT else "滞"


#: 账本三段的 (rule 前缀, 短名后缀)，序为年、月、日。年段是基准那一段，不加任何标记；
#: 月、日两段各加一层 —— 一条规则在一份账本里最多出现三次，前缀是唯一的分辨手段（spec §6.3）。
_LEDGER_SEGMENTS: tuple[tuple[str, str], ...] = (("", ""), ("yue.", "（流月）"), ("ri.", "（流日）"))


def hit_rows(
    year_keys: Sequence[str],
    month_keys: Sequence[str],
    day_keys: Sequence[str] = (),
) -> list[tuple[ScoreFactor, TransitRule]]:
    """命中集 → (账本行, 规则) 成对，序为年段、月段、日段。

    账本与 `fired` 读同一份产出，所以"逐行可见的判语"与"这一行的分值"不可能分家；
    月段在键前加 `yue.`、日段加 `ri.`，短名各带"（流月）"或"（流日）"后缀，因为一条
    规则可以在同一份账本里出现三次，不带前缀就读不出那一行是谁加的分。
    `day_keys` 缺省为空：流年与流月那两页本来就没有日段，它们不该各补一个 `[]`。
    """
    rows: list[tuple[ScoreFactor, TransitRule]] = []
    for keys, (prefix, suffix) in zip(
        (year_keys, month_keys, day_keys), _LEDGER_SEGMENTS, strict=True
    ):
        for key in keys:
            rule = transit_rule(key)
            rows.append(
                (
                    ScoreFactor(
                        rule=f"{prefix}{key}",
                        label=rule.label + suffix,
                        delta=rule.delta,
                        source=TRANSIT_RULE_SOURCE,
                    ),
                    rule,
                )
            )
    return rows


def transit_ledger(rows: Sequence[tuple[ScoreFactor, TransitRule]]) -> ScoreValue:
    """命中行 → 自解释账本；截断由 `build_ledger` 记成它自己的一行。"""
    raw_total = TRANSIT_BASE + sum(factor.delta for factor, _ in rows)
    return build_ledger(
        base=TRANSIT_BASE,
        tier=_tier(min(100.0, max(0.0, raw_total))),
        contributions=[factor for factor, _ in rows],
        base_rule="transit.base",
    )


def transit_fired(rows: Sequence[tuple[ScoreFactor, TransitRule]]) -> list[TransitFired]:
    """账本行的人类可读镜像：键与短名逐字取自那一行，判语取自规则表。"""
    return [
        TransitFired(
            key=factor.rule,
            label=factor.label,
            family=rule.family,
            delta=factor.delta,
            reading=rule.reading,
        )
        for factor, rule in rows
    ]


def transit_narrative(rows: Sequence[tuple[ScoreFactor, TransitRule]]) -> str:
    """命中判语连缀，与六维详批同法。一条未中时返回空串，而不是一个孤零零的句号。"""
    if not rows:
        return ""
    return "；".join(rule.reading for _, rule in rows) + "。"


# ---------------------------------------------------------------- 流年对象（spec §7.3）
@dataclass(frozen=True)
class AnnualLuck:
    """lunar-python 给的一个流年：干支、虚岁，加上它所从出的那一步大运。

    `liunian` 是历法里的原对象，留着不为别的：流月只能由 `LiuNian.getLiuYue()` 给，
    而这一层已经把那个对象摊平出来了 —— 要月份时再按年份回头找一次，是两个入口。
    """

    year: int
    age: int
    ganzhi: str
    dayun_index: int
    dayun_ganzhi: str | None
    liunian: object  # lunar_python.LiunianYear；流月要从它身上取


def annual_luck_by_year(
    eight_char: object, gender: Gender | None
) -> dict[int, AnnualLuck]:
    """`getYun().getDaYun()[i].getLiuNian()` 摊平成 `公历年 -> 流年`。

    流年必须从大运段里取，不能按公历年自己算干支：起运前的童年段也排在 `getDaYun()`
    第 0 项里，摊平这一步顺带记下"这一年属于第几步运"，而大运族正要论这件事。
    `getGanZhi()` 在童年段是空串，这里翻成 None —— "无运可论"与"运干为空字符串"两件
    事里，前者才是事实。性别未知则方向都定不下来，返回空表而不是猜一个（spec §8.4）。
    """
    if gender is None:
        return {}
    luck: dict[int, AnnualLuck] = {}
    for step in eight_char.getYun(1 if gender is Gender.MALE else 0).getDaYun():
        for liu_nian in step.getLiuNian():
            luck[liu_nian.getYear()] = AnnualLuck(
                year=liu_nian.getYear(),
                age=liu_nian.getAge(),
                ganzhi=liu_nian.getGanZhi(),
                dayun_index=step.getIndex(),
                dayun_ganzhi=step.getGanZhi() or None,
                liunian=liu_nian,
            )
    return luck


def year_scan(natal: TransitNatal, luck: AnnualLuck) -> TransitScan:
    """流年那一柱的扫描 —— 装配与流月段共用的唯一定义。

    月账本要以它为前缀（spec §6.4），所以"年段命中了什么"只能有一处算法；两处各算
    一遍的话，年卡和月卡对同一年给出两套行，前端无从解释。
    """
    return scan_transit_pillar(
        natal,
        luck.ganzhi,
        position="transit_year",
        label="流年",
        scope="sui",
        dayun_ganzhi=luck.dayun_ganzhi,
    )


def _transit_year(natal: TransitNatal, luck: AnnualLuck, *, focus: bool = False) -> TransitYear:
    """装配一个流年：合成柱、单段账本、三张岁运明细、十神释义与断语。

    `focus` 即请求里的 `focus_year` 是否就是这一年：给 12 段节气月，其余年留 None，
    前端整块不渲染，而不是摆出十二个空月。
    """
    scan = year_scan(natal, luck)
    year_keys = transit_hit_keys(scan.judgement)
    rows = hit_rows(year_keys, [])
    corpus = ten_god_meaning(scan.pillar.shishen_gan)
    return TransitYear(
        year=luck.year,
        age=luck.age,
        pillar=scan.pillar,
        dayun_index=luck.dayun_index,
        dayun_ganzhi=luck.dayun_ganzhi,
        ten_god=TransitTenGod(
            god=corpus.ten_god,
            meaning=corpus.meaning,
            source=corpus.source,
        ),
        score=transit_ledger(rows),
        fired=transit_fired(rows),
        narrative=transit_narrative(rows),
        relations=scan.relations,
        shensha=scan.shensha,
        branch_groups=scan.branch_groups,
        months=_transit_months(natal, luck, year_keys) if focus else None,
    )


# ---------------------------------------------------------------- 节气月界（spec §6.4）
#: 十二"节"：月以节交，中间的"气"（雨水、春分……）不交月令，一个都不进这张表。
#: 序从立春起，与 `LiuYue.getIndex()` 的 0..11 逐位对齐 —— 立春之后才是正月（寅月）。
_JIE_NAMES: tuple[str, ...] = (
    "立春", "惊蛰", "清明", "立夏", "芒种", "小暑",
    "立秋", "白露", "寒露", "立冬", "大雪", "小寒",
)
#: `getJieQiTable()` 一名两键：中文名给落在窗口之内的那一次交节，大写拼音给落到窗口
#: 之外的另一次。只认中文名会在窗口边界上整年地漂 —— 实测 2026-02-01 探针里 `立春` 是
#: 2026-02-04 而 `LI_CHUN` 是 2027-02-04，`大雪` 是 2026-12-07 而 `DA_XUE` 反倒是
#: 2025-12-07。两名并收，缺的才真的是缺。
_JIE_PINYIN: tuple[str, ...] = (
    "LI_CHUN", "JING_ZHE", "QING_MING", "LI_XIA", "MANG_ZHONG", "XIAO_SHU",
    "LI_QIU", "BAI_LU", "HAN_LU", "LI_DONG", "DA_XUE", "XIAO_HAN",
)


def _jieqi_harvest(year: int) -> dict[tuple[str, int], date]:
    """把 `year` 与 `year + 1` 两次探针里的十二节收成 `(节名, 公历年) -> 交节日`。

    两次探针是必需的，不是一份表偷个懒：`getJieQiTable()` 是滚动窗口，实测以 2 月 1 日
    为基准时覆盖"上一个冬至 → 当年大雪"，于是本年的 小寒 属上一年、次年的 小寒 又还没
    进窗口，两头各差一节。键里带公历年，为的正是把跨年那一节记在它自己该在的年份里。
    """
    harvest: dict[tuple[str, int], date] = {}
    for probe_year in (year, year + 1):
        table = Solar.fromYmd(probe_year, 2, 1).getLunar().getJieQiTable()
        for name, pinyin in zip(_JIE_NAMES, _JIE_PINYIN, strict=True):
            for key in (name, pinyin):
                term = table.get(key)
                if term is not None:
                    harvest[(name, term.getYear())] = date(
                        term.getYear(), term.getMonth(), term.getDay()
                    )
    return harvest


def jieqi_boundaries(year: int) -> list[tuple[date, date]]:
    """`year` 年十二个节气月的起止日：寅月起于本年立春，丑月止于次年立春前一日。

    一节不多、一节不少 —— 少一节则后面每一段都跟着错位，而月账本还在照常加分，没有
    任何一处会喊。所以缺节是 `ValueError`，不是"给个大概"。
    """
    #: 前十二个是各月之始，第十三个（次年立春）只作末段的终点。
    marks = [(name, year) for name in _JIE_NAMES[:-1]]
    marks += [("小寒", year + 1), ("立春", year + 1)]
    harvest = _jieqi_harvest(year)
    missing = [f"{name}（{when} 年）" for name, when in marks if (name, when) not in harvest]
    if missing:
        raise ValueError(f"{year} 年缺少交节：{'、'.join(missing)}")
    edges = [harvest[key] for key in marks]
    return [
        (start, following - timedelta(days=1))
        for start, following in zip(edges, edges[1:], strict=False)  # 13 条边 → 12 段
    ]


def _transit_months(
    natal: TransitNatal, luck: AnnualLuck, year_keys: Sequence[str]
) -> list[TransitMonth]:
    """聚焦年的十二段节气月，每段一份"年段 + 月段"的两段账本（spec §6.4）。

    `year_keys` 是那一年命中的规则键，由 `_transit_year` 现算现给：月段不回头重扫年柱，
    否则年卡与月卡对同一年各算一套命中，前缀就不成立了。

    月段以 `scope="yue"` 计价：太岁与大运两族的 `scopes` 不含 `yue`，`transit_hit_keys` 当场就
    把它们挡掉，一年一次的账不会因换了一根月柱再记一遍；`dayun_ganzhi` 同时留 None，
    同一件事的两道保险。月柱的干支、序号、月名一律取 lunar-python 的 `LiuYue`（五虎遁
    在历法手里），引擎只负责把它和 `jieqi_boundaries` 推出来的月界逐位对齐。
    """
    months: list[TransitMonth] = []
    boundaries = jieqi_boundaries(luck.year)
    for liu_yue, (start, end) in zip(luck.liunian.getLiuYue(), boundaries, strict=True):
        ganzhi = liu_yue.getGanZhi()
        scan = scan_transit_pillar(
            natal,
            ganzhi,
            position="transit_month",
            label="流月",
            scope="yue",
            dayun_ganzhi=None,
        )
        rows = hit_rows(year_keys, transit_hit_keys(scan.judgement))
        months.append(
            TransitMonth(
                index=liu_yue.getIndex(),
                month_in_chinese=liu_yue.getMonthInChinese(),
                ganzhi=ganzhi,
                pillar=scan.pillar,
                start_solar=start.isoformat(),
                end_solar=end.isoformat(),
                score=transit_ledger(rows),
                fired=transit_fired(rows),
            )
        )
    return months


# ---------------------------------------------------------------- 总装（spec §7.4）
def _covered_dayun(chart: BaziChart, span: TransitRange) -> list[DayunStep]:
    """区间跨过的运程，取主命盘算好的那一份而不是另起一次 `getYun()`。

    当前运的旗标（`is_current`）因此与命盘页同源，两页不会各说一个"今年在哪步运里"；
    童年段也照样给出，它的 `ganzhi` 本就是空串 —— 那是 `DayunStep` 已有的约定。
    """
    return [
        step
        for step in chart.dayun
        if step.start_year <= span.end_year and span.start_year <= step.end_year
    ]


def compute_transit(
    *,
    birth_date: date,
    birth_time: time,
    gender: Gender,
    calendar: CalendarType = CalendarType.SOLAR,
    longitude: float = STANDARD_MERIDIAN_CN,
    apply_true_solar_time: bool = True,
    start_year: int | None = None,
    end_year: int | None = None,
    focus_year: int | None = None,
    reference_date: date | None = None,
    name: str | None = None,
) -> BaziTransitResult:
    """从生辰与年份区间装配一整页岁运（流年 + 可选的聚焦年十二节气月）。

    无 HTTP、无 I/O；随调用时刻变化的只有 `reference_date` 缺省，它同时决定缺省区间
    与当前运档，并经 `provenance.reference_date` 回显，所以响应自己就带着复现它的日期。

    排盘走两次同一个入口：`compute_bazi_chart` 出命局（喜忌、大运、溯源，岁运一行都不
    重算），`resolve_natal_moment` 出岁运还要用的那个 `EightChar`。两次都过同一个校正
    函数，因而不会出现"命盘用 23:30、岁运用 23:26"的两个口径 —— 这正是校正逻辑只留一份
    的原因（它在 `bazi_moment`，两个引擎同源于此）。

    性别必填在这里也是结构性的：大运方向定不下来就没有流年可摊，而区间校验要的窗口
    正是摊出来的首末两年（1988 / 2083 于命 A）。窗口取自同一份摊平结果，请求里的年份
    便一定查得到，区间之内不设"这年推不出"的第三种说法。

    摘要只带这一页要用的那几件。把整个 `BaziChart` 塞进来看着省事，实际是把"命盘"与
    "推演"绑成一次输出：主命盘的契约一改，岁运页跟着改，而这两页本就各自独立可达。
    """
    reference = reference_date or date.today()
    chart = compute_bazi_chart(
        birth_date=birth_date,
        birth_time=birth_time,
        calendar=calendar,
        longitude=longitude,
        gender=gender,
        apply_true_solar_time=apply_true_solar_time,
        reference_date=reference,
        name=name,
    )
    moment = resolve_natal_moment(
        birth_date=birth_date,
        birth_time=birth_time,
        calendar=calendar,
        longitude=longitude,
        apply_true_solar_time=apply_true_solar_time,
    )
    luck = annual_luck_by_year(moment.eight_char, gender)
    span = resolve_transit_range(
        start_year=start_year,
        end_year=end_year,
        focus_year=focus_year,
        reference_year=reference.year,
        supported_from=min(luck),
        supported_to=max(luck),
    )
    natal = natal_projection(chart)
    return BaziTransitResult(
        four_pillars=chart.four_pillars,
        pillars=list(chart.pillars),
        day_master=chart.day_master,
        day_master_element=chart.day_master_element,
        favorable_elements=list(chart.analysis.favorable_elements),
        unfavorable_elements=list(chart.analysis.unfavorable_elements),
        true_solar_time=chart.true_solar_time,
        tst_applied=chart.tst_applied,
        longitude=chart.longitude,
        start_year=span.start_year,
        end_year=span.end_year,
        focus_year=span.focus_year,
        dayun_covered=_covered_dayun(chart, span),
        years=[
            _transit_year(natal, luck[year], focus=year == span.focus_year)
            for year in range(span.start_year, span.end_year + 1)
        ],
        provenance=Provenance(
            reference_date=reference.isoformat(),
            engine="lunar-python",
            tables=[
                ProvenanceTable(name=module, version=CONTENT_VERSION, source=source)
                for module, source in (*CONTENT_SOURCES, *TRANSIT_CONTENT_SOURCES)
            ],
        ),
    )
