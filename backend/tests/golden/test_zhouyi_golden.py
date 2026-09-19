"""Golden tests for the Zhouyi (周易六爻) reference data and casting engine.

This module is built up across the Zhouyi implementation: it starts with the
structural content invariants (八 trigrams, 64 hexagrams across the eight
palaces, 纳甲 / 六神 tables) and grows to cover casting, derivation and the
classical text. Counts are content invariants per PRD 4.4 — the data is curated,
never generated.
"""

from app.content.wuxing import ZHI_ELEMENT
from app.content.zhouyi_hexagrams import (
    HEXAGRAMS,
    HEXAGRAM_BY_LINES,
    HEXAGRAM_BY_NUMBER,
    KING_WEN_SEQUENCE,
    PALACES,
    hexagram_from_lines,
    hexagram_from_trigrams,
)
from app.content.zhouyi_najia import (
    LIUSHEN_ORDER,
    LIUSHEN_START_BY_DAY_GAN,
    NAJIA,
    liushen_for_day_gan,
    najia_for_hexagram,
)
from app.content.zhouyi_trigrams import (
    TRIGRAMS,
    TRIGRAM_BY_BINARY,
    TRIGRAM_BY_KEY,
    TRIGRAM_BY_MEIHUA,
    TRIGRAM_BY_NATURE,
)

GAN = "甲乙丙丁戊己庚辛壬癸"


# --- Trigrams ---------------------------------------------------------------


def test_eight_trigrams_have_unique_structure() -> None:
    assert len(TRIGRAMS) == 8
    assert len({t.key for t in TRIGRAMS}) == 8
    assert len({t.binary for t in TRIGRAMS}) == 8
    assert len({t.nature_zh for t in TRIGRAMS}) == 8
    assert sorted(TRIGRAM_BY_MEIHUA) == list(range(1, 9))
    for trigram in TRIGRAMS:
        assert len(trigram.binary) == 3
        assert all(bit in (0, 1) for bit in trigram.binary)
        assert trigram.element in {"金", "木", "水", "火", "土"}


def test_trigram_lookups_are_consistent() -> None:
    for trigram in TRIGRAMS:
        assert TRIGRAM_BY_KEY[trigram.key] == trigram
        assert TRIGRAM_BY_NATURE[trigram.nature_zh] == trigram.key
        assert TRIGRAM_BY_BINARY[trigram.binary] == trigram.key
        assert TRIGRAM_BY_MEIHUA[trigram.meihua_number] == trigram.key


# --- Hexagrams --------------------------------------------------------------


def test_sixty_four_hexagrams_with_unique_numbers_and_lines() -> None:
    assert len(HEXAGRAMS) == 64
    assert sorted(h.number for h in HEXAGRAMS) == list(range(1, 65))
    assert len(HEXAGRAM_BY_LINES) == 64


def test_king_wen_and_palace_orderings_cover_the_same_set() -> None:
    king_wen_names = {entry[0] for entry in KING_WEN_SEQUENCE}
    palace_names = {name for _, names in PALACES for name in names}
    assert len(king_wen_names) == 64
    assert len(palace_names) == 64
    assert king_wen_names == palace_names


def test_hexagram_lines_match_their_trigrams() -> None:
    for hexagram in HEXAGRAMS:
        assert len(hexagram.lines) == 6
        assert all(bit in (0, 1) for bit in hexagram.lines)
        assert hexagram.lines[:3] == TRIGRAM_BY_KEY[hexagram.lower].binary
        assert hexagram.lines[3:] == TRIGRAM_BY_KEY[hexagram.upper].binary


def test_pure_hexagrams_repeat_one_trigram() -> None:
    pure = [h for h in HEXAGRAMS if "为" in h.full_name_zh]
    assert len(pure) == 8
    assert all(h.lower == h.upper for h in pure)


def test_palace_element_matches_palace_trigram() -> None:
    for hexagram in HEXAGRAMS:
        assert hexagram.palace_element == TRIGRAM_BY_KEY[hexagram.palace].element


def test_eight_palaces_each_have_one_ben_gong() -> None:
    ben_gong = [h for h in HEXAGRAMS if h.generation == "本宫"]
    assert len(ben_gong) == 8
    assert all(h.shi == 6 for h in ben_gong)
    assert len({h.palace for h in ben_gong}) == 8


def test_ying_is_three_lines_from_shi() -> None:
    for hexagram in HEXAGRAMS:
        assert 1 <= hexagram.shi <= 6
        assert hexagram.ying == ((hexagram.shi - 1 + 3) % 6) + 1


def test_hexagram_lookup_helpers() -> None:
    tun = HEXAGRAM_BY_NUMBER[3]
    assert tun.full_name_zh == "水雷屯"
    assert hexagram_from_lines(tun.lines) is tun
    lower = TRIGRAM_BY_KEY[tun.lower].binary
    upper = TRIGRAM_BY_KEY[tun.upper].binary
    assert hexagram_from_trigrams(lower, upper) is tun


# --- Najia and Liushen ------------------------------------------------------


def test_najia_table_covers_all_trigrams_with_valid_ganzhi() -> None:
    assert set(NAJIA) == {t.key for t in TRIGRAMS}
    for trigram in TRIGRAMS:
        for side in ("inner", "outer"):
            pairs = NAJIA[trigram.key][side]
            assert len(pairs) == 3
            for stem, branch in pairs:
                assert stem in GAN
                assert branch in ZHI_ELEMENT


def test_najia_for_hexagram_returns_six_pairs() -> None:
    pairs = najia_for_hexagram("zhen", "kan")  # 水雷屯 lower=震 upper=坎
    assert len(pairs) == 6
    assert pairs[0] == ("庚", "子")   # 震 inner first line
    assert pairs[3] == ("戊", "申")   # 坎 outer first line


def test_qian_and_kun_switch_stem_between_inner_and_outer() -> None:
    assert NAJIA["qian"]["inner"][0][0] == "甲"
    assert NAJIA["qian"]["outer"][0][0] == "壬"
    assert NAJIA["kun"]["inner"][0][0] == "乙"
    assert NAJIA["kun"]["outer"][0][0] == "癸"


def test_liushen_cycle_and_day_stem_coverage() -> None:
    assert len(LIUSHEN_ORDER) == 6
    assert len(set(LIUSHEN_ORDER)) == 6
    assert set(LIUSHEN_START_BY_DAY_GAN) == set(GAN)


def test_liushen_assignment_starts_from_day_stem_beast() -> None:
    # 甲/乙 day starts with 青龙 on line 1 and cycles through all six.
    beasts = liushen_for_day_gan("甲")
    assert beasts[0] == "青龙"
    assert set(beasts) == set(LIUSHEN_ORDER)
    # 壬/癸 day starts with 玄武.
    assert liushen_for_day_gan("壬")[0] == "玄武"
