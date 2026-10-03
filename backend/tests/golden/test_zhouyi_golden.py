"""Golden tests for the Zhouyi (周易六爻) reference data and casting engine.

This module is built up across the Zhouyi implementation: it starts with the
structural content invariants (八 trigrams, 64 hexagrams across the eight
palaces, 纳甲 / 六神 tables) and grows to cover casting, derivation, the
classical text, the 白话今译 fields and the provenance block. Counts are content
invariants per PRD 4.4 — the data is curated, never generated.
"""

from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from app.content import CONTENT_VERSION, ZHOUYI_CONTENT_SOURCES as _ZHOUYI_CONTENT_SOURCES
from app.content.wuxing import ZHI_ELEMENT
from app.content.zhouyi_guaci import GUA_CI, GUA_CI_COUNT, YONG_CI
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
from app.content.zhouyi_plain import gua_ci_key, yao_ci_key, yong_ci_key
from app.content.zhouyi_text import (
    YAO_CI,
    YAO_CI_COUNT,
    gua_ci,
    line_name,
    yao_ci,
    yong_ci,
)
from app.content.zhouyi_trigrams import (
    TRIGRAMS,
    TRIGRAM_BY_BINARY,
    TRIGRAM_BY_KEY,
    TRIGRAM_BY_MEIHUA,
    TRIGRAM_BY_NATURE,
)
from app.content.zhouyi_yaoci_lower import YAO_CI_LOWER, YAO_CI_LOWER_COUNT
from app.content.zhouyi_yaoci_upper import YAO_CI_UPPER, YAO_CI_UPPER_COUNT
from app.core.errors import InvalidCastInputError
from app.engines.plain_compose import reading
from app.engines.plain_corpora import ZHOUYI
from app.engines.zhouyi import cast_hexagram
from app.schemas.zhouyi import CastMethod, HexagramInfo, ZhouyiLine

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


# --- Classical text: 卦辞 (hexagram judgments) -------------------------------


def test_all_sixty_four_gua_ci_are_present_and_nonempty() -> None:
    assert GUA_CI_COUNT == 64
    assert sorted(GUA_CI) == list(range(1, 65))
    for number, text in GUA_CI.items():
        assert isinstance(text, str) and text.strip(), number
        assert text.endswith("。"), number


def test_gua_ci_matches_the_received_text_for_known_hexagrams() -> None:
    assert GUA_CI[1] == "元亨利贞。"                       # 乾
    assert GUA_CI[2].startswith("元亨，利牝马之贞。")        # 坤
    assert GUA_CI[3] == "元亨利贞，勿用有攸往，利建侯。"    # 屯
    assert GUA_CI[44] == "女壮，勿用取女。"                 # 姤
    assert GUA_CI[63] == "亨小，利贞，初吉终乱。"           # 既济


def test_yong_ci_exists_only_for_qian_and_kun() -> None:
    assert set(YONG_CI) == {1, 2}
    assert YONG_CI[1][0] == "用九" and YONG_CI[1][1] == "见群龙无首，吉。"
    assert YONG_CI[2][0] == "用六" and YONG_CI[2][1] == "利永贞。"


# --- Classical text: 爻辞 (line statements) ---------------------------------


def test_yao_ci_canons_split_the_sequence_and_merge_to_384() -> None:
    assert YAO_CI_UPPER_COUNT == 30 and sorted(YAO_CI_UPPER) == list(range(1, 31))
    assert YAO_CI_LOWER_COUNT == 34 and sorted(YAO_CI_LOWER) == list(range(31, 65))
    assert YAO_CI_COUNT == 384
    assert sorted(YAO_CI) == list(range(1, 65))
    assert sum(len(texts) for texts in YAO_CI.values()) == 384


def test_every_hexagram_has_six_nonempty_line_statements() -> None:
    for number, texts in YAO_CI.items():
        assert len(texts) == 6, number
        for text in texts:
            assert isinstance(text, str) and text.strip(), number
            assert text.endswith("。"), number


def test_yao_ci_matches_the_received_text_for_known_lines() -> None:
    assert yao_ci(1, 1) == "潜龙勿用。"                       # 乾 初九
    assert yao_ci(1, 5) == "飞龙在天，利见大人。"             # 乾 九五
    assert yao_ci(1, 6) == "亢龙有悔。"                       # 乾 上九
    assert yao_ci(2, 1) == "履霜，坚冰至。"                   # 坤 初六
    assert yao_ci(2, 6) == "龙战于野，其血玄黄。"             # 坤 上六
    assert yao_ci(15, 1) == "谦谦君子，用涉大川，吉。"        # 谦 初六
    assert yao_ci(64, 6) == "有孚于饮酒，无咎，濡其首，有孚失是。"  # 未济 上九


