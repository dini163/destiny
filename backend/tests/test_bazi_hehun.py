"""合婚引擎（spec §10.1–10.6）。

夹具一律**用真实生辰走 `compute_bazi_chart`**：全仓 0 处手搓 `BaziPillar` 列表
（§2.7），本轮不破例。§2.7 的两对走查命例与 §2.9 的七枚构造命例在此一次立齐，
后面每个任务都只往这个文件追加测。
"""

from datetime import date, time

import pytest

from app.core.errors import InvalidBirthDataError
from app.engines.bazi import compute_bazi_chart
from app.engines.bazi_hehun import (
    POSITION_ORDER,
    HehunChartPair,
    compute_partner_charts,
    cross_relations,
    pair_matrix,
    relation_rows,
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
