"""相位属性表的门（Plan G T1，spec §5.2 裁定 R49）。

为什么这张小表要有自己的测：它是**两个引擎的输出字段**的字面来源，而搬家的验收标准是
「搬家前后逐字节不变」。工厂看不到它（`ASPECT_NATURE` 不是 `PlainCorpus` 的条目，
它没有白话句的四项契约），所以三条口径全部住在本地：五档字面、两处引擎真的改引它、
出处串不是句子。
"""

from pathlib import Path

from app.content.aspects_nature import ASPECT_NATURE, ASPECT_NATURE_SOURCE
from app.engines.western import ASPECTS
from tests.plain_wording import FORBIDDEN


def test_the_five_aspect_types_carry_the_declared_taxonomy() -> None:
    aspect_names = [aspect[0] for aspect in ASPECTS]
    assert aspect_names == sorted(ASPECT_NATURE, key=aspect_names.index)
    # 键集 = ASPECTS 的五个类型，一个不多一个不少
    assert ASPECT_NATURE["conjunction"] == ("fusion", "融合")
    assert ASPECT_NATURE["sextile"] == ("harmonious", "和谐")
    assert ASPECT_NATURE["trine"] == ("harmonious", "和谐")
    assert ASPECT_NATURE["square"] == ("challenging", "挑战")
    assert ASPECT_NATURE["opposition"] == ("challenging", "挑战")


def test_both_overlay_engines_read_the_table_and_define_no_local_copy() -> None:
    """搬家是**两个**消费者（实测，不是 spec 说的三个；吠陀引擎不读它）。

    复测：`cd backend && grep -rn "ASPECT_NATURE" app/engines/` → 源码只命中 transit.py 与
    synastry.py 各一条 import 加一处 `ASPECT_NATURE[aspect_name]` 调用（`__pycache__/*.pyc`
    会一并匹配），`engines/vedic.py` 零命中。
    """
    root = Path(__file__).resolve().parents[2]
    for name in ("transit.py", "synastry.py"):
        source = (root / "app" / "engines" / name).read_text(encoding="utf-8")
        assert "_NATURE = {" not in source, name
        assert "from app.content.aspects_nature import ASPECT_NATURE" in source, name
        assert "ASPECT_NATURE[aspect_name]" in source, name


def test_the_source_string_is_a_provenance_string_not_a_sentence() -> None:
    for token in FORBIDDEN:
        assert token not in ASPECT_NATURE_SOURCE, token
    assert "《" not in ASPECT_NATURE_SOURCE and "依" not in ASPECT_NATURE_SOURCE
    assert ASPECT_NATURE_SOURCE.startswith("平台整理的相位属性表"), ASPECT_NATURE_SOURCE
    assert ASPECT_NATURE_SOURCE.endswith("。"), ASPECT_NATURE_SOURCE


def test_the_registration_lists_exactly_the_two_engines_that_read_it() -> None:
    from app.content import SYNASTRY_CONTENT_SOURCES

    assert [name for name, _source in SYNASTRY_CONTENT_SOURCES] == [
        "synastry_scoring", "synastry_plain", "aspects_nature"
    ]
