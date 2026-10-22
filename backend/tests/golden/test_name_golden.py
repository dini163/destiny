"""设计稿自印数字的全案对拍（spec §9.3）。

`陆青玄 / 陸青玄` 的五个末端数字 17/24/13/6/29 与五个标签 阳金/阴火/阳火/阴土/阳水
都印在设计稿里，它们分别落在推导链末端（笔画→五格→循环→尾数→奇偶）。全中即说明
spec §2.2 的 Unihan 链与 §6 的算术口径与该稿一致。
"""

import pytest

from app.content.kangxi_strokes import lookup
from app.content.name_plain import (
    NAME_GRID_OPENERS,
    NAME_READINGS,
    NAME_SANCAI_CLOSERS,
    NAME_SANCAI_OPENER,
    NAME_SCORE_CLOSERS,
    NAME_SUMMARY_OPENER,
    NAME_UNRESOLVED_KEY,
    sancai_key,
    shuli_key,
)
from app.engines.name_numerology import GRID_ORDER, NAME_STARS, analyze_name

GRID_KEYS = ["tian", "ren", "di", "wai", "zong"]


@pytest.mark.parametrize("text", ["陸青玄", "陆青玄"])
def test_design_mockup_five_grids(text: str) -> None:
    analysis = analyze_name(text[:1], text[1:])
    by_key = {grid.key: grid for grid in analysis.grids}

    assert [by_key[key].value for key in GRID_KEYS] == [17, 24, 13, 6, 29]
    assert [by_key[key].formula for key in GRID_KEYS] == ["16+1", "16+8", "8+5", "29−24+1", "16+8+5"]
    assert [by_key[key].wuxing for key in GRID_KEYS] == ["金", "火", "火", "土", "水"]
    assert [by_key[key].yinyang for key in GRID_KEYS] == ["阳", "阴", "阳", "阴", "阳"]
    assert analysis.input.modality == "单姓复名"
    assert analysis.sancai is not None and analysis.score is not None


def test_simplified_and_traditional_inputs_agree_on_grids() -> None:
    """简繁只是入口糖，笔画校准在数据层（spec §9.4）。"""
    assert analyze_name("陆", "青玄").grids == analyze_name("陸", "青玄").grids


def test_char_entries_show_input_but_count_the_traditional() -> None:
    """展示字形 = 用户输入的；计笔画字形 = 核定后的正体。两者同排回显。"""
    analysis = analyze_name("陆", "青玄")
    assert [item.char for item in analysis.chars] == ["陆", "青", "玄"]
    assert [item.resolved for item in analysis.chars] == ["陸", "青", "玄"]
    assert [item.kangxi_strokes for item in analysis.chars] == [16, 8, 5]


def test_sancai_pairs_are_the_three_expected_reads() -> None:
    analysis = analyze_name("陸", "青玄")
    assert analysis.sancai is not None
    assert [pair.pair for pair in analysis.sancai.pairs] == ["天人", "人地", "天地"]
    elements = analysis.sancai.elements
    assert (elements.tian, elements.ren, elements.di) == ("金", "火", "火")


def test_stroke_row_behind_the_mockup_numbers() -> None:
    """五格数字的唯一外部锚点是这三笔笔画；断在此处即 T1 推导链有问题。"""
    assert [lookup(char).kangxi_strokes for char in "陸青玄"] == [16, 8, 5]


ZHANG_YI = analyze_name("张", "一")  # 四格皆凶：裁定 R2 的证据盘
LU_QINGXUAN = analyze_name("陆", "青玄")  # 半吉/吉/大吉/半吉/半吉 + 三才多克
ZHANG_UNRESOLVED = analyze_name("张", "𠀋")  # 名在语料外：降级支路


def _grid(analysis, key: str):
    return next(grid for grid in analysis.grids if grid.key == key)


def test_each_grid_card_is_opener_plus_its_own_number() -> None:
    """一格白话 = 该格开篇句 + 数理转述，两行以换行分隔。单格无档位，所以没有收尾句。"""
    assert _grid(LU_QINGXUAN, "ren").plain == "\n".join(
        [NAME_GRID_OPENERS["ren"], NAME_READINGS[shuli_key(24)]]
    )
    assert _grid(LU_QINGXUAN, "tian").plain == "\n".join(
        [NAME_GRID_OPENERS["tian"], NAME_READINGS[shuli_key(17)]]
    )


