"""紫微安星表的不变式（Task 5 Step 3 · 轴 1 深包 A）。

这里锁的是「安星手册的表本身」，不是引擎的推导：引擎（`app/engines/ziwei.py`）只读这些表，
表上任何一个格子被改动，全仓所有紫微盘就同时换了星位，而**没有任何一处代码会报错**。
故本轮把表的形状钉死，复推链条与《全书》歌诀一并抄在测试里（各持一端的理由见
`tests/content/test_rune_corpora.py` 头注：只抄一份，改动者与抄写者同时错掉才没人红）。

四道真正有牙的门：

1. **十四主星齐**（名字、五行、星系归属）——漏一颗，那一张盘就少一个星情，且
   `test_twelve_palaces_are_well_formed`（golden）那条「14 颗各落一次」会因为
   引擎只排 13 颗而**照样绿**（它是数出来的，不是对齐表的）。
2. **四化表 10 干 × 4 化无空洞**，且与四化诀逐字相符——一格被抹平或填错，
   页面拿到的是「太阳化禄」与「武曲化禄」两种互斥的命读，而 JSON 上无从看出。
3. **十二宫地支固定序 + 宫名序**——宫序一乱，十二个宫名整体错位，每一宫的名字都在骗人。
4. **五行局的局数与局名**——局数就是起运虚岁，中文数字写错一位，页面上的局名与十二段
   大限当场对不上；**区间的无缝/不重叠不在这条里**（表里没有区间，区间由引擎按局数摊出），
   它住在 golden 的扫盘条，五局各有实盘。

外加一条最狠的 `test_major_star_pairings_match_the_classical_combo_table`：把两条 offset
序列在寅申轴镜像下摊成 12 张盘，逐对主星同宫落宫与《全书》通行「双星同宫」表逐字比对。
这一条同时锁住了紫微系六个间隔、天府系八个间隔、以及十四星的名字集合 —— 改动其中
任何一格，那一对（或那几对）同宫关系当场改名。
"""

import pytest

from app.content.ziwei import (
    GAN,
    GAN_INDEX,
    HUOXING_BASE,
    LINGXING_BASE,
    LUCUN_BY_YEAR_GAN,
    MAJOR_STARS,
    MINOR_STARS,
    MING_ZHU,
    PALACE_NAMES,
    SHEN_ZHU,
    SIHUA,
    SIHUA_LABELS,
    TIANFU_SERIES,
    TIANKUI_TIANYUE,
    TIANMA_BY_YEAR_ZHI,
    WUXING_JU,
    YIN_GAN_BY_YEAR_GAN,
    ZHI,
    ZHI_INDEX,
    ZIWEI_SERIES,
    ZIWEI_SOURCE,
)

# ---------------------------------------------------------------- 独立抄写的锚
# 以下每一份都是**照安星手册重抄**的常量，故意不从 `app.content.ziwei` 派生。

#: 十四主星（紫微系六 + 天府系八），安星手册的排列表序。
CLASSICAL_MAJOR_STARS: tuple[str, ...] = (
    "紫微", "天机", "太阳", "武曲", "天同", "廉贞",
    "天府", "太阴", "贪狼", "巨门", "天相", "天梁", "七杀", "破军",
)

#: 十四主星五行（《全书》星曜五行：紫微土、天机木、太阳火、武曲金、天同水、廉贞火、
#: 天府土、太阴水、贪狼木、巨门水、天相水、天梁土、七杀金、破军水）。
CLASSICAL_MAJOR_ELEMENTS: dict[str, str] = {
    "紫微": "土", "天机": "木", "太阳": "火", "武曲": "金", "天同": "水", "廉贞": "火",
    "天府": "土", "太阴": "水", "贪狼": "木", "巨门": "水", "天相": "水", "天梁": "土",
    "七杀": "金", "破军": "水",
}

#: 星系归属：紫微系六星逆布、天府系八星顺布（斗数通例，安星诀的第一句就是这个分野）。
CLASSICAL_ZIWEI_GROUP: frozenset[str] = frozenset({"紫微", "天机", "太阳", "武曲", "天同", "廉贞"})
CLASSICAL_TIANFU_GROUP: frozenset[str] = frozenset(
    {"天府", "太阴", "贪狼", "巨门", "天相", "天梁", "七杀", "破军"}
)

