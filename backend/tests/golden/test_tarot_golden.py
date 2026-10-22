"""Golden tests for the tarot deck content and draw engine.

The deck count (78 = 22 Major + 56 Minor) and card uniqueness are content
invariants enforced here per PRD 4.4. Draw behaviour asserts uniqueness within a
spread, that reversals honour the flag, and that spread sizes match the layout.
Randomness comes from :mod:`secrets` (CSPRNG), so exact cards are not pinned;
instead the tests assert structural guarantees and, where useful, variety.
"""

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.content import CONTENT_VERSION, TAROT_CONTENT_SOURCES
from app.content.tarot_cards import SUIT_ELEMENT
from app.content.tarot_deck import DECK, MAJOR_SIZE, MINOR_SIZE, SPREADS, TAROT_SOURCE, get_card
from app.content.tarot_keywords_zh import TAROT_KEYWORDS_ZH_SOURCE
from app.content.tarot_polarity import TAROT_POLARITY_SOURCE
from app.core.errors import UnsupportedMethodError
from app.engines.tarot import _synthesize, build_verdict, draw_spread
from app.schemas.tarot import DrawnCard, TarotSpreadResponse
from tests.plain_wording import FORBIDDEN, advice_hits

SPREAD_SIZES = {
    "single": 1,
    "three_card": 3,
    "celtic_cross": 10,
    "relationship": 5,
    "career": 5,
    "decision": 5,
}


# --- Deck content invariants ------------------------------------------------


def test_deck_has_seventy_eight_unique_cards() -> None:
    assert len(DECK) == 78
    ids = [card.id for card in DECK]
    assert len(set(ids)) == 78


def test_deck_splits_into_major_and_minor() -> None:
    majors = [c for c in DECK if c.arcana == "major"]
    minors = [c for c in DECK if c.arcana == "minor"]
    assert len(majors) == MAJOR_SIZE == 22
    assert len(minors) == MINOR_SIZE == 56


def test_major_arcana_numbers_are_zero_through_twenty_one() -> None:
    numbers = sorted(c.number for c in DECK if c.arcana == "major")
    assert numbers == list(range(22))


def test_minor_arcana_cover_four_suits_of_fourteen() -> None:
    minors = [c for c in DECK if c.arcana == "minor"]
    for suit in SUIT_ELEMENT:
        suit_cards = sorted(c.number for c in minors if c.suit == suit)
        assert suit_cards == list(range(1, 15))


def test_court_cards_carry_ranks_and_numbered_cards_do_not() -> None:
    court_numbers = {11, 12, 13, 14}
    for card in DECK:
        if card.arcana == "minor" and card.number in court_numbers:
            assert card.rank in {"Page", "Knight", "Queen", "King"}
        elif card.arcana == "minor":
            assert card.rank is None


def test_major_arcana_have_no_suit_or_element() -> None:
    for card in DECK:
        if card.arcana == "major":
            assert card.suit is None
            assert card.element is None


def test_every_card_has_meanings_and_keywords_both_orientations() -> None:
    for card in DECK:
        assert card.upright_meaning.strip()
        assert card.reversed_meaning.strip()
        assert len(card.upright_keywords) >= 3
        assert len(card.reversed_keywords) >= 3


def test_get_card_round_trips_by_id() -> None:
    assert get_card("major-00").name == "The Fool"
    assert get_card("wands-14").rank == "King"
    with pytest.raises(KeyError):
        get_card("does-not-exist")


# --- Spread library ---------------------------------------------------------


def test_spread_library_matches_expected_sizes() -> None:
    assert set(SPREADS) == set(SPREAD_SIZES)
    for spread_id, size in SPREAD_SIZES.items():
        assert SPREADS[spread_id].size == size


def test_spread_positions_have_unique_keys_and_bilingual_labels() -> None:
    for spread in SPREADS.values():
        keys = [p.key for p in spread.positions]
        assert len(set(keys)) == len(keys)
        for position in spread.positions:
            assert position.label.strip()
            assert position.label_zh.strip()
            assert position.meaning.strip()


# --- Draw behaviour ---------------------------------------------------------


