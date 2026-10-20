"""岁运三片语料与九句框架：工厂看不到的那九件事（批次二 spec §4.2 / §4.3 / §7.1 / §7.3–§7.5）。

工厂管措辞四条与 `set(entries) == universe()`；这里钉它结构上够不着的：
① 登记身份（R24：`PLAIN_CORPORA` 是同键字面量字典，两行 `bazi_transit` 会静默留后一条）；
② 档位键表与引擎词面一致（`_tier` 改一个档名，工厂看不见，本文件看得见）；
③ 三条档位句互异；④ 九句框架的样例句过 `frame_violations`，且每句槽名逐字对账；
⑤ 禁插清单（spec §4.2 那五条）：账本词面与三个档名在白话文本里零命中，槽值同样不许带进去；
⑥ 样例句本身是**引擎给得出的形状**（账本恒等式、极值序、`count == 年数`、`span == 高分 − 低分`），
   框架门只量单句形状，量不到槽与槽之间的算术（J-T1 评审轮 I1 的同一条路子）；
⑦ 边界页：单流年页（`count` 为 1、`best` 即 `worst`）、未起运页（`{dayun}` 落 `尚未起运`）、
   月极值并列页、零命中页与十二格同分页——后两形由契约承认（`TransitDayCell.day_hits` /
   `TransitHourCell.hour_hits` 的字段说明自己写着「一条未中为 []」），本表不报「扫过几段共几格」
   那类数（时辰表每天恒出十二格，格数只是十二的整倍数，没有一条命令能把它跑出来），
   所以它们只进样例句、不写进句子；
⑧ 三页节标题名单（`BAZI_TRANSIT_TITLES`）是装配与前端共用的那一份，键序即页面序；
⑨ 出处串自守：`BAZI_TRANSIT_PLAIN_SOURCE` 点名的两道分界常量真在位、真的就是 `_tier` 在用的那两道。

样例句值除标注「契约一形」的那三份外全部来自实算（无 mock，AGENTS §9；那三份是 schema
字段说明承认的形状，数值是让边界值必须过门的最小构造，不宣称那样一页今天存在——三形名见下面
样例句表的头注）。复测命令逐份写在下面各样例句表的注释里。
"""

from datetime import date

from app.content.bazi_transit_plain import (
    BAZI_LIURI_DAYS_FRAME,
    BAZI_LIURI_FOCUS_FRAME,
    BAZI_LIURI_MONTH_FRAME,
    BAZI_LIUSHI_DAY_FRAME,
    BAZI_LIUSHI_FOCUS_FRAME,
    BAZI_LIUSHI_HOURS_FRAME,
    BAZI_TRANSIT_MONTH_FRAME,
    BAZI_TRANSIT_PLAIN_SOURCE,
    BAZI_TRANSIT_RANGE_FRAME,
    BAZI_TRANSIT_READINGS,
    BAZI_TRANSIT_THREAD_FRAME,
    BAZI_TRANSIT_TITLES,
    BAZI_TRANSIT_TONE_KEYS,
)
from app.engines.bazi_strength import STRONG_CUT, WEAK_CUT
from app.engines.bazi_transit import _tier
from app.engines.plain_compose import num, overview
from app.engines.plain_corpora import BAZI_TRANSIT, PLAIN_CORPORA
from tests.plain_wording import (
    FORBIDDEN,
    LEDGER_WORDS,
    ORIENTATION_WORDS,
    PREDICTION_FORBIDDEN,
    TIER_WORDS,
    WU_DECISION_FORBIDDEN,
    advice_hits,
    frame_slots,
    frame_violations,
    wording_violations,
)

