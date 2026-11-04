"""Golden tests for the 梅花易数 (Plum Blossom Numerology) derivation engine.

十五张锚卦全部**手推**复核过（算式就地写在 docstring 里），依据邵雍《梅花易数》的
先天八卦数 1乾 2兑 3离 4震 5巽 6坎 7艮 8坤、报数/年月日时起卦（÷8 定上下卦、÷6 定动爻，
**余数为零即作除数本身**）、互体（二三四爻为下互、三四五爻为上互）、变卦（动爻阴阳互变）、
体用（无动爻之卦为体、有动爻之卦为用）与卦气旺衰（月建当令五行定旺相休囚死）。
主锚 `[7,3]` 之外，另挑十四张压住参考盘压不到的路：三数法、单数法（须加时辰序）、
余数为零（`[16,8]` 上卦 16÷8 余 0 → 作 8 坤；24÷6 余 0 → 作 6 动爻）、动爻在下（`[5,2]` 初爻）
与在上、五种卦气状态（旺相休囚死各至少一张）、立春与春节之间的日子（年支取农历年、月令取
节气月）、闰月（月数取同号）、体用五关系各自成段，以及时辰敏感的两张（戌时/辰时）——
参考时刻是巳时（时辰序 6），上卦和与下卦和 mod 6 同余，只有换成序 11 与序 5 才压得住
「动爻由下卦和（含时辰）定，不由上卦和定」。

账本（``score_factors``）里的**整数是本系统口径**，不是古法：古典可复推的是关系分类（生体/克体/
比和/泄/耗）与其符号，以及「用生体＞比和＞体克用＞体生用＞用克体」的吉凶次序；权重与
50±Σ 的印刷形状是系统设计。故这里钉的是「算式自洽 + 次序不翻 + 每格与钉住的口径一致」，
`tests/content/test_meihua_corpus.py` 另钉表体本身。互卦一本账的 ±6 夹界由 `[8,9,10]`（raw −7）
与 `报数[8]·单数法辰时`（raw −7）压住；变卦一本账的夹界在古典权重表（±4/±3/−5）下不可达，
故无锚可压，也刻意不为此造合成盘。
"""

from datetime import datetime
from typing import NamedTuple

import pytest
from fastapi.testclient import TestClient
from lunar_python import Solar

from app.content import CONTENT_VERSION
from app.content.meihua_plain import wangshuai_key
from app.core.errors import InvalidCastInputError
from app.engines.meihua import MEIHUA_STARS, _verdict_band, cast_meihua
from app.engines.plain_corpora import PLAIN_CORPORA, MEIHUA

CAST = datetime(2024, 5, 15, 10, 30)
XU_CAST = datetime(2024, 5, 15, 20, 30)     # 同一日的戌时（时辰序 11）
CHEN_CAST = datetime(2024, 5, 15, 7, 30)     # 同一日的辰时（时辰序 5）
LICHUN_CAST = datetime(2023, 2, 4, 9, 15)   # 农历癸卯年正月十四巳时：春节（01-22）后、立春（10:42）前
LEAP_CAST = datetime(2023, 4, 1, 10, 30)    # 农历癸卯年闰二月十一巳时


class Case(NamedTuple):
    """One hand-derived 梅花 cast. 每格来自手推表（依据见模块 docstring），非引擎抄录。"""

    id: str
    method: str
    numbers: tuple[int, ...] | None
    cast: datetime
    upper: int                     # 先天卦数 1-8
    lower: int
    moving: int                    # 1-6，自下数
    ben_number: int                # 文王序
    ben_name: str                  # 卦名（如「贲」）
    ben_full: str                  # 上下卦合成的全名
    ben_lines: tuple[int, ...]     # 自下而上
    hu_number: int
    hu_full: str
    bian_number: int
    bian_full: str
    ti_name: str
    ti_element: str
    ti_position: str
    ti_state: str
    yong_name: str
    yong_element: str
    yong_position: str
    yong_state: str
    relation: str                  # 机器键
    relation_zh: str
    tiyong_verdict: str
    grade: int
    month_zhi: str                 # 月建（节气界）
    season: str
    commanding: str                # 当令五行
    deltas: tuple[int, int, int, int]
    score: int
    band: str