def test_four_causal_grids_are_not_dropped_by_band_splitting() -> None:
    """张一 四格 delta 皆为 0.0：分带符号若取 delta，这四句会静默消失（spec 裁定 R2）。

    四格同档（凶）而数理并不同：天/人/总是 12、地格是 2（实测锚点表），所以逐格比的是
    自己那一行的转述，而不是四格共用一条。
    """
    assert [f.delta for f in ZHANG_YI.score.factors] == [0.0, 0.0, 0.0, 0.0, 10.0, 0.0]
    for key, number in (("tian", 12), ("ren", 12), ("di", 2), ("zong", 12)):
        assert _grid(ZHANG_YI, key).plain.split("\n")[1] == NAME_READINGS[shuli_key(number)]


def test_plain_summary_bands_by_fortune_and_says_a_shared_number_once() -> None:
    """总论按「大吉/吉 → 顺、半吉/凶 → 注意」两侧重排；同数两格不重说（裁定 R12）。"""
    lines = ZHANG_YI.plain_summary.split("\n")
    assert lines == [
        NAME_SUMMARY_OPENER,
        NAME_READINGS[shuli_key(1)],
        NAME_READINGS[shuli_key(12)],
        NAME_READINGS[shuli_key(2)],
        NAME_SCORE_CLOSERS["下"],
    ]
    assert lines.count(NAME_READINGS[shuli_key(12)]) == 1  # 天/人/总三格同为数理 12


def test_plain_summary_keeps_grid_order_inside_each_band() -> None:
    """顺侧（人 24、地 13）先于注意侧（天 17、外 6、总 29），两侧内部照 `GRID_ORDER`。"""
    assert LU_QINGXUAN.plain_summary.split("\n") == [
        NAME_SUMMARY_OPENER,
        NAME_READINGS[shuli_key(24)],
        NAME_READINGS[shuli_key(13)],
        NAME_READINGS[shuli_key(17)],
        NAME_READINGS[shuli_key(6)],
        NAME_READINGS[shuli_key(29)],
        NAME_SCORE_CLOSERS["中"],
    ]


def test_sancai_plain_is_one_paragraph_with_a_tier_closer() -> None:
    """三才整块一段：开篇 + 顺侧 + 注意侧 + 档位收尾；两对同为克我只说一遍。"""
    assert LU_QINGXUAN.sancai is not None
    lines = LU_QINGXUAN.sancai.plain.split("\n")
    assert lines == [
        NAME_SANCAI_OPENER,
        NAME_READINGS[sancai_key("比和")],
        NAME_READINGS[sancai_key("克我")],
        NAME_SANCAI_CLOSERS["多克"],
    ]
    assert lines.count(NAME_READINGS[sancai_key("克我")]) == 1
    assert ZHANG_YI.sancai is not None
    assert ZHANG_YI.sancai.plain.split("\n") == [
        NAME_SANCAI_OPENER,
        NAME_READINGS[sancai_key("比和")],
        NAME_SANCAI_CLOSERS["相生和顺"],
    ]


def test_unresolved_grid_and_response_never_fabricate_a_number() -> None:
    """缺笔画那一格搬「未核定」那一条；三才与分数整块 None，总论只说有的一格。"""
    assert _grid(ZHANG_UNRESOLVED, "ren").plain == "\n".join(
        [NAME_GRID_OPENERS["ren"], NAME_READINGS[NAME_UNRESOLVED_KEY]]
    )
    assert _grid(ZHANG_UNRESOLVED, "ren").verdict is None
    assert ZHANG_UNRESOLVED.sancai is None and ZHANG_UNRESOLVED.score is None
    assert ZHANG_UNRESOLVED.verdict is None
    assert ZHANG_UNRESOLVED.plain_summary == "\n".join(
        [NAME_SUMMARY_OPENER, NAME_READINGS[shuli_key(12)]]
    )


def test_verdict_card_carries_grade_stars_points_and_none_when_unresolved() -> None:
    """结论卡片：档位词 = score.tier，星级 = 署名映射 NAME_STARS，points 为五格 + 三才；
    笔画未核定（score None）时 verdict 整块省略，不补占位卡。"""
    for analysis in (ZHANG_YI, LU_QINGXUAN):
        assert analysis.score is not None and analysis.verdict is not None
        card = analysis.verdict
        assert card.grade == analysis.score.tier
        assert card.stars == NAME_STARS[card.grade]
        assert 1 <= card.stars <= 5
        expected_points = len(analysis.grids) + (1 if analysis.sancai is not None else 0)
        assert len(card.points) == expected_points
        assert card.grade in card.headline
        assert analysis.score.tier in card.headline
        assert card.advice
    assert ZHANG_UNRESOLVED.verdict is None