"""周易今译的本地门（丁组 spec §4.2、§4.4、§8）。

自 T13 起本文件吃**真登记**的那张 `PLAIN_CORPORA["zhouyi"]`（即 `ZHOUYI`），与工厂同源。
共享措辞契约那一条工厂也在跑（工厂侧叫 `test_every_entry_meets_the_wording_contract`）；
本文件另 24 条门工厂一条都不跑（条数复测：`cd backend && grep -c "^def test_" tests/content/test_zhouyi_plain_corpus.py`
→ 25，减去与工厂同跑的那一条），其中最要紧的是断词那一族（引用 / 不漏译 / 不升格、剥 `「…」`
后的建议词，以及七类自述句：爻题起头 / 极性·位·得正失正 / 世应 / 断词个数 / 点名断词 / 字数 /
处数），另有 anchor 逐字、键构造器、`COVERED` 名单、门 2「源文不漏进 `entries`」、出处串自述，
以及 Plan E 终审补的四门两字·点名单字·句数·中间段自述（`G1`-`G4`），
与文件末尾的三条登记钉（`PLAIN_CORPORA` 名下一份、登记形状、450 键全集）和三条出处钉
（`ZHOUYI_CONTENT_SOURCES` 的逐字名单、与梅花共用串的等值、今译表落在第五行）。

T1-T12 期间这张测必须自造一张 `PlainCorpus`：登记行要等 450 条齐了才能进 `PLAIN_CORPORA`，
否则键全集门在只有 8 条时就红 11 批（计划偏差表第 4 行）。登记完成后那张已删——留着就是
同一份措辞口径的第二份副本（AGENTS.md §8 说的那种会漂的东西）；本地这条 450 例扫描为什么
仍然留，见该测的 docstring。
"""

import re

import pytest

from app.content import MEIHUA_CONTENT_SOURCES, ZHOUYI_CONTENT_SOURCES, zhouyi_text
from app.content.zhouyi_guaci import YONG_CI
from app.content.zhouyi_hexagrams import HEXAGRAM_BY_NUMBER
from app.content.zhouyi_plain import (
    ZHOUYI_ANCHORS,
    ZHOUYI_PLAIN_SOURCE,
    ZHOUYI_READINGS,
    gua_ci_key,
    yao_ci_key,
    yong_ci_key,
)
from app.content.zhouyi_text import ZHOUYI_SOURCE
from app.engines.plain_corpora import PLAIN_CORPORA, ZHOUYI
from tests.plain_wording import advice_hits, wording_violations

#: 本批已覆盖的卦号。T2-T12 每批往里加自己那 5-6 卦，一条也不许多。
COVERED: tuple[int, ...] = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64,)

#: 原文的六个断词与八个升格串（spec §4.4）。
VERDICT_WORDS = ("吉", "凶", "厉", "悔", "吝", "咎")
ESCALATION = ("大吉", "小吉", "凶险", "注定", "必然", "一定", "天意", "命定")
_QUOTED = re.compile(r"「[^」]*」")


def _built_keys() -> list[str]:
    return sorted(ZHOUYI_READINGS)


def test_the_three_key_builders_are_the_only_key_source() -> None:
    """键构造器不补零、带卦号（spec §4.3 三条判据里的两条）。"""
    assert gua_ci_key(1) == "zhouyi.gua.1"
    assert yao_ci_key(1, 6) == "zhouyi.yao.1.6"
    assert yong_ci_key(2) == "zhouyi.yong.2"


def test_every_built_anchor_equals_the_live_source_text() -> None:
    """spec §4.2 门 1：源表改一个字，这里就红。逐键报。"""
    for key in _built_keys():
        assert key in ZHOUYI_ANCHORS, f"{key} 有今译却没 anchor"
        kind, rest = key[len("zhouyi."):].split(".", 1)
        if kind == "gua":
            assert ZHOUYI_ANCHORS[key] == zhouyi_text.gua_ci(int(rest)), key
        elif kind == "yong":
            assert ZHOUYI_ANCHORS[key] == zhouyi_text.yong_ci(int(rest))[1], key
        else:
            number, position = (int(x) for x in rest.split("."))
            assert ZHOUYI_ANCHORS[key] == zhouyi_text.yao_ci(number, position), key