def test_line_name_derives_the_classical_title() -> None:
    assert line_name(1, True) == "初九" and line_name(1, False) == "初六"
    assert line_name(2, True) == "九二" and line_name(2, False) == "六二"
    assert line_name(3, False) == "六三" and line_name(4, True) == "九四"
    assert line_name(5, True) == "九五" and line_name(5, False) == "六五"
    assert line_name(6, True) == "上九" and line_name(6, False) == "上六"


def test_text_accessors_agree_with_the_raw_tables() -> None:
    assert gua_ci(1) == GUA_CI[1]
    assert yong_ci(1) == YONG_CI[1]
    assert yong_ci(3) is None
    for number in range(1, 65):
        assert gua_ci(number) == GUA_CI[number]
        for position in range(1, 7):
            assert yao_ci(number, position) == YAO_CI[number][position - 1]


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


# --- Classical text carried by a cast ---------------------------------------


def test_qian_cast_carries_gua_ci_yong_jiu_and_yang_line_titles() -> None:
    result = _manual([[3, 2, 2]] * 6)  # 乾为天, all young yang, no moving lines
    assert result.ben.gua_ci == "元亨利贞。"
    assert result.ben.yong_ci == "见群龙无首，吉。"                       # 乾 用九
    assert [ln.yao_name for ln in result.lines] == ["初九", "九二", "九三", "九四", "九五", "上九"]
    assert result.lines[0].yao_ci == "潜龙勿用。"
    assert result.lines[4].yao_ci == "飞龙在天，利见大人。"


def test_kun_cast_uses_yin_line_titles_and_yong_liu() -> None:
    result = _manual([[2, 2, 2]] * 6)  # 坤为地, all young yin
    assert result.ben.number == 2
    assert result.ben.yong_ci == "利永贞。"                              # 坤 用六
    assert [ln.yao_name for ln in result.lines] == ["初六", "六二", "六三", "六四", "六五", "上六"]
    assert result.lines[0].yao_ci == "履霜，坚冰至。"


def test_moving_line_reads_yao_ci_from_the_primary_hexagram() -> None:
    result = _manual([[3, 3, 3]] + [[3, 2, 2]] * 5)  # 乾 line 1 moving -> 天风姤
    assert result.ben.number == 1 and result.bian is not None and result.bian.number == 44
    assert result.lines[0].moving is True
    assert result.lines[0].yao_name == "初九"
    assert result.lines[0].yao_ci == "潜龙勿用。"                        # from 乾, not 姤


def test_non_qian_kun_hexagram_has_no_yong_ci() -> None:
    result = cast_hexagram(method=CastMethod.TIME, cast_time=CAST_TIME)  # 天山遁 (33)
    assert result.ben.number == 33
    assert result.ben.gua_ci == "亨，小利贞。"
    assert result.ben.yong_ci is None


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
    assert body["ben"]["gua_ci"] == "元亨利贞。"
    assert body["bian"] is None
    assert len(body["lines"]) == 6
    assert body["lines"][0]["yao_name"] == "初九"
    assert body["lines"][0]["yao_ci"] == "潜龙勿用。"
    assert body["engine"] == "liuyao-najia"


def test_zhouyi_cast_endpoint_rejects_manual_without_coins(client: TestClient) -> None:
    response = client.post("/api/v1/zhouyi/cast", json={"method": "manual"})
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_cast_input"


# --- 白话今译随卦走（丁组 spec §5、§8） --------------------------------------


def test_the_plain_fields_are_required_not_defaulted() -> None:
    """必填即契约：缺字段视为伪造响应（spec §5 与多系统 spec 的 `score` 同一条立场）。
    只有用九/用六是合法的缺席，所以它带 default。"""
    assert HexagramInfo.model_fields["plain_gua_ci"].is_required()
    assert ZhouyiLine.model_fields["plain_yao_ci"].is_required()
    assert not HexagramInfo.model_fields["plain_yong_ci"].is_required()


def test_qian_cast_carries_every_plain_retelling_of_its_own_rows() -> None:
    """乾那一手：卦辞、用九、六爻今译逐条等于表里的那一条（对账走 `reading`，不抄第二份字面）。"""
    result = _manual([[3, 2, 2]] * 6)
    assert result.ben.plain_gua_ci == reading(ZHOUYI, gua_ci_key(1))
    assert result.ben.plain_yong_ci == reading(ZHOUYI, yong_ci_key(1))
    assert [line.plain_yao_ci for line in result.lines] == [
        reading(ZHOUYI, yao_ci_key(1, position)) for position in range(1, 7)
    ]


def test_a_plain_retelling_is_never_the_source_line_it_renders() -> None:
    """spec §4.2 门 2 的响应侧一半：今译字段里不许原样躺着经文——那是把源文当白话发出去。"""
    result = _manual([[3, 2, 2]] * 6)
    assert result.ben.plain_gua_ci != result.ben.gua_ci
    assert result.ben.plain_yong_ci != result.ben.yong_ci
    for line in result.lines:
        assert line.plain_yao_ci != line.yao_ci


