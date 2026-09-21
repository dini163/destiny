"""把官方 Unihan 发布推导成姓名学所用的康熙笔画语料。

用法（构建期工具，不进运行时，也不打进 wheel）：

    cd backend
    PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe tools/build_kangxi_corpus.py \\
        --unihan "C:/Users/dini1/AppData/Local/Temp/unihan/Unihan.zip" \\
        --unicode-version 18.0.0 --corpus-date 2026-07-31

两份产物都入库固化（spec 决策一：运行时不联网、可复现、可审阅）：

    data/kangxi_radicals.json   214 条 部首号 -> 正字 + 康熙画数
    data/kangxi_strokes.json    30,717 条 字 -> 部首号.部首外余画 (+读音/简繁边)

唯一推导式（spec §2.2，无一项手填）：

    康熙笔画(字) = 部首画数(kRSUnicode 首位部首号) + 部首外余画
    部首画数(N)  = kTotalStrokes(部首 N 的正字)

`kTotalStrokes` 单独用必错：它是现代物理笔画，江=6 而康熙=7（水部取 水 4 画，
不取 氵 3 画）。必须走"部首正字画数 + 余画"这条链，这是本文件的理由。
"""

from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
RADICALS_OUT = BACKEND_ROOT / "data" / "kangxi_radicals.json"
STROKES_OUT = BACKEND_ROOT / "data" / "kangxi_strokes.json"

DATA_FILES = ("Unihan_IRGSources.txt", "Unihan_Readings.txt", "Unihan_Variants.txt")

#: 取用范围（spec §5.1）：扩展 A + BMP 主体 + 兼容表意文字，再沿简繁边取闭包。
#: 范围外（扩展 B 及以后等）一律视为未收录，如实报告，不外推。
CORE_RANGES = ((0x3400, 0x4DBF), (0x4E00, 0x9FFF), (0xF900, 0xFAFF))

RADICAL_SOURCE_NOTE = (
    "Unihan kRSUnicode 首位部首号 + 该部首正字 kTotalStrokes 推导"
    "（Unicode {version}，非手抄）"
)
STROKE_SOURCE_NOTE = (
    "《康熙字典》部首体系笔画，由 Unihan kRSUnicode + kTotalStrokes 推导"
    "（Unicode {version}，{count} 条）"
)

#: 外部康熙表与 Unihan 部首正字画数不一致的行（spec §5.5）。
#: 改动推导值只有两种情形：值落在该部首候选正字的画数集合里（Unihan 内部另有正字），
#: 或理由里附了出处链接（外部表与 Unihan 冲突）。两者皆无 = 凭空发明数字，构建器拒绝。
#: 计划期已用 `data/kangxi_radicals.json` 与外部表逐行对拍，实测 214 行只有这一行冲突：
RADICAL_STROKE_OVERRIDES: dict[int, tuple[int, str]] = {
    114: (
        5,
        "《康熙字典》禸部为五画部首（https://zh.wikipedia.org/wiki/禸部，2026-09-21 取），"
        "Unihan kTotalStrokes(禸)=4。取 4 则 禹(114.4)=8、禺=8，与外部表"
        "（禹 9 画、禺 9 画）及 Unihan 自身 kTotalStrokes(禹)=9 双重矛盾；"
        "取 5 后三处全部自洽，故判 Unihan 的 禸 画数为异常。",
    ),
}

#: 部首展示字形（溯源表里的"部首"列）。Unihan 里没有独立的康熙部首字形字段，
#: kIICore 优先规则会选到通用字而非部首本字；外部表给出正确的部首字形，逐条登记。
#: 实测冲突 4 行：47 巛/川、52 幺/乡、146 襾/西、174 靑/青。
#: 只改字形显示，不改画数——这四行两侧画数相同（对拍后 214 行画数零冲突）。
RADICAL_LABEL_OVERRIDES: dict[int, tuple[str, str]] = {
    47: ("巛", "外部康熙部首表第 47 字作 巛；Unihan 正字取到通用字 川。"),
    52: ("幺", "外部康熙部首表第 52 字作 幺；Unihan 正字取到简体 乡。"),
    146: ("襾", "外部康熙部首表第 146 字作 襾；Unihan 正字取到通用字 西。"),
    174: ("靑", "外部康熙部首表第 174 字作 靑；Unihan 正字取到通用字 青。"),
}


