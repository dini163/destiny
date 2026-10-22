"""Golden tests for the 雷诺曼 (Lenormand) deck and combination-draw engine.

The deck is the fixed 36-card Petit Lenormand; the draw uses :mod:`secrets` (CSPRNG,
PRD 4.4), so exact cards are not pinned. Instead the tests assert the structural
guarantees: spread sizes and layouts, card uniqueness within a spread, that the Grand
Tableau lays all 36 distinct cards, that the polarity tally accounts for every card,
that line spreads read N-1 adjacent 组合直读 pairs, and that the significator is the
correct 指示牌 (男人 28 / 女人 29).

Task 9B（判据 ⑧-⑪）把锚从「引擎返回的东西非空」换成外部可对拍的结构与算术，并补上上面
那段没覆盖的三面：

* **表侧**（⑧）—— 直接读 ``content.lenormand.CARDS``，钉抽牌结果看不见的列内唯一性与
  「映射常量 vs 表里的牌名」这一跨处一致性；``number`` 恰为 1..36 由
  :func:`test_grand_tableau_lays_all_thirty_six_distinct_cards` 从抽牌侧钉，不在此重念。
* **席位几何**（⑨）—— 大桌是 4×8 + 末行 4（**不是 8×8**，计划的措辞已被代码与牌阵自陈推翻），
  前端的网格就按 ``row``/``col`` 落格，而这两字段此前一次都没被断言过。
* **组合语义按 layout 三分岔**（⑩）—— ``line`` 是 N−1、``box`` 恒 8（中心 × 环）、
  ``tableau`` 无指示牌时退回首行线读（7 条，不是 35 对）；两个 fallback 分支过去是死代码。
* **指示牌四正邻位**（⑪）—— 一条真实的 36 张发牌 + ``model_copy`` 翻旗标 + 直调
  ``_tableau_combinations``，六个席位逐一手算条数与 ``context``，并钉住拼接方向。
"""

from collections import Counter

import pytest
from fastapi.testclient import TestClient

from app.content.lenormand import CARDS, SIGNIFICATOR_BY_GENDER, SPREADS
from app.core.errors import UnsupportedMethodError
from app.engines.lenormand import (
    POLARITY_WEIGHT,
    _box_combinations,
    _tableau_combinations,
    build_verdict,
    draw_lenormand,
)
from app.engines.plain_corpora import LENORMAND
from app.engines.verdict import grade_for
from app.schemas.lenormand import Combination, DrawnCard

SPREAD_SIZES = {"single": 1, "three_card": 3, "five_card": 5, "nine_card": 9, "grand_tableau": 36}
SPREAD_LAYOUTS = {
    "single": "line",
    "three_card": "line",
    "five_card": "line",
    "nine_card": "box",
    "grand_tableau": "tableau",
}


def test_grand_tableau_lays_all_thirty_six_distinct_cards() -> None:
    reading = draw_lenormand(spread_id="grand_tableau")
    assert len(reading.cards) == 36
    assert len(set(reading.drawn_ids)) == 36
    assert sorted(c.number for c in reading.cards) == list(range(1, 37))


def test_spread_sizes_and_layouts() -> None:
    for spread_id, size in SPREAD_SIZES.items():
        reading = draw_lenormand(spread_id=spread_id)
        assert reading.spread_id == spread_id
        assert reading.layout == SPREAD_LAYOUTS[spread_id]
        assert len(reading.cards) == size
        assert len(set(reading.drawn_ids)) == size


def test_positions_are_ordered_and_unique() -> None:
    reading = draw_lenormand(spread_id="five_card")
    assert [c.position_index for c in reading.cards] == list(range(5))
    assert len({c.position_key for c in reading.cards}) == 5


def test_polarity_tally_accounts_for_every_card() -> None:
    for spread_id, size in SPREAD_SIZES.items():
        reading = draw_lenormand(spread_id=spread_id)
        assert reading.positive_count + reading.neutral_count + reading.negative_count == size
        for card in reading.cards:
            assert card.polarity in {1, 0, -1}
            assert card.polarity_label in {"积极", "中性", "消极"}