CASES = (
    Case("报数[7,3]·体生用", "number", (7, 3), CAST, 7, 3, 4,
         22, "贲", "山火贲", (1, 0, 1, 0, 0, 1), 40, "雷水解", 30, "离为火",
         "离", "火", "lower", "旺", "艮", "土", "upper", "相",
         "ti_sheng_yong", "体生用", "小凶", -1, "巳", "孟夏", "火", (-8, 8, -1, 3), 52, "中平"),
    Case("报数[8,9,10]·三数法", "number", (8, 9, 10), CAST, 8, 1, 3,
         11, "泰", "地天泰", (1, 1, 1, 0, 0, 0), 54, "雷泽归妹", 19, "地泽临",
         "坤", "土", "upper", "相", "乾", "金", "lower", "死",
         "ti_sheng_yong", "体生用", "小凶", -1, "巳", "孟夏", "火", (-8, 5, -6, -2), 39, "小凶"),
    Case("报数[8]·单数法", "number", (8,), CAST, 8, 6, 2,
         7, "师", "地水师", (0, 1, 0, 0, 0, 0), 24, "地雷复", 2, "坤为地",
         "坤", "土", "upper", "相", "坎", "水", "lower", "囚",
         "ti_ke_yong", "体克用", "小吉", 1, "巳", "孟夏", "火", (18, 5, -2, 3), 74, "吉"),
    Case("报数[8]·单数法辰时", "number", (8,), CHEN_CAST, 8, 5, 1,
         46, "升", "地风升", (0, 1, 1, 0, 0, 0), 54, "雷泽归妹", 11, "地天泰",
         "坤", "土", "upper", "相", "巽", "木", "lower", "休",
         "yong_ke_ti", "用克体", "大凶", -2, "巳", "孟夏", "火", (-26, 5, -6, -2), 21, "凶"),
    Case("报数[5,2]·用克体", "number", (5, 2), CAST, 5, 2, 1,
         61, "中孚", "风泽中孚", (1, 1, 0, 0, 1, 1), 27, "山雷颐", 59, "风水涣",
         "巽", "木", "upper", "休", "兑", "金", "lower", "死",
         "yong_ke_ti", "用克体", "大凶", -2, "巳", "孟夏", "火", (-26, 0, 2, 4), 30, "小凶"),
    Case("报数[4,1]·体死", "number", (4, 1), CAST, 4, 1, 5,
         34, "大壮", "雷天大壮", (1, 1, 1, 1, 0, 0), 43, "泽天夬", 43, "泽天夬",
         "乾", "金", "lower", "死", "震", "木", "upper", "休",
         "ti_ke_yong", "体克用", "小吉", 1, "巳", "孟夏", "火", (18, -8, 6, 3), 69, "小吉"),
    Case("报数[6,3]·体囚", "number", (6, 3), CAST, 6, 3, 3,
         63, "既济", "水火既济", (1, 0, 1, 0, 1, 0), 64, "火水未济", 3, "水雷屯",
         "坎", "水", "upper", "囚", "离", "火", "lower", "旺",
         "ti_ke_yong", "体克用", "小吉", 1, "巳", "孟夏", "火", (18, -5, 2, -2), 63, "小吉"),
    Case("报数[16,8]·余数为零", "number", (16, 8), CAST, 8, 8, 6,
         2, "坤", "坤为地", (0, 0, 0, 0, 0, 0), 2, "坤为地", 23, "山地剥",
         "坤", "土", "lower", "相", "坤", "土", "upper", "相",
         "bi_he", "体用比和", "吉", 1, "巳", "孟夏", "火", (28, 5, 6, 3), 92, "上吉"),
    Case("报数[3,3]·比和而旺", "number", (3, 3), CAST, 3, 3, 6,
         30, "离", "离为火", (1, 0, 1, 1, 0, 1), 28, "泽风大过", 55, "雷火丰",
         "离", "火", "lower", "旺", "离", "火", "upper", "旺",
         "bi_he", "体用比和", "吉", 1, "巳", "孟夏", "火", (28, 8, 3, 4), 93, "上吉"),
    Case("报数[2,7]·用生体", "number", (2, 7), CAST, 2, 7, 3,
         31, "咸", "泽山咸", (0, 0, 1, 1, 1, 0), 44, "天风姤", 45, "泽地萃",
         "兑", "金", "upper", "死", "艮", "土", "lower", "相",
         "yong_sheng_ti", "用生体", "大吉", 2, "巳", "孟夏", "火", (38, -8, 2, 4), 86, "上吉"),
    Case("年月日时·参考", "time", None, CAST, 1, 7, 5,
         33, "遁", "天山遁", (0, 0, 1, 1, 1, 1), 44, "天风姤", 56, "火山旅",
         "艮", "土", "lower", "相", "乾", "金", "upper", "死",
         "ti_sheng_yong", "体生用", "小凶", -1, "巳", "孟夏", "火", (-8, 5, -6, 4), 45, "中平"),
    # 时辰敏感锚：参考时刻是巳时（时辰序 6），上卦和与下卦和 mod 6 同余，把「动爻÷6」错用
    # 上卦和也测不出；戌时（序 11）与辰时（序 5）两张才压得住「动爻由下卦和定」。
    Case("年月日时·戌时", "time", None, XU_CAST, 1, 4, 4,
         25, "无妄", "天雷无妄", (1, 0, 0, 1, 1, 1), 53, "风山渐", 42, "风雷益",
         "震", "木", "lower", "休", "乾", "金", "upper", "死",
         "yong_ke_ti", "用克体", "大凶", -2, "巳", "孟夏", "火", (-26, 0, 2, 3), 29, "凶"),
    Case("年月日时·立春前", "time", None, LICHUN_CAST, 3, 1, 1,
         14, "大有", "火天大有", (1, 1, 1, 1, 0, 1), 43, "泽天夬", 50, "火风鼎",
         "离", "火", "upper", "休", "乾", "金", "lower", "相",
         "ti_ke_yong", "体克用", "小吉", 1, "丑", "季冬", "土", (18, 0, -2, 4), 70, "吉"),
    Case("年月日时·闰二月", "time", None, LEAP_CAST, 1, 7, 5,
         33, "遁", "天山遁", (0, 0, 1, 1, 1, 1), 44, "天风姤", 56, "火山旅",
         "艮", "土", "lower", "死", "乾", "金", "upper", "囚",
         "ti_sheng_yong", "体生用", "小凶", -1, "卯", "仲春", "木", (-8, -8, -6, 4), 32, "小凶"),
    Case("报数[8]·单数法立春前", "number", (8,), LICHUN_CAST, 8, 6, 2,
         7, "师", "地水师", (0, 1, 0, 0, 0, 0), 24, "地雷复", 2, "坤为地",
         "坤", "土", "upper", "旺", "坎", "水", "lower", "死",
         "ti_ke_yong", "体克用", "小吉", 1, "丑", "季冬", "土", (18, 8, -2, 3), 77, "吉"),
)