def parse_unihan(zip_path: Path) -> dict[str, dict[int, object]]:
    """读三个 Unihan 文件，返回 {字段名: {码位: 原值}}。

    Unihan 数据行是**三列制表符分隔**：`U+4E00<TAB>kTotalStrokes<TAB>4`（实测；行首
    `#` 开头的是注释，其中 `#\tkField` 那样的字段清单也在内）。字段名带前导 `k`
    （kTotalStrokes / kRSUnicode / kIICore / kMandarin / kSimplifiedVariant /
    kTraditionalVariant），比对时必须连 `k` 一起写——只用 `TotalStrokes` 会静默匹配
    0 行，本轮设计阶段就踩过。`kTotalStrokes` 要转 int；把它当字符串用会让画数比较
    退化成字典序（"10" < "2"），是个静默错误。
    三类字段分居三个文件（实测）：kRSUnicode/kTotalStrokes/kIICore 在 IRGSources，
    kMandarin 在 Readings，两条简繁边在 Variants——少读一个文件不报错，只让对应字段全空。
    """
    tables: dict[str, dict[int, object]] = {
        "kTotalStrokes": {},
        "kRSUnicode": {},
        "kIICore": {},
        "kMandarin": {},
        "kSimplifiedVariant": {},
        "kTraditionalVariant": {},
    }
    with zipfile.ZipFile(zip_path) as archive:
        for name in DATA_FILES:
            with archive.open(name) as handle:
                for raw in handle:
                    line = raw.decode("utf-8").rstrip("\n")
                    if not line.startswith("U+"):
                        continue
                    parts = line.split("\t")
                    if len(parts) < 3:
                        continue
                    codepoint = int(parts[0][2:], 16)
                    field, value = parts[1], parts[2].strip()
                    if field not in tables or not value:
                        continue
                    tables[field][codepoint] = int(value) if field == "kTotalStrokes" else value
    return tables


def first_radical_entry(tables: dict[str, dict[int, object]], codepoint: int) -> tuple[int, int] | None:
    """取 kRSUnicode 首位作索引部首，返回 (部首号, 部首外余画)。

    两个实测陷阱（spec §2.3）：一行可有多值且以空格分隔（`35.6 66.6`）；部首号可带
    `'`（变体部首标记，如 `120'.3`）。残差 `-1` 原样返回，由调用方按"该字即部首索引
    字形"处理——不可 +(-1)。
    """
    raw = tables["kRSUnicode"].get(codepoint)
    if not raw:
        return None
    radical_text, _, residual_text = str(raw).split()[0].partition(".")
    return int(radical_text.rstrip("'")), int(residual_text)


def pick_radical_char(tables: dict[str, dict[int, object]], members: list[int]) -> int:
    """在同属一个部首的候选正字里挑一个（spec §2.3 陷阱一）。

    不能用"画数最大者"：水(4) 与 氺(5) 同 claim 部首 85，取大者会让全部水部字 +1
    （江→8）。也不能用"最小码位"：龍(16) 会输给 竜(10)。采用序：
    有 kIICore → 在 BMP 内 → kIICore 区域数多 → kTotalStrokes 大 → 码位小。

    ⚠️ kIICore 的值是**两字母区域码直接拼接**、没有分隔符（实测 高 = `AGTJHKMP`、
    髙 = `CJ`），所以区域数 = `len(value) // 2`。按 `;` 或空格切会得到 1，两个候选
    永远平手，退到"画数大者"就会选中异体 髙(11) 而不是 高(10)，全部 高部字 +1 画。
    """
    iicore = tables["kIICore"]
    total = tables["kTotalStrokes"]

    def rank(codepoint: int) -> tuple[int, int, int, int, int]:
        return (
            1 if codepoint in iicore else 0,
            1 if 0x4E00 <= codepoint <= 0x9FFF else 0,
            len(str(iicore.get(codepoint, ""))) // 2,
            int(total.get(codepoint, 0)),
            -codepoint,
        )

    return max(members, key=rank)


#: 与外部康熙表冲突的行：(部首号, Unihan 正字, Unihan 画数, 采用画数, 出处理由)
Divergence = tuple[int, str, int, int, str]


