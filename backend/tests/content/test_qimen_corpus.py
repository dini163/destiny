"""奇门语料表自身的不变式（Task 6 Step 3 · 轴 1 深包 B）。

这里钉的是 `app/content/qimen.py` 的**表体**，不是引擎的推导：安盘的每一个格子都取自这张
表，表上被改动一格，全仓所有奇门盘同时换宫，而**没有任何一处代码会报错**。
`tests/golden/test_qimen_golden.py` 钉的是四张手推盘的推导与环无关关系（并把值使落宫与逐宫
星门神**刻意留白**，见其模块头注与 findings F-A1-6）；本模块与之分工明确——只管表：
不重不漏、与洛书方位自洽、与歌诀逐字相符、与六十甲子可互相回推。

三处真正有牙的门：

1. **局数表逐字对拍《烟波钓叟歌》阳遁/阴遁起局歌诀**（歌诀本文抄在测试里）。一格数字被改动，
   盘面照样是一张九宫格、照样「不重不漏」，golden 那侧只钉住了四个锚点时辰，其余时辰的
   局数错了没人红——只有回到歌诀才钉得住。
2. **24 节气齐、阴阳遁各 12 且不相交**：`app/engines/qimen.py:88` 取
   `lunar.getPrevJieQi().getName()`，其定义域正是 lunar-python 给的 24 个节气名（AGENTS 第 6 条：
   历法不自算）。这一条同时是 `engines/qimen.py:91-92` 那个 `ValueError`（500，非信封）的
   可达性证明：**表全 = 分支不可达**，表缺一格它就真的会发生。
3. **八门本宫沿洛书方位恰为顺时针一周**（休北1→生东北8→伤东3→杜东南4→景南9→死西南2→
   惊西7→开西北6），而 `RING8` 是洛书数升序去中五——两者是不同的置换。本模块只把「两个环都
   是什么」写死成事实，不裁决该用哪一个（裁决记在 findings F-A1-6）。

复测本文件测数：`cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m pytest
tests/content/test_qimen_corpus.py -q` → 17 passed（2026-09-26 实录，含驿马四条参数化）。
"""

import math
from collections import Counter

import pytest
from lunar_python import Solar

from app.content import QIMEN_CONTENT_SOURCES
from app.content.qimen import (
    DIPAN_SEQUENCE,
    DOOR_BY_HOME,
    EIGHT_DOORS,
    EIGHT_GODS,
    GOD_LUCK,
    GOD_NATURE,
    JIAZI,
    JIAZI_INDEX,
    LUOSHU,
    LUOSHU_SEQ9,
    NINE_STARS,
    QIMEN_SOURCE,
    RING8,
    RING8_POS,
    SIX_YI,
    STAR_BY_HOME,
    STAR_BY_NAME,
    THREE_QI,
    XUNKONG_BY_XUNSHOU,
    XUNSHOU_INDEX_TO_YI,
    YI_TO_XUNSHOU,
    YIMA_BY_ZHI,
    YIN_JU,
    YANG_JU,
    YUAN_BY_ZHI,
    YUAN_NAMES,
    ZHI,
    gan_kind,
)
from app.content.wuxing import ELEMENT_ORDER

GAN = "甲乙丙丁戊己庚辛壬癸"

