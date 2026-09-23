"""合婚引擎（spec §10.1–10.6）。

夹具一律**用真实生辰走 `compute_bazi_chart`**：全仓 0 处手搓 `BaziPillar` 列表
（§2.7），本轮不破例。§2.7 的两对走查命例与 §2.9 的七枚构造命例、§6.2 的交接命例在此一次立齐，
后面每个任务都只往这个文件追加测。
"""

from datetime import date, time

import pytest

from app.content import CONTENT_VERSION
from app.content.bazi_hehun_rules import (
    ELEMENT_ATTRIBUTIONS,
    HEHUN_BASE,
    HEHUN_FAMILIES,
    HEHUN_MODEL_SOURCE,
    HEHUN_NAYIN_NOTE,
    HEHUN_PALACE_KEYS,
    HEHUN_RULES,
    HEHUN_RULE_SOURCE,
    HEHUN_SYNC_CLOSE,
    HEHUN_SYNC_WIDE,
    HEHUN_YIJI_DECLARATION,
    hehun_rule,
)
from app.content.bazi_nayin import nayin_meaning
from app.core.errors import InvalidBirthDataError, TransitRangeError
from app.engines.bazi import compute_bazi_chart
from app.engines.bazi_hehun import (
    PALACE_BRANCH_CLASH,
    PALACE_BRANCH_HARMONY,
    PALACE_BRANCH_MERGE,
    PALACE_PILLAR_REVERSE,
    PALACE_STEM_MERGE,
    PILLAR_NAME,
    POSITION_ORDER,
    YONGSHEN_QUADRANT,
    YONGSHEN_QUADRANTS,
    YONGSHEN_VIEWS,
    GroupMember,
    HehunAxisRange,
    HehunAxisWindow,
    HehunChartPair,
    axis_segments,
    axis_sync,
    axis_window,
    complement,
    compute_hehun,
    compute_partner_charts,
    cross_groups,
    cross_relations,
    element_vigor,
    group_bonds_both_day_pillars,
    group_is_a_palace_fact,
    group_is_new_between_charts,
    group_rows,
    group_spans_both_charts,
    hehun_axis,
    hehun_fired,
    hehun_ledger,
    hehun_rows,
    hehun_tier,
    nayin_key,
    nayin_relation,
    nayin_row,
    nayin_view,
    pair_matrix,
    palace_keys,
    palace_rows,
    partner_annual_luck,
    partner_profile,
    relation_rows,
    resolve_hehun_axis_range,
    scanned_groups,
    yi_ji,
    yongshen_facts,
    yongshen_rows,
)
from app.engines.bazi_rules import derive_relations
from app.engines.bazi_transit import compute_transit
from app.schemas.bazi import BaziChart
from app.schemas.bazi_hehun import BaziHehunRequest, BaziHehunResult, HehunAxis, HehunProfile
from app.schemas.common import Gender
from app.schemas.scoring import MODEL_PARAM_SOURCE
from app.solar.geo import resolve_longitude


def _chart(y: int, m: int, d: int, hh: int, mm: int, city: str, gender: Gender) -> BaziChart:
    """按城市定经线，与站内测的 `_chart` 同一取法（`tests/test_bazi_geju.py:18`）。"""
    return compute_bazi_chart(
        birth_date=date(y, m, d),
        birth_time=time(hh, mm),
        longitude=resolve_longitude(city, None),
        gender=gender,
        apply_true_solar_time=True,
    )


def _profile(y: int, m: int, d: int, hh: int, mm: int, city: str) -> HehunProfile:
    return HehunProfile(birth_date=date(y, m, d), birth_time=time(hh, mm), city=city)


# 乾造参照：戊辰 甲寅 庚子 丁亥，喜土金忌木水火（spec §2.7、§2.9 全部命例以此为准）
MALE = _chart(1988, 2, 15, 23, 30, "成都", Gender.MALE)
# 同频对 坤：庚午 壬午 辛亥 癸巳，喜金土忌水火木 —— 12 条跨造关系 + 1 条跨造半合
FEMALE_SAME = _chart(1990, 6, 15, 10, 0, "北京", Gender.FEMALE)
# 互补对 坤：乙丑 癸未 壬戌 丁未，喜水金忌土火木 —— 浏览器走查用这一对
FEMALE_COMPLEMENT = _chart(1985, 7, 22, 14, 30, "上海", Gender.FEMALE)

# §2.9 构造命例与 §6.2 交接例：婚姻宫四族、四档可达性、成局族交接，全部按生辰实测（全仓 0 处手搓 BaziPillar）
# 全吉对：乾自带的辰子半合水因"坤 那颗子只是同字重复"被 §2.3 第二道判据滤掉 → 成局族空
FEMALE_AUSPICIOUS = _chart(1995, 9, 18, 18, 0, "北京", Gender.FEMALE)   # 乙亥 乙酉 壬子 己酉
# 欠和对：乾有辰子、坤来申辰 → 半合升级为三合，kind 变了 → 入账（§2.3 反向对照）
FEMALE_HOSTILE = _chart(1989, 8, 18, 10, 0, "成都", Gender.FEMALE)      # 己巳 壬申 庚戌 庚辰
# 支级最干净的正例：(乾日, 坤日) 格里只有地支六冲一条 → 对称族里一次都不出现
FEMALE_DAY_CLASH = _chart(1989, 3, 11, 10, 0, "成都", Gender.FEMALE)    # 己巳 丁卯 庚午 庚辰
# 柱级封口：庚子 × 甲午 = 干冲 + 支冲 = 反吟，该格三条命中全封
FEMALE_DAY_REVERSE = _chart(1989, 4, 4, 7, 0, "成都", Gender.FEMALE)    # 己巳 丁卯 甲午 丁卯
# 干级 + 支级各出一条：日干庚乙五合、日管子丑六合 → 总账本 13 行 74.0（Task 4 装配完整账本后的数）
FEMALE_DAY_MERGE = _chart(1996, 11, 24, 14, 30, "成都", Gender.FEMALE)  # 丙子 己亥 乙丑 癸未
# 支级的第三条路：申子辰三合跨两造日支，格内**没有**任何一条六合关系 → branch_merge 全由成局族撑起
FEMALE_GROUP_MERGE = _chart(1992, 2, 2, 20, 0, "成都", Gender.FEMALE)   # 辛未 辛丑 戊申 辛酉
# 格内只有日干相冲：婚姻宫族不立"日干冲"那一键，所以这一格空手，那条命中留在对称族
FEMALE_STEM_CLASH = _chart(1997, 2, 1, 15, 0, "成都", Gender.FEMALE)    # 丙子 辛丑 甲戌 辛未
# §6.2 与成局族的交接：日柱伏吟（乾 庚子 × 坤 庚子）把归属收在柱级一条上，而申子辰三合
# 跨住两造日支 —— 那一格没有支级行可收编，成局族这一行必须照记（+8 不该两头都不入账）
FEMALE_DAY_FUYIN_GROUP = _chart(1985, 8, 29, 3, 30, "成都", Gender.FEMALE)  # 乙丑 甲申 庚子 丁丑


def _pair_of(female: BaziChart) -> HehunChartPair:
    return HehunChartPair(male=MALE, female=female)


def test_two_charts_come_from_one_call_and_neither_is_mutated() -> None:
    """§10.1 污染红线：合婚第一次把两造同时喂进 `_slots()` 派生关系。"""
    before_male, before_female = MALE.model_dump_json(), FEMALE_SAME.model_dump_json()
    assert len(cross_relations(_pair_of(FEMALE_SAME))) == 12
    assert (MALE.model_dump_json(), FEMALE_SAME.model_dump_json()) == (before_male, before_female)


def test_the_cross_chart_scan_keeps_only_genuine_cross_facts() -> None:
    """§2.1 实测：16 行里 12 行跨造、4 行各自盘内；少那一步滤，两造各自的账会被加第二遍。"""
    hits = cross_relations(_pair_of(FEMALE_SAME))
    assert len(derive_relations(MALE.pillars, [p.ganzhi for p in FEMALE_SAME.pillars])) == 16
    assert {(hit.kind, hit.male_position, hit.female_position) for hit in hits} == {
        ("天干五合", "year", "hour"),
        ("天干相冲", "month", "year"),
        ("地支六合", "month", "day"),
        ("地支六害", "month", "hour"),
        ("无恩之刑", "month", "hour"),
        ("地支六冲", "day", "year"),
        ("地支六冲", "day", "month"),
        ("天干五合", "hour", "month"),
        ("自刑", "hour", "day"),
        ("天干相冲", "hour", "hour"),
        ("地支六冲", "hour", "hour"),
        ("反吟", "hour", "hour"),
    }
    # 点名被滤的四行：乾自己的 寅亥合/甲庚冲、坤自己的 午午自刑/亥巳冲。
    # 前两行尤其要紧 —— 乾时支亥与坤日支亥也成一个寅亥合，同一 kind 同格位附近
    # 既有一行是跨造事实、有一行不是，只看 kind 分不出来，必须靠 `_is_extra` 的两端判定。
    seen = {(hit.kind, hit.male_position, hit.female_position) for hit in hits}
    assert ("地支六合", "month", "hour") not in seen  # 乾 月寅 × 乾 时亥
    assert ("天干相冲", "month", "day") not in seen  # 乾 月甲 × 乾 日庚
    assert ("自刑", "year", "month") not in seen  # 坤 年午 × 坤 月午
    assert ("地支六冲", "day", "hour") not in seen  # 坤 日亥 × 坤 时巳


