"""吠陀占星 (Jyotish) golden —— 参考盘 2000-01-01 12:00 UT，格林尼治 (51.4769N, 0.0005W)。

那正是 J2000 历元，儒略日恰为 2451545.0，所以本文件里几乎所有数字都能在**不动引擎**
的前提下手推出来。写测顺序一律是「先独立复推，再采信引擎」——本轮 Task 7 的立测判据
（计划第 14 条），因为本系统没有 spec 文件，代码自述的锚点不能同时当出题人和答卷人。

三条独立锚（出处与推导都写在用它们的测里）：

1. **Lahiri 岁差在 J2000 = 23.857°**。《Indian Ephemerides》(Indian Observatory) 的 Lahiri
   表给 2000-01-01 的 ayanamsa = 23°51′；瑞士星历的解析岁差模型给 23.857092°。
   复测：`cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "import swisseph
   as swe; swe.set_sid_mode(swe.SIDM_LAHIRI);
   print(swe.get_ayanamsa_ut(swe.julday(2000,1,1,12.0)))"`
   → 23.857092353708822（2026-09-27 实录）。岁差是解析项，不读星历数据文件，所以这一条
   在只有 Moshier 的环境里照样成立。
2. **一般岁差常数 pA = 5029.0966″/儒略世纪**（IAU 1976；IAU 2006 Capitaine 的一阶项
   5029.12447″/世纪，两者差 0.028″，不影响本容差）= 1.396971°/世纪。ayanamsa 是岁差的
   累积量，所以 1900/2000/2100 三纪的逐段增量必须落在它附近。
3. **J2000 处太阳平均黄经 L₀ = 280.4664647°**（标准 J2000 根数，亦即 Meeus《Astronomical
   Algorithms》式 25.2 的第一项）。九曜里太阳是唯一能用一行公式独立复算的，故用它来
   证明「恒星黄经 = 热带黄经 − 岁差」这条本模块自述的换算真的发生了。

锚 1 还有一道**定义级**对照：Chitrapaksha 的公案是「Spica 落在 180°00′」，瑞士星历把它
做成 `SIDM_TRUE_CITRA`，与本引擎的 `SIDM_LAHIRI`（同一定义的解析拟合）实测差 56.6″–66.0″。
这句公案能在**星上**直接核，不必只核岁差多项式：Spica 在瑞士星历的**内置亮星表**里，
`fixstar_ut` 不读盘就能给它的黄经（要 `sefstars.txt` 的是 Vega 那类非内置星，wheel 未打包
该文件）。复测：`cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c
"import swisseph as swe; jd=swe.julday(2000,1,1,12.0);
print(swe.fixstar_ut('Spica',jd,0)[0][0], swe.fixstar_ut('Spica',jd,swe.FLG_SIDEREAL)[0][0])"`
→ 203.836145 / 179.982923（恒星黄经），`SIDM_TRUE_CITRA` 下第二个数是 180.0（2026-09-27 实录）；
推导与容差见 `test_spica_itself_sits_at_one_eighty_zero_under_the_chitrapaksha_definition`。

Vimshottari 一侧的独立锚是**体系本身**：九曜值年 7·20·6·10·7·18·16·19·17（共 120 年）与
计都→金星→太阳→太阴→火星→罗睺→木星→土星→水星的固定主序，是任何一本 Jyotish 手册
都同意的定则；安塔尔大运按 `大运值年 × 该曜值年 ÷ 120` 切分，也全部手算得出。

复测本文件测数：`cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m pytest
tests/golden/test_vedic_golden.py -v` → 28 passed（2026-09-27 实录，原 12 项全留、只收紧，
修复轮 1 另加一条在星上核 Chitrapaksha 定义的测）。
"""

from datetime import date, datetime, time

import pytest
import swisseph as swe
from fastapi.testclient import TestClient

from app.content.vedic import (
    DASHA_ORDER,
    DASHA_SPANS,
    DASHA_SPANS_BY_ORDER,
    GRAHAS,
    NAKSHATRA_SPAN,
    NAKSHATRAS,
    VIMSHOTTARI_TOTAL,
    nakshatra_of,
    pada_of,
)
from app.engines.vedic import _sidereal_flags, compute_vedic_chart

LAT = 51.4769
LON = -0.0005
BIRTH = date(2000, 1, 1)
TARGET = date(2026, 9, 25)

#: J2000 历元的儒略日（UT 12:00），手算即 2451544.5 + 1.0。
JD_J2000 = 2451545.0

#: 锚 1：Lahiri ayanamsa @ 2000-01-01（《Indian Ephemerides》23°51′，星历给 23.857092°）。
LAHIRI_AT_J2000 = 23.8571
#: 锚 2：一般岁差常数换算成度/儒略世纪。
PRECISION_DEG_PER_CENTURY = 5029.0966 / 3600.0
#: 锚 3：J2000 太阳平均黄经（Meeus 式 25.2 常数项）。
SUN_MEAN_LONGITUDE_J2000 = 280.4664647

#: 儒略年（平均回归年）日数：Vimshottari 的日期算术用它，公开常数 365.24219。
JULIAN_YEAR_DAYS = 365.24219

#: 独立抄自任意一本 Jyotish 手册的九曜值年与主序（不是从 app/content 读的）。
PUBLISHED_VIMSHOTTARI: tuple[tuple[str, int], ...] = (
    ("Ketu", 7), ("Venus", 20), ("Sun", 6), ("Moon", 10), ("Mars", 7),
    ("Rahu", 18), ("Jupiter", 16), ("Saturn", 19), ("Mercury", 17),
)

#: 27 宿的通行拉丁转写次序（Ashwini 起、Revati 终），独立手抄。
PUBLISHED_NAKSHATRAS: tuple[str, ...] = (
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
)

#: 星历数据文件缺失时 swe 仍会算，但必须如实回报它实际用了哪一副星历。
_MOON_BODIES: tuple[tuple[str, int], ...] = (
    ("Sun", swe.SUN), ("Moon", swe.MOON), ("Mars", swe.MARS), ("Mercury", swe.MERCURY),
    ("Jupiter", swe.JUPITER), ("Venus", swe.VENUS), ("Saturn", swe.SATURN),
    ("Rahu", swe.MEAN_NODE),
)


