"""Curated content datasets (real reference content, never generated at runtime).

Each content module is authored from authoritative public-domain sources and is
guarded by count-invariant tests (e.g. 78 tarot cards, 64 hexagrams, 384 lines).

``CONTENT_VERSION`` is the roll-up version those tests protect: a corpus edit and
a version bump are one change, because responses echo the version per table and
``tests/test_bazi_schema.py`` fails when a table moves without it.
"""

from app.content.bazi_changsheng import CHANG_SHENG_SOURCE
from app.content.bazi_tiaohou import TIAOHOU_SOURCE
from app.content.bazi_transit_rules import TRANSIT_RULE_SOURCE
from app.content.kangxi_strokes import STROKE_SOURCE as KANGXI_STROKE_SOURCE
from app.content.name_numerology import NUMEROLOGY_SOURCE
from app.content.name_sancai import SANCAI_SOURCE
from app.schemas.scoring import MODEL_PARAM_SOURCE

CONTENT_VERSION = "2026.09"

#: 书级出处，按模块名回显在响应的 `provenance.tables` 里。逐条出处始终在各条目
#: 自己的 `source` 字段（到章不到书），这里只到书；模型参数与古籍同表时必须两段都写，
#: 免得一张表看起来比它实际有的更"有出处"。
CONTENT_SOURCES: tuple[tuple[str, str], ...] = (
    ("bazi_shishen", "《渊海子平》"),
    ("bazi_nayin", "《三命通会》"),
    ("bazi_wangshuai", f"《三命通会》定等第次序 · {MODEL_PARAM_SOURCE}"),
    ("bazi_geju", "《三命通会》《渊海子平》"),
    ("bazi_tiaohou", TIAOHOU_SOURCE),
    ("bazi_shensha", "《三命通会》《渊海子平》"),
    ("bazi_relations", "《三命通会》《渊海子平》《滴天髓》"),
    ("bazi_dimensions", f"引文为判语（健康维只署本系统） · {MODEL_PARAM_SOURCE}"),
)

#: 姓名学三表。单列一份是刻意的：`CONTENT_SOURCES` 会被 `app/engines/bazi.py:378`
#: 整表回显进每一个八字响应，把姓名学语料混进去就是让八字声称自己引用了它没用的表。
NAME_CONTENT_SOURCES: tuple[tuple[str, str], ...] = (
    ("kangxi_strokes", KANGXI_STROKE_SOURCE),
    ("name_numerology", NUMEROLOGY_SOURCE),
    ("name_sancai", SANCAI_SOURCE),
)

#: 岁运两张表。单列一份的理由同 `NAME_CONTENT_SOURCES`：主命盘不引用它们，
#: 混进 `CONTENT_SOURCES` 等于让 `/natal` 声称引了它没用过的表。
TRANSIT_CONTENT_SOURCES: tuple[tuple[str, str], ...] = (
    ("bazi_changsheng", CHANG_SHENG_SOURCE),
    ("bazi_transit_rules", TRANSIT_RULE_SOURCE),
)
