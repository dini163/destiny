"""笔画链的运行时契约：只读固化产物，算不出就返回 None（spec 决策八）。"""

import pytest

from app.content.kangxi_strokes import (
    STROKE_SOURCE,
    corpus_meta,
    lookup,
    radical_strokes,
    tone_of,
    traditional_candidates,
)


def test_derived_field_is_not_a_second_truth() -> None:
    """江：水部 4 画 + 余 3 画 = 7，不是现代 kTotalStrokes 的 6。"""
    entry = lookup("江")
    assert entry is not None
    assert entry.radical_char == "水"
    assert entry.radical_strokes == 4
    assert entry.residual_strokes == 3
    assert entry.kangxi_strokes == entry.radical_strokes + entry.residual_strokes == 7


def test_index_form_char_has_zero_residual() -> None:
    """王 = 96.-1：它本身就是部首索引字形，取玉部 5 画，不可 +(-1)。"""
    entry = lookup("王")
    assert entry is not None
    assert entry.radical_no == 96
    assert entry.radical_char == "玉"
    assert entry.residual_strokes == 0
    assert entry.kangxi_strokes == 5


def test_out_of_scope_char_is_reported_absent() -> None:
    assert lookup("🀄") is None
    assert lookup("A") is None


def test_traditional_candidates_fall_back_to_the_char_itself() -> None:
    assert traditional_candidates("陸") == ["陸"]
    assert "陸" in traditional_candidates("陆")
    assert len(traditional_candidates("发")) > 1
    assert len(traditional_candidates("干")) > 1


@pytest.mark.parametrize(
    ("pinyin", "expected"),
    [
        ("jiāng", ("jiang", 1, "阴平")),
        ("lóng", ("long", 2, "阳平")),
        ("shǎn", ("shan", 3, "上声")),
        ("qìng", ("qing", 4, "去声")),
        ("de", ("de", 5, "轻声")),
        # ǚ/ǜ 是带分音符的复合调号：NFD 拆成 u + ¨ + ˇ/`，去掉 caron/grave 后
        # 必须留着 ü（裸拼音里两点是元音本体，不是调号），所以两行都要写死。
        ("lǚ", ("lü", 3, "上声")),
        ("lǜ", ("lü", 4, "去声")),
    ],
)
def test_tone_of_reads_the_diacritic(pinyin: str, expected: tuple[str, int, str]) -> None:
    assert tone_of(pinyin) == expected


def test_every_row_holds_the_identity_and_a_source() -> None:
    meta = corpus_meta()
    assert meta.size > 30_000 and meta.unicode_version
    assert "推导" in STROKE_SOURCE
    for radical_no in range(1, 215):
        assert radical_strokes(radical_no) > 0
