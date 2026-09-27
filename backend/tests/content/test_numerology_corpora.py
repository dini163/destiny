"""数字命理四张语料表的不变式（spec §9.1、决策 2/12）。

这里锁的不是"表好不好看"，而是三件一旦漂移就静默出错的事：

1. **字母表两处不许各说各话**：`LETTER_VALUES`（引擎用）与 `VALUE_GROUPS`（前端渲染用）
   由同一份事实推出，双向锁死。
2. **六张释义表的键域必须正好等于算式能产出的值域**：多一个键是死数据，少一个键是
   运行时 `KeyError`。挑战表的 `{0..8}` 与流年表的"不含 33"都由算式反推，不靠记忆。
3. **洛书必须是真幻方**：八个平面正是它的八条线。设计稿的升序摆法不具幻方性质，
   照它摆等于把八个箭矢静默降级成三堆无关数字 —— 故那条摆法也在此显式判负。
"""

import pytest

from app.content.numerology_cycles import (
    CHALLENGE_DURATION,
    CHALLENGE_DURATIONS,
    CHALLENGE_MEANINGS,
    CYCLES_SOURCE,
    PERSONAL_CYCLE_MEANINGS,
    PINNACLE_AGE_RULE,
    PINNACLE_MEANINGS,
    cycles_source,
)
from app.content.numerology_loshu import (
    LOSHU_SOURCE,
    LOSHU_SQUARE,
    MISSING_NUMBER_MEANINGS,
    PLANES,
    loshu_source,
)
from app.content.numerology_meanings import (
    CORE_MEANINGS,
    KARMIC_DEBT_MEANINGS,
    KARMIC_LESSONS,
    MEANINGS_SOURCE,
    meanings_source,
)
from app.content.numerology_pythagorean import (
    KARMIC_DEBT_NUMBERS,
    LETTER_VALUES,
    MASTER_NUMBERS,
    PYTHAGOREAN_SOURCE,
    VALUE_GROUPS,
    VOWELS,
    letter_value,
)

#: 值是纯字符串的六张表；出处由模块级 `*_SOURCE` 承担，故只验非空。
PLAIN_TABLES: tuple[tuple[str, dict[int, str]], ...] = (
    ("KARMIC_LESSONS", KARMIC_LESSONS),
    ("KARMIC_DEBT_MEANINGS", KARMIC_DEBT_MEANINGS),
    ("PINNACLE_MEANINGS", PINNACLE_MEANINGS),
    ("CHALLENGE_MEANINGS", CHALLENGE_MEANINGS),
    ("PERSONAL_CYCLE_MEANINGS", PERSONAL_CYCLE_MEANINGS),
    ("MISSING_NUMBER_MEANINGS", MISSING_NUMBER_MEANINGS),
)


# ---------------------------------------------------------------- 字母表（决策 2）


def test_letter_values_domain_is_exactly_the_uppercase_alphabet() -> None:
    assert set(LETTER_VALUES) == {chr(code) for code in range(ord("A"), ord("Z") + 1)}
    assert len(LETTER_VALUES) == 26
    assert set(LETTER_VALUES.values()) <= set(range(1, 10))


def test_letter_values_and_value_groups_lock_each_other() -> None:
    """双向锁死：倒排推出的字母→值 == `LETTER_VALUES`，且每一组不多不少。"""
    from_groups = {letter: value for value, letters in VALUE_GROUPS for letter in letters}
    assert from_groups == LETTER_VALUES
    assert [value for value, _ in VALUE_GROUPS] == list(range(1, 10))
    for value, letters in VALUE_GROUPS:
        assert set(letters) == {char for char, v in LETTER_VALUES.items() if v == value}


def test_the_nine_group_has_only_two_letters() -> None:
    """26 = 9 + 9 + 8：9 一组只有 I、R。锁住它，免得有人按"每组三个"去补字母。"""
    assert dict(VALUE_GROUPS)[9] == ("I", "R")