def _chart(target: date = TARGET):
    return compute_vedic_chart(
        birth_date=BIRTH,
        birth_time=time(12, 0),
        latitude=LAT,
        longitude=LON,
        utc_offset_hours=0.0,
        target_date=target,
        ephemeris_path=None,
    )


def _chart_at(year: int) -> object:
    """同一地点、同一 UTC 口径，只换出生世纪：用来核岁差的推进速率。"""
    return compute_vedic_chart(
        birth_date=date(year, 1, 1),
        birth_time=time(12, 0),
        latitude=LAT,
        longitude=LON,
        utc_offset_hours=0.0,
        target_date=date(year, 6, 1),
        ephemeris_path=None,
    )


def _degree_text(longitude: float) -> str:
    """按引擎的度分排版规则自行组装一条 `12°34'`（`app/engines/western.py:84-92`
    的 `_format_degree`，`app/engines/vedic.py:297` 经它印命度）。

    三步一条都不能省：①先折到**星座内**度数（0–30），不是 0–360 全黄经；②角分是
    **四舍五入**（`int(round(...))`），不是截断；③舍入到 60 分时度 +1、分归 0。
    独立性来自换路径而不是换实现——本测不调 `_format_degree`，把规则另写一遍再逐字符对。
    """
    within = (longitude % 360.0) % 30.0
    degrees = int(within)
    minutes = int(round((within - degrees) * 60))
    if minutes == 60:  # 舍入撞满 60 分时度 +1、分归 0——不写这一步就和引擎不同
        degrees += 1
        minutes = 0
    return f"{degrees}°{minutes:02d}'"


# ---------------------------------------------------------------- 参考盘与时标


def test_julian_day_and_lahiri_ayanamsa() -> None:
    chart = _chart()
    # 引擎把儒略日 round 到 5 位，J2000 恰为整数，故容差收到 1e-6（原来给的是 1e-4）。
    assert chart.julian_day == pytest.approx(JD_J2000, abs=1e-6)
    assert chart.zodiac == "sidereal"
    assert chart.ayanamsa_name == "Lahiri (Chitrapaksha)"
    # 原来是 23.0 < x < 25.0 的宽窗，宽到不能区分 Lahiri / Raman / Yajna。
    assert chart.ayanamsa == pytest.approx(LAHIRI_AT_J2000, abs=1e-4)


def test_navagraha_are_the_nine_classical_grahas_in_order() -> None:
    chart = _chart()
    assert [p.name for p in chart.planets] == [g.name for g in GRAHAS]
    assert len(chart.planets) == 9
    # No modern planets in classical Jyotish.
    assert {"Uranus", "Neptune", "Pluto"}.isdisjoint({p.name for p in chart.planets})


def test_ketu_is_exactly_opposite_rahu() -> None:
    chart = _chart()
    rahu = next(p.longitude for p in chart.planets if p.name == "Rahu")
    ketu = next(p.longitude for p in chart.planets if p.name == "Ketu")
    assert ketu == pytest.approx((rahu + 180.0) % 360.0, abs=1e-6)


def test_lagna_and_moon_are_sidereal() -> None:
    chart = _chart()
    assert chart.lagna_sign_zh == "白羊"
    assert chart.lagna_degree_text == "0°24'"
    assert chart.moon_sign_zh == "天秤"
    assert chart.moon_nakshatra_zh == "室伐底"  # Swati, ruled by Rahu
    assert chart.moon_nakshatra_lord_zh == "罗睺"
    assert chart.moon_pada == 4


def test_each_graha_nakshatra_matches_its_own_longitude() -> None:
    chart = _chart()
    for planet in chart.planets:
        assert planet.nakshatra == nakshatra_of(planet.longitude).name_en
        assert 1 <= planet.pada <= 4
        # 宿主的 Vimshottari 主曜必须与宿表同源（页面按此印「宿主」）。
        assert planet.nakshatra_lord == nakshatra_of(planet.longitude).lord
        assert planet.pada == pada_of(planet.longitude)


def test_whole_sign_houses_counted_from_lagna() -> None:
    chart = _chart()
    assert len(chart.rashis) == 12
    assert [r.sign_index for r in chart.rashis] == list(range(12))
    assert sum(1 for r in chart.rashis if r.is_lagna) == 1
    lagna = next(r for r in chart.rashis if r.is_lagna)
    assert lagna.house == 1
    for planet in chart.planets:
        cell = next(r for r in chart.rashis if r.sign_index == planet.sign_index)
        assert planet.house == cell.house
        assert planet.name in cell.planet_names


def test_vimshottari_span_and_birth_balance() -> None:
    chart = _chart()
    vs = chart.vimshottari
    assert vs.total_years == VIMSHOTTARI_TOTAL == 120
    assert vs.birth_nakshatra_zh == "室伐底"
    assert vs.birth_lord == "Rahu"
    assert vs.balance_at_birth_years == pytest.approx(0.7147, abs=1e-4)
    assert 0.0 < vs.balance_at_birth_years <= 18.0  # Rahu's full span


def test_mahadashas_tile_the_full_cycle_in_fixed_order() -> None:
    chart = _chart()
    vs = chart.vimshottari
    assert sum(m.years for m in vs.mahadashas) == pytest.approx(120.0, abs=0.05)
    lords = [m.lord for m in vs.mahadashas]
    start = DASHA_ORDER.index(lords[0])
    for i, lord in enumerate(lords):
        assert lord == DASHA_ORDER[(start + i) % 9]


def test_antardashas_sum_to_their_mahadasha() -> None:
    chart = _chart()
    for md in chart.vimshottari.mahadashas:
        assert md.antardashas
        assert sum(a.years for a in md.antardashas) == pytest.approx(md.years, abs=0.05)