def test_extra_index_maps_back_to_the_partners_own_position() -> None:
    """§2.4：`extra{n}` ↔ 坤 pillars[n]，序为年→月→日→时；报出的字必须真出自那一根柱。"""
    hits = cross_relations(_pair_of(FEMALE_COMPLEMENT))
    assert [(h.kind, h.male_position, h.female_position, h.female_character) for h in hits] == [
        ("地支六破", "year", "year", "丑"),
        ("天干五合", "year", "month", "癸"),
        ("地支六冲", "year", "day", "戌"),
        ("天干五合", "day", "year", "乙"),
        ("地支六合", "day", "year", "丑"),
        ("地支六害", "day", "month", "未"),
        ("地支六害", "day", "hour", "未"),
        ("天干相冲", "hour", "month", "癸"),
        ("天干五合", "hour", "day", "壬"),
    ]
    # 四个 extra 下标在上一段里都出现过（year/month/day/hour 各至少一次），这一段把它
    # 钉成不变式：每一行的两个字都各自出自它所属那一造的那一根柱。
    for hit in hits:
        male = MALE.pillars[POSITION_ORDER.index(hit.male_position)]
        female = FEMALE_COMPLEMENT.pillars[POSITION_ORDER.index(hit.female_position)]
        assert hit.male_character in {male.gan, male.zhi, male.ganzhi}
        assert hit.female_character in {female.gan, female.zhi, female.ganzhi}


def test_every_symmetric_fact_is_booked_exactly_once_as_mutual() -> None:
    """§10.4 首条：乾午冲坤子是一件事实而不是两件，所以 direction 恒为 mutual。"""
    rows = relation_rows(_pair_of(FEMALE_SAME))
    assert len(rows) == 12
    assert {row.direction for row in rows} == {"mutual"}
    assert {row.family for row in rows} == {"relation"}
    clash = [row for row in rows if row.rule == "hh.relation.branch_clash"]
    assert len(clash) == 3                       # 三条六冲各一行，不合并也不双计


def test_the_matrix_is_always_sixteen_cells_and_empty_cells_are_lists() -> None:
    cells = pair_matrix(_pair_of(FEMALE_COMPLEMENT))
    assert len(cells) == 16
    assert [(c.male_position, c.female_position) for c in cells][:5] == [
        ("year", "year"),
        ("year", "month"),
        ("year", "day"),
        ("year", "hour"),
        ("month", "year"),
    ]
    empty = [c for c in cells if not c.hits]
    assert all(cell.hits == [] for cell in empty)
    # 9 = 本文件上面 `test_extra_index_maps_back_to_the_partners_own_position` 逐条点过的那九行；
    # 矩阵与账本同源，所以这里的总数就是那一趟扫描的行数（合局不占格，它没有柱位对）。
    assert sum(len(c.hits) for c in cells) == 9


def test_an_illegal_partner_fails_the_whole_request_and_says_who() -> None:
    """§9.1/§9.2：一造合法一造非法时整请求失败，绝不回半张盘；只加 `partner` 一项归属。"""
    broken = _profile(1988, 2, 15, 23, 30, "不存在的地方")
    with pytest.raises(InvalidBirthDataError) as raised:
        compute_partner_charts(_profile(1988, 2, 15, 23, 30, "成都"), broken, date(2026, 9, 22))
    assert raised.value.context == {"partner": "female"}
    assert raised.value.code == "invalid_birth_data"
    assert raised.value.status_code == InvalidBirthDataError.status_code
    reversed_ = pytest.raises(InvalidBirthDataError)
    with reversed_ as again:
        compute_partner_charts(broken, _profile(1990, 6, 15, 10, 0, "北京"), date(2026, 9, 22))
    assert again.value.context == {"partner": "male"}


def test_the_two_profiles_are_charted_with_their_own_meridian_decision() -> None:
    """§5.1：`apply_true_solar_time` 各造一份，关掉校正的一方不能带动另一方。"""
    pair = compute_partner_charts(
        _profile(1988, 2, 15, 23, 30, "成都"),
        _profile(1990, 6, 15, 10, 0, "北京"),
        date(2026, 9, 22),
    )
    assert (pair.male.four_pillars, pair.female.four_pillars) == (
        "戊辰 甲寅 庚子 丁亥",
        "庚午 壬午 辛亥 癸巳",
    )
    assert pair.male.provenance is not None and pair.male.provenance.reference_date == "2026-09-22"


def test_a_group_needs_a_member_from_each_chart_to_be_a_fact_between_them() -> None:
    """§2.3 第一道判据：切片 2 那句"任一成员落在 extra"在合婚里会把彼造自己的局当跨造事实。

    `FEMALE_SAME` 实测两局：半合水（乾 自己的辰子）与半合火（乾月寅 + 坤 两午）。
    前者两侧不齐 → 滤，后者 → 入账。
    """
    pair = _pair_of(FEMALE_SAME)
    scanned = scanned_groups(pair)
    assert [(g.kind, g.element) for g in scanned] == [("半合", "水"), ("半合", "火")]
    # 判据的真假各钉一次：期望若是 `group_spans_both_charts` 现算出来的，谓词写反时两边一起反，
    # 这一条测就恒真（§2.3 明说第一道判据"单独设测"，测的正是它自己）。
    assert [group_spans_both_charts(g) for g in scanned] == [False, True]
    assert [(g.kind, g.element, g.members) for g in cross_groups(pair)] == [
        (
            "半合",
            "火",
            (
                GroupMember("male", "month", "寅"),
                GroupMember("female", "year", "午"),
                GroupMember("female", "month", "午"),
            ),
        )
    ]


def test_a_group_that_only_repeats_one_charts_own_group_is_not_a_new_fact() -> None:
    """§2.3 第二道判据的两侧：对方那颗同字的支没有补上新支，就没有第二次加分的理由。

    乾侧：`FEMALE_AUSPICIOUS` 的半合水（乾辰子 + 坤子）—— 摘掉 坤 那颗子，乾 自己仍是同一个半合水。
    坤侧：`FEMALE_DAY_MERGE` 的三会水（乾亥子 + 坤亥子丑）—— 乾 一侧立不起三会，坤 自己就是亥子丑。
    """
    auspicious = scanned_groups(_pair_of(FEMALE_AUSPICIOUS))
    assert [(g.kind, g.element, g.members) for g in auspicious] == [
        (
            "半合",
            "水",
            (
                GroupMember("male", "year", "辰"),
                GroupMember("male", "day", "子"),
                GroupMember("female", "day", "子"),
            ),
        )
    ]
    assert all(group_spans_both_charts(g) for g in auspicious)      # 第一道判据留下了它
    assert not any(group_is_new_between_charts(g) for g in auspicious)  # 第二道判据滤掉它
    assert cross_groups(_pair_of(FEMALE_AUSPICIOUS)) == []

    day_merge = scanned_groups(_pair_of(FEMALE_DAY_MERGE))
    assert [(g.kind, g.element) for g in day_merge] == [("半合", "水"), ("三会", "水")]
    assert not any(group_is_new_between_charts(g) for g in day_merge)
    assert cross_groups(_pair_of(FEMALE_DAY_MERGE)) == []


def test_an_upgrade_of_the_kind_makes_the_group_a_new_fact() -> None:
    """§2.3 的反向对照：乾 有 辰子（半合水）、坤 来 申 → 跨造三合水，kind 变了就入账。

    判据只看 `kind` 与 `element`，不看成员，所以这一局与上一测那一局的分野是可核对的。
    乾日支 子 在局里、坤日支 戌 不在 → 它不是婚姻宫支级（下一测的另一半）。
    """
    groups = cross_groups(_pair_of(FEMALE_HOSTILE))
    assert [(g.kind, g.element, g.members) for g in groups] == [
        (
            "三合",
            "水",
            (
                GroupMember("male", "year", "辰"),
                GroupMember("male", "day", "子"),
                GroupMember("female", "month", "申"),
                GroupMember("female", "hour", "辰"),
            ),
        )
    ]
    assert group_bonds_both_day_pillars(groups[0]) is False


def test_each_booked_group_books_one_mutual_row_named_by_its_element() -> None:
    """成局族：一局一行、`mutual`，短名带五行的那半句用来分辨同 kind 的两局。"""
    assert [
        (row.rule, row.label, row.family, row.direction, row.delta)
        for row in group_rows(_pair_of(FEMALE_DAY_CLASH))
    ] == [
        ("hh.group.three_meeting", "跨造三会（木）", "group", "mutual", 6.0),
        ("hh.group.half_harmony", "跨造半合（火）", "group", "mutual", 4.0),
        ("hh.group.half_harmony", "跨造半合（木）", "group", "mutual", 4.0),
    ]


