"""白话语料的唯一登记处（多系统白话 spec §4）。

只做一件事：把 `content/` 里的纯表塞进 `PlainCorpus`，让 `tests/test_plain_corpora.py`
的机检工厂按参数化跑遍每一张表。这里**不产句子、不判命**，也不许出现第二份键名——
`universe()` 一律从源表现算，条目数与键集合因此不可能和源表漂开（少建、多建同样红）。
"""

from __future__ import annotations

from itertools import combinations, product

from app.content import (
    kabbalah_plain,
    lenormand_plain,
    name_plain,
    qimen_plain,
    synastry_plain,
    transit_plain,
    western_plain,
    zhouyi_plain,
    ziwei_plain,
)
from app.content import vedic_plain
from app.content.vedic import GRAHAS, NAKSHATRAS, SIGNS_EN
from app.content.bazi_dimensions import DIMENSION_RULES
from app.content.bazi_plain import DIMENSION_OPENERS, PLAIN_READINGS, TIER_CLOSERS
from app.content.kabbalah import DAATH, PATHS, SEPHIROTH
from app.content.lenormand import CARDS
from app.content.meihua import BAGUA_IMAGE, TIYONG_RELATIONS, WANGSHUAI_TEXT
from app.content.meihua_plain import (
    MEIHUA_READINGS,
    MEIHUA_SUMMARY_OPENER,
    MEIHUA_TIER_CLOSERS,
    leixiang_key,
    tiyong_key,
    wangshuai_key,
)
from app.content.name_numerology import NUMBERS
from app.content.name_sancai import SANCAI_RELATIONS
from app.content.qimen import EIGHT_DOORS, EIGHT_GODS, NINE_STARS
from app.content.synastry import SYNASTRY_CORE_BONDS
from app.content.ziwei import MAJOR_STARS, MINOR_STARS, SIHUA_LABELS
from app.engines.plain_compose import PlainCorpus

# `plain_corpora → engines/western` 是 `engines → engines`，AGENTS.md §1 只禁 `engines → api`，
# 这条合法。**不许**改成 `from app.engines.synastry import _AXIS_ZH`——`synastry.py` 反过来要
# import 本模块取 `SYNASTRY`，那就是循环。两轴的字面量因此留在 `_synastry_universe()` 里，
# 由本系统 golden 测的那条 `_AXIS_ZH` 对账条款守住它不漂。
from app.engines.western import ASPECTS, PLANETS, SIGN_ELEMENT, SIGN_MODALITY, SIGNS


def _bazi_universe() -> set[str]:
    """六维判语表的全部键（第一期 39 条）。

    条数复测：`cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "from app.content.bazi_dimensions import DIMENSION_RULES; print(sum(len(v) for v in DIMENSION_RULES.values()))"` → 39。
    """
    return {rule.key for rules in DIMENSION_RULES.values() for rule in rules}


BAZI = PlainCorpus(
    system="bazi",
    entries=PLAIN_READINGS,
    openers=DIMENSION_OPENERS,
    closers=TIER_CLOSERS,
    grouping="band",
    universe=_bazi_universe,
)


def _name_universe() -> set[str]:
    """姓名学的键全集 = 八十一数理 + 五条三才关系 + 一条笔画未核定支路。

    86 来自两张源表（复测：`cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "from app.content.name_numerology import NUMBERS; from app.content.name_sancai import SANCAI_RELATIONS; print(len(NUMBERS), len(SANCAI_RELATIONS))"` → `81 5`），
    第 87 条 `name.unresolved` 不对应源表，对应 `build_grid` 的 `value is None` 支路
    （多出来的一条已写进 spec 的回填提交，不是本表自造）。
    """
    return (
        {name_plain.shuli_key(number) for number in NUMBERS}
        | {name_plain.sancai_key(relation) for relation in SANCAI_RELATIONS}
        | {name_plain.NAME_UNRESOLVED_KEY}
    )


