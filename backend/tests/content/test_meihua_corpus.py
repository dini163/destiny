"""梅花语料表自身的不变式（Task 6 Step 3 · 轴 1 深包 B）。

`tests/golden/test_meihua_golden.py` 钉的是十五张手推锚卦的**推导结果**（起卦数、本/互/变、
体用定位、卦气、账本），本模块钉的是推导所依据的**表体**：先天八卦数、64 卦的上卦×下卦全覆盖、
八卦万物类象、体用生克五关系、旺相休囚死判定表、月支季节名。表上被改动一格，引擎照样算得完，
断语照样成段，只有对照古法才发现得了——所以对照必须写在这里。

与既有测试的分工：64 卦的**文王序计数、卦画与上下卦一致、八宫与文王序同集、卦辞齐**这四条
住在 `tests/golden/test_zhouyi_golden.py`（那是六爻系统的表门，不重述）。本模块只补梅花这一侧
真正独有的三件事：**先天卦数**（起卦算术的定义域）、**上卦×下卦 8×8 积集齐**（`HEXAGRAM_BY_TRIGRAMS`
那条索引若缺一格，某一组上下卦的盘会在 `_hexagram()` 里 KeyError，而那一格恰好不在十五张锚卦里）、
**体用五行与卦气的 5×5 全组合**（引擎只按两行查表，表缺一格就有一类盘没有结论）。

**出处缺口已于 2026-09-30 闭合**（多系统白话计划 Task 7）：`MeihuaCast` 现有 `provenance`，
`app/content/__init__.py` 现有 `MEIHUA_CONTENT_SOURCES`，万物类象与体用判词从此可查。
清单的五张表（wuxing 不进，lunar-python 以 `provenance.engine` 短值认账而不进 tables）钉在
`tests/golden/test_meihua_golden.py::test_provenance_lists_exactly_the_five_tables_the_cast_reads`，
本模块仍只管表体（先天卦数、8×8 全覆盖、体用与卦气的 5×5 全组合），出处不重复钉。

复测本文件测数：`cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m pytest tests/content/test_meihua_corpus.py -o addopts=""` → 9 passed（2026-09-30 复测；旧写法带 `-q`，
与本仓库 `pyproject.toml` 的 `addopts = "-q"` 叠成 `-qq`，统计行不打印，命令自证不了自己）。
"""

import unicodedata
from collections import Counter

from app.content.meihua import (
    BAGUA_IMAGE,
    SEASON_BY_MONTH_ZHI,
    TIYONG_RELATIONS,
    WANGSHUAI_TEXT,
    wangshuai_state,
)
from app.content.qimen import LUOSHU
from app.content.wuxing import CONTROLS, ELEMENT_ORDER, GENERATES, ZHI_ELEMENT
from app.content.zhouyi_hexagrams import (
    HEXAGRAMS,
    HEXAGRAM_BY_LINES,
    HEXAGRAM_BY_NUMBER,
    HEXAGRAM_BY_TRIGRAMS,
)
from app.content.zhouyi_trigrams import TRIGRAMS, TRIGRAM_BY_KEY, TRIGRAM_BY_MEIHUA