#: 九星洛书本宫（蓬1 芮2 冲3 辅4 禽5 心6 柱7 任8 英9）——手抄 classical 全表。
STAR_HOMES = {
    "天蓬": 1, "天芮": 2, "天冲": 3, "天辅": 4, "天禽": 5,
    "天心": 6, "天柱": 7, "天任": 8, "天英": 9,
}
#: 八门本宫（休1 死2 伤3 杜4 开6 惊7 生8 景9，中五无门）。
DOOR_HOMES = {
    "休门": 1, "死门": 2, "伤门": 3, "杜门": 4,
    "开门": 6, "惊门": 7, "生门": 8, "景门": 9,
}
#: 八门 classical 次序（休生伤杜景死惊开）——它与本宫表合起来应恰是方位顺时针一周。
DOOR_CLASSICAL_ORDER = ("休门", "生门", "伤门", "杜门", "景门", "死门", "惊门", "开门")
#: 洛书八方方位 → 罗盘方位角（北 0，顺时针）。用于从 LUOSHU 的 direction 字段推出地理环。
BEARING = {"北": 0, "东北": 45, "东": 90, "东南": 135, "南": 180, "西南": 225, "西": 270, "西北": 315}
#: 六冲（子午、丑未、寅申、卯酉、辰戌、巳亥）——驿马「三合局冲处」的手推依据。
CLASH = {"子": "午", "午": "子", "丑": "未", "未": "丑", "寅": "申", "申": "寅",
         "卯": "酉", "酉": "卯", "辰": "戌", "戌": "辰", "巳": "亥", "亥": "巳"}
#: 四个三合局，首支为长生（申子辰水局、亥卯未木局、寅午戌火局、巳酉丑金局）。
TRINITIES = (("申", "子", "辰"), ("亥", "卯", "未"), ("寅", "午", "戌"), ("巳", "酉", "丑"))

#: 《烟波钓叟歌》阳遁节选原文（本文逐字抄自该歌诀，用于与表逐字对拍）：
#: 冬至惊蛰一七四，小寒二八五，大寒春分三九六，立春八五二，雨水九六三，
#: 清明立夏四一七，谷雨小满五二八，芒种六三九。
YANG_JU_SONG = {
    "冬至": (1, 7, 4), "惊蛰": (1, 7, 4), "小寒": (2, 8, 5), "大寒": (3, 9, 6),
    "春分": (3, 9, 6), "立春": (8, 5, 2), "雨水": (9, 6, 3), "清明": (4, 1, 7),
    "立夏": (4, 1, 7), "谷雨": (5, 2, 8), "小满": (5, 2, 8), "芒种": (6, 3, 9),
}
#: 阴遁节选原文：夏至白露九三六，小暑八二五，大暑秋分七一四，立秋二五八，处暑一四七，
#: 立冬寒露六九三，霜降小雪五八二，大雪四七一。
YIN_JU_SONG = {
    "夏至": (9, 3, 6), "白露": (9, 3, 6), "小暑": (8, 2, 5), "大暑": (7, 1, 4),
    "秋分": (7, 1, 4), "立秋": (2, 5, 8), "处暑": (1, 4, 7), "立冬": (6, 9, 3),
    "寒露": (6, 9, 3), "霜降": (5, 8, 2), "小雪": (5, 8, 2), "大雪": (4, 7, 1),
}


def _lunar_jieqi_names() -> set[str]:
    """lunar-python 给出的 24 节气名（权威库，AGENTS 第 6 条）。

    `getJieQiTable()` 的键里除中文名外还有若干拼音键，故取「非 ASCII 键」那一份。
    """
    return set(_lunar_jieqi_order())


def _lunar_jieqi_order(*, year: int = 2024) -> tuple[str, ...]:
    """lunar-python 节气表的**时间序**：自冬至起、经小寒……至大雪，24 名一圈。

    表的键序按 Solar 时间排列，起于上一年冬至，所以取非 ASCII 键的插入序即为节气年序。
    下面两条断言把「插入序 = 年序」这个前提钉住：它一旦被库改成别的顺序，本文件由它派生的
    阴阳遁分工（`test_the_two_dun_together_cover_all_twenty_four_jieqi`）会立刻失真。
    """
    table = Solar.fromYmdHms(year, 5, 15, 10, 30, 0).getLunar().getJieQiTable()
    order = tuple(name for name in table if not name.isascii())
    assert len(order) == 24, order
    assert order[0] == "冬至" and order[1] == "小寒", order[:2]
    assert order[12] == "夏至" and order[-1] == "大雪", (order[12], order[-1])
    return order


