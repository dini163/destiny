"""数字命理引擎的性质测（spec §9.2）。

这里断言的是**结构性质** —— 换任何输入都该成立的那些；某个人的具体数字归
`tests/golden/`。性质测是本系统的主要防线：数字命理没有天文库可依赖，也没有 mock
可躲，算错了就是静默地印出一个看似合理的数。只有不变式能抓住它。

设计稿就是活例：它把表达数、灵魂冲动数、人格面具数三个全印错了，而「元音和 + 辅音和
== 全字母和」这一条性质一眼就能揭穿（16 + 34 = 50，而稿子印的 9 与 2 加起来根本不是
11）。故那条不变式排在最前面。
"""

from __future__ import annotations

import re
from collections.abc import Callable
from datetime import date, timedelta

import pytest

from app.content.numerology_cycles import (
    CHALLENGE_DURATION,
    CHALLENGE_DURATIONS,
    CHALLENGE_MEANINGS,
    PERSONAL_CYCLE_MEANINGS,
    PINNACLE_MEANINGS,
    cycles_source,
)
from app.content.numerology_loshu import LOSHU_SQUARE, PLANES, loshu_source
from app.content.numerology_meanings import (
    CORE_MEANINGS,
    KARMIC_LESSONS,
    CoreMeaning,
    meanings_source,
)
from app.content.numerology_pythagorean import (
    KARMIC_DEBT_NUMBERS,
    LETTER_VALUES,
    MASTER_NUMBERS,
    VOWELS,
)
from app.core.errors import NumerologyInputError
from app.engines.numerology import (
    CHALLENGE_KEYS,
    CORE_KEYS,
    NUMEROLOGY_SUMMARY_FRAME,
    PINNACLE_KEYS,
    CoreResult,
    age_at,
    challenges,
    compute_chart,
    core_numbers,
    current_pinnacle,
    loshu_grid,
    name_grid,
    numerology_plain_summary,
    personal_cycles,
    pinnacles,
    reduce_number,
    split_letters,
)
from app.schemas.numerology import CoreNumber, PersonalCycle, PersonalCycles
from tests.plain_wording import ADVICE_TOKENS, FORBIDDEN, advice_hits

#: 覆盖各种边界：空格、连字符、撇号、含 Y、无元音、无辅音、单字母、全小写。
NAMES: tuple[str, ...] = (
    "LU QINGXUAN",
    "Anna",
    "Jean-Luc Picard",
    "O'Brien",
    "Yvonne",
    "Lynn",
    "Aia",
    "li xiao long",
    "X",
)

BIRTH = date(1994, 5, 14)

#: 个人周期的基准日。显式传参才确定（缺省取今天，那是给真请求用的）。
REFERENCE = date(2026, 9, 24)


def _spread(start: date, count: int, step_days: int) -> tuple[date, ...]:
    """一份确定性的生日样本：跨度约九十年，够把值域与边界都扫到。"""
    return tuple(start + timedelta(days=step_days * index) for index in range(count))


MANY_BIRTHS: tuple[date, ...] = _spread(date(1930, 1, 7), 120, 271)


def _digit_sum(total: int) -> int:
    """测试用的算式神谕：故意独立于引擎重写一遍，否则这条测只是在测它自己。"""
    return sum(int(char) for char in str(total))


def _by_key(result: CoreResult) -> dict[str, CoreNumber]:
    return {item.key: item for item in result.core}


# ------------------------------------------------------------------ 约简原语（§6.1）


@pytest.mark.parametrize(
    ("total", "value", "root"),
    [
        (5, 5, 5),
        (15, 6, 6),
        (11, 11, 2),
        (22, 22, 4),
        (33, 33, 6),
        (16, 7, 7),
        (50, 5, 5),
        # 下面三个是 spec §2.3 里 Decoz 亲自印出的约简链，逐格对得上才算过。
        (1994, 5, 5),
        (1990, 1, 1),
        (1998, 9, 9),
    ],
)
def test_reduce_number_keeps_masters_by_default(total: int, value: int, root: int) -> None:
    reduced = reduce_number(total)
    assert (reduced.value, reduced.root) == (value, root)


@pytest.mark.parametrize(("total", "value"), [(11, 2), (22, 4), (33, 6)])
def test_masters_survive_only_when_asked(total: int, value: int) -> None:
    """`keep_master=False` 是全系统唯一的例外通道，只给四挑战用（决策 3）。"""
    assert reduce_number(total, keep_master=False).value == value
    assert reduce_number(total).value == total


@pytest.mark.parametrize("total", [0, -1, -16])
def test_reduce_number_refuses_a_non_positive_total(total: int) -> None:
    """拒收而不是返回 0（决策 17）：静默返回 0 会变成一个查无释义的"0 数核心数"。"""
    with pytest.raises(ValueError):
        reduce_number(total)


@pytest.mark.parametrize("total", [*range(1, 60), 1990, 1994, 1998, 2026])
def test_every_step_is_checkable_with_a_calculator(total: int) -> None:
    """账本自洽：每一行要么原样（已是终值），要么真的等于把 `total` 的各位相加。"""
    reduced = reduce_number(total)
    assert reduced.steps, "每一步约简都要进账本（决策 5），账本不许为空"
    assert reduced.steps[0].total == total
    assert reduced.steps[-1].reduced == reduced.value
    for step in reduced.steps:
        if step.reduced == step.total:
            assert step.total < 10 or step.total in MASTER_NUMBERS
        else:
            assert step.reduced == _digit_sum(step.total)
    for previous, current in zip(reduced.steps, reduced.steps[1:]):
        assert current.total == previous.reduced, "账本必须首尾相接，不许跳步"


@pytest.mark.parametrize("total", [*range(1, 60), 1990, 1994, 1998])
def test_root_is_always_a_single_digit(total: int) -> None:
    reduced = reduce_number(total)
    assert 1 <= reduced.root <= 9
    if reduced.value < 10:
        assert reduced.root == reduced.value
    else:
        assert reduced.value in MASTER_NUMBERS
        assert reduced.root == _digit_sum(reduced.value)


@pytest.mark.parametrize("total", range(1, 200))
def test_every_total_lands_in_the_meaning_table(total: int) -> None:
    """约简的落点必须永远查得到释义，否则引擎会在线上 `KeyError`。"""
    assert reduce_number(total).value in CORE_MEANINGS


def test_label_reaches_every_row_of_the_ladder() -> None:
    assert {step.label for step in reduce_number(1990, label="年").steps} == {"年"}


def test_expression_override_rewrites_only_the_first_row() -> None:
    """相加行要印 `5+5+5`（对得上上一行），而不是把 15 拆成 `1+5`（spec §6.1 补记）。"""
    assert reduce_number(15, label="相加").steps[0].expression == "1+5"
    overridden = reduce_number(15, label="相加", expression="5+5+5")
    assert overridden.steps[0].expression == "5+5+5"
    assert overridden.value == 6
    # 多行的链上，覆盖只作用于第一行，后续仍按位拆解。
    chained = reduce_number(1990, label="年", expression="1+9+9+0")
    assert [step.expression for step in chained.steps] == ["1+9+9+0", "1+9", "1+0"]