IDS = [c.id for c in CASES]

#: 古典吉凶次序：用生体（大吉）＞ 体用比和（吉）＞ 体克用（小吉）＞ 体生用（小凶）＞ 用克体（大凶）。
CLASSICAL_ORDER = ["yong_sheng_ti", "bi_he", "ti_ke_yong", "ti_sheng_yong", "yong_ke_ti"]


def _cast(case: Case):
    return cast_meihua(
        method=case.method,
        numbers=list(case.numbers) if case.numbers else None,
        question=None,
        cast_time=case.cast,
    )


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_raising_arithmetic(case: Case) -> None:
    """起卦数：报数法首数÷8余为上卦、次数÷8余为下卦、诸数合计÷6余为动爻（余 0 作除数本身）；
    单数法之下卦与动爻另加时辰序；年月日时法以（年支序+农历月+农历日）为上卦数、再加时辰序。

    例：[16,8] → 16÷8 余 0 作 8（坤）、8÷8 余 0 作 8（坤）、24÷6 余 0 作 6（上爻）。
    参考时刻 2024-05-15 10:30 = 农历甲辰年四月初八巳时 → 年支序 5、月 4、日 8、时辰序 6。
    """
    result = _cast(case)
    assert result.derivation.upper_number == case.upper
    assert result.derivation.lower_number == case.lower
    assert result.moving_position == case.moving == result.derivation.moving_position
    # 透明算式里印出的三个余数必须就是实际卦数（算式与结果分家即假透明）。
    assert f"余{case.upper}为上卦" in result.derivation.formula
    assert f"余{case.lower}为下卦" in result.derivation.formula
    assert f"余{case.moving}为动爻" in result.derivation.formula


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_present_hexagram(case: Case) -> None:
    """本卦：先天数定上下卦（1乾 2兑 3离 4震 5巽 6坎 7艮 8坤），卦画自下而上，文王序对拍。"""
    ben = _cast(case).ben
    assert (ben.number, ben.name_zh, ben.full_name_zh) == (case.ben_number, case.ben_name, case.ben_full)
    assert tuple(ben.lines) == case.ben_lines
    assert (ben.lower.position, ben.upper.position) == ("lower", "upper")
    assert {ben.lower.name_zh, ben.upper.name_zh} == {case.ti_name, case.yong_name}


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_nuclear_and_changed_hexagrams(case: Case) -> None:
    """互卦取本体二三四爻为下互、三四五爻为上互；变卦只改动爻那一爻，余五爻不变。"""
    result = _cast(case)
    assert (result.hu.number, result.hu.full_name_zh) == (case.hu_number, case.hu_full)
    assert (result.bian.number, result.bian.full_name_zh) == (case.bian_number, case.bian_full)
    lines = result.ben.lines
    assert tuple(result.hu.lines) == (lines[1], lines[2], lines[3], lines[2], lines[3], lines[4])
    expected = list(lines)
    expected[case.moving - 1] ^= 1
    assert tuple(result.bian.lines) == tuple(expected)


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_ti_yong_roles_and_relation(case: Case) -> None:
    """体用：动爻在四五六（上卦）则上为用、下为体；在一二三则上为体、下为用。五行生克定名。"""
    result = _cast(case)
    assert result.ti.trigram.name_zh == case.ti_name
    assert result.ti.trigram.element == case.ti_element
    assert result.ti.trigram.position == case.ti_position
    assert result.yong.trigram.name_zh == case.yong_name
    assert result.yong.trigram.element == case.yong_element
    assert result.yong.trigram.position == case.yong_position
    assert (result.ti.role, result.yong.role) == ("ti", "yong")
    # 体与用必为本体卦的上下两画卦，各占一段。
    assert {result.ti.trigram.position, result.yong.trigram.position} == {"lower", "upper"}
    assert (result.tiyong.relation, result.tiyong.relation_zh) == (case.relation, case.relation_zh)
    assert (result.tiyong.verdict, result.tiyong.grade) == (case.tiyong_verdict, case.grade)


