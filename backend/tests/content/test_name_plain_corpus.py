"""姓名学白话表的闸：只钉工厂钉不住的那两种失败。

措辞、键集合、开篇句与档位句的形状全在 `tests/test_plain_corpora.py` 的参数化工厂里跑，
本文件不重断第二遍（AGENTS.md §2）。工厂看不见的是**键覆盖**与**档位词表**：前者是登记表
`X.system: X` 的两行同 `system` 时 Python 静默留最后一行，前一张表就此掉出闸外，而工厂的两条
形状断言（条数 == 去重条数、键 == corpus.system）照样绿；后者是 `PlainCorpus` 只有条目的
`universe` 钩子，没有档位钩子（控制器裁定 R25：四家档位来源各不相同——两张 tier 表的并集、
一个阈值 tuple、一个函数的像——抽成钩子等于每个系统再写一遍那个可调用物，故 G3 由各系统
自己的测钉）。所以两条都由消费方自证。
"""

from app.content.name_plain import NAME_GRID_OPENERS
from app.engines.name_numerology import GRID_LABELS, SANCAI_TIERS, SCORE_TIERS
from app.engines.plain_corpora import NAME, PLAIN_CORPORA


def test_name_corpus_is_the_one_the_registry_holds() -> None:
    assert PLAIN_CORPORA["name"] is NAME


def test_closers_cover_exactly_the_tiers_the_engine_prints() -> None:
    """G3（spec §5 规则 6）：收尾句键集合 == `SCORE_TIERS ∪ SANCAI_TIERS` 的档位名，一个不多一个不少。

    条数复测：`cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "from app.engines.name_numerology import SCORE_TIERS, SANCAI_TIERS; print(len(SCORE_TIERS), len(SANCAI_TIERS))"` → `5 4`。
    """
    assert set(NAME.closers) == {name for _, name in SCORE_TIERS} | {name for _, name in SANCAI_TIERS}


def test_grid_openers_cover_exactly_the_grids_the_engine_prints() -> None:
    """开篇句键集合 == 引擎实际印出的五格（裁定 R31）。

    工厂只比 `entries` 与 `universe()`，框架句的覆盖面各系统自钉（同 G3/R25 的分工）：
    `content/name_plain.py:32` 那句「键与 `GRID_LABELS` 同集合」今天为真却无人守——格子名一旦
    增删或拼错，开篇句会静默少一格而工厂仍绿。本条钉的是表的形状，不是装配输出，所以住这里
    而不是 golden。复测：`cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "from app.content.name_plain import NAME_GRID_OPENERS; from app.engines.name_numerology import GRID_LABELS; print(sorted(NAME_GRID_OPENERS), sorted(GRID_LABELS))"`
    """
    assert set(NAME_GRID_OPENERS) == set(GRID_LABELS)
