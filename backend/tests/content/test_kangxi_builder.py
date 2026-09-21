"""构建期产物的守卫：出处闸门、恒等式、简繁边方向与 24 字对拍。"""

import json
from pathlib import Path

import pytest

from tests.content.name_radical_fixture import KANGXI_RADICALS

DATA = Path(__file__).resolve().parent.parent.parent / "data"
STROKES = json.loads((DATA / "kangxi_strokes.json").read_text(encoding="utf-8"))
RADICALS = json.loads((DATA / "kangxi_radicals.json").read_text(encoding="utf-8"))
BY_CHAR = {item["char"]: item for item in STROKES["items"]}
DERIVED = {item["radical_no"]: item["strokes"] for item in RADICALS["items"]}
DERIVED_CHARS = {item["radical_no"]: item["char"] for item in RADICALS["items"]}

#: spec §2.2 的 24 字实测对拍（计划期 24/24 一致）。江=7 而非现代 6 是这一组的关键。
GOLDEN_STROKES = {
    "江": 7, "河": 9, "王": 5, "涵": 12, "潤": 16, "淵": 12, "陸": 16, "青": 8,
    "玄": 5, "珊": 10, "珍": 10, "張": 11, "華": 14, "運": 16, "達": 16, "芝": 10,
    "隊": 17, "草": 12, "德": 15, "儀": 15, "國": 11, "龍": 16, "鳳": 14, "李": 7,
}


def kangxi(char: str) -> int:
    """产物里不存第三个真相：康熙笔画恒等于 部首画数 + 余画（spec §5.2）。"""
    item = BY_CHAR[char]
    return DERIVED[item["radical_no"]] + item["residual"]


def test_products_are_self_consistent() -> None:
    assert STROKES["size"] == len(STROKES["items"]) == len(BY_CHAR)
    assert STROKES["unicode_version"] == RADICALS["unicode_version"]
    assert "推导" in STROKES["source"] and "推导" in RADICALS["source"]


def test_radical_rows_match_the_external_fixture() -> None:
    """spec §5.5 出处闸门：214 行的画数与部首字形都必须等于外部出版表。

    计划期对拍：画数只差第 114 部、字形差 4 行，全部已按出处进 override。
    这条测试失败时先查推导，不要改 fixture。
    """
    assert len(DERIVED) == 214
    assert DERIVED == {no: strokes for no, (strokes, _) in KANGXI_RADICALS.items()}
    assert DERIVED_CHARS == {no: char for no, (_, char) in KANGXI_RADICALS.items()}


def test_radical_114_override_is_justified_by_its_members() -> None:
    """第 114 部取 5 的理由必须仍然成立：禹/禺 部外 4 画、康熙 9 画。

    取 4 会得到 8，与外部表和 Unihan 自身 `kTotalStrokes(禹)=9` 同时矛盾。
    """
    assert DERIVED[114] == 5
    assert kangxi("禹") == 9 and kangxi("禺") == 9


@pytest.mark.parametrize(("char", "expected"), sorted(GOLDEN_STROKES.items()))
def test_golden_kangxi_strokes(char: str, expected: int) -> None:
    """唯一能自动抓住「误用 kTotalStrokes」这类致命错误的哨兵。"""
    assert kangxi(char) == expected


def test_variant_edges_point_the_right_way() -> None:
    """两条简繁边的方向是产物可用性的前提，写反了 422 追问永远不会触发。"""
    assert "陸" in BY_CHAR["陆"]["traditional"]
    assert "陆" in BY_CHAR["陸"]["simplified"]
    assert "財" in BY_CHAR["财"]["traditional"]
    # 一简对多繁：发的两个繁体都在，交给用户选，后端不猜。
    assert set(BY_CHAR["发"]["traditional"]) == {"發", "髮"}
    # 本身即正体的字不该被追问：traditional 为空时加载器只返回自己。
    assert BY_CHAR["李"]["traditional"] == []
    # 部首索引字形（王 = 96.-1）余画记 0，恒等式对全表成立。
    assert BY_CHAR["王"]["residual"] == 0 and kangxi("王") == 5
