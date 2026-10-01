"""卡巴拉白话转述表：工厂看不到的那四件事（多系统白话 spec §7、§11）。

工厂管措辞四条与 `set(entries) == universe()`；这里只钉它结构上够不着的：
① 登记身份（R24：字典字面量同名两行时 Python 静默留后一行，前一张表就此掉出机检闸外）；
② `universe()` 的三张源表构成（工厂只验证它可复现且非空，验不出「Daath 只算一次」）；
③ 无小节这一形状本身——`openers == {}` 由工厂的 `SECTIONLESS` 钉，这里钉「33 条确实
都能被取到」，因为卡巴拉不走 `compose()`，工厂的键集合闸绿不等于输出绿；
④ 「不新增判断」的机检半边（G3 的条目正文那一半）：工厂四条看的是长度/含「你」/句号数/
拼接残留，一句带「宜」的释义完全可能四条全过，所以取向词得由本文件按整表扫（见
`test_plain_entries_add_no_orientation_the_source_table_lacks`）。
"""

from app.content.kabbalah import DAATH, PATHS, SEPHIROTH
from app.content.kabbalah_plain import KABBALAH_PLAIN_SOURCE, KABBALAH_READINGS
from app.engines.plain_compose import reading
from app.engines.plain_corpora import KABBALAH, PLAIN_CORPORA

#: 白话正文的结论词口径：四字（宜/忌/吉/凶），沿用合盘那家已经在用的那条
#: （`tests/golden/test_synastry_golden.py::test_aspect_frames_carry_no_verdict_words`）。
#: 不用灵数那张六字表（`tests/test_numerology.py::ADVICE_TOKENS` 多「需」「应」两字）：
#: 本语料会误红一处——`sephirah-5` 的「以及守住那条界线所需的那份勇气」里「需」是名词性
#: 用法，不是「你需要做什么」。抹词形表在这里只有一条，为它立第二套口径不如按四字扫。
#: 复测（2026-10-01 实跑）：`cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "
#: from app.content.kabbalah_plain import KABBALAH_READINGS as R
#: print([(k, t) for k, v in sorted(R.items()) for t in ('宜','忌','需','应','吉','凶') if t in v])
#: print([(k, t) for k, v in sorted(R.items()) for t in ('宜','忌','吉','凶') if t in v])"`
#: → `[('sephirah-5', '需')]` 与 `[]`。
VERDICT_WORDS: tuple[str, ...] = ("宜", "忌", "吉", "凶")

#: 源表按六字扫（它连「所需」这类名词用法都没有）。扫的是 `.meaning` 一个字段，
#: 不扫 `letter_zh`/`name_zh`/`keywords`：路径 13 的字母音译是「吉梅尔」，专名里的字不是判语。
#: 复测：`cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "
#: from app.content.kabbalah import SEPHIROTH, DAATH, PATHS
#: print([(n.id, w) for n in [*SEPHIROTH, DAATH, *PATHS] for w in ('宜','忌','需','应','吉','凶') if w in n.meaning])"` → `[]`。
SOURCE_ADVICE_WORDS: tuple[str, ...] = ("宜", "忌", "需", "应", "吉", "凶")


def test_plain_entries_add_no_orientation_the_source_table_lacks() -> None:
    """两头同扫：源表 33 句 `.meaning` 六字全空，白话 33 句四字全空——白话层不许有源表没有的取向。

    `test_kabbalah_corpus_is_the_row_the_factory_iterates` 里那条 `closers is None` 只钉得住
    「不补档位收尾句」；有人往某一格正文里塞一句「宜静待与磨合」，工厂四条与 `closers`
    两不犯着，全绿上线。红的时候报的是 `(表, 键, 词)`：源表那一路红意味着语料自己开始判
    吉凶，本层「照搬源表意象」那句自述（`content/kabbalah_plain.py` 头注）就得重看；
    白话那一路红意味着转述加出了原表没有的严重程度，正是这一家不许的那件事。
    """
    for node in [*SEPHIROTH, DAATH, *PATHS]:
        for word in SOURCE_ADVICE_WORDS:
            assert word not in node.meaning, ("content/kabbalah.py", node.id, "meaning", word)
    for key, text in sorted(KABBALAH_READINGS.items()):
        for word in VERDICT_WORDS:
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
    assert KABBALAH.universe() == (
        {f"sephirah-{s.number}" for s in SEPHIROTH}
        | {"daath"}
        | {f"path-{p.number}" for p in PATHS}
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
