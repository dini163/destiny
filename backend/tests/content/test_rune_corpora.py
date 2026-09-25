"""卢恩两张语料表的不变式（卢恩 spec §9.1）。

这里锁的不是"释义写得好不好"，而是四件一旦漂移就**静默**出错的事：

1. **字形**。设计稿在这一页印错了四个字符（ᚫ AESC / ᛋ SIGEL / ᛝ ING / ᛭ 标点），
   还整个漏了 Dagaz。肉眼看不出前三个与正解的差别，故字形不靠人判：
   `unicodedata` 随解释器分发，是一份离线、权威、可被单测直接调用的源。
2. **逆位**。八枚旋转对称的符文没有逆位读法。若有人给它们补上一句逆位释义来"填满表格"，
   页面就会印出一个与字形矛盾的徽标 —— 读者拿到一句无从核对的话。
3. **空白符的血统**。Wyrd 是 1980 年代的商业增补。它的出处一旦与那 24 枚共用
   「序位据 Kylver 石碑、字形据 Unicode 标准字符名」，就是一枚现代增补在借古石碑的凭据。
4. **角标可分辨**。前端 `SourceNote` 对非书引出处只印第一个「（」之前的半句，
   故条目名必须拼在限定语**之前**，且 25 枚互不撞车（数字命理走查查出的缺陷）。

第 1 条为什么还要另钉一份码位清单：`unicodedata.name(chr(cp)) == r.unicode_name` 只锁得住
「码位与官方名不自洽」，锁不住「两个字段一起改成另一枚错符文」—— 后者会让神谕通过，
而库里悄悄少了一枚真字母。故 `ELDER_FUTHARK_CODEPOINTS` 在此**独立抄一份**，
语料与测试各持一端，任一边单独改动都会红。
"""

import unicodedata

import pytest

from app.content import RUNE_CONTENT_SOURCES
from app.content.rune_futhark import (
    AETT_FREYJA,
    AETT_HEIMDALL,
    AETT_NAMES,
    AETT_NAMES_ZH,
    AETT_NAMING_NOTE,
    AETT_THEMES_ZH,
    AETT_TYR,
    DECK_24,
    DECK_25,
    FUTHARK,
    MANUSCRIPT_NOTE,
    REVERSIBLE_NOTE,
    RUNES_SOURCE,
    RUNES_SOURCE_NAME,
    RUNES_SOURCE_QUALIFIER,
    WYRD,
    WYRD_NOTE,
    WYRD_SOURCE,
    WYRD_SOURCE_NAME,
    WYRD_SOURCE_QUALIFIER,
    get_rune,
    runes_source,
)
from app.content.rune_spreads import (
    DEFAULT_SPREAD_ID,
    SPREADS,
    SPREAD_IDS,
    SPREADS_SOURCE,
    SPREADS_SOURCE_NAME,
    SPREADS_SOURCE_QUALIFIER,
    Spread,
    get_spread,
    spreads_source,
)

#: 24 枚 Elder Futhark 的码位，按 Kylver 序，**独立于语料模块抄写在此**（见模块 docstring）。
ELDER_FUTHARK_CODEPOINTS: tuple[int, ...] = (
    0x16A0, 0x16A2, 0x16A6, 0x16A8, 0x16B1, 0x16B2, 0x16B7, 0x16B9,
    0x16BA, 0x16BE, 0x16C1, 0x16C3, 0x16C7, 0x16C8, 0x16C9, 0x16CA,
    0x16CF, 0x16D2, 0x16D6, 0x16D7, 0x16DA, 0x16DC, 0x16DE, 0x16DF,
)

#: 设计稿印错的那四个码位（spec §2.3）。前三个是形近字，第四个是标点，都不是 Elder Futhark。
MOCKUP_LOOKALIKE_CODEPOINTS = frozenset({0x16AB, 0x16CB, 0x16DD, 0x16ED})

#: 旋转 180° 后与自身重合、故无逆位的八枚（spec §2.5）。
SYMMETRIC_KEYS = frozenset({
    "gebo", "hagalaz", "isa", "jera", "eihwaz", "sowilo", "ingwaz", "dagaz",
})

#: 语料里一律不许出现的词：设计稿拿它们编过五行表、司职神名、赋能度百分比与春分时机窗。
FORBIDDEN_TOKENS: tuple[str, ...] = ("%", "要素", "司职", "赋能度", "时机窗口", "五行", "元素")