def test_exactly_one_current_period_is_marked() -> None:
    chart = _chart()
    vs = chart.vimshottari
    current_md = [m for m in vs.mahadashas if m.is_current]
    assert len(current_md) == 1
    assert current_md[0].lord == "Saturn"
    # 「current」必须真的把目标日夹在区间里，而不只靠引擎内部同一个变量。
    assert current_md[0].start_date <= "2026-09-25" < current_md[0].end_date
    current_ad = [a for a in current_md[0].antardashas if a.is_current]
    assert len(current_ad) == 1
    assert current_ad[0].start_date <= "2026-09-25" < current_ad[0].end_date
    assert sum(1 for a in current_md[0].antardashas if a.is_current) == 1
    assert vs.current is not None
    assert vs.current.mahadasha_lord_zh == "土星"
    assert vs.current.antardasha_lord_zh == "太阳"
    assert vs.current.target_date == "2026-09-25"


# ---------------------------------------------------------------- 锚 1/2：岁差


def test_ayanamsa_advances_at_the_published_general_precession() -> None:
    """锚 2：岁差是累积量，逐世纪增量必须等于一般岁差常数 5029.0966″/世纪。

    独立在哪：常数来自 IAU 岁差模型（公开数字），不是从 swe 的输出读的；ayanamsa 的
    解析岁差项不依赖星历数据文件，所以本测在只有 Moshier 的环境里同样成立。
    实测（复测命令见模块 docstring 的锚 1，把年份换成 1900/2000/2100）：
    22.460550 / 23.857092 / 25.254287 → 逐段 1.396543° 与 1.397195°，
    与 1.396971° 分别差 1.543″ 与 0.806″（2026-09-27 实录）。
    容差 0.01°/世纪（36″）容得下岁差模型的二次项，也照样杀得掉「换了一副岁差模型」
    （IAU 常数错一位、或干脆不累积）。它**杀不掉**只换零点的同率派：实测 RAMAN、
    KRISHNAMURTI、YUKTESHWAR、JN_BHASIN、LAHIRI_1940 与 LAHIRI 的逐段增量相同到 1e-6°，
    差别只是一个常数（LAHIRI − RAMAN = 1.446301°，三个纪元一字不差）。那一类由
    ayanamsa 绝对值钉与本文件下一条 Chitrapaksha 交叉核对管（2026-09-27 实录，
    复测命令见下一条）。
    """
    first, middle, last = (_chart_at(year) for year in (1900, 2000, 2100))
    assert first.ayanamsa < middle.ayanamsa < last.ayanamsa
    assert middle.ayanamsa - first.ayanamsa == pytest.approx(PRECISION_DEG_PER_CENTURY, abs=0.01)
    assert last.ayanamsa - middle.ayanamsa == pytest.approx(PRECISION_DEG_PER_CENTURY, abs=0.01)
    # 岁差在加速：IAU 模型的二阶项让后半世纪比前半世纪略快。
    assert last.ayanamsa - middle.ayanamsa > middle.ayanamsa - first.ayanamsa


def test_lahiri_tracks_the_chitrapaksha_definition_within_a_minute_of_arc() -> None:
    """Chitrapaksha/Spica 路线：岁差多项式一侧核 Lahiri 与 TRUE_CITRA 的差，星本身另有一条测。

    探测经过本身是真的：绑定确实暴露了 `fixstar_ut`（先前探测找的 `calc_fixstar_ut` 是
    C 侧名字，Python 侧没有），本仓 wheel 也确实没有 `sefstars.txt`
    （`find .venv -iname 'sefstars*' -o -iname 'sestars*'` 零命中，2026-09-27）。但先前据此
    写的「所以定位置星表这条路不通」**不成立**：Spica 在瑞士星历的内置亮星表里，
    `swe.fixstar_ut("Spica", ...)` 直接返回热带黄经 203.836145°，读不读星表都一样；
    真需要 `sefstars.txt` 的是 Vega 那类非内置星（它们报
    `SwissEph file 'sefstars.txt' not found`）。先前那次「`fixstar_ut("Spica,αVir", ...)` 撞
    绑定解析 bug（`invalid literal for int()`）」疑为 GBK 控制台伪象：
    `PYTHONIOENCODING=utf-8` 下同一调用返回与裸名一字不差的值（复测命令见模块 docstring 锚 1）。
    星本身的位置因此另有专测，本测只管岁差多项式这一半：瑞士星历内置 `SIDM_TRUE_CITRA`，
    它的定义就是 Chitrapaksha 那句公案「Spica 落在 180°00′ 天秤」，与本引擎用的
    `SIDM_LAHIRI`（多项式近似）互为对照。

    实测（2026-09-27，复测见本段）：
    `cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "import swisseph as swe
    f=lambda:[swe.get_ayanamsa_ut(swe.julday(y,1,1,12.0)) for y in (1900,2000,2100)]
    swe.set_sid_mode(swe.SIDM_LAHIRI); l=f()
    swe.set_sid_mode(swe.SIDM_TRUE_CITRA); c=f()
    swe.set_sid_mode(swe.SIDM_RAMAN); r=f()
    print([round(x,6) for x in l], [round(x-y,6) for x,y in zip(l,c)],
    [round(x-y,6) for x,y in zip(l,r)])"`
    → LAHIRI 22.460550/23.857092/25.254287；LAHIRI−TRUE_CITRA 0.015726/0.017077/0.018326°
    （56.6″/61.5″/66.0″，一弧分上下）；LAHIRI−RAMAN 恒为 1.446301°。
    容差 0.02°（72″）：Lahiri 的官方口径本就是「最接近 Chitrapaksha 的解析拟合」，
    真把岁差模式设错（如 J2000 固定框，1900→2000 段会变成 −358.60°）就红。
    """
    epochs = (1900, 2000, 2100)

    def series(mode: int) -> list[float]:
        swe.set_sid_mode(mode)
        return [swe.get_ayanamsa_ut(swe.julday(year, 1, 1, 12.0)) for year in epochs]

    try:
        lahiri = series(swe.SIDM_LAHIRI)
        citra = series(swe.SIDM_TRUE_CITRA)
        raman = series(swe.SIDM_RAMAN)
    finally:
        swe.set_sid_mode(swe.SIDM_LAHIRI)  # 进程级全局态：必须装回引擎用的那一副

    for value, expected in zip(lahiri, (22.460550, 23.857092, 25.254287)):
        assert value == pytest.approx(expected, abs=1e-6)  # 本引擎实际用的那一副的三纪值
    for index in range(3):
        assert abs(lahiri[index] - citra[index]) < 0.02  # 与 Spica=180° 的定义差不到一弧分强
        assert lahiri[index] > citra[index]  # 且方向恒定：Lahiri 略大
    # 只换零点的同率派：率相同、差为常数——上一条测的容差为什么杀不到它，证据在这里。
    offsets = {round(lahiri[index] - raman[index], 6) for index in range(3)}
    assert offsets == {1.446301}
    rates = [lahiri[1] - lahiri[0], raman[1] - raman[0]]
    assert rates[0] == pytest.approx(rates[1], abs=1e-6)


