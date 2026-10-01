"""Rune cast engine: cryptographically secure draws over the curated Elder Futhark.

This module is a pure function over :mod:`app.content.rune_futhark` and
:mod:`app.content.rune_spreads`. Stone selection and orientation use
:mod:`secrets` (an OS-backed CSPRNG), never the ``random`` module, satisfying
PRD 4.4. Interpretations are not generated: the synthesis is composed
deterministically from the real rune meanings, position texts and aett themes,
so every word returned traces back to the content library.

Two things this engine structurally cannot produce, which is stronger than
filtering them out afterwards:

* **A reversed symmetric rune.** ``_orientation_for`` only consults the RNG when
  ``allow_reversed and rune.reversible and not rune.is_wyrd``; otherwise it
  returns ``"upright"`` without drawing. The eight rotationally symmetric runes
  therefore never appear reversed in any response, so the reversed-side accessor
  that raises on them is unreachable from here.
* **A score or a percentage.** Nothing in this module computes one, and the
  response schema has no field for one. The only statistic shipped is
  ``aett_balance``, which is a count of what actually fell -- something the
  reader can verify by counting the stones on screen.

The engine never invents an adjective either. Where a rune has no reversed
reading, nothing is written for it; where the blank stone is drawn, the text
says it is a modern addition rather than dressing it as ancient.
"""

import secrets

from app.content import CONTENT_VERSION, RUNE_CONTENT_SOURCES
from app.content.rune_futhark import (
    AETT_FREYJA,
    AETT_HEIMDALL,
    AETT_NAMES,
    AETT_NAMES_ZH,
    AETT_NAMING_NOTE,
    AETT_THEMES_ZH,
    AETT_TYR,
    DECK_24,
    DECK_25,
    MANUSCRIPT_NOTE,
    REVERSIBLE_NOTE,
    WYRD,
    WYRD_NOTE,
    Rune,
    get_rune,
)
from app.content.rune_spreads import SPREADS, Spread, SpreadPosition, get_spread
from app.core.errors import UnsupportedMethodError
from app.engines.plain_compose import overview
from app.schemas.common import ProvenanceTable
from app.schemas.runes import (
    AettCount,
    AettGroup,
    CodexRune,
    DrawnRune,
    RuneCastResponse,
    RuneCodex,
    RuneProvenance,
    ShadowNote,
)

# A single OS-backed generator; secrets.SystemRandom is stateless across calls
# (it draws from os.urandom), so a module-level instance is safe to reuse.
_RNG = secrets.SystemRandom()

_ORIENTATIONS = ("upright", "reversed")

#: ætt 配比里那个「不入三组」桶的键。Wyrd `aett is None`，但抽到的枚数得有去处，
#: 否则「三组之和 + Wyrd == 抽到枚数」这条会计等式在开着空白符时就不成立。
UNASSIGNED_KEY = "wyrd"

#: 三组的固定次序：按 Kylver 序，也按 `AETT_NAMES` 的声明序。
AETT_ORDER: tuple[str, ...] = (AETT_FREYJA, AETT_HEIMDALL, AETT_TYR)

#: 抽牌口径，原文下发给读者核对（同数字命理把算式规则下发那一条纪律）。
METHOD = (
    "牌组：Elder Futhark 24 枚，按 Kylver 石碑序；开启空白符时为 25 枚。"
    "抽法：Python secrets（OS 熵源 CSPRNG）的 sample() 不放回抽取，故一次铸石内绝无重复符文。"
    "定向：仅当允许逆位、且该符文字形旋转 180° 后不与自身重合时，才再以同一种熵源独立定向；"
    "八枚对称符（Gebo、Hagalaz、Isa、Jera、Eihwaz、Sowilo、Ingwaz、Dagaz）与空白符恒为正位。"
    "释义：全部取自策展语料，引擎只做选取与串接，不生成语料之外的词句；"
    "无任何评分、无任何百分比 —— 本页不吃出生时间与地点，没有可以推出那类数字的输入。"
)


