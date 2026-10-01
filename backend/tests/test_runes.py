"""Rune draw engine properties (卢恩 spec §9.2).

The organising question here is not "does the engine return something plausible"
but "can it return the things it must never return". Two of those are checked
structurally rather than statistically:

* A symmetric rune landing reversed. The statistical test (600 casts) would only
  ever show that it *did not happen yet*. The stronger test patches the RNG and
  asserts ``choice`` is **never called** for a symmetric stone -- the engine does
  not generate the combination and then filter it, it declines to ask.
* A score or a percentage. Those are checked by walking the response model's
  field names, so adding one anywhere in the tree fails the suite.

Statistical tests use counts high enough that a real bug is near-certain to
show, and low enough that the suite stays fast.
"""

import re

import pytest

from app.content.rune_futhark import (
    AETT_NAMES,
    AETT_NAMES_ZH,
    DECK_24,
    DECK_25,
    get_rune,
)
from app.content.rune_spreads import SPREAD_IDS, SPREADS
from app.core.errors import UnsupportedMethodError
from app.engines import runes as runes_engine
from app.engines.runes import UNASSIGNED_KEY, draw
from app.schemas.runes import RuneCastResponse

#: 每种牌阵抽这么多次来验「不放回」与「键序对齐」。
CASTS_FOR_STRUCTURE = 50

#: 验「对称符永不逆位」要抽得更多：三分之一的符文对称，200 次足以让真 bug 现形。
CASTS_FOR_ORIENTATION = 200

SYMMETRIC_KEYS = frozenset({
    "gebo", "hagalaz", "isa", "jera", "eihwaz", "sowilo", "ingwaz", "dagaz",
})


class FixedRNG:
    """Deterministic stand-in for `secrets.SystemRandom`.

    Records whether ``choice`` was called at all, which is the point: for a
    symmetric stone the engine must not even ask for an orientation.
    """

    def __init__(self, picks: list[str], orientation: str = "upright") -> None:
        self._picks = picks
        self._orientation = orientation
        self.choice_calls = 0

    def sample(self, population, k: int) -> list:
        by_key = {rune.key: rune for rune in population}
        return [by_key[key] for key in self._picks[:k]]

    def choice(self, seq):
        self.choice_calls += 1
        return self._orientation


@pytest.fixture
def fixed_rng(monkeypatch):
    def install(picks: list[str], orientation: str = "upright") -> FixedRNG:
        fake = FixedRNG(picks, orientation)
        monkeypatch.setattr(runes_engine, "_RNG", fake)
        return fake
    return install


# --- 入口约定 --------------------------------------------------------------


def test_draw_is_keyword_only() -> None:
    """位置参数会让 `draw("five", True, False, q)` 这种调用点看不出哪个开关是哪个。"""
    with pytest.raises(TypeError):
        draw("three")  # type: ignore[misc]


@pytest.mark.parametrize("bad_id", ["celtic_cross", "yggdrasil", "", "THREE"])
def test_unknown_spread_raises_domain_error(bad_id: str) -> None:
    with pytest.raises(UnsupportedMethodError):
        draw(spread_id=bad_id)


@pytest.mark.parametrize("spread_id", SPREAD_IDS)
def test_stone_count_matches_spread_size(spread_id: str) -> None:
    result = draw(spread_id=spread_id)
    assert len(result.stones) == SPREADS[spread_id].size
    assert len(result.drawn_keys) == SPREADS[spread_id].size


# --- 不放回与位次对齐 ------------------------------------------------------


@pytest.mark.parametrize("spread_id", SPREAD_IDS)
def test_stones_are_drawn_without_replacement(spread_id: str) -> None:
    for _ in range(CASTS_FOR_STRUCTURE):
        result = draw(spread_id=spread_id)
        assert len(set(result.drawn_keys)) == len(result.drawn_keys)


