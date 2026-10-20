"""白话措辞机检禁字表的唯一正主（第一期 spec §3 第 2 条）。

为什么住测试侧而不是 `app/`：禁哪几个字是**评审口径**，不是产品行为——生产代码从不检查
措辞，措辞的守门人是这批测试。把表搬进 `app/` 就是让生产代码认识自己的测试，分层立刻反了
（AGENTS.md §1）。本模块也不是测试模块：文件名不带 `test_` 前缀，pytest 不收集它；消费方以
`from tests.plain_wording import …` 引（同 `tests/content/name_radical_fixture.py` 的引法，
无需 `__init__.py`，也无需动 `conftest.py`）。

复测两个口径仍各在其位（条数随登记表增长，数以命令输出为准，本注释不钉数）：`cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m pytest tests/test_plain_corpora.py -o addopts=""` 与 `cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m pytest tests/content/test_bazi_plain_corpus.py -o addopts=""`。建议词/结论词第三口径的复测是本模块自身的闸内自测——文件名不带 `test_` 前缀，全量跑不收集，须显式点名的路子同 `tests/content/name_radical_fixture.py`：`cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m pytest tests/plain_wording.py -o addopts=""`。
"""

import re

from app.engines.plain_compose import is_slot_key

#: 机检禁字集逐字取自第一期 spec §3 第 2 条：「（《」与「』」是出处引用标记，「；」是
#: 拼接残留。「则」「之」同条只列为**风格**要求（白话不得有文言句式），不进机检——单字黑名单会连带打死
#: 「规则」「之前」，红得一派无辜（第一期控制器裁定 R3，本表沿用同一口径）。
FORBIDDEN = ("；", "（《", "』")

#: 槽位词条是名词短语，不许自带结论（spec §5 规则 5：判断只能来自词条自身之外的
#: 档位收尾句，而槽位词条不参与收尾）。「。」同禁：槽位文本是被嵌在句子中间的，
#: 自带句号会把一句白话劈成两句，正好破坏装配器唯一的标点契约。
#: 槽位口径由参数化工厂 `tests/test_plain_corpora.py` 自己用；段落框架句只走全句口径
#: 那一半，所以下游只引 `FORBIDDEN`。
SLOT_FORBIDDEN = (*FORBIDDEN, "吉", "凶", "宜", "忌", "你", "{", "}", "\n", "。")

#: 结论词/建议词六字表（唯一正主；Plan B 终审随附债之一，R26 的同一口径）。
#: 「需」「应」有名词性用法（「所需的那份勇气」「适应变动」），所以扫描前先抹
#: `NON_ADVICE_FORMS` 里**具名的词形**而不是抹单字——抹单字会连真建议一起放过
#: （第一期控制器裁定 R3 的同一条理由，Plan B 的 R27 把它写成了形状）。
ADVICE_TOKENS: tuple[str, ...] = ("宜", "忌", "需", "应", "吉", "凶")

#: 四字窄口径：去掉「需」「应」这两个名词性最强的字。给「明知上游没有名词用法、
#: 却不想为一条句子放宽整张表」的系统用（卡巴拉 `sephirah-5`；合盘的框架句）。
VERDICT_TOKENS: tuple[str, ...] = ("宜", "忌", "吉", "凶")

#: 必须具名才能抹的词形。新抹一个词形要在用它的系统里写一句理由。
#: `("对应","反应")` 两条来自数字命理（数2 essence、数5 talent）；
#: 「适应」是 Task 1 把整表扫扩到 `keywords` 时新撞上的数5 关键词。
#: 「对应」的第二个消费者是奇门九星：`nature` 的前半就是一个星名
#: （「天蓬·贪狼」），转述只能写成「在表里对应贪狼」，命中 9 条（复测见
#: `tests/content/test_qimen_plain_corpus.py::test_no_retelling_borrows_the_source_tables_orientation_word`）。
NON_ADVICE_FORMS: tuple[str, ...] = ("对应", "反应", "适应")

#: 按系统分域的**具名非决策词**：完整的专名撞上 G36 的决策词时，先抹掉这个专名再跑禁串。
#: 今天的唯一成员是吠陀二十七宿里的「百药」（`app/content/vedic.py` 的 `NAKSHATRAS`，
#: `Shatabhisha`）——它是宿名，不是药材或决策。掩码的边界刻意写成两条：
#: ①只抹**完整词形**（裸「药」仍红；把「百药」拆开写仍红）；
#: ②只对列出的系统生效（同一个串在别的系统下仍红）。三条都由本节的本地自测钉住。
NON_DECISION_FORMS: dict[str, tuple[str, ...]] = {"vedic": ("百药",)}


def mask_non_decision_forms(system: str, text: str) -> str:
    """抹掉该系统的具名非决策词，返回可跑禁串的文本。"""
    for form in NON_DECISION_FORMS.get(system, ()):
        text = text.replace(form, "")
    return text