@pytest.mark.parametrize("total", sorted(KARMIC_DEBT_NUMBERS))
def test_a_debt_number_is_flagged_only_when_detection_is_on(total: int) -> None:
    steps = reduce_number(total, detect_karmic_debt=True).steps
    assert steps[0].total == total and steps[0].karmic_debt
    assert not any(step.karmic_debt for step in reduce_number(total).steps)


# ------------------------------------------------------------------ 姓名拆字（决策 7/8）


@pytest.mark.parametrize("name", NAMES)
def test_vowel_and_consonant_totals_sum_to_the_letter_total(name: str) -> None:
    """毕达哥拉斯体系的结构性质，也是抓设计稿三处印错的那把尺（spec §6.2）。"""
    letters = split_letters(name)
    assert letters.vowel_total + letters.consonant_total == letters.letter_total


@pytest.mark.parametrize("name", NAMES)
def test_split_letters_agrees_with_the_corpus_table(name: str) -> None:
    """字母值只认语料表；引擎不许自带第二份映射。"""
    letters = split_letters(name)
    expected = [LETTER_VALUES[char] for char in name.upper() if char in LETTER_VALUES]
    assert [item.value for item in letters.letters] == expected
    assert letters.letter_total == sum(expected)


@pytest.mark.parametrize("name", NAMES)
def test_vowel_flags_follow_the_toggle(name: str) -> None:
    default = split_letters(name)
    flipped = split_letters(name, y_as_vowel=True)
    assert len(default.letters) == len(flipped.letters)
    for left, right in zip(default.letters, flipped.letters, strict=True):
        assert left.char == right.char and left.value == right.value
        if left.char == "Y":
            assert not left.is_vowel and right.is_vowel
        else:
            assert left.is_vowel == right.is_vowel == (left.char in VOWELS)


@pytest.mark.parametrize("name", ["Anna", "LU QINGXUAN", "O'Brien"])
def test_the_y_toggle_is_inert_without_a_y(name: str) -> None:
    assert "Y" not in name.upper()
    assert split_letters(name) == split_letters(name, y_as_vowel=True)


@pytest.mark.parametrize("name", ["Lynn", "Yvonne", "Bryan"])
def test_the_y_toggle_moves_the_totals_in_opposite_directions(name: str) -> None:
    assert "Y" in name.upper()
    default = split_letters(name)
    flipped = split_letters(name, y_as_vowel=True)
    assert flipped.vowel_total > default.vowel_total
    assert flipped.consonant_total < default.consonant_total
    assert flipped.vowel_total - default.vowel_total == (
        default.consonant_total - flipped.consonant_total
    )
    # 全字母总和与 Y 的身份无关：它只是从一列挪到另一列。
    assert flipped.letter_total == default.letter_total


@pytest.mark.parametrize(
    ("name", "skipped"),
    [
        ("LU QINGXUAN", (" ",)),
        ("Jean-Luc Picard", (" ", "-")),
        ("O'Brien", ("'",)),
        ("Anna", ()),
    ],
)
def test_non_letters_are_skipped_and_counted_honestly(name: str, skipped: tuple[str, ...]) -> None:
    letters = split_letters(name)
    assert letters.skipped_chars == skipped
    assert letters.skipped_count == sum(name.count(char) for char in skipped)
    assert len(letters.letters) + letters.skipped_count == len(name)


@pytest.mark.parametrize("name", ["陆青玄", "陸青玄", "12345", "!!!", "   ", "アキラ", ""])
def test_a_name_without_latin_letters_is_a_domain_error(name: str) -> None:
    """纯中文名过得了 pydantic 的长度校验，坏的是字符集前提，故归引擎（spec §7）。"""
    with pytest.raises(NumerologyInputError) as excinfo:
        split_letters(name)
    error = excinfo.value
    assert error.code == "numerology_no_latin_letters"
    assert error.status_code == 422
    assert error.context is not None
    assert error.context["field"] == "full_name"
    assert isinstance(error.context["chars"], list)


def test_the_error_context_carries_the_offending_characters() -> None:
    """`context` 是给机器的：前端据它提示「请改用拼音」，而不是去解析文案。"""
    with pytest.raises(NumerologyInputError) as excinfo:
        split_letters("陆青玄")
    assert excinfo.value.context is not None
    assert excinfo.value.context["chars"] == ["陆", "青", "玄"]


# ------------------------------------------------------------------ 六个核心数（§6.2）


def test_core_numbers_come_in_a_fixed_order() -> None:
    result = core_numbers("LU QINGXUAN", BIRTH)
    assert CORE_KEYS == (
        "life_path",
        "expression",
        "soul_urge",
        "personality",
        "birthday",
        "maturity",
    )
    assert [item.key for item in result.core] == list(CORE_KEYS)


@pytest.mark.parametrize("name", NAMES)
def test_every_core_number_is_fully_auditable(name: str) -> None:
    result = core_numbers(name, BIRTH)
    for item in result.core:
        assert item.label.strip() and item.source.strip()
        if item.value is None:
            # 决策 17：算不出就整块留空，绝不填 0 冒充一个数。
            assert item.unavailable_reason
            assert not item.steps and not item.keywords
            assert item.root is None and item.meaning is None
            assert item.talent is None and item.challenge is None
            assert item.master_title is None and not item.is_master
            continue
        assert item.unavailable_reason is None
        assert item.value in CORE_MEANINGS
        assert item.root is not None and 1 <= item.root <= 9
        assert item.is_master == (item.value in MASTER_NUMBERS)
        assert (item.master_title is not None) == item.is_master
        assert item.meaning and item.talent and item.challenge and item.keywords
        assert item.steps and item.steps[-1].reduced == item.value


def test_a_name_without_vowels_leaves_soul_urge_unavailable() -> None:
    result = core_numbers("Lynn", date(1990, 1, 1))
    core = _by_key(result)
    assert core["soul_urge"].value is None
    assert core["soul_urge"].unavailable_reason
    # 其余五个照算：一格算不出不等于整盘失败。
    assert all(core[key].value is not None for key in CORE_KEYS if key != "soul_urge")


def test_a_name_without_consonants_leaves_personality_unavailable() -> None:
    result = core_numbers("Aia", date(1990, 1, 1))
    core = _by_key(result)
    assert core["personality"].value is None
    assert core["soul_urge"].value is not None