#: 紫微系自紫微**逆行**所退宫数：天机退一、隔一宫太阳、连退至武曲天同、隔二宫廉贞。
CLASSICAL_ZIWEI_OFFSETS: tuple[int, ...] = (0, -1, -3, -4, -5, -8)

#: 天府系自天府**顺行**所进宫数：天府→七杀连排六宫，再进四宫落破军（中隔三宫）。
CLASSICAL_TIANFU_OFFSETS: tuple[int, ...] = (0, 1, 2, 3, 4, 5, 6, 10)

#: 两系各自的安星顺序（安星诀是「紫微→天机→空一→太阳→……」这样的口述序列，
#: 名字与 offset 是一对一绑死的；换序等于换表）。
CLASSICAL_ZIWEI_SERIES_ORDER: tuple[str, ...] = (
    "紫微", "天机", "太阳", "武曲", "天同", "廉贞",
)
CLASSICAL_TIANFU_SERIES_ORDER: tuple[str, ...] = (
    "天府", "太阴", "贪狼", "巨门", "天相", "天梁", "七杀", "破军",
)

#: 生年四化诀（全书派）每干一句「禄权科忌」四字：甲廉破武阳、乙机梁紫阴、丙同机昌廉、
#: 丁阴同机巨、戊贪阴弼机、己武贪梁曲、庚阳武阴同、辛巨阳曲昌、壬梁紫辅武、癸破巨阴贪。
#: 星名以单字记（阳=太阳、阴=太阴、昌=文昌、曲=文曲、弼=右弼、辅=左辅），展开成全名比对。
CLASSICAL_SIHUA_JUE: dict[str, tuple[str, str, str, str]] = {
    "甲": ("廉贞", "破军", "武曲", "太阳"),
    "乙": ("天机", "天梁", "紫微", "太阴"),
    "丙": ("天同", "天机", "文昌", "廉贞"),
    "丁": ("太阴", "天同", "天机", "巨门"),
    "戊": ("贪狼", "太阴", "右弼", "天机"),
    "己": ("武曲", "贪狼", "天梁", "文曲"),
    "庚": ("太阳", "武曲", "太阴", "天同"),
    "辛": ("巨门", "太阳", "文曲", "文昌"),
    "壬": ("天梁", "紫微", "左辅", "武曲"),
    "癸": ("破军", "巨门", "太阴", "贪狼"),
}

#: 十二宫自命宫**逆布**的宫名序（迁移恒在命宫对宫，即第六位）。
CLASSICAL_PALACE_NAMES: tuple[str, ...] = (
    "命宫", "兄弟", "夫妻", "子女", "财帛", "疾厄",
    "迁移", "仆役", "官禄", "田宅", "福德", "父母",
)

#: 局数的中文数字（手册写「水二局、木三局、金四局、土五局、火六局」，不是「水2局」）。
CLASSICAL_JU_CN_NUMBERS: dict[int, str] = {2: "二", 3: "三", 4: "四", 5: "五", 6: "六"}

#: 纳音五行 → (局数, 局名)：水二、木三、金四、土五、火六。局数即大限起运虚岁。
CLASSICAL_WUXING_JU: dict[str, tuple[int, str]] = {
    "水": (2, "水二局"), "木": (3, "木三局"), "金": (4, "金四局"),
    "土": (5, "土五局"), "火": (6, "火六局"),
}

#: 五虎遁年上起月歌：「甲己之年丙作首，乙庚之岁戊为头，丙辛必定寻庚起，丁壬壬位顺行流，
#: 更有戊癸何方觅，甲寅之上好追求。」—— 五组年干各自定下寅宫（正月）天干。
CLASSICAL_WUHU_DUN: dict[str, str] = {
    "甲": "丙", "己": "丙", "乙": "戊", "庚": "戊", "丙": "庚", "辛": "庚",
    "丁": "壬", "壬": "壬", "戊": "甲", "癸": "甲",
}

#: 禄存（十干临官禄位）：甲寅、乙卯、丙巳、丁午、戊巳、己午、庚申、辛酉、壬亥、癸子。
CLASSICAL_LUCUN: dict[str, str] = {
    "甲": "寅", "乙": "卯", "丙": "巳", "丁": "午", "戊": "巳",
    "己": "午", "庚": "申", "辛": "酉", "壬": "亥", "癸": "子",
}

