"""白话装配器（多系统白话 spec §3）：把已命中键的受控转述句拼成一段人话。

第一期八字的 `build_plain` 是本层的一个实例，本模块把它通用的那一半提出来。四条
立身规矩：① 表住在 `content/`、装配住在 `engines/`（`PlainCorpus` 是 dataclass，
若在 content 构造就成了 content 引 engines，违反 AGENTS.md §1 的单向分层）；
② 本模块**不收账本对象、不查 delta**，分带符号由调用方算好传入，它不知道任何系统
账本的存在；③ 句子逐字搬运，拼接处不加连接词、不现编中文；④ 未知键 `KeyError`
（宁崩不漏），band 分支遇 0 值符号 `ValueError`（第一期 delta=0 静默丢句那条坑的
机器化防线，复测：`cd backend && grep -rn "delta != 0" tests/content/test_bazi_plain_corpus.py`）。
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class PlainCorpus:
    """一个系统的白话语料：条目表 + 小节开篇句 + 档位收尾句 + 装配口径。

    `grouping` 用字面量而不是 `band=0` 兼作「不分带」：梅花 4 条候选条目里「休」的
    delta 就是 0（`engines/meihua.py:330`），八卦类象本无吉凶符号，把它按 0 分带等于
    静默丢句（白话 spec §6）。`slot_prefixes` 是槽位词表的前缀（合盘的 12 个点义是
    「自我与生命方向」这类名词短语，不是整句白话），措辞机检对它们换一套口径——
    没有这个开关，工厂要么对 12 条词表假红，要么被整体放松（spec 裁定 R6）。
    """

    system: str
    entries: Mapping[str, str]
    openers: Mapping[str, str]
    closers: Mapping[str, str] | None
    grouping: Literal["band", "keep"]
    universe: Callable[[], set[str]]
    slot_prefixes: frozenset[str] = frozenset()


def is_slot_key(corpus: PlainCorpus, key: str) -> bool:
    """该键是否属于槽位词表（机检工厂据此选口径）。"""
    return any(key.startswith(prefix) for prefix in corpus.slot_prefixes)


def reading(corpus: PlainCorpus, key: str) -> str:
    """按键逐字取白话。未知键是编程错误而不是用户错误，所以崩而不兜底。"""
    try:
        return corpus.entries[key]
    except KeyError as exc:
        raise KeyError(f"{corpus.system} 未知白话键：{key}") from exc


def compose(
    corpus: PlainCorpus,
    section: str,
    items: Sequence[tuple[str, int | float]],
    tier: str | None = None,
) -> str:
    """命中键 → 一段白话：开篇句 + 条目逐字 + 收尾句，段间换行，不现编任何短语。

    `band` 先顺后逆、同侧保持传入次序，且**遇 0 值符号直接崩**：装配器按符号分两侧时，
    0 会两头都不进，句子无声消失。`keep` 按传入原序、不看符号。
    """
    parts = [corpus.openers[section]]
    if corpus.grouping == "band":
        zeros = [key for key, sign in items if sign == 0]
        if zeros:
            raise ValueError(f"{corpus.system} 的 {section} 段有 0 值符号条目，白话会静默丢句：{zeros}")
        parts += [reading(corpus, key) for key, sign in items if sign > 0]
        parts += [reading(corpus, key) for key, sign in items if sign < 0]
    else:
        parts += [reading(corpus, key) for key, _sign in items]
    if tier is not None:
        if corpus.closers is None:
            raise ValueError(f"{corpus.system} 无档位词表，收尾结论不许由合成器补，白话层不新增判断")
        parts.append(corpus.closers[tier])
    return "\n".join(parts)


def compose_template(frame: str, slots: Mapping[str, str]) -> str:
    """框架句 + 受控槽位词条 → 整句白话（合盘 720 键的唯一可行形状，spec §6）。

    frame 里只准出现名词与机制描述，吉凶由被填进来的词条自身携带（spec §5 规则 5）；
    缺槽位词条 `KeyError`，与 `reading` 同一个「宁崩不漏」口径。
    """
    return frame.format(**slots)


def overview(frame: str, parts: Mapping[str, str]) -> str:
    """总论：框架句 + 逐字搬运的部件。部件本身可以是别处已装配好的整段。"""
    return frame.format(**parts)


def dedupe(items: Sequence[tuple[str, int]]) -> list[tuple[str, int]]:
    """同键只留首次出现的那一条，符号与原序不动。

    压的是**重复**不是内容：两格同数（或两对同关系）时逐条搬运会让同一句在同一段里
    连说两三遍。键集合的完整性由机检工厂的 `set(entries) == universe()` 守（spec §4），
    本函数不参与其中任何一条判断。
    """
    seen: set[str] = set()
    kept: list[tuple[str, int]] = []
    for key, sign in items:
        if key not in seen:
            seen.add(key)
            kept.append((key, sign))
    return kept