#: 戊组三系统（西洋本命 / 行运 / 吠陀）的时态门：本期出处口径是**平台自撰**（spec 裁定 R46），
#: 没有古籍可挡在句子前面，所以「这句在替用户预告事件」这一类必须由机器兜住最刺眼的一段。
#: 用户 2026-10-04 的第 4 条裁定把它写成硬要求（spec §7 G31）。清单**可增不可减**，减要走裁定。
#: 甲–丁不追改：它们的判语是转述已有出处，句式里本来就没有未来时。
#: 「该」是 Plan F 的 T2 评审轮增补的第十七串（清单可增不可减）：六字表抓不到裸用的
#: 「该」（「这事该不该由你定」既无「你该」也无「该做」），而它同样是替用户定。
#: 判据：往任一条 western 句子里塞一个「该」，`tests/content/test_western_plain_corpus.py` 即红；
#: 今天 72 条落座句与 10 条开篇句命中为零（塞进语料前先跑这条，别改本表）。
PREDICTION_FORBIDDEN: tuple[str, ...] = (
    "将会", "一定会", "必然会", "注定", "保证", "明年", "下个月",
    "你会", "你将", "你要", "你该", "建议你", "记得", "务必", "千万别", "一定要", "该",
)

#: 戊组决策名词门（spec §7 点名的雷区：健康＝第六宫／处女座／土星—月亮一线，投资＝第十一宫／
#: 木星，法律＝第七宫）。footer 免责声明承诺了「不是建议」，语料就不许给具体决策名词。
#: 这八串是把「等」写成清单（Plan F 偏差表第 8 行）：不写死就会在新句子里漏进「手术」「投资」
#: 「吃了一片药」这类形状，而 542 条读不完。
WU_DECISION_FORBIDDEN: tuple[str, ...] = ("就诊", "体检", "理财", "买房", "诉讼", "手术", "投资", "药")

#: 上面两组只对这三家生效。复测：`cd backend && grep -n "PREDICTION_GATED_SYSTEMS" tests/plain_wording.py`。
PREDICTION_GATED_SYSTEMS: frozenset[str] = frozenset({"western", "transit", "vedic"})

#: 批次二 spec §4.2 的账本词面清单（合婚四档 + 六宜忌组 + 七条规则短名，跨两份语料测与三份
#: golden 共用）。后五串出自 `content/bazi_transit_rules.TRANSIT_RULES` 的 `label`，与岁运三片同源，
#: 所以这张表住在这里而不是某个系统的语料测里——清单定义在测模块里再被另一个测模块 import，
#: 那个文件会在两个模块名下各导一次（`tests/test_plain_corpora.py:71-82` 记的坑）。
#: **只准增不准删**，删要走裁定——每加一枚就是替某张表挡住一次「把账本短名念进散文」。
LEDGER_WORDS: tuple[str, ...] = (
    "天作之合", "相得益彰", "中和可处", "欠和宜慎",
    "同宜", "乾独宜", "坤独宜", "同忌", "乾独忌", "坤独忌",
    "我忌彼旺", "我忌彼弱", "半合忌", "三合成忌", "三会忌", "运干入忌", "运支主气入忌",
)

#: 取向词门（批次二 spec §8 第 5 条，本批**自加**、不是工厂门；口径同
#: `tests/content/test_kabbalah_plain_corpus.py` 的 `PLAIN_VERDICT_WORDS` 那六串）。
#: 它们不在 `ADVICE_TOKENS` 里，所以六字表放过、这条拦住：白话只报账本形状，不给盘面定顺逆。
ORIENTATION_WORDS: tuple[str, ...] = ("顺势", "逆势", "有利", "不利", "好运", "厄运")


def advice_hits(
    text: str,
    *,
    tokens: tuple[str, ...] = ADVICE_TOKENS,
    masks: tuple[str, ...] = NON_ADVICE_FORMS,
) -> list[str]:
    """`text` 里真正下结论或给建议的字面量；`masks` 里的具名词形不算命中。"""
    masked = text
    for form in masks:
        masked = masked.replace(form, "")
    return [token for token in tokens if token in masked]


_PLACEHOLDER = re.compile(r"\{[a-z][a-z0-9_]*\}")


def frame_slots(frame: str) -> list[str]:
    """框架句声明的槽位名，序即出现序。

    与本文件既有的 `_PLACEHOLDER`（同一条正则，条目门剥占位符用的）必须认同一个形状：
    分成两份写迟早分家——一份放宽了花括号那段的字符集，另一份就看不见新形状的槽，
    `overview()` 在页面上 KeyError 而测里全绿。那条正则**不带捕获组**（它只管抹掉占位符），
    所以这里剥壳取名字而不是 `group(1)`。
    `tests/content/test_hehun_plain_corpus.py` 与 `test_bazi_transit_plain_corpus.py` 都 import 这一个。
    """
    return [match.group(0).strip("{}") for match in _PLACEHOLDER.finditer(frame)]