@pytest.mark.parametrize("name", NAMES)
def test_the_two_zero_totals_cannot_happen_at_once(name: str) -> None:
    """请求已保证至少一个拉丁字母，故它要么进元音列要么进辅音列，两列不可能同时空。"""
    core = _by_key(core_numbers(name, BIRTH))
    assert core["soul_urge"].value is not None or core["personality"].value is not None


@pytest.mark.parametrize(
    ("birth", "expected"),
    [
        (date(1994, 5, 14), 5),
        (date(1990, 8, 11), 11),
        (date(1990, 8, 22), 22),
        (date(1998, 10, 15), 6),
    ],
)
def test_birthday_number_is_just_the_reduced_day(birth: date, expected: int) -> None:
    """生日数是六个核心数里唯一可能"就是主数本身"的：11 日 → 11，不约简（spec §6.2）。"""
    core = _by_key(core_numbers("Anna", birth))
    assert core["birthday"].value == expected


@pytest.mark.parametrize("name", NAMES)
def test_maturity_is_the_sum_of_life_path_and_expression(name: str) -> None:
    core = _by_key(core_numbers(name, BIRTH))
    expected = reduce_number(core["life_path"].value + core["expression"].value)
    assert core["maturity"].value == expected.value
    assert core["maturity"].root == expected.root


def test_karmic_debt_comes_from_the_life_path_sum_row() -> None:
    """Decoz 的原例：1998-10-15 → `1+6+9=16`，生命灵数 7 且带 16 业力债（spec §2.3）。"""
    result = core_numbers("Anna", date(1998, 10, 15))
    assert [debt.number for debt in result.karmic_debts] == [16]
    assert result.karmic_debts[0].meaning.strip()
    life_path = result.core[0]
    assert life_path.value == 7
    assert [step.karmic_debt for step in life_path.steps].count(True) == 1


def test_a_year_passing_through_nineteen_is_not_a_karmic_debt() -> None:
    """锁"不多报"：1990 约简途中出现 19，但业力债只认相加行（spec §6.8）。

    不锁这条，把 `detect_karmic_debt` 默认打开就会静默多出一个 Decoz 本人也没报的
    业力债 —— 而它在页面上看起来完全像一个真结论。
    """
    result = core_numbers("Anna", date(1990, 8, 12))
    assert result.karmic_debts == ()
    assert result.core[0].value == 3


@pytest.mark.parametrize(
    "variant", ["LUQINGXUAN", "lu qingxuan", "Lu QingXuan", "LU-QINGXUAN", "LU.QINGXUAN"]
)
def test_core_numbers_ignore_case_and_separators(variant: str) -> None:
    """字母值与它出现在名字里的位置无关，故分隔符只改跳过计数，不改任何数。"""
    baseline = [item.value for item in core_numbers("LUQINGXUAN", BIRTH).core]
    assert [item.value for item in core_numbers(variant, BIRTH).core] == baseline


def test_the_engine_is_deterministic() -> None:
    """无天文、无随机、无外部依赖：同输入必须同输出，这是本系统的立身之本（spec §1）。"""
    first = core_numbers("LU QINGXUAN", BIRTH)
    second = core_numbers("LU QINGXUAN", BIRTH)
    assert first == second


# ------------------------------------------------------------------ 周岁（§6.3）


@pytest.mark.parametrize(
    ("birth", "reference", "expected"),
    [
        (date(1994, 5, 14), date(1994, 5, 14), 0),
        (date(1994, 5, 14), date(1994, 5, 13), None),
        (date(1994, 5, 14), date(1993, 12, 31), None),
        (date(1994, 5, 14), date(2024, 5, 13), 29),
        (date(1994, 5, 14), date(2024, 5, 14), 30),
        (date(1994, 5, 14), date(2024, 12, 31), 30),
        (date(2000, 2, 29), date(2024, 2, 28), 23),
        (date(2000, 2, 29), date(2024, 2, 29), 24),
        (date(2000, 2, 29), date(2023, 3, 1), 23),
    ],
)
def test_age_at_is_completed_years_or_none(
    birth: date, reference: date, expected: int | None
) -> None:
    """周岁。基准日早于生日时是 `None` —— 填 0 会读成「刚出生」，填负数更荒唐。"""
    assert age_at(birth, reference) == expected


# ------------------------------------------------------------------ 四顶峰（§6.3）


#: (生日, 四顶峰值, 第一顶峰终止年龄)。三例有外部出处：主角见 spec §2.4，
#: 另两例是 Decoz 亲自印出的算例 A/B（§2.3）。
PINNACLE_CASES: tuple[tuple[date, tuple[int, int, int, int], int], ...] = (
    (date(1994, 5, 14), (1, 1, 2, 1), 30),
    (date(1990, 8, 12), (11, 4, 6, 9), 33),
    (date(1998, 10, 15), (7, 6, 4, 1), 29),
    (date(1998, 9, 27), (9, 9, 9, 9), 27),
)


@pytest.mark.parametrize(("birth", "values", "first_end"), PINNACLE_CASES)
def test_pinnacle_values_follow_the_decoz_formulas(
    birth: date, values: tuple[int, int, int, int], first_end: int
) -> None:
    """`P1=M+D`、`P2=D+Y`、`P3=P1+P2`、`P4=M+Y`，基底与各和都先约简（保留主数）。

    期望值由测试自己再走一遍 `reduce_number` 得出，不是把实现的结果抄成期望 ——
    抄过来的期望值只能证明实现与它自己一致。
    """
    month = reduce_number(birth.month).value
    day = reduce_number(birth.day).value
    year = reduce_number(birth.year).value
    first = reduce_number(month + day).value
    second = reduce_number(day + year).value
    third = reduce_number(first + second).value
    fourth = reduce_number(month + year).value
    expected = (first, second, third, fourth)
    items = pinnacles(birth, reference_date=birth)
    assert [item.key for item in items] == list(PINNACLE_KEYS)
    assert [item.index for item in items] == [1, 2, 3, 4]
    assert tuple(item.value for item in items) == values == expected
    assert items[0].end_age == first_end


@pytest.mark.parametrize(("birth", "values", "first_end"), PINNACLE_CASES)
def test_the_pinnacle_age_axis_is_derived_from_the_life_path_root(
    birth: date, values: tuple[int, int, int, int], first_end: int
) -> None:
    """`first_end = 36 − root(LifePath)`，其后 P2/P3 各九年，P4 无终点（`None`，不填 999）。"""
    items = pinnacles(birth, reference_date=birth)
    life_root = _by_key(core_numbers("Anna", birth))["life_path"].root
    assert items[0].start_age == 0
    assert items[0].end_age == 36 - life_root == first_end
    assert items[1].start_age == items[0].end_age + 1
    assert items[1].end_age == items[0].end_age + 9
    assert items[2].start_age == items[1].end_age + 1
    assert items[2].end_age == items[1].end_age + 9
    assert items[3].start_age == items[2].end_age + 1
    assert items[3].end_age is None


