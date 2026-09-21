"""岁运（流年 / 流月）引擎：区间解析、排盘时刻共用件，与其后的命中判定与账本装配。

本模块**不重复**任何命局推导：喜忌取自 `select_yongshen` 的合并结果，关系、合局、
神煞由 `bazi_rules` 的三个 derive 函数带上岁运之柱重扫一遍，柱的十神 / 地势 / 纳音
由 `bazi_pillar.build_transit_pillar` 合成。计分是岁运自己的一张表
（`content/bazi_transit_rules`，46 条），命局的 39 条判语、旺衰三因子与用神都不参
与，也不被改写（spec §4 决策 3）。

`resolve_natal_moment` 住在这里是刻意的：岁运要再走一次 `getYun()` 才拿得到流年与
流月对象，而那一刻必须先和主命盘用同一个真太阳时校正 —— 校正逻辑有两份，迟早分出
两个口径。所以它从 `compute_bazi_chart` 里原样搬来，主命盘改为消费它。
"""

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import date, datetime, time

from lunar_python import Lunar, Solar

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
from app.engines.bazi_pillar import build_transit_pillar
from app.engines.bazi_rules import (
    derive_branch_groups,
    derive_relations,
    derive_shensha,
    is_fanyin,
)
from app.engines.bazi_strength import STRONG_CUT, WEAK_CUT
from app.schemas.bazi import BaziChart, BaziPillar
from app.schemas.bazi_rules import BranchGroup, RelationPair, ShenShaEntry
from app.schemas.bazi_transit import TransitFired, TransitMonth, TransitTenGod, TransitYear
from app.schemas.common import CalendarType, Gender
from app.schemas.scoring import ScoreFactor, ScoreValue, build_ledger
from app.solar.true_solar_time import true_solar_offset_minutes, true_solar_time

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


@dataclass(frozen=True)
class NatalMoment:
    """排盘输入经真太阳时校正后的那一刻，与由它起出的 lunar-python 对象。

    `standard_datetime` 是用户填的那一刻（响应里的 `standard_datetime` 字段），
    `chart_datetime` 是校正后实际起柱的那一刻；关掉校正时两者相同，且
    `true_solar_time_text` / `offset_minutes` 留空而不是填 0 —— "没校正"和"校正量
    恰为零"是两件事。
    """

    standard_datetime: datetime
    chart_datetime: datetime
    longitude_used: float
    true_solar_time_text: str | None
    offset_minutes: float | None
    lunar: Lunar
    eight_char: object  # lunar_python.EightChar；本仓一贯不依赖其类型名


def resolve_natal_moment(
    *,
    birth_date: date,
    birth_time: time,
    calendar: CalendarType,
    longitude: float,
    apply_true_solar_time: bool,
) -> NatalMoment:
    """Resolve birth input into the instant the chart is actually cast from.

    A lunar-calendar date is converted to its Gregorian equivalent (preserving
    the wall-clock time) so both the True Solar Time correction and the pillar
    derivation operate on one standard civil datetime; ``lunar-python`` uses the
    supplied wall-clock time verbatim, hence the correction is applied *before*
    ``Solar(...)`` is constructed.
    """
    standard_dt = _standard_datetime(birth_date, birth_time, calendar)

    if apply_true_solar_time:
        chart_dt = true_solar_time(standard_dt, longitude)
        offset_minutes: float | None = round(true_solar_offset_minutes(standard_dt, longitude), 2)
        tst_text: str | None = chart_dt.strftime("%Y-%m-%d %H:%M")
    else:
        chart_dt = standard_dt
        offset_minutes = None
        tst_text = None

    solar = Solar.fromYmdHms(
        chart_dt.year, chart_dt.month, chart_dt.day, chart_dt.hour, chart_dt.minute, chart_dt.second
    )
    lunar = solar.getLunar()
    return NatalMoment(
        standard_datetime=standard_dt,
        chart_datetime=chart_dt,
        longitude_used=longitude,
        true_solar_time_text=tst_text,
        offset_minutes=offset_minutes,
        lunar=lunar,
        eight_char=lunar.getEightChar(),
    )