def test_covered_hexagrams_are_complete_no_row_missing() -> None:
    """批次花名册：`COVERED` 里的每一卦必须卦辞 + 六爻（乾坤再加用）齐。"""
    expected = set()
    for number in COVERED:
        expected.add(gua_ci_key(number))
        expected |= {yao_ci_key(number, p) for p in range(1, 7)}
        if number in YONG_CI:
            expected.add(yong_ci_key(number))
    assert set(ZHOUYI_READINGS) == expected
    assert set(ZHOUYI_ANCHORS) == expected


@pytest.mark.parametrize("key", _built_keys())
def test_every_plain_text_meets_the_shared_factory_contract(key) -> None:
    """≥40 字 / 恰一「。」 / 含「你」/ 无「；」（spec §4.1 的契约来源是工厂，不是本文件）。

    工厂的 `test_every_entry_meets_the_wording_contract[zhouyi:*]` 对同一个对象跑同一条谓词，
    这份重复是**刻意留的**：那 450 例的存在依赖登记——有人把 `zhouyi` 从 `PLAIN_CORPORA` 摘掉时，
    工厂那侧的用例是静默消失而不是变红（T13 评审实测：un-register 只让
    `test_the_corpus_is_registered_under_its_own_name` 一条红）。本条不依赖登记，照样逐条跑，
    所以它是「登记被撤销时仍然存在的独立验证」，不是口径副本。
    """
    assert wording_violations(ZHOUYI, key) == []


@pytest.mark.parametrize("key", _built_keys())
def test_verdict_words_are_quoted_and_never_escalated(key) -> None:
    """spec §4.4 三条一次判完：引用、不漏译、不升格。"""
    text = ZHOUYI_READINGS[key]
    naked = _QUOTED.sub("", text)
    for word in VERDICT_WORDS:
        assert word not in naked, f"{key} 的今译在引号外写了断词「{word}」"
        source = ZHOUYI_ANCHORS[key]
        if word in source:
            assert f"「{word}」" in text, f"{key} 源文有「{word}」而今译没引用它"
    for word in ESCALATION:
        assert word not in text, f"{key} 升格了断词：{word}"


@pytest.mark.parametrize("key", _built_keys())
def test_advice_caliber_runs_on_the_text_outside_quotes(key) -> None:
    """spec §4.4 末段：剥掉 `「…」` 才跑既有建议词口径，不改工厂、不改表。"""
    naked = _QUOTED.sub("", ZHOUYI_READINGS[key])
    assert advice_hits(naked) == []


def test_the_plain_table_never_leaks_the_source_text_into_entries() -> None:
    """spec §4.2 门 2：`entries` 里只准有今译。源文既不满 40 字也不含「你」，
    混进去就是让闸去检查古文——这条用「anchor 与今译两两不等」把门 2 钉住。"""
    for key in _built_keys():
        assert ZHOUYI_READINGS[key] != ZHOUYI_ANCHORS[key], key
        assert not ZHOUYI_READINGS[key].startswith(ZHOUYI_ANCHORS[key][:6]), key


def test_every_line_reading_opens_with_its_own_yao_title() -> None:
    """spec §4.1 段② 的骨架：每一条爻辞今译都以本爻的爻题起头，题从卦画表现算，
    不写字面量清单（T2/T3 实测「上九」被写成「居奇位」这一类自相矛盾，就是这条钉住的）。"""
    for key in _built_keys():
        if not key.startswith("zhouyi.yao."):
            continue
        number, position = (int(x) for x in key[len("zhouyi.yao."):].split("."))
        expected = zhouyi_text.line_name(
            position, HEXAGRAM_BY_NUMBER[number].lines[position - 1] == 1
        )
        assert ZHOUYI_READINGS[key].startswith(expected), (
            f"{key} 的今译以 {ZHOUYI_READINGS[key][:2]} 起头，本爻的题是 {expected}"
        )