#: 禁词面正主是 `LEDGER_WORDS` 那十七串（J-T1 已把**五**条岁运规则短名收进去：
#: `三会忌 / 三合成忌 / 半合忌 / 运干入忌 / 运支主气入忌`，本文件不另立「本页那份」）；
#: 那个「五」的复测（三个数依次是规则短名去重数、与 `LEDGER_WORDS` 的交集数、清单全长）：
#: `cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "from app.content.bazi_transit_rules import TRANSIT_RULES as R; from tests.plain_wording import LEDGER_WORDS; lab={r.label for r in R.values()}; print(len(lab), len(lab & set(LEDGER_WORDS)), len(LEDGER_WORDS))"` → `46 5 17`。
#: 本文件再并上三个档名（整串零命中，spec §7.1 括注）与 `FORBIDDEN` 三串。
_BANNED = [
    *PREDICTION_FORBIDDEN,
    *WU_DECISION_FORBIDDEN,
    *ORIENTATION_WORDS,
    *LEDGER_WORDS,
    *TIER_WORDS,
    *FORBIDDEN,
]

#: 九句框架的样例句。每份都写清它抄自哪一页（复测见各条），只有标注「契约一形」的那三份例外：
#: 三形逐字是流日第三节的「零命中契约一形」、流时第二节的「十二格同分契约一形」、
#: 流时第三节的「零命中契约一形」。那个「三」的复测（`chr(...)` 拼的就是「契约一形」四字，
#: 为中文字面量不进 `-c`）：`cd backend && PYTHONIOENCODING=utf-8
#: .venv/Scripts/python.exe -c "import tests.content.test_bazi_transit_plain_corpus as m; tag=chr(0x5951)+chr(0x7EA6)+chr(0x4E00)+chr(0x5F62); print(sum(1 for _f, s in m.FRAMES for k in s if tag in k))"` → `3`。
#: 它们是 schema 字段说明承认的形状（`day_hits` / `hour_hits` 为空数组）；本表不报「扫过几段共几格」
#: 那类经验数（时辰表每天恒出十二格，任何扫描的格数都只是十二的整倍数，格数本身不是凭据），
#: 收进来只为让边界值必须过门，而不是宣称那样一页今天存在。
RANGE_SAMPLES: dict[str, dict[str, str]] = {
    # 复测：`-c "import tests.test_bazi_transit as T; r=T._default(); print([(y.year, y.score.value) for y in r.years])"`
    # → 29 / 61 / 56 / 74 / 59：够得着 65 的只有 2029，落不到 45 的只有 2026。
    "五年三档齐": {
        "start": num(2026),
        "end": num(2030),
        "count": num(5),
        "strong": num(1),
        "weak": num(1),
        "strong_cut": num(STRONG_CUT),
        "weak_cut": num(WEAK_CUT),
    },
    # 边界页：`start_year == end_year` 那一页（`_transit(start_year=2029, end_year=2029)` → 一格，74.0）。
    "单流年页": {
        "start": num(2029),
        "end": num(2029),
        "count": num(1),
        "strong": num(1),
        "weak": num(0),
        "strong_cut": num(STRONG_CUT),
        "weak_cut": num(WEAK_CUT),
    },
    # 未起运那三年（`_transit(start_year=1990, end_year=1992)` → 41 / 73 / 36）。
    "三年两滞": {
        "start": num(1990),
        "end": num(1992),
        "count": num(3),
        "strong": num(1),
        "weak": num(2),
        "strong_cut": num(STRONG_CUT),
        "weak_cut": num(WEAK_CUT),
    },
}

THREAD_SAMPLES: dict[str, dict[str, str]] = {
    # 缺省页：`[s.ganzhi for s in T._default().dayun_covered]` → `['戊午']`，五年一运。
    "五年一运": {
        "dayun": "戊午",
        "best_year": num(2029),
        "best_ganzhi": "己酉",
        "best_value": num(74.0),
        "worst_year": num(2026),
        "worst_ganzhi": "丙午",
        "worst_value": num(29.0),
    },
    # 边界页：`[s.ganzhi for s in T._transit(start_year=1990, end_year=1992).dayun_covered]` → `['']`，
    # 装配侧 `"、".join(非空) or "尚未起运"` 因此落进这一形。
    "未起运页": {
        "dayun": "尚未起运",
        "best_year": num(1991),
        "best_ganzhi": "辛未",
        "best_value": num(73.0),
        "worst_year": num(1992),
        "worst_ganzhi": "壬申",
        "worst_value": num(36.0),
    },
    # 边界页：单流年那一页上 `max` 与 `min` 给的是同一年（2029 己酉 74.0）。
    "单年best即worst": {
        "dayun": "戊午",
        "best_year": num(2029),
        "best_ganzhi": "己酉",
        "best_value": num(74.0),
        "worst_year": num(2029),
        "worst_ganzhi": "己酉",
        "worst_value": num(74.0),
    },
}