def test_line_spreads_read_adjacent_combinations() -> None:
    # A line of N cards yields N-1 adjacent 组合直读 pairs.
    assert len(draw_lenormand(spread_id="single").combinations) == 0
    assert len(draw_lenormand(spread_id="three_card").combinations) == 2
    assert len(draw_lenormand(spread_id="five_card").combinations) == 4


def test_combination_phrase_is_composed_from_a_distinct_pair() -> None:
    reading = draw_lenormand(spread_id="three_card")
    assert reading.combinations
    for combo in reading.combinations:
        assert combo.phrase.strip()
        assert combo.left.number != combo.right.number


def test_significator_is_the_correct_card() -> None:
    male = draw_lenormand(spread_id="grand_tableau", significator="male")
    assert male.significator is not None
    assert male.significator.number == 28
    assert male.significator.name_zh == "男人"
    female = draw_lenormand(spread_id="grand_tableau", significator="female")
    assert female.significator is not None
    assert female.significator.number == 29
    assert female.significator.name_zh == "女人"
    assert draw_lenormand(spread_id="grand_tableau").significator is None


def test_draws_are_varied_not_deterministic() -> None:
    first = draw_lenormand(spread_id="five_card").drawn_ids
    second = draw_lenormand(spread_id="five_card").drawn_ids
    assert first != second


def test_rng_and_engine_are_declared() -> None:
    reading = draw_lenormand(spread_id="three_card")
    assert reading.rng == "secrets"
    assert reading.engine == "lenormand-combination"
    assert reading.synthesis.strip()


def test_unknown_spread_raises() -> None:
    with pytest.raises(UnsupportedMethodError):
        draw_lenormand(spread_id="not_a_spread")


def test_lenormand_endpoint(client: TestClient) -> None:
    response = client.post("/api/v1/lenormand/draw", json={"spread_id": "three_card"})
    assert response.status_code == 200
    body = response.json()
    assert body["spread_id"] == "three_card"
    assert len(body["cards"]) == 3
    assert len(set(body["drawn_ids"])) == 3
    assert body["rng"] == "secrets"


def test_lenormand_endpoint_rejects_unknown_spread(client: TestClient) -> None:
    response = client.post("/api/v1/lenormand/draw", json={"spread_id": "nope"})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "unsupported_method"


# --- 判据 ⑧：牌库表侧不变式（不经过任何一次抽牌） ---------------------------------

def test_the_card_table_holds_without_a_single_draw() -> None:
    """直接吃 `CARDS`：抽牌结果反推不到的那几面。

    为什么值得单独钉：这 36 枚牌今天只以「抽出来的样子」被看过（`grep -rn CARDS
    backend/tests/` 在 Task 9B 之前为空），而抽牌侧只能给出张数与编号。两枚牌共用同一个
    `name_zh`、或某枚牌的 `as_modifier` 被写成和 `essence` 一样（组合直读立刻退化成把原词
    念两遍，页面上就是「rider rider」这类废话，条数照样对）—— 这两种坏法条数测全察觉不到。

    刻意**不**在这里重断 `number` 恰为 1..36：那件事由
    :func:`test_grand_tableau_lays_all_thirty_six_distinct_cards` 从抽牌侧钉着，再从表侧
    念一遍就是自我确认式的重复。
    """
    assert len(CARDS) == 36
    for field in ("id", "name", "name_zh"):
        values = [getattr(card, field) for card in CARDS]
        assert len(set(values)) == 36, field

    essences = [card.essence for card in CARDS]
    modifiers = [card.as_modifier for card in CARDS]
    assert all(essences) and all(modifiers), "essence / as_modifier 不允许空串"
    assert len(set(essences)) == 36, "两枚牌共用同一个名词核心 → 组合直读失去区分度"
    assert len(set(modifiers)) == 36, "两枚牌共用同一个修饰语 → 组合直读失去区分度"
    for card in CARDS:
        assert card.essence != card.as_modifier, card.number
        assert card.keywords and all(card.keywords), card.number
        assert card.meaning.strip(), card.number
    assert {card.polarity for card in CARDS} <= {-1, 0, 1}