def draw(
    *,
    spread_id: str,
    include_wyrd: bool = False,
    allow_reversed: bool = True,
    question: str | None = None,
) -> RuneCastResponse:
    """Cast a rune spread.

    Raises :class:`UnsupportedMethodError` when ``spread_id`` is not a defined
    spread. Stones are drawn without replacement, so a spread never repeats a
    rune; each stone is then oriented upright or reversed (independently, by
    secure draw) only when that is geometrically meaningful for it.

    Keyword-only, matching ``compute_chart`` and ``draw_spread`` elsewhere: a
    call site that reads ``draw("five", True, False, q)`` tells the reader
    nothing about which flag is which.
    """
    spread = get_spread(spread_id)
    if spread is None:
        raise UnsupportedMethodError(f"Unknown rune spread: {spread_id!r}")

    deck = DECK_25 if include_wyrd else DECK_24
    if spread.size > len(deck):  # pragma: no cover - 5 < 24, unreachable today
        raise UnsupportedMethodError(
            f"Spread {spread_id!r} needs {spread.size} stones, deck holds {len(deck)}"
        )

    # Sample without replacement: sample() guarantees unique elements.
    drawn = _RNG.sample(deck, spread.size)

    stones: list[DrawnRune] = [
        _stone(index, rune, position, allow_reversed)
        for index, (rune, position) in enumerate(zip(drawn, spread.positions, strict=True))
    ]

    balance = _aett_balance(stones)

    return RuneCastResponse(
        spread_id=spread.id,
        spread_name=spread.name,
        spread_name_zh=spread.name_zh,
        spread_description=spread.description,
        question=question,
        stones=stones,
        drawn_keys=[stone.key for stone in stones],
        allow_reversed=allow_reversed,
        include_wyrd=include_wyrd,
        aett_balance=balance,
        synthesis=_synthesis(spread, stones, question, balance, allow_reversed),
        shadow_counsel=_shadow_counsel(stones),
        reversible_note=REVERSIBLE_NOTE,
        codex=_codex(),
        provenance=_provenance(len(deck)),
    )


def _stone(index: int, rune: Rune, position: SpreadPosition, allow_reversed: bool) -> DrawnRune:
    """One drawn rune in one position, with the drawn orientation's text resolved."""
    orientation = _orientation_for(rune, allow_reversed)
    return DrawnRune(
        position_index=index,
        position_key=position.key,
        position_label=position.label,
        position_label_zh=position.label_zh,
        position_meaning=position.meaning,
        order=rune.order,
        key=rune.key,
        glyph=rune.glyph,
        name=rune.name,
        name_zh=rune.name_zh,
        transliteration=rune.transliteration,
        name_meaning=rune.name_meaning,
        name_meaning_uncertain=rune.name_meaning_uncertain,
        aett=rune.aett,
        aett_zh=rune.aett_zh,
        reversible=rune.reversible,
        is_wyrd=rune.is_wyrd,
        orientation=orientation,
        keywords=list(rune.keywords_for(orientation)),
        meaning=rune.meaning_for(orientation),
        source=rune.source,
    )


def _orientation_for(rune: Rune, allow_reversed: bool) -> str:
    """Orient one stone, only consulting the RNG when a reversal is meaningful.

    The guard is the point: symmetric runes and the blank stone return
    ``"upright"`` without drawing, so "symmetric + reversed" cannot appear in a
    response at all. Generating it and filtering it later would leave the
    invalid combination reachable by any future caller that forgets the filter.
    """
    if allow_reversed and rune.reversible and not rune.is_wyrd:
        return _RNG.choice(_ORIENTATIONS)
    return "upright"


def _aett_balance(stones: list[DrawnRune]) -> list[AettCount]:
    """Count the drawn stones per group, plus one bucket for the unassigned blank.

    All four rows are always emitted. A zero count is a real value, and dropping
    the row would make "nothing fell in Tyr's aett this time" indistinguishable
    from "the engine forgot this group".
    """
    counts: dict[str, int] = {key: 0 for key in AETT_ORDER}
    counts[UNASSIGNED_KEY] = 0
    for stone in stones:
        # `aett` 为 None 只可能是 Wyrd；真符文一律有组，故这里不需要第三种分支。
        counts[stone.aett if stone.aett is not None else UNASSIGNED_KEY] += 1

    rows = [
        AettCount(
            key=key,
            name=AETT_NAMES[key],
            name_zh=AETT_NAMES_ZH[key],
            count=counts[key],
        )
        for key in AETT_ORDER
    ]
    rows.append(
        AettCount(
            key=UNASSIGNED_KEY,
            name="Unassigned (blank stone)",
            name_zh="不入三组（空白符）",
            count=counts[UNASSIGNED_KEY],
        )
    )
    return rows