@pytest.mark.parametrize("spread_id", SPREAD_IDS)
def test_stones_follow_spread_position_order(spread_id: str) -> None:
    """`drawn_keys` 与 `stones` 同序，且逐位对上语料里那一种牌阵的位次。"""
    positions = SPREADS[spread_id].positions
    for _ in range(CASTS_FOR_STRUCTURE):
        result = draw(spread_id=spread_id)
        assert result.drawn_keys == [stone.key for stone in result.stones]
        assert [stone.position_key for stone in result.stones] == [p.key for p in positions]
        assert [stone.position_index for stone in result.stones] == list(range(len(positions)))
        assert [stone.position_label_zh for stone in result.stones] == [
            p.label_zh for p in positions
        ]


@pytest.mark.parametrize("spread_id", SPREAD_IDS)
def test_stone_text_matches_the_corpus_for_the_drawn_orientation(spread_id: str) -> None:
    """引擎不生成文字：卡面上的释义与关键词必须逐字等于语料里对应朝向那一份。"""
    for _ in range(CASTS_FOR_STRUCTURE):
        result = draw(spread_id=spread_id)
        for stone in result.stones:
            rune = get_rune(stone.key)
            assert stone.meaning == rune.meaning_for(stone.orientation)
            assert stone.keywords == list(rune.keywords_for(stone.orientation))
            assert stone.order == rune.order
            assert stone.glyph == rune.glyph
            assert stone.source == rune.source


# --- 逆位：结构上不可能，而非事后过滤 --------------------------------------


@pytest.mark.parametrize("spread_id", SPREAD_IDS)
def test_symmetric_runes_never_land_reversed(spread_id: str) -> None:
    for _ in range(CASTS_FOR_ORIENTATION):
        for stone in draw(spread_id=spread_id).stones:
            if not stone.reversible:
                assert stone.orientation == "upright", stone.name


@pytest.mark.parametrize("spread_id", SPREAD_IDS)
def test_symmetric_key_set_matches_the_corpus(spread_id: str) -> None:
    """响应里的 `reversible` 就是语料那一份，没有被引擎改写过。"""
    for stone in draw(spread_id=spread_id).stones:
        assert stone.reversible is (stone.key not in SYMMETRIC_KEYS)


def test_engine_never_asks_for_a_symmetric_stones_orientation(fixed_rng) -> None:
    """比统计更强的一条：对称符与空白符**连问都不问**朝向。

    `_orientation_for` 的守卫决定了 `choice` 根本不会被调用。若哪天有人把守卫挪成
    「先抽朝向、再在输出前过滤」，`choice_calls` 就会变成 3，这条当场红 ——
    而 600 次统计测对此毫无感觉，因为过滤后的输出仍然全是正位。
    """
    fake = fixed_rng(["gebo", "hagalaz", "isa"], orientation="reversed")
    result = draw(spread_id="three")
    assert fake.choice_calls == 0
    assert [stone.orientation for stone in result.stones] == ["upright"] * 3


def test_engine_does_ask_for_a_reversible_stones_orientation(fixed_rng) -> None:
    """对照组：三枚都可逆时必须问三次，否则上一条只是碰巧为真。"""
    fake = fixed_rng(["fehu", "uruz", "thurisaz"], orientation="reversed")
    result = draw(spread_id="three")
    assert fake.choice_calls == 3
    assert [stone.orientation for stone in result.stones] == ["reversed"] * 3


def test_mixed_draw_only_asks_for_the_reversible_ones(fixed_rng) -> None:
    """Wunjo/Sowilo 可逆？不：Sowilo 对称。三枚里两枚可逆，故只问两次。"""
    fake = fixed_rng(["wunjo", "sowilo", "gebo"], orientation="reversed")
    result = draw(spread_id="three")
    assert fake.choice_calls == 1
    orientations = {stone.key: stone.orientation for stone in result.stones}
    assert orientations == {"wunjo": "reversed", "sowilo": "upright", "gebo": "upright"}


@pytest.mark.parametrize("spread_id", SPREAD_IDS)
def test_allow_reversed_false_yields_all_upright(spread_id: str) -> None:
    for _ in range(CASTS_FOR_STRUCTURE):
        result = draw(spread_id=spread_id, allow_reversed=False)
        assert all(stone.orientation == "upright" for stone in result.stones)
        assert result.allow_reversed is False