def test_the_significator_mapping_and_the_card_names_are_the_same_fact() -> None:
    """跨处一致性：映射常量说的「男人 28 / 女人 29」必须由表里的牌名自己兑一次。

    今天 `SIGNIFICATOR_BY_GENDER`（`content/lenormand.py`）与牌名各被断言一次，**没有一条测
    说这两处必须相等**：改牌名只红一条测，改映射常量则可能全绿 —— 页面会安静地把「女性问卜」
    的指示牌画成另一枚牌。这条把两侧焊在一起：从表里按 `name_zh` 反查编号，必须等于常量。

    本测只钉三同族字段里的第一件（编号映射 ↔ 表内按牌名回查）；全库仅这两枚中性
    （`polarity == 0`）与「指示牌」关键词由下一条测 :func:`test_the_two_significator_cards_are_the_only_neutral_ones`
    （同文件 `:186`，跑它用 `-k only_neutral`）钉住。
    复测：`pytest tests/golden/test_lenormand_golden.py -k significator_mapping_and_the_card_names`。
    """
    assert SIGNIFICATOR_BY_GENDER == {"male": 28, "female": 29}
    number_by_name = {card.name_zh: card.number for card in CARDS}
    assert {gender: number_by_name[name] for gender, name in
            (("male", "男人"), ("female", "女人"))} == SIGNIFICATOR_BY_GENDER


def test_the_two_significator_cards_are_the_only_neutral_ones() -> None:
    """指示牌 28/29 是全库仅有的两枚中性牌，且自我声明为「指示牌」。

    与上一条同族但看的是另外两个字段：`polarity == 0` 的集合、`keywords` 含「指示牌」的集合，
    都必须恰为映射常量指到的那两枚。坏法举例：给某枚吉凶牌补一个「指示牌」关键词，或把男人
    改成极性 +1 —— 只有这一条会红。

    「仅 28/29 中性」是**现状围栏、不是契约**（同 `tests/test_kabbalah_api.py` 的
    `-k hex_colour` 那条 11 色互异的口径）：Petit Lenormand 若干传统把 26 书 / 36 十字也读作
    中性，语料重新定性是完全合法的编辑动作 —— 若日后有意让第三枚牌转中性，本测应当被**显式
    改写**而不是被当成回归修回去。复测：`pytest tests/golden/test_lenormand_golden.py
    -k only_neutral` 绿 = 两集合仍恰为 {28, 29}（2026-09-27 实测）。
    """
    mapped = set(SIGNIFICATOR_BY_GENDER.values())
    assert mapped == {28, 29}
    assert {card.number for card in CARDS if card.polarity == 0} == mapped
    assert {card.number for card in CARDS if "指示牌" in card.keywords} == mapped


def test_combination_direction_is_ambiguous_for_no_pair_of_cards() -> None:
    """A 修饰 B 与 B 修饰 A 必须得到两句不同的话 —— 表级性质，为判据 ⑪ 的方向断言兜底。

    引擎按「后牌修饰前牌」拼接（`_combine`），测里要断「反向拼法不等于实际 phrase」。那个
    `!=` 只有在全库不存在任何一对 (a, b) 使 `b.as_modifier + a.essence == a.as_modifier +
    b.essence` 时才不会随机翻红。36×35 全有序对实测零命中（2026-09-27，
    `python -c "from app.content.lenormand import CARDS; print(sum(1 for a in CARDS for b in
    CARDS if a.number != b.number and b.as_modifier + a.essence == a.as_modifier + b.essence))"`
    → `0`），故 ⑪ 的 `!=` 可以安全地吃随机发牌。
    """
    assert len(CARDS) == 36
    for first in CARDS:
        for second in CARDS:
            if first.number == second.number:
                continue
            forward = second.as_modifier + first.essence
            backward = first.as_modifier + second.essence
            assert forward != backward, (first.number, second.number)


# --- 判据 ⑨：大桌席位几何 --------------------------------------------------------

