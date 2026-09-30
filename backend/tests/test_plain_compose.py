"""公共装配器的行为契约（白话 spec §3、§11）。

本文件不测任何系统的语料内容，只测装配器的分支与异常。两张表是**测试自造的
最小 corpus**（不是假命盘、不是假响应，不违反 AGENTS.md §9 的无 mock 铁律），
第三张表用真实生产对象：卡巴拉的 `_synthesize` 逐字节判据。
"""

from collections import OrderedDict

import pytest

from app.engines.kabbalah import compute_gematria
from app.engines.plain_compose import (
    PlainCorpus,
    compose,
    compose_template,
    is_slot_key,
    overview,
    reading,
)

BANDED = PlainCorpus(
    system="demo",
    entries=OrderedDict(
        [
            ("demo.a", "甲句：你在这一条上先感到的是顺，后面的事都跟着松开一段。"),
            ("demo.b", "乙句：你在这一条上使的劲会偏到旁边去，收回来才能落在事上。"),
            ("demo.c", "丙句：这一条给你的是一种慢，快不起来但也散不掉。"),
        ]
    ),
    openers={"demo": "这一节看的是你与配置之间顺不顺，只述倾向，不替你决定。"},
    closers={"好": "合起来读，你这一节属顺的一侧，按自己的节奏推进就好。"},
    grouping="band",
    universe=lambda: {"demo.a", "demo.b", "demo.c"},
)

KEPT = PlainCorpus(
    system="kept",
    entries={"kept.x": "第一句：你在这一条上得到的是明面上的顺，别人也看得见。",
             "kept.y": "第二句：这一条给你的是暗地里的一段吃力，说出来才算公平。"},
    openers={"kept": "这一节按盘面原序陈述，你读到的是次序而不是排名。"},
    closers=None,
    grouping="keep",
    universe=lambda: {"kept.x", "kept.y"},
)

SLOTTED = PlainCorpus(
    system="slot",
    entries={"slot.point.Sun": "自我与生命方向", "slot.aspect.conjunction": "框架句"},
    openers={},
    closers=None,
    grouping="keep",
    universe=lambda: {"slot.point.Sun", "slot.aspect.conjunction"},
    slot_prefixes=frozenset({"slot.point."}),
)


def test_compose_band_puts_positive_signs_before_negative_ones() -> None:
    out = compose(BANDED, "demo", [("demo.c", -1), ("demo.a", 2), ("demo.b", -3)], "好")
    assert out == "\n".join(
        [BANDED.openers["demo"], BANDED.entries["demo.a"],
         BANDED.entries["demo.c"], BANDED.entries["demo.b"], BANDED.closers["好"]]
    )


def test_compose_band_keeps_input_order_inside_each_side() -> None:
    out = compose(BANDED, "demo", [("demo.b", 1), ("demo.c", 2)], None)
    assert out.split("\n")[1:3] == [BANDED.entries["demo.b"], BANDED.entries["demo.c"]]


def test_compose_band_rejects_zero_sign_instead_of_dropping_the_line() -> None:
    with pytest.raises(ValueError, match="静默丢句"):
        compose(BANDED, "demo", [("demo.a", 1), ("demo.c", 0)], "好")


def test_compose_keep_outputs_the_board_order_and_never_checks_the_sign() -> None:
    out = compose(KEPT, "kept", [("kept.y", 0), ("kept.x", -9)], None)
    assert out == "\n".join([KEPT.openers["kept"], KEPT.entries["kept.y"], KEPT.entries["kept.x"]])


def test_compose_without_closer_declaration_refuses_a_tier() -> None:
    with pytest.raises(ValueError, match="不新增判断"):
        compose(KEPT, "kept", [("kept.x", 1)], "好")


def test_compose_emits_no_tier_sentence_when_tier_is_none() -> None:
    assert "顺的一侧" not in compose(BANDED, "demo", [("demo.a", 1)], None)


@pytest.mark.parametrize("kwargs", [
    {"section": "nope", "items": [("demo.a", 1)]},
    {"section": "demo", "items": [("demo.zzz", 1)]},
    {"section": "demo", "items": [("demo.a", 1)], "tier": "没有这一档"},
])
def test_unknown_keys_crash_rather_than_leak_a_fallback_sentence(kwargs) -> None:
    with pytest.raises(KeyError):
        compose(BANDED, **kwargs)


def test_reading_is_verbatim_transport_and_unknown_key_crashes() -> None:
    assert reading(BANDED, "demo.a") is BANDED.entries["demo.a"]
    with pytest.raises(KeyError, match="未知白话键"):
        reading(BANDED, "demo.nope")


