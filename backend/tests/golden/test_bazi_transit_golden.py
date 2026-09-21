"""岁运的 golden：基准命 A 的 2024–2028 逐年逐行，加 2026 的十二节气月（spec §9.2）。

每个期望值都是"手算一遍再看实算"的产物，且两处口径已在计划里钉死：地支基准取**日
干**的十二长生（`content/bazi_changsheng`，与 lunar-python 120 格对拍），运岁生克只以
**干**论（`engines/bazi_transit._gan_element`）。键序就是账本序 —— 它与
`TRANSIT_RULES` 的表序同源，换了序这里就红，而不是前端默默换个说法。

柱本身（干支、虚岁、所属大运段）来自 lunar-python 的 `getDaYun()[i].getLiuNian()`，
月柱来自 `LiuNian.getLiuYue()`，所以历法漂移在这一份 golden 里藏不住；分值全为本系统
模型参数，引文只到判语里。十二段只手算正月一行：月段的账与年段走的是同一张 46 条表，
其余十一行的价值在"逐字钉住不许漂"，把它们全手算一遍只是把同一次核对做十二遍。
"""

from datetime import date, time
from functools import cache

import pytest

from app.content.bazi_transit_rules import TRANSIT_RULE_SOURCE
from app.engines.bazi import compute_bazi_chart
from app.engines.bazi_transit import (
    _AnnualLuck,
    _Natal,
    _annual_luck_by_year,
    _natal_projection,
    _transit_year,
    resolve_natal_moment,
)
from app.schemas.bazi_transit import TransitMonth, TransitYear
from app.schemas.common import CalendarType, Gender
from app.schemas.scoring import MODEL_PARAM_SOURCE

_BIRTH = dict(
    birth_date=date(1988, 2, 15),
    birth_time=time(23, 30),
    calendar=CalendarType.SOLAR,
    longitude=104.1,
    gender=Gender.MALE,
    apply_true_solar_time=True,
)

#: 手算依据见计划"手算依据"一节；每行的键序 == `TRANSIT_RULES` 表序里被命中的那些。
YEARS: dict[int, dict[str, object]] = {
    2024: {
        "ganzhi": "甲辰",
        "keys": [
            "transit.base",
            "yongshen.gan_unfavourable",  # 甲=木 ∈ 忌
            "yongshen.zhi_favourable",  # 辰本气戊=土 ∈ 喜
            "taisui.value",  # 辰辰，本命年支
            "taisui.punish",  # 辰辰自刑
            "heyue.anhe_unfavourable",  # 申子辰半合水（辰+子），水 ∈ 忌
            "ganzhi.chong_day_master",  # 甲庚相冲
            "dishi.supportive",  # 辰为庚之养
        ],
        "value": 33.0,
        "tier": "滞",
    },
    2025: {
        "ganzhi": "乙巳",
        "keys": [
            "transit.base",
            "yongshen.gan_unfavourable",  # 乙=木 ∈ 忌
            "yongshen.zhi_unfavourable",  # 巳本气丙=火 ∈ 忌
            "palace.punish_month",  # 寅巳无恩之刑
            "palace.harm_month",  # 寅巳六害
            "ganzhi.combine_day_master",  # 乙庚合
            "dishi.supportive",  # 巳为庚之长生
            "shensha.jiesha",  # 申子辰劫煞在巳
        ],
        "value": 27.0,
        "tier": "滞",
        # 巳又冲时支亥：palace 族只论提纲与日支两宫，时宫之冲不在定价范围内
    },
    2026: {
        "ganzhi": "丙午",
        "keys": [
            "transit.base",
            "yongshen.gan_unfavourable",  # 丙=火 ∈ 忌
            "yongshen.zhi_unfavourable",  # 午本气丁=火 ∈ 忌
            "palace.chong_day",  # 子午冲日支
            "heyue.anhe_unfavourable",  # 寅午半合火（含旺支午）
            "dayun.sui_sheng_yun",  # 丙火生戊午之戊土
            "shensha.yuede",  # 寅月月德在丙
        ],
        "value": 29.0,
        "tier": "滞",
        # 午为庚之沐浴：三档皆不入，故无地势行（沐浴一书两说，spec §6.2）
    },
    2027: {
        "ganzhi": "丁未",
        "keys": [
            "transit.base",
            "yongshen.gan_unfavourable",  # 丁=火 ∈ 忌
            "yongshen.zhi_favourable",  # 未本气己=土 ∈ 喜
            "palace.harm_day",  # 子未六害
            "dayun.sui_sheng_yun",  # 丁火生戊土
            "dishi.supportive",  # 未为庚之冠带
            "shensha.tianyi",  # 庚日夜贵人在丑未
            "shensha.tiande",  # 寅月天德在丁
        ],
        "value": 61.0,
        "tier": "平",
    },
    2028: {
        "ganzhi": "戊申",
        "keys": [
            "transit.base",
            "yongshen.gan_favourable",  # 戊=土 ∈ 喜
            "yongshen.zhi_favourable",  # 申本气庚=金 ∈ 喜
            "palace.chong_month",  # 寅申冲提纲
            "palace.punish_month",  # 寅巳申三刑见寅申
            "heyue.sanhe_unfavourable",  # 申子辰三合水局，水 ∈ 忌
            # 戊与运干戊同为土，不生也不克 → 大运生克两行俱不记
            "dishi.prosperous",  # 申为庚之临官（建禄同此）
            # 申害时支亥：与 2025 同理，时宫之害不在 palace 族四宫之内
        ],
        "value": 56.0,
        "tier": "平",
    },
}


