"""合婚引擎（spec §10.1–10.6）。

夹具一律**用真实生辰走 `compute_bazi_chart`**：全仓 0 处手搓 `BaziPillar` 列表
（§2.7），本轮不破例。§2.7 的两对走查命例与 §2.9 的七枚构造命例、§6.2 的交接命例在此一次立齐，
后面每个任务都只往这个文件追加测。
"""

from datetime import date, time

import pytest

from app.content.bazi_hehun_rules import HEHUN_PALACE_KEYS
from app.core.errors import InvalidBirthDataError
from app.engines.bazi import compute_bazi_chart
from app.engines.bazi_hehun import (
    PALACE_BRANCH_CLASH,
    PALACE_BRANCH_HARMONY,
    PALACE_BRANCH_MERGE,
    PALACE_PILLAR_REVERSE,
    PALACE_STEM_MERGE,
    PILLAR_NAME,
    POSITION_ORDER,
    GroupMember,
    HehunChartPair,
    compute_partner_charts,
    cross_groups,
    cross_relations,
    group_bonds_both_day_pillars,
    group_is_a_palace_fact,
    group_is_new_between_charts,
    group_rows,
    group_spans_both_charts,
    nayin_key,
    nayin_relation,
    nayin_row,
    pair_matrix,
    palace_keys,
    palace_rows,
    relation_rows,
    scanned_groups,
)
from app.engines.bazi_rules import derive_relations
from app.schemas.bazi import BaziChart
from app.schemas.bazi_hehun import HehunProfile
from app.schemas.common import Gender
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
    assert any(row.label.endswith("（乾日×坤月）") for row in relation_rows(pair))


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
