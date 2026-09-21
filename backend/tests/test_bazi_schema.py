"""The JSON contract: old keys keep working, new keys carry their own provenance."""

from datetime import date, time

import pytest

from app.content import CONTENT_VERSION
from app.content.bazi_shishen import TEN_GOD_MEANING
from app.engines.bazi import compute_bazi_chart
from app.schemas.common import Gender

REFERENCE_DATE = date(2026, 9, 20)
CHART = compute_bazi_chart(
    birth_date=date(1988, 2, 15), birth_time=time(23, 30), longitude=104.1,
    gender=Gender.MALE, apply_true_solar_time=True, reference_date=REFERENCE_DATE,
)

NEW_KEYS = {
    "name", "geju", "yongshen", "shensha", "ten_god_readings", "relations", "branch_groups",
    "hidden_stem_ledger", "dayun_current", "interpretation", "provenance",
}


def test_legacy_keys_are_unchanged() -> None:
    payload = CHART.model_dump()
    assert payload["four_pillars"] == "戊辰 甲寅 庚子 丁亥"
    assert payload["analysis"]["level"] == "weak"
    # 旧 key 不删不改名，但取值口径已迁到三法合并结果（spec §7）
    assert payload["analysis"]["favorable_elements"] == payload["yongshen"]["favorable_elements"]


def test_new_keys_are_present_and_typed() -> None:
    payload = CHART.model_dump()
    assert NEW_KEYS <= set(payload)
    assert payload["geju"]["name"] == "偏财格"
    assert [d["dimension"] for d in payload["interpretation"]["six_dimensions"]] == [
        "事业", "财运", "婚姻", "健康", "学业", "人际",
    ]


def test_missing_elements_uses_primary_and_hidden_scope() -> None:
    """庚日主通根于辰中戊土、五行俱全，故本命无缺行；口径写在字段描述里。"""
    assert CHART.missing_elements == []


def test_ten_god_readings_are_corpus_lookup_not_invention() -> None:
    """每条摘要都是语料原样：count 与 positions 自洽，释义来自 content。"""
    for reading in CHART.ten_god_readings:
        corpus = TEN_GOD_MEANING[reading.ten_god]
        assert reading.count == len(reading.positions)
        assert reading.meaning == corpus.meaning and reading.source == corpus.source
        assert reading.six_relation == corpus.six_relations["男命"]      # CHART 为乾造
    covered = {r.ten_god for r in CHART.ten_god_readings}
    assert covered <= set(TEN_GOD_MEANING)


def test_dayun_current_agrees_with_the_flagged_step() -> None:
    """`dayun_current` 与 `dayun[].is_current` 是同一事实的两个视图，必须互指。"""
    flagged = [step for step in CHART.dayun if step.is_current]
    assert len(flagged) == 1
    assert CHART.dayun_current is not None
    assert CHART.dayun_current.index == flagged[0].index
    assert all(r.pillar_a.startswith("extra") or r.pillar_b.startswith("extra")
               for r in CHART.dayun_current.relations)


def test_provenance_is_self_describing() -> None:
    assert CHART.provenance.reference_date == "2026-09-20"
    assert CHART.provenance.engine == "lunar-python"
    assert CHART.provenance.tables, "溯源表为空等于没有溯源"
    assert {table.version for table in CHART.provenance.tables} == {CONTENT_VERSION}


def test_every_score_in_the_payload_is_ledgered() -> None:
    """遍历 wire payload：凡 value/tier/factors 三件套都必须账本闭合。"""

    def walk(node) -> None:
        if isinstance(node, dict):
            if {"value", "tier", "factors"} <= node.keys():
                deltas = [factor["delta"] for factor in node["factors"]]
                assert sum(deltas) == pytest.approx(node["value"], abs=0.05)
                assert 0.0 <= node["value"] <= 100.0
                assert node["factors"][0]["rule"].endswith(".base")
                assert all(factor["source"] for factor in node["factors"])
            for child in node.values():
                walk(child)
        elif isinstance(node, list):
            for child in node:
                walk(child)

    walk(CHART.model_dump())


def test_name_is_echoed_without_changing_the_chart() -> None:
    """称谓只回显：除 `name` 本身外，带与不带的响应必须逐字段相同。"""
    named = compute_bazi_chart(
        birth_date=date(1988, 2, 15), birth_time=time(23, 30), longitude=104.1,
        gender=Gender.MALE, apply_true_solar_time=True, reference_date=REFERENCE_DATE,
        name="示例甲",
    )
    assert named.name == "示例甲"
    assert named.model_dump(exclude={"name"}) == CHART.model_dump(exclude={"name"})