def wording_violations(corpus, key: str) -> list[str]:
    """一条白话条目的措辞违例清单，空表即合规；判定次序：先禁字，再按槽位/整句分流。

    返回违例而不是直接 assert，是为了让参数化用例与 `tests/test_plain_corpora.py` 末尾的槽位自测走同一份代码
    （R21）：口径分流那条分支在生产登记表上今天无人触发，把分支体抄第二遍来「补覆盖」
    只会多出一个会漂的副本。
    """
    text = corpus.entries[key]
    violations: list[str] = []
    for token in FORBIDDEN:
        if token in text:
            violations.append(f"FORBIDDEN 禁字「{token}」")
    if corpus.system in PREDICTION_GATED_SYSTEMS:
        gated_text = mask_non_decision_forms(corpus.system, text)
        for token in PREDICTION_FORBIDDEN + WU_DECISION_FORBIDDEN:
            if token in gated_text:
                violations.append(f"戊组禁字「{token}」")
    if is_slot_key(corpus, key):
        if not text.strip():
            violations.append("槽位词条非空契约破")
        for token in SLOT_FORBIDDEN:
            if token in text:
                violations.append(f"SLOT_FORBIDDEN 禁字「{token}」")
        if len(text) > 20:
            violations.append(f"槽位词条 {len(text)} 字，超过 20 字上限")
        return violations
    # 条目可以合法携带 `{slot}`（T6 的 5 条相位框架句就带 {a}/{b}），所以长度按剥掉占位符的
    # 正体算，而标点契约按原文算。
    body = _PLACEHOLDER.sub("", text)
    if len(body) < 40:
        violations.append(f"剥掉占位符后正体 {len(body)} 字，不足 40 字")
    if not (text.endswith("。") and text.count("。") == 1):
        violations.append("整句须以唯一一个「。」收尾")
    if "你" not in text:
        violations.append("整句缺「你」")
    return violations


def frame_violations(system: str, text: str) -> list[str]:
    """框架句（小节开篇句与档位收尾句）的违例清单，空表即合规。

    四项口径与 `tests/test_plain_corpora.py::test_frame_sentences_meet_the_same_contract` 逐字同值
    （≥20 字 / 恰一「。」 / 含「你」/ `FORBIDDEN`），本函数是那份断言的**唯一正主**，工厂改为调用它。
    抽成可调用物的理由有两条，都不是美学：①本期新增门 `PREDICTION_FORBIDDEN` 与
    `WU_DECISION_FORBIDDEN` 也要管框架句，抄第二遍就会有一处忘记加；②`WESTERN` 在 T1-T14
    **刻意不登记**（Plan F 全局约束「批次期定义而不登记」，登记行归 T15，2026-10-06 已补），
    那十四批里工厂的参数化用例看不到它，本地门
    必须能吃同一份口径——这是 Plan E 偏差 4 把 `wording_violations` 移到本模块的同一条路子。

    40 字下限**不适用**：开篇句是引导句不是判语，把整句口径套上去是假红（工厂 docstring 里
    R6 那条「两种口径各在其位」的同一理由）。`system` 是入参而不是从 corpus 取，因为框架句
    在装配前就要能被判。
    """
    violations: list[str] = []
    for token in FORBIDDEN:
        if token in text:
            violations.append(f"FORBIDDEN 禁字「{token}」")
    if system in PREDICTION_GATED_SYSTEMS:
        gated_text = mask_non_decision_forms(system, text)
        for token in PREDICTION_FORBIDDEN + WU_DECISION_FORBIDDEN:
            if token in gated_text:
                violations.append(f"戊组禁字「{token}」")
    if len(text) < 20:
        violations.append(f"框架句 {len(text)} 字，不足 20 字")
    if not (text.endswith("。") and text.count("。") == 1):
        violations.append("框架句须以唯一一个「。」收尾")
    if "你" not in text:
        violations.append("框架句缺「你」")
    return violations


def test_non_decision_forms_are_scoped_and_narrow() -> None:
    assert mask_non_decision_forms("vedic", "百药这一宿") == "这一宿"
    assert mask_non_decision_forms("western", "百药这一宿") == "百药这一宿"
    assert mask_non_decision_forms("vedic", "百药与药") == "与药"


def test_advice_hits_masks_named_word_forms() -> None:
    assert advice_hits("对应之数与反应快都不算。") == []
    assert advice_hits("适应变动不算。") == []
    assert advice_hits("适应变动不算，应当算。") == ["应"]
    assert advice_hits("化忌是四化名相本身。", masks=("化禄", "化权", "化科", "化忌")) == []
    assert advice_hits("此格忌反复争执。") == ["忌"]
    assert set(VERDICT_TOKENS) < set(ADVICE_TOKENS)


def test_frame_slots_reads_exactly_the_entry_gates_placeholder() -> None:
    """大括号里带大写的那一槽**不匹配**——这就是「两份正则迟早分家」的现场证据。"""
    assert frame_slots("甲{x}乙{y_1}丙{A}") == ["x", "y_1"]