def test_bian_and_hu_carry_their_own_plain_gua_ci() -> None:
    """`bian` / `hu` 走同一个 `_hexagram_info`，今译必须跟着走（spec §8 golden 行点名这两个）。

    六掷与 `scripts/record_frontend_fixtures.py` 的 zhouyi 夹具同手（丰 55 → 咸 31，互卦大过 28），
    T16 的前端测吃的就是这一手：两头对得上才叫一条链，不是两处各测各的。
    """
    result = _manual([[3, 3, 3], [3, 3, 2], [2, 2, 3], [3, 2, 2], [2, 2, 2], [3, 3, 2]])
    assert result.ben.number == 55
    assert result.bian is not None and result.bian.number == 31
    assert result.hu.number == 28
    assert result.bian.plain_gua_ci == reading(ZHOUYI, gua_ci_key(31))
    assert result.hu.plain_gua_ci == reading(ZHOUYI, gua_ci_key(28))
    assert result.bian.plain_yong_ci is None


def test_a_hexagram_without_yong_has_no_plain_yong_ci() -> None:
    """62 卦的 `None` 是忠实的缺席（spec §5），不许由引擎兜底编一句出来。"""
    result = cast_hexagram(method=CastMethod.TIME, cast_time=CAST_TIME)  # 天山遁 (33)
    assert result.ben.number == 33
    assert result.ben.yong_ci is None
    assert result.ben.plain_yong_ci is None
    assert result.ben.plain_gua_ci == reading(ZHOUYI, gua_ci_key(33))


def test_zhouyi_cast_endpoint_serves_the_plain_fields(client: TestClient) -> None:
    """HTTP 层的形状钉：键在响应里、值是表里那一条，六爻一个都不漏。

    纯乾一手安静（无动爻），`bian` 因此为 null——这条把它钉住，免得「一手安静」只是句旁白。
    """
    response = client.post(
        "/api/v1/zhouyi/cast",
        json={
            "method": "manual",
            "manual_coins": [[3, 2, 2]] * 6,
            "cast_time": "2024-05-15T10:30:00",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["ben"]["plain_gua_ci"] == reading(ZHOUYI, gua_ci_key(1))
    assert body["ben"]["plain_yong_ci"] == reading(ZHOUYI, yong_ci_key(1))
    assert [line["plain_yao_ci"] for line in body["lines"]] == [
        reading(ZHOUYI, yao_ci_key(1, position)) for position in range(1, 7)
    ]
    assert body["hu"]["plain_gua_ci"] == reading(ZHOUYI, gua_ci_key(1))
    assert body["bian"] is None


# --- 出处块：五张表 + 历法来源（丁组 spec §5、AGENTS.md §7） --------------------


def test_provenance_lists_exactly_the_five_tables_the_cast_reads() -> None:
    """响应忠于登记表：成对钉「名 + 出处串」，而不是只钉名。

    出处串的**字面**只住在 `tests/content/test_zhouyi_plain_corpus.py` 那一处（抄第二份字面
    违反 AGENTS.md §8），所以本测比的是投影相等于那张元组——引擎若改手抄五行、表名与次序都对而
    出处串写错，只有成对这一条抓得到（只钉名的话全套测照样绿）。下面那五行表名是刻意的第二份：
    它钉的是响应/展示序本身（登记表自己改序时它红，成对那一半只看忠实不忠实），
    T16 的前端夹具吃这一序。
    """
    provenance = _manual([[3, 2, 2]] * 6).provenance
    assert [(table.name, table.source) for table in provenance.tables] == list(_ZHOUYI_CONTENT_SOURCES)
    assert [table.name for table in provenance.tables] == [
        "zhouyi_trigrams",
        "zhouyi_hexagrams",
        "zhouyi_najia",
        "zhouyi_text",
        "zhouyi_plain",
    ]
    assert provenance.engine == "lunar-python"
    assert provenance.content_version == CONTENT_VERSION
    assert {table.version for table in provenance.tables} == {CONTENT_VERSION}
    assert all(table.source for table in provenance.tables)


def test_zhouyi_cast_endpoint_serves_the_provenance_block(client: TestClient) -> None:
    """键集即前端契约（`tests/test_meihua_api.py` 那套 `FRONTEND_*_KEYS` 的周易简化版：
    周易没有独立的 api 测文件，端点形状就钉在 golden 里，与 T14 那条端点测同一个家）。
    JSON 这一侧同样成对钉名与出处串：序列化不该让响应比引擎多知道一份表名。"""
    response = client.post(
        "/api/v1/zhouyi/cast",
        json={"method": "manual", "manual_coins": [[3, 2, 2]] * 6, "cast_time": "2024-05-15T10:30:00"},
    )
    assert response.status_code == 200
    body = response.json()
    assert set(body["provenance"]) == {"engine", "content_version", "tables"}
    for table in body["provenance"]["tables"]:
        assert set(table) == {"name", "version", "source"}
    assert [(table["name"], table["source"]) for table in body["provenance"]["tables"]] == list(
        _ZHOUYI_CONTENT_SOURCES
    )
