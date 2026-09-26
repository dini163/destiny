"""Golden tests for the 奇门遁甲 (Qi Men Dun Jia) board engine.

Reference cast: 2024-05-15 10:30 (巳时). The board is fully deterministic — the 节气 +
日干支符头 fix the 局 (立夏上元 → 阳遁四局), the 时辰旬首 (甲子) fixes the 值符值使, and the
三奇六仪 地盘 follows the 阳遁四局 layout (戊起四宫顺行：戊己庚辛壬癸 then 丁丙乙). Every
star / door / god is walked from the 安盘 tables, so the nine palaces below are a real
洛书 board, not an invention.
"""

from datetime import datetime

from fastapi.testclient import TestClient

from app.engines.qimen import compute_qimen_chart

CAST = datetime(2024, 5, 15, 10, 30)

# 阳遁四局 地盘：戊起四宫顺布六仪，再布三奇（丁丙乙）于一二三宫。
DIPAN_BY_PALACE = {1: "丁", 2: "丙", 3: "乙", 4: "戊", 5: "己", 6: "庚", 7: "辛", 8: "壬", 9: "癸"}
NINE_STARS = {"天蓬", "天芮", "天冲", "天辅", "天禽", "天心", "天柱", "天任", "天英"}
EIGHT_DOORS = {"休门", "生门", "伤门", "杜门", "景门", "死门", "惊门", "开门"}
EIGHT_GODS = {"值符", "螣蛇", "太阴", "六合", "白虎", "玄武", "九地", "九天"}


def _chart(cast: datetime = CAST):
    return compute_qimen_chart(cast_time=cast, question=None)


def test_four_pillars() -> None:
    chart = _chart()
    assert chart.year_ganzhi == "甲辰"
    assert chart.month_ganzhi == "己巳"
    assert chart.day_ganzhi == "己卯"
    assert chart.time_ganzhi == "己巳"  # 10:30 → 巳时


def test_ding_ju() -> None:
    chart = _chart()
    assert chart.jieqi == "立夏"
    assert chart.yuan == "上元"
    assert chart.dun == "阳遁"
    assert chart.ju_number == 4
    assert chart.ju_name == "阳遁四局"


def test_zhifu_zhishi_and_xunshou() -> None:
    chart = _chart()
    assert chart.xunshou == "甲子"
    assert chart.xunshou_yi == "戊"   # 甲子遁戊
    assert chart.zhifu_star == "天辅"
    assert chart.zhishi_door == "杜门"
    assert chart.kongwang == "戌亥"   # 甲子旬空戌亥
    assert 1 <= chart.zhifu_palace <= 9
    assert 1 <= chart.zhishi_palace <= 9


def test_dipan_matches_yang_dun_ju_four() -> None:
    chart = _chart()
    for palace in chart.palaces:
        assert palace.dipan_gan == DIPAN_BY_PALACE[palace.number]


def test_nine_palaces_center_empty_others_populated() -> None:
    chart = _chart()
    assert len(chart.palaces) == 9
    assert sorted(p.number for p in chart.palaces) == list(range(1, 10))
    centers = [p for p in chart.palaces if p.is_center]
    assert len(centers) == 1 and centers[0].number == 5
    center = centers[0]
    assert center.door is None and center.god is None and center.stars == []
    for palace in chart.palaces:
        if not palace.is_center:
            assert palace.door is not None
            assert palace.god is not None
            assert len(palace.stars) >= 1


def test_all_stars_doors_gods_laid_exactly_once() -> None:
    chart = _chart()
    stars = [s.name for p in chart.palaces for s in p.stars]
    doors = [p.door.name for p in chart.palaces if p.door]
    gods = [p.god.name for p in chart.palaces if p.god]
    assert set(stars) == NINE_STARS
    assert len(stars) == len(set(stars)) == 9
    assert set(doors) == EIGHT_DOORS and len(doors) == 8
    assert set(gods) == EIGHT_GODS and len(gods) == 8


def test_zhifu_zhishi_palace_flags_are_unique() -> None:
    chart = _chart()
    assert sum(1 for p in chart.palaces if p.is_zhifu_palace) == 1
    assert sum(1 for p in chart.palaces if p.is_zhishi_palace) == 1


def test_qimen_endpoint(client: TestClient) -> None:
    response = client.post("/api/v1/qimen/chart", json={"cast_time": "2024-05-15T10:30:00"})
    assert response.status_code == 200
    body = response.json()
    assert body["ju_name"] == "阳遁四局"
    assert body["zhifu_star"] == "天辅"
    assert len(body["palaces"]) == 9
    assert body["engine"] == "qimen-luoshu-rotating"


def test_qimen_endpoint_defaults_cast_time_to_now(client: TestClient) -> None:
    response = client.post("/api/v1/qimen/chart", json={})
    assert response.status_code == 200
    body = response.json()
    assert len(body["palaces"]) == 9
    assert body["ju_number"] in range(1, 10)
    assert body["dun"] in {"阳遁", "阴遁"}