NAME = PlainCorpus(
    system="name",
    entries=name_plain.NAME_READINGS,
    openers={
        **name_plain.NAME_GRID_OPENERS,
        "sancai": name_plain.NAME_SANCAI_OPENER,
        "summary": name_plain.NAME_SUMMARY_OPENER,
    },
    closers={**name_plain.NAME_SCORE_CLOSERS, **name_plain.NAME_SANCAI_CLOSERS},
    # 分带符号取自 NameFortune 的顺/注两侧 + HARMONIOUS_RELATIONS 的归属，不取 delta：
    # FORTUNE_SCORES 的最低档「凶」是 0 分，delta = 权重 × 分值 恒 ≥ 0，按 delta 分带会
    # 成建制地丢句（spec 裁定 R2）。符号由 Task 5 的引擎算好传入，装配器不认识 NameFortune。
    grouping="band",
    universe=_name_universe,
)


def _synastry_universe() -> set[str]:
    """合盘的键全集 = 12 点义 + 5 相位框架句 + 5 核心羁绊 = 22。

    三个来源各自现算，不写第二份名单（spec §4 的「少建、多建同样红」）：十大行星取
    `engines/western.PLANETS` 的第一元，五种相位取 `western.ASPECTS` 的第一元（合盘与
    本命盘共用这张表——`engines/synastry.py` 是从 `engines.western` import 它，不复制），
    五条轴取 `content/synastry.py` 的 `SYNASTRY_CORE_BONDS`。ASC/MC 是本函数里唯一的
    字面量，理由见本文件上面的 import 注。
    """
    return (
        {synastry_plain.point_key(name) for name, *_ in PLANETS}
        | {synastry_plain.point_key(name) for name in ("ASC", "MC")}
        | {synastry_plain.aspect_frame_key(name) for name, *_ in ASPECTS}
        | {synastry_plain.bond_key(*pair) for pair in SYNASTRY_CORE_BONDS}
    )


SYNASTRY = PlainCorpus(
    system="synastry",
    entries=synastry_plain.SYNASTRY_READINGS,
    openers={
        "summary": synastry_plain.SYNASTRY_SUMMARY_OPENER,
        "summary_none": synastry_plain.SYNASTRY_SUMMARY_NONE_OPENER,
    },
    closers=synastry_plain.SYNASTRY_TIER_CLOSERS,
    # 分带符号直接是赋分表自己的 `SYNASTRY_ASPECT_DELTA[type]`（1.5/2.0/3.0/-2.5/-2.0，
    # 无一为 0，所以 band 分支的 0 值闸在这套数据上永不触发；真触发说明有人改了表）。
    # 「顺的一侧在前」因此就是表说的「和谐在前、挑战在后」，白话层没有自己排过一次序（G2）。
    grouping="band",
    universe=_synastry_universe,
    slot_prefixes=frozenset({"synastry.point."}),
)


def _meihua_universe() -> set[str]:
    """三张源表键的全集：5 体用 + 8 卦 + 5 状态 = 18。

    不抄数、不写字面量清单：`TIYONG_RELATIONS` / `BAGUA_IMAGE` / `WANGSHUAI_TEXT`
    加一格，本函数就跟着多一格，语料少写一条即红（工厂的 `set(entries) == universe()`）。
    条数复测：`cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "from app.engines.plain_corpora import MEIHUA; print(len(MEIHUA.universe()))"` → 18。
    """
    return (
        {tiyong_key(key) for key in TIYONG_RELATIONS}
        | {leixiang_key(key) for key in BAGUA_IMAGE}
        | {wangshuai_key(state) for state in WANGSHUAI_TEXT}
    )