def test_the_five_relations_keep_their_classical_order() -> None:
    """十五张锚卦覆盖五条体用关系各至少一张，且吉凶次序不翻。"""
    by_relation: dict[str, Case] = {}
    for case in CASES:
        by_relation.setdefault(case.relation, case)
    assert set(by_relation) == set(CLASSICAL_ORDER)
    assert [by_relation[key].grade for key in CLASSICAL_ORDER] == [2, 1, 1, -1, -2]
    assert [by_relation[key].tiyong_verdict for key in CLASSICAL_ORDER] == \
        ["大吉", "吉", "小吉", "小凶", "大凶"]
    # 账本首项即体用生克的分量：次序必须与古法同向（体克用与比和虽同属吉，比和更胜）。
    assert [by_relation[key].deltas[0] for key in CLASSICAL_ORDER] == [38, 28, 18, -8, -26]


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_gua_qi_uses_the_jieqi_month_command(case: Case) -> None:
    """卦气：月建（节气界）定当令五行，体/用五行依令判旺相休囚死。

    巳月火当令 → 火旺、土相、木休、金死、水囚。锚集里五种状态齐备：旺（[3,3]、[7,3]、
    立春前单数法之土）、相（[16,8]、[8,9,10]）、休（[5,2]、立春前年月日时之火）、
    囚（[6,3]、闰二月之乾金）、死（[4,1]、[2,7]）。
    """
    result = _cast(case)
    assert (result.wangshuai.month_zhi, result.wangshuai.season_zh) == (case.month_zhi, case.season)
    assert result.wangshuai.commanding_element == case.commanding
    assert result.ti.wangshuai == case.ti_state
    assert result.yong.wangshuai == case.yong_state
    assert case.ti_state in result.ti.wangshuai_text


