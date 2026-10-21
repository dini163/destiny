"""Curated content datasets (real reference content, never generated at runtime).

Each content module is authored from authoritative public-domain sources and is
guarded by count-invariant tests (e.g. 78 tarot cards, 64 hexagrams, 384 lines).

``CONTENT_VERSION`` is the roll-up version those tests protect: a corpus edit and
a version bump are one change, because responses echo the version per table and
``tests/test_bazi_schema.py`` fails when a table moves without it.
"""

from importlib.metadata import version

from app.content.aspects_nature import ASPECT_NATURE_SOURCE
from app.content.bazi_changsheng import CHANG_SHENG_SOURCE
from app.content.bazi_hehun_rules import HEHUN_RULE_SOURCE
from app.content.bazi_plain import PLAIN_SOURCE
from app.content.bazi_tiaohou import TIAOHOU_SOURCE
from app.content.bazi_transit_plain import BAZI_TRANSIT_PLAIN_SOURCE
from app.content.bazi_transit_rules import TRANSIT_RULE_SOURCE
from app.content.hehun_plain import HEHUN_PLAIN_SOURCE
from app.content.kabbalah import KABBALAH_SOURCE
from app.content.kabbalah_plain import KABBALAH_PLAIN_SOURCE
from app.content.kangxi_strokes import STROKE_SOURCE as KANGXI_STROKE_SOURCE
from app.content.lenormand import LENORMAND_SOURCE
from app.content.lenormand_plain import LENORMAND_PLAIN_SOURCE
from app.content.meihua import MEIHUA_SOURCE
from app.content.meihua_plain import MEIHUA_PLAIN_SOURCE
from app.content.name_numerology import NUMEROLOGY_SOURCE
from app.content.name_plain import NAME_PLAIN_SOURCE
from app.content.name_sancai import SANCAI_SOURCE
from app.content.numerology_cycles import CYCLES_SOURCE
from app.content.numerology_loshu import LOSHU_SOURCE
from app.content.numerology_meanings import MEANINGS_SOURCE
from app.content.numerology_pythagorean import PYTHAGOREAN_SOURCE
from app.content.qimen import QIMEN_SOURCE
from app.content.qimen_plain import QIMEN_PLAIN_SOURCE
from app.content.rune_futhark import RUNES_SOURCE
from app.content.rune_spreads import SPREADS_SOURCE
from app.content.synastry import SYNASTRY_SOURCE
from app.content.synastry_plain import SYNASTRY_PLAIN_SOURCE
from app.content.tarot_deck import TAROT_SOURCE
from app.content.tarot_keywords_zh import TAROT_KEYWORDS_ZH_SOURCE
from app.content.transit_plain import TRANSIT_PLAIN_SOURCE
from app.content.vedic import VEDIC_SOURCE
from app.content.vedic_plain import VEDIC_PLAIN_SOURCE
from app.content.western_plain import WESTERN_PLAIN_NOTE, WESTERN_PLAIN_SOURCE
from app.content.zhouyi_hexagrams import ZHOUYI_HEXAGRAMS_SOURCE
from app.content.zhouyi_najia import ZHOUYI_NAJIA_SOURCE
from app.content.zhouyi_plain import ZHOUYI_PLAIN_SOURCE
from app.content.zhouyi_text import ZHOUYI_SOURCE
from app.content.zhouyi_trigrams import ZHOUYI_TRIGRAMS_SOURCE
from app.content.ziwei import ZIWEI_SOURCE
from app.content.ziwei_plain import ZIWEI_PLAIN_SOURCE
from app.core.provenance import MODEL_PARAM_SOURCE