MEIHUA = PlainCorpus(
    system="meihua",
    entries=MEIHUA_READINGS,
    openers={"summary": MEIHUA_SUMMARY_OPENER},
    closers=MEIHUA_TIER_CLOSERS,
    # 「休」的 delta 是 0（`engines/meihua.py` 的 `_wangshuai_delta`），八卦类象本就无吉凶符号：
    # 按符号分带会让这两类条目两头都不进，句子无声消失（spec §6 给梅花选 keep 的全部理由，
    # 钉在 `tests/golden/test_meihua_golden.py::test_the_zero_delta_gua_qi_row_still_gets_its_sentence`）。
    grouping="keep",
    universe=_meihua_universe,
)


def _kabbalah_universe() -> set[str]:
    """卡巴拉的键全集 = 10 原质 + 隐藏 Daath + 22 路径 = 33，全部照节点自己的 `id`。

    不写第二份名单：`content/kabbalah.py:98,223` 是 `id` 的唯一构造处，源表加一格而表少一句
    即红（工厂的 `set(entries) == universe()`）。条数复测：`cd backend && PYTHONIOENCODING=utf-8
    .venv/Scripts/python.exe -c "from app.engines.plain_corpora import KABBALAH; print(len(KABBALAH.universe()))"` → 33。
    """
    return {node.id for node in (*SEPHIROTH, DAATH)} | {node.id for node in PATHS}


KABBALAH = PlainCorpus(
    system="kabbalah",
    entries=kabbalah_plain.KABBALAH_READINGS,
    # 卡巴拉的白话挂在**节点自身**（`SephirahNode.plain_meaning` / `PathNode.plain_meaning`），
    # 页面上一次只看一个节点，没有段落容器，所以没有开篇句可用——硬造一句就是
    # 一句永远不会被印出来的死字（spec §13「漂到引擎永远不触发的键上」）。
    # 工厂对这一形状显式登记例外，见 `tests/test_plain_corpora.py::SECTIONLESS`。
    openers={},
    # 生命之树无分数、无档位（spec §7 只要求转述表），收尾句因此为 None，
    # 装配器不许替它补一句总吉凶（G2）。
    closers=None,
    # 33 条里没有任何吉凶符号可分带：`grouping` 取 keep，未来若接入 T3 之外的整段装配，
    # 次序由调用方决定，不由白话层排序。
    grouping="keep",
    universe=_kabbalah_universe,
)


def _ziwei_universe() -> set[str]:
    """紫微的键全集 = 14 主星 + 14 乙级 + 4 四化标记 = 32。

    宫名不在这里：十二宫的一句是小节开篇句不是条目（G22），出现在 entries 里就是
    同一个宫在同一段说两遍。条数复测：`cd backend && PYTHONIOENCODING=utf-8
    .venv/Scripts/python.exe -c "from app.engines.plain_corpora import ZIWEI; print(len(ZIWEI.universe()))"` → 32。
    """
    return (
        {ziwei_plain.star_key(name) for name in MAJOR_STARS}
        | {ziwei_plain.star_key(name) for name in MINOR_STARS}
        | {ziwei_plain.sihua_key(label) for label in SIHUA_LABELS}
    )


ZIWEI = PlainCorpus(
    system="ziwei",
    entries=ziwei_plain.ZIWEI_READINGS,
    # 十二宫开篇句。键 = `PALACE_NAMES` 逐字，覆盖面由
    # `tests/content/test_ziwei_plain_corpus.py::test_openers_are_exactly_the_twelve_palace_names` 钉。
    openers=ziwei_plain.ZIWEI_PALACE_OPENERS,
    # 斗数整盘无分数、无档位（spec §13 的明面代价）：白话只说倾向，不补一句综合吉凶。
    closers=None,
    # G21：`band` 分支遇 0 值符号直接 `ValueError`，而星情没有任何符号可传；次序 = 宫位序
    # （引擎按地支 index 0-11 逐宫装配，宫内按 `STAR_ORDER` 的安星序）。
    grouping="keep",
    universe=_ziwei_universe,
)


