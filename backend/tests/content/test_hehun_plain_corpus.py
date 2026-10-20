"""合婚白话表：工厂看不到的那七件事（批次二 spec §9.1 + J-T1 评审轮）。

工厂管措辞四条与 `set(entries) == universe()`；这里钉它结构上够不着的：
① 登记身份（R24：`PLAIN_CORPORA` 是同键字面量字典，两行 `hehun` 会静默留后一条）；
② 两张键表与引擎 / 契约的**词面一致**（`hehun_tier` 改一个档名、`AxisSync` 加一档，
   工厂看不见，本文件的 `get_args` 对账看得见）；
③ 七条互异；④ 三句框架的样例句过 `frame_violations`，且每个槽位被引用一次；
⑤ 禁插清单（spec §4.2）：账本词面在白话文本里零命中；
⑥ 样例句本身是**引擎给得出的形状**（`plus − minus == value` 的账本恒等式 + 平局取最早那一段），
   框架门只量单句形状，量不到槽与槽之间的算术（评审轮 I1 / C2）；
⑦ 出处串自守：`HEHUN_PLAIN_SOURCE` 点名的五处常量真在位、且真的就是 `hehun_tier` / `axis_sync`
   在用的那五道分界（spec §8.7）。
"""

from typing import get_args

from app.content.bazi_hehun_rules import (
    HEHUN_BASE,
    HEHUN_SYNC_CLOSE,
    HEHUN_SYNC_WIDE,
    HEHUN_TOP_CUT,
)
from app.content.hehun_plain import (
    HEHUN_AXIS_FRAME,
    HEHUN_COMPLEMENT_FRAME,
    HEHUN_PLAIN_SOURCE,
    HEHUN_READINGS,
    HEHUN_SCORE_FRAME,
    HEHUN_SECTION_TITLES,
    HEHUN_SYNC_KEYS,
    HEHUN_TONE_KEYS,
)
from app.engines.bazi_hehun import axis_sync, hehun_tier
from app.engines.bazi_strength import STRONG_CUT, WEAK_CUT
from app.engines.plain_compose import num, overview
from app.engines.plain_corpora import HEHUN, PLAIN_CORPORA
from app.schemas.bazi_hehun import AxisSync
from tests.plain_wording import (
    LEDGER_WORDS,
    ORIENTATION_WORDS,
    PREDICTION_FORBIDDEN,
    WU_DECISION_FORBIDDEN,
    advice_hits,
    frame_slots,
    frame_violations,
    wording_violations,
)

#: 三句框架的样例句：喂**真实形状**的槽值——小数由 `num()` 出串、五行串是「木、火」这种
#: 顿号连接的单字、`{best_start}` / `{best_end}` 恒为年份串（`axis_years` 契约 `ge=1`，段表不空，
#: 所以「没有」这一支在生产里不存在，见 `hehun_plain` 的框架句注）。三份 SCORE 三元组还各自
#: 满足账本恒等式（`test_score_samples_obey_the_ledger_identity`），第三份 AXIS 喂的是尺在平局时
#: 给得出的那一形（`同频` 计数为 0 ⇒ 全平局 ⇒ 最早那一段），不是随手编的年份。
SCORE_SAMPLES: dict[str, dict[str, str]] = {
    "小数分": {"value": num(62.5), "plus": num(78.5), "minus": num(16.0)},
    "零分且负账": {"value": num(0.0), "plus": num(50.0), "minus": num(50.0)},
    "整数高分": {"value": num(85.0), "plus": num(90.0), "minus": num(5.0)},
}

COMPLEMENT_SAMPLES: dict[str, dict[str, str]] = {
    "两造各有补阙": {
        "m_give": "木、火",
        "m_thin": "水",
        "f_give": "水、金",
        "f_thin": "火",
        "nayin": "水生木",
    },
    "一侧补格全空": {
        "m_give": "金、水、土",
        "m_thin": "没有",
        "f_give": "没有",
        "f_thin": "木、火",
        "nayin": "木与木同气",
    },
}

AXIS_SAMPLES: dict[str, dict[str, str]] = {
    "单年全同频": {
        "start": num(2026),
        "end": num(2026),
        "aligned": num(1),
        "half": num(0),
        "apart": num(0),
        "best_start": num(2026),
        "best_end": num(2026),
    },
    "十年三档都有": {
        "start": num(2026),
        "end": num(2035),
        "aligned": num(3),
        "half": num(4),
        "apart": num(3),
        "best_start": num(2029),
        "best_end": num(2031),
    },
    "整段无一档同频": {
        "start": num(2026),
        "end": num(2030),
        "aligned": num(0),
        "half": num(2),
        "apart": num(3),
        "best_start": num(2026),
        "best_end": num(2027),
    },
}

#: 三句框架共用的一套禁串：条目门用的那份，框架句一样不许躲。
_BANNED = [*PREDICTION_FORBIDDEN, *WU_DECISION_FORBIDDEN, *ORIENTATION_WORDS, *LEDGER_WORDS]


def test_hehun_corpus_is_the_row_the_factory_iterates() -> None:
    assert PLAIN_CORPORA["hehun"] is HEHUN
    assert HEHUN.closers is None          # G3：白话层不补档位结论
    assert HEHUN.grouping == "keep"       # 本批无符号可传，band 分支无从触发
    assert HEHUN.slot_prefixes == frozenset()
    assert HEHUN.openers == {}            # 无小节形状本身（SECTIONLESS 那两颗钉的第三处呼应）