#: 摊平一次大运要走完十个流年段，比整张命盘还贵；本文件全程只读，故就地缓存。
@cache
def _fixture() -> tuple[_Natal, dict[int, _AnnualLuck]]:
    """命 A 的命局投影与摊平好的十年大运 —— 年表与月表共用的那一份输入。"""
    chart = compute_bazi_chart(**_BIRTH)
    moment = resolve_natal_moment(
        birth_date=_BIRTH["birth_date"],
        birth_time=_BIRTH["birth_time"],
        calendar=CalendarType.SOLAR,
        longitude=104.1,
        apply_true_solar_time=True,
    )
    return _natal_projection(chart), _annual_luck_by_year(moment.eight_char, Gender.MALE)


@cache
def _years() -> dict[int, TransitYear]:
    natal, luck = _fixture()
    return {year: _transit_year(natal, luck[year]) for year in YEARS}


#: 2026（丙午）十二段：干支由五虎遁定（丙辛之年以庚寅起首），交节日为 §2.1 探针实测。
#: 正月一行另见手算测；余下十一行的账本走的是同一张 46 条表，钉的是"不许默默漂移"。
MONTHS_2026: list[tuple[str, str, str]] = [
    ("庚寅", "2026-02-04", "2026-03-04"),  # 立春 → 惊蛰前一日
    ("辛卯", "2026-03-05", "2026-04-04"),
    ("壬辰", "2026-04-05", "2026-05-04"),
    ("癸巳", "2026-05-05", "2026-06-04"),
    ("甲午", "2026-06-05", "2026-07-06"),
    ("乙未", "2026-07-07", "2026-08-06"),
    ("丙申", "2026-08-07", "2026-09-06"),
    ("丁酉", "2026-09-07", "2026-10-07"),
    ("戊戌", "2026-10-08", "2026-11-06"),
    ("己亥", "2026-11-07", "2026-12-06"),
    ("庚子", "2026-12-07", "2027-01-04"),
    ("辛丑", "2027-01-05", "2027-02-03"),  # 小寒 → 次年立春前一日
]


@cache
def _months() -> list[TransitMonth]:
    """聚焦年的十二段，走 `_transit_year(focus=True)` —— 与端点发出的那一份同一条路。"""
    natal, luck = _fixture()
    focused = _transit_year(natal, luck[2026], focus=True)
    assert focused.months is not None
    return focused.months


def test_the_baseline_years_all_sit_inside_the_wu_wu_luck_pillar() -> None:
    """golden 的地基：五年俱在戊午运（2024–2033）内。运段一漂，大运族五行全体改账。"""
    transit = _years()[2026]
    assert transit.pillar.ganzhi == "丙午"
    assert (transit.dayun_index, transit.dayun_ganzhi) == (4, "戊午")
    assert all(t.dayun_ganzhi == "戊午" for t in _years().values())


@pytest.mark.parametrize("year", sorted(YEARS))
def test_each_year_hits_exactly_the_transcribed_rules_in_ledger_order(year: int) -> None:
    expected = YEARS[year]
    transit = _years()[year]
    assert transit.pillar.ganzhi == expected["ganzhi"]
    assert [factor.rule for factor in transit.score.factors] == expected["keys"]
    assert transit.score.value == pytest.approx(expected["value"])
    assert transit.score.tier == expected["tier"]


def test_the_ledgers_are_arithmetic_and_each_row_carries_its_own_source() -> None:
    """每一行账都能自己核对：Σ delta == value；基准行是本系统加权，命中行引岁运规则表。"""
    for transit in _years().values():
        factors = transit.score.factors
        assert sum(factor.delta for factor in factors) == pytest.approx(transit.score.value)
        assert factors[0].source == MODEL_PARAM_SOURCE
        assert all(factor.source == TRANSIT_RULE_SOURCE for factor in factors[1:])


def test_the_five_years_do_not_all_land_in_one_band() -> None:
    """反向确实存在：三滞两平。判定层若整族失配，五年会齐刷刷落在同一档里。"""
    assert [t.score.tier for t in _years().values()] == ["滞", "滞", "滞", "平", "平"]


def test_the_2026_twelve_months_carry_the_probed_ganzhi_and_jieqi_spans() -> None:
    """十二段的历法事实：干支（五虎遁）与起止日（交节）逐字对拍 §2.1 探针。

    分值不在这里对拍 —— 它由月柱命中什么决定，手算一段（下一条）比抄十二行更有牙。
    """
    assert [(m.ganzhi, m.start_solar, m.end_solar) for m in _months()] == MONTHS_2026


def test_the_first_month_of_2026_is_derivable_by_hand() -> None:
    """庚寅月：庚=金 ∈ 喜 +10、寅本气甲=木 ∈ 忌 −8、庚绝于寅 −6、太极贵人在寅 +3。

    月段净 −1 分，接在 29.0 的丙午年段之后 → 28.0 滞。年段那七行不是这里的内容，逐行
    引自同一份 `YEARS[2026]`；月段四行的次序就是 `TRANSIT_RULES` 的表序，一行不多。
    """
    month = _months()[0]
    rows = [factor.rule for factor in month.score.factors]
    year_rows = YEARS[2026]["keys"]
    assert rows[: len(year_rows)] == year_rows
    assert rows[len(year_rows) :] == [
        "yue.yongshen.gan_favourable",
        "yue.yongshen.zhi_unfavourable",
        "yue.dishi.decaying",
        "yue.shensha.taiji",
    ]
    assert (month.score.value, month.score.tier) == (28.0, "滞")