def test_grand_tableau_seats_are_four_rows_of_eight_plus_four_not_an_eight_by_eight_grid() -> None:
    """席位表几何：36 席互不重叠、行内计数 `[8, 8, 8, 8, 4]`、**明写这不是 8×8**。

    计划 Task 9 Step 3 原文写「Grand Tableau 8×8 布局落 36 枚」，那是措辞缺陷：代码
    （`content/lenormand.py` 的 `_grand_tableau`）走 `index < 32 → row=index//8` /
    `else: row, col = 4, index-32`，牌阵自己的 `description` 也印「四行八张外加末行四张」。
    裁定：以代码与表自陈为准（4×8+4），故这里把「不是 8×8」写成可执行断言 ——
    8×8 该有 64 席，这里的包围盒只有 5×8=40 格，其中 (4,4)..(4,7) 四格永不落牌。
    哪天有人「补齐 8 列」或改了 `index-32`，这条与判据 ⑪ 的邻位条数一起红。

    前端 `LenormandPage` 的网格按 `row`/`col` 落格；在 Task 9B 之前这两个字段一次都没被断言过。
    复测：`pytest tests/golden/test_lenormand_golden.py -k eight_by_eight`。
    """
    positions = SPREADS["grand_tableau"].positions
    assert len(positions) == 36
    cells = [(pos.row, pos.col) for pos in positions]
    assert len(set(cells)) == 36, "两席共用一格 → 前端网格互相覆盖"

    assert [pos.key for pos in positions] == [f"seat-{n:02d}" for n in range(1, 37)]
    assert [pos.label_zh for pos in positions] == [f"第{n}位" for n in range(1, 37)]

    rowcounts = [count for _, count in sorted(Counter(pos.row for pos in positions).items())]
    assert rowcounts == [8, 8, 8, 8, 4]
    assert max(pos.row for pos in positions) == 4
    assert max(pos.col for pos in positions) == 7

    last_row = [(pos.col, pos.key) for pos in positions if pos.row == 4]
    assert sorted(last_row) == [(0, "seat-33"), (1, "seat-34"), (2, "seat-35"), (3, "seat-36")]

    # 不是 8×8：包围盒 40 格、36 席，缺的四格全在末行右侧（行计数 [8,8,8,8,4] 与末行席位
    # 两条已在上面钉死，这里补齐包围盒那半边）。
    bounding_box = {(row, col) for row in range(5) for col in range(8)}
    assert bounding_box - set(cells) == {(4, 4), (4, 5), (4, 6), (4, 7)}


# --- 判据 ⑩：三种 layout 的组合语义各自分岔 --------------------------------------

def test_the_box_reads_its_centre_against_every_other_seat() -> None:
    """`box`（九宫阵）：恒 8 条、`left` 全是中心 `heart`、`context` 全含「核心」。

    中心是 (1,1) 那一席，环它 8 席。那个 8 是「八面环绕」的算术，不是 N−1 —— 九宫阵恰好在
    N=9 时两者同号（容易被误当成线读家族），所以这里钉的是「`left` 恒为中心席 + 逐字
    context 序列」而不是条数本身。context 按发牌顺序（过去 → 显象 → 未来 → 内因 → 外缘 →
    根基 → 隐情 → 归宿）逐字钉住，前端直接印这一串。
    复测：`pytest tests/golden/test_lenormand_golden.py -k box_reads_its_centre`。
    """
    reading = draw_lenormand(spread_id="nine_card")
    centre = next(card for card in reading.cards if card.position_key == "heart")
    assert (centre.row, centre.col) == (1, 1)

    combos = reading.combinations
    assert len(combos) == 8
    assert [combo.context for combo in combos] == [
        "核心 × 过去", "核心 × 显象", "核心 × 未来", "核心 × 内因",
        "核心 × 外缘", "核心 × 根基", "核心 × 隐情", "核心 × 归宿",
    ]
    assert {combo.left.number for combo in combos} == {centre.number}
    ring = {card.number for card in reading.cards} - {centre.number}
    assert {combo.right.number for combo in combos} == ring