def test_a_group_that_bonds_both_day_pillars_is_booked_in_the_palace_family() -> None:
    """§6.2 支级的第三条路：格内一条关系都没有，`branch_merge` 完全由三合撑起来。

    `FEMALE_GROUP_MERGE`：乾日 子 × 坤日 申，两者无六合无冲无害无破 —— 矩阵那一格是空的，
    但 申子辰 那一局把两人的日支拴在了一起。同一局不能在成局族再记一次，于是 `+8` 的
    三合换成 `+8` 的婚姻宫；同造的另一局（三会水，未含坤日）照旧进成局族。
    """
    pair = _pair_of(FEMALE_GROUP_MERGE)
    assert [(g.kind, g.element) for g in cross_groups(pair) if group_is_a_palace_fact(g)] == [
        ("三合", "水")
    ]
    assert [(row.rule, row.label) for row in group_rows(pair)] == [
        ("hh.group.three_meeting", "跨造三会（水）")
    ]
    assert palace_keys(pair) == ["hh.palace.branch_merge"]
    day_cell = next(
        cell
        for cell in pair_matrix(pair)
        if (cell.male_position, cell.female_position) == ("day", "day")
    )
    assert day_cell.hits == []


def test_a_pillar_level_fact_seals_the_whole_palace_cell() -> None:
    """§6.2 柱级优先：反吟的两半正是"干相冲 + 支六冲"，再各记一条就是把一件事记三遍。

    乾 庚子 × 坤 甲午 一格里三条命中全封；同 kind 的其他格（乾日 子 × 坤月 卯 的无礼之刑）
    照常入账，封口只针对那一格。
    """
    pair = _pair_of(FEMALE_DAY_REVERSE)
    assert palace_keys(pair) == ["hh.palace.pillar_reverse"]
    hits = cross_relations(pair)
    assert [
        hit.kind
        for hit in hits
        if (hit.male_position, hit.female_position) == ("day", "day")
    ] == [
        "天干相冲",
        "地支六冲",
        "反吟",
    ]
    assert len(hits) == 11
    assert len(relation_rows(pair)) == 8
    assert not any(row.label.endswith("（乾日×坤日）") for row in relation_rows(pair))
    # 格位逐字断言：(乾日, 坤月) 那一格里照记账的确实且仅有 乾日 子 × 坤月 卯 的一条无礼之刑。
    assert [
        row.label for row in relation_rows(pair) if row.label.endswith("（乾日×坤月）")
    ] == ["无礼之刑（乾日×坤月）"]


def test_a_branch_clash_in_the_palace_leaves_the_relation_family_clean() -> None:
    """§10.4：账本只有 `hh.palace.branch_clash` 一行，`hh.relation.*` 里没有同一件事。

    乾 子 × 坤 午 那一格只有地支六冲一条（`FEMALE_DAY_CLASH` 实测），所以它是归属规则
    最干净的正例；对称族里另外两条六冲（乾时亥 × 坤年巳、乾月… ）照常入账。
    """
    pair = _pair_of(FEMALE_DAY_CLASH)
    assert palace_keys(pair) == ["hh.palace.branch_clash"]
    rows = relation_rows(pair)
    assert len(rows) == len(cross_relations(pair)) - 1
    assert ("hh.palace.branch_clash", "日支战") in [(r.rule, r.label) for r in palace_rows(pair)]
    assert not [r for r in rows if r.label.endswith("（乾日×坤日）")]


def test_stem_and_branch_levels_book_one_row_each_in_the_same_cell() -> None:
    """§6.2 的"至出一条柱级 + 至多两条字级"：干级与支级各收成一条，两回事不合并。

    乾 庚子 × 坤 乙丑：日干庚乙五合（+10）、日管子丑六合（+8）→ 格内两条命中都被收编，
    对称族从 9 条降到 7 条。
    """
    pair = _pair_of(FEMALE_DAY_MERGE)
    assert palace_keys(pair) == ["hh.palace.stem_merge", "hh.palace.branch_merge"]
    assert [(r.rule, r.label, r.delta) for r in palace_rows(pair)] == [
        ("hh.palace.stem_merge", "日干五合", 10.0),
        ("hh.palace.branch_merge", "日支相合", 8.0),
    ]
    assert len(cross_relations(pair)) == 9
    assert len(relation_rows(pair)) == 7


def test_two_same_branches_harmonise_even_when_the_cell_has_no_relation_hit() -> None:
    """支级第三档：日支同字 → `branch_harmony`。

    乾 子 × 坤 壬子 那一格**一条关系都没有**（§2.9 实测：`kinds_in_cell=[]`），
    而比和仍然成立 —— 所以婚姻宫族不能只从对称族的命中里推。
    """
    pair = _pair_of(FEMALE_AUSPICIOUS)
    assert palace_keys(pair) == ["hh.palace.branch_harmony"]
    hits = cross_relations(pair)
    assert hits[0].kind == "地支六合"  # 该格之外的账照旧
    assert len([h for h in hits if (h.male_position, h.female_position) == ("day", "day")]) == 0


def test_a_cell_without_any_bond_books_no_palace_row() -> None:
    """三对走查/构造命例给不出婚姻宫：那一格无干合、无支级关系、两支也不同字。"""
    for female in (FEMALE_SAME, FEMALE_COMPLEMENT, FEMALE_HOSTILE):
        assert palace_keys(_pair_of(female)) == []


def test_a_day_stem_clash_has_no_palace_key_so_it_stays_in_the_symmetric_family() -> None:
    """§6.2 那条"婚姻宫族只立五合不立冲"的落点：一格有命中，婚姻宫却空手，账本要读得出为什么。

    `FEMALE_STEM_CLASH`（乾 庚子 × 坤 甲戌）那一格只有天干相冲一条 —— 干级只认五合，支级
    既无关系也不同字，所以三道归属全不触发。这一条于是以格位的名字留在对称族：矩阵那一格
    照旧显示它，账本里也只有这一处提到它，`-6` 只加一次。
    """
    pair = _pair_of(FEMALE_STEM_CLASH)
    assert palace_keys(pair) == []
    assert palace_rows(pair) == []
    assert [
        (row.rule, row.label, row.delta)
        for row in relation_rows(pair)
        if row.label.endswith("（乾日×坤日）")
    ] == [("hh.relation.stem_clash", "两造干冲（乾日×坤日）", -6.0)]
    day_cell = next(
        cell
        for cell in pair_matrix(pair)
        if (cell.male_position, cell.female_position) == ("day", "day")
    )
    assert [(hit.kind, hit.male_character, hit.female_character) for hit in day_cell.hits] == [
        ("天干相冲", "庚", "甲")
    ]


def test_the_five_nayin_relations_each_pick_their_own_key() -> None:
    """§7.2 的 5×5 通行说：主语固定为乾，一对纳音只出一个关系、只入一行账。

    五枚命例恰好把五个键走全（乾年命一律 大林木·木）：坤 土→我克、金→克我、
    火→我生、木→比和、水→生我。分值 −6…+6 与 §6.1 的年命族预算同一条尺。
    """
    five_nayin_cases = (
        FEMALE_SAME,
        FEMALE_COMPLEMENT,
        FEMALE_AUSPICIOUS,
        FEMALE_HOSTILE,
        FEMALE_DAY_MERGE,
    )
    assert [
        (nayin_relation(_pair_of(f)), nayin_key(_pair_of(f)), nayin_row(_pair_of(f)).delta)
        for f in five_nayin_cases
    ] == [
        ("我克", "hh.nayin.wo_ke", 2.0),
        ("克我", "hh.nayin.ke_wo", -6.0),
        ("我生", "hh.nayin.wo_sheng", -4.0),
        ("比和", "hh.nayin.bi_he", 4.0),
        ("生我", "hh.nayin.sheng_wo", 6.0),
    ]
    assert nayin_row(_pair_of(FEMALE_DAY_MERGE)).label == "生我（乾木·坤水）"


def test_the_names_the_ledger_suffixes_use_are_the_ones_the_charts_carry() -> None:
    """`PILLAR_NAME` 与 `HEHUN_PALACE_KEYS` 都是第二处写法，这里逐字对回唯一真值来源。

    柱名对回本命盘的 `BaziPillar.label`（去掉"柱"字即两字简称），婚姻宫五键对回 Task 1
    的键表 —— 归属分支里的字符串若是打错了，`hehun_rule()` 也会在第一次取行时就炸，
    但那一句炸不到"键存在却用错了地方"，所以这里连用在哪一格都钉住。
    """
    assert {position: PILLAR_NAME[position] + "柱" for position in POSITION_ORDER} == {
        pillar.position: pillar.label for pillar in MALE.pillars
    }
    assert set(palace_keys(_pair_of(FEMALE_DAY_MERGE))) <= set(HEHUN_PALACE_KEYS)
    assert {
        PALACE_STEM_MERGE,
        PALACE_BRANCH_MERGE,
        PALACE_BRANCH_CLASH,
        PALACE_BRANCH_HARMONY,
        PALACE_PILLAR_REVERSE,
    } == set(HEHUN_PALACE_KEYS)


def test_a_pillar_level_seal_never_vanishes_a_group_row() -> None:
    """§6.2 与成局族的交接：成局族那一行要**有人接了**才交得出去。

    `FEMALE_DAY_FUYIN_GROUP`（乾 庚子 × 坤 庚子）实测：日柱伏吟 → 归属直接收在柱级那一条，
    支级根本不出现；而 乾 辰子 + 坤 申子 拼成的申子辰三合跨住两造日支，`group_is_a_palace_fact`
    为真。若 `group_rows` 只看这一条就丢行，这 +8 于是两头都不记 —— 而 §6.2 说的是
    "一条事实只记一次"，从不是"一次都不记"。（三会水 不在 `PALACE_GROUP_KINDS` 里：
    §6.1 的 `branch_merge` 只收六合/三合/半合。）
    """
    pair = _pair_of(FEMALE_DAY_FUYIN_GROUP)
    assert [g.kind for g in cross_groups(pair) if group_is_a_palace_fact(g)] == ["三合"]
    assert palace_keys(pair) == [PALACE_PILLAR_REVERSE]
    assert [(r.rule, r.label, r.delta) for r in palace_rows(pair)] == [
        ("hh.palace.pillar_reverse", "日柱伏反吟", -8.0)
    ]
    assert [(r.rule, r.label, r.delta) for r in group_rows(pair)] == [
        ("hh.group.three_harmony", "跨造三合（水）", 8.0),
        ("hh.group.three_meeting", "跨造三会（水）", 6.0),
    ]