#: 天乙贵人歌「甲戊庚牛羊，乙己鼠猴乡，丙丁猪鸡位，壬癸兔蛇藏，六辛逢马虎」，
#: 前支阳贵（天魁）、后支阴贵（天钺）。
CLASSICAL_GUIREN: dict[str, tuple[str, str]] = {
    "甲": ("丑", "未"), "戊": ("丑", "未"), "庚": ("丑", "未"),
    "乙": ("子", "申"), "己": ("子", "申"),
    "丙": ("亥", "酉"), "丁": ("亥", "酉"),
    "壬": ("卯", "巳"), "癸": ("卯", "巳"), "辛": ("午", "寅"),
}

#: 三合局 → (驿马, 火星起宫, 铃星起宫)：申子辰马在寅 / 亥卯未马在巳 / 寅午戌马在申 /
#: 巳酉丑马在亥；火「寅午戌丑、申子辰寅、亥卯未酉、巳酉丑卯」；铃「寅午戌卯、余皆戌」。
CLASSICAL_SANHE: dict[frozenset[str], tuple[str, str, str]] = {
    frozenset("申子辰"): ("寅", "寅", "戌"),
    frozenset("亥卯未"): ("巳", "酉", "戌"),
    frozenset("寅午戌"): ("申", "丑", "卯"),
    frozenset("巳酉丑"): ("亥", "卯", "戌"),
}

#: 命主十二支（《全书》「子属贪狼丑亥门，寅戌禄存卯酉文曲，辰申廉贞巳未武曲，午破军」）。
#: 本表只锁**表体**；命主到底逐年支还是逐命宫支有两版歌诀，见 ledger F-A1-4，
#: 故这里不钉取哪一支进表，golden 也不钉这个字段。
CLASSICAL_MING_ZHU: dict[str, str] = {
    "子": "贪狼", "丑": "巨门", "寅": "禄存", "卯": "文曲", "辰": "廉贞", "巳": "武曲",
    "午": "破军", "未": "武曲", "申": "廉贞", "酉": "文曲", "戌": "禄存", "亥": "巨门",
}

#: 身主十二支（逐生年支，无争议）：「子午生人火星身，丑未天相寅申梁，
#: 卯酉天同身主是，巳亥天机辰戌昌」。
CLASSICAL_SHEN_ZHU: dict[str, str] = {
    "子": "火星", "丑": "天相", "寅": "天梁", "卯": "天同", "辰": "文昌", "巳": "天机",
    "午": "火星", "未": "天相", "申": "天梁", "酉": "天同", "戌": "文昌", "亥": "天机",
}

#: 《全书》通行的「双星同宫」落宫表（由两条 offset 序列在寅申镜像下摊出十二盘所得，
#: 与安星手册诸本所列为同一张表）。改任一 offset，这里立刻对不上。
CLASSICAL_MAJOR_PAIRINGS: dict[frozenset[str], frozenset[str]] = {
    frozenset({"紫微", "天府"}): frozenset({"寅", "申"}),
    frozenset({"紫微", "天相"}): frozenset({"辰", "戌"}),
    frozenset({"紫微", "贪狼"}): frozenset({"卯", "酉"}),
    frozenset({"紫微", "破军"}): frozenset({"丑", "未"}),
    frozenset({"紫微", "七杀"}): frozenset({"巳", "亥"}),
    frozenset({"天府", "武曲"}): frozenset({"子", "午"}),
    frozenset({"天府", "廉贞"}): frozenset({"辰", "戌"}),
    frozenset({"天机", "太阴"}): frozenset({"寅", "申"}),
    frozenset({"天机", "巨门"}): frozenset({"卯", "酉"}),
    frozenset({"天机", "天梁"}): frozenset({"辰", "戌"}),
    frozenset({"太阳", "太阴"}): frozenset({"丑", "未"}),
    frozenset({"太阳", "天梁"}): frozenset({"卯", "酉"}),
    frozenset({"太阳", "巨门"}): frozenset({"寅", "申"}),
    frozenset({"武曲", "天相"}): frozenset({"寅", "申"}),
    frozenset({"武曲", "贪狼"}): frozenset({"丑", "未"}),
    frozenset({"武曲", "七杀"}): frozenset({"卯", "酉"}),
    frozenset({"武曲", "破军"}): frozenset({"巳", "亥"}),
    frozenset({"天同", "太阴"}): frozenset({"子", "午"}),
    frozenset({"天同", "巨门"}): frozenset({"丑", "未"}),
    frozenset({"天同", "天梁"}): frozenset({"寅", "申"}),
    frozenset({"廉贞", "天相"}): frozenset({"子", "午"}),
    frozenset({"廉贞", "贪狼"}): frozenset({"巳", "亥"}),
    frozenset({"廉贞", "破军"}): frozenset({"卯", "酉"}),
    frozenset({"廉贞", "七杀"}): frozenset({"丑", "未"}),
}