#: 阳遁十二节气 = 年序前半（冬至→芒种），阴遁 = 后半（夏至→大雪）。从权威库的序派生，
#: 不在测试里重抄一遍表 —— 重抄的那份错了也不会红。
YANG_JU_TERMS = frozenset(_lunar_jieqi_order()[:12])
YIN_JU_TERMS = frozenset(_lunar_jieqi_order()[12:])


def test_jiazi_table_is_the_sixty_stem_branch_pairs() -> None:
    """六十甲子表：60 格不重不漏，且逐格等于天干序×地支序的配对；六旬首取自该表 0·10·…·50。"""
    assert len(JIAZI) == 60 and len(set(JIAZI)) == 60
    assert JIAZI[0] == "甲子" and JIAZI[59] == "癸亥"
    assert all(JIAZI[i] == GAN[i % 10] + ZHI[i % 12] for i in range(60))
    assert JIAZI_INDEX["甲子"] == 0 and JIAZI_INDEX["己卯"] == 15
    assert [JIAZI[i] for i in range(0, 60, 10)] == ["甲子", "甲戌", "甲申", "甲午", "甲辰", "甲寅"]


def test_ju_tables_are_word_for_word_the_yanbo_diaosou_song() -> None:
    """阳遁/阴遁局数表与《烟波钓叟歌》歌诀逐字相符，且两个节气表互不相交。

    表里 72 个数字（两遁各 12 节气 × 三元）任何一个被改动都不会让引擎报错——它照样按
    `triple[yuan]` 取到一个 1-9 的局数，照样排出满盘，只是那张盘的局从头到尾是错的。
    """
    assert YANG_JU == YANG_JU_SONG
    assert YIN_JU == YIN_JU_SONG
    assert not (set(YANG_JU) & set(YIN_JU))


def test_the_two_dun_together_cover_all_twenty_four_jieqi() -> None:
    """阴阳遁各 12 节气、逐名点到，合起来恰是 lunar-python 的 24 节气名，一格不缺不多。

    这条同时是 `engines/qimen.py:91-92` 那个 `raise ValueError`（未映射到信封，会成 500）的
    可达性证明：`getPrevJieQi().getName()` 的值域就是这张 24 名的表，表全则分支永不可达。
    覆盖必须**逐名**断言而不是只数到 24 —— 数数放行的是「少一个节气、另一个节气多一格」这类
    错位，而那正是让引擎走进裸 `ValueError` 的形状。
    """
    authority = _lunar_jieqi_names()
    assert len(authority) == 24, sorted(authority)
    assert set(YANG_JU) == YANG_JU_TERMS, sorted(set(YANG_JU) ^ YANG_JU_TERMS)
    assert set(YIN_JU) == YIN_JU_TERMS, sorted(set(YIN_JU) ^ YIN_JU_TERMS)
    assert not (set(YANG_JU) & set(YIN_JU))
    assert set(YANG_JU) | set(YIN_JU) == authority
    assert len(YANG_JU) == len(YIN_JU) == 12


def test_every_jieqi_triple_is_the_yuan_progression_of_its_shangyuan_ju() -> None:
    """每个节气的三元局数由上元局数唯一决定：阳遁顺行 +6/+3，阴遁逆行 -6/-3（洛书九宫回环）。

    拆补法按日干支符头取上/中/下元，引擎只做 `triple[yuan]` 一次索引；若某格被改成不落在该
    节气所属元序上（例如把「雨水」的中元从 6 改成 1），表仍满 24 格、局数仍在 1–9 内，任何
    逐格断言都放行 —— 只有「三元之间 must 差 3/6 步」这条结构性关系抓得住它。
    """
    for jieqi, (upper, middle, lower) in YANG_JU.items():
        assert middle == (upper - 1 + 6) % 9 + 1, (jieqi, upper, middle)
        assert lower == (upper - 1 + 3) % 9 + 1, (jieqi, upper, lower)
    for jieqi, (upper, middle, lower) in YIN_JU.items():
        assert middle == (upper - 1 - 6) % 9 + 1, (jieqi, upper, middle)
        assert lower == (upper - 1 - 3) % 9 + 1, (jieqi, upper, lower)