# §2.9 的七枚构造命例与 §2.7 的两对走查命例都在这一张表里：(名, 坤造, 行数, 总分, 档位)
# 行数是账本**贡献行**的条数（不含 `build_ledger` 那条基准行）；九枚全都不触 0/100 截断。
# Task 3 追加的第八枚 `FEMALE_DAY_FUYIN_GROUP` 不在表内：它是 §6.2 成局族交接的判据例
# （§10.4 最后一条），断的是"柱级封口不吞成局族的行"，不是某一档可达。
MEASURED_LEDGERS: list[tuple[str, BaziChart, int, float, str]] = [
    ("全吉对", FEMALE_AUSPICIOUS, 19, 94.0, "天作之合"),
    ("干支双收对", FEMALE_DAY_MERGE, 13, 74.0, "相得益彰"),
    ("婚姻宫由三合撑起对", FEMALE_GROUP_MERGE, 16, 71.0, "相得益彰"),
    ("日干冲无宫可对对", FEMALE_STEM_CLASH, 11, 64.0, "中和可处"),
    ("互补对", FEMALE_COMPLEMENT, 17, 38.0, "欠和宜慎"),
    ("欠和对", FEMALE_HOSTILE, 20, 37.0, "欠和宜慎"),
    ("日支战对", FEMALE_DAY_CLASH, 20, 14.0, "欠和宜慎"),
    ("日柱反吟对", FEMALE_DAY_REVERSE, 17, 9.0, "欠和宜慎"),
    ("同频对", FEMALE_SAME, 20, 0.0, "欠和宜慎"),
]


def test_every_measured_pair_lands_where_the_design_said() -> None:
    """§10.5 可达性：四档各有实测命例，且**不触截断**。

    行数与总分一起断言，是因为只断总分看不出"少记一行被另一行补回来了"这种巧合。
    「中和可处」那一枚停在 64.0 —— 离 65 那道界只有一分，正是把 `>=` 断在错的一侧时
    会立刻变红的那一类数（§10.5 只强制要求 ≥80 与 <45 两端可达，中间两档是本轮加严）。
    """
    for name, female, rows, total, tier in MEASURED_LEDGERS:
        ledger = hehun_ledger(hehun_rows(_pair_of(female)))
        assert (name, len(ledger.factors) - 1, ledger.value, ledger.tier) == (name, rows, total, tier)


def test_the_ledger_is_self_explaining_and_starts_with_the_base() -> None:
    """§10.5 末条 + §6.3 第 3 条：`value == Σ factors[].delta`，每一行的出处都带模型参数那一句。

    九枚命例里最低 0.0、最高 94.0，都在 [0, 100] 之内，所以没有一枚会多出
    `score.clamped` 那一行 —— 上一测的 `len(factors) - 1 == 行数` 已经把这条钉住了。
    """
    rows = hehun_rows(_pair_of(FEMALE_DAY_CLASH))
    ledger = hehun_ledger(rows)
    assert ledger.factors[0].rule == "hehun.base"
    assert ledger.factors[0].label == "基准分"
    assert ledger.factors[0].delta == HEHUN_BASE
    assert ledger.value == pytest.approx(sum(factor.delta for factor in ledger.factors))
    # 基准行的 source 是 `build_ledger` 打的 `MODEL_PARAM_SOURCE` 原句（§6.3 第 3 条点名 `HEHUN_BASE`
    # 的出处就是那一句；岁运 golden 测 `test_bazi_transit_golden.py:195` 钉的是同一行为），贡献行才写合婚自己的口径。
    assert {factor.source for factor in ledger.factors[1:]} == {HEHUN_RULE_SOURCE}
    assert ledger.factors[0].source == MODEL_PARAM_SOURCE
    assert MODEL_PARAM_SOURCE in HEHUN_RULE_SOURCE


def test_the_day_merge_ledger_reads_family_by_family() -> None:
    """整份账本逐字对拍（13 行 74.0），族序即 `HEHUN_FAMILIES`：对称→成局→互济→年命→婚姻宫。

    这枚命例是五族里四族的同屏样本（成局族为空，两道判据都滤尽了），
    也是"一格出两行字级"的那一枚：干级 +10、支级 +8，格内那两条命中在对称族里消失。
    """
    assert [
        (row.family, row.rule, row.direction, row.label, row.delta)
        for row in hehun_rows(_pair_of(FEMALE_DAY_MERGE))
    ] == [
        ("relation", "hh.relation.branch_break", "mutual", "两造支破（乾年×坤日）", -3.0),
        ("relation", "hh.relation.stem_merge", "mutual", "两造干合（乾年×坤时）", 8.0),
        ("relation", "hh.relation.stem_merge", "mutual", "两造干合（乾月×坤月）", 8.0),
        ("relation", "hh.relation.branch_merge", "mutual", "两造支合（乾月×坤月）", 8.0),
        ("relation", "hh.relation.branch_harm", "mutual", "两造支害（乾日×坤时）", -5.0),
        ("relation", "hh.relation.self_punishment", "mutual", "两造自刑（乾时×坤月）", -4.0),
        ("relation", "hh.relation.stem_clash", "mutual", "两造干冲（乾时×坤时）", -6.0),
        ("yongshen", "hh.yongshen.supply", "male_to_female", "我喜彼旺（乾视坤·土旺）", 6.0),
        ("yongshen", "hh.yongshen.shortfall", "male_to_female", "我喜彼弱（乾视坤·金弱）", -5.0),
        ("yongshen", "hh.yongshen.clash", "male_to_female", "我忌彼旺（乾视坤·水旺）", -7.0),
        ("nayin", "hh.nayin.sheng_wo", "mutual", "生我（乾木·坤水）", 6.0),
        ("palace", "hh.palace.stem_merge", "mutual", "日干五合", 10.0),
        ("palace", "hh.palace.branch_merge", "mutual", "日支相合", 8.0),
    ]


def test_the_vigor_ruler_is_set_against_the_chart_s_own_mean() -> None:
    """§2.6：尺是**该造自己的五行均值**，不是原始分值，也不是对方的盘。

    乾 实测比值 木1.3924 火0.8228 土1.0759 金0.6329 水1.0759 —— 离 1.25/0.75 两道界
    都有距离，所以五个标签都断得出口（取四位前后是同一个读数，§2.6）。
    """
    assert element_vigor(MALE) == {"木": "旺", "火": "平", "土": "平", "金": "弱", "水": "平"}


def test_the_four_quadrants_and_both_views_all_book_in_one_pair() -> None:
    """§10.4：同频对恰好把补/阙/冲/安四格与两个视角一次给全（实测六行）。

    「安」= 乾视坤·木弱（坤 木比值 0.1948，离两道界都远）。§10.4 原本担心只有这一枚
    非走查命例给得出安格，实测在四位读数下走查那对也给得出一条（§2.6、§2.7），两对互为备份。
    """
    assert [
        (row.rule, row.direction, row.label, row.delta) for row in yongshen_rows(_pair_of(FEMALE_SAME))
    ] == [
        ("hh.yongshen.shortfall", "male_to_female", "我喜彼弱（乾视坤·土弱）", -5.0),
        ("hh.yongshen.supply", "male_to_female", "我喜彼旺（乾视坤·金旺）", 6.0),
        ("hh.yongshen.harmless", "male_to_female", "我忌彼弱（乾视坤·木弱）", 3.0),
        ("hh.yongshen.clash", "male_to_female", "我忌彼旺（乾视坤·水旺）", -7.0),
        ("hh.yongshen.shortfall", "female_to_male", "我喜彼弱（坤视乾·金弱）", -5.0),
        ("hh.yongshen.clash", "female_to_male", "我忌彼旺（坤视乾·木旺）", -7.0),
    ]


def test_the_same_element_books_two_rows_that_say_two_different_things() -> None:
    """§6.2 的双向裁定：同一个「金」在两个视角上方向相反，两行说的是两种气，不是双计。

    乾 喜金而 坤 金旺（比值 1.4935 → 补），坤 喜金而 乾 金弱（0.6329 → 阙）；
    两条不同的补救路径，各记一行。
    """
    rows = [row for row in yongshen_rows(_pair_of(FEMALE_SAME)) if "金" in row.label]
    assert [(row.direction, row.label, row.delta) for row in rows] == [
        ("male_to_female", "我喜彼旺（乾视坤·金旺）", 6.0),
        ("female_to_male", "我喜彼弱（坤视乾·金弱）", -5.0),
    ]