#: 行运一页真正读到的三张表：三层相位的白话表（600 条）、次限月亮与四轴的白话表（48 条）、
#: 相位属性表。单列理由同 `WESTERN_CONTENT_SOURCES`：混进 `TRANSIT_CONTENT_SOURCES`
#: 等于让**八字岁运**响应声称引用了西洋语料（那两个名字撞车，本名单必须与之分开维护）。
#: 前两张共用 `TRANSIT_PLAIN_SOURCE`：它们是同一张自撰表的两半，串里讲的正是这两半共同做的事。
#: 第三行用它自己的串：`aspects_nature` 讲的是通行归类不是自撰判语，共用那串等于把
#: 「不署书名是因为没有古籍可引」的理由安到一张本来就不是判语的表上。
TRANSIT_OVERLAY_CONTENT_SOURCES: tuple[tuple[str, str], ...] = (
    ("transit_plain", TRANSIT_PLAIN_SOURCE),
    ("transit_plain_aspect", TRANSIT_PLAIN_SOURCE),
    ("aspects_nature", ASPECT_NATURE_SOURCE),
)

CONTENT_VERSION = "2026.09"

#: 书级出处，按模块名回显在响应的 `provenance.tables` 里。逐条出处始终在各条目
#: 自己的 `source` 字段（到章不到书），这里只到书；模型参数与古籍同表时必须两段都写，
#: 免得一张表看起来比它实际有的更"有出处"。
#: 这份清单是被 `engines/bazi.py` 整表回显的那一份，所以它的准入条件是「凡是在响应里
#: 呈现六维解读的那一页都读得到」：`bazi_plain` 与 `bazi_dimensions` 的唯一读者
#: 都是 `interpret_chart`，而流日/流时/岁运页经 `compute_bazi_chart` 照样调它
#: （三个调用点各在本页的装配函数里：`compute_liuri_matrix`、`compute_transit`、
#: `compute_liushi_day`，复测：`cd backend && grep -n "compute_bazi_chart(" app/engines/bazi_liuri.py app/engines/bazi_transit.py app/engines/bazi_liushi.py`）。把这些页已经
#: 认账的兄表列着、把同一条路径上的弟表单列出去，就是 AGENTS.md §7 反过来的那种不诚实
#: ——「少一行是不认账」（`bazi_liuri.py` 的 `liuri_provenance` 头注，复测：
#: `cd backend && grep -n "少一行是不认账" app/engines/bazi_liuri.py`）。故白话表随兄表同进本清单，不另立
#: `PLAIN_CONTENT_SOURCES`。**这句只管 `CONTENT_SOURCES` 这一侧**：合婚页不靠继承这张表拿到
#: 白话，它自己读的 `hehun_plain` 是按页清单里逐名列举的第 11 行（见下方
#: `HEHUN_CONTENT_SOURCES` 头注，复测：`cd backend && grep -n '("hehun_plain", ' app/content/__init__.py`
#: → 149 行一处，即只按页列举、没有进本清单）。不跟着加的是 `bazi_plain` 那一行——
#: 合婚页连 `bazi_dimensions` 都不列。
#: 条目数复测：`cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "from app.content import CONTENT_SOURCES; print(len(CONTENT_SOURCES))"` → 9。
CONTENT_SOURCES: tuple[tuple[str, str], ...] = (
    ("bazi_shishen", "《渊海子平》"),
    ("bazi_nayin", "《三命通会》"),
    ("bazi_wangshuai", f"《三命通会》定等第次序 · {MODEL_PARAM_SOURCE}"),
    ("bazi_geju", "《三命通会》《渊海子平》"),
    ("bazi_tiaohou", TIAOHOU_SOURCE),
    ("bazi_shensha", "《三命通会》《渊海子平》"),
    ("bazi_relations", "《三命通会》《渊海子平》《滴天髓》"),
    ("bazi_dimensions", f"引文为判语（健康维只署本系统） · {MODEL_PARAM_SOURCE}"),
    ("bazi_plain", PLAIN_SOURCE),
)