def test_spica_itself_sits_at_one_eighty_zero_under_the_chitrapaksha_definition() -> None:
    """定义级对照落在**星上**，不只是岁差多项式的自证：Chitrapaksha 说 Spica = 180°00′。

    上一条测比的是两套岁差的**差**（解析量，与天上的星无关）；这条核那颗星自己的恒星黄经：
    `swe.fixstar_ut("Spica", jd, FLG_SIDEREAL)`。Spica 在瑞士星历的内置亮星表里，
    本绑定 wheel 未打包 `sefstars.txt` 也照样给得出位置（Vega 那类非内置星才要那张表）。
    实测（2026-09-27，三纪 1900/2000/2100）：
    `cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "import swisseph as swe
    for mode in (swe.SIDM_LAHIRI, swe.SIDM_TRUE_CITRA):
        swe.set_sid_mode(mode); print([swe.fixstar_ut('Spica', swe.julday(y,1,1,12.0),
    swe.FLG_SIDEREAL)[0][0] % 360.0 for y in (1900,2000,2100)])"`
    → TRUE_CITRA 三纪都是 180.0（定义本身，逐位精确）；LAHIRI 是
    179.984274 / 179.982923 / 179.981674，与 180° 差 56.61″ / 61.48″ / 65.98″。
    容差 0.02°（=72″）与上一条测同源、覆盖三纪最大 65.98″，不是一弧分——「一弧分上下」是
    描述，不是判据。
    """
    epochs = (1900, 2000, 2100)
    positions: dict[int, list[float]] = {}
    try:
        for mode in (swe.SIDM_LAHIRI, swe.SIDM_TRUE_CITRA):
            swe.set_sid_mode(mode)
            positions[mode] = [
                swe.fixstar_ut("Spica", swe.julday(year, 1, 1, 12.0), swe.FLG_SIDEREAL)[0][0]
                % 360.0
                for year in epochs
            ]
    finally:
        swe.set_sid_mode(swe.SIDM_LAHIRI)  # 进程级全局态：装回引擎用的那一副

    # 那一副岁差模式按定义就是把这颗星压在 180°00′ 上：三纪逐位精确，不给容差。
    for year, citra in zip(epochs, positions[swe.SIDM_TRUE_CITRA]):
        assert citra == pytest.approx(180.0, abs=1e-9), year
    # 本引擎用的 LAHIRI 是同一句公案的解析拟合：差在一弧分上下，且方向恒定（拟合略小）。
    for year, lahiri in zip(epochs, positions[swe.SIDM_LAHIRI]):
        offset = 180.0 - lahiri
        assert 0.0 < offset < 0.02, year


def test_sidereal_longitudes_are_tropical_minus_ayanamsa() -> None:
    """本模块自述「sidereal = tropical − ayanamsa」，那就按这句话逐曜复算一遍。

    取的是同一瞬时、同一 Moshier 星历，但**不带 FLG_SIDEREAL** 的调用，再减掉锚 1 的
    岁差——两条独立的库路径必须落在同一个恒星黄经上。
    实测差值：八曜全部 13.85″–14.10″（2026-09-27 复测见本测 docstring 末的命令），
    那是「视位置」与「分点岁差参考框架」之间的固有差，不是算错。容差 0.005°=18″，
    容得下它，但绝容不下一个用错的岁差（Raman/Yajna 与 Lahiri 差 0.1° 以上）或干脆
    忘了减岁差（差 23.86°）。
    复测：`cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "import swisseph
    as swe; swe.set_sid_mode(swe.SIDM_LAHIRI); jd=swe.julday(2000,1,1,12.0);
    a=swe.get_ayanamsa_ut(jd); pairs=[(swe.SUN,256.5157),(swe.MOON,199.4706),
    (swe.MARS,304.1101),(swe.MERCURY,248.0361),(swe.JUPITER,1.3998),(swe.VENUS,217.7126),
    (swe.SATURN,16.5424),(swe.MEAN_NODE,101.1874)];
    print(max(abs((swe.calc_ut(jd,b,swe.FLG_SPEED)[0][0]-a)%360 - s) for b,s in pairs))"`
    """
    chart = _chart()
    ayanamsa = swe.get_ayanamsa_ut(JD_J2000)
    assert ayanamsa == pytest.approx(LAHIRI_AT_J2000, abs=1e-4)
    for name, body in _MOON_BODIES:
        tropical = swe.calc_ut(JD_J2000, body, swe.FLG_SPEED)[0][0]
        predicted = (tropical - ayanamsa) % 360.0
        actual = next(p.longitude for p in chart.planets if p.name == name)
        assert predicted == pytest.approx(actual, abs=0.005), name