#: 每条 `source` 都必须自认是摘要而非引文，用这些词之一交代。
NOT_VERBATIM_MARKERS: tuple[str, ...] = ("非逐字引文", "非古籍")

#: 打了「词源不确定」标记的条目，正文里必须有一句读者看得见的交代。
UNCERTAINTY_ADMISSIONS: tuple[str, ...] = ("不详", "一说", "构拟", "无定论", "不确定")


def corpus_strings() -> list[tuple[str, str]]:
    """语料里所有会下发到前端的字符串，带一个可定位的标签。

    只收**数据**（dataclass 字段与模块级 note 常量），不收 docstring：docstring 里
    为了说明"我们不用五行"而提到「五行」是正当的，把它扫进来等于禁止解释自己。
    """
    out: list[tuple[str, str]] = []
    for rune in DECK_25:
        for field in rune.__dataclass_fields__:
            value = getattr(rune, field)
            if isinstance(value, str):
                out.append((f"{rune.key}.{field}", value))
            elif isinstance(value, tuple):
                out.extend(
                    (f"{rune.key}.{field}[{i}]", item)
                    for i, item in enumerate(value)
                    if isinstance(item, str)
                )
    for name in ("REVERSIBLE_NOTE", "WYRD_NOTE", "AETT_NAMING_NOTE", "MANUSCRIPT_NOTE"):
        out.append((name, globals()[name]))
    for label, mapping in (
        ("AETT_NAMES", AETT_NAMES),
        ("AETT_NAMES_ZH", AETT_NAMES_ZH),
        ("AETT_THEMES_ZH", AETT_THEMES_ZH),
    ):
        out.extend((f"{label}[{k}]", v) for k, v in mapping.items())
    out.extend((n, v) for n, v in (
        ("RUNES_SOURCE", RUNES_SOURCE),
        ("RUNES_SOURCE_NAME", RUNES_SOURCE_NAME),
        ("RUNES_SOURCE_QUALIFIER", RUNES_SOURCE_QUALIFIER),
        ("WYRD_SOURCE", WYRD_SOURCE),
        ("WYRD_SOURCE_NAME", WYRD_SOURCE_NAME),
        ("WYRD_SOURCE_QUALIFIER", WYRD_SOURCE_QUALIFIER),
        ("SPREADS_SOURCE", SPREADS_SOURCE),
        ("SPREADS_SOURCE_NAME", SPREADS_SOURCE_NAME),
        ("SPREADS_SOURCE_QUALIFIER", SPREADS_SOURCE_QUALIFIER),
    ))
    for spread in SPREADS.values():
        for field in ("id", "name", "name_zh", "description", "source"):
            out.append((f"spread.{spread.id}.{field}", getattr(spread, field)))
        for position in spread.positions:
            for field in ("key", "label", "label_zh", "meaning"):
                out.append((f"pos.{spread.id}.{position.key}.{field}", getattr(position, field)))
    return out


# --- 1. 字形神谕 -----------------------------------------------------------


@pytest.mark.parametrize("rune", FUTHARK, ids=lambda r: r.key)
def test_glyph_matches_its_own_codepoint(rune) -> None:
    """`glyph` 必须就是 `chr(codepoint)` —— 存两份而不同时，以码位为准。"""
    assert rune.codepoint is not None
    assert rune.glyph == chr(rune.codepoint)


@pytest.mark.parametrize("rune", FUTHARK, ids=lambda r: r.key)
def test_unicode_name_is_the_real_official_name(rune) -> None:
    """本轮最强的一条：拿解释器自带的 `unicodedata` 逐枚核官方字符名。

    谁把 ᚨ 换成 ᚫ（AESC）、ᛊ 换成 ᛋ（SIGEL LONG-BRANCH-SOL）、ᛜ 换成 ᛝ（ING），
    这条当场红 —— 设计稿那三个形近字被永久挡在门外。
    """
    assert rune.codepoint is not None and rune.unicode_name is not None
    assert unicodedata.name(chr(rune.codepoint)) == rune.unicode_name


def test_codepoints_are_exactly_the_elder_futhark() -> None:
    """逐字等于独立抄写的那份清单。防的是「码位与官方名一起改成另一枚错符文」。"""
    assert tuple(r.codepoint for r in FUTHARK) == ELDER_FUTHARK_CODEPOINTS


