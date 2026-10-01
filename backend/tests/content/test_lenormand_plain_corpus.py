"""雷诺曼白话转述表：工厂看不到的那五件事（多系统白话 spec §8 丙组、§11）。

① 登记身份（R24）；② `universe()` 就是 36 张牌的 `id`，且 id 形状由源表负责
   （本表不另造键——见 `LENORMAND_READINGS` 的头注）；③ 小节覆盖面 `set(openers)
   == set(SPREADS)`（R31：漏一阵就少一句开篇，而那一阵的段仍然完整可读，工厂抓不到）；
④ 转述对账（G14）：`name_zh` 与 `essence` 两个字段逐字进句子——牌义表是策展文本，
   转述只能围着这两个词写，不能改成另一种占卜的说法；⑤ 取向词反向对账（G24）：
   源表自己有 6 处带取向字（4 条 `meaning` + 2 条 `as_modifier`，命中的牌与字段
   就地写在测里），白话一句都不引，同时极性 `polarity` 也不进句子。
"""

from app.content.lenormand import CARDS, POLARITY_LABEL, SPREADS
from app.content.lenormand_plain import (
    LENORMAND_PLAIN_SOURCE,
    LENORMAND_READINGS,
    LENORMAND_SPREAD_OPENERS,
)
from app.engines.plain_compose import reading
from app.engines.plain_corpora import LENORMAND, PLAIN_CORPORA
from tests.plain_wording import advice_hits

#: 六字表在 `plain_wording.ADVICE_TOKENS`，这里不复制一份（T1 的合并债就是为此）。
#: 但反向对账要知道**源表**哪几格自带取向词，所以命中位置写死在下面两条测里。


def test_lenormand_corpus_is_the_row_the_factory_iterates() -> None:
    assert PLAIN_CORPORA["lenormand"] is LENORMAND
    # G3：综合判读已经由 `synthesis` 承担（`engines/lenormand.py:95`），白话不再补一句
    # 档位结论——两处同时下判就是重复，且第二处没有分数可依。
    assert LENORMAND.closers is None
    # 偏差表第 1 行的同款：极性三档里有 0（两张指示牌），`band` 分支遇 0 直接
    # `ValueError`（`plain_compose.py:65-67`）。见下面那条 keep 判据。
    assert LENORMAND.grouping == "keep"
    assert LENORMAND.slot_prefixes == frozenset()


def test_universe_is_the_thirty_six_card_ids_verbatim() -> None:
    assert len(CARDS) == 36
    assert LENORMAND.universe() == {card.id for card in CARDS}
    assert set(LENORMAND_READINGS) == LENORMAND.universe()
    # 键就是源表的 id，不做二次转写：`lenormand-01` 这种形状由 `_card()` 保证
    # （`content/lenormand.py:41-58`，id 在 :53 拼成），本表若自拼一份，改编号宽度时会漂。
    assert all(key.startswith("lenormand-") for key in LENORMAND.universe())


def test_openers_are_exactly_the_five_spread_ids() -> None:
    """R31：小节名单 = 五阵 id。`single` 那阵只有一张牌，缺开篇句就只剩一句牌义。"""
    assert set(LENORMAND_SPREAD_OPENERS) == set(SPREADS)
    assert set(LENORMAND.openers) == set(SPREADS)
    assert len(LENORMAND.openers) == 5


def test_each_opener_states_how_that_spread_is_read() -> None:
    """开篇句只讲「这一阵怎么读」，且认得出自己开的是哪一阵（G18 不给建议，G14 不新增前提）。

    `grand_tableau` 豁免阵名：源表的阵名是「大桌全景」，句子里说的是「大桌」＋「三十六张牌」，
    那是简称不是缺项（钉全名只会逼出一张别名表）。其余四阵的阵名一律逐字。
    """
    for spread_id, spread in sorted(SPREADS.items()):
        text = LENORMAND_SPREAD_OPENERS[spread_id]
        assert spread.name_zh in text or spread_id == "grand_tableau", (spread_id, spread.name_zh)
        assert advice_hits(text) == [], (spread_id, advice_hits(text))


