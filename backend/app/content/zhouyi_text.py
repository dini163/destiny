"""Unified access to the classical 周易 text (卦辞 + 爻辞).

Aggregates the curated received-text tables — :mod:`app.content.zhouyi_guaci`
(64 judgments plus 乾/坤's 用九/用六) and the two 爻辞 canons (上经 1-30,
下经 31-64) — into a single lookup surface for the engine, and derives the
classical line titles (初九 / 六二 …) from position and polarity so they can
never disagree with the hexagram structure.

All content is static, public-domain reference data; nothing here is generated
at runtime. Count invariants (64 卦辞, 384 爻辞) are enforced by tests.
"""

from app.content.zhouyi_guaci import GUA_CI, GUA_CI_COUNT, YONG_CI
from app.content.zhouyi_yaoci_lower import YAO_CI_LOWER
from app.content.zhouyi_yaoci_upper import YAO_CI_UPPER

#: 源文书的书级出处。这一串是全站唯一的一份：`content/__init__.py` 里梅花与周易两张
#: 清单共用它（丁组计划偏差表第 5 行），抄第二遍必漂。
ZHOUYI_SOURCE = "《周易》卦辞 · 通行本（王弼注本）公版原文"

# King Wen number -> six 爻辞 (bottom-to-top), merged from the two canons.
YAO_CI: dict[int, tuple[str, ...]] = {**YAO_CI_UPPER, **YAO_CI_LOWER}

LINES_PER_HEXAGRAM = 6
YAO_CI_COUNT = 384

_LINE_ORDINALS = {2: "二", 3: "三", 4: "四", 5: "五"}


def line_name(position: int, is_yang: bool) -> str:
    """Return the classical 爻题 (e.g. 初九, 六二, 上六) for a line.

    ``position`` is 1-6 bottom-to-top; ``is_yang`` selects 九 (yang) or 六 (yin).
    The first and last lines read 初 / 上 before the polarity; the middle four
    read polarity before the ordinal (九二 … 六五).
    """
    polarity = "九" if is_yang else "六"
    if position == 1:
        return "初" + polarity
    if position == LINES_PER_HEXAGRAM:
        return "上" + polarity
    return polarity + _LINE_ORDINALS[position]


def gua_ci(number: int) -> str:
    """Return the 卦辞 (hexagram judgment) for a King Wen number 1-64."""
    return GUA_CI[number]


def yao_ci(number: int, position: int) -> str:
    """Return the 爻辞 for a hexagram's line (position 1-6, bottom-to-top)."""
    return YAO_CI[number][position - 1]


def yong_ci(number: int) -> tuple[str, str] | None:
    """Return 乾/坤's (用九/用六) title and text, or ``None`` for other hexagrams."""
    return YONG_CI.get(number)
