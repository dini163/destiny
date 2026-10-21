"""卡巴拉白话转述表：工厂看不到的那七件事（多系统白话 spec §7、§11 + 批次二 J-T6）。

工厂管措辞四条与 `set(entries) == universe()`；这里只钉它结构上够不着的：
① 登记身份（R24：字典字面量同名两行时 Python 静默留后一行，前一张表就此掉出机检闸外）；
② `universe()` 的三张源表构成（工厂只验证它可复现且非空，验不出「Daath 只算一次」）；
③ 无小节这一形状本身——`openers == {}` 由工厂的 `SECTIONLESS` 钉，这里钉「36 条确实
都能被取到」，因为卡巴拉不走 `compose()`，工厂的键集合闸绿不等于输出绿；
④ 「不新增判断」的机检半边（G3 的条目正文那一半）：工厂四条看的是长度/含「你」/句号数/
拼接残留，一句带「宜」的释义完全可能四条全过，所以取向词得由本文件按整表扫（见
`test_plain_entries_add_no_orientation_the_source_table_lacks`）；
⑤ 三条整树总论过同一套本地门（J-T6）：取向词、四字结论词、工厂四条，一条不许因为
「它不是节点释义」而少跑一遍；
⑥ 总论三键三名的**字面**钉：装配与 golden 都拿这两个常量自己对 zip 自己，常量认不出
自己的字面，互换两名两边照样绿；
⑦ 总论不许撞节点文案：`set(entries) == universe()` 与措辞四条都看不见「把某一格的释义
搬过来说第二遍」，本文件用最长连续相同段这把尺量它（阈值 `_ECHO_RUN`）。
"""

import difflib

from app.content.kabbalah import DAATH, PATHS, SEPHIROTH
from app.content.kabbalah_plain import (
    KABBALAH_OVERVIEW_KEYS,
    KABBALAH_OVERVIEW_TITLES,
    KABBALAH_PLAIN_SOURCE,
    KABBALAH_READINGS,
)
from app.engines.plain_compose import reading
from app.engines.plain_corpora import KABBALAH, PLAIN_CORPORA
from tests.plain_wording import (
    ADVICE_TOKENS,
    ORIENTATION_WORDS,
    VERDICT_TOKENS as PLAIN_VERDICT_WORDS,
    advice_hits,
    wording_violations,
)

#: 撞句阈值：总论与任一节点文案（原表 `.meaning` 或 33 句白话）之间允许的最长**连续相同**串。
#: 定尺方法（不是拍的）：三条总论与 66 份节点文案两两比最长公共子串，2026-10-21 实测最大 5
#: （「读到的是」这一类连接段），阈值取实测值 +1 = 6，即「连续六字相同」才算撞句。
#: 复测（与本文件 `_longest_shared_run` 同一个算法，两处不成两口径）：
#: `cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "
#: import difflib
#: from app.content.kabbalah import SEPHIROTH, DAATH, PATHS
#: from app.content.kabbalah_plain import KABBALAH_READINGS as R, KABBALAH_OVERVIEW_KEYS as K
#: run=lambda a,b: difflib.SequenceMatcher(None,a,b,autojunk=False).find_longest_match(0,len(a),0,len(b)).size
#: node=[n.meaning for n in (*SEPHIROTH, DAATH, *PATHS)]+[v for k,v in R.items() if k not in K]
#: print(max(run(R[k],t) for k in K for t in node))"` → `5`。
_ECHO_RUN = 6

#: 白话正文的结论词口径：四字（宜/忌/吉/凶），即 `tests/plain_wording.py::VERDICT_TOKENS`
#: 的导入别名（沿用合盘那家已经在用的那条，`tests/golden/test_synastry_golden.py::
#: test_aspect_frames_carry_no_verdict_words`）。不用那张六字表（`ADVICE_TOKENS` 多「需」
#: 「应」两字）：本语料会误红一处——`sephirah-5` 的「以及守住那条界线所需的那份勇气」里
#: 「需」是名词性用法，不是「你需要做什么」。抹词形表在这里只有一条，为它立第二套口径
#: 不如按四字扫。
#: 复测（2026-10-01 首跑；2026-10-21 三条整树总论落地后复跑，两串输出未变）：
#: `cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "
#: from app.content.kabbalah_plain import KABBALAH_READINGS as R
#: print([(k, t) for k, v in sorted(R.items()) for t in ('宜','忌','需','应','吉','凶') if t in v])
#: print([(k, t) for k, v in sorted(R.items()) for t in ('宜','忌','吉','凶') if t in v])"`
#: → `[('sephirah-5', '需')]` 与 `[]`。