def _qimen_universe() -> set[str]:
    """奇门的键全集 = 9 星 + 8 门 + 8 神 = 25。

    九宫不在这里：宫的一句是小节开篇句不是条目（G22）。天禽本宫不坐，只随「寄坤二」那一枚
    入段（`engines/qimen.py:168-170` 那句 `stars.append`），全盘落一次；就算它落两次，键也仍然只有一个——
    `universe()` 按名字取，不按落宫次数取。
    条数复测：`cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "from app.engines.plain_corpora import QIMEN; print(len(QIMEN.universe()))"` → 25。
    """
    return (
        {qimen_plain.star_key(star.name) for star in NINE_STARS}
        | {qimen_plain.door_key(door.name) for door in EIGHT_DOORS}
        | {qimen_plain.god_key(god) for god in EIGHT_GODS}
    )


QIMEN = PlainCorpus(
    system="qimen",
    entries=qimen_plain.QIMEN_READINGS,
    # 九宫开篇句。键 = `LUOSHU[*].gua` 逐字（含中宫的 `中`），覆盖面由
    # `test_qimen_plain_corpus.py::test_openers_are_exactly_the_nine_luoshu_gua` 钉。
    openers=qimen_plain.QIMEN_PALACE_OPENERS,
    # 盘面不打分、不判档位（spec §13）：白话逐宫说话，不补一句综合吉凶。
    closers=None,
    # 偏差表第 1 行：`LUOSHU` 没有 luck 字段、`EIGHT_DOORS` 两条「中平」，`band` 分支
    # 遇 0 值符号直接 `ValueError`——所以 `keep`，次序 = 引擎的读盘序「星→门→神」。
    grouping="keep",
    universe=_qimen_universe,
)


def _lenormand_universe() -> set[str]:
    """雷诺曼的键全集 = 36 张牌的 `id`（源表现成的字段，不二次转写）。

    五阵 id 不在这里：阵的一句是小节开篇句不是条目（G22）。条数复测：
    `cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "from app.engines.plain_corpora import LENORMAND; print(len(LENORMAND.universe()))"` → 36。
    """
    return {card.id for card in CARDS}


LENORMAND = PlainCorpus(
    system="lenormand",
    entries=lenormand_plain.LENORMAND_READINGS,
    # 五阵开篇句。键 = `SPREADS` 的 id，覆盖面由
    # `test_lenormand_plain_corpus.py::test_openers_are_exactly_the_five_spread_ids` 钉。
    openers=lenormand_plain.LENORMAND_SPREAD_OPENERS,
    # 综合判读由 `synthesis` 承担（`engines/lenormand.py:98`），白话不再补档位结论。
    closers=None,
    # 极性三档里有 0（28 男人 / 29 女人两张指示牌），`band` 分支遇 0 值符号直接
    # `ValueError`；而牌阵的读序本来就是位序（第 1 张 → 第 n 张），`keep` 正是它。
    grouping="keep",
    universe=_lenormand_universe,
)


#: 周易的登记表：514 条 = 450 条逐爻今译（64 卦辞 + 384 爻辞 + 用九/用六）+ 64 条整卦总论。
#: 两张表在 `zhouyi_plain.py` 里分开存，工厂吃的是合并后的 `corpus_entries()`。
#: 分解数复测：
#: `cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "from app.content.zhouyi_guaci import GUA_CI, YONG_CI; from app.content.zhouyi_text import YAO_CI; print(len(GUA_CI), sum(len(v) for v in YAO_CI.values()), len(YONG_CI))"` → 64 384 2。
ZHOUYI = PlainCorpus(
    system="zhouyi",
    entries=zhouyi_plain.corpus_entries(),
    # 今译挂在卦辞那一行与六条爻行自身，页面上没有段落容器（spec §5 与卡巴拉同形）：
    # 硬造一句开篇句就是一句永远不会被印出来的死字，所以是 `{}` 并进 `SECTIONLESS` 登记。
    openers={},
    # 六爻无分数、无档位（spec §7 规则 5）：白话只说倾向，不替读者补一句综合吉凶。
    closers=None,
    # 514 条没有任何吉凶符号可分带，而 `band` 分支遇 0 值符号直接 `ValueError`（第一期
    # delta=0 静默丢句那条坑的机器化防线）；读序本来就是卦内爻序（初 → 上），`keep` 正是它。
    grouping="keep",
    # 键全集由聚合面从三张源表（`GUA_CI` / `YONG_CI` / `YAO_CI`）加卦表现算，这里不写第二份
    # 算法：源表多一条而今译少一句，工厂的 `set(entries) == universe()` 立刻红。
    # 条数复测：`cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "from app.engines.plain_corpora import ZHOUYI; print(len(ZHOUYI.universe()))"` → 514。
    universe=zhouyi_plain.corpus_universe,
)


