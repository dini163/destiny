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

#: 牌义与布局的书级出处：三张牌表（`tarot_major` / `tarot_minor` / `tarot_deck`）共用这一串，
#: 因为它们的凭据是同一条；关键词中译表另有其串（`tarot_keywords_zh.TAROT_KEYWORDS_ZH_SOURCE`），
#: 理由见 `content/__init__.py` 的 `TAROT_CONTENT_SOURCES` 注（G14）。
TAROT_SOURCE = "Rider-Waite-Smith 塔罗通行牌义 · 78 张大小阿卡纳与六种 Waite 系布阵位次（PRD 6.7）"

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
    meaning_zh: str   # the same gloss in Chinese (paired, not retold)


@dataclass(frozen=True)
class Spread:
    """A named card layout with an ordered list of positions."""

    id: str
    name: str
    name_zh: str
    description: str
    description_zh: str
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
    description_zh: str,
    positions: tuple[tuple[str, str, str, str, str], ...],
) -> Spread:
    """Build a :class:`Spread` from raw ``(key, label, label_zh, meaning, meaning_zh)`` tuples."""
    return Spread(
        id=id,
        name=name,
        name_zh=name_zh,
        description=description,
        description_zh=description_zh,
        positions=tuple(SpreadPosition(*p) for p in positions),
    )


_SINGLE = _spread(
    "single", "Single Card", "单张牌",
    "One card for a daily reflection or a quick, focused answer.",
    "抽一张牌，用于一天的自省，或对一个焦点问题要个干脆的答复。",
    (
        ("guidance", "Guidance", "指引", "The central theme or advice for the question or day.", "指引位给出整件事的核心主题，也就是这次求问或这一天得到的提示。"),
    ),
)

_THREE_CARD = _spread(
    "three_card", "Three Card", "时间之流三张",
    "The flow of a situation across time: past, present and future.",
    "三张牌铺开一条时间线，看一件事的来路、当下与去处。",
    (
        ("past", "Past", "过去", "Roots and events already shaping the situation.", "过去位看的是根子，那些已经发生、正在塑造当下局面的事。"),
        ("present", "Present", "现在", "The current dynamics and where you stand now.", "现在位看的是眼下的动势，以及你此刻站的位置。"),
        ("future", "Future", "未来", "The likely direction if things continue as they are.", "未来位看的是照目前的走向继续下去，事情大概会往哪去。"),
    ),
)

_CELTIC_CROSS = _spread(
    "celtic_cross", "Celtic Cross", "凯尔特十字",
    "The classic ten-card spread for a deep, layered reading of a situation.",
    "经典的十张牌阵，用于把一个问题做深、做透的多层解读。",
    (
        ("present", "Present", "现状", "The heart of the matter, the situation as it stands.", "现状位是这件事的核心，也是它此刻的样子。"),
        ("challenge", "Challenge", "挑战", "The immediate obstacle or opposing force, laid across the present.", "挑战位是摆在现状跟前的阻碍，或是那股与它相对的力量。"),
        ("foundation", "Foundation", "根基", "The subconscious basis or root cause beneath the situation.", "根基位在水面之下，是促成局面那个你未必察觉的根由。"),
        ("recent_past", "Recent Past", "近期过去", "Recent events now receding but still influential.", "近期过去位是已经淡出、却还在起作用的近几件事。"),
        ("crown", "Crown", "显意识", "The conscious aim or best possible outcome overhead.", "显意识位是你明面上认定的目标，也是这件事最好的可能。"),
        ("near_future", "Near Future", "近期未来", "What is approaching in the immediate future.", "近期未来位是紧接着就要上门的那部分。"),
        ("self", "Self", "自我态度", "Your own attitude and approach to the situation.", "自我态度位讲的是你自己对这件事的态度与打法。"),
        ("environment", "Environment", "环境影响", "External influences and the people around you.", "环境影响位是外来的作用力，和你身边那个人群。"),
        ("hopes_fears", "Hopes & Fears", "希望与恐惧", "What you hope for and what you fear, often the same.", "希望与恐惧位是你所盼的和你所怕的，两者常常是同一件事。"),
        ("outcome", "Outcome", "最终结果", "The likely outcome given the current trajectory.", "最终结果位是按眼下的轨迹推下去，最可能落成的那个结果。"),
    ),
)

_RELATIONSHIP = _spread(
    "relationship", "Relationship", "关系牌阵",
    "A five-card spread reading both partners and the bond between them.",
    "五张牌分别读双方，以及把两人连在一起的那条纽带。",
    (
        ("you", "You", "你", "Your feelings, needs and stance in the relationship.", "你位讲的是你在这段关系里的感受、你看重的东西与你的立场。"),
        ("partner", "Partner", "对方", "The other person's feelings, needs and stance.", "对方位讲的是另一方的感受、他或她看重的东西与立场。"),
        ("connection", "Connection", "关系本质", "The nature of the bond that currently links you.", "关系本质位是把你们连在一起的那条纽带，此刻是什么样。"),
        ("challenge", "Challenge", "挑战", "The main difficulty or friction to work through.", "挑战位是这段关系里主要那道难关，或要磨合的摩擦。"),
        ("potential", "Potential", "发展方向", "Where the relationship is heading if nurtured.", "发展方向位是这段关系被好好经营时要去的地方。"),
    ),
)

_CAREER = _spread(
    "career", "Career", "事业牌阵",
    "A five-card spread for work, projects and professional direction.",
    "五张牌读工作、项目与事业上的方向。",
    (
        ("current", "Current Position", "当前处境", "Where you stand in your work right now.", "当前处境位是你在工作里此刻站的位置。"),
        ("strength", "Strength", "优势", "The assets and skills working in your favour.", "优势位是正在替你出力的本钱与技能。"),
        ("obstacle", "Obstacle", "阻碍", "The challenge or limitation blocking progress.", "阻碍位是挡住进展的那道挑战或限制。"),
        ("action", "Action", "行动建议", "The practical step to take next.", "行动位讲的是下一步要迈出去的那个具体动作。"),
        ("outcome", "Outcome", "事业走向", "The likely professional result of the current path.", "事业走向位是这条路径大概率落成的职业结果。"),
    ),
)

_DECISION = _spread(
    "decision", "Decision", "是非抉择牌阵",
    "A five-card spread comparing two options to inform a choice.",
    "五张牌把两个选项摆在一起对照，供你做选择时参考。",
    (
        ("situation", "Situation", "当前局面", "The decision you face and its context.", "当前局面位是你面对的这道选择，以及它的来龙去脉。"),
        ("option_a", "Option A", "选择甲", "The nature and energy of the first path.", "选择甲位讲的是第一条路的性质与那股劲。"),
        ("option_b", "Option B", "选择乙", "The nature and energy of the second path.", "选择乙位讲的是第二条路的性质与那股劲。"),
        ("guidance", "Guidance", "指引", "Advice on how to weigh the two options.", "指引位讲的是该用什么尺度去掂这两条路。"),
        ("outcome", "Likely Outcome", "可能结果", "The probable result of the choice you lean toward.", "可能结果位是你心里偏向的那条选择大概会得到什么。"),
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