#: 全部星名域（14 主 + 14 乙级），四化与命身主都不得越出这个集合。
STAR_UNIVERSE: frozenset[str] = frozenset(MAJOR_STARS) | frozenset(MINOR_STARS)

#: 紫微系的六个间隔之差（退 1、退 2、退 1、退 1、退 3）：口诀里的「空一宫」「空二宫」。
ZIWEI_SERIES_GAPS: tuple[int, ...] = (1, 2, 1, 1, 3)

#: 天府系前七星连排（间隔全 1），破军与前星隔三宫。
TIANFU_SERIES_GAPS: tuple[int, ...] = (1, 1, 1, 1, 1, 1, 4)


def tianfu_index(ziwei_index: int) -> int:
    """天府与紫微关于寅申轴对称（手册《紫微天府对照表》），即宫序之和恒为寅的两倍。

    抄在测试里而不是引引擎的算式：这条对称是**表级**事实（引擎 `ziwei.py:113` 只是用了它），
    两处各持一端才有门。
    """
    return (2 * ZHI_INDEX["寅"] - ziwei_index) % 12


Series = tuple[tuple[str, int], ...]


def star_palaces(
    ziwei_index: int,
    ziwei_series: Series = ZIWEI_SERIES,
    tianfu_series: Series = TIANFU_SERIES,
) -> dict[str, int]:
    """按两系 offset 把十四颗主星摊到十二宫（紫微在 ``ziwei_index`` 宫）。"""
    tianfu = tianfu_index(ziwei_index)
    palace_of = {name: (ziwei_index + off) % 12 for name, off in ziwei_series}
    palace_of.update({name: (tianfu + off) % 12 for name, off in tianfu_series})
    return palace_of


def pair_table(
    ziwei_series: Series = ZIWEI_SERIES,
    tianfu_series: Series = TIANFU_SERIES,
) -> dict[frozenset[str], frozenset[str]]:
    """十二张盘的「双星同宫」并集：星名对 → 它们同宫时所在宫的地支集合。"""
    table: dict[frozenset[str], set[str]] = {}
    for ziwei_index in range(12):
        palace_of = star_palaces(ziwei_index, ziwei_series, tianfu_series)
        by_palace: dict[int, list[str]] = {}
        for name, palace in palace_of.items():
            by_palace.setdefault(palace, []).append(name)
        for palace, names in by_palace.items():
            if len(names) == 2:
                table.setdefault(frozenset(names), set()).add(ZHI[palace])
    return {names: frozenset(zhis) for names, zhis in table.items()}


# ------------------------------------------------------------------ 1. 干支序


def test_ganzhi_orders_are_the_sexagenary_alphabet() -> None:
    """天干、地支的序是六十一甲子表的地基，顺序被换则五虎遁与索引全串位。"""
    assert GAN == "甲乙丙丁戊己庚辛壬癸"
    assert ZHI == "子丑寅卯辰巳午未申酉戌亥"
    assert len(GAN) == 10 and len(ZHI) == 12
    assert len(set(GAN)) == 10 and len(set(ZHI)) == 12


def test_index_maps_are_the_inverse_of_the_orders() -> None:
    """两张索引表必须是序本身的下标，且双射 —— 引擎全靠它把地支换成数。"""
    assert {z: i for i, z in enumerate(ZHI)} == ZHI_INDEX
    assert {g: i for i, g in enumerate(GAN)} == GAN_INDEX
    assert sorted(ZHI_INDEX.values()) == list(range(12))
    assert sorted(GAN_INDEX.values()) == list(range(10))


# ------------------------------------------------------------------ 2. 十四主星


def test_fourteen_major_stars_are_all_present_in_handbook_order() -> None:
    """14 颗齐，且名字集合与安星手册逐字相同：多一颗、少一颗、改名都算缺件。"""
    assert len(MAJOR_STARS) == 14
    assert set(MAJOR_STARS) == set(CLASSICAL_MAJOR_STARS)
    assert tuple(MAJOR_STARS) == CLASSICAL_MAJOR_STARS