#: 段② 里能对卦画验算的句式。「阳位/阴位」是「奇位/偶位」的同一说法（阳位 = 奇位）；判语只认
#: 与这半句同一个小句里的「得正/失正」——很多行只报位置不下判，所以判语组是可缺的。
_POSITION_CLAIM = re.compile(r"([阳阴])爻居([奇偶阳阴])位")
_VERDICT = re.compile(r"(得正|失正)")


def test_every_stated_position_claim_matches_the_line_binary() -> None:
    """极性、位的奇偶、得正/失正三样都从 `Hexagram.lines` 现算对一遍（spec §4.1：段② 只许说
    卦画里**已有**的结构，说反了就是往用户眼前塞一条错的位置事实）。"""
    for key in _built_keys():
        if not key.startswith("zhouyi.yao."):
            continue
        number, position = (int(x) for x in key[len("zhouyi.yao."):].split("."))
        is_yang = HEXAGRAM_BY_NUMBER[number].lines[position - 1] == 1
        is_odd = position % 2 == 1
        expected_verdict = "得正" if is_yang == is_odd else "失正"
        for clause in ZHOUYI_READINGS[key].split("，"):
            match = _POSITION_CLAIM.search(clause)
            if match is None:
                continue
            polarity, parity = match.groups()
            assert polarity == ("阳" if is_yang else "阴"), (
                f"{key} 写成{polarity}爻，卦画这一爻是{'阳' if is_yang else '阴'}"
            )
            assert (parity in ("奇", "阳")) == is_odd, (
                f"{key} 把第 {position} 位（{'奇' if is_odd else '偶'}位）说成{parity}位"
            )
            stated = _VERDICT.search(clause)
            if stated:
                assert stated.group(1) == expected_verdict, (
                    f"{key} 说 {stated.group(1)}，按卦画应是 {expected_verdict}"
                )


#: 今译里自称世/应的句式全站只有两种（T6/T7 实跑 67 条：33 世、34 应），所以能逐条对列复算。
_SHI_YING_CLAIM = re.compile(r"它是这一卦的(世爻|「应爻」)")


def test_every_stated_shi_ying_claim_matches_the_najia_columns() -> None:
    """段② 剩下那一半：京房世应住在 `Hexagram.shi` / `.ying`（`zhouyi_hexagrams.py:123-124`，由
    `SHI_BY_GENERATION` × `_ying_of` 现算），所以「它是这一卦的世爻」这句话是**可机检的事实**，
    不是只能人读的语气。说错一格就是往用户眼前塞一条错的卦位身份。"""
    for key in _built_keys():
        if not key.startswith("zhouyi.yao."):
            continue
        number, position = (int(x) for x in key[len("zhouyi.yao."):].split("."))
        hexagram = HEXAGRAM_BY_NUMBER[number]
        for claimed in _SHI_YING_CLAIM.findall(ZHOUYI_READINGS[key]):
            if claimed == "世爻":
                assert position == hexagram.shi, (
                    f"{key} 自称世爻，这一卦（{hexagram.name_zh}·{hexagram.generation}）世在 {hexagram.shi}"
                )
            else:
                assert position == hexagram.ying, (
                    f"{key} 自称「应爻」，这一卦（{hexagram.name_zh}·{hexagram.generation}）应在 {hexagram.ying}"
                )


