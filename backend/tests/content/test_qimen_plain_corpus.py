"""奇门白话转述表：工厂看不到的那六件事（多系统白话 spec §8 丙组、§11）。

① 登记身份（R24）；② `universe()` 的构成 9+8+8=25，且星/门/神三批名字互不相同
   （撞名会撞键，条数照旧 25，工厂照样绿——紫微侧同一条测的先例）；③ 小节覆盖面
   `set(openers) == {LUOSHU[n].gua}`（R31：漏一宫就少一段开篇句）；④ 转述对账（G14）：
   `nature` 逐字 + `element`（星/门）+ `home` 的汉字序数；⑤ 取向词反向对账（G24）：
   源表的 `luck` 值（吉/凶/中平）不得出现在白话里——奇门是三家里唯一「源表字段本身
   就是取向词」的，所以这条只在奇门测里钉；⑥ 中宫那句「不坐星、不配门也不配神」
   的上游凭据（`SCHOOL_NOTE`，G14 不许白话替学派新增前提）。
"""

from app.content.qimen import EIGHT_DOORS, EIGHT_GODS, GOD_NATURE, LUOSHU, NINE_STARS
from app.content.qimen_plain import (
    QIMEN_PALACE_OPENERS,
    QIMEN_PLAIN_SOURCE,
    QIMEN_READINGS,
    door_key,
    god_key,
    star_key,
)
from app.engines.plain_corpora import PLAIN_CORPORA, QIMEN
from app.engines.qimen import SCHOOL_NOTE
from app.engines.plain_compose import reading
from tests.plain_wording import NON_ADVICE_FORMS, advice_hits

#: 源表用汉字序数写本位（`本位居一` / `本位在一宫`），汉字表就是 `engines/qimen.py:236`
#: 的 `_CN`（1-9），此处独立写死是因为测试不许反向 import 引擎的私物。
_CN = "一二三四五六七八九"

#: 同 `tests/content/test_ziwei_plain_corpus.py` 的 `_NATURE_SKIP`：`nature` 是
#: 「贪狼·暗昧盗贼」这种两段暗号，分隔符与取向字本来就不进白话（G24），
#: 逐字对账时一并跳过，剩下的每个字都必须出现在句子里。
_NATURE_SKIP: frozenset[str] = frozenset("吉凶宜忌需应·、（）")


def _missing_chars(source: str, text: str) -> list[str]:
    return sorted({c for c in source if c not in _NATURE_SKIP and c not in text})


def test_qimen_corpus_is_the_row_the_factory_iterates() -> None:
    assert PLAIN_CORPORA["qimen"] is QIMEN
    # G3：奇门只逐宫说话，盘面没有分数，收尾结论不许由合成器补。
    assert QIMEN.closers is None
    # 偏差表第 1 行：`LUOSHU` 九宫没有 luck 字段，`EIGHT_DOORS` 两条是「中平」，
    # `band` 分支遇 0 值直接 `ValueError`（`plain_compose.py:65-67`）→ 只准 `keep`。
    assert QIMEN.grouping == "keep"
    assert QIMEN.slot_prefixes == frozenset()


def test_universe_is_nine_stars_plus_eight_doors_plus_eight_gods() -> None:
    assert (len(NINE_STARS), len(EIGHT_DOORS), len(EIGHT_GODS)) == (9, 8, 8)
    assert QIMEN.universe() == (
        {star_key(star.name) for star in NINE_STARS}
        | {door_key(door.name) for door in EIGHT_DOORS}
        | {god_key(god) for god in EIGHT_GODS}
    )
    assert len(QIMEN.universe()) == 25
    # 三批名字互不相同：撞名会撞掉一个键而条数不变（紫微侧同病同治）。
    names = [{star.name for star in NINE_STARS}, {d.name for d in EIGHT_DOORS}, set(EIGHT_GODS)]
    for i in range(3):
        for j in range(i + 1, 3):
            assert not (names[i] & names[j]), (i, j, names[i] & names[j])


def test_openers_are_exactly_the_nine_luoshu_gua() -> None:
    """R31：小节名单就是九宫的卦名（含中宫的 `中`），一个不多一个不少。"""
    assert set(QIMEN_PALACE_OPENERS) == {meta.gua for meta in LUOSHU.values()}
    assert set(QIMEN.openers) == {meta.gua for meta in LUOSHU.values()}
    assert len(QIMEN.openers) == 9