def test_vowels_are_the_five_and_y_is_not_one_of_them() -> None:
    """Y 默认按辅音（决策 7）：它是否算元音取决于音节，而音节切分不可单测。"""
    assert VOWELS == frozenset({"A", "E", "I", "O", "U"})
    assert "Y" not in VOWELS
    assert VOWELS <= set(LETTER_VALUES)


def test_master_and_karmic_debt_sets_are_disjoint_and_exact() -> None:
    assert MASTER_NUMBERS == frozenset({11, 22, 33})
    assert KARMIC_DEBT_NUMBERS == frozenset({13, 14, 16, 19})
    assert not (MASTER_NUMBERS & KARMIC_DEBT_NUMBERS)


def test_karmic_debt_meanings_cover_exactly_the_debt_numbers() -> None:
    """双向锁死：释义表不多一键（死数据）、不少一键（运行时 `KeyError`）。

    主数与业力债是两个不相交的集合，所以一个数不可能既是主数又带业力债释义 ——
    上面那条 disjoint 断言与这一条合起来把「13 算不算主数」这类模糊永久排除。
    """
    assert set(KARMIC_DEBT_MEANINGS) == set(KARMIC_DEBT_NUMBERS)
    assert not (set(KARMIC_DEBT_MEANINGS) & set(CORE_MEANINGS))


def test_letter_value_is_case_insensitive_and_rejects_non_letters() -> None:
    assert letter_value("a") == letter_value("A") == 1
    assert letter_value("z") == 8
    # 抛错而不返回 0：静默返回 0 会让"名字里没有拉丁字母"变成一次看似成功的全零计算。
    for bad in ("1", " ", "-", "'", ".", "陆", ""):
        with pytest.raises(KeyError):
            letter_value(bad)


# ---------------------------------------------------------------- 释义表键域（§5.2/§5.3/§5.4）


def test_core_meanings_domain_is_exactly_the_twelve() -> None:
    assert set(CORE_MEANINGS) == set(range(1, 10)) | set(MASTER_NUMBERS)
    assert len(CORE_MEANINGS) == 12


def test_karmic_lessons_domain_is_one_to_nine() -> None:
    assert set(KARMIC_LESSONS) == set(range(1, 10))


def test_pinnacle_domain_covers_masters_because_pinnacles_keep_them() -> None:
    assert set(PINNACLE_MEANINGS) == set(range(1, 10)) | set(MASTER_NUMBERS)


def test_challenge_domain_is_exactly_what_the_formula_can_produce() -> None:
    """挑战是两个月/日/年**约简后**单数字（各在 1..9）的绝对差，故值域只能是 0..8。

    由算式反推键域，而不是照记忆写 `{0..8}`：这样一旦有人改了挑战公式，这条测试会
    先炸，而不是等到线上 `KeyError`。0 必须在表内 —— Decoz 原文「The 0 (zero)
    Challenge is very common」。
    """
    reachable = {abs(a - b) for a in range(1, 10) for b in range(1, 10)}
    assert reachable == set(range(0, 9))
    assert set(CHALLENGE_MEANINGS) == reachable
    # 第三挑战是 |C1−C2|，两个操作数已在 0..8 里，值域不会因此变宽。
    assert {abs(a - b) for a in reachable for b in reachable} == reachable


def _reduce_keeping_masters(total: int) -> int:
    """测试自带的约简神谕：故意独立于引擎重写一次，否则这条测只是在测它自己。"""
    while total >= 10 and total not in MASTER_NUMBERS:
        total = sum(int(char) for char in str(total))
    return total