def test_the_eighteen_ju_are_complete_and_well_formed() -> None:
    """阴阳遁各 9 局（共 18 局）齐：每遁用到的局数恰是 1-9；每个节气的三元局数互不相同。"""
    assert sorted({n for triple in YANG_JU.values() for n in triple}) == list(range(1, 10))
    assert sorted({n for triple in YIN_JU.values() for n in triple}) == list(range(1, 10))
    for label, table in (("阳遁", YANG_JU), ("阴遁", YIN_JU)):
        for jieqi, triple in table.items():
            assert len(set(triple)) == 3, (label, jieqi, triple)
            assert all(1 <= n <= 9 for n in triple), (label, jieqi, triple)


def test_yuan_by_branch_is_three_groups_of_four() -> None:
    """拆补法符头：12 支齐，子午卯酉上元、寅申巳亥中元、辰戌丑未下元——每元恰四支。"""
    assert set(YUAN_BY_ZHI) == set(ZHI)
    assert YUAN_NAMES == ("上元", "中元", "下元")
    groups = {
        index: {z for z in ZHI if YUAN_BY_ZHI[z] == index}
        for index in range(len(YUAN_NAMES))
    }
    assert groups == {0: set("子午卯酉"), 1: set("寅申巳亥"), 2: set("辰戌丑未")}
    assert all(len(members) == 4 for members in groups.values())


def test_loshu_palaces_fill_the_grid_and_hold_the_branches_once_each() -> None:
    """洛书九宫：宫号 1-9 各一次、3×3 九格各一次、八宫纳支合起来恰是十二支各一次（中宫无支）。"""
    assert sorted(LUOSHU) == list(range(1, 10))
    assert {(p.row, p.col) for p in LUOSHU.values()} == {(r, c) for r in range(3) for c in range(3)}
    assert sorted(p.number for p in LUOSHU.values() if p.row == 1 and p.col == 1) == [5]
    assert LUOSHU[5].gua == "中" and LUOSHU[5].zhi == "" and LUOSHU[5].direction == "中宫"
    assert len({p.gua for p in LUOSHU.values()}) == 9
    assert Counter("".join(p.zhi for p in LUOSHU.values())) == Counter(ZHI)
    for palace in LUOSHU.values():
        assert palace.element in ELEMENT_ORDER, palace.number
        assert palace.gua != palace.direction
        assert set(palace.zhi) <= set(ZHI)


def test_the_two_rings_are_different_permutations() -> None:
    """地理环（洛书八方按方位角顺时针）与 `RING8`（洛书数升序去中五）不是同一个置换。

    这是 findings F-A1-6 的表级事实陈述：`SCHOOL_NOTE` 声明转盘法（整盘刚体旋转），刚体旋转
    只能沿地理环；`RING8` 在 3×3 网格里是九宫飞布的轨迹。本测不裁决用哪一环（golden 因此
    刻意不钉逐宫门/星/神的宫号），只钉死「两个环各是什么、且彼此不同」——任何一方被悄悄
    改成另一方时，本测与 golden 的注释会同时失真。
    """
    assert LUOSHU_SEQ9 == tuple(range(1, 10))
    assert RING8 == tuple(n for n in LUOSHU_SEQ9 if n != 5)
    assert RING8_POS == {n: i for i, n in enumerate(RING8)}
    geographic = tuple(
        sorted((p for p in LUOSHU if p != 5), key=lambda p: BEARING[LUOSHU[p].direction])
    )
    assert geographic == (1, 8, 3, 4, 9, 2, 7, 6)
    assert [LUOSHU[n].direction for n in geographic] == \
        ["北", "东北", "东", "东南", "南", "西南", "西", "西北"]
    # 顺时针一周：相邻两宫在 3×3 网格里必相邻（含斜邻），且首尾相接成环。
    for index, palace in enumerate(geographic):
        nxt = geographic[(index + 1) % 8]
        assert max(abs(LUOSHU[palace].row - LUOSHU[nxt].row),
                   abs(LUOSHU[palace].col - LUOSHU[nxt].col)) == 1, (palace, nxt)
    assert RING8 != geographic
    # 两环的置换距离非零的具体证据：第三个元素起就分家（3 东 vs 4 东南）。
    assert list(RING8)[:3] == [1, 2, 3] and list(geographic)[:3] == [1, 8, 3]