@pytest.mark.parametrize("birth", MANY_BIRTHS)
def test_the_pinnacle_axis_has_no_gap_and_no_overlap(birth: date) -> None:
    """年龄轴必须铺满一生：不许留洞（有岁数落不到任何一段），也不许重叠（落进两段）。"""
    items = pinnacles(birth, reference_date=birth)
    for previous, current in zip(items, items[1:]):
        assert current.start_age == previous.end_age + 1
    assert items[0].start_age == 0 and items[3].end_age is None
    for item in items:
        assert item.value in PINNACLE_MEANINGS
        assert item.is_master == (item.value in MASTER_NUMBERS)
        assert item.root == reduce_number(item.value, keep_master=False).value
        assert item.label and item.expression and item.meaning and item.source


def test_pinnacles_keep_master_numbers() -> None:
    """Decoz 算例 A 的 P1 = 8 + 3 = 11：主数原样保留，`root` 另给 2（决策 3）。"""
    first = pinnacles(date(1990, 8, 12), reference_date=date(1990, 8, 12))[0]
    assert (first.value, first.root, first.is_master) == (11, 2, True)
    assert first.meaning == PINNACLE_MEANINGS[11]


def test_the_pinnacle_expression_carries_the_whole_chain() -> None:
    """顶峰卡不带 `steps`，账本就只能压在算式里：基底印完整约简链，和印出是否再约。

    少印一环，读者就得自己重算 —— 而「没人能复核」正是设计稿那些数的病根（spec §2.4）。
    """
    items = pinnacles(BIRTH, reference_date=BIRTH)
    assert items[0].expression == "月 5 + 日 14→5 = 10 → 1"
    assert items[2].expression == "第一顶峰 1 + 第二顶峰 1 = 2"
    decos_a = pinnacles(date(1990, 8, 12), reference_date=date(1990, 8, 12))
    # 主数是和本身，故末尾没有约简箭头 —— 箭头只在真的约了的时候出现。
    assert decos_a[0].expression == "月 8 + 日 12→3 = 11"
    assert decos_a[2].expression == "第一顶峰 11 + 第二顶峰 4 = 15 → 6"


#: (基准日, 落在哪一程)。主角的年龄轴是 0-30 / 31-39 / 40-48 / 49+（spec §2.4）。
CURRENT_CASES: tuple[tuple[date, str | None], ...] = (
    (date(1994, 5, 14), "first"),
    (date(2024, 5, 13), "first"),
    (date(2024, 5, 14), "first"),
    (date(2025, 5, 14), "second"),
    (date(2033, 5, 14), "second"),
    (date(2034, 5, 14), "third"),
    (date(2042, 5, 14), "third"),
    (date(2043, 5, 14), "fourth"),
    (date(2120, 1, 1), "fourth"),
    (date(1990, 1, 1), None),
)


@pytest.mark.parametrize(("reference", "key"), CURRENT_CASES)
def test_the_current_pinnacle_is_the_one_the_reference_date_falls_in(
    reference: date, key: str | None
) -> None:
    """`current_pinnacle` 读的是响应里印出的 `start_age/end_age`，与 `is_current` 对拍。

    两者一致才算数：只测标记，就测不出「轴改了而标记没跟着改」；只测查找，就测不出
    标记本身错。落不到任何一段（基准日早于生日 → 周岁未知）时必须是 `None`。
    """
    items = pinnacles(BIRTH, reference_date=reference)
    current = current_pinnacle(items, age_at(BIRTH, reference))
    assert (current.key if current else None) == key
    assert [item.key for item in items if item.is_current] == ([key] if key else [])
    assert sum(item.is_current for item in items) <= 1


# ------------------------------------------------------------------ 四挑战（§6.4）


CHALLENGE_CASES: tuple[tuple[date, tuple[int, int, int, int]], ...] = (
    (date(1994, 5, 14), (0, 0, 0, 0)),
    (date(1998, 9, 27), (0, 0, 0, 0)),
    (date(1990, 8, 12), (5, 2, 3, 7)),
    (date(1998, 10, 15), (5, 3, 2, 8)),
    (date(1990, 11, 29), (0, 1, 1, 1)),
)


@pytest.mark.parametrize(("birth", "values"), CHALLENGE_CASES)
def test_challenge_values_are_the_absolute_differences(
    birth: date, values: tuple[int, int, int, int]
) -> None:
    """`C1=|M−D|`、`C2=|D−Y|`、`C3=|C1−C2|`（主挑战）、`C4=|M−Y|`；基底主数一并约简。"""
    month = reduce_number(birth.month, keep_master=False).value
    day = reduce_number(birth.day, keep_master=False).value
    year = reduce_number(birth.year, keep_master=False).value
    first, second = abs(month - day), abs(day - year)
    expected = (first, second, abs(first - second), abs(month - year))
    items = challenges(birth)
    assert [item.key for item in items] == list(CHALLENGE_KEYS)
    assert [item.index for item in items] == [1, 2, 3, 4]
    assert tuple(item.value for item in items) == values == expected


@pytest.mark.parametrize("birth", MANY_BIRTHS)
def test_challenges_stay_inside_the_zero_to_eight_domain(birth: date) -> None:
    for item in challenges(birth):
        assert 0 <= item.value <= 8
        assert item.value in CHALLENGE_MEANINGS
        assert item.label and item.expression and item.meaning
        # 时段是来源的定性区间，逐字回显，不许另编年份（spec §5.3）。
        assert item.duration == CHALLENGE_DURATIONS[item.key]
        assert item.duration in CHALLENGE_DURATION


def test_a_shared_reduced_base_makes_all_four_challenges_zero() -> None:
    """spec §2.4 那条：主角的月日年约简后同为 5，四个绝对差必然全 0。

    设计稿印的 1/0/1/0 因此不可能来自任何算式。0 也**不是**缺失值：Decoz 原文
    「The 0 (zero) Challenge is very common」，故四张卡各自照样给释义。
    """
    items = challenges(BIRTH)
    assert [item.value for item in items] == [0, 0, 0, 0]
    assert all(item.meaning == CHALLENGE_MEANINGS[0] for item in items)


def test_masters_are_reduced_inside_the_challenge_chain() -> None:
    """决策 3 的唯一例外，且例外写在算式上：11 月与 29 日在挑战链里都先约成 2。"""
    items = challenges(date(1990, 11, 29))
    assert items[0].expression == "|月 11→2 − 日 29→11→2| = 0"
    assert items[1].expression == "|日 29→11→2 − 年 1990→19→10→1| = 1"
    assert items[2].expression == "|第一挑战 0 − 第二挑战 1| = 1"
    assert items[2].key == "main"


# ------------------------------------------------------------------ 个人周期（§6.7）


CYCLE_KEYS: tuple[str, ...] = ("previous_year", "year", "next_year", "month", "day")