@pytest.mark.parametrize("star_name", CLASSICAL_MAJOR_STARS)
def test_each_major_star_carries_its_element_group_and_keyword(star_name: str) -> None:
    """逐颗核五行与星系归属，并确认星情 keyword 不是空格子。

    阴阳一栏只钉「成员合法 + 日阳月阴」：《全书》诸本在个别星曜上有出入（七杀或作阳金、
    天同或作阴水），把一本之言当表钉死会成为下一轮的假阳性。五行十四颗则是诸本一致。
    """
    star = MAJOR_STARS[star_name]
    assert star.element == CLASSICAL_MAJOR_ELEMENTS[star_name]
    assert star.group == ("紫微系" if star_name in CLASSICAL_ZIWEI_GROUP else "天府系")
    assert star.yin_yang in {"阴", "阳"}
    assert star.nature and "·" in star.nature
    assert star.key and star.key.isascii() and star.key != star_name


def test_yin_yang_column_is_populated_and_keeps_sun_moon_polarity() -> None:
    """太阳必阳、太阴必阴（日月之性，无异说）；两系里阴阳都不能是清一色。"""
    assert MAJOR_STARS["太阳"].yin_yang == "阳"
    assert MAJOR_STARS["太阴"].yin_yang == "阴"
    for group in (CLASSICAL_ZIWEI_GROUP, CLASSICAL_TIANFU_GROUP):
        polarities = {MAJOR_STARS[name].yin_yang for name in group}
        assert polarities == {"阴", "阳"}
    assert {star.yin_yang for star in MAJOR_STARS.values()} == {"阴", "阳"}


def test_star_keys_are_unique() -> None:
    """ascii key 是前端画星格用的稳定标识，撞名就会有两颗星共用一个图元。"""
    keys = [star.key for star in MAJOR_STARS.values()]
    assert len(set(keys)) == 14


def test_minor_stars_are_the_fourteen_yi_level_stars() -> None:
    """乙级十四颗：六吉 + 禄马二 + 六煞，缺一位则盘面静默少一星。"""
    assert set(MINOR_STARS) == {
        "左辅", "右弼", "文昌", "文曲", "天魁", "天钺",
        "禄存", "天马", "擎羊", "陀罗", "火星", "铃星", "地空", "地劫",
    }
    assert {star.kind for star in MINOR_STARS.values()} == {"吉", "煞", "禄马"}
    for star in MINOR_STARS.values():
        assert star.element in {"金", "木", "水", "火", "土"}


def test_major_and_minor_star_names_do_not_overlap() -> None:
    """两表共 28 颗星，一颗都不能重名 —— 重名会让引擎的后写覆盖前写。"""
    assert len(STAR_UNIVERSE) == 28


# ------------------------------------------------------------------ 3. 两条安星序列


def test_ziwei_series_runs_backwards_with_the_mnemonic_intervals() -> None:
    """紫微系六星的间隔逐字对上「退一、隔一、退一、退一、隔二」。"""
    assert [name for name, _ in ZIWEI_SERIES] == list(CLASSICAL_ZIWEI_SERIES_ORDER)
    assert [off for _, off in ZIWEI_SERIES] == list(CLASSICAL_ZIWEI_OFFSETS)
    assert [name for name, _ in ZIWEI_SERIES][0] == "紫微"
    gaps = [
        abs(ZIWEI_SERIES[i][1] - ZIWEI_SERIES[i - 1][1])
        for i in range(1, len(ZIWEI_SERIES))
    ]
    assert gaps == list(ZIWEI_SERIES_GAPS)
    assert all(off < 0 for _, off in ZIWEI_SERIES[1:])  # 一律逆行


def test_tianfu_series_runs_forwards_with_pojun_last() -> None:
    """天府系八星顺排，破军居第十宫（前七星连排，中间空三宫）。"""
    assert [name for name, _ in TIANFU_SERIES] == list(CLASSICAL_TIANFU_SERIES_ORDER)
    assert [off for _, off in TIANFU_SERIES] == list(CLASSICAL_TIANFU_OFFSETS)
    assert [name for name, _ in TIANFU_SERIES][0] == "天府"
    assert [name for name, _ in TIANFU_SERIES][-1] == "破军"
    gaps = [
        TIANFU_SERIES[i][1] - TIANFU_SERIES[i - 1][1]
        for i in range(1, len(TIANFU_SERIES))
    ]
    assert gaps == list(TIANFU_SERIES_GAPS)
    assert all(off > 0 for _, off in TIANFU_SERIES[1:])  # 一律顺行


