"""设计稿自印数字的全案对拍（spec §9.3）。

`陆青玄 / 陸青玄` 的五个末端数字 17/24/13/6/29 与五个标签 阳金/阴火/阳火/阴土/阳水
都印在设计稿里，它们分别落在推导链末端（笔画→五格→循环→尾数→奇偶）。全中即说明
spec §2.2 的 Unihan 链与 §6 的算术口径与该稿一致。
"""

import pytest

from app.content.kangxi_strokes import lookup
from app.engines.name_numerology import GRID_ORDER, analyze_name

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