#: 每个周期由几个基底相加：流年是「出生月 + 出生日 + 目标年」三个，流月/流日各两个。
CYCLE_BASE_COUNTS: dict[str, int] = {
    "previous_year": 3,
    "year": 3,
    "next_year": 3,
    "month": 2,
    "day": 2,
}


def _all_cycles(cycles: PersonalCycles) -> tuple[PersonalCycle, ...]:
    return (cycles.previous_year, cycles.year, cycles.next_year, cycles.month, cycles.day)


def test_personal_cycles_cover_three_years_plus_the_month_and_the_day() -> None:
    cycles = personal_cycles(BIRTH, reference_date=REFERENCE)
    assert [item.key for item in _all_cycles(cycles)] == list(CYCLE_KEYS)
    assert [item.period for item in _all_cycles(cycles)] == [
        "2025",
        "2026",
        "2027",
        "2026-09",
        "2026-09-24",
    ]


def test_the_personal_year_keeps_the_master_the_mockup_flattened() -> None:
    """主角 2026：`5+5+1=11`，主数原样保留 —— 设计稿那个 2 在本轮是 11/2（spec §6.7）。"""
    year = personal_cycles(BIRTH, reference_date=REFERENCE).year
    assert (year.value, year.root, year.is_master) == (11, 2, True)
    assert year.steps[-1].label == "相加"
    assert year.steps[-1].expression == "5+5+1"
    assert year.meaning == PERSONAL_CYCLE_MEANINGS[11]


def test_the_month_and_day_chain_off_the_previous_root() -> None:
    """`PM = root(PY) + reduce(目标月)`、`PD = root(PM) + reduce(目标日)`（决策 11）。"""
    cycles = personal_cycles(BIRTH, reference_date=REFERENCE)
    assert cycles.month.steps[-1].expression == "2+9" and cycles.month.value == 11
    assert cycles.day.steps[-1].expression == "2+6" and cycles.day.value == 8
    # 链是接上的：流月的第一个基底行就是流年那个 11 被约成 2。
    assert cycles.month.steps[0].total == cycles.year.value
    assert cycles.month.steps[0].reduced == cycles.year.root
    assert cycles.day.steps[0].total == cycles.month.value
    # 出处后缀必须写共用那张表的名字，不能写「流年」：流月卡上引「流年 11」是句假话，
    # 而它看上去完全像一条真出处 —— 同 `CHALLENGE_DURATIONS` 那条片段式锁法的用意。
    for item in (cycles.month, cycles.day):
        assert "个人周期" in item.source and "流年" not in item.source


def test_a_personal_year_can_reach_thirty_three() -> None:
    """33 真凑得出来，而且凑它的日期是活人会问的：`9+2+22` 与 `11+11+11` 两条路都通。

    加数各自约简后保留主数（决策 3），故每个加数 ∈ `{1..9,11,22,33}`。本测试是
    `PERSONAL_CYCLE_MEANINGS` 补上 33 那一项的凭据 —— 语料初稿写「三个加数各 ≤9」，
    与决策 3 直接冲突；没有 33 这一项，1970-09-02 出生的人问 1993 年就会 `KeyError`
    成 500，而它只在罕见的生日 + 罕见的基准年凑到一起时才爆。
    """
    via_twenty_two = personal_cycles(date(1970, 9, 2), reference_date=date(1993, 5, 1)).year
    assert via_twenty_two.steps[-1].expression == "9+2+22"
    assert (via_twenty_two.value, via_twenty_two.root) == (33, 6)
    assert via_twenty_two.meaning == PERSONAL_CYCLE_MEANINGS[33]
    via_eleven = personal_cycles(date(1990, 11, 29), reference_date=date(2027, 3, 1)).year
    assert via_eleven.steps[-1].expression == "11+11+11"
    assert (via_eleven.value, via_eleven.root, via_eleven.is_master) == (33, 6, True)
    assert via_eleven.meaning == PERSONAL_CYCLE_MEANINGS[33]


@pytest.mark.parametrize(
    "reference", [REFERENCE, date(2000, 1, 1), date(2027, 11, 29), date(2024, 2, 29)]
)
def test_every_personal_cycle_ledger_adds_up(reference: date) -> None:
    """账本自洽：每一行要么原样要么真等于各位相加，且相加行 == 各基底约简后的值之和。"""
    for item in _all_cycles(personal_cycles(BIRTH, reference_date=reference)):
        assert item.value in PERSONAL_CYCLE_MEANINGS
        assert item.root == reduce_number(item.value, keep_master=False).value
        assert item.is_master == (item.value in MASTER_NUMBERS)
        assert item.label and item.period and item.meaning and item.source
        # 相加段不一定只有一行（`5+5+9=19→10→1`），故按标签把账本切成「基底段 + 相加段」，
        # 不能图省事写成 `steps[:-1]` —— 那样合计行会被当成第四个基底。
        cut = next(index for index, row in enumerate(item.steps) if row.label == "相加")
        bases, sums = item.steps[:cut], item.steps[cut:]
        assert sums[-1].reduced == item.value
        for row in item.steps:
            assert row.reduced == row.total or row.reduced == _digit_sum(row.total)
        # 一个基底一个标签；同一标签的最后一行就是那个基底约简后的值（多行链也只取末行）。
        per_base: dict[str, int] = {}
        for row in bases:
            per_base[row.label] = row.reduced
        assert len(per_base) == CYCLE_BASE_COUNTS[item.key]
        # 合计行是相加段的**第一行**：算式串只覆盖第一行（`reduce_number` 的约定），
        # 读者拿它验算上一段的三个数。
        assert sums[0].total == sum(per_base.values())
        assert sums[0].expression == "+".join(str(value) for value in per_base.values())


@pytest.mark.parametrize("birth", MANY_BIRTHS)
def test_personal_cycles_close_over_the_meaning_table(birth: date) -> None:
    for item in _all_cycles(personal_cycles(birth, reference_date=REFERENCE)):
        assert item.value in PERSONAL_CYCLE_MEANINGS
        assert 1 <= item.root <= 9


def test_the_reference_date_defaults_to_today() -> None:
    """缺省取今天（决策 11，与八字诸页同一个习惯）；golden 测试靠显式传参固定。"""
    cycles = personal_cycles(BIRTH)
    assert cycles.year.period == str(date.today().year)
    assert cycles.day.period == date.today().isoformat()
    assert sum(item.is_current for item in pinnacles(BIRTH)) == 1


# ------------------------------------------------------------------ 姓名天赋九宫（§6.5）