def test_celtic_cross_draws_ten_unique_cards_in_position_order() -> None:
    result = draw_spread(spread_id="celtic_cross")
    assert len(result.cards) == 10
    assert len(set(result.drawn_ids)) == 10
    assert [c.position_index for c in result.cards] == list(range(10))
    assert [c.position_key for c in result.cards] == [p.key for p in SPREADS["celtic_cross"].positions]


def test_reversals_disabled_yields_all_upright() -> None:
    result = draw_spread(spread_id="celtic_cross", allow_reversed=False)
    assert all(c.orientation == "upright" for c in result.cards)
    assert result.reversed_count == 0
    assert result.allow_reversed is False


def test_reversals_enabled_produce_both_orientations_over_many_draws() -> None:
    seen: set[str] = set()
    for _ in range(40):
        result = draw_spread(spread_id="celtic_cross", allow_reversed=True)
        seen.update(c.orientation for c in result.cards)
        if seen == {"upright", "reversed"}:
            break
    assert seen == {"upright", "reversed"}


def test_drawn_card_fields_agree_with_orientation() -> None:
    """牌侧六格回 `get_card()`、位次侧四格回 `SPREADS` 逐字对账：同一张牌、同一个 orientation、同一个位次。

    位次那一半是终审发现 3 补的缺口：改前只有
    `test_celtic_cross_draws_ten_unique_cards_in_position_order` 的 `position_key` 顺序钉，
    加上 `label`/`label_zh`/`meaning`/`meaning_zh` 四格无人对账——「引擎把第 3 位的中文释义
    装到第 5 位上」今天无测可红。形状照 `tests/test_runes.py:115-119`（逐位比
    `position_key` / `position_index` / `position_label_zh`）。四格等式立起来之后，
    `position_meaning_zh != position_meaning` 就被语料门的
    `test_every_spread_position_carries_a_chinese_gloss` 蕴含，留它是同一件事两份口径
    （AGENTS.md §2），删。
    """
    # 十张的阵：取向那两格只在出现逆位时才分得出（见循环里的注释），十张把可见率放大到 1023/1024。
    result = draw_spread(spread_id="celtic_cross")
    for card in result.cards:
        source = get_card(card.card_id)
        assert card.name == source.name
        assert card.arcana == source.arcana
        assert card.keywords == list(source.keywords(card.orientation))
        assert card.meaning == source.meaning(card.orientation)
        # 配对的另一半：中文侧必须由**同一个 orientation** 决定，接反了读起来完全通顺，
        # 所以只有出现逆位时这两格才分得出取向。
        # 变异复核的形状：把引擎那格的 `card.meaning_zh(orientation)` 改成 `meaning_zh("upright")`
        # 之后，只有**本张牌是逆位**时断言才会红，而本条抽十张、全正位（这一格看不见）的概率是
        # `0.5**10`（复测：`cd backend && PYTHONIOENCODING=utf-8
        # .venv/Scripts/python.exe -c "print(0.5**10)"` → `0.0009765625`）。改前用 `three_card`
        # （`0.5**3` → `0.125`，即 1/8 的轮次看不见这个变异；当时实测「跑 20 轮红 19 / 绿 1」，
        # 那组读数是历史记录，住在 ledger 的变异表里，不在本注释）。
        # 所以单轮看见绿**不等于门是空的**，要多跑几轮。
        assert card.keywords_zh == list(source.keywords_zh(card.orientation))
        assert card.meaning_zh == source.meaning_zh(card.orientation)
        # 位次侧同账：引擎那五格全读同一个 `position` 对象，所以按 `position_index` 回原表
        # 逐项重组对账，错装一位就红（这一半与朝向无关，每轮都确定性走到）。
        pos = SPREADS[result.spread_id].positions[card.position_index]
        assert card.position_label == pos.label
        assert card.position_label_zh == pos.label_zh
        assert card.position_meaning == pos.meaning
        assert card.position_meaning_zh == pos.meaning_zh


