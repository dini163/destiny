"""Curated content datasets (real reference content, never generated at runtime).

Each content module is authored from authoritative public-domain sources and is
guarded by count-invariant tests (e.g. 78 tarot cards, 64 hexagrams, 384 lines).

``CONTENT_VERSION`` is the roll-up version those tests protect: a corpus edit and
a version bump are one change, because responses echo the version per table and
``tests/test_bazi_schema.py`` fails when a table moves without it.
"""

from importlib.metadata import version

from app.content.bazi_changsheng import CHANG_SHENG_SOURCE
from app.content.bazi_hehun_rules import HEHUN_RULE_SOURCE
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

#: 历注宜忌一张表。单列的理由同 `TRANSIT_CONTENT_SOURCES`：矩阵页之外没有人引用它。
ALMANAC_CONTENT_SOURCES: tuple[tuple[str, str], ...] = (
    (
        "almanac_yiji",
        "外部历法库 lunar-python（6tail/lunar-python）之通书宜忌，非本仓古籍语料，不参与任何计分",
    ),
)
#: 历注的版本**不**取 `CONTENT_VERSION`：通书宜忌随库版本变，用本仓语料的滚动版本给
#: 外部内容打版等于撒一个谎（spec §7.5）。
ALMANAC_CONTENT_VERSION = version("lunar-python")

#: `CONTENT_SOURCES` 的按名索引。合婚与后续任何"只引其中几页"的端点都用它取，
#: 免得把书名逐字抄第二遍 —— 抄一份错一处，书名也就分了家。
NATAL_SOURCE_BY_MODULE: dict[str, str] = dict(CONTENT_SOURCES)

#: 合婚一页真正读到的十张表。单列的理由同 `NAME_CONTENT_SOURCES`：`bazi_dimensions`
#: （六维详批）在本页既没参与计算也没有呈现，列进来等于让合婚声称引了它没引的书；
#: 而 `bazi_wangshuai` / `bazi_geju` / `bazi_tiaohou` 三张看着像"本命盘的事"，
#: 其实两造的喜忌集正是由它们合并出来的（互补图与宜忌的唯一输入），一张都删不得。
#: 岁运那两张由轻量轴读：轴行一分一档与 `/bazi/liuyue` 的年表同一把尺（合婚 spec §10.5）。
HEHUN_CONTENT_SOURCES: tuple[tuple[str, str], ...] = (
    ("bazi_shishen", NATAL_SOURCE_BY_MODULE["bazi_shishen"]),
    ("bazi_nayin", NATAL_SOURCE_BY_MODULE["bazi_nayin"]),
    ("bazi_wangshuai", NATAL_SOURCE_BY_MODULE["bazi_wangshuai"]),
    ("bazi_geju", NATAL_SOURCE_BY_MODULE["bazi_geju"]),
    ("bazi_tiaohou", NATAL_SOURCE_BY_MODULE["bazi_tiaohou"]),
    ("bazi_shensha", NATAL_SOURCE_BY_MODULE["bazi_shensha"]),
    ("bazi_relations", NATAL_SOURCE_BY_MODULE["bazi_relations"]),
    *TRANSIT_CONTENT_SOURCES,
    ("bazi_hehun_rules", HEHUN_RULE_SOURCE),
)