def _shadow_counsel(stones: list[DrawnRune]) -> list[ShadowNote] | None:
    """The reversed side of every reversible rune drawn, as a labelled contrast.

    Returns ``None`` -- not an empty list -- when no reversible rune was drawn,
    so the frontend can drop the whole block instead of rendering an empty
    heading (决策 23: 算不出就 None，不许出现看着像值的占位).
    """
    notes: list[ShadowNote] = []
    for stone in stones:
        rune = get_rune(stone.key)
        if not rune.reversible or rune.reversed_meaning is None or rune.reversed_keywords is None:
            continue
        if stone.orientation == "reversed":
            note = (
                "本次已抽到逆位，此条与卡面所读同文，列出只为与其余各条并读，"
                "不是另一次结果。"
            )
        else:
            note = "本次为正位；此条是它的反面参照（逆位释义），不是本次结果。"
        notes.append(
            ShadowNote(
                key=stone.key,
                name=stone.name,
                name_zh=stone.name_zh,
                glyph=stone.glyph,
                position_key=stone.position_key,
                position_label_zh=stone.position_label_zh,
                drawn_orientation=stone.orientation,
                shadow_keywords=list(rune.reversed_keywords),
                shadow_meaning=rune.reversed_meaning,
                note=note,
            )
        )
    return notes or None


#: 直读的三件框架句（多系统白话 spec §7 表行 2）。句子本身不是语料：它只把
#: 位次名、牌名、正逆与**语料的释义**串起来，所以本期零新语料、`RUNE_CONTENT_SOURCES`
#: 不加条目（G16 / spec §9）。三条病症的修法写在 T6 的表里，逐字复测：
#: `cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "from app.engines.runes import draw; print(draw(spread_id='three').synthesis)"`
RUNES_SYNTHESIS_FRAME = "{opening}{stones}{balance}"
RUNES_OPENING_ASKED = "以{name_zh}（{name}）铸石，所问：{question}。"
RUNES_OPENING_UNASKED = "以{name_zh}（{name}）铸石，未附所问。"
#: 逐枚句。中文牌名在前、英文在括注，连接符用 `——` 而不是第二层冒号；
#: 位次只剩中文（英文位次名仍在 `stones[].position_label` 里下发，同一句不重说）。
RUNES_STONE_LINE = "{position}落得{name_zh}（{name}，{orientation}）——{meaning}"
#: 空白符那句用「。」而不是第二个「：」收束：语料自己的释义就以冒号开头
#: （「石面上什么也没刻：……」，`rune_futhark.py` 的 WYRD），框架句再垫一个冒号就是
#: 同一句里的两层冒号 —— 正是本模块要清除的那个病症。「现代增补，非古传统」这半句留在
#: 原处，因为它复述的就是空白符自己的 `source` 凭据（它不据 Kylver、不据 Unicode）。
RUNES_WYRD_LINE = "{position}落得空白符（Wyrd）——现代增补，非古传统。{meaning}"


def _synthesis(
    spread: Spread,
    stones: list[DrawnRune],
    question: str | None,
    balance: list[AettCount],
    allow_reversed: bool,
) -> str:
    """Compose the reading from real corpus text only.

    Every clause here is either a position label, a rune name, an orientation
    word, a corpus meaning, or a count of what actually fell. No adjective is
    introduced that the corpus does not already carry, and no rune is named that
    was not drawn -- both are asserted by the engine tests.

    The three frame sentences are named constants so the wording can be audited
    in one place; the 25 meanings themselves are untouched (G2).
    """
    if question and question.strip():
        opening = RUNES_OPENING_ASKED.format(
            name_zh=spread.name_zh, name=spread.name, question=question.strip()
        )
    else:
        opening = RUNES_OPENING_UNASKED.format(name_zh=spread.name_zh, name=spread.name)

    lines: list[str] = []
    for stone in stones:
        orientation_zh = "逆位" if stone.orientation == "reversed" else "正位"
        if stone.is_wyrd:
            lines.append(
                RUNES_WYRD_LINE.format(position=stone.position_label_zh, meaning=stone.meaning)
            )
        else:
            lines.append(
                RUNES_STONE_LINE.format(
                    position=stone.position_label_zh,
                    name_zh=stone.name_zh,
                    name=stone.name,
                    orientation=orientation_zh,
                    meaning=stone.meaning,
                )
            )

    return overview(
        RUNES_SYNTHESIS_FRAME,
        {"opening": opening, "stones": "".join(lines), "balance": _balance_sentence(stones, balance, allow_reversed)},
    )


