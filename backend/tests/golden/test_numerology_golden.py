"""外部锚点对拍（spec §9.3）。

三组锚点**全部有出处**，没有一组是把引擎自己算的结果抄回来当期望值：

* **Decoz 算例 A / B** —— Hans Decoz 在 worldnumerology.com 印出的两个生日。他用它们
  说明两件事：生命灵数三法只有一法正确（§2.2），以及只有正确法能揭示业力债（§2.3）。
  这两个数因此是「算法正确性」这条最关键口径的外部落点。
* **本项目主角** `LU QINGXUAN` / 1994-05-14 —— 与 `test_name_golden.py` 里姓名学的
  golden 主角**同一个人**（刻意的连续性）。期望值逐格取自 spec §2.4 那张表的
  「正确值」列，而那一列是按 §2.2 的正确算式手推出来的。

**设计稿印的数字与本测试大面积冲突**，故把偏差钉在测试旁边而不只留在文档里
（plan T5 Step 2）：稿子印的是 生命灵数 **33/6**、表达 **11/2**、灵魂冲动 **9**、
人格面具 **2**、成熟 **8**、顶峰 **1/11/3/5**、挑战 **1/0/1/0**、业力课**只有 4**、
均衡度 **82%**、2026 流年 **2**。冲突处一律以 spec §2.4 为准 —— 稿子的版式、卡片
结构、字母映射表、约简阶梯、顶峰年龄轴与意志之箭都对，它印出的**数值**多为装饰。

对拍时若某格对不上：**先怀疑实现，再怀疑 spec 的验算**，最后才允许改期望值，
且改的话要在 spec §11 记一条（plan T5 Step 3）。
"""

from datetime import date

import pytest

from app.engines.numerology import compute_chart, life_path

#: 主角基准日。显式给出，免得个人年/月/日随「今天」漂移（决策 11）。
REFERENCE = date(2026, 9, 24)

#: 设计稿主角，与姓名学 golden 同一人。
PROTAGONIST = "LU QINGXUAN"
PROTAGONIST_BIRTH = date(1994, 5, 14)


def _steps(card) -> list[tuple[str, str, int, int]]:
    """把账本压成 (label, expression, total, reduced) 四元组，便于逐行对拍。"""
    return [(s.label, s.expression, s.total, s.reduced) for s in card.steps]


# ------------------------------------------------------- Decoz 算例 A（spec §2.3）


def test_decoz_example_a_reduces_to_three_by_the_only_correct_method() -> None:
    """1990-08-12 → 生命灵数 **3**，账本含 `8+3+1=12`。

    这个生日的狡猾之处：§2.2 那两种**错误**法也算得出 3
    （逐位相加 `1+9+9+0+8+1+2=30→3`；三整数相加 `8+12+1990=2010→3`）。
    故末位数字在这里什么也证明不了，能证明算法的是**中间量**：
    正确法必须先把月/日/年各自约简成 8、3、1，再相加得 12。
    断言账本逐行，等于同时排除了那两种错法。
    """
    card, debts = life_path(date(1990, 8, 12))

    assert card.value == 3 and card.root == 3 and card.is_master is False
    assert _steps(card) == [
        ("月", "8", 8, 8),
        ("日", "1+2", 12, 3),
        ("年", "1+9+9+0", 1990, 19),
        ("年", "1+9", 19, 10),
        ("年", "1+0", 10, 1),
        ("相加", "8+3+1", 12, 3),
    ]
    # 两种错法的中间量一个都不许出现：30 是逐位相加，2010 是三整数相加。
    assert {30, 2010} & {total for *_, total, _ in _steps(card)} == set()
    assert debts == ()


# ------------------------------------------------------- Decoz 算例 B（spec §2.3）


