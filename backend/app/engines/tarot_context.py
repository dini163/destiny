"""Read existing draw keywords through an explicitly selected lens."""

from app.content import CONTENT_VERSION, TAROT_CONTEXT_SOURCES
from app.content.tarot_context import TOPICS
from app.schemas.common import ProvenanceTable


def contextual_reading(cards, topic):
    title, question, action = TOPICS[topic]
    lines = [
        f"阅读主题：{title}。以下提纲基于你选择的主题，不分析自由文字，也不声称知道现实发生了什么。"
    ]
    for card in cards:
        keywords = "、".join(card.keywords_zh[:3])
        lines.append(f"{card.position_label_zh} · {card.name_zh}（{keywords}）：{question}")
    lines.append(f"可以尝试：{action}")
    return lines


def apply_context(result, topic):
    result.contextual_reading = contextual_reading(result.cards, topic)
    result.provenance.tables.extend(
        ProvenanceTable(name=name, source=source, version=CONTENT_VERSION)
        for name, source in TAROT_CONTEXT_SOURCES
    )
    return result