MONTH_SAMPLES: dict[str, dict[str, str]] = {
    # `_transit(..., focus_year=2027)` 的十二格：最高 己酉 80.0、最低 癸卯 34.0，两处都不并列。
    "并列不成的两年": {
        "year": num(2027),
        "top_ganzhi": "己酉",
        "top_value": num(80.0),
        "low_ganzhi": "癸卯",
        "low_value": num(34.0),
    },
    # 边界页：`focus_year=2026` 的十二格里 癸巳（index 3）与 甲午（index 4）同为 0.0，
    # `min` 取排在最前的 癸巳；最高 辛丑 46.0 独格。
    "低点两格并列": {
        "year": num(2026),
        "top_ganzhi": "辛丑",
        "top_value": num(46.0),
        "low_ganzhi": "癸巳",
        "low_value": num(0.0),
    },
}

LIURI_MONTH_SAMPLES: dict[str, dict[str, str]] = {
    # `compute_liuri_matrix(anchor_date=2028-01-15)`：癸丑段 2028-01-06→2028-02-03，月分 58.0，
    # 29 格里 顺 6 / 平 13 / 滞 10。
    "顺滞都不为零": {
        "ganzhi": "癸丑",
        "start_solar": "2028-01-06",
        "end_solar": "2028-02-03",
        "value": num(58.0),
        "strong": num(6),
        "weak": num(10),
    },
    # 边界页：`anchor_date=2026-06-15` 的甲午段 2026-06-05→2026-07-06，月分 0.0，
    # 32 格全滞 ⇒ `{strong}` 为 0。
    "整段无高分格": {
        "ganzhi": "甲午",
        "start_solar": "2026-06-05",
        "end_solar": "2026-07-06",
        "value": num(0.0),
        "strong": num(0),
        "weak": num(32),
    },
}

LIURI_DAYS_SAMPLES: dict[str, dict[str, str]] = {
    # 同上月段：29 格，最高 己酉 77.0、最低 甲午 16.0（段内日柱不可能重格：月段按相邻两「节」切，
    # 节气间隔恒短于日柱 60 甲子那一循环，这是结构事实，不靠扫过几格）。
    "月内日柱不重": {
        "count": num(29),
        "high": "己酉",
        "high_value": num(77.0),
        "low": "甲午",
        "low_value": num(16.0),
    },
    # 边界页：甲午段 32 格，最高 己未 10.0、最低 辛亥 0.0 ⇒ 两端同侧也可能极低。
    "整段极低": {
        "count": num(32),
        "high": "己未",
        "high_value": num(10.0),
        "low": "辛亥",
        "low_value": num(0.0),
    },
}

LIURI_FOCUS_SAMPLES: dict[str, dict[str, str]] = {
    # `focus_date=2028-01-15`：己亥 60.0，`ri.` 行 7 条（同一页账本共 21 行：年段 8 含 `基准分`
    # 那一行 + `yue.` 6 + `ri.` 7；「规则行 20」那种读法要显式说明它排除了 `transit.base` 那一行）。
    # 复测：`cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "import tests.test_bazi_liuri as L; from datetime import date; r=L.compute_liuri_matrix(**L._NATAL_KWARGS, anchor_date=date(2028,1,15), focus_date=date(2028,1,15), reference_date=date(2028,1,15)); f=r.focused.score.factors; print(len(f), sum(1 for x in f if x.rule.startswith('yue.')), sum(1 for x in f if x.rule.startswith('ri.')), sum(1 for x in f if x.rule == 'transit.base'), len(r.focused.day_hits))"` → `21 6 7 1 7`。
    "七条命中": {"date": "2028-01-15", "ganzhi": "己亥", "value": num(60.0), "hits": num(7)},
    # `focus_date=2029-10-20`：癸未 67.0，`ri.` 行 5 条。
    "五条命中": {"date": "2029-10-20", "ganzhi": "癸未", "value": num(67.0), "hits": num(5)},
    # 契约一形（`TransitDayCell.day_hits` 字段说明：「一条未中为 []」），本表不报扫过几格的数。
    "零命中契约一形": {"date": "2031-05-05", "ganzhi": "壬辰", "value": num(63.0), "hits": num(0)},
}