#: 先天八卦数（邵雍伏羲序）：乾1 兑2 离3 震4 巽5 坎6 艮7 坤8——报数起卦 ÷8 余数的定义域。
XIANTIAN_NUMBERS = {
    "乾": 1, "兑": 2, "离": 3, "震": 4, "巽": 5, "坎": 6, "艮": 7, "坤": 8,
}
#: 八卦五行（《说卦传》通行）：乾兑金、震巽木、坎水、离火、艮坤土。
TRIGRAM_ELEMENTS = {
    "乾": "金", "兑": "金", "离": "火", "震": "木", "巽": "木", "坎": "水", "艮": "土", "坤": "土",
}
#: 八卦之象（《说卦传》）。
TRIGRAM_NATURES = {
    "乾": "天", "兑": "泽", "离": "火", "震": "雷", "巽": "风", "坎": "水", "艮": "山", "坤": "地",
}
#: 后天八卦方位（洛书），应与 `content/qimen.LUOSHU` 的宫方位同字。
LATER_HEAVEN_DIRECTIONS = {
    "乾": "西北", "坤": "西南", "震": "东", "巽": "东南",
    "坎": "北", "离": "南", "艮": "东北", "兑": "西",
}
#: 体用五关系的古典次序（吉→凶）与其判词等级。
RELATION_ORDER = ("yong_sheng_ti", "bi_he", "ti_ke_yong", "ti_sheng_yong", "yong_ke_ti")
RELATION_NAMES = {
    "yong_sheng_ti": ("用生体", "大吉", 2),
    "bi_he": ("体用比和", "吉", 1),
    "ti_ke_yong": ("体克用", "小吉", 1),
    "ti_sheng_yong": ("体生用", "小凶", -1),
    "yong_ke_ti": ("用克体", "大凶", -2),
}
#: 季节与其五行：春木、夏火、秋金、冬水（季月即辰未戌丑，属土）。
SEASON_ELEMENTS = {"春": "木", "夏": "火", "秋": "金", "冬": "水"}
#: 卦气的古法判据（我同=旺、令生我=相、我生令=休、我克令=囚、令克我=死）。
WANGSHUAI_RULE_STATES = ("旺", "相", "休", "囚", "死")


def _classify(ti: str, yong: str) -> str:
    """由五行两行独立回推体用关系键（只用 `content/wuxing` 的两条循环，不引引擎）。"""
    if ti == yong:
        return "bi_he"
    if GENERATES[ti] == yong:
        return "ti_sheng_yong"
    if GENERATES[yong] == ti:
        return "yong_sheng_ti"
    if CONTROLS[ti] == yong:
        return "ti_ke_yong"
    if CONTROLS[yong] == ti:
        return "yong_ke_ti"
    raise AssertionError(f"{ti}/{yong} 落在两条五行循环之外")


def test_the_eight_trigrams_carry_the_pre_heaven_numbers_once_each() -> None:
    """先天八卦数 1-8 各出现一次，且 `TRIGRAM_BY_MEIHUA` 是它的双射索引。

    起卦算术的全部定义域就是这八个数（÷8 余 0 作 8）：少一号或多一号，某一类报数会
    映射到不存在的卦，而引擎只在映射成功时才算得下去。
    """
    assert len(TRIGRAMS) == 8 and len({t.key for t in TRIGRAMS}) == 8
    assert {t.name_zh: t.meihua_number for t in TRIGRAMS} == XIANTIAN_NUMBERS
    assert sorted(t.meihua_number for t in TRIGRAMS) == list(range(1, 9))
    assert set(TRIGRAM_BY_MEIHUA) == set(range(1, 9))
    for number, key in TRIGRAM_BY_MEIHUA.items():
        assert TRIGRAM_BY_KEY[key].meihua_number == number
    assert len({t.binary for t in TRIGRAMS}) == 8
    assert len({t.symbol for t in TRIGRAMS}) == 8
    for trigram in TRIGRAMS:
        assert len(trigram.binary) == 3 and set(trigram.binary) <= {0, 1}
        assert trigram.element == TRIGRAM_ELEMENTS[trigram.name_zh], trigram.name_zh
        assert trigram.nature_zh == TRIGRAM_NATURES[trigram.name_zh], trigram.name_zh


def test_every_upper_lower_trigram_pair_has_exactly_one_hexagram() -> None:
    """64 卦全覆盖：`HEXAGRAM_BY_TRIGRAMS` 的键集正是 8×8 的笛卡尔积，一格不多一格不少。

    梅花本/互/变三卦都靠这张索引落卦。少一格不会让引擎在锚卦上出错——只有落在
    那一组的盘才 KeyError，而那一组恰好可能不在十五张锚卦里。
    """
    keys = {t.key for t in TRIGRAMS}
    assert set(HEXAGRAM_BY_TRIGRAMS) == {(lower, upper) for lower in keys for upper in keys}
    assert len(HEXAGRAM_BY_TRIGRAMS) == 64
    assert len(HEXAGRAMS) == len(HEXAGRAM_BY_LINES) == 64