def test_the_sun_of_j2000_lands_where_the_textbook_elements_put_it() -> None:
    """锚 3：J2000 的太阳是公开根数，唯一能整条独立复推的曜。

    L₀ = 280.4664647° 是标准 J2000 太阳根数（Meeus 式 25.2 常数项，亦即 USNO/《Astronomical
    Almanac》用的那一条）。J2000 历元当天 M = 357.5291°，均距点改正 C = 2e·sin M = −0.083°
    （e = 0.016709；先前这里写 −0.068°，按该式重算于 2026-09-27 推翻），再加光行差 −20.5″
    → 视热带黄经 280.378°；减锚 1 的岁差 23.8571° → 恒星黄经 256.521°，引擎实测
    256.5157°（差 0.005°：一阶根数不含升交点/章动项的固有差）。256.52° 落在射手座
    （240–270）第 20 宿 Purva Ashadha（253.333°–266.667°）第 1 足（253.333°–256.667°）。
    这一串数字全由锚 1 与锚 3 手推，不经引擎；引擎给的正是 Purva Ashadha pada 1。
    """
    chart = _chart()
    sun = next(p for p in chart.planets if p.name == "Sun")
    tropical = (sun.longitude + chart.ayanamsa) % 360.0
    assert tropical == pytest.approx(SUN_MEAN_LONGITUDE_J2000, abs=0.5)
    predicted_sidereal = SUN_MEAN_LONGITUDE_J2000 - LAHIRI_AT_J2000
    assert predicted_sidereal == pytest.approx(sun.longitude, abs=0.5)
    assert sun.sign == "Dhanu" and sun.sign_index == 8
    assert nakshatra_of(predicted_sidereal).name_en == "Purva Ashadha"
    assert pada_of(predicted_sidereal) == 1
    assert sun.nakshatra == "Purva Ashadha" and sun.pada == 1


def test_the_lagna_is_the_sidereal_ascendant_of_the_same_instant() -> None:
    """命度也要能独立复推：swe.houses 的热带上升点减岁差，就是印在盘上的度分。

    上升点公式本身归瑞士星历（AGENTS 第 6 条不许自算），所以独立性来自**换了条路径**：
    这里取不带 FLG_SIDEREAL 的 houses()，自己减 ayanamsa，再按引擎那套「星座内度数 +
    角分四舍五入 + 满 60 进 1」的排版规则（`_degree_text`，见其 docstring 的三步）组装字符串，
    与引擎的 lagna_degree_text 逐字符对。
    实测：ascmc[0] = 24.26414° → 24.26414 − 23.85709 = 0.40705° → 0°24′（2026-09-27 实录）。
    参考盘的 0.40705° 折算出的 24.423′ 恰好在截断与四舍五入的同侧，所以本测另钉一个
    **两条规则分道扬镳**的取值：不另加测的话，「把舍入写成截断」在这张盘上悄无声息。
    同时钉住整宫制的第 1 宫就是命度所在的 Mesha。
    """
    chart = _chart()
    swe.set_sid_mode(swe.SIDM_LAHIRI)  # 与 _sidereal_flags 同一调用，幂等；见测末说明
    _cusps, ascmc = swe.houses(JD_J2000, LAT, LON, b"W")
    ayanamsa = swe.get_ayanamsa_ut(JD_J2000)
    lagna = (ascmc[0] - ayanamsa) % 360.0
    assert lagna == pytest.approx(0.4071, abs=0.01)
    assert _degree_text(lagna) == chart.lagna_degree_text
    # 舍入 + 进位：10.9918° 的分数部分 ×60 = 59.508′，截断给 59、四舍五入给 60 再进位到 11°00'。
    assert _degree_text(10.9918) == "11°00'"
    assert f"{int(10.9918)}°{int((10.9918 % 1) * 60):02d}'" == "10°59'"  # 旧写法（截断）留在原地作对照
    # 排版口径是「星座内」：同一位置写成全黄经 370.9918° 必须折回同一条字符串。
    assert _degree_text(370.9918) == "11°00'"
    assert chart.lagna_sign == "Mesha" and chart.lagna_index == 0
    assert chart.lagna_nakshatra == "Ashwini"


# ---------------------------------------------------------------- Step 2：星历模式诚实性


def test_the_ephemeris_flag_branch_is_a_pure_bit_choice(monkeypatch) -> None:
    """`_sidereal_flags` 的分支只能用位标志证明——`swe.set_ephe_path` 是进程级全局态。

    pyswisseph 2.10.03 没有 `get_ephe_path`，一旦被写脏就取不回原值，会把 DE 文件路径
    漏给同一 pytest 进程里的 western/transit/synastry。所以本测把 `set_ephe_path`
    换成记录器（`monkeypatch` 在测末原样装回），断言的是**返回的 flag 位**与**被转发的
    路径字符串**，不是任何算出来的度数——没有 mock 数据，只有被隔离的副作用。
    """
    calls: list[str] = []
    monkeypatch.setattr(swe, "set_ephe_path", calls.append)

    with_path = _sidereal_flags("E:/destiny/ephe")
    without_path = _sidereal_flags(None)
    assert calls == ["E:/destiny/ephe"]  # 只有配了路径才碰全局态，且原样转发

    assert with_path & swe.FLG_SWIEPH and not with_path & swe.FLG_MOSEPH
    assert without_path & swe.FLG_MOSEPH and not without_path & swe.FLG_SWIEPH
    for flags in (with_path, without_path):
        assert flags & swe.FLG_SIDEREAL  # 恒星黄道是两支共同的，缺它就是退回热带
        assert flags & swe.FLG_SPEED  # 逆行与速度字段靠这一位
    assert with_path ^ without_path == swe.FLG_SWIEPH | swe.FLG_MOSEPH