def test_the_box_falls_back_to_a_line_read_when_it_has_no_centre() -> None:
    """`_box_combinations` 的 `centre is None` 分支：过去是死代码，形状决定「几条组合」。

    这条不是给生产路径写的 —— `nine_card` 的表里永远有 `heart` 席，`draw_lenormand` 走不到
    这个分支。钉它的理由是：分支一旦哪天被别的牌阵（例如未来的 6 张 box）走到，退出来的
    是 N−1 线读而不是 0 条，而这是没有任何测说过的。做法是把中心席的 `position_key` 改掉，
    直接调私有组合件（直调私有件在测里有先例：`_midpoint`、`_cross_aspects`、`_sidereal_flags`）。
    """
    nine = draw_lenormand(spread_id="nine_card")
    headless = [card.model_copy(update={"position_key": "no-heart"})
                if card.position_key == "heart" else card for card in nine.cards]
    combos = _box_combinations(headless)
    assert len(combos) == 8, "9 张退成线读 = 8 对，不是 0 条也不是 9 条"
    assert [combo.context for combo in combos] == [
        "过去 → 显象", "显象 → 未来", "未来 → 内因", "内因 → 核心",
        "核心 → 外缘", "外缘 → 根基", "根基 → 隐情", "隐情 → 归宿",
    ]
    assert [(combo.left.number, combo.right.number) for combo in combos] == [
        (a.number, b.number) for a, b in zip(headless, headless[1:])
    ]


def test_the_tableau_without_a_significator_falls_back_to_the_first_row_only() -> None:
    """大桌无指示牌：**恰 7 条**，恰为首行线读 `第1位 → 第2位` … `第7位 → 第8位`。

    这个 fallback 直接决定「无性别输入时页面显示几条组合」，今天无测。它必须是 7 而不是 35：
    引擎取 `row == 0` 的 8 席按 `col` 排序做线读（`_tableau_combinations`），而不是全桌两两配对。
    与判据 ⑩ 的另一支同源 —— 无指示牌时 `significator` 为 null，前端那一块整段不渲染。
    """
    reading = draw_lenormand(spread_id="grand_tableau")
    assert reading.significator is None
    assert sum(1 for card in reading.cards if card.is_significator) == 0

    combos = reading.combinations
    assert len(combos) == 7, "首行 8 席 = 7 对，不是 35 对全桌配对"
    assert [combo.context for combo in combos] == [f"第{i}位 → 第{i + 1}位" for i in range(1, 8)]
    first_row = sorted((c for c in reading.cards if c.row == 0), key=lambda c: c.col)
    assert len(first_row) == 8
    assert [(combo.left.number, combo.right.number) for combo in combos] == [
        (a.number, b.number) for a, b in zip(first_row, first_row[1:])
    ]
    # `CardRef` 不带行列（只有 number/name_zh/essence），故按编号回查本次发牌的席位。
    row_by_number = {c.number: c.row for c in reading.cards}
    assert {row_by_number[combo.left.number] for combo in combos} == {0}
    assert {row_by_number[combo.right.number] for combo in combos} == {0}


# --- 判据 ⑪：指示牌四正邻位（确定性边界几何） -------------------------------------

#: 四正邻位的 `context` →（邻席相对指示牌的位移, 邻席在组合里的角色）。
#: 顺序即引擎的发射顺序：之前 → 之后 → 之上 → 之下（`_tableau_combinations`）。
LEGS: dict[str, tuple[tuple[int, int], str]] = {
    "指示牌之前 · 近过去": ((0, -1), "subject"),
    "指示牌之后 · 近未来": ((0, 1), "modifier"),
    "指示牌之上 · 显意识": ((-1, 0), "modifier"),
    "指示牌之下 · 潜意识": ((1, 0), "modifier"),
}

#: 六个席位的 (row, col) 与逐一手算的 `context` 序列。
#: 2026-09-27 实测；(row, col) 与 context 序列两侧都被本测的断言当场复核（本测即复测：
#: `pytest tests/golden/test_lenormand_golden.py -k orthogonal_neighbours_that_exist`）。
#: 选这六个是因为它们把边界穷尽了：左上角、右上角、内席、末行左端、以及只有 4 席的末行两端。
SIGNIFICATOR_LEGS: dict[str, tuple[tuple[int, int], tuple[str, ...]]] = {
    "seat-01": ((0, 0), ("指示牌之后 · 近未来", "指示牌之下 · 潜意识")),
    "seat-08": ((0, 7), ("指示牌之前 · 近过去", "指示牌之下 · 潜意识")),
    "seat-10": ((1, 1), ("指示牌之前 · 近过去", "指示牌之后 · 近未来",
                         "指示牌之上 · 显意识", "指示牌之下 · 潜意识")),
    "seat-25": ((3, 0), ("指示牌之后 · 近未来", "指示牌之上 · 显意识", "指示牌之下 · 潜意识")),
    "seat-33": ((4, 0), ("指示牌之后 · 近未来", "指示牌之上 · 显意识")),
    "seat-36": ((4, 3), ("指示牌之前 · 近过去", "指示牌之上 · 显意识")),
}