def _western_universe() -> set[str]:
    """西洋本命的键全集 = spec §5.3 那十条键式，基数全部从 content/engines 现算，不写字面量清单。

    542 = 120 落座 + 120 落宫 + 225 相位 + 24 轴座 + 12 交点座 + 12 交点宫 + 12 宫题
          + 4 元素 + 3 形态 + 10 逆行。条数复测：
    `cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "from app.engines.plain_corpora import WESTERN; print(len(WESTERN.universe()))"` → 542。
    分族基数复测：
    `cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "from itertools import combinations; from app.engines.western import ASPECTS, PLANETS; print(len(list(combinations(PLANETS,2))), len(ASPECTS))"` → 45 5（225 = 45×5）。

    元素与形态的名册从 `SIGN_ELEMENT`/`SIGN_MODALITY` 用 `dict.fromkeys` 去重取，不写四串三串：
    那两张表是 `SIGNS` 的平行数组（`engines/western.py:61-62`），星座表一动这里自动跟着动，
    写字面量清单就是把「十二个星座各属哪一格」这件事抄第二遍。
    """
    planet_names = [name for name, *_ in PLANETS]
    aspect_names = [aspect[0] for aspect in ASPECTS]
    return (
        {western_plain.planet_sign_key(planet, sign) for planet, sign in product(planet_names, SIGNS)}
        | {western_plain.planet_house_key(planet, house) for planet, house in product(planet_names, range(1, 13))}
        | {
            western_plain.aspect_key(first, second, aspect)
            for (first, second), aspect in product(combinations(planet_names, 2), aspect_names)
        }
        # 两轴写字面量而不是取 `compute_western_chart` 的 `axes`：那张表恒含 DES/IC 四枚（`engines/western.py:306-307`
        # 就是 `ascendant + 180` 算出来的镜像），而 spec §2 刻意不建 DES/IC 与南交点。同一处形状
        # 的先例是 `_synastry_universe` 里那两枚 `("ASC", "MC")`（本文件上方 `SYNASTRY` 登记前的
        # import 注），漂了由 `test_western_plain_corpus.py` 的轴族对账门抓。
        | {western_plain.axis_sign_key(axis, sign) for axis, sign in product(("ASC", "MC"), SIGNS)}
        | {western_plain.node_sign_key(sign) for sign in SIGNS}
        | {western_plain.node_house_key(house) for house in range(1, 13)}
        | {western_plain.house_theme_key(house) for house in range(1, 13)}
        | {western_plain.element_key(element) for element in dict.fromkeys(SIGN_ELEMENT)}
        | {western_plain.modality_key(modality) for modality in dict.fromkeys(SIGN_MODALITY)}
        | {western_plain.retrograde_key(planet) for planet in planet_names}
    )


