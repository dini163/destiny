"""十二长生（地势）表：10 干偏移 + 阳顺阴逆。

放 content 是因为它和神煞表同类：一张静止的查表 + 一句取法说明，推演在 engines。
偏移表照《三命通会·论五行旺相休囚死并寄生十二宫》的通行排法铺开：

    长生 沐浴 冠带 临官 帝旺 衰 病 死 墓 绝 胎 养

`丙 == 戊`、`丁 == 己` 是**火土同宫**（火寄于土），不是抄重了；阳干顺行、阴干逆行，
所以同一个支对阳干与阴干的位次相反。两条都由 `tests/test_bazi_changsheng.py` 的
120 格满覆盖对拍钉住 lunar-python 自己的表：若它改表，测试立刻红，而不是这里静默漂移。
"""

_GAN_ORDER = "甲乙丙丁戊己庚辛壬癸"
_BRANCH_ORDER = "子丑寅卯辰巳午未申酉戌亥"

CHANG_SHENG_ORDER: tuple[str, ...] = (
    "长生",
    "沐浴",
    "冠带",
    "临官",
    "帝旺",
    "衰",
    "病",
    "死",
    "墓",
    "绝",
    "胎",
    "养",
)
CHANG_SHENG_COUNT = len(CHANG_SHENG_ORDER)

#: 日干 -> 长生在十二支序上的偏移（阳干顺数、阴干逆数）。
CHANG_SHENG_OFFSET: dict[str, int] = {
    "甲": 1,
    "丙": 10,
    "戊": 10,
    "庚": 7,
    "壬": 4,
    "乙": 6,
    "丁": 9,
    "己": 9,
    "辛": 0,
    "癸": 3,
}

CHANG_SHENG_SOURCE = (
    "《三命通会·论五行旺相休囚死并寄生十二宫》"
    "（偏移与阳顺阴逆为本系统表法，与 lunar-python 120 格对拍）"
)


def di_shi(day_gan: str, zhi: str) -> str:
    """日主在某一支上的十二长生位次。查不到即报错，不返回空串。"""
    if day_gan not in CHANG_SHENG_OFFSET:
        raise ValueError(f"未知天干：{day_gan}")
    if zhi not in _BRANCH_ORDER:
        raise ValueError(f"未知地支：{zhi}")
    direction = 1 if _GAN_ORDER.index(day_gan) % 2 == 0 else -1  # 阳顺阴逆
    index = (CHANG_SHENG_OFFSET[day_gan] + _BRANCH_ORDER.index(zhi) * direction) % CHANG_SHENG_COUNT
    return CHANG_SHENG_ORDER[index]