def test_time_method_takes_the_lunar_year_but_the_jieqi_month() -> None:
    """2023-02-04 09:15 落在春节（01-22）之后、立春（10:42）之前，两条历法界在此分岔。

    起卦用的年支是**农历年**（癸卯 → 卯 → 4），卦气用的月建是**节气月**（立春前仍作丑土）。
    农历库的 ``getMonthZhi()`` 给的是正月之支「寅」——引擎若改接那一根，本测即红：寅木当令
    会把体的「休」换成「旺」，账本与分数全变。梅花起卦 traditionally 用农历数、卦气用月建，
    两侧各取其界，故钉值。
    """
    result = cast_meihua(method="time", numbers=None, question=None, cast_time=LICHUN_CAST)
    lunar = Solar.fromYmdHms(2023, 2, 4, 9, 15, 0).getLunar()
    assert lunar.getYearZhi() == "卯"                  # 农历年支（春节界）
    assert lunar.getMonthZhi() == "寅"                 # 正月之支——引擎未取用
    assert result.derivation.inputs.startswith("农历年支序4、月1、日14")
    assert result.wangshuai.month_zhi == "丑"          # 月建（节气界）
    assert result.wangshuai.commanding_element == "土"
    assert result.ti.wangshuai == "休"


def test_leap_month_uses_the_same_month_number() -> None:
    """闰月与正二月同数：2023-04-01 为闰二月十一，起卦月数取 2（农历库以负号表闰）。"""
    lunar = Solar.fromYmdHms(2023, 4, 1, 10, 30, 0).getLunar()
    assert lunar.getMonth() == -2
    result = cast_meihua(method="time", numbers=None, question=None, cast_time=LEAP_CAST)
    assert result.derivation.inputs.startswith("农历年支序4、月2、日11")
    # 4+2+11 = 17 与参考时刻的 5+4+8 = 17 同余 → 同一组卦数，但月令已换，卦气随之而变。
    assert (result.derivation.upper_number, result.derivation.lower_number) == (1, 7)
    assert result.ti.wangshuai == "死"


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_ledger_is_the_score(case: Case) -> None:
    """吉凶指数 = 50 + Σ 四本账（体用生克 / 卦气旺衰 / 互卦过程 / 变卦结局），无暗账。

    互卦一本账上限 ±6：[8,9,10] 的两互卦为 -2（体生之泄）与 -5（克体），raw -7 被夹到 -6 ——
    锚表里的 -6 就是这条夹界的证据（若把夹界去掉，本测即红）。
    """
    result = _cast(case)
    factors = result.score_factors
    assert [f.label for f in factors] == ["体用生克", "卦气旺衰", "互卦(过程)", "变卦(结局)"]
    assert [f.delta for f in factors] == list(case.deltas)
    assert result.score == 50 + sum(f.delta for f in factors) == case.score
    assert case.ti_state in factors[1].detail
    # 过程/结局两本账把自己的数印在 detail 里（透明性不许只给一个数字）。
    assert f"过程助力{case.deltas[2]:+d}" in factors[2].detail
    assert f"结局{case.deltas[3]:+d}" in factors[3].detail


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_verdict_band_matches_the_declared_cut_offs(case: Case) -> None:
    """档位边界现测：≥85 上吉、≥70 吉、≥55 小吉、≥45 中平、≥30 小凶，其余凶；且 0-100 封顶。"""
    result = _cast(case)
    assert 0 <= result.score <= 100
    score = result.score
    expected = ("上吉" if score >= 85 else "吉" if score >= 70 else "小吉" if score >= 55
                else "中平" if score >= 45 else "小凶" if score >= 30 else "凶")
    assert result.verdict.grade == expected == case.band


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_verdict_card_carries_grade_stars_points_and_advice(case: Case) -> None:
    """结论卡片：档位词 = 账本 band，星级 = 署名映射 MEIHUA_STARS，points 恰为四本账，
    headline/advice 由框架句装配且复述档位词，引擎不现编中文。"""
    result = _cast(case)
    card = result.verdict
    assert card.grade == result.verdict.grade == case.band
    assert card.stars == MEIHUA_STARS[case.band]
    assert 1 <= card.stars <= 5
    assert len(card.points) == len(result.score_factors) == 4
    assert [p for p in card.points]
    assert case.band in card.headline
    assert str(result.score) in card.headline
    assert card.advice
    # 每本账的 label 都进了一条分项，净增减印在同一条上（透明性同账本）。
    for factor, point in zip(result.score_factors, card.points, strict=True):
        assert factor.label in point
        assert f"{factor.delta:+d}" in point


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_text_is_rendered_from_the_same_board(case: Case) -> None:
    """断语与类象必须由同一盘派生：summary 里出现的卦名、体用、月令、互变与卦辞即结构化字段本身。"""
    result = _cast(case)
    assert result.ben.full_name_zh in result.summary
    assert result.ti.trigram.name_zh in result.summary
    assert result.tiyong.relation_zh in result.summary
    assert result.hu_analysis in result.summary
    assert result.bian_analysis in result.summary
    assert result.ben.gua_ci in result.summary
    assert result.ti.leixiang.startswith(f"{result.ti.trigram.name_zh}为{result.ti.trigram.nature_zh}：")
    assert result.engine == "meihua-tiyong"
    assert result.method == case.method
    assert result.cast_time == case.cast.strftime("%Y-%m-%d %H:%M")