def test_compose_template_fills_slots_verbatim() -> None:
    frame = "你的{a}与对方的{b}落在同一个位置上，两股力气合用一处，你在相处里最先感到的是它们撞在一起。"
    out = compose_template(frame, {"a": "自我与生命方向", "b": "情绪与安全感"})
    assert out == "你的自我与生命方向与对方的情绪与安全感落在同一个位置上，两股力气合用一处，你在相处里最先感到的是它们撞在一起。"


def test_compose_template_missing_slot_crashes_not_blanks_it() -> None:
    with pytest.raises(KeyError, match="b"):
        compose_template("你的{a}与对方的{b}合在一处，这一条不需要解释就能感到两股力气并到了一起。", {"a": "自我与生命方向"})


def test_overview_substitutes_parts_verbatim_and_refuses_a_missing_slot() -> None:
    assert overview("甲{one}乙{two}丙。", {"one": "一", "two": "二"}) == "甲一乙二丙。"
    with pytest.raises(KeyError, match="two"):
        overview("甲{one}乙{two}丙。", {"one": "一"})


KABBALAH_FRAME_REHEARSAL = (
    "「{normalized}」的英文 ordinal 数值为 {ordinal}（reduction {reduction}，数根 {root}）。"
    "折入生命之树，它相应于第 {sephirah_number} 原质【{sephirah_name_zh} {sephirah_name_hebrew} · "
    "{sephirah_pillar_name_zh} · {sephirah_sphere}】——{sephirah_meaning}"
    "又连于第 {path_number} 路径【{path_letter_zh} {path_letter}（{path_letter_value}）· "
    "{path_tarot_zh} {path_tarot_numeral} · {path_correspondence}】——{path_meaning}"
    "两相参详：此名之数理落点，提示由「{path_from_name_zh}」经「{path_tarot_zh}」之路，"
    "趋近「{sephirah_name_zh}」之境的功课。"
)


def _kabbalah_parts(reading_obj) -> dict[str, str]:
    seph, path = reading_obj.sephirah, reading_obj.path
    return {
        "normalized": reading_obj.normalized,
        "ordinal": str(reading_obj.english_ordinal),
        "reduction": str(reading_obj.english_reduction),
        "root": str(reading_obj.digital_root),
        "sephirah_number": str(seph.number),
        "sephirah_name_zh": seph.name_zh,
        "sephirah_name_hebrew": seph.name_hebrew,
        "sephirah_pillar_name_zh": seph.pillar_name_zh,
        "sephirah_sphere": seph.sphere,
        "sephirah_meaning": seph.meaning,
        "path_number": str(path.number),
        "path_letter_zh": path.letter_zh,
        "path_letter": path.letter,
        "path_letter_value": str(path.letter_value),
        "path_tarot_zh": path.tarot_zh,
        "path_tarot_numeral": path.tarot_numeral,
        "path_correspondence": path.correspondence,
        "path_meaning": path.meaning,
        "path_from_name_zh": path.from_name_zh,
    }


@pytest.mark.parametrize("word", ["Sol", "LILITH", "abracadabra", "Q", "destiny"])
def test_overview_reproduces_the_live_kabbalah_synthesis_byte_for_byte(word) -> None:
    """G13 的第二道「装得下」判据（spec §3、§11 抽象判据行的卡巴拉半边）。

    `engines/kabbalah.py:184-192` 的 `_synthesize` 把原质与路径的字段**穿插**在同一句里
    （`tarot_zh` 与 `name_zh` 各出现两次），所以只有「具名槽位 + 逐字搬运」的形态装得下它，
    部件列表拼接装不下——这正是裁定 R11 把 `overview` 定成 `frame.format(**parts)` 的原因。
    这里不迁卡巴拉（那是 Plan B 的收编任务），只钉住形状：frame 是 Plan B 的表要抄的模板，
    不是第二份生产文案。**卡巴拉正文若被改动，这条会红**——红了的意义是 Plan B 那张表必须
    跟着改，而不是本装配器坏了。
    """
    assert KABBALAH_FRAME_REHEARSAL.format(**_kabbalah_parts(compute_gematria(word))) == compute_gematria(word).synthesis


def test_is_slot_key_only_answers_for_the_declared_slot_vocabulary() -> None:
    assert is_slot_key(SLOTTED, "slot.point.Sun") is True
    assert is_slot_key(SLOTTED, "slot.aspect.conjunction") is False
    assert is_slot_key(BANDED, "demo.a") is False