def test_our_own_list_excludes_the_four_lookalikes() -> None:
    """对上面那份清单的自查：万一抄清单时手滑收进了设计稿的错字，这条会红。"""
    assert set(ELDER_FUTHARK_CODEPOINTS).isdisjoint(MOCKUP_LOOKALIKE_CODEPOINTS)


def test_codepoints_are_distinct_and_strictly_ascending() -> None:
    """24 个码位互异，且按 `order` 严格递增（Kylver 序与 Unicode 码位序恰好同向）。"""
    codepoints = [r.codepoint for r in FUTHARK]
    assert len(set(codepoints)) == 24
    assert codepoints == sorted(codepoints)


def test_every_codepoint_lives_in_the_runic_block() -> None:
    """全在 U+16A0–U+16FF 卢恩区内 —— 区外的字符连 `unicodedata` 都不会给它一个卢恩名。"""
    assert all(0x16A0 <= r.codepoint <= 0x16FF for r in FUTHARK)


def test_first_six_transliterations_spell_futhark() -> None:
    """前六枚连读逐字是 `fuþark` —— futhark 这个名词本身的来历，也是序位的最强外部锚。

    注意**不是** `"futhark"` 的前六个字母：那七个字母的前六个是 `f u t h a r`，对不上。
    """
    assert "".join(r.transliteration for r in FUTHARK[:6]) == "fuþark"


# --- 2. 规模与键域 ---------------------------------------------------------


def test_deck_sizes() -> None:
    """24 枚古符文；开空白符为 25 枚（roadmap 与 PRD §4.4 都点了这两个数）。"""
    assert len(FUTHARK) == 24
    assert len(DECK_24) == 24
    assert len(DECK_25) == 25


def test_orders_run_one_to_twentyfour_without_gaps() -> None:
    assert [r.order for r in FUTHARK] == list(range(1, 25))


def test_keys_are_unique_and_lowercased_names() -> None:
    keys = [r.key for r in FUTHARK]
    assert len(set(keys)) == 24
    assert all(r.key == r.name.lower() for r in FUTHARK)


def test_dagaz_is_present_at_order_23() -> None:
    """单独立一条：设计稿把本该属于 Dagaz 的那格给了 Wyrd，故它整个不见了。"""
    assert "dagaz" in {r.key for r in FUTHARK}
    dagaz = get_rune("dagaz")
    assert dagaz.order == 23
    assert dagaz.glyph == "\u16DE"
    assert dagaz.codepoint == 0x16DE


def test_deck_25_is_exactly_futhark_plus_wyrd() -> None:
    assert DECK_25 == (*FUTHARK, WYRD)
    assert WYRD not in FUTHARK


def test_get_rune_roundtrips_and_raises_on_unknown() -> None:
    for rune in DECK_25:
        assert get_rune(rune.key) is rune
    with pytest.raises(KeyError):
        get_rune("aesc")


# --- 3. 逆位 ---------------------------------------------------------------


def test_symmetric_set_is_exactly_the_eight() -> None:
    """不可逆的正好是这八枚，不多不少。多了是漏了逆位读法，少了是编了一句凑数。"""
    assert {r.key for r in FUTHARK if not r.reversible} == set(SYMMETRIC_KEYS)
    assert sum(1 for r in FUTHARK if r.reversible) == 16


def test_eihwaz_and_ehwaz_are_not_confused() -> None:
    """两个名字差一个字母、几何性质相反，最容易被填反 —— 故点名钉住。"""
    assert get_rune("eihwaz").glyph == "\u16C7" and not get_rune("eihwaz").reversible
    assert get_rune("ehwaz").glyph == "\u16D6" and get_rune("ehwaz").reversible


def test_irreversible_runes_carry_no_reversed_content() -> None:
    for rune in FUTHARK:
        if not rune.reversible:
            assert rune.reversed_meaning is None, rune.name
            assert rune.reversed_keywords is None, rune.name


def test_reversible_runes_carry_both_reversed_fields() -> None:
    for rune in FUTHARK:
        if rune.reversible:
            assert rune.reversed_meaning, rune.name
            assert rune.reversed_keywords, rune.name


@pytest.mark.parametrize("key", sorted(SYMMETRIC_KEYS))
def test_asking_a_symmetric_rune_for_reversed_raises(key: str) -> None:
    """访问器**抛而不是静默回退到正位**：回退会把引擎的定向 bug 藏起来。"""
    rune = get_rune(key)
    with pytest.raises(ValueError):
        rune.meaning_for("reversed")
    with pytest.raises(ValueError):
        rune.keywords_for("reversed")