def test_decoz_example_b_reveals_the_karmic_debt_the_wrong_methods_hide() -> None:
    """1998-10-15 → 生命灵数 **7**，且账本标出 **16 业力债**。

    Decoz 用这一例演示「只有正确法能揭示业力债」：两种错法的末位同样是 7
    （`1+9+9+8+1+0+1+5=34→7`、`10+15+1998=2023→7`），但中途都不经过 16，
    于是 16/7 这笔债被它们**吞掉**。所以本测试不只断言债存在，
    还断言那两个错法的中间量（34、2023）从未出现在账本里。
    """
    card, debts = life_path(date(1998, 10, 15))

    assert card.value == 7 and card.root == 7
    assert _steps(card) == [
        ("月", "1+0", 10, 1),
        ("日", "1+5", 15, 6),
        ("年", "1+9+9+8", 1998, 27),
        ("年", "2+7", 27, 9),
        ("相加", "1+6+9", 16, 7),
    ]
    # 业力债只认「相加」那一行：16 出现在这里才是 Decoz 说的那笔债。
    assert [d.number for d in debts] == [16]
    assert debts[0].label == "相加" and debts[0].expression == "1+6+9"
    flagged = [s for s in card.steps if s.karmic_debt]
    assert [(s.label, s.total) for s in flagged] == [("相加", 16)]
    # 错法的中间量：34 与 2023 都不该在账本里露面。
    assert {34, 2023} & {total for *_, total, _ in _steps(card)} == set()


# ------------------------------------------------------- 主角：六个核心数（§2.4）


@pytest.fixture(scope="module")
def chart():
    """主角全盘。`reference_date` 固定，故本模块的所有期望值都不随今天漂移。"""
    return compute_chart(
        full_name=PROTAGONIST,
        birth_date=PROTAGONIST_BIRTH,
        name_zh="陆青玄",
        reference_date=REFERENCE,
    )


def test_protagonist_core_numbers_are_the_spec_column_not_the_mockup(chart) -> None:
    """六个核心数 = 6 / 5 / 7 / 7 / 5 / 11-2（spec §2.4「正确值」列）。

    设计稿在这一行印错了四处，且错法各不相同，故逐个点名：
    生命灵数 33（用了错法 1）、表达 11/2（凭空写「异体高阶」）、
    灵魂冲动 9（同卡印了两个互相矛盾的算式）、人格面具 2（34 约简是 7 不是 2）、
    成熟 8（喂了伪造的表达数 2）。只有生日数 5 稿子是对的。
    """
    by_key = {card.key: card for card in chart.core}

    assert [card.key for card in chart.core] == [
        "life_path",
        "expression",
        "soul_urge",
        "personality",
        "birthday",
        "maturity",
    ]
    assert [(k, by_key[k].value, by_key[k].root) for k in by_key] == [
        ("life_path", 6, 6),
        ("expression", 5, 5),
        ("soul_urge", 7, 7),
        ("personality", 7, 7),
        ("birthday", 5, 5),
        ("maturity", 11, 2),
    ]
    # 成熟数是唯一的主数，故唯一带 `master_title`；其余五张都不许自称主数。
    assert [card.is_master for card in chart.core] == [False] * 5 + [True]
    assert by_key["maturity"].master_title
    assert all(card.master_title is None for card in chart.core[:5])
    # 生命灵数是 6 而**不是** 33：稿子那个 33 来自错法 1（`1+9+9+4+0+5+1+4=33`）。
    assert by_key["life_path"].value != 33
    assert all(card.unavailable_reason is None for card in chart.core)


def test_protagonist_life_path_ledger_is_the_ladder_the_mockup_got_right(chart) -> None:
    """约简阶梯逐行对拍：年 `1+9+9+4=23→5`、月 `5`、日 `1+4=5`、`5+5+5=15→6`。

    这一段稿子印对了（§2.4 第二行 ✓），所以它同时也是「稿子对的地方我们没改坏」的护栏。
    """
    life = chart.core[0]
    assert _steps(life) == [
        ("月", "5", 5, 5),
        ("日", "1+4", 14, 5),
        ("年", "1+9+9+4", 1994, 23),
        ("年", "2+3", 23, 5),
        ("相加", "5+5+5", 15, 6),
    ]
    # 稿子的 33 与错法 2 的 2013 都不许出现在账本里（spec §2.4 偏差 A）。
    assert {33, 2013} & {total for *_, total, _ in _steps(life)} == set()
    assert chart.karmic_debts == []


