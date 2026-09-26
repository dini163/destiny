"""引擎不变式（spec §9.2）：恒等式、四模态、1..200 全枚举、账本可核对、缺值不编数。"""

import pytest

from app.content import CONTENT_VERSION
from app.content.kangxi_strokes import lookup
from app.core.errors import DestinyError, NameInputError
from app.core.provenance import MODEL_PARAM_SOURCE
from app.engines import name_numerology as engine
from app.engines.name_numerology import (
    GRID_ORDER,
    GRID_WEIGHTS,
    WAI_FORMULA,
    analyze_name,
    cycle_number,
    grid_values,
    grids_of,
    modality_of,
    name_provenance,
    name_score,
    number_element,
    number_yinyang,
)


def _strokes(text: str) -> list[int]:
    values = [lookup(char).kangxi_strokes for char in text]
    assert all(isinstance(value, int) for value in values), text
    return values


def _terms(surname: str, given: str) -> dict[str, engine.GridTerm]:
    return {term.key: term for term in grids_of(_strokes(surname), _strokes(given))}


def test_name_input_error_carries_machine_readable_context() -> None:
    """422 的候选列表走 `context`，前端按它渲染按钮；文案不是接口。"""
    error = NameInputError("not_han", "只能使用汉字。", {"chars": ["L"]})
    assert (error.status_code, error.code, error.context) == (422, "not_han", {"chars": ["L"]})
    assert DestinyError("不带 context 的既有错误").context is None


def test_cycle_number_wraps_at_eighty_one() -> None:
    """81 循环：81→81，82→1，162→81（spec 决策五）。"""
    for total in range(1, 201):
        assert 1 <= cycle_number(total) <= 81
    assert (cycle_number(81), cycle_number(82), cycle_number(162)) == (81, 1, 81)


def test_element_follows_the_last_digit_rule() -> None:
    expected = {1: "木", 2: "木", 3: "火", 4: "火", 5: "土", 6: "土", 7: "金", 8: "金", 9: "水", 0: "水"}
    for total in range(1, 201):
        assert number_element(total) == expected[cycle_number(total) % 10], total


def test_yinyang_follows_parity() -> None:
    for total in range(1, 201):
        assert number_yinyang(total) == ("阳" if cycle_number(total) % 2 else "阴"), total


def test_modality_labels() -> None:
    assert modality_of(1, 1)[0] == "单姓单名"
    assert modality_of(1, 2)[0] == "单姓复名"
    assert modality_of(2, 1)[0] == "复姓单名"
    assert modality_of(2, 3)[0] == "复姓复名"


def test_single_surname_single_name_yields_outer_grid_one() -> None:
    """统一式 `外格 = 总格 − 人格 + 1` 在单姓单名下必须得数理 1（天地开泰）。"""
    assert grid_values(_strokes("李"), _strokes("白"))["wai"] == 1


def test_identities_hold_for_every_sampled_name() -> None:
    names = [("李", "白"), ("張", "三"), ("歐陽", "龍"), ("陸", "青玄"), ("司馬", "相如"), ("王", "一")]
    for surname, given in names:
        surname_strokes, given_strokes = _strokes(surname), _strokes(given)
        grids = grid_values(surname_strokes, given_strokes)
        assert grids["zong"] == sum(surname_strokes) + sum(given_strokes)
        assert grids["ren"] == surname_strokes[-1] + given_strokes[0]
        assert grids["wai"] == grids["zong"] - grids["ren"] + 1
        expected_di = given_strokes[0] + 1 if len(given_strokes) == 1 else sum(given_strokes)
        assert grids["di"] == expected_di
        expected_tian = (
            surname_strokes[0] + 1 if len(surname_strokes) == 1
            else surname_strokes[0] + surname_strokes[-1]
        )
        assert grids["tian"] == expected_tian


def test_every_grid_echoes_the_arithmetic_it_used() -> None:
    """算式是这一格可核对的唯一凭据（spec §6.2）：`16+8` 说明人格取姓末 16、名首 8。"""
    terms = _terms("陸", "青玄")
    assert [terms[key].formula for key in GRID_ORDER] == ["16+1", "16+8", "8+5", "29−24+1", "16+8+5"]
    assert [terms[key].value for key in GRID_ORDER] == [17, 24, 13, 6, 29]