@pytest.mark.parametrize("key", sorted(SYMMETRIC_KEYS))
def test_symmetric_rune_still_reads_upright(key: str) -> None:
    rune = get_rune(key)
    assert rune.meaning_for("upright") == rune.upright_meaning
    assert rune.keywords_for("upright") == rune.upright_keywords


def test_reversible_note_names_all_eight() -> None:
    """这句要印到页面上让读者自己转字形核对，故它必须与数据同步。"""
    for rune in FUTHARK:
        if not rune.reversible:
            assert rune.name in REVERSIBLE_NOTE, rune.name
    assert "180" in REVERSIBLE_NOTE


# --- 4. 词源诚实性 ---------------------------------------------------------


def test_perthro_etymology_is_flagged_uncertain() -> None:
    """Perthro 的词源学界无定论，如实记「词源不详」并打上不确定标记（决策 9）。"""
    perthro = get_rune("perthro")
    assert perthro.name_meaning_uncertain is True
    assert "词源不详" in perthro.name_meaning


def test_every_name_meaning_is_non_empty() -> None:
    assert all(r.name_meaning for r in DECK_25)


def test_uncertainty_flag_implies_the_text_admits_it() -> None:
    """打了标记却不写「不详/不确定」一类的话，等于标了个读者看不见的免责声明。"""
    for rune in DECK_25:
        if rune.name_meaning_uncertain:
            assert any(w in rune.name_meaning for w in UNCERTAINTY_ADMISSIONS), rune.name


# --- 5. 三组（ættir） ------------------------------------------------------


@pytest.mark.parametrize("aett", [AETT_FREYJA, AETT_HEIMDALL, AETT_TYR])
def test_each_aett_holds_exactly_eight_contiguous_runes(aett: str) -> None:
    members = [r for r in FUTHARK if r.aett == aett]
    assert len(members) == 8
    assert [r.order for r in members] == list(range(members[0].order, members[0].order + 8))


def test_aettir_partition_the_whole_futhark() -> None:
    assert len({r.aett for r in FUTHARK}) == 3
    assert sum(1 for r in FUTHARK if r.aett in AETT_NAMES) == 24


def test_aett_labels_are_consistent_with_the_maps() -> None:
    for rune in FUTHARK:
        assert rune.aett_zh == AETT_NAMES_ZH[rune.aett]
        assert rune.aett in AETT_THEMES_ZH


def test_aett_naming_note_admits_the_term_is_modern() -> None:
    """分组有实物依据，但「ætt」这个称呼与三组的名字都是近代且各家不一（决策 5）。"""
    assert "近代" in AETT_NAMING_NOTE
    assert "各家不一" in AETT_NAMING_NOTE


# --- 6. 空白符 Wyrd --------------------------------------------------------


def test_wyrd_fields() -> None:
    assert WYRD.order == 25
    assert WYRD.key == "wyrd"
    assert WYRD.glyph == ""
    assert WYRD.codepoint is None
    assert WYRD.unicode_name is None
    assert WYRD.transliteration == ""
    assert WYRD.aett is None
    assert WYRD.aett_zh is None
    assert WYRD.reversible is False
    assert WYRD.reversed_meaning is None
    assert WYRD.reversed_keywords is None
    assert WYRD.is_wyrd is True
    assert WYRD.upright_meaning


def test_no_real_rune_claims_to_be_wyrd() -> None:
    assert all(not r.is_wyrd for r in FUTHARK)
    assert sum(1 for r in DECK_25 if r.is_wyrd) == 1


def test_wyrd_glyph_is_not_the_runic_cross_punctuation() -> None:
    """设计稿拿 U+16ED 当空白符，而那码位的官方名是 RUNIC CROSS PUNCTUATION —— 是标点。"""
    assert WYRD.glyph != "\u16ED"
    assert unicodedata.name("\u16ED") == "RUNIC CROSS PUNCTUATION"


def test_wyrd_names_no_hierarchy_among_the_norns() -> None:
    """回归锁：《女先知之歌》只列三位女神之名，不曾给她们排名。

    本语料曾写过「诺伦三女神之首」—— 把「名字排在第一」读成了「位阶居首」，
    是凭空的补说。列出名字是可以的，替古文献定尊卑不行。
    """
    for label, text in corpus_strings():
        assert "之首" not in text, label