def test_the_two_series_partition_the_fourteen_major_stars() -> None:
    """两系合起来正好是十四颗，且不重不漏 —— 归属换了，盘面就少一系。"""
    series_names = {name for name, _ in ZIWEI_SERIES} | {name for name, _ in TIANFU_SERIES}
    assert series_names == set(CLASSICAL_MAJOR_STARS)
    assert {name for name, _ in ZIWEI_SERIES} == set(CLASSICAL_ZIWEI_GROUP)
    assert {name for name, _ in TIANFU_SERIES} == set(CLASSICAL_TIANFU_GROUP)
    assert len(ZIWEI_SERIES) == 6 and len(TIANFU_SERIES) == 8


def test_series_offsets_are_distinct_within_each_series() -> None:
    """同系两星不得落在同一宫（否则十四颗里有两颗会永远并排）。"""
    for series in (ZIWEI_SERIES, TIANFU_SERIES):
        offsets = {off % 12 for _, off in series}
        assert len(offsets) == len(series)


@pytest.mark.parametrize("ziwei_index", range(12))
def test_each_board_places_all_fourteen_stars_without_triples(ziwei_index: int) -> None:
    """任一紫微落宫都把十四颗摊进十二宫：一颗不落一宫、也从不三颗同宫。"""
    palace_of = star_palaces(ziwei_index)
    assert set(palace_of) == set(CLASSICAL_MAJOR_STARS)
    by_palace: dict[int, list[str]] = {}
    for name, palace in palace_of.items():
        by_palace.setdefault(palace, []).append(name)
    assert all(len(names) <= 2 for names in by_palace.values())
    assert all(0 <= palace < 12 for palace in palace_of.values())
    # 14 颗摊进 12 宫的算术：双星宫数 - 空宫数 = 2（紫微在寅/申时无空宫，恰好两组双星）。
    doubled = sum(1 for names in by_palace.values() if len(names) == 2)
    assert doubled - (12 - len(by_palace)) == 2


def test_major_star_pairings_match_the_classical_combo_table() -> None:
    """把两条序列摊成十二张盘，双星同宫关系的并集与《全书》通行的「主星同宫」表逐字相同。

    这是本模块最强的一条：offset 与星名两件事同时被锁 —— 改一个间隔，同宫的那一对
    （或它落空的宫）当场改名；把某颗星换掉，表里就会冒出未知星名。
    表本身是手推出来的：紫微在寅时紫府同宫、机阴在申、日巨在卯…… 十二盘并集即 24 对。
    """
    assert pair_table() == CLASSICAL_MAJOR_PAIRINGS


def test_killing_pojun_trinity_holds_on_every_board() -> None:
    """杀（七杀）破（破军）狼（贪狼）恒居三方四正：三支两两相差四宫，与紫微落宫无关。"""
    for ziwei_index in range(12):
        palace_of = star_palaces(ziwei_index)
        offsets = sorted((palace_of[s] - palace_of["贪狼"]) % 12 for s in ("贪狼", "七杀", "破军"))
        assert offsets == [0, 4, 8]
        assert palace_of["七杀"] != palace_of["破军"]  # 破军与七杀之间恒空三宫


def test_the_pairing_table_actually_pins_the_offsets() -> None:
    """上一道的自查：动一个 offset 后并集表必须变 —— 若不变，那张表就是钉不住表的废码。"""
    shifted_pojun = tuple(
        (name, off + 1 if name == "破军" else off) for name, off in TIANFU_SERIES
    )
    assert pair_table(ZIWEI_SERIES, shifted_pojun) != CLASSICAL_MAJOR_PAIRINGS
    doubled_sun = tuple((name, off - 2 if name == "太阳" else off) for name, off in ZIWEI_SERIES)
    assert pair_table(doubled_sun, TIANFU_SERIES) != CLASSICAL_MAJOR_PAIRINGS


# ------------------------------------------------------------------ 4. 四化表