def test_personal_cycle_domain_is_exactly_what_the_chained_sum_can_reach() -> None:
    """键域由算式反推，不靠记忆：加数各自保留主数（决策 3），相加后也保留主数。

    于是每个加数 ∈ `{1..9, 11, 22, 33}`，落点也只可能是这一批 —— 33 真凑得出来
    （`9 + 2 + 22`、`11 + 11 + 11`）。初稿写的是 `{1..9,11,22}`，理由「三个加数各 ≤9」
    与决策 3 直接冲突，故按决策 3 补齐（偏差记在 spec §5.3）。少一个键就是一次
    生产上的 `KeyError`，而它只在罕见的生日 + 罕见的基准年凑到一起时才爆。
    流月/流日只有两个加数，值域更窄，故一并锁在这条里。
    """
    addends = set(range(1, 10)) | set(MASTER_NUMBERS)
    reachable = {
        _reduce_keeping_masters(a + b + c) for a in addends for b in addends for c in addends
    }
    assert reachable == addends
    assert set(PERSONAL_CYCLE_MEANINGS) == reachable
    two_addends = {_reduce_keeping_masters(a + b) for a in addends for b in addends}
    assert two_addends <= reachable, "流月/流日共用这张表，值域必须被它盖住"
    assert set(PERSONAL_CYCLE_MEANINGS) <= set(CORE_MEANINGS)


#: 年尺度的字眼。这张表被流年/流月/流日三处共用，故其中任何一个都是错的：
#: 印到流月卡上，「新周期第一年…决定后八年」就成了「这个月决定后八年」。
#: 尺度只能由卡片自己的 `label` 提供（个人流年 / 个人流月 / 个人流日），
#: 不能藏在释义正文里 —— 正文里的尺度词看上去完全像一句真结论，而它只在
#: 三种尺度中的一种上为真。
YEAR_SCALE_WORDS = ("之年", "第一年", "九年", "明年", "今年", "本年", "去年", "前几年", "后八年")


def test_personal_cycle_meanings_hold_at_every_scale() -> None:
    """共用表的每条释义必须在年/月/日三种尺度上同时为真（按字眼拦，不靠读）。"""
    for number, text in PERSONAL_CYCLE_MEANINGS.items():
        for word in YEAR_SCALE_WORDS:
            assert word not in text, (
                f"{number} 的释义带年尺度字眼「{word}」：流月/流日也在用这张表，"
                "印过去就是假话；尺度该由 label 说，不该写进正文"
            )


def test_challenge_durations_are_the_source_intervals_split_per_challenge() -> None:
    """四个挑战各自回显来源的定性时段；值必须是 `CHALLENGE_DURATION` 原文的片段。

    片段式锁法而不是只验非空：「另编一个确切年份」是这张表唯一可能的坏法，
    而它看上去完全像一条真结论。片段必须是原文子串，编不进去。
    """
    assert set(CHALLENGE_DURATIONS) == {"first", "second", "main", "fourth"}
    for key, text in CHALLENGE_DURATIONS.items():
        assert text.strip(), f"{key} 的时段文本是空的"
        assert text in CHALLENGE_DURATION, f"{key} 的时段必须是规则原文的片段"
    assert "贯穿一生" in CHALLENGE_DURATIONS["main"]
    for key in ("first", "second", "fourth"):
        assert "约" in CHALLENGE_DURATIONS[key], f"{key} 是区间而不是确年，得带「约」"


def test_loshu_missing_meanings_domain_is_one_to_nine() -> None:
    assert set(MISSING_NUMBER_MEANINGS) == set(range(1, 10))


def test_master_entries_carry_root_and_title_and_the_rest_do_not() -> None:
    roots = {11: 2, 22: 4, 33: 6}
    for number, entry in CORE_MEANINGS.items():
        if number in MASTER_NUMBERS:
            assert entry.root == roots[number], f"{number} 的根应是 {roots[number]}"
            assert entry.master_title and "·" in entry.master_title
        else:
            assert entry.root == number
            # 非主数没有称号；`None` 而不是空串，前端据此整块不渲染。
            assert entry.master_title is None