@pytest.fixture(scope="module")
def tableau_cards() -> list[DrawnCard]:
    """一次真实的 36 张大桌发牌，供下面的边界几何复用。

    抽牌是 CSPRNG（AGENTS §5）不可控，但邻位**条数与方位**只由 `(row, col)` 决定，牌面是谁
    不影响 —— 于是「取一次真实发牌 + `model_copy` 翻 `is_significator` 旗标」就是拿到确定性
    几何的正确做法：不 stub 响应、不 patch 随机源（AGENTS §9 无 mock）。
    """
    return draw_lenormand(spread_id="grand_tableau").cards


def _seat(cards: list[DrawnCard], seat: str) -> DrawnCard:
    return next(card for card in cards if card.position_key == seat)


def _legs_with_significator(cards: list[DrawnCard], seat: str) -> list[Combination]:
    """把指定席标成指示牌后直调组合件 —— 私有件在测里直调有先例（见上一条测的 docstring）。"""
    tagged = [card.model_copy(update={"is_significator": card.position_key == seat}) for card in cards]
    return _tableau_combinations(tagged)


@pytest.mark.parametrize("seat", list(SIGNIFICATOR_LEGS))
def test_the_significator_reads_only_the_orthogonal_neighbours_that_exist(
    tableau_cards: list[DrawnCard], seat: str
) -> None:
    """六个边界席位逐一手算：条数、`context` 序列、每一腿另一端是哪张牌。

    这是本包唯一真正的算术锚 —— 纯几何，与抽到哪张牌无关：
    seat-01 (0,0) 只有右与下 → 2；seat-08 (0,7) 只有左与下 → 2；seat-10 (1,1) 四正 → 4；
    seat-25 (3,0) 左无、余三条 → 3；seat-33 (4,0) 与 seat-36 (4,3) 下方无席（末行是第 4 行，
    第 5 行不存在）→ 各 2。「没有对角腿、没有越界腿」不由条数说话，而由下面那条逐腿对拍
    说话：每一腿的另一端必须等于该方位上真实存在的那张牌，方位错了、角色反了都红。
    末行只有 4 席一旦哪天被补齐，seat-33/36 会多出「之下」腿，此测立刻红。
    """
    (row, col), expected_contexts = SIGNIFICATOR_LEGS[seat]
    sig = _seat(tableau_cards, seat)
    assert (sig.row, sig.col) == (row, col), seat
    assert sig.is_significator is False, "夹具本身不预置旗标 —— 翻旗标是本测的动作"

    combos = _legs_with_significator(tableau_cards, seat)
    assert [combo.context for combo in combos] == list(expected_contexts), seat

    by_cell = {(card.row, card.col): card for card in tableau_cards}
    for combo in combos:
        (dr, dc), neighbour_role = LEGS[combo.context]
        neighbour = by_cell[(sig.row + dr, sig.col + dc)]
        if neighbour_role == "subject":  # 「之前」：邻席是被读的主词，指示牌修饰它
            assert (combo.left.number, combo.right.number) == (neighbour.number, sig.number)
        else:
            assert (combo.left.number, combo.right.number) == (sig.number, neighbour.number)
    assert all(combo.left.number != combo.right.number for combo in combos)