#: 西洋本命白话的登记表：542 条自撰判语（spec 裁定 R46「自撰 + 诚实双署」）。
#: **从 T1 到 T14 刻意不进 `PLAIN_CORPORA`，登记行在 T15 补上**——提前登记会让工厂的
#: `set(entries) == universe()` 从 T1 红到 T14（`universe()` 是全量算的，语料是一批批建的）。
#: 那十四批的口径由 `tests/content/test_western_plain_corpus.py` 逐条守着，那 542 例不依赖
#: 登记，所以「登记被撤销/忘了加」这一类失败在本系统里仍有一条独立验证（同一立意的先例见
#: `tests/content/test_zhouyi_plain_corpus.py:85` 那条刻意重复的契约测；本系统对应的那颗钉是
#: 同文件的 `test_the_corpus_is_registered_under_its_own_system_name`）。
WESTERN = PlainCorpus(
    system="western",
    entries=western_plain.WESTERN_READINGS,
    # 八个小节 + 两条空态开篇句，共十条；键名就是 `build_plain` 传给 `compose()` 的 section 名。
    openers=western_plain.WESTERN_OPENERS,
    # 本命盘没有分数账本（spec 裁定 R48）：三页一律不给「这盘好不好」的总结句，
    # 而 `plain_compose.py:72-74` 那条 `ValueError` 正是为了拦「由合成器补一句结论」。
    closers=None,
    # 不分带（spec §6 三条理由：丙组三条语料今天全是 keep；`band` 分支遇 0 值符号直接崩而落座/
    # 宫题/元素没有符号；页尾块的次序应按盘面既有次序，重排本身就是一种判断）。
    grouping="keep",
    universe=_western_universe,
)


def _transit_universe() -> set[str]:
    """行运三层的键全集 = spec §5.3 那四行键式，基数全部从 content/engines 现算。

    648 = 600（10 移动星 × 12 本命点 × 5 相位）+ 12 推运月亮落座 + 12 推运月亮落宫 + 24 推运两轴。
    复测：`cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "from app.engines.plain_corpora import TRANSIT; print(len(TRANSIT.universe()))"` → 648。
    移动星名取 `PLANETS`，本命点取「十星 + ASC/MC」——这两枚的字面与 `_AXIS_ZH` 的一致性由
    `tests/content/test_transit_plain_corpus.py::test_the_key_builders_are_the_only_key_source`
    的轴对账钉守住（T2 整改轮 1 B1 补上；此前这里指向 `tests/golden/test_transit_golden.py` 的
    「已有轴钉」是假话，该文件没有任何轴测）。本模块是生产代码，不 import 引擎私有量
    （AGENTS §1 的依赖方向；`tests/plain_corpora` 的工厂测同样不引）——`_natal_points` 是
    函数内局部构造，没有可 import 的常量。
    """
    planet_names = [name for name, *_ in PLANETS]
    aspect_names = [aspect[0] for aspect in ASPECTS]
    natal_points = (*planet_names, "ASC", "MC")
    return (
        {transit_plain.aspect_key(moving, natal, aspect)
         for moving, natal, aspect in product(planet_names, natal_points, aspect_names)}
        | {transit_plain.progressed_moon_sign_key(sign) for sign in SIGNS}
        | {transit_plain.progressed_moon_house_key(house) for house in range(1, 13)}
        | {transit_plain.progressed_axis_key(axis, sign) for axis, sign in product(("ASC", "MC"), SIGNS)}
    )