def test_allow_reversed_false_never_calls_choice(fixed_rng) -> None:
    fake = fixed_rng(["fehu", "uruz", "thurisaz"])
    draw(spread_id="three", allow_reversed=False)
    assert fake.choice_calls == 0


def test_drawn_orientation_never_breaks_the_raising_accessor() -> None:
    """`meaning_for` 对「对称符 + reversed」是抛异常的；这条证明引擎永远走不到那里。"""
    for spread_id in SPREAD_IDS:
        for _ in range(CASTS_FOR_STRUCTURE):
            for stone in draw(spread_id=spread_id).stones:
                rune = get_rune(stone.key)
                assert rune.meaning_for(stone.orientation) == stone.meaning


# --- 空白符开关 ------------------------------------------------------------


def test_wyrd_absent_and_deck_is_24_when_disabled() -> None:
    for _ in range(CASTS_FOR_ORIENTATION):
        result = draw(spread_id="five", include_wyrd=False)
        assert "wyrd" not in result.drawn_keys
        assert result.provenance.deck_size == 24
        assert result.include_wyrd is False


def test_deck_is_25_when_wyrd_enabled() -> None:
    result = draw(spread_id="three", include_wyrd=True)
    assert result.provenance.deck_size == 25
    assert result.include_wyrd is True


def test_wyrd_can_actually_be_drawn_when_enabled() -> None:
    """开着开关抽 400 次五石阵，若一次都没抽到空白符，说明牌组根本没换成 25 枚。"""
    seen = False
    for _ in range(400):
        if "wyrd" in draw(spread_id="five", include_wyrd=True).drawn_keys:
            seen = True
            break
    assert seen, "Wyrd never appeared in 400 five-stone casts with the toggle on"


def test_wyrd_is_always_upright_when_drawn(fixed_rng) -> None:
    fake = fixed_rng(["wyrd", "fehu", "uruz"], orientation="reversed")
    result = draw(spread_id="three", include_wyrd=True)
    wyrd_stone = next(s for s in result.stones if s.is_wyrd)
    assert wyrd_stone.orientation == "upright"
    assert wyrd_stone.glyph == ""
    assert fake.choice_calls == 2  # 只为 fehu 与 uruz 问了朝向，没为空白符问


def test_wyrd_is_flagged_modern_in_the_synthesis(fixed_rng) -> None:
    fixed_rng(["wyrd", "gebo", "isa"], orientation="upright")
    result = draw(spread_id="three", include_wyrd=True)
    assert "现代增补" in result.synthesis
    assert "非古传统" in result.synthesis


# --- ætt 配比 --------------------------------------------------------------


@pytest.mark.parametrize("spread_id", SPREAD_IDS)
def test_aett_balance_always_has_four_rows(spread_id: str) -> None:
    """三组 + 空白符桶，count 为 0 也照列 —— 0 是真实值，不是缺失。"""
    for _ in range(CASTS_FOR_STRUCTURE):
        rows = draw(spread_id=spread_id).aett_balance
        assert [row.key for row in rows] == ["freyja", "heimdall", "tyr", UNASSIGNED_KEY]


def test_aett_counts_sum_to_the_number_of_stones() -> None:
    for spread_id in SPREAD_IDS:
        for include_wyrd in (False, True):
            for _ in range(CASTS_FOR_STRUCTURE):
                result = draw(spread_id=spread_id, include_wyrd=include_wyrd)
                assert sum(row.count for row in result.aett_balance) == len(result.stones)


def test_wyrd_goes_to_the_unassigned_bucket_only(fixed_rng) -> None:
    fixed_rng(["wyrd", "gebo", "isa"], orientation="upright")
    result = draw(spread_id="three", include_wyrd=True)
    rows = {row.key: row.count for row in result.aett_balance}
    assert rows[UNASSIGNED_KEY] == 1
    assert rows["freyja"] == 1  # Gebo
    assert rows["heimdall"] == 1  # Isa
    assert rows["tyr"] == 0