def test_the_nine_stars_are_one_per_luoshu_home() -> None:
    """九星不重不漏：九名、九宫本宫各一次，星五行即本宫五行（蓬水芮土…英火）。"""
    assert len(NINE_STARS) == 9 and len({s.name for s in NINE_STARS}) == 9
    assert {s.name: s.home for s in NINE_STARS} == STAR_HOMES
    assert sorted(s.home for s in NINE_STARS) == list(range(1, 10))
    for star in NINE_STARS:
        assert star.element == LUOSHU[star.home].element, star.name
        assert star.luck in {"吉", "凶", "中平"}, star.name
        assert star.nature and "·" in star.nature, star.name
    assert set(STAR_BY_HOME) == set(range(1, 10))
    assert set(STAR_BY_NAME) == {s.name for s in NINE_STARS}
    assert STAR_BY_HOME[5].name == "天禽" and STAR_BY_NAME["天禽"].home == 5


def test_the_eight_doors_are_one_per_direction_and_never_the_center() -> None:
    """八门不重不漏：八名、八本宫（1-9 除中五），门五行即本宫五行，且本宫沿地理环恰为顺时针一周。"""
    assert len(EIGHT_DOORS) == 8 and len({d.name for d in EIGHT_DOORS}) == 8
    assert {d.name: d.home for d in EIGHT_DOORS} == DOOR_HOMES
    assert set(DOOR_BY_HOME) == set(RING8) and 5 not in DOOR_BY_HOME
    for door in EIGHT_DOORS:
        assert door.element == LUOSHU[door.home].element, door.name
        assert door.luck in {"吉", "凶", "中平"}, door.name
        assert door.nature and "·" in door.nature, door.name
    # classical 次序（休生伤杜景死惊开）落成本宫，就是地理环——「八门本宫即环」的自证。
    by_name = {d.name: d for d in EIGHT_DOORS}
    assert tuple(by_name[name].home for name in DOOR_CLASSICAL_ORDER) == \
        (1, 8, 3, 4, 9, 2, 7, 6)
    assert {d.luck for d in EIGHT_DOORS} == {"吉", "凶", "中平"}


def test_the_eight_gods_are_named_luck_bearing_and_nature_bearing() -> None:
    """八神不重不漏：八将各一，吉凶表与类象表都以这八名为键，值符居首（阳遁顺布起点）。"""
    assert len(EIGHT_GODS) == 8 and len(set(EIGHT_GODS)) == 8
    assert EIGHT_GODS[0] == "值符"
    assert set(GOD_LUCK) == set(EIGHT_GODS) and set(GOD_NATURE) == set(EIGHT_GODS)
    assert set(GOD_LUCK.values()) == {"吉", "凶"}
    for god in EIGHT_GODS:
        assert GOD_NATURE[god] and "·" in GOD_NATURE[god], god
    assert Counter(GOD_LUCK.values()) == {"吉": 5, "凶": 3}


