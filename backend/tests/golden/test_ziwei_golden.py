"""Golden tests for the 紫微斗数 (Zi Wei Dou Shu) chart engine.

Reference birth: 2000-08-16 12:00 (solar), Beijing longitude, male, True Solar Time off.
The chart is fully deterministic from the 农历 data, and every value below is walked from
the classical 安星 tables and independently checkable: 庚辰年七月十七午时 puts 命宫在寅
(寅起正月顺数至七月得申，再从申起子时逆数至午时得寅); 五虎遁 庚年正月起戊寅 → 命宫戊寅
(纳音城头土); 庚干四化 = 太阳禄 / 武曲权 / 太阴科 / 天同忌; 庚(阳干)+男 → 阳男大限顺行,
起运虚岁 = 局数.
"""

from datetime import date, time

from fastapi.testclient import TestClient

from app.engines.ziwei import compute_ziwei_chart
from app.schemas.common import CalendarType, Gender

BIRTH = date(2000, 8, 16)
BTIME = time(12, 0)


def _chart(gender: Gender = Gender.MALE):
    return compute_ziwei_chart(
        birth_date=BIRTH,
        birth_time=BTIME,
        calendar=CalendarType.SOLAR,
        longitude=116.4074,
        gender=gender,
        apply_true_solar_time=False,
        name=None,
    )


def test_lunar_conversion_and_time_zhi() -> None:
    chart = _chart()
    assert chart.lunar_year_ganzhi == "庚辰"
    assert chart.lunar_month == 7
    assert chart.lunar_day == 17
    assert chart.lunar_leap is False
    assert chart.time_zhi == "午"  # 12:00 → 午时


def test_ming_gong_ganzhi_and_nayin() -> None:
    chart = _chart()
    assert chart.ming_gong_zhi == "寅"
    assert chart.ming_gong_ganzhi == "戊寅"   # 五虎遁：庚年正月起戊寅
    assert chart.ming_gong_nayin == "城头土"  # 戊寅己卯城头土
    assert chart.shen_gong_zhi == "寅"


def test_wuxing_ju_and_dayun_direction() -> None:
    chart = _chart()
    assert chart.wuxing_ju == "土五局"
    assert chart.wuxing_ju_number == 5
    assert chart.dayun_start_age == 5       # 起运虚岁 = 局数
    assert chart.dayun_direction == "顺行"   # 庚(阳干) + 男 → 阳男顺行


def test_dayun_direction_flips_by_gender() -> None:
    # 阳男阴女顺行 / 阴男阳女逆行：庚为阳干，故女命逆行。
    assert _chart(gender=Gender.FEMALE).dayun_direction == "逆行"


def test_sihua_matches_the_year_gan() -> None:
    chart = _chart()
    assert chart.sihua.year_gan == "庚"
    assert chart.sihua.lu == "太阳"
    assert chart.sihua.quan == "武曲"
    assert chart.sihua.ke == "太阴"
    assert chart.sihua.ji == "天同"


def test_ziwei_and_tianfu_share_the_ming_palace() -> None:
    chart = _chart()
    assert chart.ziwei_zhi == "寅"
    assert chart.tianfu_zhi == "寅"
    ming = next(p for p in chart.palaces if p.is_ming)
    star_names = {s.name for s in ming.stars}
    assert {"紫微", "天府"} <= star_names


def test_twelve_palaces_are_well_formed() -> None:
    chart = _chart()
    assert len(chart.palaces) == 12
    assert sorted(p.index for p in chart.palaces) == list(range(12))
    assert sum(1 for p in chart.palaces if p.is_ming) == 1
    for palace in chart.palaces:
        assert len(palace.ganzhi) == 2
        assert palace.ganzhi.endswith(palace.zhi)
    # The fourteen 主星 are laid exactly once across the board.
    main_stars = [s.name for p in chart.palaces for s in p.stars if s.kind == "主星"]
    assert len(main_stars) == 14
    assert len(set(main_stars)) == 14


def test_ziwei_endpoint(client: TestClient) -> None:
    response = client.post(
        "/api/v1/ziwei/chart",
        json={
            "birth_date": "2000-08-16",
            "birth_time": "12:00",
            "calendar": "solar",
            "longitude": 116.4074,
            "gender": "male",
            "apply_true_solar_time": False,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["ming_gong_zhi"] == "寅"
    assert body["wuxing_ju"] == "土五局"
    assert body["sihua"]["lu"] == "太阳"
    assert len(body["palaces"]) == 12
    assert body["engine"] == "ziwei-deterministic"