def _standard_datetime(birth_date: date, birth_time: time, calendar: CalendarType) -> datetime:
    """Return the civil standard-time datetime for the supplied birth data."""
    if calendar is CalendarType.LUNAR:
        lunar = Lunar.fromYmdHms(
            birth_date.year,
            birth_date.month,
            birth_date.day,
            birth_time.hour,
            birth_time.minute,
            birth_time.second,
        )
        solar = lunar.getSolar()
        return datetime(
            solar.getYear(),
            solar.getMonth(),
            solar.getDay(),
            solar.getHour(),
            solar.getMinute(),
            solar.getSecond(),
        )
    return datetime.combine(birth_date, birth_time)


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
class _Judgement:
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


def _group_faces(j: _Judgement, kind: str, *, favourable: bool) -> bool:
    """局本身不论吉凶：合出的五行落进喜用集才算顺、落进忌神集才算逆（spec §6.2）。"""
    elements = j.group_elements(kind)
    return bool(elements & (j.favourable if favourable else j.unfavourable))


Predicate = Callable[[_Judgement], bool]
#: 大运谓词多收一个参数：过闸之后的大运干支。谓词因此不必各自判空。
DayunPredicate = Callable[[_Judgement, str], bool]


def _gan_element(ganzhi: str) -> str:
    """干之五行。运岁生克只以干论：一支藏多气，论支就有一支两种向背。"""
    return GAN_ELEMENT[ganzhi[0]]


def _on_dayun(predicate: DayunPredicate) -> Predicate:
    """大运族的总闸：童年段 `DaYun.getGanZhi()` 为空串，无运可论则整族不评估。

    闸写在谓词上而不是写在装配段，因为"空串"与"这条岁运没有对应大运"是同一件事的两
    种说法，装配段以后换法时判定层不该跟着改。
    """

    def gated(judgement: _Judgement) -> bool:
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


def _hit_keys(judgement: _Judgement) -> list[str]:
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
class _Natal:
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


def _natal_projection(chart: BaziChart) -> _Natal:
    """从已算好的命盘里取出岁运要读的字段。"""
    return _Natal(
        pillars=list(chart.pillars),
        day_master=chart.day_master,
        year_zhi=chart.pillars[0].zhi,  # 年柱之支即本命，太岁以此为准
        favourable=frozenset(chart.analysis.favorable_elements),
        unfavourable=frozenset(chart.analysis.unfavorable_elements),
    )


# ---------------------------------------------------------------- 岁运扫描（spec §7.3）
@dataclass(frozen=True)
class _Scan:
    """一根岁运柱扫完的结果：合成柱、打分上下文，与随响应发出的三张明细。

    三张明细都只留一端落在 `_TRANSIT_SLOT` 的条目。命局四柱内部本来就有的象是命局
    自己的账（决策 3），灌进岁运账本会重复计价，前端也会把同一条象显示两遍。
    """

    pillar: BaziPillar
    judgement: _Judgement
    relations: list[RelationPair]
    shensha: list[ShenShaEntry]
    branch_groups: list[BranchGroup]