#: 源表按六字（`ADVICE_TOKENS`）扫（它连「所需」这类名词用法都没有）。扫的是 `.meaning`
#: 一个字段，不扫 `letter_zh`/`name_zh`/`keywords`：路径 13 的字母音译是「吉梅尔」，
#: 专名里的字不是判语。
#: 复测：`cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "
#: from app.content.kabbalah import SEPHIROTH, DAATH, PATHS
#: print([(n.id, w) for n in [*SEPHIROTH, DAATH, *PATHS] for w in ('宜','忌','需','应','吉','凶') if w in n.meaning])"` → `[]`。


def test_plain_entries_add_no_orientation_the_source_table_lacks() -> None:
    """两头同扫：源表 33 句 `.meaning` 六字全空，白话 36 句四字全空——白话层不许有源表没有的取向。

    `test_kabbalah_corpus_is_the_row_the_factory_iterates` 里那条 `closers is None` 只钉得住
    「不补档位收尾句」；有人往某一格正文里塞一句「宜静待与磨合」，工厂四条与 `closers`
    两不犯着，全绿上线。红的时候报的是 `(表, 键, 词)`：源表那一路红意味着语料自己开始判
    吉凶，本层「照搬源表意象」那句自述（`content/kabbalah_plain.py` 头注）就得重看；
    白话那一路红意味着转述加出了原表没有的严重程度，正是这一家不许的那件事。
    """
    for node in [*SEPHIROTH, DAATH, *PATHS]:
        for word in ADVICE_TOKENS:
            assert word not in node.meaning, ("content/kabbalah.py", node.id, "meaning", word)
    for key, text in sorted(KABBALAH_READINGS.items()):
        for word in PLAIN_VERDICT_WORDS:
            assert word not in text, ("kabbalah_plain", key, word)


def test_kabbalah_corpus_is_the_row_the_factory_iterates() -> None:
    assert PLAIN_CORPORA["kabbalah"] is KABBALAH
    # G3：卡巴拉无分数，白话不许补一句总吉凶——工厂今天两种形状都收，只有这条钉着 None。
    # 条目正文那一半（「吉」「宜」混在长句里）归 `test_plain_entries_add_no_orientation_...`。
    assert KABBALAH.closers is None


def test_universe_is_ten_sephiroth_plus_daath_plus_twenty_two_paths() -> None:
    nodes = [*SEPHIROTH, DAATH]
    assert len(nodes) == 11 and len(PATHS) == 22
    # 期望集从源表原始字段独立重建：`_kabbalah_universe()` 抄的是节点的 `.id`，
    # 照抄它的构造式就抓不到 id 格式被改（只抓得到选取变化）。
    # 三条整树总论同理**逐字列名**而不引 `KABBALAH_OVERVIEW_KEYS`：引了常量，这条就退化成
    # 「自己跟自己对账」，改名与漏登记都看不见（同上面那条不引构造式的理由）。
    assert KABBALAH.universe() == (
        {f"sephirah-{s.number}" for s in SEPHIROTH}
        | {"daath"}
        | {f"path-{p.number}" for p in PATHS}
        | {"overview-reading", "overview-pillars", "overview-descent"}
    )
    # Daath 不在 `SEPHIROTH` 里：若有人把它塞进那个元组，键集会重复而条数不变，所以数一下。
    assert len({node.id for node in nodes}) == 11


def test_every_node_id_resolves_through_the_assembler() -> None:
    """逐格走 `reading()`：卡巴拉没有整段装配路径，工厂的键集合闸之外无人验证「取得到」。"""
    for key in sorted(KABBALAH.universe()):
        assert reading(KABBALAH, key) == KABBALAH_READINGS[key]