def test_wyrd_is_never_counted_into_a_real_aett() -> None:
    """空白符 `aett is None`，故它绝不能让任何一组的计数虚增。"""
    for _ in range(CASTS_FOR_ORIENTATION):
        result = draw(spread_id="five", include_wyrd=True)
        wyrd_drawn = "wyrd" in result.drawn_keys
        rows = {row.key: row.count for row in result.aett_balance}
        real_total = sum(rows[key] for key in AETT_NAMES)
        assert real_total == len(result.stones) - (1 if wyrd_drawn else 0)
        assert rows[UNASSIGNED_KEY] == (1 if wyrd_drawn else 0)


def test_aett_labels_come_from_the_corpus() -> None:
    rows = draw(spread_id="single").aett_balance
    for row in rows:
        if row.key == UNASSIGNED_KEY:
            continue
        assert row.name == AETT_NAMES[row.key]
        assert row.name_zh == AETT_NAMES_ZH[row.key]


# --- 综合直读 --------------------------------------------------------------


def rune_name_pattern(name: str) -> re.Pattern[str]:
    """词边界匹配，免得 `Isa` 这类短名撞上英文单词里的字母串。"""
    return re.compile(rf"(?<![A-Za-z]){re.escape(name)}(?![A-Za-z])")


@pytest.mark.parametrize("spread_id", SPREAD_IDS)
def test_synthesis_names_no_rune_that_was_not_drawn(spread_id: str) -> None:
    """防「拼进了没抽到的符文」—— 那会是引擎在凭空断言。"""
    for _ in range(CASTS_FOR_STRUCTURE):
        result = draw(spread_id=spread_id)
        drawn = set(result.drawn_keys)
        for rune in DECK_25:
            if rune.key in drawn:
                continue
            assert not rune_name_pattern(rune.name).search(result.synthesis), rune.name


@pytest.mark.parametrize("spread_id", SPREAD_IDS)
def test_synthesis_mentions_every_drawn_rune(spread_id: str) -> None:
    """反过来也要成立：抽到的每一枚都得在直读里出现，否则等于漏读了一位。"""
    for _ in range(CASTS_FOR_STRUCTURE):
        result = draw(spread_id=spread_id)
        for rune_name in (get_rune(key).name for key in result.drawn_keys):
            assert rune_name in result.synthesis, rune_name


def test_synthesis_leads_with_the_question_when_given() -> None:
    result = draw(spread_id="single", question="该不该换工作")
    assert "该不该换工作" in result.synthesis
    assert result.question == "该不该换工作"


def test_synthesis_says_so_when_no_question_is_given() -> None:
    assert "未附所问" in draw(spread_id="single").synthesis


def test_synthesis_states_the_orientation_of_each_stone() -> None:
    """直读里必须逐枚说清正逆，否则读者无从知道卡面读的是哪一面。

    按引擎的句式逐字核（「…落得{name_zh}（{name}，{正位|逆位}）」），
    而不是只数一下全文里有没有「逆位」两个字 —— 后者即使漏读了某一枚也会通过。
    """
    for _ in range(CASTS_FOR_STRUCTURE):
        result = draw(spread_id="five", allow_reversed=True)
        for stone in result.stones:
            if stone.is_wyrd:
                continue  # 空白符无正逆之分，句式也不同
            orientation_zh = "逆位" if stone.orientation == "reversed" else "正位"
            expected = f"{stone.name_zh}（{stone.name}，{orientation_zh}）"
            assert expected in result.synthesis, expected