#: 断词清点句的五种写法，全站实测覆盖得完（450 键 = 计数 59 / 零自述 3 / 单断词 16 /
#: 不下断词 54 / 点名句 221，共 353 条断言；T12 已建满 450 键，此后只有改语句才会改这个数）。
#: 口径同 `VERDICT_WORDS`：只数那六个字在
#: anchor 里的**出现次数**（`无咎` 记 1、`贞吉` 记 1、`悔厉吉` 记 3）。
#: 钉不住的两种写法有意留在门外：「它给的不是断词而是……」（与 `不给断词` 不同形，
#: 强并会把「不是」读成否定式清点）与裸量词「它两处给顺路」（宾语是利字，不是断词）。
#: 五个数的复测（一行，与本文件下方五个正则同口径）：
#: `cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "import re;from app.content.zhouyi_plain import ZHOUYI_READINGS as R;P=[('计数',r'([一两二三四五六])个断词'),('零自述',r'一个断词也不[给说]'),('单断词',r'断词只(?:有|出现|那|这)[^，。]{0,6}一[个处次]'),('不下断词',r'不[下给]断词|没有断词'),('点名句',r'断词[^，。「」]{0,6}「([吉凶厉悔吝咎])」')];o={k:len(re.findall(p,''.join(R.values()))) for k,p in P};print(o,sum(o.values()))"`
_VERDICT_COUNT = re.compile(r"([一两二三四五六])个断词")
_VERDICT_ZERO = re.compile(r"一个断词也不[给说]")
_VERDICT_SINGLE = re.compile(r"断词只(?:有|出现|那|这)[^，。]{0,6}一[个处次]")
_VERDICT_NONE = re.compile(r"不[下给]断词|没有断词")
_VERDICT_NAMED = re.compile(r"断词[^，。「」]{0,6}「([吉凶厉悔吝咎])」")
_CN_COUNT = {"一": 1, "两": 2, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6}


def _verdict_tally(anchor: str) -> int:
    return sum(anchor.count(word) for word in VERDICT_WORDS)


def test_every_stated_verdict_count_matches_the_anchor() -> None:
    """「这一爻两个断词」是**可验算的清点句**：数错就是当着用户的面数错原文，把亨称作
    断词就是替原文多下一句判词（T8/T9 评审揪出的正是这一类）。零自述、单断词、不下断词
    三种写法在这里各自独立钉一次实数——先前的门只把零自述当计数的豁免，自己一条也不主张，
    所以一行满口断词照样可以自称「一个断词也不给」（T10/T11 评审 I-3）。"""
    for key in _built_keys():
        anchor = ZHOUYI_ANCHORS[key]
        reading = ZHOUYI_READINGS[key]
        real = _verdict_tally(anchor)
        zero_spans = [m.span() for m in _VERDICT_ZERO.finditer(reading)]
        for m in _VERDICT_COUNT.finditer(reading):
            claimed = (
                0 if any(s <= m.start() < e for s, e in zero_spans) else _CN_COUNT[m.group(1)]
            )
            assert claimed == real, (
                f"{key} 说「{m.group(0)}」，anchor「{anchor}」里断词实数 {real}"
            )
        for rx, want, label in (
            (_VERDICT_ZERO, 0, "零自述"),
            (_VERDICT_SINGLE, 1, "单断词自述"),
            (_VERDICT_NONE, 0, "不下断词"),
        ):
            for m in rx.finditer(reading):
                assert real == want, (
                    f"{key} 的{label}「{m.group(0)}」，anchor「{anchor}」里断词实数 {real}"
                )


def test_every_named_verdict_word_appears_in_the_anchor() -> None:
    """点名句（「原断词是「吉」」「断词只有一个「凶」」）报出的那个字必须真在原文里。
    它只查**存在**，不查唯一性——唯一性归上一条的「单断词自述」；这一条管更硬的那错：
    报一个原文里根本没有的断词，等于替原文凭空造一句判词。"""
    for key in _built_keys():
        anchor = ZHOUYI_ANCHORS[key]
        for m in _VERDICT_NAMED.finditer(ZHOUYI_READINGS[key]):
            assert m.group(1) in anchor, (
                f"{key} 点名「{m.group(0)}」，anchor「{anchor}」里没有 {m.group(1)} 字"
            )


