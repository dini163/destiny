"""白话措辞机检禁字表的唯一正主（第一期 spec §3 第 2 条）。

为什么住测试侧而不是 `app/`：禁哪几个字是**评审口径**，不是产品行为——生产代码从不检查
措辞，措辞的守门人是这批测试。把表搬进 `app/` 就是让生产代码认识自己的测试，分层立刻反了
（AGENTS.md §1）。本模块也不是测试模块：文件名不带 `test_` 前缀，pytest 不收集它；消费方以
`from tests.plain_wording import …` 引（同 `tests/content/name_radical_fixture.py` 的引法，
无需 `__init__.py`，也无需动 `conftest.py`）。

复测两个口径仍各在其位（条数随登记表增长，数以命令输出为准，本注释不钉数）：`cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m pytest tests/test_plain_corpora.py -o addopts=""` 与 `cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m pytest tests/content/test_bazi_plain_corpus.py -o addopts=""`。
"""

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