@pytest.mark.parametrize("spread_id", SPREAD_IDS)
def test_synthesis_leads_with_the_chinese_name_of_every_stone(spread_id: str) -> None:
    """中文牌名为主、英文名为括注（spec §7：英文牌名裸夹中文是这条直读的主要病灶）。

    按引擎的新句式逐字核「…落得{name_zh}（{name}，{正位|逆位}）」，
    而不是数全文里有没有中文牌名——后者即使漏改一枚也会通过。
    """
    for _ in range(CASTS_FOR_STRUCTURE):
        result = draw(spread_id=spread_id, allow_reversed=True)
        for stone in result.stones:
            if stone.is_wyrd:
                continue  # 空白符无正逆之分，句式另有一条
            orientation_zh = "逆位" if stone.orientation == "reversed" else "正位"
            expected = f"{stone.name_zh}（{stone.name}，{orientation_zh}）"
            assert expected in result.synthesis, expected


@pytest.mark.parametrize("spread_id", SPREAD_IDS)
def test_synthesis_has_no_nested_colon_and_no_keyword_restatement(spread_id: str) -> None:
    """两层冒号与关键词复述同源于「要点为…」那半句，删掉它就同时治了两条（spec §7）。

    上限是 1 而不是 0：语料自己的释义每句里就带一个冒号（「可动之财与原始动力：钱、物、
    精力与手上已有的资源。…」，复测：`cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c
    "from app.content.rune_futhark import DECK_25; print(max(s.count('：') for r in DECK_25 for s in ((r.upright_meaning or '') + '|' + (r.reversed_meaning or '')).split('。')))"` → 1），
    判语一字不许改（G2），所以只能要求「一层」。今天这条必红：旧句式在同一个语料句之前
    又加了 `要点为{keywords}：`，那一节里有两个冒号。
    """
    for _ in range(CASTS_FOR_STRUCTURE):
        result = draw(spread_id=spread_id)
        assert "要点为" not in result.synthesis
        for clause in result.synthesis.split("。"):
            assert clause.count("：") <= 1, clause


#: 空白句的确定性填充符：全是字形对称的符文，`_orientation_for` 对它们连熵源都不问，
#: 所以整句逐字可预期 —— 不必靠循环抽 400 次碰运气（`fixed_rng` 在本文件就是这个用途）。
_WYRD_FILLER_KEYS = ["gebo", "hagalaz", "isa", "jera"]


@pytest.mark.parametrize("spread_id", SPREAD_IDS)
def test_wyrd_clause_has_no_nested_colon(spread_id: str, fixed_rng) -> None:
    """上面那条冒号闸用默认口径抽（`include_wyrd=False`），空白符一行都走不到；
    而 API 明明把这个开关下发给了读者（`schemas/runes.py:52`、`api/v1/runes.py:32`），
    故那条分支今天无人守 —— 这里补上。

    空白句在语料释义之前自己又打了一个冒号（「……非古传统：石面上什么也没刻：……」），
    正是本任务要清除的嵌套冒号在同一条「。」句里的第二个。语料那句的冒号动不得（G2），
    所以能动的只有框架句那一个分隔符。
    """
    size = SPREADS[spread_id].size
    fixed_rng(["wyrd", *_WYRD_FILLER_KEYS[: size - 1]], orientation="upright")
    result = draw(spread_id=spread_id, include_wyrd=True)

    assert "wyrd" in result.drawn_keys
    wyrd_stone = next(stone for stone in result.stones if stone.is_wyrd)
    # 先证分支真被走到：语料释义逐字在句内，否则下面的闸是空跑。
    assert wyrd_stone.meaning in result.synthesis
    for clause in result.synthesis.split("。"):
        assert clause.count("：") <= 1, clause


@pytest.mark.parametrize("spread_id", SPREAD_IDS)
def test_synthesis_keeps_every_latin_run_parenthesised(spread_id: str) -> None:
    """英文只准待在括注里：`（Perthro` 可以，`落得Perthro` 不行。

    把成对括注整段摘掉之后，正文里不该再出现任何一枚牌的名字——牌阵名、位次名、牌名
    三种英文今天全部收在 `（…）` 内，摘完还剩下的就是裸夹。位次英文名随「括注去重」
    一起从这句里消失，但它仍随 `stones[].position_label` 下发，信息没少一条。
    """
    for _ in range(CASTS_FOR_STRUCTURE):
        result = draw(spread_id=spread_id)
        stripped = re.sub(r"（[^（）]*）", "", result.synthesis)
        for rune in DECK_25:
            assert not rune_name_pattern(rune.name).search(stripped), rune.name


