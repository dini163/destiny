"""白话语料的唯一登记处（多系统白话 spec §4）。

只做一件事：把 `content/` 里的纯表塞进 `PlainCorpus`，让 `tests/test_plain_corpora.py`
的机检工厂按参数化跑遍每一张表。这里**不产句子、不判命**，也不许出现第二份键名——
`universe()` 一律从源表现算，条目数与键集合因此不可能和源表漂开（少建、多建同样红）。
"""

from __future__ import annotations

from app.content import kabbalah_plain, name_plain, synastry_plain
from app.content.bazi_dimensions import DIMENSION_RULES
from app.content.bazi_plain import DIMENSION_OPENERS, PLAIN_READINGS, TIER_CLOSERS
from app.content.kabbalah import DAATH, PATHS, SEPHIROTH
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
from app.content.synastry import SYNASTRY_CORE_BONDS
from app.engines.plain_compose import PlainCorpus

# `plain_corpora → engines/western` 是 `engines → engines`，AGENTS.md §1 只禁 `engines → api`，
# 这条合法。**不许**改成 `from app.engines.synastry import _AXIS_ZH`——`synastry.py` 反过来要
# import 本模块取 `SYNASTRY`，那就是循环。两轴的字面量因此留在 `_synastry_universe()` 里，
# 由本系统 golden 测的那条 `_AXIS_ZH` 对账条款守住它不漂。
from app.engines.western import ASPECTS, PLANETS


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

#: 系统词表到 corpus 的唯一映射。新系统在本表登记一行即接入工厂，测试文件不改——
#: 除登记在 `SECTIONLESS` 里的形状例外（无小节系统必须 `openers == {}`）。
PLAIN_CORPORA: dict[str, PlainCorpus] = {
    BAZI.system: BAZI,
    NAME.system: NAME,
    SYNASTRY.system: SYNASTRY,
    MEIHUA.system: MEIHUA,
    KABBALAH.system: KABBALAH,
}
