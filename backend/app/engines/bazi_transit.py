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

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, time

from lunar_python import Lunar, Solar

from app.content.bazi_transit_rules import transit_rule
from app.core.errors import TransitRangeError
from app.schemas.bazi_rules import BranchGroup, RelationPair
from app.schemas.common import CalendarType
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
    dayun_ganzhi: str | None  # 童年段（未起运）为 None：整个 dayun 族不评估
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

    @property
    def has_dayun(self) -> bool:
        return bool(self.dayun_ganzhi)


def _group_faces(j: _Judgement, kind: str, *, favourable: bool) -> bool:
    """局本身不论吉凶：合出的五行落进喜用集才算顺、落进忌神集才算逆（spec §6.2）。"""
    elements = j.group_elements(kind)
    return bool(elements & (j.favourable if favourable else j.unfavourable))


Predicate = Callable[[_Judgement], bool]

#: 键序 == `TRANSIT_RULES` 的表序 == 账本行序；一键一谓词，由 Task 7 末尾的完备性
#: 断言钉住。谓词本身不含古籍字 —— 文案在 `reading` 里，分数在 `delta` 里。
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
    # dayun / dishi / shensha 三族 18 键在 Task 7 追加。
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