@pytest.mark.parametrize("name", NAMES)
def test_the_name_grid_counts_every_letter_exactly_once(name: str) -> None:
    """每个字母进且只进一格；`tokens` 把它是谁说得清清楚楚，读者能逐字复核。"""
    letters = split_letters(name)
    grid = name_grid(letters)
    assert [cell.digit for cell in grid.cells] == list(range(1, 10))
    assert grid.total == len(letters.letters)
    assert sum(cell.count for cell in grid.cells) == grid.total
    contributed = sorted(token for cell in grid.cells for token in cell.tokens)
    assert contributed == sorted(item.char for item in letters.letters)
    for cell in grid.cells:
        assert cell.count == len(cell.tokens)
        assert all(LETTER_VALUES[token] == cell.digit for token in cell.tokens)
    # 摆法由后端下发：前端自己排序就会排出设计稿那个非幻方的升序摆法（决策 12）。
    assert grid.layout == [list(row) for row in LOSHU_SQUARE]
    assert grid.source


@pytest.mark.parametrize("name", NAMES)
def test_karmic_lessons_are_exactly_the_empty_cells(name: str) -> None:
    """业力课 = 姓名里缺失的数（决策 9）；设计稿只印了 4，漏了同样缺失的 2。"""
    grid = name_grid(split_letters(name))
    empty = {cell.digit for cell in grid.cells if cell.count == 0}
    assert {lesson.digit for lesson in grid.karmic_lessons} == empty
    assert [lesson.digit for lesson in grid.karmic_lessons] == sorted(empty)
    for lesson in grid.karmic_lessons:
        assert lesson.meaning == KARMIC_LESSONS[lesson.digit]
        assert lesson.source


def test_the_protagonist_name_grid_matches_the_spec_table() -> None:
    """spec §2.4：计数合计 10（不是设计稿的 14），业力课 {2,4}（不是它的一条）。"""
    grid = name_grid(split_letters("LU QINGXUAN"))
    counts = {cell.digit: cell.count for cell in grid.cells}
    assert counts == {1: 1, 2: 0, 3: 3, 4: 0, 5: 2, 6: 1, 7: 1, 8: 1, 9: 1}
    assert grid.total == 10
    assert [lesson.digit for lesson in grid.karmic_lessons] == [2, 4]


# ------------------------------------------------------------------ 生辰洛书九宫（§6.6）


@pytest.mark.parametrize("birth", MANY_BIRTHS)
def test_the_loshu_grid_counts_birthday_digits_and_never_zero(birth: date) -> None:
    """0 不计（洛书无 0 格）；计数合计 == 生日里非 0 数字字符的个数（决策 10）。"""
    grid = loshu_grid(birth)
    digits = [int(char) for char in birth.isoformat() if char.isdigit()]
    assert grid.digits == digits
    assert len(digits) == 8
    assert grid.zero_count == digits.count(0)
    assert grid.total == len([digit for digit in digits if digit != 0])
    assert [cell.digit for cell in grid.cells] == list(range(1, 10))
    assert sum(cell.count for cell in grid.cells) == grid.total
    for cell in grid.cells:
        assert cell.count == len(cell.tokens)
    assert grid.layout == [list(row) for row in LOSHU_SQUARE]
    # 八条线的和恒为 15，且下发到响应里 —— 幻方性质不只藏在后端单测里（决策 12）。
    assert grid.line_sums == [15] * 8
    assert [lesson.digit for lesson in grid.missing] == sorted(
        cell.digit for cell in grid.cells if cell.count == 0
    )


def test_loshu_tokens_name_the_exact_position_in_the_birthday() -> None:
    """每格计数都能被读者用生日逐位复核：token 说的是「哪一位」，不是一个光秃秃的数字。"""
    grid = loshu_grid(BIRTH)
    tokens = {cell.digit: cell.tokens for cell in grid.cells}
    assert tokens[1] == ["年千位 1", "日十位 1"]
    assert tokens[9] == ["年百位 9", "年十位 9"]
    assert tokens[4] == ["年个位 4", "日个位 4"]
    assert tokens[5] == ["月个位 5"]
    assert grid.zero_count == 1 and grid.total == 7
    assert [lesson.digit for lesson in grid.missing] == [2, 3, 6, 7, 8]


@pytest.mark.parametrize("birth", MANY_BIRTHS)
def test_plane_completeness_is_exactly_three_digits_present(birth: date) -> None:
    """引擎只选句：齐→`present_text`，缺→`missing_text`，不拼不改写。"""
    grid = loshu_grid(birth)
    counts = {cell.digit: cell.count for cell in grid.cells}
    assert len(grid.planes) == 8
    assert [plane.key for plane in grid.planes] == [item.key for item in PLANES]
    for plane, corpus in zip(grid.planes, PLANES, strict=True):
        expected_missing = [digit for digit in plane.cells if counts[digit] == 0]
        assert plane.cells == list(corpus.cells)
        assert plane.name_zh == corpus.name_zh and plane.name_en == corpus.name_en
        assert plane.complete == (not expected_missing)
        assert plane.missing == expected_missing
        assert plane.text == (corpus.present_text if plane.complete else corpus.missing_text)
        assert plane.source == corpus.source
        assert sum(plane.cells) == 15


def test_the_protagonist_has_only_the_will_plane_complete() -> None:
    """spec §2.4 末行：设计稿唯一活下来的箭矢断言（意志之箭 9-5-1 三数齐）。"""
    grid = loshu_grid(BIRTH)
    assert [plane.key for plane in grid.planes if plane.complete] == ["will"]
    will = next(plane for plane in grid.planes if plane.key == "will")
    assert will.cells == [9, 5, 1] and will.missing == []


def test_the_two_grids_read_different_inputs() -> None:
    """决策 9：两张九宫的输入不同 —— 改名不动洛书，改生日不动姓名九宫。

    在整盘层面断言，而不是分开调两个函数：分开调时「各读各的输入」是被函数签名
    保证的同义反复，只有两份完整响应并排对才能证明它们真的互不污染。
    设计稿把两者揉成一张表，于是同时印错了两处（§2.4）。
    """
    base = compute_chart(full_name="LU QINGXUAN", birth_date=BIRTH, reference_date=REFERENCE)
    renamed = compute_chart(full_name="Anna", birth_date=BIRTH, reference_date=REFERENCE)
    reborn = compute_chart(
        full_name="LU QINGXUAN", birth_date=date(1994, 5, 15), reference_date=REFERENCE
    )
    assert renamed.loshu_grid == base.loshu_grid
    assert renamed.name_grid != base.name_grid
    assert reborn.name_grid == base.name_grid
    assert reborn.loshu_grid != base.loshu_grid
    # 分隔符不进计数，故不影响姓名九宫（决策 8）。
    assert name_grid(split_letters("LU QINGXUAN")) == name_grid(split_letters("LU-QINGXUAN"))


# ------------------------------------------------------------------ 总装（§7）