#: 行运三层白话的登记表：648 条自撰判语（Plan G spec 裁定 R46/R47/R48，与 `WESTERN` 同一条
#: 诚实形状）。**从 T2 到 T22 刻意不进 `PLAIN_CORPORA`，登记行在 T23 补上**——提前登记会让工厂的
#: `set(entries) == universe()` 从 T2 红到 T22（`universe()` 是全量算的，语料是一批批建的）。
#: 那二十一批的口径由 `tests/content/test_transit_plain_corpus.py` 逐条守着，那 7×条数 例不依赖
#: 登记；「早登记」与「漏分流」两侧的形状由同文件的
#: `test_the_corpus_is_not_registered_while_batches_land` 一颗钉同时守住。
#: content import 只引聚合面所在的那一个模块（`transit_plain` 内部已经 `import transit_plain_aspect`
#: 并完成合并，与 `WESTERN` 同形；多引一枚 `transit_plain_aspect` 就是未使用的 import）。
TRANSIT = PlainCorpus(
    system="transit",
    entries=transit_plain.TRANSIT_READINGS,
    # 五个小节 + 三条空态开篇句，共八条；键名就是 `build_plain` 要传给 `compose()` 的 section 名。
    openers=transit_plain.TRANSIT_OPENERS,
    # 三层都不给分数账本（spec 裁定 R48）：页面不许由合成器补一句「这段时间好不好」的总结句，
    # 而 `plain_compose.py:72-74` 那条 `ValueError` 正是为了拦「由合成器补一句结论」。
    closers=None,
    # 不分带（`band` 分支遇 0 值符号直接 `ValueError` 而相位条目没有符号可传，`plain_compose.py:64-67`；
    # `keep` 分支不看符号，所以 `items` 的符号位一律传 `0`——这条形状写在 spec 裁定 R48）。
    grouping="keep",
    universe=_transit_universe,
)


def _vedic_universe() -> set[str]:
    """吠陀键全集 = spec §5.3 那四行键式，基数全部从 content 现算。

    252 = 108（9 曜 × 12 座）+ 108（9 曜 × 12 宫）+ 27（宿）+ 9（主事星）。
    宿键与主事星键都**不乘曜数**：一宿服务九曜 + 命度，一颗主事星服务大运与小运
    （`vedic_plain` 头注的「一张表服务多行」）。复测：
    `cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "from app.engines.plain_corpora import VEDIC; print(len(VEDIC.universe()))"` → 252。
    """
    grahas = [graha.name for graha in GRAHAS]
    return (
        {vedic_plain.gruha_sign_key(graha, sign) for graha, sign in product(grahas, SIGNS_EN)}
        | {
            vedic_plain.gruha_house_key(graha, house)
            for graha, house in product(grahas, range(1, 13))
        }
        | {vedic_plain.nakshatra_key(nak.name_en) for nak in NAKSHATRAS}
        | {vedic_plain.dasha_lord_key(graha) for graha in grahas}
    )


#: 吠陀白话的登记表：252 条自撰判语（spec 裁定 R46/R47/R48，与 WESTERN/TRANSIT 同一条
#: 诚实形状）。T1-T7 建表期间刻意不进 `PLAIN_CORPORA`——提前登记会让工厂的
#: `set(entries) == universe()` 从第一批红到第七批；那七批的口径由
#: `tests/content/test_vedic_plain_corpus.py` 逐条守着。登记行在 T8 落地，同一文件的三颗
#: 登记钉继续守着「登记行被误删」与「G31/G36 分流被改名」两种静默形状。
VEDIC = PlainCorpus(
    system="vedic",
    entries=vedic_plain.VEDIC_READINGS,
    openers=vedic_plain.VEDIC_OPENERS,
    closers=None,
    grouping="keep",
    universe=_vedic_universe,
)


#: 系统词表到 corpus 的唯一映射。新系统在本表登记一行即接入工厂，测试文件不改——
#: 除登记在 `SECTIONLESS` 里的形状例外（无小节系统必须 `openers == {}`）。
PLAIN_CORPORA: dict[str, PlainCorpus] = {
    BAZI.system: BAZI,
    NAME.system: NAME,
    SYNASTRY.system: SYNASTRY,
    MEIHUA.system: MEIHUA,
    KABBALAH.system: KABBALAH,
    ZIWEI.system: ZIWEI,
    QIMEN.system: QIMEN,
    LENORMAND.system: LENORMAND,
    ZHOUYI.system: ZHOUYI,
    WESTERN.system: WESTERN,
    TRANSIT.system: TRANSIT,
    VEDIC.system: VEDIC,
}
