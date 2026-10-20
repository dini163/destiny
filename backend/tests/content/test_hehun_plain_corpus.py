"""合婚白话表：工厂看不到的那五件事（批次二 spec §9.1）。

工厂管措辞四条与 `set(entries) == universe()`；这里钉它结构上够不着的：
① 登记身份（R24：`PLAIN_CORPORA` 是同键字面量字典，两行 `hehun` 会静默留后一条）；
② 两张键表与引擎 / 契约的**词面一致**（`hehun_tier` 改一个档名、`AxisSync` 加一档，
   工厂看不见，本文件的 `get_args` 对账看得见）；
③ 七条互异；④ 三句框架的样例句过 `frame_violations`，且每个槽位被引用一次；
⑤ 禁插清单（spec §4.2）：账本词面在白话文本里零命中。
"""

from typing import get_args

from app.content.hehun_plain import (
    HEHUN_AXIS_FRAME,
    HEHUN_COMPLEMENT_FRAME,
    HEHUN_READINGS,
    HEHUN_SCORE_FRAME,
    HEHUN_SECTION_TITLES,
    HEHUN_SYNC_KEYS,
    HEHUN_TONE_KEYS,
)
from app.engines.bazi_hehun import hehun_tier
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
#: 顿号连接的单字、干支是两字串、`{best_start}` / `{best_end}` 恒为年份串（`axis_years` 契约
#: `ge=1`，段表不空，所以「没有」这一支在生产里不存在，见 `hehun_plain` 的框架句注）。
SCORE_SAMPLES: dict[str, dict[str, str]] = {
    "小数分": {"value": num(62.5), "plus": num(78.5), "minus": num(16.0)},
    "零分且负账": {"value": num(0.0), "plus": num(9.0), "minus": num(24.5)},
    "整数高分": {"value": num(85.0), "plus": num(63.0), "minus": num(4.0)},
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
        "best_start": num(2027),
        "best_end": num(2028),
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