def test_synthesis_references_question_and_spread() -> None:
    """整段 synthesis 里出现的是**本次那个阵**的中英双名，别的阵名一个都不串。

    改前的写法是「`assert "Celtic Cross" not in result.synthesis`」，而那次抽的是 `single`——
    `celtic_cross` 的英文名当时**根本没可能**出现在句子里，这条断言恒真（spec §8 明令要消灭的
    那一类「看着像测过」）。中文框架句里阵名是真插值，所以现在可以钉「在位」与「不串台」两件事。
    串台那半边从 `SPREADS` 现算（除本次那个阵之外全排），英文与中文两名都排：写死五个阵名的
    话，第七个阵进来就静默漏排（复测：`cd backend && PYTHONIOENCODING=utf-8
    .venv/Scripts/python.exe -c "from app.content.tarot_deck import SPREADS;
    print(len(SPREADS), [s.name for s in SPREADS.values()])"`）。
    """
    result = draw_spread(spread_id="single", question="Should I take the offer?")
    assert result.question == "Should I take the offer?"
    assert "本次以 单张牌（Single Card）为这个问题布阵：Should I take the offer?" in result.synthesis
    for spread_id, other in SPREADS.items():
        if spread_id == "single":
            continue
        assert other.name not in result.synthesis, spread_id
        assert other.name_zh not in result.synthesis, spread_id
    assert result.synthesis.strip()


def test_major_and_reversed_counts_match_cards() -> None:
    result = draw_spread(spread_id="celtic_cross")
    assert result.major_arcana_count == sum(1 for c in result.cards if c.arcana == "major")
    assert result.reversed_count == sum(1 for c in result.cards if c.orientation == "reversed")


def test_draws_are_varied_not_deterministic() -> None:
    first = draw_spread(spread_id="celtic_cross").drawn_ids
    second = draw_spread(spread_id="celtic_cross").drawn_ids
    assert first != second


def test_unknown_spread_raises() -> None:
    with pytest.raises(UnsupportedMethodError):
        draw_spread(spread_id="not_a_spread")


def test_the_chinese_half_of_every_text_field_is_required() -> None:
    """新字段是契约不是装饰：从真实响应里删掉任一格，模型必须拒绝。

    为什么不用「少字段仍然 200」那种写法：那证明的是 pydantic 容许缺席，而本期要的正好相反
    （G12）。这里先拿真响应 `model_dump()` 再逐格删，删的是**这一次真实抽取**的字段，
    所以证明的是「这条 JSON 契约少一格就立不住」（spec §8「字段自身归 pydantic」那一支，
    AGENTS.md §4）。

    要钉的清单是**五格**：牌侧三格（`position_meaning_zh` / `keywords_zh` / `meaning_zh`）走第一个
    循环，响应侧 `spread_description_zh` / `cards` / `provenance` 走第二个。`cards` 是对照格（本来就
    必填，用来证明这个循环确实能红），所以第二循环里真正新增的是两格。G12 的原话把 `provenance`
    单列在「5 个字段」之后（`plans/…plan-d.md:28`），按计划自己的件表（`:83`：`DrawnCard` +3、
    响应 +`spread_description_zh` +`provenance`）它就是那第五格，别再往外加。
    `provenance` 补齐的是终审发现 4：改前它没有缺席证明，缺席只会被别处的
    `body["provenance"]["tables"]` KeyError 顺带打红——那是撞上的，不是钉的。
    """
    result = draw_spread(spread_id="three_card", question="required fields?")
    payload = result.model_dump()

    for field in ("position_meaning_zh", "keywords_zh", "meaning_zh"):
        broken_card = {k: v for k, v in payload["cards"][0].items() if k != field}
        with pytest.raises(ValidationError) as excinfo:
            DrawnCard.model_validate(broken_card)
        assert field in str(excinfo.value)

    for field in ("spread_description_zh", "cards", "provenance"):
        broken_response = {k: v for k, v in payload.items() if k != field}
        with pytest.raises(ValidationError) as excinfo:
            TarotSpreadResponse.model_validate(broken_response)
        assert field in str(excinfo.value)


# --- HTTP adapter -----------------------------------------------------------