def test_an_element_in_the_flat_zone_books_nothing() -> None:
    """§7.1 诚实性约束的因：落在"平"区的五行既不入象限也不入账本。

    互补对里 乾忌火 而 坤 火比值 1.0625（离 1.25 与 0.75 两道界都有距离）—— 乾忌三条
    候选里唯一落空的就是它，木 0.75 与 水 1.4375 都各自成了象限（§2.6 的四位读数）。
    """
    rows = yongshen_rows(_pair_of(FEMALE_COMPLEMENT))
    assert not [row for row in rows if "火" in row.label]
    assert [row.label for row in rows] == [
        "我喜彼旺（乾视坤·土旺）",
        "我喜彼弱（乾视坤·金弱）",
        "我忌彼弱（乾视坤·木弱）",
        "我忌彼旺（乾视坤·水旺）",
        "我喜彼弱（坤视乾·金弱）",
        "我忌彼旺（坤视乾·木旺）",
    ]


def test_a_chart_without_a_list_of_its_own_books_only_one_view() -> None:
    """一造的喜忌集为空时那一向就是零行（§5.2 的 `null` 只出现在结构性之处）。

    坤 1989-04-04 的 `favorable_elements` 与 `unfavorable_elements` 实测都是空表
    （§2.9 命例之一），所以整对只有 乾视坤 的四行 —— 四行都在，只是反过来的那一向没有。
    """
    rows = yongshen_rows(_pair_of(FEMALE_DAY_REVERSE))
    assert {row.direction for row in rows} == {"male_to_female"}
    assert [(row.label, row.delta) for row in rows] == [
        ("我喜彼弱（乾视坤·金弱）", -5.0),
        ("我忌彼旺（乾视坤·木旺）", -7.0),
        ("我忌彼弱（乾视坤·水弱）", 3.0),
        ("我忌彼旺（乾视坤·火旺）", -7.0),
    ]


def test_the_four_bands_are_cut_where_the_design_said() -> None:
    """§6.4：四档是本系统命名；中间两道分界直接引 `bazi_strength` 的两条常量。

    80 是本轮唯一新增的分界（决策 5）。边界取"压线值 + 一角钱"两两一对，
    断的是 `>=` 而不是 `>`，档位是整数分的函数，与 §2.6 那条比值纪律无关。
    """
    assert hehun_tier(80.0) == "天作之合"
    assert hehun_tier(79.9) == "相得益彰"
    assert hehun_tier(65.0) == "相得益彰"
    assert hehun_tier(64.9) == "中和可处"
    assert hehun_tier(45.0) == "中和可处"
    assert hehun_tier(44.9) == "欠和宜慎"


def test_every_ledger_row_has_a_mirrored_fired_entry() -> None:
    """§10.6 第二条：账本与判语不分家 —— 一行账配一句判语，逐行对齐。

    镜像的断法是按序逐条对，不是按 `rule` 集合对：同一个键可以在一份账本里出现三次
    （三条六冲），集合会把这个巧合抹平，而读者在页面上是按行读的。
    """
    rows = hehun_rows(_pair_of(FEMALE_SAME))
    fired = hehun_fired(rows)
    assert len(fired) == len(rows)
    for row, entry in zip(rows, fired, strict=True):
        assert (entry.rule, entry.label, entry.family, entry.direction, entry.delta) == (
            row.rule,
            row.label,
            row.family,
            row.direction,
            row.delta,
        )
        assert entry.reading == HEHUN_RULES[row.rule].reading
    assert {entry.family for entry in fired} <= set(HEHUN_FAMILIES)


def test_the_complement_figure_books_nothing_the_ledger_did_not() -> None:
    """§7.1 诚实性约束 / §10.6 互补条：图上的每一个五行都在账上有同名的一行。

    正反两个方向、**逐视角**一起断：`该视角四格的元素数 == 该 direction 的行数` 钉住
    "打过分的行一个都不少、也没有串到对方的视角里去"（全局求和做不到这一点 ——
    两格互换内容时总数照旧）；`cell.rule in booked`（只对**非空**格）钉住"没打过的分画不出来"。
    空格不参与第二条 —— 一造没有那条喜忌集时那一格本就没有账。
    最后一断钉的是"图上写的视角短名与账本短名里那一处是同一个字"：两处若走岔，
    用户在「乾视坤」那张图上读到的就不是账上标着乾视坤的那几行。
    """
    for female in (FEMALE_SAME, FEMALE_COMPLEMENT, FEMALE_DAY_MERGE, FEMALE_DAY_REVERSE):
        pair = _pair_of(female)
        figure = complement(pair)
        rows = yongshen_rows(pair)
        booked = {factor.rule for factor in hehun_ledger(hehun_rows(pair)).factors}
        assert [(view.viewer, view.label) for view in figure.views] == [
            (view.viewer, view.label) for view in YONGSHEN_VIEWS
        ]
        for view, yongshen_view in zip(figure.views, YONGSHEN_VIEWS, strict=True):
            own = [row for row in rows if row.direction == yongshen_view.direction]
            assert sum(len(cell.elements) for cell in view.cells) == len(own)
            assert all(yongshen_view.label in row.label for row in own)
        cells = [cell for view in figure.views for cell in view.cells if cell.elements]
        assert {cell.rule for cell in cells} <= booked


def test_the_figure_always_has_two_views_of_four_quadrants() -> None:
    """§10.6 呈现完整性：2 视角 × 4 象限恒在，空格是 `elements: []` 而不是缺格。

    互补对特意挑进来：它的四格里 乾视坤 那一张是满的（土补 / 金阙 / 水冲 / 木安），
    坤视乾 那一张的「补」与「安」两格是空的（乾的土、水、火三行在"平"区，§2.6 的四位读数）——
    同一次走查里两种状态都看得见，页面上空格要渲染成"无"，所以契约里它们必须存在。
    """
    figure = complement(_pair_of(FEMALE_COMPLEMENT))
    assert [(v.viewer, v.label) for v in figure.views] == [("male", "乾视坤"), ("female", "坤视乾")]
    for view in figure.views:
        assert [(c.name, c.mine, c.theirs, c.delta) for c in view.cells] == [
            ("补", "favorable", "旺", 6.0),
            ("阙", "favorable", "弱", -5.0),
            ("冲", "unfavorable", "旺", -7.0),
            ("安", "unfavorable", "弱", 3.0),
        ]
    assert [[len(c.elements) for c in view.cells] for view in figure.views] == [
        [1, 1, 1, 1],
        [0, 1, 1, 0],
    ]


def test_the_measured_quadrant_contents_are_the_rulers_own_readings() -> None:
    """同频对的八格里落账者，逐字来自 §2.6 那把尺（比值取四位）。

    乾视坤：坤 土 0.4545 → 阙、坤 金 1.4935 → 补、坤 木 0.1948 → 安、坤 水 1.6883 → 冲；
    坤视乾：乾 金 0.6329 → 阙、乾 木 1.3924 → 冲。格内的序是**观看方**喜忌集的序。
    """
    figure = complement(_pair_of(FEMALE_SAME))
    assert [
        (cell.name, [(e.element, e.ratio) for e in cell.elements]) for cell in figure.views[0].cells
    ] == [
        ("补", [("金", 1.4935)]),
        ("阙", [("土", 0.4545)]),
        ("冲", [("水", 1.6883)]),
        ("安", [("木", 0.1948)]),
    ]
    assert [
        (cell.name, [(e.element, e.ratio) for e in cell.elements]) for cell in figure.views[1].cells
    ] == [("补", []), ("阙", [("金", 0.6329)]), ("冲", [("木", 1.3924)]), ("安", [])]


def test_the_five_nayin_relations_each_compose_their_own_sentence() -> None:
    """§7.2 的固定句式：｛乾年命、坤年命｝，｛三字生克句｝为｛关系｝；｛该键自己的断语｝＋尾注。

    五枚命例的坤造年柱恰好覆盖五个关系（庚午 路旁土我克 / 乙丑 海中金克我 /
    乙亥 山头火我生 / 己巳 大林木比和 / 丙子 涧下水生我），所以这一段同时是
    `nayin_phrase` 的四分支与"不共用同一句"的证明。主语固定为乾（§6.2）。
    """
    females = (
        FEMALE_SAME,
        FEMALE_COMPLEMENT,
        FEMALE_AUSPICIOUS,
        FEMALE_HOSTILE,
        FEMALE_DAY_MERGE,
    )
    assert [
        (view.relation, view.reading)
        for view in (nayin_view(_pair_of(female)) for female in females)
    ] == [
        (
            "我克",
            "乾年命大林木、坤年命路旁土，木克土为我克；我去克彼，我居其长，凡事宜主不宜客。"
            + HEHUN_NAYIN_NOTE,
        ),
        (
            "克我",
            "乾年命大林木、坤年命海中金，金克木为克我；彼来克我，我居其短，凡事宜和不宜争。"
            + HEHUN_NAYIN_NOTE,
        ),
        (
            "我生",
            "乾年命大林木、坤年命山头火，木生火为我生；我去生彼，泄我之气，凡事宜守不宜耗。"
            + HEHUN_NAYIN_NOTE,
        ),
        (
            "比和",
            "乾年命大林木、坤年命大林木，木与木同气为比和；两家同气，其情相安，无高低之辨。"
            + HEHUN_NAYIN_NOTE,
        ),
        (
            "生我",
            "乾年命大林木、坤年命涧下水，水生木为生我；彼之来生我，其气长养，凡事宜受、宜进、宜生。"
            + HEHUN_NAYIN_NOTE,
        ),
    ]