LIUSHI_DAY_SAMPLES: dict[str, dict[str, str]] = {
    # `compute_liushi_day(solar_date=2028-01-15)`：己亥日头 60.0。
    "有分的日头": {"date": "2028-01-15", "ganzhi": "己亥", "value": num(60.0)},
    # 边界页：`solar_date=2026-06-15` 的庚申日，日段分值为 0.0（`value >= 0` 的下界那一页）。
    "日段零分": {"date": "2026-06-15", "ganzhi": "庚申", "value": num(0.0)},
}

LIUSHI_HOURS_SAMPLES: dict[str, dict[str, str]] = {
    # 同那天的十二格：未 13:00 83.0 / 子 23:00 32.0 ⇒ 差 51。
    "高低分明": {
        "top_zhi": "未",
        "top_clock": "13:00",
        "top_value": num(83.0),
        "low_zhi": "子",
        "low_clock": "23:00",
        "low_value": num(32.0),
        "span": num(round(83.0 - 32.0, 2)),
    },
    # `solar_date=2029-10-10`：未 13:00 86.0 / 寅 03:00 32.0 ⇒ 差 54。
    "换一天": {
        "top_zhi": "未",
        "top_clock": "13:00",
        "top_value": num(86.0),
        "low_zhi": "寅",
        "low_clock": "03:00",
        "low_value": num(32.0),
        "span": num(round(86.0 - 32.0, 2)),
    },
    # 边界页：`solar_date=2026-06-15`：辰 07:00 4.0 / 子 23:00 0.0 ⇒ 差只有 4，钟面 23:00 那格最低。
    "整段极低": {
        "top_zhi": "辰",
        "top_clock": "07:00",
        "top_value": num(4.0),
        "low_zhi": "子",
        "low_clock": "23:00",
        "low_value": num(0.0),
        "span": num(round(4.0 - 0.0, 2)),
    },
    # 契约一形（`TransitHourCell.hour_hits` 字段说明：「时段一条未中为 []，此时本格分值等于日头分」
    # ⇒ 十二格同分，`max` 与 `min` 都取时辰序首格，`{span}` 落 0）；时辰表每天恒出十二格，
    # 扫多少日都只是十二的整倍数，所以这里只挂契约标签，不挂「扫过 N 格未见」那种经验数。
    "十二格同分契约一形": {
        "top_zhi": "子",
        "top_clock": "23:00",
        "top_value": num(47.0),
        "low_zhi": "子",
        "low_clock": "23:00",
        "low_value": num(47.0),
        "span": num(round(47.0 - 47.0, 2)),
    },
}

LIUSHI_FOCUS_SAMPLES: dict[str, dict[str, str]] = {
    # `focus_hour_zhi=午`（2028-01-15）：午 11:00 51.0，`shi.` 行 4 条。
    "四条命中": {"zhi": "午", "clock": "11:00", "value": num(51.0), "hits": num(4)},
    # `focus_hour_zhi=子`（2029-10-10）：子 23:00 40.0，`shi.` 行 5 条——23:00 那格的钟面属于前一日。
    "子时格": {"zhi": "子", "clock": "23:00", "value": num(40.0), "hits": num(5)},
    # 契约一形（同 `hour_hits` 的「时段一条未中为 []」）。
    "零命中契约一形": {"zhi": "卯", "clock": "05:00", "value": num(60.0), "hits": num(0)},
}