def test_sihua_covers_ten_gans_x_four_transformations_without_holes() -> None:
    """10 干 × 4 化 = 40 格，一格都不许空、不许越出星名域、不许同干重星。"""
    assert set(SIHUA) == set(GAN)
    assert SIHUA_LABELS == ("化禄", "化权", "化科", "化忌")
    for year_gan, row in SIHUA.items():
        assert len(row) == 4, f"{year_gan} 干四化缺格: {row}"
        assert all(text for text in row), f"{year_gan} 干四化有空格: {row}"
        assert len(set(row)) == 4, f"{year_gan} 干四化重星: {row}"
        for star_name in row:
            assert star_name in STAR_UNIVERSE, f"{year_gan} 干四化出现未知星名 {star_name}"


@pytest.mark.parametrize("year_gan", GAN)
def test_sihua_row_equals_the_mnemonic(year_gan: str) -> None:
    """逐干与四化诀对照：手册背的是「庚阳武阴同」这一句，表必须与它同字。"""
    assert SIHUA[year_gan] == CLASSICAL_SIHUA_JUE[year_gan]


def test_the_sihua_table_names_eleven_major_stars_plus_six_ji() -> None:
    """四化点名的主星只有十一颗，另点昌曲辅弼四颗乙级；天府、天相、七杀十干皆不化。

    「府相杀不化」是通行四化表的形状（十干四十格里没有它们），把它钉成集合差，
    任何一格被填成天府/天相/七杀 都会当场变红。
    """
    transformed = {star_name for row in SIHUA.values() for star_name in row}
    assert transformed <= set(STAR_UNIVERSE)
    assert {"文昌", "文曲", "左辅", "右弼"} <= transformed
    assert set(MAJOR_STARS) - transformed == {"天府", "天相", "七杀"}
    assert len(transformed) == 15  # 十一主星 + 昌曲辅弼


# ------------------------------------------------------------------ 5. 十二宫与五行局


def test_twelve_palace_names_are_the_counterwise_order() -> None:
    """宫名序固定：自命宫逆布，第六位恒为迁移（命宫对宫），第十二位恒为父母。"""
    assert PALACE_NAMES == CLASSICAL_PALACE_NAMES
    assert len(set(PALACE_NAMES)) == 12
    assert PALACE_NAMES[0] == "命宫"
    assert PALACE_NAMES[6] == "迁移"
    assert PALACE_NAMES.index("财帛") == 4 and PALACE_NAMES.index("官禄") == 8


def test_wuxing_ju_maps_five_elements_to_two_through_six() -> None:
    """纳音五行五格齐，局数 2–6 各一次，局名与「五行 + 中文数字 + 局」同字。"""
    assert WUXING_JU == CLASSICAL_WUXING_JU
    assert set(WUXING_JU) == {"金", "木", "水", "火", "土"}
    assert sorted(number for number, _ in WUXING_JU.values()) == [2, 3, 4, 5, 6]


@pytest.mark.parametrize("element", sorted(CLASSICAL_WUXING_JU))
def test_every_ju_is_named_by_its_element_and_number(element: str) -> None:
    """局名一律「五行 + 中文数字 + 局」，局数落在 2–6。

    起运虚岁就是局数（`app/engines/ziwei.py` 的 `dayun_start_age=ju_number`），所以这一格
    写错一位中文数字，页面上的局名与大限起运岁数当场对不上，而 JSON 仍是合法字符串。
    大限十二段**区间**的无缝/不重叠不在这里测：那张表里根本没有区间，区间是引擎按局数
    摊出来的，故钉在 `tests/golden/test_ziwei_golden.py`
    `::test_the_twelve_dayun_blocks_tile_the_lifespan_without_gaps`（五局各有实盘）。
    """
    ju_number, ju_name = WUXING_JU[element]
    assert 2 <= ju_number <= 6, f"{element} 行的局数越界: {ju_number}"
    assert ju_name == f"{element}{CLASSICAL_JU_CN_NUMBERS[ju_number]}局"


# ------------------------------------------------------------------ 6. 起星诸表


def test_wuhu_dun_covers_every_year_gan_in_five_pairs() -> None:
    """五虎遁十干齐，且合化五组（甲己、乙庚、丙辛、丁壬、戊癸）同组同干。"""
    assert YIN_GAN_BY_YEAR_GAN == CLASSICAL_WUHU_DUN
    assert set(YIN_GAN_BY_YEAR_GAN) == set(GAN)
    for pair in ("甲己", "乙庚", "丙辛", "丁壬", "戊癸"):
        values = {YIN_GAN_BY_YEAR_GAN[gan] for gan in pair}
        assert len(values) == 1, f"{pair} 年的寅宫天干不一致: {values}"