#: 「N个字」只钉主语是整条的那一式（卦辞/这一爻 + 只 + 数词）。「末尾多给两个字」
#: 「只留一个字说可以食」「它只给一个字说通」数的是句尾那半条，基准不同，硬并会误红
#: ——它们由评审员人核。
_CHAR_COUNT = re.compile(r"(?:卦辞|这一爻)只[有留]?([一两二三四五六])个字")
#: 卦辞行里的结构清点句：数量词紧跟得正/失正/失位，基准是全卦六爻（`lines` 底向上，
#: 阳居奇位、阴居偶位为得正）。这是段② 唯一能对整卦复算的句式，也是 T10/T11 评审 I-2
#: 那条「两处失位」（归妹实为四处）唯一的机器兜底。
_POSITION_TALLY = re.compile(r"([一两二三四五六])处(得正|失正|失位)")
_PUNCTUATION = ("，", "。", "：", "；", "、")


def test_every_stated_character_count_matches_the_anchor_length() -> None:
    """「兑卦的卦辞只有四个字」是可点数的：原文去掉标点剩几个字就是几个。句数复测 =
    `cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "import re
    from app.content.zhouyi_plain import ZHOUYI_READINGS as R;print(sum(len(re.findall(
    r'(?:卦辞|这一爻)只[有留]?[一两二三四五六]个字', v)) for v in R.values()))"`。
    T10/T11 评审实跑数出 2 句点错（`gua.58` 亨，利贞。= 三、`yao.6.5` 讼，元吉。= 三），
    而旧的清点门只看断词，看不见它。"""
    for key in _built_keys():
        anchor = ZHOUYI_ANCHORS[key]
        for m in _CHAR_COUNT.finditer(ZHOUYI_READINGS[key]):
            real = len([c for c in anchor if c not in _PUNCTUATION])
            assert _CN_COUNT[m.group(1)] == real, (
                f"{key} 说「{m.group(0)}」，anchor「{anchor}」去掉标点是 {real} 字"
            )


def test_every_stated_position_tally_matches_the_line_binaries() -> None:
    """「N处失位／得正」数的是全卦六爻里站错与站对的位置，能从 `Hexagram.lines` 现算，
    所以这句话同样是事实句而非评述。基准只有一处含糊不得：整卦，不是下卦也不是某爻
    上下——本门按整卦钉，别的读法不许用这个句式写。"""
    for key in _built_keys():
        number = int(key.split(".")[2])
        hexagram = HEXAGRAM_BY_NUMBER[number]
        misplaced = sum(
            1
            for position in range(1, 7)
            if bool(hexagram.lines[position - 1]) != (position % 2 == 1)
        )
        for m in _POSITION_TALLY.finditer(ZHOUYI_READINGS[key]):
            real = misplaced if m.group(2) != "得正" else 6 - misplaced
            assert _CN_COUNT[m.group(1)] == real, (
                f"{key} 说「{m.group(0)}」，{hexagram.name_zh} 卦画里失位 {misplaced} 爻、"
                f"得正 {6 - misplaced} 爻"
            )


#: ── Plan E 终审新增四门：钉「自述自己 anchor」那一族谎话 ──────────────────────────────
#: 这四门由 2026-10-03 丁组 spec 的**全分支终审**建：450 条今译里有六句把自己 anchor 的
#: 结构说反了，而那六个句式恰好落在计划「每批由评审员人核」的豁免里，人核那道缓解失效，
#: 终审逐句读 anchor 才抓出来。G1-G4 把可判的那四类谎话收进机器；(c) gua.36 那一类
#: 「把注释当清点句」不可从 anchor 单判，仍留人读，故不在门下。
#: 断句基准：`anchor.split("。")` 去空段——原文里一个「。」切一句，与 `「N句里」`、
#: 「中间那句」、「同一句里」这些自述句数的说法同口径。
_TWO_CHAR_ID = re.compile(r"([一-龥]{2})二字")
_NAMED_CHAR = re.compile(r"它给的([一-龥])字")
_SENTENCE_SPAN = re.compile(r"在([一两二三四五六])句里")
#: 「在N句里……各」——「各」得紧跟在同一小句里才算逐段清点，且点名的断词取该小句之前
#: 最近的「原断词是「X」」。整行别处的「各」不算：像「摆在事情前后各三天去推」这类写法
#: 把「各」用在别的东西上，若按整行判就会让这一支因为毫不相干的字而红（终审复审 F-2）。
_SPAN_EACH = re.compile(r"在[一两二三四五六]句里[^，。]*各")
_ONE_SENTENCE_ID = re.compile(r"同一句里")
_MIDDLE_SEGMENT = re.compile(r"中间那句")
_NAMED_VERDICT = re.compile(r"原断词是「([吉凶厉悔吝咎])」")