def test_each_palace_opener_carries_its_own_luoshu_row() -> None:
    """G14 的开篇句半边：卦名、洛书数、宫五行、所纳地支四样都在句子里。

    方位（`direction`）不钉：`LUOSHU` 写「南」而句子写「正南」、中宫写「中宫」而句子
    讲「正中央」，那是措辞不是漏项，钉它会逼出一张没必要的别名表。
    """
    for number, meta in sorted(LUOSHU.items()):
        text = QIMEN_PALACE_OPENERS[meta.gua]
        assert meta.gua in text, (number, "gua")
        assert _CN[number - 1] in text, (number, "洛书数")
        assert f"属{meta.element}" in text, (number, "element")
        if meta.zhi:
            assert meta.zhi in text, (number, "zhi")


def test_the_center_palace_opener_declares_the_ji_gong_rule() -> None:
    """中宫那句说「不坐星、不配门也不配神」，这句话的上游是学派注，不是本表自造（G14）。"""
    assert "不坐星" in QIMEN_PALACE_OPENERS["中"]
    assert "中五宫无门无神" in SCHOOL_NOTE
    assert "天禽星与中宫地盘干寄坤二宫" in SCHOOL_NOTE
    assert "寄在坤二宫" in QIMEN_READINGS[star_key("天禽")]


def test_every_star_door_and_god_key_resolves_through_the_assembler() -> None:
    for key in sorted(QIMEN.universe()):
        assert reading(QIMEN, key) == QIMEN_READINGS[key]


def test_every_retelling_carries_its_rows_nature_element_and_home() -> None:
    """G14 的落点：`nature` 逐字搬进来；星/门另报五行与本位洛书数。

    八神在源表里只有 `name/luck/nature`（`content/qimen.py:110-123` 是两张 dict，
    没有 `element`/`home` 列），所以对神只查 `nature` 一件事——多查就是造假字段。
    """
    for star in NINE_STARS:
        text = QIMEN_READINGS[star_key(star.name)]
        assert _missing_chars(star.nature, text) == [], (star.name, star.nature)
        assert f"属{star.element}" in text, (star.name, "element")
        assert f"本位居{_CN[star.home - 1]}" in text, (star.name, "home")
    for door in EIGHT_DOORS:
        text = QIMEN_READINGS[door_key(door.name)]
        assert _missing_chars(door.nature, text) == [], (door.name, door.nature)
        assert f"属{door.element}" in text, (door.name, "element")
        assert f"本位在{_CN[door.home - 1]}宫" in text, (door.name, "home")
    for god in EIGHT_GODS:
        assert _missing_chars(GOD_NATURE[god], QIMEN_READINGS[god_key(god)]) == [], god


def test_no_retelling_borrows_the_source_tables_orientation_word() -> None:
    """G24 的反向半边：源表的 `luck` 值一个字都不进白话（页面照旧在 tooltip 里印它）。

    复测（2026-10-01 草稿全表实跑）：25 条抹 `NON_ADVICE_FORMS` 后命中 `[]`，
    而九星句里那个「应」字全部来自「对应」这一具名词形；不抹时命中 9 条 `应`。
    """
    for star in NINE_STARS:
        text = QIMEN_READINGS[star_key(star.name)]
        assert star.luck not in text, (star.name, star.luck)
        assert advice_hits(text) == [], star.name
    for door in EIGHT_DOORS:
        text = QIMEN_READINGS[door_key(door.name)]
        assert door.luck not in text, (door.name, door.luck)
        assert advice_hits(text) == [], door.name
    for god in EIGHT_GODS:
        text = QIMEN_READINGS[god_key(god)]
        assert advice_hits(text) == [], (god, advice_hits(text))
    for gua, text in sorted(QIMEN_PALACE_OPENERS.items()):
        assert advice_hits(text) == [], (gua, advice_hits(text))


def test_source_line_names_all_three_tables_it_retells() -> None:
    from tests.plain_wording import FORBIDDEN

    assert QIMEN_PLAIN_SOURCE.startswith("本系统白话转述")
    for token in FORBIDDEN:
        assert token not in QIMEN_PLAIN_SOURCE, token
    # 奇门 25 条**全部有上游字段**（星 `nature`、门 `nature`、神 `GOD_NATURE`），
    # 所以串里不许出现「自持」——写了就是虚报取材范围（对照紫微那条相反的要求）。
    assert "自持" not in QIMEN_PLAIN_SOURCE
    assert "九星" in QIMEN_PLAIN_SOURCE and "八门" in QIMEN_PLAIN_SOURCE and "八神" in QIMEN_PLAIN_SOURCE
