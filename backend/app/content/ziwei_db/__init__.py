"""Ziwei interpretation database package."""

from app.content.ziwei_db.star_db import STAR_DB, STAR_META_DB, STAR_SECTIONS_DB
from app.content.ziwei_db.combo_db import COMBO_DB, DUAL_STAR_SECTION_DB
from app.content.ziwei_db.pattern_db import PATTERN_DB, SPECIAL_PATTERNS_DB, YANGZHAI_HUAMING_TOPIC
from app.content.ziwei_db.chart_tables import (
    KUIYUE_DESC_DB,
    NIANGAN_SIHUA_IMPACT_DB,
    QUANSHU_JUAN2_DB,
    SANFANG_AUX_DESC_DB,
    SANFANG_STAR_DESC_DB,
    SECOND_STAR_DESC_DB,
    SIHUA_STAR_DESC_DB,
    STAR_AUX_DB,
    STAR_BRIGHTNESS_DB,
    STAR_SIHUA_DB,
    TARGET_CHART_NOTES_DB,
    TOPIC_SUMMARY_DB,
    ZANGFU_DB,
)

__all__ = [
    "STAR_DB",
    "STAR_META_DB",
    "STAR_SECTIONS_DB",
    "COMBO_DB",
    "DUAL_STAR_SECTION_DB",
    "PATTERN_DB",
    "SPECIAL_PATTERNS_DB",
    "YANGZHAI_HUAMING_TOPIC",
    "STAR_AUX_DB",
    "TOPIC_SUMMARY_DB",
    "STAR_BRIGHTNESS_DB",
    "STAR_SIHUA_DB",
    "SECOND_STAR_DESC_DB",
    "SANFANG_STAR_DESC_DB",
    "SANFANG_AUX_DESC_DB",
    "SIHUA_STAR_DESC_DB",
    "KUIYUE_DESC_DB",
    "NIANGAN_SIHUA_IMPACT_DB",
    "ZANGFU_DB",
    "QUANSHU_JUAN2_DB",
    "TARGET_CHART_NOTES_DB",
]
