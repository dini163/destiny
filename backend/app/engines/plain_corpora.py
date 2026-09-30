"""白话语料的唯一登记处（多系统白话 spec §4）。

只做一件事：把 `content/` 里的纯表塞进 `PlainCorpus`，让 `tests/test_plain_corpora.py`
的机检工厂按参数化跑遍每一张表。这里**不产句子、不判命**，也不许出现第二份键名——
`universe()` 一律从源表现算，条目数与键集合因此不可能和源表漂开（少建、多建同样红）。
"""

from __future__ import annotations

from app.content import name_plain
from app.content.bazi_dimensions import DIMENSION_RULES
from app.content.bazi_plain import DIMENSION_OPENERS, PLAIN_READINGS, TIER_CLOSERS
from app.content.name_numerology import NUMBERS
from app.content.name_sancai import SANCAI_RELATIONS
from app.engines.plain_compose import PlainCorpus


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

#: 系统词表到 corpus 的唯一映射。新系统在本表登记一行即接入工厂，测试文件不改。
PLAIN_CORPORA: dict[str, PlainCorpus] = {
    BAZI.system: BAZI,
    NAME.system: NAME,
}
