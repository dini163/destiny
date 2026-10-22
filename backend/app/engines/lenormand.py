"""雷诺曼 (Lenormand) draw engine — cryptographically secure draws over the 36-card deck.

A pure function over :mod:`app.content.lenormand`. Card selection uses
:mod:`secrets` (an OS-backed CSPRNG), never ``random``, satisfying PRD 4.4.
Lenormand differs from tarot in two ways this engine honours:

* **No reversals** — every card is read upright.
* **Combination reading (组合直读)** — meaning lives in *pairs*: in ``A → B`` the first
  card is the subject (名词) and the second the modifier (形容词), so the phrase is
  ``B.as_modifier + A.essence``. The engine derives these pairs from the layout
  (consecutive for a line, centre×ring for the box, significator×neighbours for the
  大桌) and composes the synthesis from real card content — nothing is invented.
"""

import secrets

from app.content import CONTENT_VERSION, LENORMAND_CONTENT_SOURCES
from app.content.lenormand import (
    CARDS,
    LENORMAND_SOURCE,
    POLARITY_LABEL,
    SIGNIFICATOR_BY_GENDER,
    LenormandCard,
    LenormandSpread,
    get_spread,
)
from app.content.lenormand_plain import (
    LENORMAND_VERDICT_ADVICE,
    LENORMAND_VERDICT_ADVICE_FRAME,
    LENORMAND_VERDICT_FRAME,
    LENORMAND_VERDICT_OUTLOOK,
)
from app.core.errors import UnsupportedMethodError
from app.core.provenance import MODEL_PARAM_SOURCE
from app.engines.plain_compose import compose, overview
from app.engines.plain_corpora import LENORMAND
from app.engines.verdict import grade_for
from app.schemas.common import ProvenanceTable, Verdict
from app.schemas.lenormand import (
    CardRef,
    Combination,
    DrawnCard,
    LenormandProvenance,
    LenormandReading,
    SignificatorInfo,
)

_RNG = secrets.SystemRandom()

# --- 综合结论 verdict（2026-10-22 verdict-card spec §2b：无账本系统的新增判定层） ---
#: 极性计数权重（模型参数，MODEL_PARAM_SOURCE）：每张积极牌 +k、每张消极牌 −k，中性牌（0 极性
#: 指示牌）不计入抵消。传统牌义只给定性极性（`content/lenormand.py` 的 polarity），不给数字，
#: 故 k 自署模型参数，不是古籍赋分。复测：
#: `cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "from app.engines.lenormand import POLARITY_WEIGHT; print(POLARITY_WEIGHT)"` → `8.0`。
POLARITY_WEIGHT: float = 8.0

#: 中性起点（模型参数，MODEL_PARAM_SOURCE）：50 为五档「平」带中位，加分上抬、减分下压。
VERDICT_BASE: float = 50.0

#: 上面权重与起点的共同署名：模型参数（非古籍赋分），传统牌义只给极性不给分数。
VERDICT_WEIGHT_SOURCE = MODEL_PARAM_SOURCE

NOTE = (
    "抽牌以 Python secrets（操作系统级 CSPRNG）洗牌、无重复地发满所选牌阵；雷诺曼牌一律正位，不作逆位翻转。"
    "牌义、关键词与组合直读的名词核心/修饰词皆取自策展 36 张牌库，组合读法为「后牌修饰前牌」"
    "（第二张为第一张添上形容），全程确定性拼接，未在运行时虚构任何牌义。"
    "大桌全景以指示牌为中心，读其同行之前后与同列之上下。"
)


def build_verdict(positive: int, negative: int, neutral: int) -> Verdict:
    """从极性计数确定性合成综合结论卡片（verdict-card spec §2b）。

    不重新判牌、不现编中文：档位/星级由 `grade_for(50 + k×(积极−消极))` 派生，
    headline/advice 套 `lenormand_plain` 的框架句，points 是三类牌的张数。中性牌不计入
    抵消（0 极性指示牌两边都不靠）。
    """
    net = positive - negative
    score = max(0.0, min(100.0, VERDICT_BASE + POLARITY_WEIGHT * net))
    grade, stars = grade_for(score)
    headline = overview(LENORMAND_VERDICT_FRAME, {
        "grade": grade,
        "positive": str(positive),
        "negative": str(negative),
        "neutral": str(neutral),
        "outlook": LENORMAND_VERDICT_OUTLOOK[grade],
    })
    advice_key = "favorable" if net >= 0 else "adverse"
    advice = overview(LENORMAND_VERDICT_ADVICE_FRAME, {"advice": LENORMAND_VERDICT_ADVICE[advice_key]})
    return Verdict(
        grade=grade,
        stars=stars,
        headline=headline,
        points=[
            f"积极牌 {positive} 张",
            f"消极牌 {negative} 张",
            f"中性牌 {neutral} 张",
        ],
        advice=advice,
    )


