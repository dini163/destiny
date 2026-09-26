"""Golden tests for the 梅花易数 (Plum Blossom) derivation engine.

梅花 raises a hexagram deterministically (报数 or 年月日时) and reads it through 体用生克.
Both derivations below are hand-checkable against the 先天卦数 (1乾 2兑 3离 4震 5巽 6坎
7艮 8坤): 报数 [7,3] → 上卦艮(7)、下卦离(3) = 山火贲 (#22), 动爻 (7+3)÷6 余 4; the moving
line sits in the upper trigram, so 用=艮土、体=离火 → 体生用（泄气，小凶）. The 互卦 is the
nuclear 雷水解 (#40) and the 变卦 (line 4 flips 艮→离) is 离为火 (#30).
"""

from datetime import datetime

from fastapi.testclient import TestClient

from app.engines.meihua import cast_meihua

CAST = datetime(2024, 5, 15, 10, 30)


def _number_cast(numbers):
    return cast_meihua(method="number", numbers=numbers, question=None, cast_time=CAST)


def test_number_method_raises_the_expected_hexagram() -> None:
    cast = _number_cast([7, 3])
    assert cast.derivation.upper_number == 7  # 艮
    assert cast.derivation.lower_number == 3  # 离
    assert cast.moving_position == 4
    assert cast.ben.number == 22
    assert cast.ben.name_zh == "贲"
    assert cast.ben.full_name_zh == "山火贲"
    assert cast.ben.lines == [1, 0, 1, 0, 0, 1]


def test_nuclear_and_changed_hexagrams() -> None:
    cast = _number_cast([7, 3])
    assert cast.hu.number == 40
    assert cast.hu.full_name_zh == "雷水解"
    assert cast.bian.number == 30
    assert cast.bian.full_name_zh == "离为火"


def test_ti_yong_roles_and_verdict() -> None:
    cast = _number_cast([7, 3])
    # The moving line is in the upper trigram → upper is 用, lower is 体.
    assert cast.ti.trigram.name_zh == "离"
    assert cast.ti.trigram.element == "火"
    assert cast.yong.trigram.name_zh == "艮"
    assert cast.yong.trigram.element == "土"
    assert cast.tiyong.relation == "ti_sheng_yong"
    assert cast.tiyong.relation_zh == "体生用"
    assert cast.tiyong.verdict == "小凶"
    assert cast.tiyong.grade == -1


def test_wangshuai_uses_the_cast_month() -> None:
    cast = _number_cast([7, 3])
    assert cast.wangshuai.month_zhi == "巳"       # 立夏后为巳月
    assert cast.wangshuai.commanding_element == "火"


def test_score_ledger_is_bounded_and_transparent() -> None:
    cast = _number_cast([7, 3])
    assert 0 <= cast.score <= 100
    assert cast.verdict.strip()
    assert cast.summary.strip()
    assert len(cast.score_factors) >= 1
    assert cast.engine == "meihua-tiyong"


def test_all_three_hexagrams_are_six_binary_lines() -> None:
    cast = _number_cast([7, 3])
    for hexagram in (cast.ben, cast.hu, cast.bian):
        assert len(hexagram.lines) == 6
        assert all(line in (0, 1) for line in hexagram.lines)
        assert 1 <= hexagram.number <= 64


def test_time_method_is_deterministic() -> None:
    cast = cast_meihua(method="time", numbers=None, question=None, cast_time=CAST)
    assert cast.derivation.upper_number == 1  # 乾
    assert cast.derivation.lower_number == 7  # 艮
    assert cast.moving_position == 5
    assert cast.ben.number == 33
    assert cast.ben.full_name_zh == "天山遁"


def test_same_cast_time_yields_the_same_hexagram() -> None:
    first = cast_meihua(method="time", numbers=None, question=None, cast_time=CAST)
    second = cast_meihua(method="time", numbers=None, question=None, cast_time=CAST)
    assert first.ben.number == second.ben.number
    assert first.moving_position == second.moving_position


def test_meihua_endpoint(client: TestClient) -> None:
    response = client.post(
        "/api/v1/meihua/cast",
        json={"method": "number", "numbers": [7, 3], "cast_time": "2024-05-15T10:30:00"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["ben"]["number"] == 22
    assert body["tiyong"]["relation"] == "ti_sheng_yong"
    assert body["bian"]["number"] == 30
    assert body["engine"] == "meihua-tiyong"