def test_a_swieph_request_without_data_files_is_silently_answered_by_moshier() -> None:
    """PRD §4.1/§6 六处（62、142、216、270、281、415 行）声称「瑞士历表 DE431」；本地实测：一副都不在。

    现测（2026-09-27）：
    * 仓库与虚拟环境里没有任何星历数据文件——
      `find .venv -iname '*.se1' -o -iname '*.se2' -o -iname '*.mos'` 零命中；
      `backend/Dockerfile` 只 COPY app 与 data，`docker-compose.yml` 无 SWEPH_EPHE_PATH，
      `.env.example:20` 的 `SWEPH_EPHE_PATH=` 为空 → 线上永远走 `_sidereal_flags(None)`。
    * 于是同一瞬时按 FLG_SWIEPH 与 FLG_MOSEPH 各算一遍八曜，结果**逐位相同**：
      最大角差 0.0 角秒（复测命令见本测末），且 swe 回报的 retflags 里带的是
      FLG_MOSEPH 位——库自己承认用了 Moshier，却不报警、不抛错。
    * 唯一例外是平交点（Rahu）：它是解析量，retflags 会带 FLG_SWIEPH 位，数值仍相同。

    这就是要钉的证据：算出来的确是真天文（Moshier 解析历），但「DE431」这句声称在运行时
    没有任何东西兜着。若日后真把 DE 文件配进镜像，本测的最后两条会转红——那是**故意的
    哨兵**：届时必须重新量一次两法角差并重写 docstring，而不是把断言删掉。
    复测：`cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "import swisseph
    as swe; swe.set_sid_mode(swe.SIDM_LAHIRI); jd=swe.julday(2000,1,1,12.0);
    sw=swe.FLG_SPEED|swe.FLG_SWIEPH|swe.FLG_SIDEREAL;
    ms=swe.FLG_SPEED|swe.FLG_MOSEPH|swe.FLG_SIDEREAL;
    print(max(abs(swe.calc_ut(jd,b,sw)[0][0]-swe.calc_ut(jd,b,ms)[0][0]) for b in
    [swe.SUN,swe.MOON,swe.MARS,swe.MERCURY,swe.JUPITER,swe.VENUS,swe.SATURN,swe.MEAN_NODE]))"` → 0.0
    """
    swe.set_sid_mode(swe.SIDM_LAHIRI)  # 与引擎同一句，幂等：全仓只有 vedic 会设 sid mode
    swieph = swe.FLG_SPEED | swe.FLG_SWIEPH | swe.FLG_SIDEREAL
    moshier = swe.FLG_SPEED | swe.FLG_MOSEPH | swe.FLG_SIDEREAL
    # 最大角差**独立复算**一遍：另起一路 fresh 调用，不复用下面逐位相同断言的那两个值。
    # 这个数字是 F-A1-9 的证据（也是本测 docstring 末那条复测命令的断言化），值得真算。
    worst_arcsec = max(
        abs(swe.calc_ut(JD_J2000, body, swieph)[0][0] - swe.calc_ut(JD_J2000, body, moshier)[0][0])
        * 3600.0 for _, body in _MOON_BODIES
    )
    assert worst_arcsec == 0.0  # 两法逐位相同；配好 DE 件后这条转红是故意的哨兵
    for name, body in _MOON_BODIES:
        claimed, ret_swieph = swe.calc_ut(JD_J2000, body, swieph)
        actual, ret_mos = swe.calc_ut(JD_J2000, body, moshier)
        assert claimed == actual, name  # 逐位相同：拿不到 DE431 的任何差别
        if name != "Rahu":  # 平交点是解析项，不算「用了哪副星历」的证据
            assert ret_swieph & swe.FLG_MOSEPH, name
            assert not ret_swieph & swe.FLG_SWIEPH, name


def test_the_default_configuration_leaves_the_engine_on_the_analytical_branch() -> None:
    """配置默认值决定线上走哪一支：`sweph_ephe_path` 默认空串 → API 传下去的是 None。

    `app/api/v1/vedic.py:32` 写的是 `settings.sweph_ephe_path or None`，空串被折成 None，
    所以默认部署永远是 Moshier 分支。钉的是**代码里的字段默认值**（不是本机的 .env，
    开发者可能填过真路径），并复现 API 那一行的折值表达式。
    """
    from app.core.config import Settings

    default_path = Settings.model_fields["sweph_ephe_path"].default
    assert default_path == ""
    # 不再另断 `(default_path or None) is None`：上一行的空串已经钉死，那条恒真。折值表达式照样
    # 复现一遍（`app/api/v1/vedic.py:32`），但别把它读成「少了折值就红」——`_sidereal_flags`
    # 用的是真值判断，空串与 None 在这一支同义。
    flags = _sidereal_flags(default_path or None)
    assert flags & swe.FLG_MOSEPH and not flags & swe.FLG_SWIEPH


# ---------------------------------------------------------------- Step 3：Vimshottari


def test_the_dasha_lords_and_spans_are_the_published_vimshottari_values() -> None:
    """主序与值年是体系的公开定则，独立于 `app/content/vedic.py` 的表抄一份。

    表与这份手抄不一致，就说明语料被改过而没人重读文献；两者一致才谈得上后面的算术。
    """
    assert DASHA_ORDER == tuple(name for name, _ in PUBLISHED_VIMSHOTTARI)
    assert DASHA_SPANS_BY_ORDER == tuple(span for _, span in PUBLISHED_VIMSHOTTARI)
    assert DASHA_SPANS == dict(PUBLISHED_VIMSHOTTARI)
    assert sum(span for _, span in PUBLISHED_VIMSHOTTARI) == 120 == VIMSHOTTARI_TOTAL


def test_the_mahadasha_windows_tile_exactly_one_hundred_twenty_years() -> None:
    """120 年无缝铺满：窗口首尾相接、起点就是出生日、终点差恰为 120 个回归年。

    起算点独立可推：120 × 365.24219 = 43829.06 日，而 2000-01-01 → 2120-01-01 的日历差
    是 43829 天（含 29 个闰日：2000..2116 每四年一闰、2100 不闰）。容差 1 天是日期串
    截断到日的固有误差。
    """
    vs = _chart().vimshottari
    mds = vs.mahadashas
    assert len(mds) == 10  # 九曜一整轮 + 第十段是回卷后被 120 年截断的首曜
    assert mds[0].start_date == "2000-01-01"  # 出生当日本地时
    for previous, following in zip(mds, mds[1:]):
        assert previous.end_date == following.start_date, previous.lord
        assert previous.end_date > previous.start_date
    start = datetime.strptime(mds[0].start_date, "%Y-%m-%d").date()
    end = datetime.strptime(mds[-1].end_date, "%Y-%m-%d").date()
    assert (end - start).days == pytest.approx(120 * JULIAN_YEAR_DAYS, abs=1.0)
    # 满轮的那些段落必须恰好是各自的公布值年；首尾两段才是余额与截断。
    spans = dict(PUBLISHED_VIMSHOTTARI)
    for md in mds[1:-1]:
        assert md.years == spans[md.lord], md.lord
    assert mds[-1].lord == mds[0].lord == "Rahu"
    assert mds[-1].years == pytest.approx(spans["Rahu"] - vs.balance_at_birth_years, abs=1e-3)