def test_the_imagery_text_is_the_corpus_verbatim_not_a_rephrasing() -> None:
    """§7.2 末条：`imagery` 与 `source` 逐字取自 `NayinCorpus`，本页不重述《三命通会》。

    比对现成语料而不是抄一遍长句 —— 与 `tests/test_bazi_schema.py` 里
    `test_ten_god_readings_are_corpus_lookup_not_invention` 同一手法：抄进断言的原文
    会在语料订正那天变成一条假的红线。
    """
    view = nayin_view(_pair_of(FEMALE_SAME))
    assert (view.male.ganzhi, view.male.nayin, view.male.element) == ("戊辰", "大林木", "木")
    assert (view.female.ganzhi, view.female.nayin, view.female.element) == ("庚午", "路旁土", "土")
    for side, ganzhi in ((view.male, "戊辰"), (view.female, "庚午")):
        corpus = nayin_meaning(ganzhi)
        assert (side.imagery, side.source) == (corpus.imagery, corpus.source)
    assert (view.rule, view.delta) == ("hh.nayin.wo_ke", 2.0)
    assert view.phrase == "木克土"


def test_the_quadrant_table_is_the_only_source_of_both_views() -> None:
    """四象限表一处定义同时供给账本键与图的格名 —— 改一处不会漏另一处。

    `平` 不在表的横轴里，于是 `YONGSHEN_QUADRANT[(True, "平")]` 必然 KeyError：
    §7.1 那句"平既不入象限也不入账本"是数据结构本身给的，不是判断里写死的。
    最后一条要和**总装配**对拍，不能与 `yongshen_rows` 对拍 —— 后者就是前者的投影，
    两边比字面相等是同义反复。`hehun_rows` 走的是另一条路（五族按 `HEHUN_FAMILIES` 装配），
    所以"总装改序 / 总装另起一处互济族判定"都会让它变红，而这一断仍是真的。反过来，
    `yongshen_facts` 内部改序杀不掉它 —— 投影 `yongshen_rows` 走的是同一张事实表，两边一起变；
    那一层的顺序本就没有唯一的正确排法，多出来的象限/元素归属由
    `test_the_complement_figure_books_nothing_the_ledger_did_not` 收住。
    """
    assert [rule for rule, _n, _m, _t in YONGSHEN_QUADRANTS] == [
        "hh.yongshen.supply",
        "hh.yongshen.shortfall",
        "hh.yongshen.clash",
        "hh.yongshen.harmless",
    ]
    families = {rule: hehun_rule(rule).family for rule, *_ in YONGSHEN_QUADRANTS}
    assert families == dict.fromkeys(families, "yongshen")
    assert YONGSHEN_QUADRANT[(True, "旺")] == "hh.yongshen.supply"
    assert YONGSHEN_QUADRANT[(False, "弱")] == "hh.yongshen.harmless"
    assert (True, "平") not in YONGSHEN_QUADRANT
    pair = _pair_of(FEMALE_COMPLEMENT)
    assert [fact.row.label for fact in yongshen_facts(pair)] == [
        row.label for row in hehun_rows(pair) if row.family == "yongshen"
    ]


def test_the_family_order_is_pinned_on_a_fixture_whose_group_slot_is_not_empty() -> None:
    """Task 4 评审留下的那个空槽位盲区：装配序要钉在**成局族非空**的那一枚上。

    `hehun_rows` 的 docstring 许诺"序即 `HEHUN_FAMILIES`"，而 Task 4 的逐字样本
    （`FEMALE_DAY_MERGE`，13 行）成局族恰是空的 —— 于是把 `*group_rows(pair)` 在 relation
    与 palace 之间任意挪位，那一测照样绿。这一枚有两行成局账，挪位即红。
    条数与相邻关系用字面量钉（16 行 = 10+2+2+1+1），族序与常量的相等关系另断一条：
    前者防装配序被动，后者防 `HEHUN_FAMILIES` 自己改序。
    """
    rows = hehun_rows(_pair_of(FEMALE_DAY_FUYIN_GROUP))
    assert [row.family for row in rows] == [
        *["relation"] * 10,
        *["group"] * 2,
        *["yongshen"] * 2,
        "nayin",
        "palace",
    ]
    assert list(dict.fromkeys(row.family for row in rows)) == list(HEHUN_FAMILIES)


# 轴吃的是**档案**（经线与历法各造一份决定），不是盘：与 §5.1 的入参同一形状。
MALE_PROFILE = _profile(1988, 2, 15, 23, 30, "成都")
SAME_PROFILE = _profile(1990, 6, 15, 10, 0, "北京")
COMPLEMENT_PROFILE = _profile(1985, 7, 22, 14, 30, "上海")
AUSPICIOUS_PROFILE = _profile(1995, 9, 18, 18, 0, "北京")


def _axis(start: int, years: int, chart: BaziChart, profile: HehunProfile) -> HehunAxis:
    return hehun_axis(
        _pair_of(chart),
        partner_annual_luck(MALE_PROFILE, Gender.MALE),
        partner_annual_luck(profile, Gender.FEMALE),
        start_year=start,
        years=years,
    )


def test_an_axis_row_is_the_same_year_as_the_transit_table() -> None:
    """§10.5 同尺：轴上乾造那五格的分与档，与 `/bazi/liuyue` 同年表逐格相等。

    这一测**不重算**，而是回头调岁运引擎自己那份装配 —— "同一年在两个端点上分数不同"
    是本切片最贵的一种错，因为它会让用户在岁运页看到 61 分、在合婚轴上看到 58 分。
    """
    transit = compute_transit(
        birth_date=date(1988, 2, 15),
        birth_time=time(23, 30),
        gender=Gender.MALE,
        longitude=resolve_longitude("成都", None),
        start_year=2024,
        end_year=2028,
        reference_date=date(2026, 9, 22),
    )
    axis = _axis(2024, 5, FEMALE_SAME, SAME_PROFILE)
    assert [(row.year, row.male.value, row.male.tier) for row in axis.rows] == [
        (year.year, year.score.value, year.score.tier) for year in transit.years
    ]


def test_the_axis_is_one_row_per_year_with_a_gap_and_no_reading() -> None:
    """§7.3 的轴行形状：干支、两造各一分一档一运、差、档 —— 九枚实测值逐字对拍。

    流年干支两造的表必须给同一个字（`LiuNian` 以立春为界，与命盘无关），
    所以这里同时断两造的表一致，而不是只取乾那一份就算完。
    轴行不带 `reading`（"简表不带判语"，§5.2 继承切片 3）。
    """
    axis = _axis(2024, 5, FEMALE_SAME, SAME_PROFILE)
    assert (axis.start_year, axis.end_year) == (2024, 2028)
    assert [row.ganzhi for row in axis.rows] == ["甲辰", "乙巳", "丙午", "丁未", "戊申"]
    male_luck = partner_annual_luck(MALE_PROFILE, Gender.MALE)
    female_luck = partner_annual_luck(SAME_PROFILE, Gender.FEMALE)
    assert [(male_luck[y].ganzhi, female_luck[y].ganzhi) for y in range(2024, 2029)] == [
        ("甲辰", "甲辰"),
        ("乙巳", "乙巳"),
        ("丙午", "丙午"),
        ("丁未", "丁未"),
        ("戊申", "戊申"),
    ]
    assert [
        (
            row.year,
            row.male.value,
            row.male.tier,
            row.female.value,
            row.female.tier,
            row.gap,
            row.sync,
        )
        for row in axis.rows
    ] == [
        (2024, 33.0, "滞", 42.0, "滞", 9.0, "半同步"),
        (2025, 27.0, "滞", 0.0, "滞", 27.0, "背离"),
        (2026, 29.0, "滞", 32.0, "滞", 3.0, "同频"),
        (2027, 61.0, "平", 50.0, "平", 11.0, "半同步"),
        (2028, 56.0, "平", 66.0, "顺", 10.0, "半同步"),
    ]
    assert [(row.male.dayun, row.male.dayun_start_age) for row in axis.rows] == [
        ("戊午", 37)
    ] * 5
    assert [(row.female.dayun, row.female.dayun_start_age) for row in axis.rows] == [
        ("戊寅", 34)
    ] * 5
    assert all("reading" not in row.model_dump() for row in axis.rows)


def test_the_three_sync_bands_are_cut_at_eight_and_twenty() -> None:
    """§7.3 的三档分界：gap ≤8 同频、≤20 半同步、>20 背离（边界压线值各一枚）。

    1993 年那一格是真命例（乾 54.0 平 vs 坤 62.0 平，gap 恰为 8.0），
    所以 `<=` 与 `<` 之差在这里不是假设，是页面上已经存在的一行。
    """
    assert (HEHUN_SYNC_CLOSE, HEHUN_SYNC_WIDE) == (8.0, 20.0)
    assert axis_sync(8.0) == "同频"
    assert axis_sync(8.1) == "半同步"
    assert axis_sync(20.0) == "半同步"
    assert axis_sync(20.1) == "背离"
    child = _axis(1990, 5, FEMALE_SAME, SAME_PROFILE)
    assert [row.gap for row in child.rows] == [7.0, 7.0, 10.0, 8.0, 19.0]
    assert [row.sync for row in child.rows] == ["同频", "同频", "半同步", "同频", "半同步"]


