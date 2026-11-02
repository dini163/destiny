"""Explicit lenses over real CSPRNG draws; free text is never interpreted as fact."""

from fastapi.testclient import TestClient

from app.engines.tarot import draw_spread
from app.engines.tarot_context import contextual_reading
from app.main import app


def test_same_real_draw_produces_distinct_explicit_topic_prompts():
    cards = draw_spread(spread_id="three_card").cards
    relationship = contextual_reading(cards, "relationship")
    career = contextual_reading(cards, "career")
    assert relationship != career
    assert "关系沟通" in relationship[0]
    assert "工作与任务" in career[0]
    for card in cards:
        assert any(card.name_zh in line and card.keywords_zh[0] in line for line in relationship)


def test_topic_contract_and_consumed_table_are_returned():
    with TestClient(app) as client:
        body = client.post(
            "/api/v1/tarot/spread", json={"spread_id": "single", "reading_topic": "career"}
        )
        assert body.status_code == 200
        assert "工作与任务" in body.json()["contextual_reading"][0]
        assert body.json()["provenance"]["tables"][-1]["name"] == "tarot_context"
        assert (
            client.post(
                "/api/v1/tarot/spread", json={"spread_id": "single", "reading_topic": "invented"}
            ).status_code
            == 422
        )