def test_protagonist_expression_ledger_balances_vowels_and_consonants(chart) -> None:
    """表达数的两条支路：元音 `3+9+3+1=16→7`、辅音 `3+8+5+7+6+5=34→7`，合 `50→5`。

    这一格是 §2.4 里稿子自相矛盾最明显的一处：它印了 `∑(...)=50` 却又写「异体高阶得 11」，
    而 50 约简是 5。断言两条支路的和相加等于全字母和，即表达数不变式在真夹具上也成立。
    """
    by_key = {card.key: card for card in chart.core}
    soul = _steps(by_key["soul_urge"])
    personality = _steps(by_key["personality"])

    assert soul == [("元音", "3+9+3+1", 16, 7)]
    assert personality == [("辅音", "3+8+5+7+6+5", 34, 7)]
    # 全字母那一行按**姓名原序**排（L U Q I N G X U A N），不是元音先辅音后，
    # 所以读者能拿它对着「姓名逐字透视条」一格一格核。
    assert _steps(by_key["expression"]) == [("全字母", "3+3+8+9+5+7+6+3+1+5", 50, 5)]
    # 元音和 + 辅音和 == 全字母和（决策 6 的不变式，在主角这一对上具体成立）。
    assert 16 + 34 == 50
    assert (chart.input.vowel_total, chart.input.consonant_total) == (16, 34)
    assert chart.input.letter_total == 50
    assert (chart.input.letter_count, chart.input.skipped_count) == (10, 1)


# ------------------------------------------------------- 主角：顶峰与挑战（§2.4）


def test_protagonist_pinnacles_are_one_one_two_one_on_the_right_age_axis(chart) -> None:
    """顶峰 1/1/2/1，年龄轴 0-30 / 31-39 / 40-48 / 49+。

    稿子印的是 1/**11**/**3**/**5** —— 只有 P1 对。年龄轴稿子是对的：
    `36 − root(生命灵数 6) = 30`，此后每程 9 年，第四程无终点（`end_age is None`，
    不填 999 之类的假值）。32 岁（基准日 2026-09-24）应落在第二程。
    """
    assert [p.value for p in chart.pinnacles] == [1, 1, 2, 1]
    assert [p.key for p in chart.pinnacles] == ["first", "second", "third", "fourth"]
    assert [(p.start_age, p.end_age) for p in chart.pinnacles] == [
        (0, 30),
        (31, 39),
        (40, 48),
        (49, None),
    ]
    # 基准日 2026-09-24、生日 1994-05-14 → 周岁 32，落在第二程（31-39）。
    assert chart.input.age_at_reference == 32
    assert [p.is_current for p in chart.pinnacles] == [False, True, False, False]
    # 四程各自的算式：P1=月+日、P2=日+年、P3=P1+P2、P4=月+年（§6.3）。
    # 算式里把原值与约简值都印出来（`14→5`、`1994→23→5`），读者不必回查规则就能核。
    assert [p.expression for p in chart.pinnacles] == [
        "月 5 + 日 14→5 = 10 → 1",
        "日 14→5 + 年 1994→23→5 = 10 → 1",
        "第一顶峰 1 + 第二顶峰 1 = 2",
        "月 5 + 年 1994→23→5 = 10 → 1",
    ]
    assert all(p.is_master is False for p in chart.pinnacles)


def test_protagonist_four_challenges_are_all_zero(chart) -> None:
    """四挑战全 **0**（稿子印的是 1/0/1/0，§2.4 偏差）。

    这不是巧合也不是缺值：月、日、年三者约简后**同为 5**，四个绝对差必然全 0。
    0 在挑战值域 `{0..8}` 里是**真实成员**（决策 17 那条「唯一合法的 0」），
    故四张卡照样带释义，而不是一片空白。
    """
    assert [c.key for c in chart.challenges] == ["first", "second", "main", "fourth"]
    assert [c.value for c in chart.challenges] == [0, 0, 0, 0]
    # 三个基底约简后同为 5（月 5、日 14→5、年 1994→23→5），所以每条算式都读得出
    # 「为什么是 0」，而不是只给个 0。
    assert [c.expression for c in chart.challenges] == [
        "|月 5 − 日 14→5| = 0",
        "|日 14→5 − 年 1994→23→5| = 0",
        "|第一挑战 0 − 第二挑战 0| = 0",
        "|月 5 − 年 1994→23→5| = 0",
    ]
    assert all(c.meaning and c.duration for c in chart.challenges)


# ------------------------------------------------------- 主角：两套九宫（§2.4 / §6.5-6.6）