def _segments(anchor: str) -> list[str]:
    """按「。」切句、去空尾段——四门共用的断句口径。"""
    return [s for s in anchor.split("。") if s.strip()]


def test_every_two_character_identity_claim_is_contiguous_in_its_source() -> None:
    """「XY二字」是**逐字身份句**：说 anchor（或卦名）里有连着两字 XY，那 XY 必须真连着出现。
    写「小事」却称 anchor 压着「小心」就是把没在原文里的字端给了用户。条数复测（本正则同口径）：
    `cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "import re
    from app.content.zhouyi_plain import ZHOUYI_READINGS as R;print(sum(len(re.findall(r'([一-龥]{2})二字',v)) for v in R.values()))"` → 1。
    命中这一式的只有 `gua.38`（睽·小事吉。），终审正是从这里揪出「小心二字」→「小事二字」。"""
    for key in _built_keys():
        anchor = ZHOUYI_ANCHORS[key]
        name = HEXAGRAM_BY_NUMBER[int(key.split(".")[2])].name_zh
        for m in _TWO_CHAR_ID.finditer(ZHOUYI_READINGS[key]):
            pair = m.group(1)
            assert pair in anchor or pair in name, (
                f"{key} 说「{m.group(0)}」，anchor「{anchor}」卦名「{name}」里没有连着的 {pair} 二字"
            )


def test_every_named_single_character_is_in_the_anchor() -> None:
    """「它给的X字」点名 anchor 里那一个**单字**，X 就必须真在 anchor 里——这是比 G1 更窄的一式，
    只认「它给的」+ 单字 + 「字」。不复用宽度更大的 `X字` 门：全站实测 34 条用「…字」，宽的写法
    会误红约 28 条合法句（「把久字当作…」），清点那族已由 `:261` 的 `_CHAR_COUNT` 负责。条数复测：
    `cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "import re
    from app.content.zhouyi_plain import ZHOUYI_READINGS as R;print(sum(len(re.findall(r'它给的[一-龥]字',v)) for v in R.values()))"` → 1。
    命中只有 `gua.21`（噬嗑·亨，利用狱。），终审揪出「刑字」→「狱字」。"""
    for key in _built_keys():
        anchor = ZHOUYI_ANCHORS[key]
        for m in _NAMED_CHAR.finditer(ZHOUYI_READINGS[key]):
            assert m.group(1) in anchor, (
                f"{key} 说「{m.group(0)}」，anchor「{anchor}」里没有 {m.group(1)} 字"
            )