#: 九句框架与各自那份样例句，序即 `BAZI_TRANSIT_*` 常量在语料文件里的声明序。
FRAMES: tuple[tuple[str, dict[str, dict[str, str]]], ...] = (
    (BAZI_TRANSIT_RANGE_FRAME, RANGE_SAMPLES),
    (BAZI_TRANSIT_THREAD_FRAME, THREAD_SAMPLES),
    (BAZI_TRANSIT_MONTH_FRAME, MONTH_SAMPLES),
    (BAZI_LIURI_MONTH_FRAME, LIURI_MONTH_SAMPLES),
    (BAZI_LIURI_DAYS_FRAME, LIURI_DAYS_SAMPLES),
    (BAZI_LIURI_FOCUS_FRAME, LIURI_FOCUS_SAMPLES),
    (BAZI_LIUSHI_DAY_FRAME, LIUSHI_DAY_SAMPLES),
    (BAZI_LIUSHI_HOURS_FRAME, LIUSHI_HOURS_SAMPLES),
    (BAZI_LIUSHI_FOCUS_FRAME, LIUSHI_FOCUS_SAMPLES),
)


def test_transit_corpus_is_the_row_the_factory_iterates() -> None:
    assert PLAIN_CORPORA["bazi_transit"] is BAZI_TRANSIT
    assert BAZI_TRANSIT.closers is None       # G3：白话层不补档位结论
    assert BAZI_TRANSIT.grouping == "keep"    # 本批无符号可传，band 分支无从触发
    assert BAZI_TRANSIT.slot_prefixes == frozenset()
    assert BAZI_TRANSIT.openers == {}         # SECTIONLESS：无小节形状本身


def test_tone_keys_are_what_the_engine_says() -> None:
    """三档名逐字对齐 `_tier` 的返回值（工厂看不见这个源）。

    复测：`cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "from app.engines.bazi_transit import _tier; print(_tier(80.0), _tier(50.0), _tier(20.0))"` → `顺 平 滞`。
    另四行把两道分界本身压在边界值上：`STRONG_CUT` 与 `WEAK_CUT` 改一个数，这一条就红。
    """
    assert {_tier(80.0), _tier(50.0), _tier(20.0)} == set(BAZI_TRANSIT_TONE_KEYS)
    assert _tier(STRONG_CUT) == "顺"
    assert _tier(STRONG_CUT - 0.1) == "平"
    assert _tier(WEAK_CUT) == "平"
    assert _tier(WEAK_CUT - 0.1) == "滞"
    assert set(BAZI_TRANSIT_READINGS) == set(BAZI_TRANSIT_TONE_KEYS.values())
    assert len(BAZI_TRANSIT_READINGS) == 3


def test_universe_is_three() -> None:
    assert BAZI_TRANSIT.universe() == set(BAZI_TRANSIT_TONE_KEYS.values())
    assert len(BAZI_TRANSIT.universe()) == 3


def test_three_sentences_are_mutually_distinct() -> None:
    texts = list(BAZI_TRANSIT_READINGS.values())
    assert len(set(texts)) == 3


def test_entries_clear_every_local_gate() -> None:
    """工厂的门（≥40 字 / 恰一「。」/ 含「你」/ FORBIDDEN）+ 三条自加门。

    档位名按**整串零命中**扫：`TIER_WORDS` 并禁清单，`token in text` 一条即红，不玩边沿形
    （spec §7.1 括注；代价见 `bazi_transit_plain` 头注 ①）。
    """
    for key in sorted(BAZI_TRANSIT_READINGS):
        text = BAZI_TRANSIT_READINGS[key]
        assert wording_violations(BAZI_TRANSIT, key) == []
        assert advice_hits(text) == []
        assert [token for token in _BANNED if token in text] == []


