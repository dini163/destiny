"""姓名学五格剖象推导引擎（spec §6）。

纯函数：只做算术与选句。所有断语都来自 `content/`，本模块不组任何新句子；所有分数
都经 `build_ledger` 落账，本模块不返回裸数字。

失效模式集中在两处，各有闸门：① 笔画取错源——由 T1/T2 的推导链与哨兵测试守住；
② 缺数据时编出占位值——由本模块的 `None` 传播守住（一路传到前端整块不渲染）。
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass

from app.content import CONTENT_VERSION, NAME_CONTENT_SOURCES
from app.content import name_numerology as numerology
from app.content import name_plain
from app.content import name_sancai as sancai
from app.content.kangxi_strokes import (
    STROKE_SOURCE,
    corpus_meta,
    lookup,
    traditional_candidates,
)
from app.core.errors import NameInputError
from app.core.provenance import MODEL_PARAM_SOURCE
from app.engines.plain_compose import compose, dedupe, num, overview
from app.engines.plain_corpora import NAME
from app.schemas.common import ProvenanceTable, Verdict
from app.schemas.name import (
    CorpusProvenance,
    NameAnalysis,
    NameChar,
    NameGrid,
    NameInput,
    NameProvenance,
    NameReading,
    Sancai,
    SancaiElements,
    SancaiPair,
)
from app.schemas.scoring import ScoreFactor, ScoreValue, build_ledger

#: 允许进入引擎的字符集。语料范围外的汉字（扩展 B 及以后）不是非法输入：它们是
#: "确为汉字但本系统不覆盖"（spec §5.1），按未收录走 None + warning；只有非汉字
#: （拉丁、假名、符号）才报 not_han。放宽一次在这里，之后各层不再判字符集。
_HAN = re.compile(
    "[\u2e80-\u2fdf\u3005-\u3007\u3400-\u4dbf"
    "\u4e00-\u9fff\uf900-\ufaff\U00020000-\U0002fa1f]"
)

#: 渲染固定序：设计稿的五格全景图就是这个顺序。
GRID_ORDER: tuple[str, ...] = ("tian", "ren", "di", "wai", "zong")
GRID_LABELS: dict[str, str] = {
    "tian": "天格",
    "ren": "人格",
    "di": "地格",
    "wai": "外格",
    "zong": "总格",
}

#: 外格的统一式（决策二靠它免去按模态分叉）。算不出数字时公式串退回这句关系描述。
WAI_FORMULA = "总格−人格+1"

#: 综合气象指数权重（spec §6.5）。和恰为 1.0，所以指数天然落在 0..100。
GRID_WEIGHTS: dict[str, float] = {
    "tian": 0.15,
    "ren": 0.30,
    "di": 0.20,
    "wai": 0.10,
    "zong": 0.25,
}
#: 等级 → 分值。分值与权重都是本系统参数，与语料等级两段出处一起署在账本行上。
FORTUNE_SCORES: dict[str, float] = {"大吉": 100.0, "吉": 80.0, "半吉": 50.0, "凶": 0.0}
SCORE_TIERS: tuple[tuple[float, str], ...] = ((85, "上等"), (70, "中上"), (50, "中"), (30, "中下"), (0, "下"))

#: 五档 → 星级（署名模型参数，`MODEL_PARAM_SOURCE`；古籍只给定性档、不给星，单调不减：
#: 上等 5 / 中上 4 / 中 3 / 中下 2 / 下 1）。
#: 复测：`cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "from app.engines.name_numerology import NAME_STARS; print([(k, NAME_STARS[k]) for k in ('上等','中上','中','中下','下')])"`
#: → `[('上等', 5), ('中上', 4), ('中', 3), ('中下', 2), ('下', 1)]`。
NAME_STARS: dict[str, int] = {"上等": 5, "中上": 4, "中": 3, "中下": 2, "下": 1}

#: 五格 fortune 等级序（大吉 > 吉 > 半吉 > 凶），选分量最轻的一格进建议句；顺序按
#: `FORTUNE_SCORES` 的高低，不按账本 delta（凶格 delta 恰为 0，按 delta 选会选错）。
FORTUNE_RANK: dict[str, int] = {"大吉": 3, "吉": 2, "半吉": 1, "凶": 0}

#: 白话分带符号读的是 `NameFortune` 自身的序，不是账本 delta（spec 裁定 R2）：
#: delta = 权重 × `FORTUNE_SCORES`，而最低档「凶」是 0 分，所以 delta 恒 ≥ 0、命中凶格恰为 0，
#: 按 delta 分带会成建制丢句。实测 张一 的四格 delta 全为 0.0，复测：
#: `cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "from app.engines.name_numerology import analyze_name; print([f.delta for f in analyze_name('张','一').score.factors])"`
FORTUNE_SIDE: dict[str, int] = {"大吉": 1, "吉": 1, "半吉": -1, "凶": -1}
#: 三才分带复用引擎已有的 `HARMONIOUS_RELATIONS`：在其中为顺侧，不在其中为注意侧。
SANCAI_HARMONIOUS_SIDE = 1
SANCAI_CLASH_SIDE = -1
#: 「笔画未核定」没有吉凶，也就没有对家可分：它所在的段落里只有它自己一条，
#: 这个符号只用于通过 `compose` 的 band 闸（sign 0 → ValueError），不改变任何行的次序。
UNRESOLVED_SIDE = 1

#: 尾数定五行、奇偶定阴阳（spec §2.4：设计稿 5 个标签 5/5 命中，故不进语料表）。
ELEMENT_BY_TAIL: dict[int, str] = {
    1: "木", 2: "木", 3: "火", 4: "火", 5: "土",
    6: "土", 7: "金", 8: "金", 9: "水", 0: "水",
}

#: 三才只看这三对，顺序即渲染顺序。
SANCAI_PAIRS: tuple[tuple[str, str, str], ...] = (
    ("天人", "tian", "ren"),
    ("人地", "ren", "di"),
    ("天地", "tian", "di"),
)
#: 生我 / 我生 / 比和 都算顺，克算逆。
HARMONIOUS_RELATIONS: frozenset[str] = frozenset({"生我", "我生", "比和"})
#: 档位只数顺的对数，措辞是本系统划分（不进语料）。
SANCAI_TIERS: tuple[tuple[int, str], ...] = ((3, "相生和顺"), (2, "偏和"), (1, "多克"), (0, "相克失衡"))


@dataclass(frozen=True)
class GridTerm:
    """一格的名字、算式与算出的笔画和；任一参与项未知 ⇒ `value` 为 None。"""

    key: str
    label: str
    value: int | None
    formula: str


def cycle_number(total: int) -> int:
    """笔画和 > 81 时按 81 循环取数（决策五），结果必落在 81 表内。"""
    if total < 1:
        raise ValueError(f"数理必须是正整数，收到 {total}")
    return ((total - 1) % 81) + 1


def number_element(number: int) -> str:
    """五行看的是循环后的数理，不是笔画和原值：83 画即数理 2，属木。

    先 `cycle_number` 再取尾数，所以本函数对"笔画和"与"数理"两种入参同解——调用方
    少循环一次不会静默错一位。
    """
    return ELEMENT_BY_TAIL[cycle_number(number) % 10]


def number_yinyang(number: int) -> str:
    """奇阳偶阴，同样在 81 循环之后判（82 画是数理 1，属阳）。"""
    return "阳" if cycle_number(number) % 2 else "阴"


def modality_of(surname_len: int, given_len: int) -> tuple[str, str]:
    """四态与其公式说明（spec §6.2：用了哪条分支必须可核对）。"""
    surname_part = "复姓" if surname_len > 1 else "单姓"
    given_part = "单名" if given_len == 1 else "复名"
    tian = "姓末+姓首" if surname_len > 1 else "姓+1"
    di = "名+1" if given_len == 1 else "名字和"
    formula = f"天格={tian}；人格=姓末+名首；地格={di}；总格=全字笔画和；外格={WAI_FORMULA}"
    return f"{surname_part}{given_part}", formula


def _total(terms: Sequence[int | None]) -> int | None:
    """求和；任一加数未知 ⇒ 和未知（决策八：缺数据不给占位值）。"""
    known = [term for term in terms if term is not None]
    return sum(known) if len(known) == len(terms) else None


def _difference(minuend: int | None, subtrahend: int | None, extra: int = 1) -> int | None:
    if minuend is None or subtrahend is None:
        return None
    return minuend - subtrahend + extra


def _sum_formula(terms: Sequence[int | None]) -> str:
    """加法算式照实回显，缺的一侧写 '?'：页面渲染成 `16+8` 或 `?+8`。"""
    return "+".join("?" if term is None else str(term) for term in terms)


def _difference_formula(zong: int | None, ren: int | None) -> str:
    """外格能算就写 `29−24+1`；算不出就只写关系，不写 `?−?+1` 冒充算式。"""
    if zong is None or ren is None:
        return WAI_FORMULA
    return f"{zong}−{ren}+1"


def grids_of(
    surname_strokes: Sequence[int | None], given_strokes: Sequence[int | None]
) -> list[GridTerm]:
    """五格统一式（决策二：不按模态分叉），每格连同其算式一起返回。"""
    first_surname = surname_strokes[0]
    last_surname = surname_strokes[-1]
    first_given = given_strokes[0]
    all_strokes = [*surname_strokes, *given_strokes]

    tian_terms = [first_surname, 1] if len(surname_strokes) == 1 else [first_surname, last_surname]
    di_terms = [first_given, 1] if len(given_strokes) == 1 else list(given_strokes)
    ren_terms = [last_surname, first_given]

    tian = _total(tian_terms)
    ren = _total(ren_terms)
    di = _total(di_terms)
    zong = _total(all_strokes)

    return [
        GridTerm("tian", GRID_LABELS["tian"], tian, _sum_formula(tian_terms)),
        GridTerm("ren", GRID_LABELS["ren"], ren, _sum_formula(ren_terms)),
        GridTerm("di", GRID_LABELS["di"], di, _sum_formula(di_terms)),
        GridTerm("wai", GRID_LABELS["wai"], _difference(zong, ren), _difference_formula(zong, ren)),
        GridTerm("zong", GRID_LABELS["zong"], zong, _sum_formula(all_strokes)),
    ]


def grid_values(
    surname_strokes: Sequence[int | None], given_strokes: Sequence[int | None]
) -> dict[str, int | None]:
    """只要五格数值的视图（键按 `GRID_ORDER`）。"""
    return _as_mapping(grids_of(surname_strokes, given_strokes))


def _as_mapping(terms: Sequence[GridTerm]) -> dict[str, int | None]:
    return {term.key: term.value for term in terms}


def build_grid(term: GridTerm) -> NameGrid:
    """一格 → 契约对象。缺值时只署笔画出处，不编数理。"""
    if term.value is None:
        return NameGrid(
            key=term.key,
            label=term.label,
            formula=term.formula,
            value=None,
            number=None,
            fortune=None,
            yinyang=None,
            wuxing=None,
            pattern_name=None,
            verdict=None,
            source=STROKE_SOURCE,
            plain=compose(NAME, term.key, [(name_plain.NAME_UNRESOLVED_KEY, UNRESOLVED_SIDE)]),
        )
    number = cycle_number(term.value)
    entry = numerology.numerology_entry(number)
    return NameGrid(
        key=term.key,
        label=term.label,
        formula=term.formula,
        value=term.value,
        number=number,
        fortune=entry.fortune,
        yinyang=number_yinyang(number),
        wuxing=number_element(number),
        pattern_name=entry.pattern_name,
        verdict=entry.verdict,
        source=entry.source,
        plain=compose(NAME, term.key, [(name_plain.shuli_key(number), FORTUNE_SIDE[entry.fortune])]),
    )


def sancai_of(grids: dict[str, int | None]) -> Sancai | None:
    """三才只报生克关系（决策四）；天/人/地任一缺笔画 ⇒ 整块不出。"""
    elements: dict[str, str] = {}
    for key in ("tian", "ren", "di"):
        value = grids[key]
        if value is None:
            return None
        elements[key] = number_element(cycle_number(value))

    pairs: list[SancaiPair] = []
    harmony = 0
    for pair, left, right in SANCAI_PAIRS:
        relation = sancai.relation_between(elements[left], elements[right])
        item = sancai.SANCAI_RELATIONS[relation]
        pairs.append(SancaiPair(pair=pair, relation=relation, verdict=item.sentence, source=item.source))
        if relation in HARMONIOUS_RELATIONS:
            harmony += 1

    tier = next(name for threshold, name in SANCAI_TIERS if harmony >= threshold)
    plain = compose(
        NAME,
        "sancai",
        dedupe(
            [
                (
                    name_plain.sancai_key(pair.relation),
                    SANCAI_HARMONIOUS_SIDE
                    if pair.relation in HARMONIOUS_RELATIONS
                    else SANCAI_CLASH_SIDE,
                )
                for pair in pairs
            ]
        ),
        tier,
    )
    return Sancai(
        elements=SancaiElements(tian=elements["tian"], ren=elements["ren"], di=elements["di"]),
        pairs=pairs,
        tier=tier,
        plain=plain,
    )


def name_score(grids: dict[str, int | None]) -> ScoreValue | None:
    """综合气象指数 = Σ(格权重 × 等级分值)，每一格自成一行账（spec §6.5）。

    吉凶等级一律回 81 表查，这里不重建五格；任一格缺值 ⇒ 整块不出分。
    """
    known: dict[str, int] = {key: value for key, value in grids.items() if isinstance(value, int)}
    if set(known) != set(GRID_ORDER):
        return None

    contributions: list[ScoreFactor] = []
    for key in GRID_ORDER:
        entry = numerology.numerology_entry(cycle_number(known[key]))
        weight = GRID_WEIGHTS[key]
        contributions.append(
            ScoreFactor(
                rule=f"name.grid.{key}",
                label=f"{GRID_LABELS[key]} {entry.number} 数（{entry.fortune}·权重 {weight:.2f}）",
                delta=round(weight * FORTUNE_SCORES[entry.fortune], 2),
                source=f"{MODEL_PARAM_SOURCE} · 吉凶等级取自 {entry.source}",
            )
        )
    raw = sum(item.delta for item in contributions)
    tier = next(name for threshold, name in SCORE_TIERS if raw >= threshold)
    return build_ledger(base=0.0, tier=tier, contributions=contributions, base_rule="score.base")


def name_verdict(built: list[NameGrid], sancai: Sancai | None, score: ScoreValue) -> Verdict:
    """装配综合结论卡片（verdict-card spec §4）。

    档位词取 `score.tier`（`SCORE_TIERS`），星级取署名映射 `NAME_STARS`，headline/advice 套
    `name_plain` 的框架句，points 是五格 fortune + 三才 tier；本函数不现编中文。只在
    `score` 非 None 时由 `analyze_name` 调用，未核定场景整块省略（None 纪律）。
    """
    grade = score.tier
    weakest = min(built, key=lambda grid: FORTUNE_RANK[grid.fortune or "凶"])
    points = [f"{grid.label}：{grid.fortune}" for grid in built]
    if sancai is not None:
        points.append(f"三才：{sancai.tier}")
    headline = overview(name_plain.NAME_VERDICT_FRAME, {
        "grade": grade,
        "score": num(score.value),
        "outlook": name_plain.NAME_VERDICT_OUTLOOK[grade],
    })
    advice = overview(name_plain.NAME_VERDICT_ADVICE_FRAME, {
        "weak": weakest.label,
        "tier_advice": name_plain.NAME_TIER_ADVICE[grade],
    })
    return Verdict(
        grade=grade,
        stars=NAME_STARS[grade],
        headline=headline,
        points=points,
        advice=advice,
    )


def name_plain_summary(grids: Sequence[NameGrid], score: ScoreValue | None) -> str:
    """响应级总论：把各格卡上已经说过的那一句按顺/注意两侧重排，末尾落综合档位。

    算不出分（任一格缺笔画）时不带收尾句——白话层不新增判断（spec 规则 5），收尾句的键
    必须是真实存在的 `SCORE_TIERS` 档位。全案未核定（每格都算不出数）时没有可分带的条目，
    只搬「未核定」那一句：五张格卡各自说的正是同一句它。
    """
    items: list[tuple[str, int]] = []
    for grid in grids:
        if grid.number is None or grid.fortune is None:
            continue
        items.append((name_plain.shuli_key(grid.number), FORTUNE_SIDE[grid.fortune]))
    if not items:
        return compose(NAME, "summary", [(name_plain.NAME_UNRESOLVED_KEY, UNRESOLVED_SIDE)])
    tier = None if score is None else score.tier
    return compose(NAME, "summary", dedupe(items), tier)


def name_provenance() -> NameProvenance:
    """响应自带出处（spec §7）：语料版本 + 四张表，表列全部来自 `NAME_CONTENT_SOURCES`。"""
    meta = corpus_meta()
    return NameProvenance(
        corpus=CorpusProvenance(
            unicode_version=meta.unicode_version,
            corpus_date=meta.corpus_date,
            size=meta.size,
            source=meta.source,
        ),
        tables=[
            ProvenanceTable(name=module, version=CONTENT_VERSION, source=source)
            for module, source in NAME_CONTENT_SOURCES
        ],
    )


def _check_field(text: str, field: str) -> None:
    """空串与非汉字在这里变成 422 机器码；长度上限由请求模型的 pydantic 兜。"""
    if not text:
        raise NameInputError("not_han", f"{field}不能为空。", {"field": field, "chars": []})
    bad = [char for char in text if not _HAN.match(char)]
    if bad:
        raise NameInputError(
            "not_han",
            f"{field}只能使用汉字，收到：{''.join(bad)}。",
            {"field": field, "chars": bad},
        )


def _resolve_traditional(text: str, variants: dict[str, str], field: str) -> list[str]:
    """一简对多繁必须显式指定（决策六）；候选一次报全，让用户点一次就好。

    `variants` 里多余的键一律忽略：前端把已选过的正体对着整个姓名一路带着提交，
    "这次没用到"不是错误。反过来，用户点名的字若不在语料里则是可补救的输入错误，
    报 422 而不是让它悄悄变成 None——None 那一路是留给"用户没得选"的字的。
    """
    resolved: list[str] = []
    pending: list[dict[str, object]] = []
    for char in text:
        candidates = traditional_candidates(char)
        wanted = variants.get(char)
        if wanted is not None:
            if wanted not in candidates:
                raise NameInputError(
                    "variant_required",
                    f"{char} 的正体不在候选内（候选：{'、'.join(candidates)}）。",
                    {"field": field, "char": char, "given": wanted, "candidates": candidates},
                )
            if lookup(wanted) is None:
                raise NameInputError(
                    "stroke_unresolved",
                    f"{wanted} 不在本系统笔画语料内，无法核定康熙笔画。",
                    {"field": field, "char": char, "resolved": wanted},
                )
            resolved.append(wanted)
        elif len(candidates) == 1:
            resolved.append(candidates[0])
        else:
            pending.append({"char": char, "candidates": candidates})
            resolved.append(char)
    if pending:
        chars = "、".join(str(item["char"]) for item in pending)
        raise NameInputError(
            "ambiguous_traditional",
            f"{chars} 一简对多繁，请指定正体字后重试。",
            {"field": field, "choices": pending},
        )
    return resolved


def _strokes_of(resolved: Sequence[str]) -> tuple[list[int | None], list[str]]:
    """逐字取笔画；语料外的字如实记 warning，笔画留 None（决策八）。"""
    strokes: list[int | None] = []
    warnings: list[str] = []
    for char in resolved:
        entry = lookup(char)
        if entry is None:
            warnings.append(f"stroke_unresolved:{char}")
            strokes.append(None)
        else:
            strokes.append(entry.kangxi_strokes)
    return strokes, warnings


def _char_entry(char: str, resolved: str) -> NameChar:
    entry = lookup(resolved)
    if entry is None:
        return NameChar(char=char, resolved=resolved)
    return NameChar(
        char=char,
        resolved=resolved,
        simplified=list(entry.simplified),
        kangxi_strokes=entry.kangxi_strokes,
        radical_no=entry.radical_no,
        residual_strokes=entry.residual_strokes,
        radical_char=entry.radical_char,
        radical_strokes=entry.radical_strokes,
        readings=[
            NameReading(pinyin=r.pinyin, tone_number=r.tone_number, tone_name=r.tone_name)
            for r in entry.readings
        ],
        stroke_source=STROKE_SOURCE,
    )


def analyze_name(
    surname: str, given: str, variants: dict[str, str] | None = None
) -> NameAnalysis:
    """把两个字段推成一份可核对的五格剖象响应。"""
    _check_field(surname, "surname")
    _check_field(given, "given")
    choices = variants or {}

    surname_chars = _resolve_traditional(surname, choices, "surname")
    given_chars = _resolve_traditional(given, choices, "given")
    resolved = surname_chars + given_chars

    strokes, warnings = _strokes_of(resolved)
    terms = grids_of(strokes[: len(surname_chars)], strokes[len(surname_chars) :])
    grids = _as_mapping(terms)
    modality, modality_formula = modality_of(len(surname_chars), len(given_chars))

    built = [build_grid(term) for term in terms]
    score_value = name_score(grids)
    sancai = sancai_of(grids)
    # score 为 None（任一格笔画未核定）时 verdict 一并省略，同 score 的 None 纪律，不补占位卡。
    verdict = name_verdict(built, sancai, score_value) if score_value is not None else None

    return NameAnalysis(
        input=NameInput(
            surname=surname,
            given=given,
            resolved_traditional="".join(resolved),
            modality=modality,
            modality_formula=modality_formula,
        ),
        chars=[
            _char_entry(char, value)
            for char, value in zip(list(surname) + list(given), resolved, strict=True)
        ],
        grids=built,
        sancai=sancai,
        score=score_value,
        verdict=verdict,
        plain_summary=name_plain_summary(built, score_value),
        warnings=sorted(set(warnings)),
        provenance=name_provenance(),
    )
