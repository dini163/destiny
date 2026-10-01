"""公共装配器的行为契约（白话 spec §3、§11）。

本文件不测任何系统的语料内容，只测装配器的分支与异常。两张表是**测试自造的
最小 corpus**（不是假命盘、不是假响应，不违反 AGENTS.md §9 的无 mock 铁律）。
卡巴拉的逐字节判据原先寄在这里，Plan B Task 3 把它迁进了生产侧（见文件末注）。
"""

from collections import OrderedDict

import pytest

from app.engines.plain_compose import (
    PlainCorpus,
    compose,
    compose_template,
    dedupe,
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
    out = compose(BANDED, "demo", [("demo.a", 1)], None)
    assert out == "\n".join([BANDED.openers["demo"], BANDED.entries["demo.a"]])


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


def test_dedupe_keeps_the_first_occurrence_and_its_sign() -> None:
    assert dedupe([("a.x", -1), ("a.y", 1), ("a.x", -1)]) == [("a.x", -1), ("a.y", 1)]


def test_dedupe_does_not_lose_a_key_that_only_appears_later() -> None:
    assert [key for key, _ in dedupe([("a.x", 1), ("a.z", -1), ("a.x", 1)])] == ["a.x", "a.z"]


# 卡巴拉的逐字节判据住在生产侧：`tests/golden/test_kabbalah_golden.py::test_gematria_synthesis_text_is_pinned_before_the_overview_migration`。
# 本文件不再持有任何系统的具体文案（frame 已进 `engines/kabbalah.py`，两处定义必漂）。


def test_is_slot_key_only_answers_for_the_declared_slot_vocabulary() -> None:
    assert is_slot_key(SLOTTED, "slot.point.Sun") is True
    assert is_slot_key(SLOTTED, "slot.aspect.conjunction") is False
    assert is_slot_key(BANDED, "demo.a") is False