def test_tone_keys_are_what_the_engine_and_the_contract_say() -> None:
    """四档名逐字对齐 `hehun_tier` 的返回值；三档对齐 `AxisSync`（工厂看不见这两个源）。"""
    cuts = [80.0, 65.0, 45.0, 44.0]
    assert {hehun_tier(value) for value in cuts} == set(HEHUN_TONE_KEYS)
    assert set(get_args(AxisSync)) == set(HEHUN_SYNC_KEYS)
    assert set(HEHUN_READINGS) == {*HEHUN_TONE_KEYS.values(), *HEHUN_SYNC_KEYS.values()}
    assert len(HEHUN_READINGS) == 7


def test_universe_is_derived_from_the_two_key_tables() -> None:
    assert HEHUN.universe() == {*HEHUN_TONE_KEYS.values(), *HEHUN_SYNC_KEYS.values()}
    assert len(HEHUN.universe()) == 7


def test_seven_sentences_are_mutually_distinct() -> None:
    texts = list(HEHUN_READINGS.values())
    assert len(set(texts)) == 7


def test_entries_clear_every_local_gate() -> None:
    """工厂的门（≥40 字 / 恰一「。」/ 含「你」/ FORBIDDEN）+ 三条自加门。"""
    for key in sorted(HEHUN_READINGS):
        assert wording_violations(HEHUN, key) == []
        assert advice_hits(HEHUN_READINGS[key]) == []
        assert [token for token in _BANNED if token in HEHUN_READINGS[key]] == []


def test_frames_meet_the_frame_gate_when_instantiated() -> None:
    """三句框架 × 样例句：每句都过 `frame_violations`，且槽位逐个数一致（缺槽即 KeyError）。"""
    for frame, samples in (
        (HEHUN_SCORE_FRAME, SCORE_SAMPLES),
        (HEHUN_COMPLEMENT_FRAME, COMPLEMENT_SAMPLES),
        (HEHUN_AXIS_FRAME, AXIS_SAMPLES),
    ):
        declared = set(frame_slots(frame))
        for slots in samples.values():
            assert set(slots) == declared
            text = overview(frame, slots)
            assert frame_violations("hehun", text) == []
            assert advice_hits(text) == []
            assert [token for token in _BANNED if token in text] == []


def test_section_titles_are_three_and_pinned() -> None:
    assert HEHUN_SECTION_TITLES == ("契合分的来历", "五行互给", "同频的段落")


def test_score_samples_obey_the_ledger_identity() -> None:
    """样例句得是**引擎给得出的三元组**：`plus − minus == value` 且 `plus ≥ 起点那一笔`。

    框架门只看单句形状，管不到槽与槽之间的算术；而这一节把三个数并排印给读者，读者一减就看见矛盾。
    `build_ledger` 把起点分作为恒在的正数行放进 `factors`，所以按符号求和必满足等式且 `plus` 不小于起点。
    """
    for name, slots in SCORE_SAMPLES.items():
        value, plus, minus = (float(slots[key]) for key in ("value", "plus", "minus"))
        assert plus - minus == value, name
        assert plus >= HEHUN_BASE, name


def test_the_source_string_names_the_cuts_it_claims() -> None:
    """出处串自守（spec §8.7：串不进 `wording_violations`，由语料测自守；AGENTS §7 的诚实性压在这一行）。

    串里点名的五处常量必须**真的存在**、真的叫这几个名字，且五道分界确实落在这五个常量上
    （`hehun_tier` 三道：`HEHUN_TOP_CUT` / `STRONG_CUT` / `WEAK_CUT`；`axis_sync` 两道：
    `HEHUN_SYNC_CLOSE` / `HEHUN_SYNC_WIDE`）——改名或换分界而散文照旧、门照绿，是这条拦的形状。
    这批断言与常量**共享同一份数值**，所以它们守的是结构（哪一道界由哪个常量把、比较方向、
    档序、返回名），不是数值本身。
    """
    for name in ("HEHUN_TOP_CUT", "STRONG_CUT", "WEAK_CUT", "HEHUN_SYNC_CLOSE", "HEHUN_SYNC_WIDE"):
        assert name in HEHUN_PLAIN_SOURCE, name
    assert "自撰" in HEHUN_PLAIN_SOURCE
    assert hehun_tier(HEHUN_TOP_CUT) == "天作之合"
    assert hehun_tier(HEHUN_TOP_CUT - 0.1) == "相得益彰"
    assert hehun_tier(STRONG_CUT) == "相得益彰"
    assert hehun_tier(STRONG_CUT - 0.1) == "中和可处"
    assert hehun_tier(WEAK_CUT) == "中和可处"
    assert hehun_tier(WEAK_CUT - 0.1) == "欠和宜慎"
    assert axis_sync(HEHUN_SYNC_CLOSE) == "同频"
    assert axis_sync(HEHUN_SYNC_CLOSE + 0.1) == "半同步"
    assert axis_sync(HEHUN_SYNC_WIDE) == "半同步"
    assert axis_sync(HEHUN_SYNC_WIDE + 0.1) == "背离"