def test_the_corpus_is_registered_under_one_book_level_source() -> None:
    """奇门语料只登一张表、署名即 `QIMEN_SOURCE`；**这是登记表自身的形状，不是 §7 已合规**。

    AGENTS 第 7 条要的是「响应里披露实际读过的表」，而这条清单目前**没有消费者**：
    `grep -rn QIMEN_CONTENT_SOURCES app/` 只命中 `app/content/__init__.py:128` 的定义处（13 张
    清单里 8 张被引擎读了并渲染进响应的 `provenance.tables`，`QIMEN_`/`ZIWEI_`/`KABBALAH_`/
    `LENORMAND_`/`VEDIC_` 五张是零引用的死登记），`QimenProvenance` 也还没有 `tables` 字段
    （`app/schemas/qimen.py`）。所以本测钉的是「登记了什么、登记得对不对」（多登、漏登、署名
    漂移都会红），别把它读成出处已经到用户手上 —— 那半步记为 findings F-A2-9，梅花的全缺是
    同一条机制的另一半。
    """
    assert QIMEN_CONTENT_SOURCES == (("qimen", QIMEN_SOURCE),)
    assert "烟波钓叟歌" in QIMEN_SOURCE


def test_dipan_sequence_is_six_yi_followed_by_three_qi_and_never_jia() -> None:
    """地盘布干次序：六仪（戊己庚辛壬癸）毕而三奇（丁丙乙），盘上不见甲（甲遁于六仪）。"""
    assert DIPAN_SEQUENCE == ("戊", "己", "庚", "辛", "壬", "癸", "丁", "丙", "乙")
    assert len(set(DIPAN_SEQUENCE)) == 9
    assert set(DIPAN_SEQUENCE) == SIX_YI | set(THREE_QI)
    assert "甲" not in DIPAN_SEQUENCE
    assert set(THREE_QI.values()) == {"日奇", "月奇", "星奇"}
    assert [gan_kind(g) for g in DIPAN_SEQUENCE] == ["六仪"] * 6 + ["三奇"] * 3


def test_xunshou_hides_in_the_six_yi_and_the_xunkong_is_the_pair_the_xun_lacks() -> None:
    """旬首↔遁仪双射，且每旬的旬空就是该旬十个干支里没出现的那两支（由六十甲子表回推）。

    旬空被写错一格，盘上「空亡宫」会整体错位，而引擎照算不误——golden 只在四个锚点上钉住了
    四条结论，这里钉的是全部六旬。
    """
    assert {YI_TO_XUNSHOU[yi] for yi in SIX_YI} == {JIAZI[i] for i in range(0, 60, 10)}
    assert set(XUNSHOU_INDEX_TO_YI) == set(range(0, 60, 10))
    assert set(XUNSHOU_INDEX_TO_YI.values()) == SIX_YI
    for index, yi in XUNSHOU_INDEX_TO_YI.items():
        assert YI_TO_XUNSHOU[yi] == JIAZI[index], (index, yi)
        branches_in_xun = {gz[1] for gz in JIAZI[index:index + 10]}
        missing = "".join(z for z in ZHI if z not in branches_in_xun)
        assert len(branches_in_xun) == 10, index
        assert XUNKONG_BY_XUNSHOU[index] == missing, (JIAZI[index], missing)


@pytest.mark.parametrize("group", TRINITIES, ids=["".join(g) for g in TRINITIES])
def test_yima_is_the_clash_of_the_trinity_long_sheng(group: tuple[str, ...]) -> None:
    """驿马：三合局（申子辰/亥卯未/寅午戌/巳酉丑）之马在其长生支的对冲（寅巳申亥）。"""
    head, *others = group
    expected = CLASH[head]
    assert expected in "寅巳申亥"
    for branch in group:
        assert YIMA_BY_ZHI[branch] == expected, (branch, group)
    # 同局三支确实同马，而三支之外的支另有其马 —— 防的是「整表填同一个值」这种看着自洽的错。
    assert len({YIMA_BY_ZHI[b] for b in ZHI if b not in group}) > 1, group
    assert len(others) == 2, group


def test_yima_covers_every_branch_once() -> None:
    """十二支各有驿马、不重不漏；表的键集与权威地支表逐一对齐。"""
    assert sorted(YIMA_BY_ZHI) == sorted(ZHI)
    assert set(YIMA_BY_ZHI.values()) == set("寅巳申亥")