@pytest.mark.parametrize(
    "numbers",
    [None, [], [0], [-3], [7, 0], [1, 2, 3, 4], [7, 3, 0]],
    ids=["缺数", "空表", "单零", "单负", "双含零", "四数", "三数含零"],
)
def test_number_method_guardrails(numbers) -> None:
    """报数法只收 1–3 个正整数；越界一律 ``invalid_cast_input``，不静默取模。"""
    with pytest.raises(InvalidCastInputError) as excinfo:
        cast_meihua(method="number", numbers=numbers, question=None, cast_time=CAST)
    assert excinfo.value.code == "invalid_cast_input"
    assert "正整数" in excinfo.value.message


def test_the_same_input_reproduces_the_same_cast() -> None:
    """梅花起卦无随机：同入参两次排盘的完整载荷逐字段相同。"""
    first = cast_meihua(method="number", numbers=[7, 3], question="问事", cast_time=CAST)
    second = cast_meihua(method="number", numbers=[7, 3], question="问事", cast_time=CAST)
    assert first.model_dump() == second.model_dump()


def test_meihua_endpoint(client: TestClient) -> None:
    response = client.post(
        "/api/v1/meihua/cast",
        json={"method": "number", "numbers": [7, 3], "cast_time": "2024-05-15T10:30:00"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["ben"]["number"] == 22
    assert body["hu"]["number"] == 40
    assert body["bian"]["number"] == 30
    assert body["derivation"]["upper_number"] == 7
    assert body["derivation"]["lower_number"] == 3
    assert body["moving_position"] == 4
    assert body["tiyong"]["relation"] == "ti_sheng_yong"
    assert body["wangshuai"] == {"month_zhi": "巳", "season_zh": "孟夏", "commanding_element": "火"}
    assert [f["delta"] for f in body["score_factors"]] == [-8, 8, -1, 3]
    assert body["score"] == 52
    assert body["engine"] == "meihua-tiyong"


# --- 白话整段与出处块（多系统白话计划 Task 7）------------------------------------

#: 参考盘 报数[7,3] 于 2024-05-15 10:30（巳时）的白话整段：山火贲，体离火（旺）、用艮土（相），
#: 体生用，指数 52 → 中平。七行逐字来自语料表，改动任一条即红。
#: 长度 61/56/92/52/90/54/55，复测（2026-09-30 实录 `[61, 56, 92, 52, 90, 54, 55]`）：`cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "from app.engines.meihua import cast_meihua;from datetime import datetime;print([len(s) for s in cast_meihua(method='number',numbers=[7,3],question=None,cast_time=datetime(2024,5,15,10,30)).plain_summary.split(chr(10))])"`
PLAIN_MAIN_ANCHOR = [
    "把这一卦按体、用两侧各读一遍：先说体用之间的生克，再顺着你这一侧的取象与卦气，然后是对方那一侧的，两侧同为一卦时只说一遍。",
    "体卦去生用卦，你的力气是往外花在这件事上的，付出多而收回少，这一段是容易亏空的一格，进来与出去的数目常常不相称。",
    "离取象为火，你在这一步见到的人是次女、读书人、军中之人与相貌出众的人，落在身上是目、心与血脉，方位在南，物上是火、书画、甲胄一类与文明相关的器物，性子是外面明亮、内里附丽，来得快也急。",
    "这一卦的五行正当其时，你看到的是正盛的一股劲，好事遇上它加力，坏事遇上它也减几分，五档里数它的加力最多。",
    "艮取象为山，你在这一步见到的人是少年男子、小孩子、住山的人与修行之人，落在身上是手、指、背与鼻，方位在东北，物上是山石、门阙、果实与床，性子是静止稳重，也固执，事情到它这里就停住。",
    "这一卦被当令的五行所生，你看到的是正在长起来的一股劲，助力一点点变多，这件事有后续，不是一眼看得见底的那种。",
    "合起来读，你这一卦各方力量互有消长、势均力敌，机缘与阻碍相持并存，此时稳住根基、看清局势对你而言最为切实。",
]


def test_plain_summary_reads_the_body_side_then_the_use_side() -> None:
    """五句正文 + 开篇 + 收尾，序即盘面序（`TiYongParty` 的字段序：取象在卦气之前）。"""
    assert _cast(CASES[0]).plain_summary.split("\n") == PLAIN_MAIN_ANCHOR


def test_a_pure_hexagram_says_the_shared_sentences_once() -> None:
    """八纯卦（坤为地）体用同卦同气：类象与卦气各只说一遍，整段从七行收成五行。

    这就是公共层 `dedupe()` 在梅花这一侧的存在理由：逐条搬运会让同一句在同一段里
    连说两遍，而它今天有真实盘面能触发（报数[16,8] 与 [3,3] 两张锚卦都是八纯卦）。
    """
    result = cast_meihua(method="number", numbers=[16, 8], question=None, cast_time=CAST)
    assert (result.ti.trigram.key, result.yong.trigram.key) == ("kun", "kun")
    assert result.ti.wangshuai == result.yong.wangshuai
    lines = result.plain_summary.split("\n")
    assert len(lines) == 5
    assert len(set(lines)) == 5, "同一段里出现了重复句"


def test_the_zero_delta_gua_qi_row_still_gets_its_sentence() -> None:
    """`grouping="keep"` 的实证：体卦处「休」时账本符号是 0，分带会当场拒装配（ValueError）。

    报数[5,2] 用克体、体卦巽木在巳月处休，`_wangshuai_delta("休") == 0`
    （`app/engines/meihua.py` 的 `_wangshuai_delta`）。走 band 分支这一格两头都不进，白话层要么崩要么丢句，
    走 keep 它照旧成段——这就是 spec §6 给梅花选 keep 的全部理由，钉在真实盘上。
    """
    result = cast_meihua(method="number", numbers=[5, 2], question=None, cast_time=CAST)
    assert result.ti.wangshuai == "休"
    assert [factor.delta for factor in result.score_factors][1] == 0
    assert MEIHUA.entries[wangshuai_key("休")] in result.plain_summary.split("\n")


def test_closers_cover_exactly_the_bands_the_engine_prints() -> None:
    """收尾句键集 == `_verdict_band` 的像集（G3：closers 的键必须恰是该系统的档位集合）。

    逐档 label 由 `_verdict_band` 现算，15 张锚卦各自的末行也各钉一次，两半合起来
    才是「引擎印得出的档，白话都有下文；白话写出的档，引擎都印得出」。
    """
    assert {_verdict_band(score) for score in range(0, 101)} == set(MEIHUA.closers)
    assert {case.band for case in CASES} == set(MEIHUA.closers)      # 六档十五锚全覆盖
    for case in CASES:
        result = _cast(case)
        assert result.plain_summary.split("\n")[-1] == MEIHUA.closers[case.band]


def test_plain_summary_never_quotes_the_gua_ci() -> None:
    """卦辞今译是丁组 `zhouyi_plain` 的活（spec §6 末段）：本表一条都不许带。

    钉「不含原文」而不是钉「不含今译」：原文是表里就有的字符串，今译一旦并表，
    同一句卦辞就有了两个转述版本，这条门是那次合并之前的最后一道闸。
    """
    for case in CASES:
        result = _cast(case)
        assert result.ben.gua_ci not in result.plain_summary


def test_provenance_lists_exactly_the_five_tables_the_cast_reads() -> None:
    """出处清单：五张表一张不多一张不少，版本同 `CONTENT_VERSION`（AGENTS.md §7）。"""
    provenance = _cast(CASES[0]).provenance
    assert [table.name for table in provenance.tables] == [
        "meihua", "meihua_plain", "zhouyi_trigrams", "zhouyi_hexagrams", "zhouyi_text",
    ]
    assert {table.version for table in provenance.tables} == {CONTENT_VERSION}
    assert all(table.source for table in provenance.tables)
    # 历法来源认账的是**库**，不是推导器名（AGENTS.md §6；顶层 engine 才是 meihua-tiyong）。
    assert provenance.engine == "lunar-python"
    # 口径句必须说得出算式与确定性这两件可核对的事，否则它只是一句广告。
    assert "mod 8" in provenance.method and "无随机" in provenance.method


def test_meihua_corpus_is_the_one_the_registry_holds() -> None:
    """登记身份闸（裁定 R24，与姓名学/合盘同形）。工厂按 `PLAIN_CORPORA.values()` 跑表，
    看不见键覆盖：两行同 `system` 时 Python 静默留最后一行，前一张表就此掉出闸外，
    而工厂的两条形状断言照样绿。这一条由消费方自证在场，且它在 Step 5 就已经是绿的。"""
    assert PLAIN_CORPORA["meihua"] is MEIHUA
