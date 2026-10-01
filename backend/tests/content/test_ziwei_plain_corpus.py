"""紫微白话转述表：工厂看不到的那五件事（多系统白话 spec §8 丙组、§11）。

① 登记身份（R24：`PLAIN_CORPORA` 是同键字面量字典，两行 `ziwei` 会静默留后一条，
   前一张表就此掉出机检闸外）；② `universe()` 由三张源表现算的构成（工厂只验它
   可复现且非空，验不出「乙级 14 与主星 14 不是同一批星」）；③ 小节覆盖面 `set(openers)
   == set(PALACE_NAMES)`（R31：工厂只验 openers 非空，漏一个宫就有一宫只剩星句）；
④ 转述对账（G14）：主星句必须把 `nature` 的字逐个搬进来、把 `element`/`yin_yang`/
   `group` 三样写实；⑤ 结论词整表扫（G24：白话比卡巴拉口径更严，六字全禁，
   只准抹具名的四化名相）。
"""

from app.content.ziwei import MAJOR_STARS, MINOR_STARS, PALACE_NAMES, SIHUA_LABELS
from app.content.ziwei_plain import (
    ZIWEI_PALACE_OPENERS,
    ZIWEI_PLAIN_SOURCE,
    ZIWEI_READINGS,
    sihua_key,
    star_key,
)
from app.engines.plain_compose import reading
from app.engines.plain_corpora import PLAIN_CORPORA, ZIWEI
from tests.plain_wording import NON_ADVICE_FORMS, advice_hits

#: 四化名相是本表唯一需要抹除的词形：`化忌` 里那个「忌」是名相的一部分，不是建议
#: （G24 的具名登记）。除它以外一个字都不放宽——草稿全表实测不需要第二条（复测见
#: `test_no_retelling_adds_an_orientation_the_star_table_lacks`）。
SIHUA_FORMS: tuple[str, ...] = ("化禄", "化权", "化科", "化忌")

#: 乙级星在正表里没有 `nature` 字段（`content/ziwei.py:86-91` 只有 name/element/kind），
#: 盘面 tooltip 今天是 `${kind}·${element}`（`ZiweiChartGrid.tsx:88`），也就是「吉·金」这种
#: 两字暗号。白话把 `kind` 写成能读的一类话，映射唯一，所以在此钉死而不是靠读者核对。
KIND_PHRASE: dict[str, str] = {"吉": "助力", "煞": "煞星", "禄马": "禄马"}

#: 源表用汉字序数的只有奇门（`本位居一`），紫微此处只用到 1..9 的汉字，写在测里当转写表。
_NATURE_SKIP: frozenset[str] = frozenset("吉凶宜忌需应·、（）")


def _missing_chars(source: str, text: str) -> list[str]:
    """`source` 里每个非结论词、非标点的字都必须在 `text` 出现（G14 的机器半边）。"""
    return sorted({c for c in source if c not in _NATURE_SKIP and c not in text})


def test_ziwei_corpus_is_the_row_the_factory_iterates() -> None:
    assert PLAIN_CORPORA["ziwei"] is ZIWEI
    # G3：斗数整盘无分数，收尾结论不许由合成器补（`compose()` 传 tier 必 ValueError）。
    assert ZIWEI.closers is None
    # G21：`band` 分支遇 0 值符号直接崩，而斗数没有任何符号可传——次序由宫位序决定。
    assert ZIWEI.grouping == "keep"
    # 偏差表第 7 行：本计划不用 `compose_template`，三家都没有槽位键空间。
    assert ZIWEI.slot_prefixes == frozenset()


def test_universe_is_fourteen_major_plus_fourteen_minor_plus_four_sihua() -> None:
    assert len(MAJOR_STARS) == 14 and len(MINOR_STARS) == 14
    assert ZIWEI.universe() == (
        {f"ziwei.star.{name}" for name in MAJOR_STARS}
        | {f"ziwei.star.{name}" for name in MINOR_STARS}
        | {f"ziwei.sihua.{label}" for label in SIHUA_LABELS}
    )
    assert len(ZIWEI.universe()) == 32
    # 主星与乙级不得有同名星：有的话键集会撞掉一格而条数不变，工厂照样绿。
    assert not (set(MAJOR_STARS) & set(MINOR_STARS))


def test_openers_are_exactly_the_twelve_palace_names() -> None:
    """R31：小节名单就是 `PALACE_NAMES`，一个不多一个不少（漏一个宫=那一宫只剩星句）。"""
    assert set(ZIWEI_PALACE_OPENERS) == set(PALACE_NAMES)
    assert set(ZIWEI.openers) == set(PALACE_NAMES)


def test_every_star_and_sihua_key_resolves_through_the_assembler() -> None:
    for key in sorted(ZIWEI.universe()):
        assert reading(ZIWEI, key) == ZIWEI_READINGS[key]


def test_each_major_retelling_carries_every_field_its_row_has() -> None:
    """G14 的落点：`nature` 逐字 + `element` + `yin_yang` + `group`，四样都在句子里。

    「转述不越权」的正半边是「转述不缺件」：只钉禁字表会放过一句空泛的好话（「这颗星
    很有特点」四条口径全绿），而它对用户的价值恰好是零——本期存在的理由就是把
    「帝座·尊贵领导」摊开成一句人话。
    """
    for name, star in sorted(MAJOR_STARS.items()):
        text = ZIWEI_READINGS[star_key(name)]
        assert _missing_chars(star.nature, text) == [], (name, "nature", _missing_chars(star.nature, text))
        assert f"属{star.element}" in text, (name, "element")
        assert f"{star.yin_yang}性" in text, (name, "yin_yang")
        assert f"{star.group[:-1]}这一系" in text, (name, "group")


def test_each_minor_retelling_carries_its_element_and_kind() -> None:
    for name, star in sorted(MINOR_STARS.items()):
        text = ZIWEI_READINGS[star_key(name)]
        assert f"属{star.element}" in text, (name, "element")
        assert KIND_PHRASE[star.kind] in text, (name, "kind", star.kind)


def test_no_retelling_adds_an_orientation_the_star_table_lacks() -> None:
    """G24：六字表整表扫；紫微侧唯一的词形豁免是四化名相本身。

    复测（2026-10-01 草稿全表实跑，`PYTHONIOENCODING=utf-8` + 同一口径）：
    主星/乙级/四化 32 条抹 `SIHUA_FORMS` 后命中 `[]`；12 宫开篇句不抹任何词形也是 `[]`；
    不抹词形时唯一的命中是 `('化忌', '忌')`。
    """
    masks = (*NON_ADVICE_FORMS, *SIHUA_FORMS)
    for key, text in sorted(ZIWEI_READINGS.items()):
        assert advice_hits(text, masks=masks) == [], (key, advice_hits(text, masks=masks))
    for palace, text in sorted(ZIWEI_PALACE_OPENERS.items()):
        assert advice_hits(text) == [], (palace, advice_hits(text))


def test_source_line_declares_which_rows_are_self_held() -> None:
    """出处诚实性（AGENTS §7）：乙级类象与四化词义没有上游字段，出处串必须自己说清。"""
    from tests.plain_wording import FORBIDDEN

    assert ZIWEI_PLAIN_SOURCE.startswith("本系统白话转述")
    assert "自持" in ZIWEI_PLAIN_SOURCE, "乙级类象/四化词义属自持词表，串里不写就是冒充源表转述"
    for token in FORBIDDEN:
        assert token not in ZIWEI_PLAIN_SOURCE, token