def test_tarot_spread_endpoint(client: TestClient) -> None:
    response = client.post(
        "/api/v1/tarot/spread",
        json={"spread_id": "three_card", "allow_reversed": True, "question": "test"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["spread_id"] == "three_card"
    assert len(body["cards"]) == 3
    assert len(set(body["drawn_ids"])) == 3
    assert body["rng"] == "secrets"
    assert body["engine"] == "content-library"


def test_tarot_endpoint_returns_both_halves_of_every_text_field(client: TestClient) -> None:
    """端点侧的配对凭据：四对字段两两成对（牌阵描述 1 对 + 每张牌 3 对），且中文侧非空、与英文侧不同串。

    内容层的不重复/长度/措辞门在 `tests/content/test_tarot_zh_corpus.py`，这里只钉
    「装配发生了、方向没接反、契约字段一个都没少」——同一件事两处断言就两份口径（AGENTS.md §2
    的那条精神在 backend 内部同样适用）。
    """
    body = client.post(
        "/api/v1/tarot/spread",
        json={"spread_id": "celtic_cross", "allow_reversed": True, "question": "both halves"},
    ).json()
    assert body["spread_description_zh"] and body["spread_description_zh"] != body["spread_description"]
    assert len(body["cards"]) == 10
    for card in body["cards"]:
        assert card["meaning_zh"] and card["meaning_zh"] != card["meaning"]
        assert card["position_meaning_zh"] and card["position_meaning_zh"] != card["position_meaning"]
        assert len(card["keywords_zh"]) == len(card["keywords"]) > 0
        assert card["keywords_zh"] != card["keywords"]


def test_tarot_spread_endpoint_rejects_unknown_spread(client: TestClient) -> None:
    response = client.post("/api/v1/tarot/spread", json={"spread_id": "nope"})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "unsupported_method"


def test_provenance_lists_exactly_the_five_tables_read() -> None:
    """五行三串（G14）：三张牌表共用 `TAROT_SOURCE`，译表与极性表各单独一串。

    `tarot_cards.py` **不在清单里**：它带的是 dataclass、两个工厂与几张查表字典（`element`、
    `rank` 那两格的取值确实进了响应），但没有一行是印进页面的句子——完整理由与「读了文案 ≠
    import 过字典」这条界线见 `content/__init__.py` 的 `TAROT_CONTENT_SOURCES` 注（G13）。
    行序就是页面上的展示序（`components/ui/ProvenancePanel.tsx` 按数组渲染），所以这里钉
    **等序列表**而不是集合——集合会把「把译表挪到第一行」放过去，而那一改动在页面上看得见。
    下面那条 `len(TAROT_CONTENT_SOURCES) == 5` 不是门，是 belt-and-braces：`_tables()` 迭代的
    就是那个元组，清单任何增删都会先红在上面那条等序列表——把它单独当成一条门就是「看着像
    测过」（spec §8 明令消灭的那一类）。
    """
    result = draw_spread(spread_id="single")
    tables = result.provenance.tables
    assert [(t.name, t.source) for t in tables] == [
        ("tarot_major", TAROT_SOURCE),
        ("tarot_minor", TAROT_SOURCE),
        ("tarot_deck", TAROT_SOURCE),
        ("tarot_keywords_zh", TAROT_KEYWORDS_ZH_SOURCE),
        ("tarot_polarity", TAROT_POLARITY_SOURCE),
    ]
    assert len(TAROT_CONTENT_SOURCES) == 5
    assert [t.version for t in tables] == [CONTENT_VERSION] * 5
    # 三张牌表共用一串是刻意的（凭据同一条：RWS 通行牌义 + Waite 布局），抄成三份必漂。
    assert tables[0].source == tables[1].source == tables[2].source
    # 译表与极性表各自单独署名：一张自持现代译表、一张自持吉凶归类（模型参数），都不冒充原典。
    assert tables[3].source != tables[0].source
    assert tables[4].source != tables[0].source
    assert tables[4].source != tables[3].source


def test_provenance_engine_and_note_and_the_two_pinned_labels(client: TestClient) -> None:
    """出处块不改动那两个已被逐字钉住的标签：`rng == "secrets"`、`engine == "content-library"`。

    本期把正文翻成中文，**没有**换引擎、没有换随机源，所以 `test_tarot_spread_endpoint` 里
    那两条逐字钉（`body["rng"] == "secrets"`、`body["engine"] == "content-library"`）必须原样
    绿；`provenance.engine` 那一格说的是拼句方法，与响应顶层那个恒定的库标签是两个字段，不共用
    （先例：`engines/lenormand.py` 里 `engine="lenormand-combination"` 那一格与它的响应标签）。

    末尾那三条走 `client` 而不是走 `draw_spread`：上面一条测钉的是**引擎对象**上的四行两串，
    这里钉的是同一份清单**穿过 snake_case JSON 之后**还在原位（`provenance` 整块被 pydantic
    漏掉、`tables` 在序列化时变成 dict 而前端类型照列表读，都只在走线这一侧才红）。两边断言
    的对象不同，不是同一件事的两份口径（AGENTS.md §2 的分工精神）。
    """
    result = draw_spread(spread_id="three_card")
    assert result.provenance.engine == "tarot-content-library"
    assert result.provenance.content_version == CONTENT_VERSION
    assert result.provenance.source == TAROT_SOURCE
    # 非空由这一条管：`note` 必须真说出随机源（页面上它就是一行小字，空串照样「有出处块」）。
    # 曾另有一句 `assert note.strip()`——被本条严格蕴含（含 "secrets" 必非空），留就是没登记的
    # belt-and-braces，删。
    assert "secrets" in result.provenance.note
    # 出处诚实性的第二格（G13 同类，先例是 `engines/qimen.py` 的 `SCHOOL_NOTE` 被
    # `tests/content/test_qimen_plain_corpus.py` 逐句钉）：综合解读的**框架句式**住在本模块，
    # 不在牌库里，所以 `note` 不许说成「一律取自牌库」——那正是本任务改前那句的写法。
    # 变异复测：把 `NOTE` 第二句换回「…与综合解读一律取自策展 78 张牌库…」，本条红。
    assert "固定句式" in result.provenance.note
    assert "一律取自" not in result.provenance.note

    body = client.post("/api/v1/tarot/spread", json={"spread_id": "single"}).json()
    assert body["rng"] == "secrets"
    assert body["engine"] == "content-library"
    assert [t["name"] for t in body["provenance"]["tables"]] == [
        "tarot_major",
        "tarot_minor",
        "tarot_deck",
        "tarot_keywords_zh",
        "tarot_polarity",
    ]


# --- Synthesis frames -------------------------------------------------------


def _card_into(card_id: str, position, index: int, orientation: str) -> DrawnCard:
    """从真表装一张真牌到真位次上，只为把 `_synthesize` 的计数分支钉到可复现。"""
    source = get_card(card_id)
    return DrawnCard(
        position_index=index,
        position_key=position.key,
        position_label=position.label,
        position_label_zh=position.label_zh,
        position_meaning=position.meaning,
        position_meaning_zh=position.meaning_zh,
        card_id=source.id,
        name=source.name,
        name_zh=source.name_zh,
        arcana=source.arcana,
        number=source.number,
        suit=source.suit,
        rank=source.rank,
        element=source.element,
        orientation=orientation,
        keywords=list(source.keywords(orientation)),
        keywords_zh=list(source.keywords_zh(orientation)),
        meaning=source.meaning(orientation),
        meaning_zh=source.meaning_zh(orientation),
    )


def _wording_clean(label: str, text: str) -> str:
    """G15 的第四、五类对象共用的一条措辞门：禁串与建议词一次判完。

    住在测文件里而不进 `plain_wording`：`FORBIDDEN` 与 `advice_hits` 的词表口径仍由那份唯一
    正主供给（G8），这里只是把两判合起来用。为什么框架句本身也要扫（不只扫装配结果）：一次
    抽牌只会命中八个分支里的**三个**（lead + 一个计数句 + 一个取向句），靠真抽取扫一遍撞不齐
    ——`major_many` 要十张里过半是大牌，实测 300 次 `celtic_cross` 抽取只撞出 23~40 次（复测：
    `cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "from app.engines.tarot import draw_spread; print(sum(1 for _ in range(300) if '张牌里有' in draw_spread(spread_id='celtic_cross', allow_reversed=True).synthesis))"`；
    抽牌走 CSPRNG（G4），所以这里给的是**同量级区间**而不是一个钉死的数——留一个单次测量值
    在这里，下次跑出来不同就成了一条注释说谎）。而逐字钉的那三串本身就是八句的全部形状 ——
    拿它们过门才是**确定性**覆盖。
    """
    for banned in FORBIDDEN:
        assert banned not in text, f"{label} 带禁串 {banned!r}"
    hits = advice_hits(text)
    assert hits == [], f"{label} 命中建议词 {hits}"
    return text


def test_synthesis_frames_are_pinned_verbatim_question_major_many_all_upright() -> None:
    """框架钉 ①：`lead_question` + `per_card`（正位）×3 + `major_many` + `all_upright`。

    六句合成**一整串**逐字对账，句与句之间那个空格就是引擎的 `join`，所以「句子本身对但
    拼接变了形状」也红。为什么不用「`overview(引擎的 frame, parts) == result.synthesis`」
    那种写法：见 `test_kabbalah_golden.py` 的
    `test_gematria_synthesis_text_is_pinned_before_the_overview_migration` 那段理由
    （拿唯一正主自己拼再跟自己比是恒等式，什么也没钉）。

    两个计数刻意取**不一样**的数（3 张里 2 张大牌）：`major_many` 那句插了 `{total}` 与
    `{major_count}` 两个槽，若这里传 1/1，把两个槽对调照样逐字相等，这一句就白钉了
    （T5 评审实测：1/1 形状下该变异 26 条全绿）。`question` 两侧的空格同样是刻意的 ——
    引擎那句走的是 `question.strip()`，钉得住才不算漏。

    `_lead_keywords_zh` 的 `limit=3` 截断在这里是**被量到**的：三张牌的中文关键词各有 4~5 条
    （`major-00` 正位 5 条、`wands-03` 与 `cups-06` 各 4 条；复测：`cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "from app.content.tarot_deck import get_card; print([len(get_card(c).keywords_zh('upright')) for c in ('major-00','wands-03','cups-06')])"` → `[5, 4, 4]`），
    钉串里却只出现前三条，框架钉 ② 的 `pentacles-05` 逆位同理（4 条取 3）——所以「取的是 …」
    那格的长度语义不是没测过。
    """
    spread = SPREADS["three_card"]
    cards = [
        _card_into("major-00", spread.positions[0], 0, "upright"),
        _card_into("wands-03", spread.positions[1], 1, "upright"),
        _card_into("cups-06", spread.positions[2], 2, "upright"),
    ]
    text = _wording_clean(
        "框架钉 ①",
        _synthesize(spread, cards, "  Should I take the offer?  ", 2, 0, True),
    )
    assert text == " ".join(
        [
            "本次以 时间之流三张（Three Card）为这个问题布阵：Should I take the offer?",
            "过去（Past）抽出 愚人（The Fool），正位，取的是 开端、纯真、随性。",
            "现在（Present）抽出 权杖三（Three of Wands），正位，取的是 准备、先见、事业开创。",
            "未来（Future）抽出 圣杯六（Six of Cups），正位，取的是 重访旧日、童年记忆、纯真。",
            "3 张牌里有 2 张大牌，那些超出你当下掌控的人生主题与力量正明显起作用。",
            "所有牌都落正位，这些能量表达得清楚，没有被挡。",
        ]
    )


def test_synthesis_frames_are_pinned_verbatim_plain_minor_reversed_no_major() -> None:
    """框架钉 ②：`lead_plain` + `per_card`（逆位）+ `no_major` + `some_reversed`。"""
    spread = SPREADS["three_card"]
    cards = [_card_into("pentacles-05", spread.positions[0], 0, "reversed")]
    text = _wording_clean("框架钉 ②", _synthesize(spread, cards, None, 0, 1, True))
    assert text == " ".join(
        [
            "本次以 时间之流三张（Three Card）布阵。",
            "过去（Past）抽出 星币五（Five of Pentacles），逆位，取的是 从损失里回血、灵性上的贫瘠、重新燃起的希望。",
            "一张大牌也没有出现，所以这次讲的是日常的、你能直接上手的现实力量，而不是更大的人生主题。",
            "1 张逆位，指向被阻滞、被内收或被延迟的能量，它们要的是被看清，不是被硬推。",
        ]
    )


def test_synthesis_frames_are_pinned_verbatim_major_some_and_the_reversal_skip() -> None:
    """框架钉 ③：`major_some`，以及 `allow_reversed=False` 时**不出现**取向那一句。

    三张牌里 1 张大牌（`1 * 2 >= 3` 为假）走 `major_some`；`allow_reversed=False` 走的是
    引擎里 `if allow_reversed:` 那个分支的假侧——今天没有任何一条测钉过「不该出现的句子
    确实没出现」，而 `total`/`major` 两个插值都来自调用参数，`major_arcana_count` 那格由
    `test_major_and_reversed_counts_match_cards` 另行对账，所以这里写死数字不是自证。
    """
    spread = SPREADS["three_card"]
    cards = [
        _card_into("major-00", spread.positions[0], 0, "upright"),
        _card_into("wands-03", spread.positions[1], 1, "upright"),
        _card_into("cups-06", spread.positions[2], 2, "upright"),
    ]
    assert _wording_clean("框架钉 ③", _synthesize(spread, cards, None, 1, 0, False)) == " ".join(
        [
            "本次以 时间之流三张（Three Card）布阵。",
            "过去（Past）抽出 愚人（The Fool），正位，取的是 开端、纯真、随性。",
            "现在（Present）抽出 权杖三（Three of Wands），正位，取的是 准备、先见、事业开创。",
            "未来（Future）抽出 圣杯六（Six of Cups），正位，取的是 重访旧日、童年记忆、纯真。",
            "1 张大牌在这份日常处境里标出分量更重、由不得你选的线索。",
        ]
    )


def test_an_assembled_synthesis_passes_the_wording_gates() -> None:
    """六个阵各抽一次（正逆位两种开关），装配后的整段 `synthesis` 过禁串与建议词门。

    `assert "布阵" in text` 那一句是**必要**的，不是装饰：没有它，这条测在改前的英文模板上
    照样全绿（英文里既没有「；」也没有六个建议字），那条门就成了一条恒真断言——spec §8
    警告的正是这种「看着像测过」。
    """
    for spread_id in SPREADS:
        for allow_reversed in (True, False):
            label = f"{spread_id}/reversed={allow_reversed}"
            text = draw_spread(spread_id=spread_id, allow_reversed=allow_reversed).synthesis
            assert "布阵" in text, label
            _wording_clean(f"装配 {label}", text)


# --- 综合结论卡片（verdict）：纯计数快照钉五档，真实发牌只钉结构自洽 ---------------------

#: (积极, 消极, 中性, 大牌, 逆位) → (档位, 星级)。发牌是 CSPRNG 不可控，故档位分布由纯函数
#: `build_verdict` 的构造计数钉住（无 mock：计数是引擎同一公式的输入，不桩响应）。五档各落一例。
VERDICT_SNAPSHOTS: tuple[tuple[int, int, int, int, int, str, int], ...] = (
    (4, 0, 0, 2, 0, "大吉", 5),
    (2, 0, 1, 1, 0, "吉", 4),
    (1, 1, 1, 1, 1, "平", 3),
    (1, 2, 0, 0, 1, "小凶", 2),
    (0, 4, 0, 1, 2, "凶", 1),
)


@pytest.mark.parametrize(
    "positive, negative, neutral, major, reversed_count, grade, stars", VERDICT_SNAPSHOTS
)
def test_verdict_snapshot_is_pinned(
    positive: int,
    negative: int,
    neutral: int,
    major: int,
    reversed_count: int,
    grade: str,
    stars: int,
) -> None:
    """五个计数组合的结论卡片逐字段钉死（确定性快照，不经过随机发牌）。"""
    verdict = build_verdict(positive, negative, neutral, major, reversed_count)
    assert verdict.grade == grade
    assert verdict.stars == stars
    assert verdict.headline.startswith(f"你这一阵抽出的牌属{grade}：")
    assert verdict.points == [
        f"积极牌 {positive} 张",
        f"消极牌 {negative} 张",
        f"中性牌 {neutral} 张",
        f"大牌 {major} 张",
        f"逆位 {reversed_count} 张",
    ]
    assert verdict.advice.endswith("。")