def test_uncomputable_outer_grid_states_the_relation_not_a_fake_formula() -> None:
    """减法式算不出数字时退回关系串 `总格−人格+1`，不写 `?−?+1` 冒充算式。

    5 画即 王（玉部 5 画）；第二字留 None，等价于用户输入了语料外的字。
    """
    terms = {term.key: term for term in grids_of([5], [None])}
    assert terms["tian"].formula == "5+1" and terms["tian"].value == 6
    assert terms["wai"].formula == WAI_FORMULA and terms["wai"].value is None
    assert terms["zong"].formula == "5+?" and terms["zong"].value is None


def test_missing_stroke_propagates_without_placeholder() -> None:
    """未收录字 ⇒ 受影响格为 None，不得变成 0。"""
    assert grid_values([7, None], [None, 5]) == dict.fromkeys(GRID_ORDER)


def test_weights_sum_to_one_so_the_index_is_a_percentage() -> None:
    assert round(sum(GRID_WEIGHTS.values()), 10) == 1.0


def test_score_ledger_has_one_row_per_grid_and_sums_to_value() -> None:
    score = name_score({"tian": 17, "ren": 24, "di": 13, "wai": 6, "zong": 29})
    assert score is not None
    rules = [factor.rule for factor in score.factors]
    assert rules[0] == "score.base"
    assert rules[1:] == [f"name.grid.{key}" for key in GRID_ORDER]
    assert score.value == pytest.approx(round(sum(factor.delta for factor in score.factors), 2))
    assert score.factors[0].source == MODEL_PARAM_SOURCE
    for factor in score.factors[1:]:
        # 权重是本系统参数、吉凶等级来自 81 表：两段出处必须同排（spec §7 诚实条款）。
        assert MODEL_PARAM_SOURCE in factor.source
        assert "数理" in factor.source and "八十一" in factor.source


def test_score_is_withheld_when_any_grid_is_missing() -> None:
    """spec §8.2 规则 3：五格任一缺 ⇒ 整个 score 不出，不给打折分。"""
    assert name_score({"tian": 17, "ren": 24, "di": None, "wai": 6, "zong": 29}) is None


def test_provenance_lists_the_three_name_corpora() -> None:
    provenance = name_provenance()
    assert [table.name for table in provenance.tables] == [
        "kangxi_strokes",
        "name_numerology",
        "name_sancai",
    ]
    assert {table.version for table in provenance.tables} == {CONTENT_VERSION}
    assert provenance.corpus.size > 30_000


def test_name_sources_never_leak_into_the_bazi_table_list() -> None:
    """`CONTENT_SOURCES` 会被八字引擎整表回显；两套语料必须分列，否则八字冒领出处。"""
    from app.content import CONTENT_SOURCES, NAME_CONTENT_SOURCES

    assert {name for name, _ in CONTENT_SOURCES}.isdisjoint({name for name, _ in NAME_CONTENT_SOURCES})


def test_unused_variant_is_a_no_op() -> None:
    """前端会把已选过的正体一路带着提交；这次用不上的键不是错误。"""
    assert analyze_name("王", "青", {"发": "發"}).input.resolved_traditional == "王青"


def test_variant_for_a_char_the_corpus_does_not_cover_is_an_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """用户点名要的字不在语料里 ⇒ 422 机器码，绝不静默降级成 None。

    真实语料里所有"一简对多繁"的候选都在范围内，这个分支只能打桩走到。打桩的是
    `lookup` 这一个纯查询函数，不是任何领域数据——项目铁律禁的是假语料。
    """
    real_lookup = engine.lookup
    monkeypatch.setattr(
        engine, "lookup", lambda char: None if char == "發" else real_lookup(char)
    )
    with pytest.raises(DestinyError) as caught:
        analyze_name("王", "发财", {"发": "發"})
    assert caught.value.code == "stroke_unresolved"
    assert caught.value.context == {"field": "given", "char": "发", "resolved": "發"}