def test_source_line_is_a_provenance_string_not_a_sentence() -> None:
    """出处串不进工厂遍历（它不是白话句），所以禁字这一半由本文件自守；口径正主在 `tests/plain_wording.py`。"""
    from tests.plain_wording import FORBIDDEN

    assert KABBALAH_PLAIN_SOURCE.startswith("本系统白话转述")
    for token in FORBIDDEN:
        assert token not in KABBALAH_PLAIN_SOURCE, token


def test_the_three_overview_entries_exist_and_clear_the_local_gates() -> None:
    assert len(KABBALAH_READINGS) == 36
    assert set(KABBALAH_OVERVIEW_KEYS) <= set(KABBALAH_READINGS)
    for key in KABBALAH_OVERVIEW_KEYS:
        assert wording_violations(KABBALAH, key) == []
        assert advice_hits(KABBALAH_READINGS[key], tokens=PLAIN_VERDICT_WORDS) == []
        assert [w for w in ORIENTATION_WORDS if w in KABBALAH_READINGS[key]] == []


def test_universe_grew_by_three_and_still_equals_the_entries() -> None:
    assert KABBALAH.universe() == set(KABBALAH_READINGS)
    assert len(KABBALAH.universe()) == 36


def test_the_existing_node_reconciliation_ignores_the_three_overviews() -> None:
    """既有那条「逐条对账源表 .meaning」的测作用域明写节点条目，不被三条总论污染。"""
    node_keys = {str(node.id) for node in [*SEPHIROTH, DAATH, *PATHS]}
    assert node_keys & set(KABBALAH_OVERVIEW_KEYS) == set()


def _longest_shared_run(left: str, right: str) -> int:
    """两串之间最长的**连续相同**段；`autojunk=False` 关掉 difflib 对长序列常见字的降噪。"""
    matcher = difflib.SequenceMatcher(None, left, right, autojunk=False)
    return matcher.find_longest_match(0, len(left), 0, len(right)).size


def test_the_overview_names_are_pinned_by_literal_not_by_the_constant() -> None:
    """三键三名的**字面**钉。装配与 golden 都是拿这两个常量自己对 zip 自己：
    把 `KABBALAH_OVERVIEW_TITLES` 前两项互换，`build_tree()` 跟着一起换，golden 那条
    「节序 == 常量」照样绿——常量认不出自己的字面，所以右边逐字列出，
    理由同 `_kabbalah_universe()` 里「不照抄构造式」那条例外（本文件 :64 起）。"""
    assert KABBALAH_OVERVIEW_KEYS == ("overview-reading", "overview-pillars", "overview-descent")
    assert KABBALAH_OVERVIEW_TITLES == ("全树读法", "三柱与四界", "光流与深渊")


def test_the_three_overviews_are_mutually_distinct() -> None:
    texts = [KABBALAH_READINGS[key] for key in KABBALAH_OVERVIEW_KEYS]
    assert len(set(texts)) == 3


def test_the_three_overviews_echo_neither_a_node_meaning_nor_a_node_retelling() -> None:
    """整树总论只讲「这张图怎么读」，不许把某一格的释义搬来说第二遍。

    工厂的 `set(entries) == universe()` 与措辞四条都看不见撞句：搬过来的句子照样够 40 字、
    照样含「你」、照样只有一个句号。尺子是「与任一节点文案（原表 `.meaning` 或 33 句白话）
    的最长连续相同段 < `_ECHO_RUN`」，阈值来历见文件头的复测串。
    """
    node_texts = [node.meaning for node in [*SEPHIROTH, DAATH, *PATHS]] + [
        text for key, text in KABBALAH_READINGS.items() if key not in set(KABBALAH_OVERVIEW_KEYS)
    ]
    for key in KABBALAH_OVERVIEW_KEYS:
        for node_text in node_texts:
            assert _longest_shared_run(KABBALAH_READINGS[key], node_text) < _ECHO_RUN, (
                key,
                node_text[:16],
            )