def test_synthesis_marks_the_aett_theme_as_a_modern_reading() -> None:
    """报了分组主题就得同时说清那是现代解读，不据此断吉凶（决策 16）。"""
    for _ in range(CASTS_FOR_STRUCTURE):
        result = draw(spread_id="five")
        if "现代解读作" in result.synthesis:
            assert "非古文献" in result.synthesis
            assert "不据此断吉凶" in result.synthesis


def test_synthesis_contains_no_percentage() -> None:
    for spread_id in SPREAD_IDS:
        assert "%" not in draw(spread_id=spread_id).synthesis


# --- 阴影参照 --------------------------------------------------------------


def test_shadow_counsel_lists_only_reversible_runes() -> None:
    for spread_id in SPREAD_IDS:
        for _ in range(CASTS_FOR_STRUCTURE):
            result = draw(spread_id=spread_id)
            if result.shadow_counsel is None:
                continue
            drawn = {stone.key: stone for stone in result.stones}
            for note in result.shadow_counsel:
                assert note.key in drawn
                assert drawn[note.key].reversible is True
                rune = get_rune(note.key)
                assert note.shadow_meaning == rune.reversed_meaning
                assert note.shadow_keywords == list(rune.reversed_keywords)


def test_shadow_counsel_covers_every_reversible_rune_drawn() -> None:
    for _ in range(CASTS_FOR_STRUCTURE):
        result = draw(spread_id="five")
        expected = {s.key for s in result.stones if s.reversible}
        actual = set() if result.shadow_counsel is None else {n.key for n in result.shadow_counsel}
        assert actual == expected


def test_shadow_counsel_is_none_when_no_reversible_rune_was_drawn(fixed_rng) -> None:
    """三枚全对称：一块都无阴影可参照，故整字段为 `None`，前端整块不渲染（决策 23）。"""
    fixed_rng(["gebo", "hagalaz", "isa"])
    result = draw(spread_id="three")
    assert all(not stone.reversible for stone in result.stones)
    assert result.shadow_counsel is None


def test_shadow_note_carries_the_drawn_orientation_and_a_disclaimer(fixed_rng) -> None:
    """少了 `drawn_orientation`，读者会把一段反面参照误读成对本次结果的断言。"""
    fixed_rng(["fehu", "gebo", "isa"], orientation="reversed")
    result = draw(spread_id="three")
    assert result.shadow_counsel is not None and len(result.shadow_counsel) == 1
    note = result.shadow_counsel[0]
    assert note.key == "fehu"
    assert note.drawn_orientation == "reversed"
    assert note.note
    assert "不是另一次结果" in note.note


def test_shadow_note_distinguishes_upright_from_reversed_draws(fixed_rng) -> None:
    fixed_rng(["fehu", "gebo", "isa"], orientation="upright")
    upright_note = draw(spread_id="three").shadow_counsel[0]
    assert upright_note.drawn_orientation == "upright"
    assert "反面参照" in upright_note.note

    fixed_rng(["fehu", "gebo", "isa"], orientation="reversed")
    reversed_note = draw(spread_id="three").shadow_counsel[0]
    assert reversed_note.drawn_orientation == "reversed"
    assert reversed_note.note != upright_note.note


# --- 全典 ------------------------------------------------------------------


@pytest.mark.parametrize("include_wyrd", [False, True])
def test_codex_is_always_25_entries(include_wyrd: bool) -> None:
    """开关管的是抽不抽得着空白符，不是它在不在典里。"""
    codex = draw(spread_id="single", include_wyrd=include_wyrd).codex
    assert codex.total == 25
    assert len(codex.aettir) == 3
    assert sum(len(group.runes) for group in codex.aettir) == 24
    assert all(len(group.runes) == 8 for group in codex.aettir)
    assert codex.wyrd.key == "wyrd"