def test_hexagram_names_and_glyphs_do_not_repeat() -> None:
    """卦名（短名）、全名与 Unicode 卦符各 64 格不重复——梅花响应把四格同时印在页面上。

    卦符按 Unicode 区块（U+4DC0 起）就是文王序，这一条相当于拿 Unicode 字符数据库外部核对
    了一遍序号（同 `tests/content/test_rune_corpora.py` 用 `unicodedata.name()` 核字形的做法）。
    复测：`cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "`
    `import unicodedata;print([unicodedata.name(chr(0x4DC0+i)) for i in (0,21,63)])"`
    """
    assert len({h.name_zh for h in HEXAGRAMS}) == 64
    assert len({h.full_name_zh for h in HEXAGRAMS}) == 64
    assert len({h.symbol for h in HEXAGRAMS}) == 64
    assert len({h.name_en for h in HEXAGRAMS}) == 64
    for number, hexagram in HEXAGRAM_BY_NUMBER.items():
        assert hexagram.symbol == chr(0x4DC0 + number - 1), number
        assert unicodedata.name(hexagram.symbol).startswith("HEXAGRAM FOR")
        assert hexagram.name_zh and hexagram.pinyin


def test_the_compound_name_encodes_upper_then_lower_image() -> None:
    """全名的前两字必须是「上卦之象、下卦之象」（纯卦作「X为象」）——表体与命名不得各说各话。

    六十四卦的上下卦是由全名解析出来的（`zhouyi_hexagrams._parse_trigrams`），也就是说
    名字就是数据结构；名字与卦画一旦分家，页面标题与断卦用的卦象会同时错。
    """
    for hexagram in HEXAGRAMS:
        name = hexagram.full_name_zh
        upper_nature = TRIGRAM_BY_KEY[hexagram.upper].nature_zh
        lower_nature = TRIGRAM_BY_KEY[hexagram.lower].nature_zh
        if "为" in name:
            assert hexagram.lower == hexagram.upper, name
            assert name == f"{TRIGRAM_BY_KEY[hexagram.lower].name_zh}为{upper_nature}", name
        else:
            assert name[0] == upper_nature and name[1] == lower_nature, name
            assert hexagram.lines[:3] == TRIGRAM_BY_KEY[hexagram.lower].binary
            assert hexagram.lines[3:] == TRIGRAM_BY_KEY[hexagram.upper].binary


def test_the_five_ti_yong_relations_are_fully_populated_and_ordered() -> None:
    """体用生克表：五键齐、判名与等级逐格与古法相符、吉凶次序不翻（用生体＞比和＞体克用＞体生用＞用克体）。

    判词文本一格不许空：这一格是断语正文里唯一直接引古籍的一段。
    """
    assert set(TIYONG_RELATIONS) == set(RELATION_ORDER)
    for key, (name_zh, verdict, grade) in RELATION_NAMES.items():
        relation = TIYONG_RELATIONS[key]
        assert relation.key == key
        assert (relation.name_zh, relation.verdict, relation.grade) == (name_zh, verdict, grade)
        assert relation.text.strip().endswith("。") and len(relation.text) > 20, key
    assert len({r.name_zh for r in TIYONG_RELATIONS.values()}) == 5
    assert len({r.verdict for r in TIYONG_RELATIONS.values()}) == 5
    # 次序：按古典吉→凶排，grade 单调不升且 base_score 单调下降（两本账同向才没有暗账）。
    grades = [TIYONG_RELATIONS[key].grade for key in RELATION_ORDER]
    bases = [TIYONG_RELATIONS[key].base_score for key in RELATION_ORDER]
    assert grades == [2, 1, 1, -1, -2]
    assert grades == sorted(grades, reverse=True)
    assert bases == sorted(bases, reverse=True)


def test_every_element_pair_of_the_five_by_five_lands_on_one_relation() -> None:
    """体用五行 5×5 共 25 组合全都有结论，且五条关系各接住 5 组（对角 5 组即比和）。

    表里少一条关系，就会有 5 张盘在 `_relation_key` 的查表处 KeyError；多一条（比如将来加
    「反生为克」）则本测立刻点名，因为 25 组的分配不再是 5+5+5+5+5。
    """
    pairs = [(ti, yong) for ti in ELEMENT_ORDER for yong in ELEMENT_ORDER]
    assert len(pairs) == 25
    classified = [_classify(ti, yong) for ti, yong in pairs]
    assert set(classified) <= set(TIYONG_RELATIONS)
    assert Counter(classified) == Counter({key: 5 for key in RELATION_ORDER})
    # 两条五行循环本身也是齐的：每个五行恰有一个「我生」与一个「我克」。
    assert set(GENERATES) == set(CONTROLS) == set(ELEMENT_ORDER)
    assert len(set(GENERATES.values())) == len(set(CONTROLS.values())) == 5