def test_every_seat_reads_exactly_its_own_orthogonal_neighbours(tableau_cards: list[DrawnCard]) -> None:
    """36 席全扫：条数 == 该席四正方向上真实存在的邻席数（与手算六点互补）。

    六条手算穷尽的是边界形状，这一条穷尽的是**每一条腿**：把「引擎给的条数」与「按 `(row, col)`
    索引独立数出来的邻格数」逐席对拍。它红得比手算那六条更早 —— 加了对角邻位、或把同列上下
    写成了同行左右，第一个内席就会露馅。
    """
    by_cell = {(card.row, card.col): card for card in tableau_cards}
    assert len(by_cell) == 36
    for card in tableau_cards:
        expected = sum(1 for dr, dc in ((0, -1), (0, 1), (-1, 0), (1, 0))
                       if (card.row + dr, card.col + dc) in by_cell)
        combos = _legs_with_significator(tableau_cards, card.position_key)
        assert len(combos) == expected, card.position_key


def test_a_combination_phrase_qualifies_the_subject_with_the_modifier(tableau_cards: list[DrawnCard]) -> None:
    """判据 ⑪ 的方向半边：`phrase` = 右牌的 `as_modifier` + 左牌的 `essence`，反向必不相等。

    「后牌修饰前牌」这句话现在写在三处（`_combine` 的注释、`Combination` 的 docstring、
    `schemas/lenormand.py` 里 `phrase` 的 description），但没有一条测把它变成可执行契约。
    本测取 seat-10 那 4 条腿逐条验算。

    **为什么锚必须回查 `content.lenormand.CARDS` 而不是照 description 用 `right.as_modifier`**：
    `CardRef` 只有 `number`/`name_zh`/`essence` 三个字段，响应里**取不到** `as_modifier`
    （实测 `AttributeError: 'CardRef' object has no attribute 'as_modifier'`，findings F-A2-17），
    而 description 却印着 "``right.as_modifier + left.essence``" —— 契约字面比响应形状多一个字段。
    最后那条 `"as_modifier" not in model_dump()` 就是这一缺口的哨兵：若 F-A2-17 以「给 CardRef
    补 `as_modifier`」修法落地，它会红，届时请把本测改成响应内自证，而不是删掉。
    """
    combos = _legs_with_significator(tableau_cards, "seat-10")
    assert len(combos) == 4
    modifier_by_number = {card.number: card.as_modifier for card in CARDS}
    essence_by_number = {card.number: card.essence for card in CARDS}
    for combo in combos:
        forward = modifier_by_number[combo.right.number] + essence_by_number[combo.left.number]
        reversed_ = modifier_by_number[combo.left.number] + essence_by_number[combo.right.number]
        assert combo.phrase == forward, combo.context
        assert combo.phrase != reversed_, combo.context
    assert "as_modifier" not in combos[0].left.model_dump(), (
        "CardRef 一旦补上 as_modifier（F-A2-17 修法①），本测应改为响应内自证")


# --- 白话段（多系统白话计划 Task 8）：随机源之下的自洽对账 ------------------------------

@pytest.mark.parametrize("spread_id", sorted(SPREAD_SIZES))
def test_plain_summary_is_the_opener_plus_one_line_per_drawn_card(spread_id: str) -> None:
    """G27 的雷诺曼版等式：行数 == 牌位数 + 1（开篇句），且逐行按位序对得上。

    `SPREAD_SIZES[spread_id]`（`:35`）是本文件既有的牌位数表，与 `LENORMAND.openers`
    一起把「五阵都能出段」钉死：任何一阵少了开篇句或丢了一张牌，等式立刻掉。
    """
    reading = draw_lenormand(spread_id=spread_id)
    lines = reading.plain_summary.split("\n")
    assert len(lines) == SPREAD_SIZES[spread_id] + 1, spread_id
    assert lines[0] == LENORMAND.openers[spread_id], spread_id
    assert lines[1:] == [LENORMAND.entries[card.card_id] for card in reading.cards]


@pytest.mark.parametrize("spread_id", sorted(SPREAD_SIZES))
def test_every_plain_line_comes_out_of_the_corpus_and_nowhere_else(spread_id: str) -> None:
    """段里的每一行都是语料表里的某一句（装配器不产新句子，spec §5）。"""
    lines = draw_lenormand(spread_id=spread_id).plain_summary.split("\n")
    corpus_lines = set(LENORMAND.entries.values()) | set(LENORMAND.openers.values())
    assert all(line in corpus_lines for line in lines)


