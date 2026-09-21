"""十二长生自研表：形状 + 与 lunar-python 私有偏移表逐格等价 + 120 格满覆盖对拍。"""

import pytest
from lunar_python import Solar

from app.content.bazi_changsheng import (
    CHANG_SHENG_OFFSET,
    CHANG_SHENG_ORDER,
    di_shi,
)

_GANS = "甲乙丙丁戊己庚辛壬癸"
_ZHIS = "子丑寅卯辰巳午未申酉戌亥"


def test_table_shape() -> None:
    assert len(CHANG_SHENG_ORDER) == 12
    assert set(CHANG_SHENG_OFFSET) == set(_GANS)


def test_fire_and_soil_share_the_palace() -> None:
    """丙与戊、丁与己偏移同值 —— 火土同宫，不是笔误（spec §2.2）。"""
    assert CHANG_SHENG_OFFSET["丙"] == CHANG_SHENG_OFFSET["戊"]
    assert CHANG_SHENG_OFFSET["丁"] == CHANG_SHENG_OFFSET["己"]


def test_yang_stems_run_forward_and_yin_stems_backward() -> None:
    """阳顺阴逆：同一个支对阳干与阴干的位次方向相反。"""
    assert di_shi("甲", "子") == "沐浴"
    assert di_shi("甲", "丑") == "冠带"
    assert di_shi("乙", "子") == "病"
    assert di_shi("乙", "丑") == "衰"


@pytest.mark.parametrize(
    ("gan", "zhi", "expected"),
    [
        ("庚", "辰", "养"),
        ("庚", "子", "死"),
        ("庚", "寅", "绝"),
        ("庚", "亥", "病"),
        ("甲", "亥", "长生"),
    ],
)
def test_known_cells(gan: str, zhi: str, expected: str) -> None:
    assert di_shi(gan, zhi) == expected


def test_unknown_character_raises_rather_than_returning_empty() -> None:
    assert di_shi("甲", "寅") == "临官"  # 正常格，防改坏
    with pytest.raises(ValueError, match="未知天干"):
        di_shi("xx", "寅")
    with pytest.raises(ValueError, match="未知地支"):
        di_shi("甲", "yy")


def _sweep() -> dict[tuple[str, str], str]:
    """连续 12 年 × 立春后十日：年支遍历十二支、日干遍历十干，恰成 120 格。"""
    out: dict[tuple[str, str], str] = {}
    for year in range(2020, 2032):  # 2020 庚子 … 2031 辛亥，年支遍历十二支
        for day in range(5, 15):  # 立春后连续十日 ⇒ 十个不同日干
            ec = Solar.fromYmd(year, 2, day).getLunar().getEightChar()
            out[(ec.getDayGan(), ec.getYearZhi())] = ec.getYearDiShi()
    return out


def test_sweep_covers_all_120_cells() -> None:
    swept = _sweep()
    assert set(swept) == {(g, z) for g in _GANS for z in _ZHIS}  # 缺格即失败，不留死角


def test_di_shi_matches_lunar_python_on_every_cell() -> None:
    for (gan, zhi), expected in _sweep().items():
        assert di_shi(gan, zhi) == expected, f"{gan}日主 在{zhi}：期望 {expected}"