def test_every_stated_sentence_span_matches_the_anchor_segments() -> None:
    """句数自述两式，都拿 `。`-切段复算（丁组 spec §4.4「段② 只许说 anchor 里已有的结构」）：
    ①「在N句里」声称内容横跨 N 句，anchor 去空段就得 ≥N 段；若同一小句里紧跟着「各」，
      该小句之前那个 `原断词是「X」` 点名的断词就得在**恰好** N 段里出现（各 = 每段都有）。
    ②「同一句里」声称两件事挤在同一句，本门按 anchor 只有 1 段来判——把分在两句里的东西说成
      同一句，既谎报结构又和同段的「末句」自相矛盾（终审 `gua.48` 正是这句）。
    ②是**保守近似**而非定义：多段 anchor 里「这两样都在第一句」那种真话本门辨不出，一律红。
    正解是把白话改写成「两句/某句」的口径，**不是把 `== 1` 松成 `>= 1`**——松了就等于没门。
    复测（本测三正则同口径，Items 1–2 落地后）：`cd backend && PYTHONIOENCODING=utf-8
    .venv/Scripts/python.exe -c "import re;from app.content.zhouyi_plain import ZHOUYI_READINGS as
    R;print('在N句里',sum(len(re.findall(r'在[一两二三四五六]句里',v)) for v in R.values()),
    '在N句里各',sum(len(re.findall(r'在[一两二三四五六]句里[^，。]*各',v)) for v in R.values()),
    '同一句里',sum(len(re.findall('同一句里',v)) for v in R.values()))"` → 在N句里 2（`gua.48`、
    `yao.24.6`，各 2 段真话）/ 在N句里各 1（`yao.24.6`，凶在两段各有）/ 同一句里 1（`yao.7.1`
    「师出以律，否臧凶。」单段，「摆在同一句里」正是真话，此路放行）。
    终审前这两句都是谎：`gua.48` 把分在两句里的东西说成同一句、`yao.24.6` 说断词「凶」在同一句里出现两次
    （实际每段各一次），故本门落地时对这两行先红后绿。"""
    for key in _built_keys():
        anchor = ZHOUYI_ANCHORS[key]
        reading = ZHOUYI_READINGS[key]
        segs = _segments(anchor)
        for m in _SENTENCE_SPAN.finditer(reading):
            want = _CN_COUNT[m.group(1)]
            assert len(segs) >= want, (
                f"{key} 说「{m.group(0)}」，anchor「{anchor}」只有 {len(segs)} 段"
            )
            named = None
            for candidate in _NAMED_VERDICT.finditer(reading[: m.start()]):
                named = candidate
            if _SPAN_EACH.match(reading, m.start()) and named:
                hit = sum(1 for s in segs if named.group(1) in s)
                assert hit == want, (
                    f"{key} 说断词「{named.group(1)}」在 {want} 句里各一次，"
                    f"anchor「{anchor}」里它在 {hit} 段出现"
                )
        for m in _ONE_SENTENCE_ID.finditer(reading):
            assert len(segs) == 1, (
                f"{key} 说「{m.group(0)}」当作同一句，anchor「{anchor}」却有 {len(segs)} 段"
            )


def test_every_middle_segment_claim_needs_three_segments() -> None:
    """「中间那句」预设 anchor 至少三段才谈得上中间；两段就没有中间，把末句称作中间那句是错指。
    前瞻兜底门：Items 1–2 落地后全站命中归零，复测
    `cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "import re
    from app.content.zhouyi_plain import ZHOUYI_READINGS as R;print(sum(len(re.findall('中间那句',v)) for v in R.values()))"` → 0。
    终审落地前这条给 1（`gua.18`「元亨，利涉大川。先甲三日，后甲三日。」两段却把末句写成「中间那句」，
    改「末那句」后归零）；留门是为后来者再写「中间那句」而原文不足三段时立刻红。"""
    for key in _built_keys():
        anchor = ZHOUYI_ANCHORS[key]
        for m in _MIDDLE_SEGMENT.finditer(ZHOUYI_READINGS[key]):
            assert len(_segments(anchor)) >= 3, (
                f"{key} 说「{m.group(0)}」，anchor「{anchor}」只有 {len(_segments(anchor))} 段，没有中间"
            )


def test_plain_source_line_says_it_is_a_retelling_not_an_original() -> None:
    """出处串自述身份（同 `test_tarot_zh_corpus.py` 里那条译表自述的先例）。"""
    assert ZHOUYI_PLAIN_SOURCE
    assert "今译" in ZHOUYI_PLAIN_SOURCE, ZHOUYI_PLAIN_SOURCE
    for banned in ("；", "（《", "』"):
        assert banned not in ZHOUYI_PLAIN_SOURCE


def test_the_corpus_is_registered_under_its_own_name() -> None:
    """R24 形状：`PLAIN_CORPORA` 是字典字面量里的 `X.system: X`，两行 `zhouyi` 会静默留后一条，
    前一张表就此掉出机检闸外而计数照样对得上（同 `tests/test_plain_corpora.py` 那条键一致钉）。"""
    assert PLAIN_CORPORA["zhouyi"] is ZHOUYI


