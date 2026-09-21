"""合成柱与 `_build_pillar` 的逐字段对拍 + 十神 100 格对拍（spec §9.1）。"""

from datetime import date, time
from typing import Sequence

import pytest
from lunar_python import Solar
from lunar_python.util import LunarUtil

from app.content.wuxing import GAN_ELEMENT, ZHI_ELEMENT
from app.engines.bazi import compute_bazi_chart
from app.engines.bazi_pillar import GAN_ORDER, build_transit_pillar

#: 6 张命盘含阳日主/阴日主、魁罡、纯阴纯阳、跨旬，覆盖柱位组合。
_SWEEP_BIRTHS = [
    (date(1988, 2, 15), time(23, 30), 104.1),
    (date(1990, 1, 8), time(12, 0), 116.4),
    (date(1993, 11, 8), time(9, 15), 116.4),
    (date(1975, 6, 20), time(3, 40), 121.5),
    (date(2001, 3, 12), time(18, 5), 113.3),
    (date(1964, 10, 26), time(7, 55), 106.6),
]
#: 日柱不在内：命盘把日干自身的十神记作 `日主`，那是本命柱专属称谓，岁运柱永远
#: 不是日主。日柱的等价性由 `test_day_pillar_differs_only_in_the_day_master_label` 钉住。
_COMPARED_POSITIONS = (("year", "年柱"), ("month", "月柱"), ("hour", "时柱"))


@pytest.mark.parametrize(("d", "t", "lng"), _SWEEP_BIRTHS)
def test_synthetic_pillar_equals_the_natal_one_field_by_field(
    d: date, t: time, lng: float
) -> None:
    """同一天干支、同一日主，两条路径必须产出逐字段相等的柱（spec §5 的等价承诺）。"""
    chart = compute_bazi_chart(
        birth_date=d, birth_time=t, longitude=lng, gender="MALE", apply_true_solar_time=True
    )
    by_position = {p.position: p for p in chart.pillars}
    for position, label in _COMPARED_POSITIONS:
        natal = by_position[position]
        made = build_transit_pillar(
            natal.ganzhi, position=position, label=label, day_master=chart.day_master
        )
        assert made.model_dump() == natal.model_dump(), f"{d} {position} 柱漂移"


@pytest.mark.parametrize(("d", "t", "lng"), _SWEEP_BIRTHS)
def test_day_pillar_differs_only_in_the_day_master_label(d: date, t: time, lng: float) -> None:
    """日柱只允许 `shishen_gan` 一格不同：命盘记 日主，合成柱按十神表记 比肩。"""
    chart = compute_bazi_chart(
        birth_date=d, birth_time=t, longitude=lng, gender="MALE", apply_true_solar_time=True
    )
    natal = next(p for p in chart.pillars if p.position == "day")
    made = build_transit_pillar(
        natal.ganzhi, position="day", label="日柱", day_master=chart.day_master
    )
    differs = {
        name
        for name in type(natal).model_fields
        if getattr(made, name) != getattr(natal, name)
    }
    assert differs == {"shishen_gan"}
    assert (natal.shishen_gan, made.shishen_gan) == ("日主", "比肩")


@pytest.mark.parametrize(
    ("ganzhi", "match"),
    [
        ("庚", "非法干支"),
        ("庚子丑", "非法干支"),
        ("xx", "非法干支"),
        ("庚yy", "非法干支"),
    ],
)
def test_rejects_a_ganzhi_outside_the_tables(ganzhi: str, match: str) -> None:
    with pytest.raises(ValueError, match=match):
        build_transit_pillar(ganzhi, position="transit_year", label="流年", day_master="庚")


def test_rejects_an_unknown_day_master() -> None:
    with pytest.raises(ValueError, match="非法日主"):
        build_transit_pillar("庚子", position="transit_year", label="流年", day_master="xx")


def test_shishen_zhi_follows_the_hidden_stems() -> None:
    """藏干十神照 `LunarUtil.ZHI_HIDE_GAN` + `SHI_SHEN` 现算，本模块不另立表。"""
    made = build_transit_pillar("甲辰", position="transit_year", label="流年", day_master="庚")
    hidden: Sequence[str] = LunarUtil.ZHI_HIDE_GAN["辰"]
    assert made.hidden_stems == list(hidden)
    assert made.shishen_zhi == [LunarUtil.SHI_SHEN["庚" + stem] for stem in hidden]
    assert made.shishen_zhi == ["偏印", "正财", "伤官"]


def test_content_element_tables_equal_lunar_python() -> None:
    """合成柱用 `app.content` 的五行表、命盘用 lunar-python 的：两套必须逐字相等。"""
    assert {gan: GAN_ELEMENT[gan] for gan in GAN_ORDER} == dict(LunarUtil.WU_XING_GAN)
    assert ZHI_ELEMENT == dict(LunarUtil.WU_XING_ZHI)


def _ten_god_sweep() -> dict[tuple[str, str], tuple[str, str]]:
    """60 个流年干支 × 10 个日干：(日干, 年干) -> (该流年整柱, 命盘给出的年干十神)。

    键只取天干：十神由（日干、该干）二元决定，年支不参与，所以 600 个探针压成 100
    格。少一格即扫描没铺满，对拍会假绿，故先断言键集；整柱留在值里喂给合成柱，
    因为不在六十甲子内的干支（如 乙子）本就排不出来。
    """
    out: dict[tuple[str, str], tuple[str, str]] = {}
    for solar_year in range(1984, 2046):  # 一个甲子，遍历全部 60 个年干支
        for day in range(10, 20):  # 同月内连续十日 ⇒ 十个不同日干
            ec = Solar.fromYmd(solar_year, 3, day).getLunar().getEightChar()
            out[(ec.getDayGan(), ec.getYearGan())] = (ec.getYear(), ec.getYearShiShenGan())
    return out


def test_sweep_covers_all_100_ten_god_cells() -> None:
    assert set(_ten_god_sweep()) == {(g, z) for g in GAN_ORDER for z in GAN_ORDER}


def test_synthetic_ten_god_matches_lunar_python_on_every_cell() -> None:
    for (day_gan, year_gan), (year_ganzhi, expected) in _ten_god_sweep().items():
        made = build_transit_pillar(
            year_ganzhi, position="transit_year", label="流年", day_master=day_gan
        )
        assert made.shishen_gan == expected, f"{day_gan}日主 见年干 {year_gan}"