#: 姓名学四表。单列一份是刻意的：`CONTENT_SOURCES` 会被 `app/engines/bazi.py:355`
#: 整表回显进每一个八字响应，把姓名学语料混进去就是让八字声称自己引用了它没用的表。
NAME_CONTENT_SOURCES: tuple[tuple[str, str], ...] = (
    ("kangxi_strokes", KANGXI_STROKE_SOURCE),
    ("name_numerology", NUMEROLOGY_SOURCE),
    ("name_sancai", SANCAI_SOURCE),
    ("name_plain", NAME_PLAIN_SOURCE),
)

#: 岁运两张表。单列一份的理由同 `NAME_CONTENT_SOURCES`：主命盘不引用它们，
#: 混进 `CONTENT_SOURCES` 等于让 `/natal` 声称引了它没用过的表。
TRANSIT_CONTENT_SOURCES: tuple[tuple[str, str], ...] = (
    ("bazi_changsheng", CHANG_SHENG_SOURCE),
    ("bazi_transit_rules", TRANSIT_RULE_SOURCE),
)

#: 岁运三片的白话转述表。**刻意不并进 `TRANSIT_CONTENT_SOURCES`**：那张清单被
#: `HEHUN_CONTENT_SOURCES` 用 `*` 展开复用，加进去等于让合婚页声称读了它没读的表
#: （AGENTS §7、本文件 :50-51 注）。它只在 `compute_transit` 与 `liuri_provenance` 两处展开。
#: 复测：`cd backend && grep -n "BAZI_TRANSIT_PLAIN_CONTENT_SOURCES" app/content/__init__.py app/engines/bazi_transit.py app/engines/bazi_liuri.py`
BAZI_TRANSIT_PLAIN_CONTENT_SOURCES: tuple[tuple[str, str], ...] = (
    ("bazi_transit_plain", BAZI_TRANSIT_PLAIN_SOURCE),
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

#: 合婚一页真正读到的十一张表。单列的理由同 `NAME_CONTENT_SOURCES`：`bazi_dimensions`
#: （六维详批）在本页既没参与计算也没有呈现，列进来等于让合婚声称引了它没引的书；
#: 而 `bazi_wangshuai` / `bazi_geju` / `bazi_tiaohou` 三张看着像"本命盘的事"，
#: 其实两造的喜忌集正是由它们合并出来的（互补图与宜忌的唯一输入），一张都删不得。
#: 岁运那两张由轻量轴读：轴行一分一档与 `/bazi/liuyue` 的年表同一把尺（合婚 spec §10.5）。
#: 第十一行 `hehun_plain` 是**白话转述表**，不是判语来源：前十张给的是计分与盘理的依据
#: （古籍书名或模型参数口径），它给的是本页 `plain` 三节逐字印进响应的档位句、同频句与
#: 三句框架——端点不列它，`provenance.tables` 就漏掉了真正被读进页面文案的那张表
#: （AGENTS §7「读了就列」；它自撰、不引古籍，凭据由 `HEHUN_PLAIN_SOURCE` 自己说清）。
#: 条数复测：`cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "from app.content import HEHUN_CONTENT_SOURCES; print(len(HEHUN_CONTENT_SOURCES))"` → 11。
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
    ("hehun_plain", HEHUN_PLAIN_SOURCE),
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

#: 紫微斗数一页真正读到的两张表：十四主星与乙级星之五行/星系、生年干四化、
#: 命主身主、纳音五行局与十二宫序，以及逐条转述它们的白话表。单列理由同
#: `NAME_CONTENT_SOURCES`：混进 `CONTENT_SOURCES` 等于让八字声称引了它没用过的斗数安星表。
ZIWEI_CONTENT_SOURCES: tuple[tuple[str, str], ...] = (
    ("ziwei", ZIWEI_SOURCE),
    ("ziwei_plain", ZIWEI_PLAIN_SOURCE),
)

#: 西洋本命一页真正读到的三张白话表：落座与落宫（`western_plain_placement`）、轴/交点/宫题/
#: 元素/形态/逆行（`WESTERN_SMALL_READINGS` 住在 `western_plain`）、相位（`western_plain_aspect`）。
#: 三行共用同一个 `WESTERN_PLAIN_SOURCE`：一张自撰表的三个分册，同一条凭据（塔罗那张
#: `TAROT_CONTENT_SOURCES` 用两条凭据是因为其中一行是**另一件东西**——一张现代译表，不是同一张表的分册）。
#: **不列 `western` 本体**：这一家没有 `content/western.py`，权威数据源是 pyswisseph（AGENTS §2/§6），
#: 列它等于凭空造一张不存在的表。单列不进 `CONTENT_SOURCES` 的理由同 `ZIWEI_CONTENT_SOURCES`。
#: 条数复测：`cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c
#: "from app.content import WESTERN_CONTENT_SOURCES; print(len(WESTERN_CONTENT_SOURCES))"` → 3。
WESTERN_CONTENT_SOURCES: tuple[tuple[str, str], ...] = (
    ("western_plain", WESTERN_PLAIN_SOURCE),
    ("western_plain_placement", WESTERN_PLAIN_SOURCE),
    ("western_plain_aspect", WESTERN_PLAIN_SOURCE),
)

#: 奇门遁甲一页真正读到的两张表：安盘正表（洛书九宫、九星八门八神、三奇六仪甲遁、
#: 阳遁/阴遁 节气局数表、三元符头与旬空驿马），以及逐条转述它们的白话表。单列理由同
#: `ZIWEI_CONTENT_SOURCES`。
QIMEN_CONTENT_SOURCES: tuple[tuple[str, str], ...] = (
    ("qimen", QIMEN_SOURCE),
    ("qimen_plain", QIMEN_PLAIN_SOURCE),
)

#: 雷诺曼一页真正读到的两张表：36 张牌义（编号、中英文名、吉凶极性、关键词、
#: 组合直读之名词核心与修饰词）与五种牌阵位次，以及逐条转述它们的白话表。单列理由同
#: `ZIWEI_CONTENT_SOURCES`。
LENORMAND_CONTENT_SOURCES: tuple[tuple[str, str], ...] = (
    ("lenormand", LENORMAND_SOURCE),
    ("lenormand_plain", LENORMAND_PLAIN_SOURCE),
)

#: 塔罗一页真正读到的四张表：22 张大牌、56 张 minors、装配件（6 阵 29 位次）、529 条关键词
#: 中译。单列理由同 `ZIWEI_CONTENT_SOURCES`：混进 `CONTENT_SOURCES` 等于让八字声称引了它
#: 没用过的牌库。`content/tarot_cards.py` **不列**：它带的是 dataclass、两个组装工厂和几张
#: 查表字典（`SUIT_ELEMENT`、`COURT_RANKS` 这类 `element`/`rank` 取值确实进了响应），但那是
#: 结构件不是文案——它没有一行是印进页面的句子，列它等于把「读了」稀释成「import 过」
#: （AGENTS.md §7「读了就列」说的是读文案，不是碰字典）。
#: 前三行共用 `TAROT_SOURCE`、第四行单独用 `TAROT_KEYWORDS_ZH_SOURCE`：一张自持的现代译表
#: 与公共领域的牌义不同凭据，抄成同一串就是让译表冒充原典（卢恩 spec 决策 24 的反向运用）。
#: 条数复测：`cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c
#: "from app.content import TAROT_CONTENT_SOURCES; print(len(TAROT_CONTENT_SOURCES))"` → 4。
TAROT_CONTENT_SOURCES: tuple[tuple[str, str], ...] = (
    ("tarot_major", TAROT_SOURCE),
    ("tarot_minor", TAROT_SOURCE),
    ("tarot_deck", TAROT_SOURCE),
    ("tarot_keywords_zh", TAROT_KEYWORDS_ZH_SOURCE),
)

#: 卡巴拉一页真正读到的两张表：十原质（三柱四界、行星守护、王徽色、大天使与神名）、
#: 隐藏的 Daath 与 22 路径（希伯来字母 / 塔罗大阿卡纳 / 行星星座元素）之黄金黎明对应，
#: 以及逐条转述它们的白话表。单列理由同 `ZIWEI_CONTENT_SOURCES`。
KABBALAH_CONTENT_SOURCES: tuple[tuple[str, str], ...] = (
    ("kabbalah", KABBALAH_SOURCE),
    ("kabbalah_plain", KABBALAH_PLAIN_SOURCE),
)

#: 吠陀占星一页真正读到的三张表：恒星黄道十二星座、九曜（Navagraha）、27 宿
#: （Nakshatra，各含守护曜与主神）与 Vimshottari 大运值年序；外加自撰白话表的两半
#: （落座/宿/主事星与落宫分住 `vedic_plain`、`vedic_plain_gruha`，同一张自撰表的两半，
#: 与行运页的 `TRANSIT_OVERLAY_CONTENT_SOURCES` 同形）。单列理由同
#: `ZIWEI_CONTENT_SOURCES`：主八字盘不引用它们。
VEDIC_CONTENT_SOURCES: tuple[tuple[str, str], ...] = (
    ("vedic", VEDIC_SOURCE),
    ("vedic_plain", VEDIC_PLAIN_SOURCE),
    ("vedic_plain_gruha", VEDIC_PLAIN_SOURCE),
)

#: 西洋合盘一页真正读到的三张表：相契度赋分权重（相位基准分、核心羁绊强调、
#: 容许度衰减与四档分界）、逐条转述它们的白话表，以及 `aspects_nature`——五类主要相位
#: →（性质键，中文档名）的三档归类表，Plan G T1 把两个引擎里各一份的 `_NATURE` 副本搬成
#: content 表，它今天填着合盘每一条相位的 `nature`/`nature_zh`。读者只有两家（复测：
#: `cd backend && grep -rn "ASPECT_NATURE" app/engines/`），所以吠陀页的清单里不许出现它；
#: 行运页自己那份是三行的 `TRANSIT_OVERLAY_CONTENT_SOURCES`（`:59`），与合盘这份分开维护。
#: 单列理由同 `ZIWEI_CONTENT_SOURCES`：主八字盘不引用它们，且赋分是本系统模型参数而非古籍语料，
#: 出处串自己说清了这一点。
SYNASTRY_CONTENT_SOURCES: tuple[tuple[str, str], ...] = (
    ("synastry_scoring", SYNASTRY_SOURCE),
    ("synastry_plain", SYNASTRY_PLAIN_SOURCE),
    ("aspects_nature", ASPECT_NATURE_SOURCE),
)

#: 梅花一页真正读到的五张表。单列理由同 `NAME_CONTENT_SOURCES`：混进 `CONTENT_SOURCES`
#: 等于让八字声称引了它没用过的周易表。三张 `zhouyi_*` 是梅花**真的**在引——卦名卦画
#: （`zhouyi_hexagrams`）、邵雍先天数 → 卦键那一份 lookup（`zhouyi_trigrams` 的
#: `TRIGRAM_BY_MEIHUA`，调用点 `engines/meihua.py:226`；该表出处串自述的是「先天卦序」，
#: 说的是同一列 `meihua_number`，两个词不许混着改），页面上那句卦辞（`zhouyi_text`）。
#: `zhouyi_text` 是聚合面，它印进响应的卦辞正文住在 `content/zhouyi_guaci.py` 的 `GUA_CI`
#: （复测：`cd backend && grep -n "GUA_CI" app/content/zhouyi_text.py`）。
#: 不列的两张各有其因：`content/wuxing` 不进 tables 是一条**只管文案表**的口径——它自维护的
#: 五行生克叙述（哪一生哪一克那一段话）不转述进任何响应，故不列（同 `CONTENT_SOURCES` 今天
#: 也不列 wuxing 的既有口径）。这条口径只管文案、不管字段取值：地支本气 `zhi_element` 就取自
#: `ZHI_ELEMENT`（复测：`cd backend && grep -n "zhi_element" app/schemas/bazi.py` 命中字段声明，
#: 填装在 `app/engines/bazi_pillar.py`），那是**字段的五行名**而非生克文案，与「文案不进响应」不冲突；
#: 旧注说成「其文字不进任何响应」是说过头了，Plan E 终审改口。`lunar-python` 定农历数与月建，
#: 它供给的是**计算事实**，没有被转述进响应的文案，故不进 tables 也不是漏账——它在
#: `provenance.engine` 那一格按八字 `engines/bazi.py:352` 的短值口径认账。分界画在文案上、
#: 不画在版本上：库的文案进了响应就得进表打版，本文件 `ALMANAC_CONTENT_SOURCES` 列通书
#: 宜忌、`ALMANAC_CONTENT_VERSION` 给 lunar-python 打版，正是这一条的先例。
#: 条数复测：`cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "from app.content import MEIHUA_CONTENT_SOURCES; print(len(MEIHUA_CONTENT_SOURCES))"` → 5。
MEIHUA_CONTENT_SOURCES: tuple[tuple[str, str], ...] = (
    ("meihua", MEIHUA_SOURCE),
    ("meihua_plain", MEIHUA_PLAIN_SOURCE),
    ("zhouyi_trigrams", ZHOUYI_TRIGRAMS_SOURCE),
    ("zhouyi_hexagrams", ZHOUYI_HEXAGRAMS_SOURCE),
    ("zhouyi_text", ZHOUYI_SOURCE),
)

#: 周易一页真正读到的五张表：三张《周易》通行本（八卦、六十四卦卦序卦画、卦爻辞正文）、
#: 一张京房纳甲与六神起例，以及逐条转述它们的今译表。单列理由同 `ZIWEI_CONTENT_SOURCES`：
#: 主八字盘不引用它们。三张 `zhouyi_*` 的出处串与 `MEIHUA_CONTENT_SOURCES` 共用同一份常量
#: （丁组计划偏差表第 5 行）。
#: **不列 `content/wuxing`**：全站口径是「它自维护的五行生克**文案**不转述进响应，故不进 tables」
#: （本文件 `MEIHUA_CONTENT_SOURCES` 注里写的同一条，八字同样不列，复测：
#: `cd backend && grep -n "wuxing" app/content/__init__.py` → 只命中注释行，一张清单都没列它）。
#: 这条只管文案表、不管字段取值——五行名确实进响应（复测：`cd backend && grep -n "zhi_element" app/schemas/bazi.py`
#: 命中字段声明），旧注「其文字不进任何响应」说过头了，Plan E 终审改口为「生克文案不进响应」。
#: 张力写在明处：周易这一侧每爻的 `branch_element` 确实是 `ZHI_ELEMENT` 的字面
#: （`engines/zhouyi.py:224`，复测：`cd backend && grep -n "branch_element=ZHI_ELEMENT" app/engines/zhouyi.py` → 224），
#: 丁组 spec §5 因此要求列它——本计划不因一个系统破全站口径。
#: 代价：若日后裁定要列，周易与八字两家一起动，不在本期（偏差表第 1 行）。
#: 条数复测：`cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "from app.content import ZHOUYI_CONTENT_SOURCES; print(len(ZHOUYI_CONTENT_SOURCES))"` → 5。
ZHOUYI_CONTENT_SOURCES: tuple[tuple[str, str], ...] = (
    ("zhouyi_trigrams", ZHOUYI_TRIGRAMS_SOURCE),
    ("zhouyi_hexagrams", ZHOUYI_HEXAGRAMS_SOURCE),
    ("zhouyi_najia", ZHOUYI_NAJIA_SOURCE),
    ("zhouyi_text", ZHOUYI_SOURCE),
    ("zhouyi_plain", ZHOUYI_PLAIN_SOURCE),
)