def test_the_registered_shape_is_sectionless_unclosed_and_unsorted() -> None:
    """spec §5 的登记形状，三个方向都不许后来者顺手改：开篇句一添就成了「页面渲染不到的小节」，
    档位句一添就是白话自己下了一句总吉凶（spec §7 规则 5「不新增判断」）。"""
    assert ZHOUYI.openers == {}
    assert ZHOUYI.closers is None
    assert ZHOUYI.grouping == "keep"


def test_the_universe_is_exactly_the_450_computed_from_the_source_tables() -> None:
    """工厂钉的是两侧**相等**，钉不出「两侧一起少」；450 这一格由本条数出来。

    条数复测：`cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "from app.engines.plain_corpora import ZHOUYI; print(len(ZHOUYI.universe()))"` → 450。
    """
    assert len(ZHOUYI.universe()) == 450
    assert ZHOUYI.universe() == set(ZHOUYI_READINGS)
    assert set(ZHOUYI_ANCHORS) == set(ZHOUYI_READINGS)


#: `zhouyi_najia` 那一条的出处串在本测里写**字面量**，是因为逐字钉一吃常量就退化成
#: 「这张元组等于它自己」——丙组终审裁定的原话：响应侧的有序断言只能钉引擎保真，
#: 钉不住登记表自身，因为 `zhouyi_provenance()` 与那条测读同一份元组。
ZHOUYI_NAJIA_SOURCE_LITERAL = "京房纳甲爻辰与六神日干起例"


def test_provenance_roster_is_the_five_rows_in_reading_order() -> None:
    """登记表由字面量钉（上一条注释）。顺序 = 页面展示序 = `zhouyi_provenance()` 的产出序。

    三条 `zhouyi_*` 的字面同时钉住了梅花那一侧：两家共用同一份常量（计划偏差表第 5 行），
    改一个值本条立刻红、`MEIHUA_CONTENT_SOURCES` 的打印也随之变（梅花那侧没有逐字钉，它的
    凭据是那份逐字节 diff 的验收命令）；抄第二份则两份各红各的，谁也不会静默漂。
    条数复测：`cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "from app.content import ZHOUYI_CONTENT_SOURCES; print(len(ZHOUYI_CONTENT_SOURCES))"` → 5。
    """
    assert ZHOUYI_CONTENT_SOURCES == (
        ("zhouyi_trigrams", "八卦卦名、卦象与邵雍先天卦序"),
        ("zhouyi_hexagrams", "《周易》通行本文王六十四卦卦序与卦画"),
        ("zhouyi_najia", ZHOUYI_NAJIA_SOURCE_LITERAL),
        ("zhouyi_text", "《周易》卦辞 · 通行本（王弼注本）公版原文"),
        ("zhouyi_plain", ZHOUYI_PLAIN_SOURCE),
    )


def test_the_shared_source_strings_are_one_copy_with_meihua() -> None:
    """偏差表第 5 行的验收：三张共用表在两份清单里逐字相等，且 `ZHOUYI_SOURCE` 就是 `zhouyi_text` 那一格。"""
    zhouyi_rows = dict(ZHOUYI_CONTENT_SOURCES)
    meihua_rows = dict(MEIHUA_CONTENT_SOURCES)
    for name in ("zhouyi_trigrams", "zhouyi_hexagrams", "zhouyi_text"):
        assert name in meihua_rows, name
        assert zhouyi_rows[name] == meihua_rows[name], name
    assert zhouyi_rows["zhouyi_text"] == ZHOUYI_SOURCE


def test_the_plain_source_line_is_the_registered_fifth_row() -> None:
    """今译表进清单（AGENTS.md §7「读了就列」）：`ZHOUYI_PLAIN_SOURCE` 的自述与登记同一笔。"""
    assert ZHOUYI_CONTENT_SOURCES[-1] == ("zhouyi_plain", ZHOUYI_PLAIN_SOURCE)