def test_a_child_limit_year_names_no_luck_pillar() -> None:
    """起运前那一年没有运可论：`dayun` 为 None，分与档照给（§7.3）。

    乾 1990—1993 四年在童限段（`DayunStep` index 0，起 1 岁），坤只有 1990—1992 三年 ——
    两造的童限长度本来就不同，所以这一段同时是"轴不因一方无运而少给一年"的证据。
    """
    child = _axis(1990, 5, FEMALE_SAME, SAME_PROFILE)
    assert [row.male.dayun for row in child.rows] == [None, None, None, None, "乙卯"]
    assert [row.female.dayun for row in child.rows] == [None, None, None, "辛巳", "辛巳"]
    assert [row.male.dayun_start_age for row in child.rows] == [1, 1, 1, 1, 7]
    assert [(row.year, row.ganzhi) for row in child.rows][:3] == [
        (1990, "庚午"),
        (1991, "辛未"),
        (1992, "壬申"),
    ]


def test_segments_split_where_either_side_changes_pillar() -> None:
    """§7.3 段边界：两造换运之年并起来切轴，21 年轴切出五段，标签只写事实本身。

    标签里的岁数区间是 `DayunStep.start_age—end_age`（虚岁，库给什么写什么），
    破折号用「—」与 `bazi_transit` 的年份区间同一个字。`第 N 运` 的 N 即 `DayunStep.index`，
    0 段不成句、改标「童限」（见上一测的 1990—1993 段）。
    """
    pair = _pair_of(FEMALE_SAME)
    male_luck, female_luck = partner_annual_luck(MALE_PROFILE, Gender.MALE), partner_annual_luck(
        SAME_PROFILE, Gender.FEMALE
    )
    spans = axis_segments(pair, male_luck, female_luck, start_year=2024, years=21)
    assert [(s.start_year, s.end_year, s.label) for s in spans] == [
        (2024, 2032, "乾·第 4 运 戊午（37—46 岁）／坤·第 4 运 戊寅（34—43 岁）"),
        (2033, 2033, "乾·第 4 运 戊午（37—46 岁）／坤·第 5 运 丁丑（44—53 岁）"),
        (2034, 2042, "乾·第 5 运 己未（47—56 岁）／坤·第 5 运 丁丑（44—53 岁）"),
        (2043, 2043, "乾·第 5 运 己未（47—56 岁）／坤·第 6 运 丙子（54—63 岁）"),
        (2044, 2044, "乾·第 6 运 庚申（57—66 岁）／坤·第 6 运 丙子（54—63 岁）"),
    ]
    child = axis_segments(pair, male_luck, female_luck, start_year=1990, years=5)
    assert [s.label for s in child] == [
        "乾·童限（1—6 岁）／坤·童限（1—3 岁）",
        "乾·童限（1—6 岁）／坤·第 1 运 辛巳（4—13 岁）",
        "乾·第 1 运 乙卯（7—16 岁）／坤·第 1 运 辛巳（4—13 岁）",
    ]


def test_segments_cover_the_axis_exactly_once() -> None:
    """段是轴的一个划分：首段起于轴首、末段终于轴末、相邻段首尾相接、总长等于年数。

    短轴（2024—2028）只有一段，那正是设计稿"一整条时间轴一张卡"的退化情形；
    不验这一条的话，"边界在窗口外"这一类错位要到浏览器走查才看得见。

    上面那三条是顺轴走一遍的构造性质，回归了也测不出来；守得住 §7.3 的是最后那一条 ——
    段首年恰等于两造 `DayunStep.start_year` 落在窗内的并集（去重、升序）。并集里再并入窗口
    起年不是遮丑：轴可以从一步大运的中间开始（Task 9 让用户自选 `axis_start`），那时首段就是
    那一步的尾巴 —— 后两个窗口（2025—2028、2026—2034）正是这一形，其窗口起年落在两造任何
    `start_year` 之外，不并它这条等式在中途起轴上就配不上"恰等于"。
    """
    pair = _pair_of(FEMALE_SAME)
    male_luck, female_luck = partner_annual_luck(MALE_PROFILE, Gender.MALE), partner_annual_luck(
        SAME_PROFILE, Gender.FEMALE
    )
    for start, years in ((2024, 5), (2024, 21), (1990, 5), (2025, 4), (2026, 9)):
        spans = axis_segments(pair, male_luck, female_luck, start_year=start, years=years)
        assert (spans[0].start_year, spans[-1].end_year) == (start, start + years - 1)
        assert sum(span.end_year - span.start_year + 1 for span in spans) == years
        assert all(a.end_year + 1 == b.start_year for a, b in zip(spans, spans[1:], strict=False))
        boundaries = sorted(
            {
                step.start_year
                for chart in (pair.male, pair.female)
                for step in chart.dayun
                if start <= step.start_year <= start + years - 1
            }
            | {start}
        )
        assert [span.start_year for span in spans] == boundaries
    assert [
        s.label for s in axis_segments(pair, male_luck, female_luck, start_year=2024, years=5)
    ] == ["乾·第 4 运 戊午（37—46 岁）／坤·第 4 运 戊寅（34—43 岁）"]


def test_the_window_is_the_overlap_of_two_luck_spans() -> None:
    """可推窗：起于各造自己摊出来的第一年，止于两造共同的末年（§9.3 的输入）。

    `min(luck)` 就是出生年（乾 1988 / 坤 1990、1985、1995），这不是假设而是实测：
    库把起运前的童年段也排在 `getDaYun()` 第 0 项里，摊平之后首年即出生年。
    终点取**较小**的那个末年 —— 轴不能画进任何一方已经没有盘的地方。
    """
    male_luck = partner_annual_luck(MALE_PROFILE, Gender.MALE)
    for profile, female_from, supported_to in (
        (SAME_PROFILE, 1990, 2082),
        (COMPLEMENT_PROFILE, 1985, 2080),
        (AUSPICIOUS_PROFILE, 1995, 2083),
    ):
        window = axis_window(male_luck, partner_annual_luck(profile, Gender.FEMALE))
        assert window == HehunAxisWindow(
            male_from=1988, female_from=female_from, supported_to=supported_to
        )


def test_the_six_groups_are_always_six_in_the_reading_order() -> None:
    """§7.4 的阅读序：同宜→乾独宜→坤独宜→同忌→乾独忌→坤独忌，恒六组。

    空组照样给（`items: []`）—— 设计稿的宜忌板是六格版面，缺格与"无"是两件事（§10.6）。
    """
    groups = yi_ji(_pair_of(FEMALE_SAME)).groups
    assert [group.kind for group in groups] == ["同宜", "乾独宜", "坤独宜", "同忌", "乾独忌", "坤独忌"]
    assert [group.items for group in groups][1] == []
    assert all(len(group.items) == 0 or all(i.element for i in group.items) for group in groups)


def test_the_complementary_pair_splits_the_five_elements_as_measured() -> None:
    """互补对（坤 喜水金 / 忌土火木）的六组，逐字对拍。

    乾 喜土金、忌木水火，所以交集只有金；水既是坤之喜又是乾之忌，
    土既是乾之喜又是坤之忌 —— 这正是"互补"两个字在数据上的形状。
    """
    assert [
        (group.kind, [item.element for item in group.items])
        for group in yi_ji(_pair_of(FEMALE_COMPLEMENT)).groups
    ] == [
        ("同宜", ["金"]),
        ("乾独宜", ["土"]),
        ("坤独宜", ["水"]),
        ("同忌", ["木", "火"]),
        ("乾独忌", ["水"]),
        ("坤独忌", ["土"]),
    ]


def test_a_partner_without_useful_god_lists_only_the_other_side() -> None:
    """坤（1996-11-24）实测喜忌集两空：三组空、乾侧三组满。

    这不是假设出来的边界，是 §2.9 已经命中的那一枚构造命例。喜忌在盘内本来就允许为空
    （`/natal` 的既有事实），宜忌板因此必须能把"空"画出来而不是整块消失。
    """
    assert [
        (group.kind, [item.element for item in group.items])
        for group in yi_ji(_pair_of(FEMALE_DAY_MERGE)).groups
    ] == [
        ("同宜", []),
        ("乾独宜", ["土", "金"]),
        ("坤独宜", []),
        ("同忌", []),
        ("乾独忌", ["木", "水", "火"]),
        ("坤独忌", []),
    ]


def test_the_attributions_are_the_common_table_and_the_declaration_is_verbatim() -> None:
    """§7.4 的两条硬约束：通说配属取自一张表，声明句逐字回显（前端不补算也不改写）。"""
    assert ELEMENT_ATTRIBUTIONS == {
        "木": ("东", "青", "春"),
        "火": ("南", "赤", "夏"),
        "土": ("中", "黄", "四季"),
        "金": ("西", "白", "秋"),
        "水": ("北", "黑", "冬"),
    }
    figure = yi_ji(_pair_of(FEMALE_COMPLEMENT))
    assert figure.declaration == HEHUN_YIJI_DECLARATION
    assert HEHUN_YIJI_DECLARATION == (
        "宜忌取自两造用神法（喜用五行的通说配属），非玄空坐向，不含住宅方位与化解物品。"
    )
    assert [(i.element, i.direction, i.color, i.season) for i in figure.groups[0].items] == [
        ("金", "西", "白", "秋")
    ]
    assert all(i.element in ELEMENT_ATTRIBUTIONS for g in figure.groups for i in g.items)


