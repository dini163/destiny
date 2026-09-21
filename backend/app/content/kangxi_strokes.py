"""康熙笔画语料的运行时入口：读固化产物 + 做纯推导，绝不联网、绝不猜数。

产物由 `tools/build_kangxi_corpus.py` 从官方 Unihan 一次性生成（spec §5.1）。本模块
唯一的算术是 `kangxi_strokes = 部首画数 + 部首外余画`——把它写成推导而不是第三个
真相，是为了让 T1 的产物里不存在"两个字段互相矛盾"的可能（spec §5.2）。

全项目的笔画都必须走 `lookup()`；任何模块自己数笔画 = 违反铁律。
"""

from __future__ import annotations

import json
import unicodedata
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
_STROKES_PATH = _DATA_DIR / "kangxi_strokes.json"
_RADICALS_PATH = _DATA_DIR / "kangxi_radicals.json"

#: 每个笔画数字在页面上都要署这一句：它是推导量，不是谁手抄的事实。
STROKE_SOURCE = (
    "《康熙字典》部首体系笔画（Unihan kRSUnicode + kTotalStrokes 推导，非手抄）"
)

#: 带调元音的分解符号 → (调号, 调名)。NFD 拆解后按符号定调，省掉 24 行手抄对照表。
#: 写成转义而非裸组合符号：这些字符在编辑器里看不见，裸写无法 review、也容易被
#: 任何一次"顺手格式化"吃掉（Windows/GBK 终端尤其如此）。
_MARK_TO_TONE = {
    "\u0304": (1, "阴平"),  # ˉ  macron
    "\u0301": (2, "阳平"),  # ˊ  acute
    "\u030c": (3, "上声"),  # ˇ  caron
    "\u0300": (4, "去声"),  # ˋ  grave
}


@dataclass(frozen=True)
class PinyinReading:
    """一个读音。姓氏多音（单/解/曾）如实给多条，UI 全展示，不替用户选。"""

    pinyin: str
    tone_number: int
    tone_name: str


@dataclass(frozen=True)
class StrokeEntry:
    char: str
    radical_no: int
    residual_strokes: int
    radical_char: str
    radical_strokes: int
    readings: tuple[PinyinReading, ...]
    traditional: tuple[str, ...]
    simplified: tuple[str, ...]
    kangxi_strokes: int
    in_corpus: bool


@dataclass(frozen=True)
class CorpusMeta:
    unicode_version: str
    corpus_date: str
    size: int
    source: str


@dataclass(frozen=True)
class _RawCorpus:
    meta: CorpusMeta
    #: 部首号 → (部首字形, 康熙画数)。只在这里解析一次，radical_* 与 entries 同源。
    radicals: dict[int, tuple[str, int]]
    entries: dict[str, StrokeEntry]


@lru_cache(maxsize=1)
def _raw() -> _RawCorpus:
    with _STROKES_PATH.open(encoding="utf-8") as handle:
        strokes = json.load(handle)
    with _RADICALS_PATH.open(encoding="utf-8") as handle:
        radicals_doc = json.load(handle)

    radicals = {int(row["radical_no"]): (str(row["char"]), int(row["strokes"])) for row in radicals_doc["items"]}
    meta = CorpusMeta(
        unicode_version=str(strokes["unicode_version"]),
        corpus_date=str(strokes["corpus_date"]),
        size=int(strokes["size"]),
        source=str(strokes["source"]),
    )

    entries: dict[str, StrokeEntry] = {}
    for item in strokes["items"]:
        char = str(item["char"])
        radical_no = int(item["radical_no"])
        residual = int(item["residual"])
        radical_char, radical_stroke = radicals[radical_no]
        readings = tuple(
            PinyinReading(pinyin=bare, tone_number=number, tone_name=name)
            for bare, number, name in (tone_of(str(text)) for text in item["pinyin"])
        )
        entries[char] = StrokeEntry(
            char=char,
            radical_no=radical_no,
            residual_strokes=residual,
            radical_char=radical_char,
            radical_strokes=radical_stroke,
            readings=readings,
            traditional=tuple(str(text) for text in item["traditional"]),
            simplified=tuple(str(text) for text in item["simplified"]),
            kangxi_strokes=radical_stroke + residual,
            in_corpus=True,
        )
    return _RawCorpus(meta=meta, radicals=radicals, entries=entries)


def tone_of(pinyin: str) -> tuple[str, int, str]:
    """拆出裸拼音与声调。

    没有声调符号就报轻声 (5)，不去猜它是第几声——猜调等于造数据。
    """
    decomposed = unicodedata.normalize("NFD", pinyin)
    for mark, (number, name) in _MARK_TO_TONE.items():
        if mark in decomposed:
            bare = unicodedata.normalize("NFC", decomposed.replace(mark, ""))
            return bare, number, name
    return pinyin, 5, "轻声"


def lookup(char: str) -> StrokeEntry | None:
    """查一个字；`None` = 本语料范围外（扩展 B 及以后等），按未收录如实处理。"""
    return _raw().entries.get(char)


def traditional_candidates(char: str) -> list[str]:
    """简 → 繁候选。本身已是正体（无 kSimplifiedVariant 指向）时只返回自己。"""
    entry = _raw().entries.get(char)
    if entry is None or not entry.traditional:
        return [char]
    return list(entry.traditional)


def radical_strokes(radical_no: int) -> int:
    """部首自身的康熙画数——页面上"某部 N 画"那个 N。"""
    return _radical_row(radical_no)[1]


def radical_char(radical_no: int) -> str:
    """部首字形（外部康熙表的写法，未必等于该部首的正字，见构建器注释）。"""
    return _radical_row(radical_no)[0]


def _radical_row(radical_no: int) -> tuple[str, int]:
    if not 1 <= radical_no <= 214:
        raise ValueError(f"康熙部首号必须在 1..214，收到 {radical_no}")
    row = _raw().radicals.get(radical_no)
    if row is None:  # pragma: no cover —— 构建器保证 214 行齐全，缺行即产物被手工改坏
        raise ValueError(f"产物缺部首 {radical_no} 行；kangxi_radicals.json 不完整。")
    return row


def corpus_meta() -> CorpusMeta:
    return _raw().meta