def test_every_card_key_resolves_through_the_assembler() -> None:
    for key in sorted(LENORMAND.universe()):
        assert reading(LENORMAND, key) == LENORMAND_READINGS[key]


def test_each_retelling_carries_its_cards_name_and_noun_core() -> None:
    """G14 的落点：`name_zh` 与 `essence` 逐字进句子。

    只钉这两样，因为它们是**可核对的两端**：牌名（盘上印的字）与名词核心
    （组合直读的主词，`_combine()` 用的就是它，`engines/lenormand.py:127`）。`meaning`
    与 `keywords` 不钉——钉住等于要求白话把源表短句逐字抄回来，而它确实没抄：复测
    （2026-10-01 实跑，命令：`cd backend && PYTHONIOENCODING=utf-8
    .venv/Scripts/python.exe -c "from app.content.lenormand import CARDS as C;
    from app.content.lenormand_plain import LENORMAND_READINGS as R;
    print(sum(c.meaning in R[c.id] for c in C), sum(k in R[c.id] for c in C for k in c.keywords))"`）
    → `0 103`：36 条 `meaning` 零逐字命中，四格关键词合计命中 103 个（平均 2.86 个/张）。
    白话围着牌名与名词核心取料，不是把源表短句搬进长句——那既过不了工厂的单句号口径，
    也会把 `meaning` 里那 4 处取向词一起带进来（下面那条正是防这个）。
    """
    for card in sorted(CARDS, key=lambda c: c.number):
        text = LENORMAND_READINGS[card.id]
        assert card.name_zh in text, (card.number, "name_zh")
        assert card.essence in text, (card.number, "essence")


def test_no_retelling_borrows_the_source_tables_orientation_words() -> None:
    """G24：源表自己带取向词的 6 处，白话一处都不引（页面照旧印 polarity_label）。

    复测（2026-10-01 实跑，命令：`cd backend && PYTHONIOENCODING=utf-8
    .venv/Scripts/python.exe -c "from app.content.lenormand import CARDS as C;
    W=('宜','忌','需','应','吉','凶');
    print([(x.number,x.name_zh) for x in C if any(t in x.meaning for t in W)]);
    print([(x.number,x.name_zh) for x in C if any(t in x.as_modifier for t in W)])"`）：
    `meaning` 命中 4 处 = 2 三叶草「宜即时把握」/ 21 山「需时突破」/ 31 太阳「大吉之象」/
    33 钥匙「关键吉兆」；`as_modifier` 命中 2 处 = 11 鞭子、26 书（都写「需要磨合/需要研读」）。
    白话 36 条 + 5 句开篇抹词后命中 `[]`，且不需要为雷诺曼新增任何具名词形。
    「需要」不在 `plain_wording.NON_ADVICE_FORMS` 的抹词名单里（那里只有对应/反应/适应），
    所以这条扫的不是被抹平的残影，而是真字。
    """
    neutral = [card.number for card in CARDS if card.polarity == 0]
    assert sorted(neutral) == [28, 29], "两张指示牌是极性零，正是 `keep` 而非 `band` 的原因"
    for card in CARDS:
        text = LENORMAND_READINGS[card.id]
        assert advice_hits(text) == [], (card.number, advice_hits(text))
        assert POLARITY_LABEL[card.polarity] not in text, card.number
    for spread_id, text in sorted(LENORMAND_SPREAD_OPENERS.items()):
        assert advice_hits(text) == [], (spread_id, advice_hits(text))


def test_source_line_declares_which_fields_the_retelling_uses() -> None:
    from tests.plain_wording import FORBIDDEN

    assert LENORMAND_PLAIN_SOURCE.startswith("本系统白话转述")
    assert "36" in LENORMAND_PLAIN_SOURCE or "三十六" in LENORMAND_PLAIN_SOURCE
    for token in FORBIDDEN:
        assert token not in LENORMAND_PLAIN_SOURCE, token
    # 36 条全部有上游字段（`name_zh`/`essence`/`keywords`/`meaning`），无自持档：
    # 「自持」二字出现在这里就是虚报（对照紫微那条相反的要求）。
    assert "自持" not in LENORMAND_PLAIN_SOURCE