def test_wyrd_provenance_says_it_is_modern() -> None:
    assert "现代" in WYRD.source
    assert "现代" in WYRD_NOTE
    assert "1980" in WYRD_NOTE


def test_wyrd_does_not_borrow_the_kylver_or_unicode_credentials() -> None:
    """Wyrd 的出处必须**否认**那两条凭据，而不是沉默地继承它们（本轮新修的一处）。

    共用 `runes_source()` 会让一枚 1980 年代的商业增补印着「序位据 Kylver 石碑、
    字形据 Unicode 标准字符名」—— 而石碑上没有第 25 格，空白符也没有字形可查。
    """
    assert "不见于" in WYRD_SOURCE_QUALIFIER
    assert "不据 Unicode" in WYRD_SOURCE_QUALIFIER
    assert WYRD_SOURCE == f"{WYRD_SOURCE_NAME}（{WYRD_SOURCE_QUALIFIER}）"
    assert "Elder Futhark" not in WYRD_SOURCE_NAME


def test_book_level_source_carves_wyrd_out() -> None:
    """书级出处也得说清第 25 枚不在这两条凭据之列，否则 `provenance.tables` 一样误导。"""
    assert "Wyrd" in RUNES_SOURCE_QUALIFIER
    assert "现代增补" in RUNES_SOURCE_QUALIFIER


# --- 7. 不许编数据 ---------------------------------------------------------


def test_corpus_contains_no_percentages_or_fabricated_tables() -> None:
    """语料里搜不到百分号，也搜不到五行/要素/司职/赋能度/时机窗口（决策 6/7/8/10）。

    设计稿这一页有五个凭空而来的百分比、三套互相矛盾的五行归属、三位司职神名
    与一个春分时机窗。卢恩铸石不吃时间与地点，那些数没有任何东西可以算出来。
    """
    for label, text in corpus_strings():
        for token in FORBIDDEN_TOKENS:
            assert token not in text, f"{label} 含 {token!r}"


def test_manuscript_note_keeps_the_real_sources_and_drops_the_fake_claims() -> None:
    """spec §11 偏差 L：两个真实出处名保留，不存在的校准声明与假哈希删掉。

    设计稿那行页脚里「CODEX REGIUS」与「KYLVER STONE」是引对了的，而
    「EPIGRAPHICAL CALIBRATION VERIFIED」是不存在的校准流程、`HASH: 0x9AF8...` 是假哈希。
    故本条两头都锁：真名必须在场，而「无实据故不印」这句取舍也必须说出来 ——
    沉默地不印，读者无从知道这里做过取舍，也无从知道设计稿本来声称过什么。
    """
    assert "Kylver" in MANUSCRIPT_NOTE
    assert "Codex Regius" in MANUSCRIPT_NOTE
    assert "GKS 2365 4to" in MANUSCRIPT_NOTE
    assert "不印" in MANUSCRIPT_NOTE
    # 假声明连当反例原样引用也不行：这一段会被逐字印到页面上。
    assert "VERIFIED" not in MANUSCRIPT_NOTE
    assert "HASH" not in MANUSCRIPT_NOTE
    assert "0x9AF8" not in MANUSCRIPT_NOTE


def test_corpus_uses_no_curly_quotes() -> None:
    """弯引号一律不许出现（本仓约定用「」）—— 顺带也是 CJK 损坏的探针。"""
    for label, text in corpus_strings():
        assert "\u201c" not in text and "\u201d" not in text, label


def test_every_meaning_and_keyword_is_non_empty() -> None:
    for rune in DECK_25:
        assert rune.upright_meaning, rune.key
        assert rune.upright_keywords, rune.key
        assert all(k for k in rune.upright_keywords), rune.key
        if rune.reversed_keywords:
            assert all(k for k in rune.reversed_keywords), rune.key


def test_every_source_admits_it_is_not_a_verbatim_quotation() -> None:
    for rune in DECK_25:
        assert any(m in rune.source for m in NOT_VERBATIM_MARKERS), rune.key


# --- 8. 出处角标可分辨 -----------------------------------------------------


def test_source_reassembles_byte_exactly() -> None:
    assert RUNES_SOURCE == f"{RUNES_SOURCE_NAME}（{RUNES_SOURCE_QUALIFIER}）"
    assert SPREADS_SOURCE == f"{SPREADS_SOURCE_NAME}（{SPREADS_SOURCE_QUALIFIER}）"


