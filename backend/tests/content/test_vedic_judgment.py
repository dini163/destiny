"""九曜吉凶与擢升陷落判定表的本地门（verdict 判定层的锚，`content/vedic_judgment.py`）。

词/表全覆盖：自然吉凶表与擢升陷落表都必须收齐九曜、不得多不得少；吉凶三分（吉/中性/凶），
擢升与陷落星座不得同宫；结论框架句覆盖共享五档。聚合折算在引擎，由 golden 对账。

复测：`cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m pytest tests/content/test_vedic_judgment.py -v`
"""

from app.content.vedic import GRAHAS
from app.content.vedic_judgment import (
    DIGNITY,
    DIGNITY_BY_NAME,
    NATURAL_QUALITY,
    QUALITY_BY_NAME,
    VERDICT_ADVICE,
    VERDICT_OUTLOOK,
    VERDICT_SUMMARY_FRAME,
)

_EXPECTED_NAMES = {g.name for g in GRAHAS}


def test_natural_quality_table_covers_all_nine_grahas_without_gaps() -> None:
    """自然吉凶表收齐九曜，与 `content/vedic.py::GRAHAS` 同名集合相等，不增不减。"""
    assert {row.name for row in NATURAL_QUALITY} == _EXPECTED_NAMES
    assert len(NATURAL_QUALITY) == 9
    assert QUALITY_BY_NAME["Jupiter"].quality == "benefic"
    assert QUALITY_BY_NAME["Venus"].quality == "benefic"
    assert QUALITY_BY_NAME["Mars"].quality == "malefic"
    assert QUALITY_BY_NAME["Saturn"].quality == "malefic"
    assert QUALITY_BY_NAME["Rahu"].quality == "malefic"
    assert QUALITY_BY_NAME["Ketu"].quality == "malefic"
    for neutral in ("Sun", "Moon", "Mercury"):
        assert QUALITY_BY_NAME[neutral].quality == "neutral"


def test_every_quality_row_carries_a_chapter_level_source() -> None:
    """每行带经典章属出处（到章不到书，R46 自撰+双署）。"""
    for row in NATURAL_QUALITY:
        assert row.source
        assert "Brihat Parashara" in row.source


def test_dignity_table_covers_all_nine_grahas_and_exalt_differs_from_debil() -> None:
    """擢升/陷落表收齐九曜；擢升星座 ≠ 陷落星座，且都在 0-11 星座序内。"""
    assert {row.name for row in DIGNITY} == _EXPECTED_NAMES
    assert len(DIGNITY) == 9
    for row in DIGNITY:
        assert 0 <= row.exaltation <= 11
        assert 0 <= row.debilitation <= 11
        assert row.exaltation != row.debilitation
        assert row.source
        assert "Uchcha" in row.source


def test_frame_dict_cover_all_five_shared_grades() -> None:
    """取向与建议两表都覆盖共享五档，总论框架含槽位。"""
    grades = {"大吉", "吉", "平", "小凶", "凶"}
    assert set(VERDICT_OUTLOOK) == grades
    assert set(VERDICT_ADVICE) == grades
    for outlook in VERDICT_OUTLOOK.values():
        assert outlook and "。" not in outlook
    for advice in VERDICT_ADVICE.values():
        assert advice.endswith("。")
    for slot in ("{grade}", "{benefic}", "{malefic}", "{exalted}", "{debased}", "{outlook}"):
        assert slot in VERDICT_SUMMARY_FRAME
