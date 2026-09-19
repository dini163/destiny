"""Full 78-card deck assembly, card lookup and the spread (牌阵) library.

The deck is the concatenation of the curated :data:`~app.content.tarot_major.MAJOR_ARCANA`
(22) and :data:`~app.content.tarot_minor.MINOR_ARCANA` (56) tables; nothing is
generated at runtime. Spreads define the ordered positions a draw fills, each
with a stable key plus bilingual label and interpretation, following the classic
Rider-Waite layouts named in PRD 6.7.
"""

from dataclasses import dataclass

from app.content.tarot_cards import TarotCard
from app.content.tarot_major import MAJOR_ARCANA
from app.content.tarot_minor import MINOR_ARCANA

# --- Deck -------------------------------------------------------------------

DECK: tuple[TarotCard, ...] = MAJOR_ARCANA + MINOR_ARCANA

# Expected deck composition, asserted by the golden tests as a content invariant.
DECK_SIZE = 78
MAJOR_SIZE = 22
MINOR_SIZE = 56

_CARDS_BY_ID: dict[str, TarotCard] = {card.id: card for card in DECK}


def get_card(card_id: str) -> TarotCard:
    """Return the card with ``card_id`` or raise ``KeyError`` if unknown."""
    return _CARDS_BY_ID[card_id]


# --- Spreads ----------------------------------------------------------------


@dataclass(frozen=True)
class SpreadPosition:
    """One slot of a spread, filled by exactly one drawn card."""

    key: str          # stable machine identifier, e.g. "past"
    label: str        # English label, e.g. "Recent Past"
    label_zh: str     # Chinese label, e.g. "近期过去"
    meaning: str      # what this position reveals


@dataclass(frozen=True)
class Spread:
    """A named card layout with an ordered list of positions."""

    id: str
    name: str
    name_zh: str
    description: str
    positions: tuple[SpreadPosition, ...]

    @property
    def size(self) -> int:
        """Number of cards this spread draws."""
        return len(self.positions)


def _spread(
    id: str,
    name: str,
    name_zh: str,
    description: str,
    positions: tuple[tuple[str, str, str, str], ...],
) -> Spread:
    """Build a :class:`Spread` from raw ``(key, label, label_zh, meaning)`` tuples."""
    return Spread(
        id=id,
        name=name,
        name_zh=name_zh,
        description=description,
        positions=tuple(SpreadPosition(*p) for p in positions),
    )


_SINGLE = _spread(
    "single", "Single Card", "单张牌",
    "One card for a daily reflection or a quick, focused answer.",
    (
        ("guidance", "Guidance", "指引", "The central theme or advice for the question or day."),
    ),
)

_THREE_CARD = _spread(
    "three_card", "Three Card", "时间之流三张",
    "The flow of a situation across time: past, present and future.",
    (
        ("past", "Past", "过去", "Roots and events already shaping the situation."),
        ("present", "Present", "现在", "The current dynamics and where you stand now."),
        ("future", "Future", "未来", "The likely direction if things continue as they are."),
    ),
)

_CELTIC_CROSS = _spread(
    "celtic_cross", "Celtic Cross", "凯尔特十字",
    "The classic ten-card spread for a deep, layered reading of a situation.",
    (
        ("present", "Present", "现状", "The heart of the matter, the situation as it stands."),
        ("challenge", "Challenge", "挑战", "The immediate obstacle or opposing force, laid across the present."),
        ("foundation", "Foundation", "根基", "The subconscious basis or root cause beneath the situation."),
        ("recent_past", "Recent Past", "近期过去", "Recent events now receding but still influential."),
        ("crown", "Crown", "显意识", "The conscious aim or best possible outcome overhead."),
        ("near_future", "Near Future", "近期未来", "What is approaching in the immediate future."),
        ("self", "Self", "自我态度", "Your own attitude and approach to the situation."),
        ("environment", "Environment", "环境影响", "External influences and the people around you."),
        ("hopes_fears", "Hopes & Fears", "希望与恐惧", "What you hope for and what you fear, often the same."),
        ("outcome", "Outcome", "最终结果", "The likely outcome given the current trajectory."),
    ),
)

_RELATIONSHIP = _spread(
    "relationship", "Relationship", "关系牌阵",
    "A five-card spread reading both partners and the bond between them.",
    (
        ("you", "You", "你", "Your feelings, needs and stance in the relationship."),
        ("partner", "Partner", "对方", "The other person's feelings, needs and stance."),
        ("connection", "Connection", "关系本质", "The nature of the bond that currently links you."),
        ("challenge", "Challenge", "挑战", "The main difficulty or friction to work through."),
        ("potential", "Potential", "发展方向", "Where the relationship is heading if nurtured."),
    ),
)

_CAREER = _spread(
    "career", "Career", "事业牌阵",
    "A five-card spread for work, projects and professional direction.",
    (
        ("current", "Current Position", "当前处境", "Where you stand in your work right now."),
        ("strength", "Strength", "优势", "The assets and skills working in your favour."),
        ("obstacle", "Obstacle", "阻碍", "The challenge or limitation blocking progress."),
        ("action", "Action", "行动建议", "The practical step to take next."),
        ("outcome", "Outcome", "事业走向", "The likely professional result of the current path."),
    ),
)

_DECISION = _spread(
    "decision", "Decision", "是非抉择牌阵",
    "A five-card spread comparing two options to inform a choice.",
    (
        ("situation", "Situation", "当前局面", "The decision you face and its context."),
        ("option_a", "Option A", "选择甲", "The nature and energy of the first path."),
        ("option_b", "Option B", "选择乙", "The nature and energy of the second path."),
        ("guidance", "Guidance", "指引", "Advice on how to weigh the two options."),
        ("outcome", "Likely Outcome", "可能结果", "The probable result of the choice you lean toward."),
    ),
)

SPREADS: dict[str, Spread] = {
    spread.id: spread
    for spread in (
        _SINGLE,
        _THREE_CARD,
        _CELTIC_CROSS,
        _RELATIONSHIP,
        _CAREER,
        _DECISION,
    )
}


def get_spread(spread_id: str) -> Spread | None:
    """Return the spread with ``spread_id`` or ``None`` if it is not defined."""
    return SPREADS.get(spread_id)
