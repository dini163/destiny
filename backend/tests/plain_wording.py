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


def wording_violations(corpus, key: str) -> list[str]:
    """一条白话条目的措辞违例清单，空表即合规；判定次序：先禁字，再按槽位/整句分流。

    返回违例而不是直接 assert，是为了让参数化用例与本文件末尾的槽位自测走同一份代码
    （R21）：口径分流那条分支在生产登记表上今天无人触发，把分支体抄第二遍来「补覆盖」
    只会多出一个会漂的副本。
    """
    text = corpus.entries[key]
    violations: list[str] = []
    for token in FORBIDDEN:
        if token in text:
            violations.append(f"FORBIDDEN 禁字「{token}」")
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


def test_advice_hits_masks_named_word_forms() -> None:
    assert advice_hits("对应之数与反应快都不算。") == []
    assert advice_hits("适应变动不算。") == []
    assert advice_hits("适应变动不算，应当算。") == ["应"]
    assert advice_hits("化忌是四化名相本身。", masks=("化禄", "化权", "化科", "化忌")) == []
    assert advice_hits("此格忌反复争执。") == ["忌"]
    assert set(VERDICT_TOKENS) < set(ADVICE_TOKENS)