def test_the_three_sentences_never_name_a_calendar_unit() -> None:
    """口径 ③ 的机械版：三条档位句共用一个主语「这一段」，不许指定年、月、日还是时。

    三页同一条句子（岁运那一节的档位是**五年账本的均值**再过尺），所以句子一旦写「这一年」，
    流日页与流时页上它就是假话。这一条拦的就是那种「只在某页读起来对」的写法。
    只扫档位句：九句框架本来就各归一页，`{ganzhi} 这一段` 与「同一年内月和月之间」那样的
    月表句是它们的本职。
    """
    banned_subjects = ("这一年", "这个月", "这一天", "这两年", "这五年")
    for key, text in BAZI_TRANSIT_READINGS.items():
        assert "这一段" in text, key
        assert [unit for unit in banned_subjects if unit in text] == [], key


def test_frames_meet_the_frame_gate_when_instantiated() -> None:
    """九句 × 样例句：每句都过 `frame_violations`，且槽位逐个数一致（缺槽即 KeyError）。"""
    for frame, samples in FRAMES:
        declared = set(frame_slots(frame))
        assert declared, "空框架出不了门：槽位清单非空才谈得上实例化"
        assert len(samples) >= 2, (
            f"{sorted(declared)} 那一句的样例句不足两份——表被清空时下面三个循环零次迭代恒绿，"
            "地板只能由这一条守（brief Step 4：每句至少两份真实形状样例句）"
        )
        for slots in samples.values():
            assert set(slots) == declared
            text = overview(frame, slots)
            assert frame_violations(BAZI_TRANSIT.system, text) == []
            assert advice_hits(text) == []
            assert [token for token in _BANNED if token in text] == []


def test_no_frame_slot_value_carries_a_banned_token() -> None:
    """禁插清单（spec §4.2）的另一半：槽**值**也不许把账本短名、判语、十二长生名、档位名带进句子。

    九句框架的槽值只有四类来源（年数与分值由 `num()`、干支、ISO 日、钟面串），所以这条门今天
    是零命中的形状门；它拦的是以后有人把 `fired[].label` 或 `qi_strength` 塞进槽里。
    `尚未起运` 那一形里有「运」字，不在禁串里——它拦的是「天作之合」这类账本词面。
    """
    for _frame, samples in FRAMES:
        for slots in samples.values():
            for name, value in slots.items():
                assert [token for token in _BANNED if token in value] == [], f"{name}={value}"
                assert advice_hits(value) == []
                assert value.strip() == value and value != ""


def test_titles_are_the_three_pages_roster() -> None:
    assert tuple(BAZI_TRANSIT_TITLES) == ("transit", "liuri", "liushi")
    assert {len(titles) for titles in BAZI_TRANSIT_TITLES.values()} == {3}
    assert len({title for titles in BAZI_TRANSIT_TITLES.values() for title in titles}) == 9