def test_compute_chart_assembles_every_section() -> None:
    chart = compute_chart(
        full_name="LU QINGXUAN", name_zh="陆青玄", birth_date=BIRTH, reference_date=REFERENCE
    )
    assert [item.key for item in chart.core] == list(CORE_KEYS)
    assert [item.key for item in chart.pinnacles] == list(PINNACLE_KEYS)
    assert [item.key for item in chart.challenges] == list(CHALLENGE_KEYS)
    assert [item.key for item in _all_cycles(chart.personal_cycles)] == list(CYCLE_KEYS)
    assert len(chart.letters) == 10
    assert chart.input.name_zh == "陆青玄"
    assert chart.input.reference_date == REFERENCE
    assert chart.input.age_at_reference == 32
    assert chart.input.letter_count == 10
    assert chart.input.skipped_count == 1 and chart.input.skipped_chars == [" "]
    assert chart.input.letter_total == chart.input.vowel_total + chart.input.consonant_total
    assert chart.input.vowel_total == 16 and chart.input.consonant_total == 34
    assert chart.provenance.reference_date == REFERENCE
    assert chart.provenance.badge == "#NUMERO-PYTHAG"
    assert len(chart.provenance.tables) == 4
    assert all(table.name and table.version and table.source for table in chart.provenance.tables)
    assert chart.provenance.engine and chart.provenance.method
    # 决策 14：响应里根本没有 `score` 这个字段，也不许有人日后顺手加回来。
    assert not hasattr(chart, "score")


def test_the_chinese_name_is_echo_only() -> None:
    """决策 1：中文名只回显，不参与任何计算 —— 加不加它，全盘的数一个都不许动。"""
    with_zh = compute_chart(
        full_name="LU QINGXUAN", name_zh="陆青玄", birth_date=BIRTH, reference_date=REFERENCE
    )
    without = compute_chart(full_name="LU QINGXUAN", birth_date=BIRTH, reference_date=REFERENCE)
    assert without.input.name_zh is None
    assert with_zh.model_dump(exclude={"input"}) == without.model_dump(exclude={"input"})


def test_the_whole_chart_is_deterministic() -> None:
    first = compute_chart(full_name="Anna", birth_date=BIRTH)
    second = compute_chart(full_name="Anna", birth_date=BIRTH)
    assert first == second
    assert first.input.reference_date == date.today()


def test_entry_level_sources_are_composed_by_the_content_helpers() -> None:
    """六处条目级出处都由语料 helper 拼；helper 保证条目名落在限定语之前。

    语料测锁的是 helper 自己，锁不住引擎有没有用它：把某一处改回
    `f"{CYCLES_SOURCE}·顶峰1"`，语料测照样全绿，而那一处的角标又变回一句光秃秃的书名
    （前端 `SourceNote` 只印第一个「（」之前的半句）—— 顶峰卡上并列的两条引用随即
    长得一模一样，读者分不出哪条引哪条。故这里按**产物**逐处核对，而不是只信 helper。
    """
    chart = compute_chart(full_name="LU QINGXUAN", birth_date=BIRTH, reference_date=REFERENCE)
    pinnacle = chart.pinnacles[0]
    challenge = chart.challenges[0]
    year = chart.personal_cycles.year
    lesson = chart.name_grid.karmic_lessons[0]
    missing = chart.loshu_grid.missing[0]
    assert pinnacle.source == cycles_source(f"顶峰{pinnacle.value}")
    assert challenge.source == cycles_source(f"挑战{challenge.value}")
    assert year.source == cycles_source(f"个人周期{year.value}")
    assert lesson.source == meanings_source(f"业力课{lesson.digit}")
    assert missing.source == loshu_source(f"缺数{missing.digit}")

    # 第六处是业力债。主角那盘没有（相加行是 15），故换 Decoz 的原例 1998-10-15 → 16。
    debt = compute_chart(full_name="Anna", birth_date=date(1998, 10, 15)).karmic_debts[0]
    assert debt.source == meanings_source(f"业力债{debt.number}")

    # 六处的角标（第一个「（」之前）都必须把条目名留在里面，否则前端印出来全是书名。
    for item in (pinnacle, challenge, year, lesson, missing, debt):
        assert "·" in item.source.split("（")[0], item.source


# --------------------------------------------------- 白话总论（多系统白话 spec §7、G18）


def test_summary_frame_carries_exactly_the_named_slots_and_no_joiner_residue() -> None:
    """R26：段落框架句不进参数化工厂（工厂只遍历 `PLAIN_CORPORA`，灵数没有表），口径由本测自守。

    禁字表唯一正主在 `tests/plain_wording.py`，这里只 import 不另立。槽位必须具名
    （裁定 R11）：卡巴拉那条例子说明穿插式的引用只有 `frame.format(**parts)` 装得下。
    """
    slots = set(re.findall(r"\{([a-z][a-z0-9_]*)\}", NUMEROLOGY_SUMMARY_FRAME))
    assert slots == {"essence", "pinnacles", "cycles", "loshu", "missing"}
    for token in FORBIDDEN:
        assert token not in NUMEROLOGY_SUMMARY_FRAME, token


def test_summary_does_not_quote_any_advice_sentence() -> None:
    """G18 的机器化形态：总论只搬核心数释义 + 报事实，一个建议句都不引。

    判据不是数禁字，而是**逐条对账**——顶峰/挑战/周期/洛书八平面的原句都不许出现在
    总论里；那四类今天几乎条条带「宜」「需」（条数复测见 `engines/numerology.py` 里
    `NUMEROLOGY_SUMMARY_FRAME` 的头注）。
    """
    chart = compute_chart(full_name="Liam Alexander Carter", birth_date=date(1990, 5, 15))
    summary = chart.plain_summary
    cycles = chart.personal_cycles
    for item in [
        *(p.meaning for p in chart.pinnacles),
        *(c.meaning for c in chart.challenges),
        *(cycles.previous_year.meaning, cycles.year.meaning, cycles.next_year.meaning,
          cycles.month.meaning, cycles.day.meaning),
    ]:
        assert item not in summary
    for plane in chart.loshu_grid.planes:
        assert plane.text not in summary
    for token in ("宜", "忌"):
        assert token not in summary, token


def test_summary_merges_every_available_core_meaning_once() -> None:
    """R12：同释义的两格（生命灵数与人格面具常同号）只说一遍，但不许把谁整个丢掉。"""
    chart = compute_chart(full_name="Liam Alexander Carter", birth_date=date(1990, 5, 15))
    lines = chart.plain_summary.split("\n")
    meanings = {card.meaning for card in chart.core if card.meaning}
    assert all(any(m in line for line in lines) for m in meanings)
    for meaning in meanings:
        assert sum(1 for line in lines if meaning in line) == 1


