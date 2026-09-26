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
from app.content.kabbalah import KABBALAH_SOURCE
from app.content.kangxi_strokes import STROKE_SOURCE as KANGXI_STROKE_SOURCE
from app.content.lenormand import LENORMAND_SOURCE
from app.content.name_numerology import NUMEROLOGY_SOURCE
from app.content.name_sancai import SANCAI_SOURCE
from app.content.numerology_cycles import CYCLES_SOURCE
from app.content.numerology_loshu import LOSHU_SOURCE
from app.content.numerology_meanings import MEANINGS_SOURCE
from app.content.numerology_pythagorean import PYTHAGOREAN_SOURCE
from app.content.qimen import QIMEN_SOURCE
from app.content.rune_futhark import RUNES_SOURCE
from app.content.rune_spreads import SPREADS_SOURCE
from app.content.synastry import SYNASTRY_SOURCE
from app.content.vedic import VEDIC_SOURCE
from app.content.ziwei import ZIWEI_SOURCE
from app.core.provenance import MODEL_PARAM_SOURCE

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

#: 数字命理一页真正读到的四张表。单列的理由同 `NAME_CONTENT_SOURCES`：混进
#: `CONTENT_SOURCES` 等于让八字声称引了它没用过的表。四张不多不少，其中
#: `numerology_loshu` 属印度数理传统而非毕达哥拉斯体系，它的出处字符串自己说清了
#: 这一点（数字命理 spec §11 残余风险 3）—— 两张九宫共用一个端点，但各署各的名。
NUMEROLOGY_CONTENT_SOURCES: tuple[tuple[str, str], ...] = (
    ("numerology_pythagorean", PYTHAGOREAN_SOURCE),
    ("numerology_meanings", MEANINGS_SOURCE),
    ("numerology_cycles", CYCLES_SOURCE),
    ("numerology_loshu", LOSHU_SOURCE),
)

#: 卢恩一页真正读到的两张表。单列的理由同 `NAME_CONTENT_SOURCES`：混进
#: `CONTENT_SOURCES` 等于让八字声称引了它没用过的表。两张不多不少：一张管
#: 24+1 枚符文本体（序位、字形、释义），一张管三种牌阵的位次。它们分开署名而不是
#: 合成一张，是因为两者的凭据不同：前者的字形可以拿 `unicodedata.name()` 逐字核（客观、
#: 可单测），后者的位次只是现代通行约定（主观、不可核）—— 合表会把后者的确定性
#: 抬高到前者的水平（卢恩 spec 决策 24）。版本仍取共用的 `CONTENT_VERSION`，同数字命理。
RUNE_CONTENT_SOURCES: tuple[tuple[str, str], ...] = (
    ("rune_futhark", RUNES_SOURCE),
    ("rune_spreads", SPREADS_SOURCE),
)

#: 紫微斗数一页真正读到的一张表：十四主星与乙级星之五行/星系、生年干四化、
#: 命主身主、纳音五行局与十二宫序。单列理由同 `NAME_CONTENT_SOURCES`：混进
#: `CONTENT_SOURCES` 等于让八字声称引了它没用过的斗数安星表。
ZIWEI_CONTENT_SOURCES: tuple[tuple[str, str], ...] = (
    ("ziwei", ZIWEI_SOURCE),
)

#: 奇门遁甲一页真正读到的一张表：洛书九宫、九星八门八神、三奇六仪甲遁、
#: 阳遁/阴遁 节气局数表、三元符头与旬空驿马。单列理由同 `ZIWEI_CONTENT_SOURCES`。
QIMEN_CONTENT_SOURCES: tuple[tuple[str, str], ...] = (
    ("qimen", QIMEN_SOURCE),
)

#: 雷诺曼一页真正读到的一张表：36 张牌义（编号、中英文名、吉凶极性、关键词、
#: 组合直读之名词核心与修饰词）与五种牌阵位次。单列理由同 `ZIWEI_CONTENT_SOURCES`。
LENORMAND_CONTENT_SOURCES: tuple[tuple[str, str], ...] = (
    ("lenormand", LENORMAND_SOURCE),
)

#: 卡巴拉一页真正读到的一张表：十原质（三柱四界、行星守护、王徽色、大天使与神名）、
#: 隐藏的 Daath 与 22 路径（希伯来字母 / 塔罗大阿卡纳 / 行星星座元素）之黄金黎明对应。
#: 单列理由同 `ZIWEI_CONTENT_SOURCES`。
KABBALAH_CONTENT_SOURCES: tuple[tuple[str, str], ...] = (
    ("kabbalah", KABBALAH_SOURCE),
)

#: 吠陀占星一页真正读到的一张表：恒星黄道十二星座、九曜（Navagraha）、27 宿
#: （Nakshatra，各含守护曜与主神）与 Vimshottari 大运值年序。单列理由同
#: `ZIWEI_CONTENT_SOURCES`：主八字盘不引用它们。
VEDIC_CONTENT_SOURCES: tuple[tuple[str, str], ...] = (
    ("vedic", VEDIC_SOURCE),
)

#: 西洋合盘一页真正读到的一张表：相契度赋分权重（相位基准分、核心羁绊强调、
#: 容许度衰减与四档分界）。单列理由同 `ZIWEI_CONTENT_SOURCES`：主八字盘不引用它，
#: 且它是本系统模型参数而非古籍语料，出处串自己说清了这一点。
SYNASTRY_CONTENT_SOURCES: tuple[tuple[str, str], ...] = (
    ("synastry_scoring", SYNASTRY_SOURCE),
)