def test_codex_covers_every_corpus_rune_exactly_once() -> None:
    codex = draw(spread_id="single").codex
    keys = [rune.key for group in codex.aettir for rune in group.runes]
    keys.append(codex.wyrd.key)
    assert sorted(keys) == sorted(rune.key for rune in DECK_25)
    assert len(set(keys)) == 25


def test_codex_carries_the_unicode_anchor_for_the_provenance_card() -> None:
    """出处卡要印「Unicode 码位锚点」，故码位与官方名必须随响应下发（决策 25）。"""
    codex = draw(spread_id="single").codex
    fehu = next(r for group in codex.aettir for r in group.runes if r.key == "fehu")
    assert fehu.codepoint == 0x16A0
    assert fehu.unicode_name == "RUNIC LETTER FEHU FEOH FE F"
    assert codex.wyrd.codepoint is None
    assert codex.wyrd.unicode_name is None
    assert codex.wyrd.glyph == ""


def test_codex_shows_both_sides_of_a_reversible_rune() -> None:
    """抽屉是参考资料，故正逆两面都要给；对称符的逆位仍为 None，不编。"""
    codex = draw(spread_id="single").codex
    by_key = {r.key: r for group in codex.aettir for r in group.runes}
    assert by_key["fehu"].reversed_meaning and by_key["fehu"].reversed_keywords
    assert by_key["gebo"].reversed_meaning is None
    assert by_key["gebo"].reversed_keywords is None
    assert by_key["gebo"].upright_meaning


def test_codex_groups_are_ordered_and_labelled() -> None:
    groups = draw(spread_id="single").codex.aettir
    assert [group.key for group in groups] == ["freyja", "heimdall", "tyr"]
    assert all(group.theme and group.naming_note for group in groups)
    assert all("近代" in group.naming_note for group in groups)


def test_dagaz_is_in_the_codex() -> None:
    """设计稿的抽屉只有 23 枚真字母（Wyrd 占了 Dagaz 那格），这里必须在位。"""
    codex = draw(spread_id="single").codex
    dagaz = next(r for group in codex.aettir for r in group.runes if r.key == "dagaz")
    assert dagaz.order == 23
    assert dagaz.codepoint == 0x16DE


# --- 出处与「没有分数」 ----------------------------------------------------


def test_provenance_names_the_entropy_source_honestly() -> None:
    """决策 19：如实说 `secrets`，不许留设计稿那句「量子混沌伪随机熵源」。"""
    provenance = draw(spread_id="single").provenance
    assert provenance.rng == "secrets"
    assert "CSPRNG" in provenance.rng_note
    assert "量子" not in provenance.rng_note
    assert "量子" not in provenance.method
    assert provenance.engine == "content-library"
    assert "secrets" in provenance.method


def test_provenance_lists_exactly_the_two_tables() -> None:
    tables = draw(spread_id="single").provenance.tables
    assert [table.name for table in tables] == ["rune_futhark", "rune_spreads"]
    assert all(table.version and table.source for table in tables)


def test_provenance_carries_both_disclaimers() -> None:
    """ætt 命名各家不一、Wyrd 是现代增补 —— 两句都得随响应下发。"""
    provenance = draw(spread_id="single").provenance
    assert "近代" in provenance.naming_note
    assert "现代增补" in provenance.wyrd_note


def test_badge_has_no_invented_serial_number() -> None:
    """决策 18：`#RUNES-FUTHARK`，不带设计稿那个无从推导的 `-2026-N09`。"""
    badge = draw(spread_id="single").provenance.badge
    assert badge == "#RUNES-FUTHARK"
    assert not re.search(r"\d", badge)


def test_reversible_note_explains_the_geometric_criterion() -> None:
    note = draw(spread_id="single").reversible_note
    assert "180" in note
    assert "merkstave" in note


def field_names(model, prefix: str = "") -> list[str]:
    """Every field name in the response tree, dotted, for the no-score scan."""
    out: list[str] = []
    for name, value in model.__dict__.items():
        path = f"{prefix}{name}"
        out.append(path)
        if hasattr(value, "__dict__") and not isinstance(value, type):
            out.extend(field_names(value, f"{path}."))
        elif isinstance(value, list):
            for item in value:
                if hasattr(item, "__dict__"):
                    out.extend(field_names(item, f"{path}[]."))
    return out