def test_protagonist_name_grid_has_two_karmic_lessons_not_one(chart) -> None:
    """姓名天赋九宫：计数合计 **10**，业力课 **{2, 4}**（稿子只印了 4）。

    稿子这一格是自相矛盾的：它一边印「∑ 10 字母共振」，一边列出合计 14 的九宫计数
    —— 10 个字母填不出 14 个计数。名字里没有 B/K/T，故 2 与 4 **同样**缺失。
    """
    grid = chart.name_grid

    assert grid.total == 10
    assert sum(cell.count for cell in grid.cells) == 10
    assert [cell.digit for cell in grid.cells] == list(range(1, 10))
    assert [cell.count for cell in grid.cells] == [1, 0, 3, 0, 2, 1, 1, 1, 1]
    assert [item.digit for item in grid.karmic_lessons] == [2, 4]
    assert all(item.meaning and item.source for item in grid.karmic_lessons)
    # 真洛书摆法（决策 12），不是稿子那个非幻方的升序摆法。
    assert grid.layout == [[4, 9, 2], [3, 5, 7], [8, 1, 6]]


def test_protagonist_loshu_completes_only_the_plane_of_will(chart) -> None:
    """生辰洛书九宫：缺 2/3/6/7/8，八平面里**只有 Will(9-5-1) 齐备**。

    这是稿子唯一活下来的箭矢断言（§2.4 末行 ✓）。洛书只吃生日的字面数字
    （决策 10），故 `1994-05-14` 取出 `1,9,9,4,0,5,1,4`：0 不计入 `total`
    但 `zero_count` 如实报 1。
    """
    loshu = chart.loshu_grid

    assert loshu.digits == [1, 9, 9, 4, 0, 5, 1, 4]
    assert (loshu.total, loshu.zero_count) == (7, 1)
    assert [cell.digit for cell in loshu.cells] == list(range(1, 10))
    assert [cell.count for cell in loshu.cells] == [2, 0, 0, 2, 1, 0, 0, 0, 2]
    assert [item.digit for item in loshu.missing] == [2, 3, 6, 7, 8]
    # 幻方性质在响应里就可核对，不只藏在后端单测里（决策 12）。
    assert loshu.line_sums == [15] * 8
    assert len(loshu.planes) == 8
    assert [p.key for p in loshu.planes if p.complete] == ["will"]
    will = next(p for p in loshu.planes if p.complete)
    assert will.cells == [9, 5, 1] and will.missing == []
    # 改名不动洛书、改生日不动姓名九宫：两张九宫各读各的输入（决策 9）。
    assert loshu.layout == chart.name_grid.layout


# ------------------------------------------------------- 主角：个人年（§2.4）


def test_protagonist_personal_year_2026_keeps_the_master_number(chart) -> None:
    """2026 个人流年 = **11 / 2**（稿子印 2，把中途的 11 约简掉了，违反决策 3）。

    算式：出生月 5 + 出生日 5 + 流年 `2+0+2+6=10→1` = **11**，主数不约简，根为 2。
    三轮（前一年/今年/后一年）随基准日移动，故一并钉住它们的时段与值。
    """
    cycles = chart.personal_cycles

    assert [(c.key, c.period) for c in (cycles.previous_year, cycles.year, cycles.next_year)] == [
        ("previous_year", "2025"),
        ("year", "2026"),
        ("next_year", "2027"),
    ]
    assert cycles.year.value == 11 and cycles.year.root == 2
    assert cycles.year.is_master is True
    assert cycles.year.steps[-1].expression == "5+5+1"
    assert cycles.year.steps[-1].total == 11
    # 三轮各不相同，故不是恒真断言：2025 是 `5+5+9=19→10→1`（19 不是主数，照约），
    # 2027 的流年加数本身是 `2+0+2+7=11` —— **主数在加数上就保留**，故写成
    # `5+5+11=21→3`。这正是决策 3 在流年链上的形状。
    assert [(c.value, c.root) for c in (cycles.previous_year, cycles.next_year)] == [(1, 1), (3, 3)]
    assert cycles.next_year.steps[-1].expression == "5+5+11"
    assert cycles.month.period == "2026-09" and cycles.day.period == "2026-09-24"
    assert all(c.meaning and c.source for c in (cycles.month, cycles.day))