def _scan(
    natal: _Natal,
    ganzhi: str,
    *,
    position: str,
    label: str,
    scope: str,
    dayun_ganzhi: str | None,
) -> _Scan:
    """以命局四柱为体、岁运一柱为用，重扫关系 / 合局 / 神煞，并留下岁运落点。

    `scope` 决定这条柱按岁还是按月计价（`_hit_keys` 用规则的 `scopes` 过滤）；
    `dayun_ganzhi` 只有流年给得出，流月留 None —— 大运只与流年论（spec §6.2）。
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
    judgement = _Judgement(
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
    return _Scan(
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


def _hit_rows(
    year_keys: Sequence[str], month_keys: Sequence[str]
) -> list[tuple[ScoreFactor, TransitRule]]:
    """命中集 → (账本行, 规则) 成对。

    账本与 `fired` 读同一份产出，所以"逐行可见的判语"与"这一行的分值"不可能分家；
    月段在键前加 `yue.`、在短名后加"（流月）"，因为一条规则可以在一份月账本里出现
    两次（年段一次、月段一次），不带前缀就读不出那一行是谁加的分。
    """
    rows: list[tuple[ScoreFactor, TransitRule]] = []
    for keys, is_month in ((year_keys, False), (month_keys, True)):
        for key in keys:
            rule = transit_rule(key)
            rows.append(
                (
                    ScoreFactor(
                        rule=f"yue.{key}" if is_month else key,
                        label=f"{rule.label}（流月）" if is_month else rule.label,
                        delta=rule.delta,
                        source=TRANSIT_RULE_SOURCE,
                    ),
                    rule,
                )
            )
    return rows


def _ledger(rows: Sequence[tuple[ScoreFactor, TransitRule]]) -> ScoreValue:
    """命中行 → 自解释账本；截断由 `build_ledger` 记成它自己的一行。"""
    raw_total = TRANSIT_BASE + sum(factor.delta for factor, _ in rows)
    return build_ledger(
        base=TRANSIT_BASE,
        tier=_tier(min(100.0, max(0.0, raw_total))),
        contributions=[factor for factor, _ in rows],
        base_rule="transit.base",
    )


def _fired(rows: Sequence[tuple[ScoreFactor, TransitRule]]) -> list[TransitFired]:
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


def _narrative(rows: Sequence[tuple[ScoreFactor, TransitRule]]) -> str:
    """命中判语连缀，与六维详批同法。一条未中时返回空串，而不是一个孤零零的句号。"""
    if not rows:
        return ""
    return "；".join(rule.reading for _, rule in rows) + "。"


# ---------------------------------------------------------------- 流年对象（spec §7.3）
@dataclass(frozen=True)
class _AnnualLuck:
    """lunar-python 给的一个流年：干支、虚岁，加上它所从出的那一步大运。"""

    year: int
    age: int
    ganzhi: str
    dayun_index: int
    dayun_ganzhi: str | None


def _annual_luck_by_year(
    eight_char: object, gender: Gender | None
) -> dict[int, _AnnualLuck]:
    """`getYun().getDaYun()[i].getLiuNian()` 摊平成 `公历年 -> 流年`。

    流年必须从大运段里取，不能按公历年自己算干支：起运前的童年段也排在 `getDaYun()`
    第 0 项里，摊平这一步顺带记下"这一年属于第几步运"，而大运族正要论这件事。
    `getGanZhi()` 在童年段是空串，这里翻成 None —— "无运可论"与"运干为空字符串"两件
    事里，前者才是事实。性别未知则方向都定不下来，返回空表而不是猜一个（spec §8.4）。
    """
    if gender is None:
        return {}
    luck: dict[int, _AnnualLuck] = {}
    for step in eight_char.getYun(1 if gender is Gender.MALE else 0).getDaYun():
        for liu_nian in step.getLiuNian():
            luck[liu_nian.getYear()] = _AnnualLuck(
                year=liu_nian.getYear(),
                age=liu_nian.getAge(),
                ganzhi=liu_nian.getGanZhi(),
                dayun_index=step.getIndex(),
                dayun_ganzhi=step.getGanZhi() or None,
            )
    return luck


def _transit_year(
    natal: _Natal, luck: _AnnualLuck, *, months: list[TransitMonth] | None = None
) -> TransitYear:
    """装配一个流年：合成柱、单段账本、三张岁运明细、十神释义与断语。

    `months` 由流月那一段（Task 9）在聚焦年传入；其余年为 None，前端整块不渲染，
    而不是渲染十二个空月。
    """
    scan = _scan(
        natal,
        luck.ganzhi,
        position="transit_year",
        label="流年",
        scope="sui",
        dayun_ganzhi=luck.dayun_ganzhi,
    )
    rows = _hit_rows(_hit_keys(scan.judgement), [])
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
        score=_ledger(rows),
        fired=_fired(rows),
        narrative=_narrative(rows),
        relations=scan.relations,
        shensha=scan.shensha,
        branch_groups=scan.branch_groups,
        months=months,
    )