#: 只能按整词比对的禁用名。子串比对会把 `transliteration` 判成含 `ratio` ——
#: 这一条原先正是子串比对，就红在那上面。故短词一律先拆 snake_case 再整词比。
#: 这三个常量只服务下面两条测试，故放在它们旁边而不提到文件头。
WORD_BANNED = frozenset({
    "ratio", "rate", "weight", "score", "percent", "percentage",
    "confidence", "odds", "probability", "likelihood",
})

#: 这三个可以安全走子串：在本域里它们不可能是某个更长合法单词的一部分，
#: 而子串比对还顺带抓住 `percentile`、`scoreValue` 这类整词比对会漏掉的变形。
SUBSTRING_BANNED = ("score", "percent", "confidence")


def banned_hits(names: list[str]) -> list[str]:
    """Those of ``names`` that look like a score or a percentage."""
    hits: list[str] = []
    for name in names:
        leaf = name.rsplit(".", 1)[-1].split("[")[-1].lower()
        if set(re.split(r"[^a-z0-9]+", leaf)) & WORD_BANNED:
            hits.append(name)
        elif any(word in leaf for word in SUBSTRING_BANNED):
            hits.append(name)
    return hits


def test_response_has_no_score_or_percentage_field() -> None:
    """决策 6/7：整棵响应树里不许有评分或百分比字段。

    走查字段名而不是查某个具体路径：新加一个 `score` 无论挂在哪一层都会被这条抓到。
    """
    names = field_names(draw(spread_id="five", include_wyrd=True))
    assert names, "field_names walked nothing, so a clean scan would prove nothing"
    assert banned_hits(names) == []


def test_the_banned_field_scan_actually_fires() -> None:
    """对照组：证明上面那条不是因扫描器失灵而恒真。

    抓得住该抓的，且不误伤真实字段名 —— `transliteration` 里那个 `ratio`
    正是当初子串比对误伤的例子。`percentile` 则只能靠子串那一分支抓住。
    """
    planted = ["score", "compatibility_ratio", "match_rate", "percentile", "confidence_level"]
    assert banned_hits(planted) == planted

    real = field_names(draw(spread_id="five", include_wyrd=True))
    assert "stones[].transliteration" in real
    assert banned_hits(real + ["score"]) == ["score"]


def test_no_numeric_field_is_a_float() -> None:
    """百分比总会以 float 现身。本响应里只有整数计数，没有连续量。"""
    result = draw(spread_id="five", include_wyrd=True)
    for row in result.aett_balance:
        assert isinstance(row.count, int)
    for stone in result.stones:
        assert isinstance(stone.order, int)
        assert isinstance(stone.position_index, int)
    assert isinstance(result.provenance.deck_size, int)


def test_response_is_serialisable_and_roundtrips() -> None:
    result = draw(spread_id="three", include_wyrd=True)
    payload = result.model_dump()
    assert RuneCastResponse.model_validate(payload) == result


def test_every_rune_in_the_deck_is_actually_reachable() -> None:
    """没有死数据：24 枚里每一枚都真能被抽到。

    单枚阵抽 600 次。若某一枚根本不在牌组里（比如当年设计稿把 Dagaz 挤掉了），
    它永远也不会出现。600 次下漏掉任一枚的概率约 3e-10，不会让测试间歇性红。
    """
    seen: set[str] = set()
    for _ in range(600):
        seen.update(draw(spread_id="single").drawn_keys)
    assert seen == {rune.key for rune in DECK_24}


def test_wyrd_is_reachable_only_when_enabled() -> None:
    """对称的一条：关着开关时抽同样多次，空白符一次也不得出现。"""
    seen: set[str] = set()
    for _ in range(300):
        seen.update(draw(spread_id="five", include_wyrd=False).drawn_keys)
    assert "wyrd" not in seen