def test_wangshuai_state_is_a_latin_square_over_the_five_elements() -> None:
    """卦气：五个当令五行 × 五个五行 = 25 格都有状态，且每一行五种状态各出现一次（对角恒为旺）。

    判据在测试里独立回推（同=旺、令生我=相、我生令=休、我克令=囚、令克我=死），
    与 `content/meihua.wangshuai_state` 的实现各持一端。
    """
    expected_states = set(WANGSHUAI_RULE_STATES)
    assert set(WANGSHUAI_TEXT) == expected_states
    for state in expected_states:
        assert WANGSHUAI_TEXT[state].strip().endswith("。")
    for commanding in ELEMENT_ORDER:
        states = {wangshuai_state(e, commanding) for e in ELEMENT_ORDER}
        assert states == expected_states, commanding
        for element in ELEMENT_ORDER:
            if element == commanding:
                expected = "旺"
            elif GENERATES[commanding] == element:
                expected = "相"
            elif GENERATES[element] == commanding:
                expected = "休"
            elif CONTROLS[element] == commanding:
                expected = "囚"
            else:
                expected = "死"
            assert wangshuai_state(element, commanding) == expected, (element, commanding)


def test_bagua_images_cover_the_eight_trigrams_with_the_later_heaven_directions() -> None:
    """万物类象：八卦齐、六项（人物/身体/动物/方位/物象/性情）无空格、方位即洛书后天卦位。

    方位一格与 `content/qimen.LUOSHU` 的宫方位交叉核对：两张表各自抄自后天八卦方位，
    一旦其中一张抄错，页面「东方震木」这类断语就会与另一页的九宫方位自相矛盾。
    """
    IMAGE_FIELDS = ("person", "body", "animal", "direction", "obj", "temper")
    assert set(BAGUA_IMAGE) == {t.key for t in TRIGRAMS}
    for trigram in TRIGRAMS:
        image = BAGUA_IMAGE[trigram.key]
        for field in IMAGE_FIELDS:
            assert getattr(image, field).strip(), (trigram.key, field)
        assert image.direction == LATER_HEAVEN_DIRECTIONS[trigram.name_zh], trigram.name_zh
        palace = next(p for p, entry in LUOSHU.items() if entry.gua == trigram.name_zh)
        assert LUOSHU[palace].direction == image.direction, trigram.name_zh


def test_season_names_cover_the_twelve_branches_and_track_their_elements() -> None:
    """卦气的月令输入：12 支齐、12 个季节名不重复，孟仲季与五行相配（季月辰未戌丑属土）。

    引擎用这张表把月支摊成「孟夏」一类字样，用 `ZHI_ELEMENT` 定当令五行——两格若脱节，
    响应里会同时出现「孟春」与「土令」这种互相矛盾的组合。
    """
    assert set(SEASON_BY_MONTH_ZHI) == set("子丑寅卯辰巳午未申酉戌亥")
    assert len(set(SEASON_BY_MONTH_ZHI.values())) == 12
    for branch, season in SEASON_BY_MONTH_ZHI.items():
        phase, name = season[0], season[1]
        assert phase in "孟仲季" and name in SEASON_ELEMENTS, (branch, season)
        expected = "土" if phase == "季" else SEASON_ELEMENTS[name]
        assert ZHI_ELEMENT[branch] == expected, (branch, season)
    # 同一季节的三支连排：孟仲季各占一支（春寅卯辰、夏巳午未、秋申酉戌、冬亥子丑）。
    grouped: dict[str, list[str]] = {}
    for branch, season in SEASON_BY_MONTH_ZHI.items():
        grouped.setdefault(season[1], []).append(branch)
    assert grouped == {"春": ["寅", "卯", "辰"], "夏": ["巳", "午", "未"],
                       "秋": ["申", "酉", "戌"], "冬": ["亥", "子", "丑"]}