def draw_lenormand(
    *,
    spread_id: str,
    question: str | None = None,
    significator: str | None = None,
) -> LenormandReading:
    """Draw and read a Lenormand spread.

    Raises :class:`UnsupportedMethodError` when ``spread_id`` is not defined.
    Cards are drawn without replacement, so a spread never repeats a card.
    """
    spread = get_spread(spread_id)
    if spread is None:
        raise UnsupportedMethodError(f"Unknown Lenormand spread: {spread_id!r}")

    drawn = _RNG.sample(CARDS, spread.size)

    sig_number = SIGNIFICATOR_BY_GENDER.get(significator or "")
    cards = [
        DrawnCard(
            position_index=index,
            position_key=position.key,
            position_label_zh=position.label_zh,
            position_meaning=position.meaning,
            row=position.row,
            col=position.col,
            card_id=card.id,
            number=card.number,
            name=card.name,
            name_zh=card.name_zh,
            polarity=card.polarity,
            polarity_label=POLARITY_LABEL[card.polarity],
            keywords=list(card.keywords),
            essence=card.essence,
            meaning=card.meaning,
            as_modifier=card.as_modifier,
            is_significator=sig_number is not None and card.number == sig_number,
        )
        for index, (card, position) in enumerate(zip(drawn, spread.positions))
    ]

    combinations = _combinations(spread, cards)
    sig_info = _significator_info(cards, sig_number) if sig_number else None

    positive = sum(1 for c in cards if c.polarity > 0)
    negative = sum(1 for c in cards if c.polarity < 0)
    neutral = len(cards) - positive - negative

    synthesis = _synthesize(spread, cards, combinations, sig_info, question, positive, negative)

    return LenormandReading(
        spread_id=spread.id,
        spread_name_zh=spread.name_zh,
        spread_name_en=spread.name_en,
        layout=spread.layout,
        description=spread.description,
        question=question,
        cards=cards,
        drawn_ids=[c.card_id for c in cards],
        combinations=combinations,
        significator=sig_info,
        synthesis=synthesis,
        positive_count=positive,
        neutral_count=neutral,
        negative_count=negative,
        verdict=build_verdict(positive, negative, neutral),
        # 白话段：阵的开篇句 + 按位序逐张牌义。本表不分带（G21 / 偏差表第 1 行）：
        # 28 男人、29 女人的极性是 0，`band` 分支遇 0 值符号直接 `ValueError`，
        # 而牌阵的读序本来就是位序。此处不可能同键（偏差表第 8 行：`_RNG.sample`
        # 无放回发牌，一张牌在一个阵里只落一个位次），所以不调 `dedupe()`。
        plain_summary=compose(
            LENORMAND,
            spread.id,
            [(card.card_id, 0) for card in cards],
        ),
        provenance=LenormandProvenance(
            engine="lenormand-combination",
            content_version=CONTENT_VERSION,
            source=LENORMAND_SOURCE,
            note=NOTE,
            tables=_tables(),
        ),
    )


def _tables() -> list[ProvenanceTable]:
    """`LENORMAND_CONTENT_SOURCES` 的第一次被消费（G19）。

    复测（改前 = BASE `f1f42e0`，2026-10-01 实跑）：`git grep -n LENORMAND_CONTENT_SOURCES
    f1f42e0 -- backend` → 只有 `app/content/__init__.py:158` 的定义处一条，登记了却无人读。
    `source=LENORMAND_SOURCE` 那行本来就是引常量而不是手抄串，本任务不动它；表名也只这一处
    来源，引擎不再抄一份书名（同 `engines/qimen.py:232-243` 的写法）。
    """
    return [
        ProvenanceTable(name=module, version=CONTENT_VERSION, source=source)
        for module, source in LENORMAND_CONTENT_SOURCES
    ]


def _ref(card: DrawnCard) -> CardRef:
    return CardRef(number=card.number, name_zh=card.name_zh, essence=card.essence)


def _combine(subject: DrawnCard, modifier: DrawnCard) -> str:
    """组合直读：后牌（modifier）修饰前牌（subject）→ ``modifier.as_modifier + subject.essence``。"""
    return f"{modifier.as_modifier}{subject.essence}"


def _combinations(spread: LenormandSpread, cards: list[DrawnCard]) -> list[Combination]:
    """Derive the 组合直读 pairs appropriate to this layout."""
    if spread.layout == "line":
        return _line_combinations(cards)
    if spread.layout == "box":
        return _box_combinations(cards)
    return _tableau_combinations(cards)


def _line_combinations(cards: list[DrawnCard]) -> list[Combination]:
    """Consecutive pairs, read left → right (earlier card is the subject)."""
    out: list[Combination] = []
    for left, right in zip(cards, cards[1:]):
        out.append(
            Combination(
                left=_ref(left), right=_ref(right),
                phrase=_combine(left, right),
                context=f"{left.position_label_zh} → {right.position_label_zh}",
            )
        )
    return out


def _box_combinations(cards: list[DrawnCard]) -> list[Combination]:
    """The 3×3 centre card combined with each of its eight surrounding cards."""
    centre = next((c for c in cards if c.position_key == "heart"), None)
    if centre is None:
        return _line_combinations(cards)
    out: list[Combination] = []
    for other in cards:
        if other is centre:
            continue
        out.append(
            Combination(
                left=_ref(centre), right=_ref(other),
                phrase=_combine(centre, other),
                context=f"核心 × {other.position_label_zh}",
            )
        )
    return out