#: G2/G18 的第二套口径：**建议词与结论词**——六字表、四字表、抹词形表与 `advice_hits`
#: 的唯一正主已搬到 `tests/plain_wording.py`（Plan C Task 1 合并，本文件只 import 不另立），
#: 抹词形 `("对应","反应")` 的实测理由与复测命令见 `tests.plain_wording.NON_ADVICE_FORMS` 头注。
def test_frame_and_summary_carry_no_advice_or_verdict_word() -> None:
    """框架句自己一个字都不许下判断（G2）；成品段同查，因为段里含框架句的每个字。

    这条不是 `test_summary_does_not_quote_any_advice_sentence` 的重复：那条查「不引别人的
    判断」，这条查「不自建判断」。成品段逐字搬进来的语料只有 `{essence}` 一路
    （`_essence_lines()` 抄的是 `core[].meaning`，其余四路只报数与位），所以「不自建判断」
    的覆盖面 = 框架句 + 由输入实算出的成品段；语料侧那一半在
    `test_no_quotable_source_sentence_carries_an_advice_or_verdict_word`，两条合起来才钉得住。
    盘侧从 2026-10-01 起在原来那一盘之外再按 `NAMES` 矩阵逐名扫（矩阵里会落到数2 的
    「对应之数」，所以段侧与表侧同一把尺：都过 `advice_hits`，见
    `tests.plain_wording.NON_ADVICE_FORMS` 头注）。
    """
    for token in ADVICE_TOKENS:
        assert token not in NUMEROLOGY_SUMMARY_FRAME, token
    for label, chart in [
        (
            "Liam Alexander Carter",
            compute_chart(full_name="Liam Alexander Carter", birth_date=date(1990, 5, 15)),
        ),
        *(
            (name, compute_chart(full_name=name, birth_date=BIRTH, reference_date=REFERENCE))
            for name in NAMES
        ),
    ]:
        assert not advice_hits(chart.plain_summary), (label, advice_hits(chart.plain_summary))


#: `source` 不进口径：它是出处串，不是会被印进白话段的正文（同
#: `test_kabbalah_plain_corpus.py` 源表扫只扫 `.meaning` 一个字的理由）。
#: `keywords` 里数5 带「适应」，`master_title` 三条是「MASTER … · 灵性直觉者」这类名相
#: （复测 2026-10-02 实跑：`cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c
#: "from app.content.numerology_meanings import CORE_MEANINGS as C; print([v.master_title for v in C.values() if v.master_title])"` → 长度 3）。
#: 复测（2026-10-01 实跑）：`cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "
#: from app.content.numerology_meanings import CORE_MEANINGS as C
#: w=('宜','忌','需','应','吉','凶')
#: print([(k,'keywords',t) for k,v in sorted(C.items()) for t in w if t in '/'.join(v.keywords).replace('对应','').replace('反应','').replace('适应','')])
#: print([(k,'keywords',t) for k,v in sorted(C.items()) for t in w if t in '/'.join(v.keywords)])"`
#: → `[]` 与 `[(5, 'keywords', '应')]`：新词形「适应」是抹得住的唯一命中。
ADVICE_SWEEP_FIELDS: tuple[tuple[str, Callable[[CoreMeaning], str]], ...] = (
    ("essence", lambda meaning: meaning.essence),
    ("talent", lambda meaning: meaning.talent),
    ("challenge", lambda meaning: meaning.challenge),
    ("keywords", lambda meaning: "/".join(meaning.keywords)),
    ("master_title", lambda meaning: meaning.master_title or ""),
)


def test_no_quotable_source_sentence_carries_an_advice_or_verdict_word() -> None:
    """整表扫而不是整盘扫：`{essence}` 落在哪几格由输入决定，只扫一盘等于只扫那几格。

    2026-10-01 评审 finding 的那句「一旦语料侧新增一句带「宜」的释义，红的是这条」原来
    不成立——Liam 那盘没走到的数，它的新释义就永远不进这条。这里把 `CORE_MEANINGS`
    全表逐格扫过，字段按 `ADVICE_SWEEP_FIELDS` 表选取（essence/talent/challenge 三个
    纯文本字段 + keywords/master_title 两个 2026-10-01 随口径合并补进来的字段）：
    后四个今天不进总论，但装配口径一旦改成搬它们，这条立刻红，而不是等页面上印出
    「宜…」才发现。
    命中即报 `(表, 键, 字段, 命中的字)`，读者不用二次定位就知道是哪张表长出了判断词。

    **顶峰/挑战/周期/洛书那四张表刻意不进这条**：它们是建议句库（条数实测见
    `engines/numerology.py` 里 `NUMEROLOGY_SUMMARY_FRAME` 的头注：那 16 句里 13 句含
    「宜/忌/需/应」），G18 裁定「事实句合并」的理由正是它们条条带建议，所以总论一个字
    都不引它们。它们的防线是 `test_summary_does_not_quote_any_advice_sentence`，
    在这四条上再断言「表内无建议词」是把设计断成反面。
    """
    for number, meaning in sorted(CORE_MEANINGS.items()):
        for field, get in ADVICE_SWEEP_FIELDS:
            text = get(meaning)
            hits = advice_hits(text)
            assert not hits, (f"CORE_MEANINGS[{number}].{field}", hits, text)


def test_summary_essence_openers_are_never_empty_so_no_branch_sentence_is_due() -> None:
    """G15 的例外要登记在明处：`{essence}` 没有「一条都没有」那条支路句，因为不可能为空。

    生命灵数由生日得（`life_path()` 不吃姓名），恒有释义，于是六个核心数里至少两格
    （生命灵数、生日数）永远带句子上桌，`meaning is None` 只会出现在灵魂冲动数/人格面具数。
    这里按名字矩阵逐条钉「第二段非空且含生命灵数释义」，即钉住那条支路句的前提；
    真要为空，装配器会先在这里红，而不是等到线上印出一句凭空编的开场白。
    复测：`cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m pytest tests/test_numerology.py -o addopts="" -k essence`
    """
    for name in NAMES:
        chart = compute_chart(full_name=name, birth_date=BIRTH, reference_date=REFERENCE)
        life_path_card = next(card for card in chart.core if card.key == "life_path")
        assert life_path_card.meaning
        lines = chart.plain_summary.split("\n")
        assert lines[1].strip(), name
        assert any(life_path_card.meaning in line for line in lines), name


def test_summary_skips_a_core_card_that_has_no_meaning() -> None:
    """`meaning is None` 的那一格在总论里一个字都不出现——它的 `unavailable_reason` 已在卡上说过。

    白话块只有一处说话的地方（`_essence_lines`），缺数解释若在这里再讲一遍就是第二处。
    反向半边：同盘其他格仍照搬，生命灵数那句恒在。
    """
    chart = compute_chart(full_name="Lynn", birth_date=BIRTH, reference_date=REFERENCE)
    blanks = [card for card in chart.core if card.meaning is None]
    assert blanks and all(card.unavailable_reason for card in blanks)
    summary = chart.plain_summary
    for card in blanks:
        assert card.label not in summary, card.key
    assert any(
        card.meaning in summary for card in chart.core if card.key != blanks[0].key and card.meaning
    )