def test_runes_source_puts_the_entry_before_the_parenthetical() -> None:
    """条目名拼在限定语**之前**：前端截断到第一个「（」，缀在末尾就会被切掉。"""
    chip = runes_source("Fehu").split("（")[0]
    assert "Fehu" in chip
    assert chip == f"{RUNES_SOURCE_NAME}·Fehu"


@pytest.mark.parametrize("rune", FUTHARK, ids=lambda r: r.key)
def test_each_rune_source_names_its_own_rune(rune) -> None:
    assert rune.source == runes_source(rune.name)
    assert rune.name in rune.source.split("（")[0]


def test_all_25_source_chips_are_distinguishable() -> None:
    """25 枚截断后互不撞车 —— 撞车就是数字命理走查查出的那个缺陷。"""
    chips = [r.source.split("（")[0] for r in DECK_25]
    assert len(set(chips)) == 25


def test_rune_sources_are_not_book_citations() -> None:
    """符文出处里没有《，故走前端截断分支 —— 上一条因此才是有效的守卫。

    若哪天有人往限定语里加了书名号，`citesBook()` 会翻成书引分支、角标改印全文，
    截断守卫就悄悄失效了。这条把前提钉住。
    """
    assert all("《" not in r.source for r in DECK_25)


# --- 9. 三种牌阵 -----------------------------------------------------------


@pytest.mark.parametrize(("spread_id", "size"), [("single", 1), ("three", 3), ("five", 5)])
def test_spread_sizes(spread_id: str, size: int) -> None:
    spread = get_spread(spread_id)
    assert isinstance(spread, Spread)
    assert spread.size == size
    assert len(spread.positions) == size


def test_spread_ids_match_the_dict() -> None:
    assert SPREAD_IDS == ("single", "three", "five")
    assert set(SPREADS) == set(SPREAD_IDS)
    assert DEFAULT_SPREAD_ID in SPREADS


def test_three_stone_positions_are_the_norns_in_order() -> None:
    assert [p.key for p in SPREADS["three"].positions] == ["urd", "verdandi", "skuld"]


def test_five_stone_positions_are_the_cross() -> None:
    assert [p.key for p in SPREADS["five"].positions] == [
        "center", "left", "right", "below", "above",
    ]


@pytest.mark.parametrize("spread_id", SPREAD_IDS)
def test_position_keys_are_distinct_within_a_spread(spread_id: str) -> None:
    keys = [p.key for p in SPREADS[spread_id].positions]
    assert len(set(keys)) == len(keys)


@pytest.mark.parametrize("spread_id", SPREAD_IDS)
def test_every_position_is_fully_filled(spread_id: str) -> None:
    for position in SPREADS[spread_id].positions:
        assert position.key and position.label and position.label_zh and position.meaning


def test_spread_sources_are_distinguishable() -> None:
    sources = [s.source for s in SPREADS.values()]
    assert len(set(sources)) == 3
    assert all(spreads_source(s.name_zh) == s.source for s in SPREADS.values())


def test_spread_qualifier_admits_the_layout_is_modern() -> None:
    """三女神之名是真的，「过去/现在/将来」这个读法与十字布局是今人的（决策 13/14）。"""
    assert "现代通行约定" in SPREADS_SOURCE_QUALIFIER
    assert "非古法" in SPREADS_SOURCE_QUALIFIER


def test_get_spread_returns_none_for_unknown_id() -> None:
    """语料层只答「有没有」，翻译成什么状态码是引擎的事。"""
    assert get_spread("celtic_cross") is None
    assert get_spread("yggdrasil") is None
    assert get_spread("") is None


# --- 10. 表清单 ------------------------------------------------------------


def test_rune_content_sources_lists_exactly_the_two_tables() -> None:
    """只列这两张：混进 `CONTENT_SOURCES` 等于让八字声称引了它没用过的表。"""
    assert RUNE_CONTENT_SOURCES == (
        ("rune_futhark", RUNES_SOURCE),
        ("rune_spreads", SPREADS_SOURCE),
    )


def test_the_two_tables_are_named_differently() -> None:
    """分开署名而非合成一张：两张的凭据强度不同（一张可单测核字形，一张只是现代约定）。"""
    names = [name for name, _ in RUNE_CONTENT_SOURCES]
    assert len(set(names)) == 2
    sources = [source for _, source in RUNE_CONTENT_SOURCES]
    assert len(set(sources)) == 2