def test_one_element_can_be_one_sides_taboo_and_the_others_favor() -> None:
    """「水」在互补对里同时出现在坤独宜与乾独忌 —— 宜忌板不是同一句话讲两遍。

    这一条顺带钉住一个实现陷阱：六组必须由**各自的**喜忌集算，
    不能图省事用一张"共用差集表"。同频对里两造喜忌同集，六个组就有三个空着，
    那同样是实测（同宜 土金、同忌 木水火，三个独集全空）。
    """
    groups = {
        group.kind: [item.element for item in group.items]
        for group in yi_ji(_pair_of(FEMALE_COMPLEMENT)).groups
    }
    assert groups["坤独宜"] == ["水"] and groups["乾独忌"] == ["水"]
    same = {
        group.kind: [item.element for item in group.items]
        for group in yi_ji(_pair_of(FEMALE_SAME)).groups
    }
    assert same == {
        "同宜": ["土", "金"],
        "乾独宜": [],
        "坤独宜": [],
        "同忌": ["木", "水", "火"],
        "乾独忌": [],
        "坤独忌": [],
    }


def test_the_axis_default_starts_at_the_later_birth_year_or_today_whichever_is_later() -> None:
    """§9.3 末条：缺省轴起点 = `max(较晚出生年, reference_date 所在年)`（实测两值两形）。

    2026 年参考 → 取参考年（两人都已出生）；1989 年参考 → 取坤的出生年 1990，
    因为那一年乾 1 岁、坤还没出生，轴若从 1989 起就有一格没有盘。
    """
    window = axis_window(
        partner_annual_luck(MALE_PROFILE, Gender.MALE),
        partner_annual_luck(SAME_PROFILE, Gender.FEMALE),
    )
    assert window == HehunAxisWindow(male_from=1988, female_from=1990, supported_to=2082)
    assert resolve_hehun_axis_range(
        start_year=None, years=21, reference_year=2026, window=window
    ) == HehunAxisRange(start_year=2026, end_year=2046)
    assert resolve_hehun_axis_range(
        start_year=None, years=5, reference_year=1989, window=window
    ) == HehunAxisRange(start_year=1990, end_year=1994)


def test_an_axis_before_the_later_birth_year_is_a_domain_error() -> None:
    """§9.3 触发一：轴起早于较晚一造的出生年。五项 context 齐给，前端一句提示改得动表单。

    `requested_to` 是补齐轴长之后的末年（1989 + 21 - 1），不是请求里的数 ——
    用户填的是起点与长度，页面要说的是"你这段轴实际会画到哪儿"。
    """
    with pytest.raises(TransitRangeError) as raised:
        compute_hehun(
            male=MALE_PROFILE,
            female=SAME_PROFILE,
            reference_date=date(2026, 9, 22),
            axis_start_year=1989,
            axis_years=21,
        )
    error = raised.value
    assert (error.code, error.status_code) == ("hehun_axis_out_of_range", 422)
    assert error.context == {
        "requested_from": 1989,
        "requested_to": 2009,
        "male_available_from": 1988,
        "female_available_from": 1990,
        "supported_to": 2082,
    }


def test_an_axis_past_the_shared_end_uses_the_same_code_but_says_another_thing() -> None:
    """§9.3 触发二：轴末超出两造共同可推的末年。同码、同五项 context，但 message 说另一头。

    两造末年不同（乾 2083 / 坤 2082），所以 2080+5-1=2084 只越了坤那一头 ——
    越界的是共同末年而不是谁的末年，`supported_to` 给的就是这一个数。
    """
    with pytest.raises(TransitRangeError) as raised:
        compute_hehun(
            male=MALE_PROFILE,
            female=SAME_PROFILE,
            reference_date=date(2026, 9, 22),
            axis_start_year=2080,
            axis_years=5,
        )
    assert raised.value.code == "hehun_axis_out_of_range"
    assert raised.value.context["supported_to"] == 2082
    assert raised.value.context["requested_to"] == 2084
    assert "2082" in raised.value.message


def test_a_partner_profile_is_a_summary_not_a_second_natal_chart() -> None:
    """§5.2：精简档案 = 四柱（干支/本柱十神/纳音）+ 生肖 + 日主 + 喜忌 + 五行分布 + 大运步表。

    神煞、格局、六维详批、藏干账本**一概不在**这里 —— 双人页不重演一个人的本命盘，
    也不给同一份结论造第二个呈现口径。键名因此可以整表断言：这份档案的形状是契约，
    不是实现细节，多一个字段就是多一处要前端确认的口径。
    """
    partner = partner_profile(MALE, "male")
    assert set(partner.model_dump()) == {
        "side",
        "name",
        "four_pillars",
        "zodiac",
        "day_master",
        "day_master_element",
        "favorable_elements",
        "unfavorable_elements",
        "elements",
        "pillars",
        "dayun",
        "true_solar_time",
        "tst_applied",
    }
    assert (partner.four_pillars, partner.zodiac, partner.day_master) == ("戊辰 甲寅 庚子 丁亥", "龙", "庚")
    assert partner.day_master_element == "金"
    assert (partner.favorable_elements, partner.unfavorable_elements) == (
        ["土", "金"],
        ["木", "水", "火"],
    )
    assert [(p.position, p.ganzhi, p.shishen_gan, p.nayin) for p in partner.pillars] == [
        ("year", "戊辰", "偏印", "大林木"),
        ("month", "甲寅", "偏财", "大溪水"),
        ("day", "庚子", "日主", "壁上土"),
        ("hour", "丁亥", "正官", "屋上土"),
    ]
    assert [(e.element, e.score) for e in partner.elements] == [
        ("木", 2.2),
        ("火", 1.3),
        ("土", 1.7),
        ("金", 1.0),
        ("水", 1.7),
    ]
    assert len(partner.dayun) == len(MALE.dayun) == 10 and partner.dayun[4].ganzhi == "戊午"
    assert (partner.tst_applied, partner.true_solar_time) == (True, "1988-02-15 22:12")


def test_the_result_is_the_ten_sections_the_contract_promised() -> None:
    """§5.2 的十个段一段不缺，且互相自洽：矩阵 16 格、fired 与账本同长、轴长等于请求年数。"""
    result = compute_hehun(
        male=MALE_PROFILE, female=SAME_PROFILE, reference_date=date(2026, 9, 22), axis_years=5
    )
    assert set(result.model_dump()) == {
        "male",
        "female",
        "score",
        "matrix",
        "fired",
        "complement",
        "nayin",
        "axis",
        "yi_ji",
        "provenance",
    }
    assert (result.male.side, result.female.side) == ("male", "female")
    assert (result.female.four_pillars, result.female.zodiac) == ("庚午 壬午 辛亥 癸巳", "马")
    assert len(result.matrix) == 16 and len(result.fired) == len(result.score.factors) - 1
    assert (result.score.value, result.score.tier) == (0.0, "欠和宜慎")
    assert (result.axis.start_year, result.axis.end_year, len(result.axis.rows)) == (2026, 2030, 5)
    assert result.nayin.relation == "我克"
    assert result.model_validate_json(result.model_dump_json()).model_dump() == result.model_dump()


def test_the_provenance_lists_only_the_tables_this_page_reads() -> None:
    """溯源纪律：一张表也没引的不能列，引了十张的不能只列三张。

    与 `NAME_CONTENT_SOURCES` 同一条理由（`content/__init__.py:37`）：把 `bazi_dimensions`
    （六维详批）列进来就是让合婚声称引了它没引的书 —— 本页既没呈现也没用它计分。
    反过来 `bazi_wangshuai` / `bazi_geju` / `bazi_tiaohou` 看着像"本命盘的事"，
    其实两造的喜忌集正是由它们合并出来的（互补图与宜忌的唯一输入），一张都删不得。
    """
    result = compute_hehun(
        male=MALE_PROFILE, female=SAME_PROFILE, reference_date=date(2026, 9, 22), axis_years=1
    )
    provenance = result.provenance
    assert [table.name for table in provenance.tables] == [
        "bazi_shishen",
        "bazi_nayin",
        "bazi_wangshuai",
        "bazi_geju",
        "bazi_tiaohou",
        "bazi_shensha",
        "bazi_relations",
        "bazi_changsheng",
        "bazi_transit_rules",
        "bazi_hehun_rules",
    ]
    assert {table.version for table in provenance.tables} == {CONTENT_VERSION}
    assert (provenance.reference_date, provenance.engine) == ("2026-09-22", "lunar-python")
    assert provenance.rule_count == len(HEHUN_RULES) == 29
    assert provenance.method == HEHUN_MODEL_SOURCE


def test_the_axis_length_default_has_exactly_one_home() -> None:
    """21 这个数只在契约上出现一次：引擎的 `axis_years` 没有缺省，路由必须显式给。

    两处各写一份迟早分家（前端读的是契约）。这一测是那条纪律的可执行版本：
    少给 `axis_years` 就是 `TypeError`，而不是"悄悄用了引擎里那份缺省"。
    要带 `match` 是因为不指定缺的是哪一项时这条测就退了色 —— 少给 `male` 同样抛
    `TypeError`，那证明的是"参数没给全"而不是"轴长没有缺省"。所以整条消息逐字给全：
    断的是"`axis_years` 是唯一缺的那一项"。
    """
    with pytest.raises(TypeError, match="missing 1 required keyword-only argument: 'axis_years'"):
        compute_hehun(male=MALE_PROFILE, female=SAME_PROFILE)  # type: ignore[call-arg]
    assert BaziHehunRequest(male=MALE_PROFILE, female=SAME_PROFILE).axis_years == 21
