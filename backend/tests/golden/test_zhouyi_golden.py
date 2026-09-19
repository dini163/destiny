"""Golden tests for the Zhouyi (周易六爻) reference data and casting engine.

This module is built up across the Zhouyi implementation: it starts with the
structural content invariants (八 trigrams, 64 hexagrams across the eight
palaces, 纳甲 / 六神 tables) and grows to cover casting, derivation and the
classical text. Counts are content invariants per PRD 4.4 — the data is curated,
never generated.
"""

from datetime import datetime

import pytest
from fastapi.testclient import TestClient

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
from app.core.errors import InvalidCastInputError
from app.engines.zhouyi import cast_hexagram
from app.schemas.zhouyi import CastMethod

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


# --- Casting and derivation -------------------------------------------------

# A fixed cast moment keeps the day pillar (己卯) and the time-method result
# deterministic; verified against lunar-python.
CAST_TIME = datetime(2024, 5, 15, 10, 30)


def _manual(coins: list[list[int]]):
    return cast_hexagram(method=CastMethod.MANUAL, manual_coins=coins, cast_time=CAST_TIME)


def test_manual_all_young_yang_is_qian() -> None:
    result = _manual([[3, 2, 2]] * 6)  # every throw sums to 7 (young yang)
    assert result.ben.number == 1
    assert result.ben.full_name_zh == "乾为天"
    assert result.moving_positions == []
    assert result.bian is None
    assert result.hu.number == 1  # nuclear hexagram of 乾 is 乾


def test_qian_najia_and_liuqin_match_the_classic_chart() -> None:
    result = _manual([[3, 2, 2]] * 6)
    assert [(ln.stem + ln.branch) for ln in result.lines] == ["甲子", "甲寅", "甲辰", "壬午", "壬申", "壬戌"]
    assert [ln.liuqin for ln in result.lines] == ["子孙", "妻财", "父母", "官鬼", "兄弟", "父母"]


def test_shi_and_ying_are_flagged_on_the_right_lines() -> None:
    result = _manual([[3, 2, 2]] * 6)
    shi = [ln.position for ln in result.lines if ln.is_shi]
    ying = [ln.position for ln in result.lines if ln.is_ying]
    assert shi == [result.ben.shi]
    assert ying == [result.ben.ying]


def test_liushen_follows_the_day_stem() -> None:
    result = _manual([[3, 2, 2]] * 6)
    assert result.day_ganzhi == "己卯"          # 己 day
    assert result.lines[0].liushen == "螣蛇"    # 己日起螣蛇
    assert [ln.liushen for ln in result.lines] == list(liushen_for_day_gan("己"))


def test_moving_line_transforms_ben_to_bian() -> None:
    result = _manual([[3, 3, 3]] + [[3, 2, 2]] * 5)  # line 1 is old yang (9)
    assert result.ben.number == 1
    assert result.moving_positions == [1]
    assert result.lines[0].value == 9
    assert result.lines[0].moving is True
    assert result.bian is not None
    assert result.bian.number == 44           # 乾 with line 1 changed -> 天风姤
    assert result.bian.full_name_zh == "天风姤"


def test_bian_flips_every_moving_line_and_only_those() -> None:
    coins = [[3, 3, 3], [3, 2, 2], [3, 2, 2], [2, 2, 2], [3, 2, 2], [3, 2, 2]]
    result = _manual(coins)                    # moving at lines 1 (old yang) and 4 (old yin)
    assert result.moving_positions == [1, 4]
    ben_lines = result.ben.lines
    bian_lines = result.bian.lines
    for position in range(1, 7):
        if position in result.moving_positions:
            assert bian_lines[position - 1] != ben_lines[position - 1]
        else:
            assert bian_lines[position - 1] == ben_lines[position - 1]


def test_hu_gua_is_the_nuclear_hexagram() -> None:
    result = _manual([[3, 3, 3], [3, 2, 2], [3, 2, 2], [2, 2, 2], [3, 2, 2], [3, 2, 2]])
    ben = result.ben.lines
    # 互卦: lower trigram = lines 2-3-4, upper trigram = lines 3-4-5 of the ben gua.
    assert result.hu.lines[:3] == ben[1:4]
    assert result.hu.lines[3:] == ben[2:5]


def test_time_method_is_deterministic_for_a_fixed_moment() -> None:
    result = cast_hexagram(method=CastMethod.TIME, cast_time=CAST_TIME)
    assert result.method == "time"
    assert result.ben.number == 33
    assert result.ben.full_name_zh == "天山遁"
    assert result.moving_positions == [5]
    assert result.bian is not None and result.bian.full_name_zh == "火山旅"


def test_line_values_encode_yin_yang_and_moving() -> None:
    # 6 old yin, 7 young yang, 8 young yin, 9 old yang.
    coins = [[2, 2, 2], [3, 2, 2], [3, 3, 2], [3, 3, 3], [2, 2, 2], [3, 2, 2]]
    result = _manual(coins)
    by_value = {ln.value: ln for ln in result.lines}
    assert by_value[6].yin_yang == "yin" and by_value[6].moving is True
    assert by_value[7].yin_yang == "yang" and by_value[7].moving is False
    assert by_value[8].yin_yang == "yin" and by_value[8].moving is False
    assert by_value[9].yin_yang == "yang" and by_value[9].moving is True
    assert by_value[6].symbol == "⚋" and by_value[9].symbol == "⚊"


def test_three_coin_lines_are_always_valid() -> None:
    for _ in range(50):
        result = cast_hexagram(method=CastMethod.THREE_COIN, cast_time=CAST_TIME)
        assert len(result.lines) == 6
        assert 1 <= result.ben.number <= 64
        for line in result.lines:
            assert line.value in {6, 7, 8, 9}


def test_three_coin_line_probabilities_match_theory() -> None:
    # Fair coins give old yin/old yang 1/8 each and young yang/yin 3/8 each.
    counts = {6: 0, 7: 0, 8: 0, 9: 0}
    casts = 1200
    for _ in range(casts):
        for line in cast_hexagram(method=CastMethod.THREE_COIN, cast_time=CAST_TIME).lines:
            counts[line.value] += 1
    total = casts * 6
    for value in (6, 9):
        assert 0.09 < counts[value] / total < 0.16
    for value in (7, 8):
        assert 0.34 < counts[value] / total < 0.41


def test_manual_cast_rejects_missing_or_malformed_coins() -> None:
    with pytest.raises(InvalidCastInputError):
        cast_hexagram(method=CastMethod.MANUAL, manual_coins=None, cast_time=CAST_TIME)
    with pytest.raises(InvalidCastInputError):
        _manual([[3, 2, 2]] * 5)                    # only five throws
    with pytest.raises(InvalidCastInputError):
        _manual([[3, 2, 4]] + [[3, 2, 2]] * 5)      # invalid coin face


# --- HTTP adapter -----------------------------------------------------------


def test_zhouyi_cast_endpoint(client: TestClient) -> None:
    response = client.post(
        "/api/v1/zhouyi/cast",
        json={
            "method": "manual",
            "manual_coins": [[3, 2, 2]] * 6,
            "question": "test",
            "cast_time": "2024-05-15T10:30:00",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["ben"]["number"] == 1
    assert body["bian"] is None
    assert len(body["lines"]) == 6
    assert body["engine"] == "liuyao-najia"


def test_zhouyi_cast_endpoint_rejects_manual_without_coins(client: TestClient) -> None:
    response = client.post("/api/v1/zhouyi/cast", json={"method": "manual"})
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_cast_input"