def _tableau_combinations(cards: list[DrawnCard]) -> list[Combination]:
    """大桌：指示牌与同行前后、同列上下相邻牌的组合；无指示牌则退回首行线读。"""
    sig = next((c for c in cards if c.is_significator), None)
    if sig is None:
        first_row = sorted((c for c in cards if c.row == 0), key=lambda c: c.col)
        return _line_combinations(first_row)

    by_cell = {(c.row, c.col): c for c in cards}
    out: list[Combination] = []
    behind = by_cell.get((sig.row, sig.col - 1))
    ahead = by_cell.get((sig.row, sig.col + 1))
    above = by_cell.get((sig.row - 1, sig.col))
    below = by_cell.get((sig.row + 1, sig.col))
    # Reading left → right: the card behind is the subject, the significator modifies it.
    if behind is not None:
        out.append(Combination(left=_ref(behind), right=_ref(sig),
                               phrase=_combine(behind, sig), context="指示牌之前 · 近过去"))
    if ahead is not None:
        out.append(Combination(left=_ref(sig), right=_ref(ahead),
                               phrase=_combine(sig, ahead), context="指示牌之后 · 近未来"))
    if above is not None:
        out.append(Combination(left=_ref(sig), right=_ref(above),
                               phrase=_combine(sig, above), context="指示牌之上 · 显意识"))
    if below is not None:
        out.append(Combination(left=_ref(sig), right=_ref(below),
                               phrase=_combine(sig, below), context="指示牌之下 · 潜意识"))
    return out


def _significator_info(cards: list[DrawnCard], sig_number: int) -> SignificatorInfo | None:
    """Locate the 指示牌 and gather everything along its row and column."""
    sig = next((c for c in cards if c.number == sig_number), None)
    if sig is None:
        return None
    same_row = [c for c in cards if c.row == sig.row and c is not sig]
    same_col = [c for c in cards if c.col == sig.col and c is not sig]
    return SignificatorInfo(
        number=sig.number,
        name_zh=sig.name_zh,
        position_index=sig.position_index,
        row=sig.row,
        col=sig.col,
        behind=[_ref(c) for c in sorted((c for c in same_row if c.col < sig.col), key=lambda c: -c.col)],
        ahead=[_ref(c) for c in sorted((c for c in same_row if c.col > sig.col), key=lambda c: c.col)],
        above=[_ref(c) for c in sorted((c for c in same_col if c.row < sig.row), key=lambda c: -c.row)],
        below=[_ref(c) for c in sorted((c for c in same_col if c.row > sig.row), key=lambda c: c.row)],
    )


def _synthesize(
    spread: LenormandSpread,
    cards: list[DrawnCard],
    combinations: list[Combination],
    sig_info: SignificatorInfo | None,
    question: str | None,
    positive: int,
    negative: int,
) -> str:
    """Compose a reading from real card meanings and combinations (no fabrication)."""
    sentences: list[str] = []
    opener = f"以「{spread.name_zh}（{spread.name_en}）」起盘"
    if question:
        opener += f"，所问：{question.strip()}"
    sentences.append(opener + "。")

    if spread.layout == "line":
        chain = "，".join(f"【{c.number:02d} {c.name_zh}】({c.meaning.rstrip('。')})" for c in cards)
        sentences.append(f"依次读来：{chain}。")
    elif sig_info is not None:
        ahead_names = "、".join(f"{c.name_zh}" for c in sig_info.ahead) or "（无）"
        behind_names = "、".join(f"{c.name_zh}" for c in sig_info.behind) or "（无）"
        sentences.append(
            f"指示牌【{sig_info.number:02d} {sig_info.name_zh}】落于第 {sig_info.row + 1} 行第 {sig_info.col + 1} 列："
            f"身后（过去）为 {behind_names}，眼前（未来）为 {ahead_names}。"
        )
    else:
        lead = cards[0]
        sentences.append(f"起手【{lead.number:02d} {lead.name_zh}】({lead.meaning.rstrip('。')})，为核心之象。")

    if combinations:
        picks = combinations[:4]
        combo_text = "；".join(f"{c.left.name_zh}×{c.right.name_zh} → {c.phrase}" for c in picks)
        sentences.append(f"组合直读：{combo_text}。")

    total = len(cards)
    if negative == 0:
        sentences.append(f"{total} 张牌无一张消极，整体气象顺遂，阻力多来自外部时机而非本质。")
    elif positive >= negative * 2:
        sentences.append(f"积极牌 {positive} 张远多于消极 {negative} 张，大势向好，个别阻碍不足为虑。")
    elif negative > positive:
        sentences.append(f"消极牌 {negative} 张多于积极 {positive} 张，宜守不宜攻，先解阻滞再图推进。")
    else:
        sentences.append(f"积极 {positive} 张、消极 {negative} 张旗鼓相当，成败系于当事人取舍。")

    return " ".join(sentences)