def _balance_sentence(
    stones: list[DrawnRune],
    balance: list[AettCount],
    allow_reversed: bool,
) -> str:
    """State the group counts, attributing each theme as a modern reading."""
    total = len(stones)
    clauses = [f"{row.name_zh} {row.count} 枚" for row in balance if row.key != UNASSIGNED_KEY]
    sentence = f"三组配比（本次共 {total} 枚）：" + "、".join(clauses) + "。"

    unassigned = next(row for row in balance if row.key == UNASSIGNED_KEY)
    if unassigned.count:
        sentence += f"另有空白符 {unassigned.count} 枚，不入三组。"

    # 只报「哪一组最多」这一件可数的事实，并用语料里的主题词说明那一组讲什么，
    # 同时点明主题是现代解读 —— 不据此断吉凶，那是语料里没有的话。
    top = max((row for row in balance if row.key != UNASSIGNED_KEY), key=lambda r: r.count)
    if top.count > 0 and top.count * 2 >= total:
        theme = AETT_THEMES_ZH[top.key]
        sentence += (
            f"其中 {top.name_zh} 占 {top.count} 枚，现代解读作「{theme}」"
            f"——这是分组主题的通行说法，非古文献，也不据此断吉凶。"
        )

    if allow_reversed:
        reversed_count = sum(1 for s in stones if s.orientation == "reversed")
        reversible_count = sum(1 for s in stones if s.reversible)
        if reversible_count == 0:
            sentence += "本次抽到的符文全部字形对称，故无正逆之分。"
        elif reversed_count == 0:
            sentence += f"本次 {reversible_count} 枚可逆符文全为正位。"
        else:
            sentence += f"本次 {reversible_count} 枚可逆符文中有 {reversed_count} 枚为逆位。"
    else:
        sentence += "本次未启用逆位，全部按正位读。"

    return sentence


def _codex() -> RuneCodex:
    """The full 24+1 reference table, grouped.

    Always 25 entries regardless of ``include_wyrd``: that toggle governs
    whether the blank stone can be drawn, not whether it exists in the codex.
    """
    groups = [
        AettGroup(
            key=key,
            name=AETT_NAMES[key],
            name_zh=AETT_NAMES_ZH[key],
            theme=AETT_THEMES_ZH[key],
            naming_note=AETT_NAMING_NOTE,
            runes=[_codex_rune(rune) for rune in DECK_24 if rune.aett == key],
        )
        for key in AETT_ORDER
    ]
    return RuneCodex(aettir=groups, wyrd=_codex_rune(WYRD), total=len(DECK_25))


def _codex_rune(rune: Rune) -> CodexRune:
    return CodexRune(
        order=rune.order,
        key=rune.key,
        glyph=rune.glyph,
        codepoint=rune.codepoint,
        unicode_name=rune.unicode_name,
        name=rune.name,
        name_zh=rune.name_zh,
        transliteration=rune.transliteration,
        phoneme=rune.phoneme,
        name_meaning=rune.name_meaning,
        name_meaning_uncertain=rune.name_meaning_uncertain,
        aett=rune.aett,
        aett_zh=rune.aett_zh,
        reversible=rune.reversible,
        is_wyrd=rune.is_wyrd,
        upright_keywords=list(rune.upright_keywords),
        reversed_keywords=None if rune.reversed_keywords is None else list(rune.reversed_keywords),
        upright_meaning=rune.upright_meaning,
        reversed_meaning=rune.reversed_meaning,
        source=rune.source,
    )


def _provenance(deck_size: int) -> RuneProvenance:
    """Response-carried provenance: entropy source, method, and the two tables."""
    return RuneProvenance(
        deck_size=deck_size,
        tables=[
            ProvenanceTable(name=module, version=CONTENT_VERSION, source=source)
            for module, source in RUNE_CONTENT_SOURCES
        ],
        method=METHOD,
        naming_note=AETT_NAMING_NOTE,
        wyrd_note=WYRD_NOTE,
        manuscript_note=MANUSCRIPT_NOTE,
    )


#: 前端与契约测都需要知道有哪几种牌阵；从语料取，不另抄一份。
SUPPORTED_SPREAD_IDS: tuple[str, ...] = tuple(SPREADS)
