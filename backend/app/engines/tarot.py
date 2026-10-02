"""Tarot draw engine: cryptographically secure draws over the curated 78-card deck.

This module is a pure function over :mod:`app.content.tarot_deck`. Card
selection and orientation use :mod:`secrets` (an OS-backed CSPRNG), never the
``random`` module, satisfying PRD 4.4. Interpretations are not generated: the
synthesis is composed deterministically from the real card meanings and spread
position texts, so every word returned traces back to the content library.
"""

import secrets

from app.content import CONTENT_VERSION, TAROT_CONTENT_SOURCES
from app.content.tarot_deck import DECK, Spread, TAROT_SOURCE, get_spread
from app.core.errors import UnsupportedMethodError
from app.schemas.common import ProvenanceTable
from app.schemas.tarot import DrawnCard, TarotProvenance, TarotSpreadResponse

# A single OS-backed generator; secrets.SystemRandom is stateless across calls
# (it draws from os.urandom), so a module-level instance is safe to reuse.
_RNG = secrets.SystemRandom()

_ORIENTATIONS = ("upright", "reversed")

#: 取向的中文说法只在框架句里出现；表里的 `orientation` 值仍是英文（`upright` | `reversed`）。
_ORIENTATION_ZH = {"upright": "正位", "reversed": "逆位"}

#: 受控引擎文案（不是语料，也不是页面免责声明）：说清随机源、文案来源与中英配对这三件事。
#: 第二句刻意把「综合解读」拆成两半说：牌面词取自表，串词的八句框架住在本模块（G16），
#: 说成「一律取自牌库」就是让引擎字面冒充语料（AGENTS.md §7 的诚实性同一条）。
NOTE = (
    "洗牌与正逆位由 Python secrets（操作系统级 CSPRNG）决定，抽牌无放回，每次抽取独立且不可复现。"
    "牌名、关键词、牌义与宫位释义取自策展 78 张牌库与六种布阵表，综合解读用本模块的固定句式"
    "串起这些真实字段，未在运行时虚构任何句子；"
    "中文正文与英文原句同行成对呈现，英文侧的字段与取值在本次中文化里一字未改。"
)


def draw_spread(
    *,
    spread_id: str,
    allow_reversed: bool = True,
    question: str | None = None,
) -> TarotSpreadResponse:
    """Draw and interpret a tarot spread.

    Raises :class:`UnsupportedMethodError` when ``spread_id`` is not a defined
    spread. Cards are drawn without replacement, so a spread never repeats a
    card; each card is then oriented upright or reversed (independently, by
    secure draw) when ``allow_reversed`` is set.
    """
    spread = get_spread(spread_id)
    if spread is None:
        raise UnsupportedMethodError(f"Unknown tarot spread: {spread_id!r}")

    # Sample without replacement: sample() guarantees unique elements.
    drawn_cards = _RNG.sample(DECK, spread.size)

    cards: list[DrawnCard] = []
    for index, (card, position) in enumerate(zip(drawn_cards, spread.positions)):
        orientation = _RNG.choice(_ORIENTATIONS) if allow_reversed else "upright"
        cards.append(
            DrawnCard(
                position_index=index,
                position_key=position.key,
                position_label=position.label,
                position_label_zh=position.label_zh,
                position_meaning=position.meaning,
                position_meaning_zh=position.meaning_zh,
                card_id=card.id,
                name=card.name,
                name_zh=card.name_zh,
                arcana=card.arcana,
                number=card.number,
                suit=card.suit,
                rank=card.rank,
                element=card.element,
                orientation=orientation,
                keywords=list(card.keywords(orientation)),
                keywords_zh=list(card.keywords_zh(orientation)),
                meaning=card.meaning(orientation),
                meaning_zh=card.meaning_zh(orientation),
            )
        )

    major_count = sum(1 for c in cards if c.arcana == "major")
    reversed_count = sum(1 for c in cards if c.orientation == "reversed")
    synthesis = _synthesize(spread, cards, question, major_count, reversed_count, allow_reversed)

    return TarotSpreadResponse(
        spread_id=spread.id,
        spread_name=spread.name,
        spread_name_zh=spread.name_zh,
        spread_description=spread.description,
        spread_description_zh=spread.description_zh,
        question=question,
        cards=cards,
        drawn_ids=[c.card_id for c in cards],
        allow_reversed=allow_reversed,
        synthesis=synthesis,
        major_arcana_count=major_count,
        reversed_count=reversed_count,
        provenance=TarotProvenance(
            engine="tarot-content-library",
            content_version=CONTENT_VERSION,
            source=TAROT_SOURCE,
            note=NOTE,
            tables=_tables(),
        ),
    )


def _lead_keywords_zh(card: DrawnCard, limit: int = 3) -> str:
    """Join a card's leading Chinese keywords for the drawn orientation."""
    return "、".join(card.keywords_zh[:limit]) if card.keywords_zh else card.name_zh


def _synthesize(
    spread: Spread,
    cards: list[DrawnCard],
    question: str | None,
    major_count: int,
    reversed_count: int,
    allow_reversed: bool,
) -> str:
    """Compose a reading from real card and position content (no fabrication)."""
    sentences: list[str] = []

    if question:
        sentences.append(
            f"本次以 {spread.name_zh}（{spread.name}）为这个问题布阵：{question.strip()}"
        )
    else:
        sentences.append(f"本次以 {spread.name_zh}（{spread.name}）布阵。")

    for card in cards:
        sentences.append(
            f"{card.position_label_zh}（{card.position_label}）抽出 {card.name_zh}（{card.name}），"
            f"{_ORIENTATION_ZH[card.orientation]}，取的是 {_lead_keywords_zh(card)}。"
        )

    total = len(cards)
    if major_count == 0:
        sentences.append(
            "一张大牌也没有出现，所以这次讲的是日常的、你能直接上手的现实力量，"
            "而不是更大的人生主题。"
        )
    elif major_count * 2 >= total:
        sentences.append(
            f"{total} 张牌里有 {major_count} 张大牌，"
            "那些超出你当下掌控的人生主题与力量正明显起作用。"
        )
    else:
        sentences.append(f"{major_count} 张大牌在这份日常处境里标出分量更重、由不得你选的线索。")

    if allow_reversed:
        if reversed_count == 0:
            sentences.append("所有牌都落正位，这些能量表达得清楚，没有被挡。")
        else:
            sentences.append(
                f"{reversed_count} 张逆位，指向被阻滞、被内收或被延迟的能量，"
                "它们要的是被看清，不是被硬推。"
            )

    return " ".join(sentences)


def _tables() -> list[ProvenanceTable]:
    """`TAROT_CONTENT_SOURCES` 的第一次被消费（G13：登记了却无人读就是虚账）。

    表名与出处只那一处清单供给，引擎不抄书名（写法同 `engines/lenormand.py`、
    `engines/qimen.py` 各自的 `_tables()`）。

    复测（消费处就这一行，别处都是定义、import、测与注释提及）：`cd backend && grep -rn "for module, source in TAROT_CONTENT_SOURCES" app/engines/tarot.py` → 一条命中，即本函数体内那行。
    改前（`git grep -c TAROT_CONTENT_SOURCES de2be71 -- backend` → 无输出、exit 1）这个名字
    根本不存在：定义与消费同笔落地，不留「登记了无人读」的死账窗口。
    """
    return [
        ProvenanceTable(name=module, version=CONTENT_VERSION, source=source)
        for module, source in TAROT_CONTENT_SOURCES
    ]
