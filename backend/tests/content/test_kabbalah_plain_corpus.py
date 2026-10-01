"""卡巴拉白话转述表：工厂看不到的那三件事（多系统白话 spec §7、§11）。

工厂管措辞四条与 `set(entries) == universe()`；这里只钉它结构上够不着的：
① 登记身份（R24：字典字面量同名两行时 Python 静默留后一行，前一张表就此掉出机检闸外）；
② `universe()` 的三张源表构成（工厂只验证它可复现且非空，验不出「Daath 只算一次」）；
③ 无小节这一形状本身——`openers == {}` 由工厂的 `SECTIONLESS` 钉，这里钉「33 条确实
都能被取到」，因为卡巴拉不走 `compose()`，工厂的键集合闸绿不等于输出绿。
"""

from app.content.kabbalah import DAATH, PATHS, SEPHIROTH
from app.content.kabbalah_plain import KABBALAH_PLAIN_SOURCE, KABBALAH_READINGS
from app.engines.plain_compose import reading
from app.engines.plain_corpora import KABBALAH, PLAIN_CORPORA


def test_kabbalah_corpus_is_the_row_the_factory_iterates() -> None:
    assert PLAIN_CORPORA["kabbalah"] is KABBALAH


def test_universe_is_ten_sephiroth_plus_daath_plus_twenty_two_paths() -> None:
    nodes = [*SEPHIROTH, DAATH]
    assert len(nodes) == 11 and len(PATHS) == 22
    assert KABBALAH.universe() == {node.id for node in nodes} | {node.id for node in PATHS}
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