def test_samples_obey_the_arithmetic_the_frames_claim() -> None:
    """样例句必须是引擎给得出的形状：句子把几个数并排印出来，读者一减就看见矛盾。

    **按槽位身份判的通用一遍**（`FRAMES` 里每一份样例句的每一个槽，不看句名）：
    `value` 与 `*_value` 一律 `0 <= x <= 100`，`strong` / `weak` / `hits` / `count` 四个计数槽
    一律 `>= 0`。分数那一条的契约正主是 `app/schemas/scoring.py` 的 `ScoreValue.value`
    （`value: float = Field(ge=0, le=100)`，岁运 / 流日 / 流时的段账本全是这一个类型）与
    日、时两格的同值 `ge/le`（`app/schemas/bazi_liuri.py` 的 `TransitDayCell.value`、
    `app/schemas/bazi_liushi.py` 的 `TransitHourCell.value`）；这条通用覆盖的六个分数槽名是
    `value` / `best_value` / `worst_value` / `top_value` / `low_value` / `high_value`
    （后四个此前一处都没被 bound；复测：`cd backend && PYTHONIOENCODING=utf-8
    .venv/Scripts/python.exe -c "import tests.content.test_bazi_transit_plain_corpus as m; L=sorted({n for _f, s in m.FRAMES for v in s.values() for n in v if n == 'value' or n.endswith('_value')}); print(len(L), L)"` → `6 ['best_value', 'high_value', 'low_value', 'top_value', 'value', 'worst_value']`）。
    跨槽关系只在**同一句框架同时带着那些槽**时才判：`RANGE` 的 `count == end − start + 1`
    与 `strong + weak <= count`、`strong_cut > weak_cut`；`LIURI_MONTH` 的
    `strong + weak <= 段长`（那句自己带着 `start_solar` / `end_solar`，段长即两串 ISO 日之差
    含首尾，它不带 `count`，所以总量从日期来而不是从年数来）；`LIURI_DAYS` 的
    `1 <= count <= 60`（那句自称「这一月」，而日柱 60 甲子才一循环——段长过 60 时
    `{high}` / `{low}` 就可能各指两格，语料侧 `BAZI_LIURI_DAYS_FRAME` 的注是同一条尺）；
    `THREAD` / `MONTH` / `LIURI_DAYS` / `LIUSHI_HOURS` 的高低两槽高者 >= 低者，
    `THREAD` 的 `best_year >= 1900` 与 `{dayun}` 非空串；`LIUSHI_HOURS` 的
    `span == round(高分 − 低分, 2)`（差只有一个正主，口径 ④）。
    """
    for _frame, samples in FRAMES:
        for slots in samples.values():
            for name, value in slots.items():
                if name == "value" or name.endswith("_value"):
                    assert 0.0 <= float(value) <= 100.0, f"{name}={value}"
                if name in ("strong", "weak", "hits", "count"):
                    assert int(value) >= 0, f"{name}={value}"
    for slots in RANGE_SAMPLES.values():
        start, end, count = (int(slots[k]) for k in ("start", "end", "count"))
        strong, weak = int(slots["strong"]), int(slots["weak"])
        assert count == end - start + 1 and strong + weak <= count
        assert float(slots["strong_cut"]) > float(slots["weak_cut"])
    for slots in THREAD_SAMPLES.values():
        assert float(slots["best_value"]) >= float(slots["worst_value"])
        assert int(slots["best_year"]) >= 1900 and slots["dayun"] != ""
    for slots in MONTH_SAMPLES.values():
        assert float(slots["top_value"]) >= float(slots["low_value"])
    for slots in LIURI_MONTH_SAMPLES.values():
        start_solar = date.fromisoformat(slots["start_solar"])
        end_solar = date.fromisoformat(slots["end_solar"])
        span_days = (end_solar - start_solar).days + 1
        assert span_days >= 1, slots["start_solar"]
        assert int(slots["strong"]) + int(slots["weak"]) <= span_days, f"strong+weak > {span_days}"
    for slots in LIURI_DAYS_SAMPLES.values():
        assert 1 <= int(slots["count"]) <= 60, slots["count"]
        assert float(slots["high_value"]) >= float(slots["low_value"])
    for slots in LIUSHI_HOURS_SAMPLES.values():
        top, low = float(slots["top_value"]), float(slots["low_value"])
        assert top >= low and float(slots["span"]) == round(top - low, 2)


def test_the_source_string_names_the_cuts_it_claims() -> None:
    """出处串自守（串不进 `wording_violations`，由语料测自守）。

    串里点名的两道分界必须真存在、真叫这两个名字，且 `_tier` 真的就用它们——换分界而散文照旧、
    门照绿，是这条拦的形状。
    `FORBIDDEN` 三串的整串零命中补在这里（先例：
    `tests/content/test_western_plain_corpus.py::test_the_source_string_is_a_provenance_string_not_a_sentence`）：
    这条串不进工厂遍历，工厂那四条 corpus 门看不到它，而它随 `plain_source` 上 J-T4 / J-T5
    三页的响应面——「；」正是三串之一，靠人审守不住。
    """
    for name in ("STRONG_CUT", "WEAK_CUT"):
        assert name in BAZI_TRANSIT_PLAIN_SOURCE, name
    assert "自撰" in BAZI_TRANSIT_PLAIN_SOURCE
    for token in FORBIDDEN:
        assert token not in BAZI_TRANSIT_PLAIN_SOURCE, token
    assert _tier(STRONG_CUT) == "顺" and _tier(WEAK_CUT - 0.1) == "滞"