def test_the_grand_tableau_retells_all_thirty_six_cards_exactly_once() -> None:
    """大桌是全 36 张：白话段必须正好覆盖全集，一张不多一张不少。

    这是「宁崩不漏」在雷诺曼侧的整盘版——`_RNG.sample` 无放回发满 36 位
    （`engines/lenormand.py:65`），所以这一条不依赖随机结果。
    """
    lines = draw_lenormand(spread_id="grand_tableau").plain_summary.split("\n")
    assert len(lines) == 37
    assert sorted(lines[1:]) == sorted(LENORMAND.entries.values())


def test_the_two_significator_cards_still_get_a_sentence() -> None:
    """0 极性的两张指示牌（28 男人 / 29 女人）在白话里照旧有句子。

    `grouping="keep"` 的实证：把它们交给 `band` 会当场 `ValueError`（符号为 0），
    而「按极性分带但跳过 0」这种写法会让这两张牌在整盘里静默掉句——这条测就是为
    了让第二种写法也红（偏差表第 1 行的雷诺曼半边，G21）。
    """
    lines = draw_lenormand(spread_id="grand_tableau").plain_summary.split("\n")
    for card in CARDS:
        if card.polarity == 0:
            assert LENORMAND.entries[card.id] in lines, card.number


def test_the_plain_summary_and_the_synthesis_are_two_different_texts() -> None:
    """白话不是 `synthesis` 的副本：两处并存、互不覆盖（spec §8 丙组的呈现前提）。"""
    reading = draw_lenormand(spread_id="three_card")
    assert reading.synthesis
    assert reading.plain_summary != reading.synthesis


# --- 综合结论卡片（verdict）：纯计数快照钉五档，真实发牌只钉结构自洽 ---------------------

#: (积极, 消极, 中性) → (档位, 星级)。发牌是 CSPRNG 不可控，故档位分布由纯函数 `build_verdict`
#: 的构造计数钉住（无 mock：计数是引擎同一公式的输入，不桩响应）。五档各落一例。
VERDICT_SNAPSHOTS: tuple[tuple[int, int, int, str, int], ...] = (
    (5, 0, 0, "大吉", 5),
    (3, 0, 0, "吉", 4),
    (2, 1, 0, "平", 3),
    (1, 2, 0, "小凶", 2),
    (0, 3, 0, "凶", 1),
)


@pytest.mark.parametrize("positive, negative, neutral, grade, stars", VERDICT_SNAPSHOTS)
def test_verdict_snapshot_is_pinned(
    positive: int, negative: int, neutral: int, grade: str, stars: int
) -> None:
    """五个计数组合的结论卡片逐字段钉死（确定性快照，不经过随机发牌）。"""
    verdict = build_verdict(positive, negative, neutral)
    assert verdict.grade == grade
    assert verdict.stars == stars
    assert verdict.headline.startswith(f"你这一阵抽出的牌属{grade}：")
    assert verdict.points == [
        f"积极牌 {positive} 张",
        f"消极牌 {negative} 张",
        f"中性牌 {neutral} 张",
    ]
    assert verdict.advice.endswith("。")


@pytest.mark.parametrize("spread_id", sorted(SPREAD_SIZES))
def test_real_draw_verdict_is_self_consistent(spread_id: str) -> None:
    """真实发牌只钉结构自洽：档位/星级与计数推出的分数一致，headline 复述档位与三项计数。"""
    reading = draw_lenormand(spread_id=spread_id)
    verdict = reading.verdict
    expected_grade, expected_stars = grade_for(
        max(0.0, min(100.0, 50.0 + POLARITY_WEIGHT * (reading.positive_count - reading.negative_count)))
    )
    assert verdict.grade == expected_grade
    assert verdict.stars == expected_stars
    assert f"积极牌{reading.positive_count}张" in verdict.headline
    assert f"消极牌{reading.negative_count}张" in verdict.headline
    assert f"中性牌{reading.neutral_count}张" in verdict.headline
    assert verdict.points == [
        f"积极牌 {reading.positive_count} 张",
        f"消极牌 {reading.negative_count} 张",
        f"中性牌 {reading.neutral_count} 张",
    ]