def radical_table(tables: dict[str, dict[int, object]]) -> tuple[list[dict[str, object]], list[Divergence]]:
    """推导 214 部首的正字与康熙画数，套用带出处的 override。

    部首正字的判据是 **`部首号.0`**（该字只由这个部首组成，余画为 0），实测 214/214
    齐全：玉 = `96.0`（5 画）、水 = `85.0`（4 画）、玄 = `95.0`（5 画）。
    ⚠️ 不要用 `-1` 那批：`96.-1` 是 王、`85.-1` 是 𰛅，它们是"索引字形"，画数是现代
    物理笔画（王 4），拿它们当正字会让整部首的字全错——spec §2.3 陷阱二的 -1 是给
    *被查字* 用的规则，不是给部首正字用的。

    第二个返回值是"override 改动了推导值"的行，构建时逐行打印，供人工与外部表复核。
    """
    members_by_radical: dict[int, list[int]] = {}
    for codepoint in tables["kRSUnicode"]:
        entry = first_radical_entry(tables, codepoint)
        if entry and entry[1] == 0:
            members_by_radical.setdefault(entry[0], []).append(codepoint)

    rows: list[dict[str, object]] = []
    divergences: list[Divergence] = []
    for radical_no in range(1, 215):
        members = sorted(members_by_radical.get(radical_no, []))
        if not members:
            raise SystemExit(f"部首 {radical_no} 找不到正字（kRSUnicode `N.0`），推导链断了。")
        candidates = {int(tables["kTotalStrokes"][cp]) for cp in members if cp in tables["kTotalStrokes"]}
        char_cp = pick_radical_char(tables, members)
        strokes = int(tables["kTotalStrokes"][char_cp])
        label = chr(char_cp)
        if radical_no in RADICAL_STROKE_OVERRIDES:
            derived = strokes
            strokes, reason = RADICAL_STROKE_OVERRIDES[radical_no]
            if strokes not in candidates and "http" not in reason:
                # 画数落在 Unihan 候选之外，只可能是"外部康熙表与 Unihan 冲突"，
                # 那必须署名出处；否则就是凭空发明数字，正是本项目禁止的。
                raise SystemExit(
                    f"部首 {radical_no} 的 override {strokes} 不在 Unihan 候选画数 "
                    f"{sorted(candidates)} 内，且理由未附出处链接；拒绝凭空改数。"
                )
            if strokes != derived:
                divergences.append((radical_no, chr(char_cp), derived, strokes, reason))
        if radical_no in RADICAL_LABEL_OVERRIDES:
            label, _ = RADICAL_LABEL_OVERRIDES[radical_no]
            if ord(label) not in members:
                raise SystemExit(
                    f"部首 {radical_no} 的字形 override {label} 不是该部首的余画 0 成员；"
                    f"外部表与本推导的候选 {sorted(chr(cp) for cp in members)} 不符，拒绝采用。"
                )
        rows.append({"radical_no": radical_no, "char": label, "strokes": strokes})
    return rows, divergences


def in_core_scope(codepoint: int) -> bool:
    return any(start <= codepoint <= end for start, end in CORE_RANGES)


def corpus_scope(tables: dict[str, dict[int, object]]) -> set[int]:
    """范围内字符 + 其一跳简繁变体（spec §5.1，实测 30,717 条）。"""
    scope = {cp for cp in tables["kRSUnicode"] if in_core_scope(cp)}
    for edge in ("kSimplifiedVariant", "kTraditionalVariant"):
        for source, targets in tables[edge].items():
            if source not in scope:
                continue
            for text in str(targets).split():
                other = int(text.removeprefix("U+"), 16)
                if other in tables["kRSUnicode"]:
                    scope.add(other)
    return scope


def split_readings(raw: object) -> list[str]:
    """kMandarin 可给多个读音，以空格或逗号分隔。"""
    if not raw:
        return []
    return [item for item in str(raw).replace(",", " ").split() if item]


def split_codepoints(raw: object) -> list[int]:
    if not raw:
        return []
    return [int(text.removeprefix("U+"), 16) for text in str(raw).split()]


def chars_of(raw: object) -> list[str]:
    """把 `U+9678` 这样的变体清单转成字符列表。"""
    return [chr(codepoint) for codepoint in split_codepoints(raw)]