#: spec §5.2 印出的那一行（"如 33 → `MASTER TEACHER · 精神导师`"）。上一条只管「有没有
#: 称号」这一维，它的非主数分支（`is None`）顺带锁住了「有称号 ⟺ 是主数」；三个称号
#: **到底是哪三串字**，在本仓的全部命中处就是下面这张表与 `tests/test_numerology_api.py`
#: 的那一句（复测：`grep -rl --include=*.py "MASTER \(INTUITION\|BUILDER\|TEACHER\)" tests/`）。
#: 字面量值得钉的理由在页面上：`CoreNumberHero.tsx:30-32` 与 `CoreNumberCard.tsx:65-67`
#: 的渲染条件是 `is_master && card.master_title`，两者同时为真才印那一行 —— 于是称号一旦
#: 被改写（哪怕只是「灵性直觉者」缩成「直觉者」），角标照印，读者看到的却是书里查不到的
#: 名字，而这条链上没有任何一处会报错。
MASTER_TITLE_TEXTS: dict[int, str] = {
    11: "MASTER INTUITION · 灵性直觉者",
    22: "MASTER BUILDER · 宏图建构者",
    33: "MASTER TEACHER · 精神导师",
}


def test_master_titles_are_the_three_the_spec_prints() -> None:
    """三个称号逐字对回 spec。集合方向上它只补一个洞：`MASTER_NUMBERS` 添员时释义必须跟上。

    「给 7 编一个称号」那种红不归这里 —— 上面那条的非主数分支（`master_title is None`）
    已经守着它了；本条的键域等式管的是另一头：有人把 44 加进主数集并补了释义，
    却没人核对那一串字该印成什么，页面上就会多出一个来路不明的称号。
    """
    assert set(MASTER_TITLE_TEXTS) == set(MASTER_NUMBERS)
    for number, text in MASTER_TITLE_TEXTS.items():
        assert CORE_MEANINGS[number].master_title == text, f"数 {number} 的称号不是这一串"


def test_every_core_entry_is_filled_and_cited() -> None:
    for number, entry in CORE_MEANINGS.items():
        assert entry.number == number
        assert entry.essence.strip(), f"数 {number} 的本质是空的"
        assert entry.talent.strip() and entry.challenge.strip()
        assert 3 <= len(entry.keywords) <= 5, f"数 {number} 的关键词应是 3–5 个"
        assert all(keyword.strip() for keyword in entry.keywords)
        assert "非古籍" in entry.source


@pytest.mark.parametrize("label,table", PLAIN_TABLES)
def test_every_plain_meaning_is_filled(label: str, table: dict[int, str]) -> None:
    for key, text in table.items():
        assert text.strip(), f"{label}[{key}] 是空的"


# ---------------------------------------------------------------- 洛书幻方（决策 12）


def _lines(square: tuple[tuple[int, int, int], ...]) -> list[tuple[int, ...]]:
    """三行 + 三列 + 两对角线，共八条线。"""
    rows = [tuple(row) for row in square]
    cols = [tuple(square[r][c] for r in range(3)) for c in range(3)]
    main_diagonal = tuple(square[i][i] for i in range(3))
    anti_diagonal = tuple(square[i][2 - i] for i in range(3))
    return [*rows, *cols, main_diagonal, anti_diagonal]


def test_loshu_square_uses_each_digit_exactly_once() -> None:
    assert sorted(n for row in LOSHU_SQUARE for n in row) == list(range(1, 10))


def test_loshu_square_is_a_magic_square_of_fifteen() -> None:
    assert {sum(line) for line in _lines(LOSHU_SQUARE)} == {15}


def test_planes_are_exactly_the_eight_lines_no_more_no_less() -> None:
    assert len(PLANES) == 8
    assert {frozenset(plane.cells) for plane in PLANES} == {
        frozenset(line) for line in _lines(LOSHU_SQUARE)
    }
    assert len({plane.key for plane in PLANES}) == 8


