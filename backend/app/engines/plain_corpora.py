"""白话语料的唯一登记处（多系统白话 spec §4）。

只做一件事：把 `content/` 里的纯表塞进 `PlainCorpus`，让 `tests/test_plain_corpora.py`
的机检工厂按参数化跑遍每一张表。这里**不产句子、不判命**，也不许出现第二份键名——
`universe()` 一律从源表现算，条目数与键集合因此不可能和源表漂开（少建、多建同样红）。
"""

from __future__ import annotations

from app.content.bazi_dimensions import DIMENSION_RULES
from app.content.bazi_plain import DIMENSION_OPENERS, PLAIN_READINGS, TIER_CLOSERS
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

#: 系统词表到 corpus 的唯一映射。新系统在本表登记一行即接入工厂，测试文件不改。
PLAIN_CORPORA: dict[str, PlainCorpus] = {
    BAZI.system: BAZI,
}