def test_the_timeline_starts_at_the_moon_own_nakshatra_balance() -> None:
    """起算点 = 本命月宿余额：整条 120 年轴由月亮在宿内的行程比例唯一决定。

    手推（不读 vs 的字段，只用八曜表里那个月亮黄经）：
    * 宿序 = int(199.4706 ÷ 13.3333) = 14 → Swati，主曜 Rahu（第 14 宿在九曜循环的第 5 位）。
    * 宿内比例 = (199.4706 − 14×13.3333) ÷ 13.3333 = 0.960295 → 已走过 96.03%。
    * 余额 = 18 × (1 − 0.960295) = 0.7147 年，即出生时 Rahu 大运只剩 0.7147 × 12 ≈ 8.6 个历月
      （先前写 8.7，与本行算式不符）。
    * 首段大运的安塔尔只留一段：Rahu 轮内九段（18×各值年÷120）累计 16.95 年时仍在
      第 8 段末，已走过的 17.2853 年落进第 9 段 Mars，故截出来正是 Mars 的 0.7147 年。
    容差 1e-4 是引擎对余额与比例各自 round 的位宽，不是放宽——原来的 abs=0.01 宽 100 倍。
    """
    chart = _chart()
    vs = chart.vimshottari
    moon = next(p for p in chart.planets if p.name == "Moon")
    index = int(moon.longitude // NAKSHATRA_SPAN)
    fraction = (moon.longitude % NAKSHATRA_SPAN) / NAKSHATRA_SPAN
    assert NAKSHATRAS[index].name_en == "Swati"
    assert vs.birth_nakshatra == NAKSHATRAS[index].name_en == chart.moon_nakshatra
    assert vs.birth_lord == NAKSHATRAS[index].lord == "Rahu" == chart.moon_nakshatra_lord
    assert fraction == pytest.approx(vs.moon_elapsed_fraction, abs=1e-6)

    birth_span = dict(PUBLISHED_VIMSHOTTARI)[vs.birth_lord]
    assert birth_span == 18
    assert birth_span * (1.0 - fraction) == pytest.approx(vs.balance_at_birth_years, abs=1e-4)

    first = vs.mahadashas[0]
    assert first.years == pytest.approx(vs.balance_at_birth_years, abs=1e-4)
    # 用公布值年手算月宿里已走过的年数，定位它落在第几段安塔尔。
    order = [name for name, _ in PUBLISHED_VIMSHOTTARI]
    start_index = order.index(vs.birth_lord)
    elapsed = birth_span * fraction
    walked = 0.0
    holder: str | None = None
    for offset in range(9):
        length = birth_span * dict(PUBLISHED_VIMSHOTTARI)[
            order[(start_index + offset) % 9]] / 120.0
        if walked <= elapsed < walked + length:
            holder = order[(start_index + offset) % 9]
        walked += length
    assert holder is not None
    assert [a.lord for a in first.antardashas] == [holder] == ["Mars"]
    assert first.antardashas[0].years == pytest.approx(birth_span - elapsed, abs=1e-3)


def test_every_full_mahadasha_splits_into_the_nine_published_antardashas() -> None:
    """每个整段大运的九个小运都按 `大运值年 × 小运主曜值年 ÷ 120` 切，主序同大运主序。

    这条是 Step 3 的硬门：`test_antardashas_sum_to_their_mahadasha` 只核了「加起来等于
    本段」，把九段等比放大同样能过；这里逐段点名核到 1e-4 年（1e-4 × 365.24219 天 ≈ 0.0365 天
    ≈ 53 分钟）。
    首段（余额截断）与末段（120 年截断）不在射程内，各自由
    `test_the_timeline_starts_at_the_moon_own_nakshatra_balance` 与铺满轴那条测管。
    """
    mds = _chart().vimshottari.mahadashas
    order = [name for name, _ in PUBLISHED_VIMSHOTTARI]
    spans = dict(PUBLISHED_VIMSHOTTARI)
    for md in mds[1:-1]:
        start_index = order.index(md.lord)
        assert [a.lord for a in md.antardashas] == order[start_index:] + order[:start_index]
        assert len(md.antardashas) == 9
        for offset, ad in enumerate(md.antardashas):
            expected = spans[md.lord] * spans[order[(start_index + offset) % 9]] / 120.0
            assert ad.years == pytest.approx(expected, abs=1e-4), (md.lord, ad.lord)
        for previous, following in zip(md.antardashas, md.antardashas[1:]):
            assert previous.end_date == following.start_date
        assert md.antardashas[0].start_date == md.start_date
        assert md.antardashas[-1].end_date == md.end_date


# ---------------------------------------------------------------- Step 4：27 宿表


def test_the_twenty_seven_nakshatras_are_the_published_list_with_their_lords() -> None:
    """27 宿的名次与星主：名、星主、神祇三样都齐，星主按九曜循环推得。

    星主循环（Ashwini→Ketu、Bharani→Venus … Pushya→Saturn，再回卷）是 Jyotish 的公开定则，
    与 `DASHA_ORDER` 手抄同源，因此「表里的 lord」与「按位次算出的 lord」互为独立校验：
    宿表若被重排或插入，两边走不到一处。
    """
    assert len(NAKSHATRAS) == 27
    assert [n.name_en for n in NAKSHATRAS] == list(PUBLISHED_NAKSHATRAS)
    assert [n.index for n in NAKSHATRAS] == list(range(27))
    cycle = [name for name, _ in PUBLISHED_VIMSHOTTARI]
    for nak in NAKSHATRAS:
        assert nak.lord == cycle[nak.index % 9], nak.name_en
        assert nak.name_zh and nak.name_devanagari and nak.deity and nak.deity_zh
    # 三条常被引用的定则：Ashwini 属计都、Rohini 属太阴、Revati 属水星。
    assert NAKSHATRAS[0].lord == "Ketu"
    assert NAKSHATRAS[3].lord == "Moon"
    assert NAKSHATRAS[26].lord == "Mercury"
    assert len({n.name_en for n in NAKSHATRAS}) == 27
    assert len({n.name_zh for n in NAKSHATRAS}) == 27
    for lord in cycle:
        assert sum(1 for n in NAKSHATRAS if n.lord == lord) == 3


def test_the_nakshatras_divide_the_zodiac_into_exact_thirteen_twentieths() -> None:
    """每宿恰 13°20′：27 × 13°20′ = 360°，起点、跨度与边界落点全部确定。

    13°20′ = 40/3 在二进制浮点里除不尽，所以表里的 start_degree/span_degrees 是 4 位
    小数的**展示值**（13.3333），真正的分界算术用 `NAKSHATRA_SPAN`。0° 与 360° 两端：
    0° 是 Ashwini 第 1 足；360° 被 `_normalize_longitude` 折回 0°，故同为 Ashwini 第 1 足；
    末宿末足的地板是 356.667°，其上任意点（测里取 359.9999°）都归 Revati 第 4 足。
    """
    assert NAKSHATRA_SPAN == pytest.approx(40.0 / 3.0, abs=1e-12)
    assert 27 * NAKSHATRA_SPAN == pytest.approx(360.0, abs=1e-9)
    for nak in NAKSHATRAS:
        assert nak.span_degrees == pytest.approx(13.3333, abs=1e-4)  # 13°20'
        assert nak.start_degree == pytest.approx(nak.index * NAKSHATRA_SPAN, abs=1e-3)
    # 上面那条循环把 index 0 与 26 都遍历到了（`NAKSHATRAS[0].start_degree == 0.0` 是它的第 0 轮，
    # 原来单列一条属恒真，已删）。循环给不出的性质留在这里：末宿的**展示值**（4 位小数）
    # 起点加跨度仍正好回绕到 360°。循环里两个数各自容 1e-3，同向偏到位就能拼出 359.998° 的缝，
    # 这一条把「27 段拼满一整圈」的闭合式单独钉住。
    tail = NAKSHATRAS[-1]
    assert tail.start_degree + tail.span_degrees == pytest.approx(360.0, abs=1e-3)

    assert nakshatra_of(0.0).index == 0 and pada_of(0.0) == 1
    assert nakshatra_of(360.0).index == 0 and pada_of(360.0) == 1
    assert nakshatra_of(359.9999).index == 26 and pada_of(359.9999) == 4
    # 每个宿与足的分界：下沿归前一宿末足，上沿归本宿本足（1e-6° = 3.6″，远小于任何真实容差）。
    for index in range(27):
        below = index * NAKSHATRA_SPAN - 1e-6
        assert nakshatra_of(below).index == (index - 1) % 27, index
        assert pada_of(below) == 4, index
        for pada in range(4):
            boundary = index * NAKSHATRA_SPAN + pada * NAKSHATRA_SPAN / 4.0
            assert nakshatra_of(boundary + 1e-6).index == index, (index, pada)
            assert pada_of(boundary + 1e-6) == pada + 1, (index, pada)
            mid = boundary + NAKSHATRA_SPAN / 8.0
            assert nakshatra_of(mid).index == index and pada_of(mid) == pada + 1, (index, pada)


def test_exact_boundary_multiples_of_the_span_fall_one_mansion_early() -> None:
    """把浮点边界钉成现状：27 个起点里有 9 个「正好压在度数上」会退回前一宿末足。

    `nakshatra_of` 用 `int(lon // NAKSHATRA_SPAN)`，而 13°20′ 除不尽，于是
    `40.0 // 13.333333333333334 = 2.9999999999999996` → 判成第 3 宿（Krittika 末足）而不是
    第 4 宿 Rohini 初足。实测受影响的位次（2026-09-27 复现，与下面算出来的名单同）：
    `cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "from app.content.vedic
    import NAKSHATRA_SPAN as S, nakshatra_of as n; print([i for i in range(27) if
    n(i*S).index != i])"` → [3, 6, 9, 12, 15, 18, 19, 21, 24]。

    危害面很窄但非零：响应里的黄经 round 到 4 位小数，凡真值落在 40.0000/80.0000/… 的
    ±0.00005 内（约 0.18″）就会少报一宿、并给出上一宿的第 4 足。修法是整数算术
    （`int(lon * 27 // 360)`）或 Decimal，届时本测连同这段 docstring 一起重定，不是删掉。
    """
    affected = [index for index in range(27) if nakshatra_of(index * NAKSHATRA_SPAN).index != index]
    assert affected == [3, 6, 9, 12, 15, 18, 19, 21, 24]
    for shifted in affected:
        landed = nakshatra_of(shifted * NAKSHATRA_SPAN)
        assert landed.index == (shifted - 1) % 27, shifted
        assert pada_of(shifted * NAKSHATRA_SPAN) == 4, shifted
    # 整数域算法（`int(lon * 27 // 360)`，docstring 末提的那个修法）与 `nakshatra_of` 在同一个
    # 取值上分道扬镳：前者给 3（Rohini 初足，正确），后者给 2（Krittika 末足，现状）。原来这条
    # 写的是纯字面量算术（`int(40.0 * 27 // 360) == 3`），恒真、给虚假覆盖感，故换成函数断言：
    # 毛病出在除法取整，不在位次表。`nakshatra_of` 哪天真改用整数算术，这条转红，届时连同
    # docstring 一起重定（哨兵口径同 F-A1-9 那条星历对拍）。
    assert (nakshatra_of(40.0).index, int(40.0 * 27 // 360)) == (2, 3)


# ---------------------------------------------------------------- 端点（留在 golden 的两条）


def test_vedic_natal_endpoint(client: TestClient) -> None:
    response = client.post(
        "/api/v1/vedic/natal",
        json={
            "birth_date": "2000-01-01",
            "birth_time": "12:00",
            "latitude": LAT,
            "longitude": LON,
            "utc_offset_hours": 0,
            "target_date": "2026-09-25",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["zodiac"] == "sidereal"
    assert body["lagna_sign_zh"] == "白羊"
    assert len(body["planets"]) == 9
    assert body["vimshottari"]["total_years"] == 120
    assert body["engine"] == "pyswisseph"


def test_vedic_natal_requires_location(client: TestClient) -> None:
    response = client.post(
        "/api/v1/vedic/natal",
        json={"birth_date": "2000-01-01", "birth_time": "12:00"},
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_birth_data"