def test_lucun_covers_every_year_gan() -> None:
    """禄存十干齐，逐字对上「甲寅乙卯丙巳随，丁午戊巳己午推，庚申辛酉壬亥坐，癸居子上」。"""
    assert LUCUN_BY_YEAR_GAN == CLASSICAL_LUCUN
    assert set(LUCUN_BY_YEAR_GAN) == set(GAN)
    assert LUCUN_BY_YEAR_GAN["丙"] == LUCUN_BY_YEAR_GAN["戊"]  # 丙戊同禄在巳
    assert LUCUN_BY_YEAR_GAN["丁"] == LUCUN_BY_YEAR_GAN["己"]  # 丁己同禄在午


def test_guiren_covers_every_year_gan_with_two_distinct_branches() -> None:
    """天乙贵人十干齐；魁与钺必须是两个不同地支（同一格填两遍是最常见的抄错）。"""
    assert TIANKUI_TIANYUE == CLASSICAL_GUIREN
    assert set(TIANKUI_TIANYUE) == set(GAN)
    for year_gan, (kui, yue) in TIANKUI_TIANYUE.items():
        assert kui != yue, f"{year_gan} 干魁钺同宫: {kui}"
        assert kui in ZHI and yue in ZHI


@pytest.mark.parametrize("group", sorted(CLASSICAL_SANHE, key=lambda g: "".join(sorted(g))))
def test_sanhe_tables_are_constant_within_a_group(group: frozenset[str]) -> None:
    """驿马、火星、铃星三张表都必须逐三合局取值：同局三支不同字，就是抄错了一支。"""
    for table, column in (
        (TIANMA_BY_YEAR_ZHI, 0),
        (HUOXING_BASE, 1),
        (LINGXING_BASE, 2),
    ):
        values = {table[year_zhi] for year_zhi in group}
        assert values == {CLASSICAL_SANHE[group][column]}, f"{sorted(group)} 取值 {values}"


def test_sanhe_tables_cover_twelve_branches_and_match_the_mnemonics() -> None:
    """十二支各就各位（三支一组共四组），且分组本身是四组三合局。"""
    assert set().union(*CLASSICAL_SANHE) == set(ZHI)
    for table in (TIANMA_BY_YEAR_ZHI, HUOXING_BASE, LINGXING_BASE):
        assert set(table) == set(ZHI)
    for group, (ma, huo, ling) in CLASSICAL_SANHE.items():
        for year_zhi in group:
            assert TIANMA_BY_YEAR_ZHI[year_zhi] == ma
            assert HUOXING_BASE[year_zhi] == huo
            assert LINGXING_BASE[year_zhi] == ling
    # 驿马四局四马地互不相同；火星四个起宫亦然（铃星只二宫，故不比这一格）。
    assert len({TIANMA_BY_YEAR_ZHI[z] for z in ZHI}) == 4
    assert len({HUOXING_BASE[z] for z in ZHI}) == 4
    assert set(LINGXING_BASE.values()) == {"卯", "戌"}


def test_ming_zhu_and_shen_zhu_tables_are_twelve_branches_of_known_stars() -> None:
    """命主、身主两张表十二支齐、值全在星名域内。

    命主到底逐年支还是逐命宫支有两版歌诀（本仓取年支），本轮**不钉取值口径**，
    只钉表体与定义域 —— 详见 ledger F-A1-4 与 `tests/golden/test_ziwei_golden.py`
    里那条刻意不给命主下断言的说明。
    """
    assert MING_ZHU == CLASSICAL_MING_ZHU
    assert SHEN_ZHU == CLASSICAL_SHEN_ZHU
    for table in (MING_ZHU, SHEN_ZHU):
        assert set(table) == set(ZHI)
        assert set(table.values()) <= STAR_UNIVERSE
    assert len(set(SHEN_ZHU.values())) == 6  # 六对同支（子午、丑未、寅申、卯酉、辰戌、巳亥）


def test_source_line_names_the_book_and_the_school() -> None:
    """出处串必须点名《紫微斗数全书》并声明四化派别 —— 派别不说，读者无从复核。"""
    assert "紫微斗数全书" in ZIWEI_SOURCE
    assert "四化" in ZIWEI_SOURCE and "全书" in ZIWEI_SOURCE