def test_the_mockup_ascending_layout_is_not_a_magic_square() -> None:
    """设计稿把九宫画成 `3 6 9 / 2 5 8 / 1 4 7`，行和是 18/15/12。

    留着这条判负，是为了让"改回设计稿摆法"在 CI 上立刻炸，而不是静默把八个箭矢
    降级成三堆无关数字（spec 决策 12、§2.6）。
    """
    mockup = ((3, 6, 9), (2, 5, 8), (1, 4, 7))
    assert {sum(line) for line in _lines(mockup)} != {15}
    assert LOSHU_SQUARE != mockup


def test_every_plane_is_filled_and_cited() -> None:
    for plane in PLANES:
        assert plane.key.strip() and plane.name_zh.strip() and plane.name_en.strip()
        assert plane.present_text.strip() and plane.missing_text.strip()
        assert len(set(plane.cells)) == 3, f"{plane.key} 的三个构成数字必须互异"
        assert "非古籍" in plane.source


def test_will_plane_is_the_one_the_mockup_got_right() -> None:
    """设计稿唯一活下来的断言：意志之箭 9-5-1（spec §2.4 末行）。"""
    will = next(plane for plane in PLANES if plane.key == "will")
    assert will.cells == (9, 5, 1)


# ---------------------------------------------------------------- 出处诚实（§5）


@pytest.mark.parametrize(
    "source",
    [PYTHAGOREAN_SOURCE, MEANINGS_SOURCE, CYCLES_SOURCE, LOSHU_SOURCE],
)
def test_every_table_source_declares_it_is_not_a_classic(source: str) -> None:
    """四张表都没有古籍依据；出处必须自认，不能让表看起来比它实际更有出处。"""
    assert "非古籍" in source


def test_loshu_source_also_declares_it_is_not_pythagorean() -> None:
    """洛书八平面属印度数理传统，混进毕达哥拉斯体系就是张冠李戴（spec §11 风险 3）。"""
    assert "非毕达哥拉斯" in LOSHU_SOURCE


def test_cycle_rule_texts_are_qualitative_and_never_claim_exact_years() -> None:
    """挑战时段来源给的本就是区间，印成确数等于编数据（spec §5.3）。"""
    assert "36" in PINNACLE_AGE_RULE and "终身" in PINNACLE_AGE_RULE
    assert "区间而非确年" in CHALLENGE_DURATION
    assert "30–35" in CHALLENGE_DURATION and "45–50" in CHALLENGE_DURATION


def test_entry_sources_keep_the_entry_inside_the_visible_chip() -> None:
    """条目名必须排在限定语之前：前端角标只印第一个「（」之前的那半句。

    `f"{CYCLES_SOURCE}·顶峰1"` 与 `cycles_source("顶峰1")` 语义一模一样，tooltip 里也
    照样看得见条目名 —— 坏法只在前端那一刀上：角标被限定语截断，于是顶峰卡上并列的
    「顶峰1」与「挑战0」印成两个一模一样的角标，洛书那八个平面也共用一句书名。
    语义没丢，丢的是页面上看得见的可分辨性，而它看上去完全不像个 bug。
    """
    for make, entries in (
        (meanings_source, ("数6", "业力债13", "业力课4")),
        (cycles_source, ("顶峰1", "挑战0", "个人周期11")),
        (loshu_source, ("Will", "缺数3", "缺数7")),
    ):
        chips = [make(entry).split("（")[0] for entry in entries]
        for entry, chip in zip(entries, chips, strict=True):
            assert entry in chip, f"{entry} 被限定语挤出了角标"
        assert len(set(chips)) == len(chips), f"角标撞车，读者分不出哪条引哪条：{chips}"
        # 拼条目名不许把「自认非古籍」那半句弄丢 —— 它是这四张表的诚实底线。
        assert all("非古籍" in make(entry) for entry in entries)