def check_variant_direction(tables: dict[str, dict[int, object]]) -> None:
    """自证两条变体边的方向，方向写反就拒绝产出。

    `kTraditionalVariant` 的键是**简体**、值是繁体（陆 → 陸）；
    `kSimplifiedVariant` 的键是**繁体**、值是简体（陸 → 陆）。两边都只覆盖 Unihan
    自己登记的字符，所以用两个已知样本做哨兵即可。
    把两边写反会让 陸 的 `traditional` 为空、`simplified` 为 陸 自己，于是简繁解析
    整体失效却仍返回 200——是最难发现的一类错误，必须在构建期炸掉。
    """
    def targets(field: str, char: str) -> set[str]:
        codepoint = ord(char)
        return {chr(x) for x in split_codepoints(tables[field].get(codepoint))}

    checks = (
        ("kTraditionalVariant", "陆", "陸"),
        ("kSimplifiedVariant", "陸", "陆"),
        ("kTraditionalVariant", "发", "發"),
    )
    for field, source, expected in checks:
        if expected not in targets(field, source):
            raise SystemExit(
                f"{field} 的 {source} 未指向 {expected}；"
                f"实测为 {sorted(targets(field, source))}。两条边的方向与本注释不符，拒绝产出。"
            )


def build(zip_path: Path, unicode_version: str, corpus_date: str) -> tuple[int, int, list[Divergence]]:
    tables = parse_unihan(zip_path)
    # 三个 Unihan 文件各管一类字段：kRSUnicode / kTotalStrokes / kIICore 在
    # Unihan_IRGSources.txt，kMandarin 在 Unihan_Readings.txt，两条简繁边在
    # Unihan_Variants.txt。少读一个文件不会报错，只会让对应字段全空——
    # 于是拼音列全空、简繁解析整体失效却仍返回 200，所以在此逐个验空。
    for field, table in tables.items():
        if not table:
            raise SystemExit(f"{field} 一行都没读到：DATA_FILES 少了承载它的 Unihan 文件。")
    check_variant_direction(tables)
    radicals, divergences = radical_table(tables)
    strokes_by_radical = {int(row["radical_no"]): int(row["strokes"]) for row in radicals}  # type: ignore[arg-type]

    items: list[dict[str, object]] = []
    skipped = 0
    for codepoint in sorted(corpus_scope(tables)):
        entry = first_radical_entry(tables, codepoint)
        if entry is None or entry[0] not in strokes_by_radical:
            skipped += 1
            continue
        radical_no, residual = entry
        traditional = chars_of(tables["kTraditionalVariant"].get(codepoint))
        simplified = chars_of(tables["kSimplifiedVariant"].get(codepoint))
        items.append(
            {
                "char": chr(codepoint),
                "radical_no": radical_no,
                # 残差 -1 = 该字本身是部首索引字形（王 = 96.-1），余画记 0，
                # 于是恒等式 kangxi == radical_strokes + residual 对全表成立。
                "residual": 0 if residual == -1 else residual,
                "pinyin": split_readings(tables["kMandarin"].get(codepoint)),
                "traditional": traditional,
                "simplified": simplified,
            }
        )

    RADICALS_OUT.write_text(
        json.dumps(
            {
                "unicode_version": unicode_version,
                "corpus_date": corpus_date,
                "source": RADICAL_SOURCE_NOTE.format(version=unicode_version),
                "items": radicals,
            },
            ensure_ascii=False,
            indent=1,
        )
        + "\n",
        encoding="utf-8",
    )
    STROKES_OUT.write_text(
        json.dumps(
            {
                "unicode_version": unicode_version,
                "corpus_date": corpus_date,
                "size": len(items),
                "source": STROKE_SOURCE_NOTE.format(version=unicode_version, count=len(items)),
                "items": items,
            },
            ensure_ascii=False,
            indent=1,
        )
        + "\n",
        encoding="utf-8",
    )
    return len(items), skipped, divergences


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--unihan", required=True, type=Path)
    parser.add_argument("--unicode-version", required=True, help="照抄 UCD 发布页的版本号")
    parser.add_argument("--corpus-date", required=True, help="UCD 发布日期 ISO，写进产物表头")
    args = parser.parse_args()

    size, skipped, divergences = build(args.unihan, args.unicode_version, args.corpus_date)
    print(f"部首 214 行；笔画语料 {size} 条 -> {STROKES_OUT}")
    print(f"跳过（无 kRSUnicode 或部首越界）{skipped} 条 -> 未收录，如实报告")
    print(f"与 Unihan 推导值冲突、已按外部康熙表改定的行数：{len(divergences)}")
    for radical_no, char, derived, strokes, reason in divergences:
        print(f"  部首 {radical_no} {char}: {derived} -> {strokes}｜{reason}")


if __name__ == "__main__":
    main()
