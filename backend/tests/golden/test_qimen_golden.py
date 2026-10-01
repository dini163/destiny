"""Golden tests for the 奇门遁甲 (Qi Men Dun Jia) board engine.

锚点 A 是本系统的主参考盘 ``2024-05-15 10:30``（己巳时）。另加三盘，专挑参考盘压不到的路：
B ``2024-01-10 08:30``（小寒中元 阳遁八局，甲寅旬，手推值使与值符同宫）、
C ``2024-09-06 14:30``（处暑中元 **阴遁**四局，逆布逆退）、
D ``2024-12-22 12:30``（冬至下元 阳遁四局，旬首甲戌遁己落**中五** → 值符天禽、值使寄坤二取
死门，且时辰壬午在甲戌旬第九位 —— 与 A 的「甲子旬第六位」同为 1 基数法，旬首算第一）。

以下每一格断言都是**手推**所得（算式就地写在测试里），依据《烟波钓叟歌》起局歌诀 + 时家奇门
通行安盘：拆补法定局（节气定阴阳遁与局数组、日干支符头定上中下元）→ 阳顺阴逆布戊己庚辛壬癸
丁丙乙于洛书九宫 → 时辰旬首所遁六仪之地盘宫定值符星与值使门 → 值符随时干（甲用所遁仪，中五
寄坤二）→ 旬空取该旬轮空二支、驿马取时支三合局冲处。四柱里的**日干支**另用一条与 lunar-python
无关的儒略日算式复核（见 ``test_day_ganzhi_matches_an_independent_julian_day_formula``）。

**两项刻意不钉（两边都不钉）——见 findings F-A1-6：**
  * 值使门落宫：手推（沿八门地理环、中五计一宫）为 A 杜门 4→**9**、B 杜门 4→**6**、
    C 生门 8→**3**、D 死门 2→**1**；引擎为 1、7、2、2。
  * 天盘九星 / 人盘八门 / 神盘八神的逐宫位置：同一成因。

分歧只有一个来源——旋转所用的「环」。``app/content/qimen.py::RING8`` 是洛书数升序去中五
(1,2,3,4,6,7,8,9)，在 3×3 网格里这正是**飞盘**的九宫飞布轨迹（底中→右上→左…）；而**转盘**
是整盘刚体旋转，只能沿地理环 1北→8东北→3东→4东南→9南→2西南→7西→6西北 步移。本仓库自己的
本宫表就是地理环的排布（八门本宫 休1 生8 伤3 杜4 景9 死2 惊7 开6 恰为顺时针一周），故「整体
旋转」必须沿该环。``SCHOOL_NOTE`` 声明「排盘用转盘法（天盘/人盘整体旋转），非飞宫飞盘法」，
逐宫结果却按洛书数环位移；值使走宫又不计中五，使 D 的第八步 ``%8`` 归零、门回本宫，任何计入
中五的走法都落在坎一。

所以本文件只钉两类东西：(1) 与环无关、可独立复推的字段（定局、地盘、旬首、值符值使**名**、
值符落宫、旬空、驿马）；(2) 与环无关的逐宫**关系**（星与所携地盘干同行、天禽随天芮、值符神
在值符星落宫、值使门在值使落宫、中宫只带地盘干、旬空/驿马按宫内地支）。这些断言换任何一环
都仍然为真，因此没有把某一派的口径写死；反之，把它们改成绝对位置就会失去这个性质——这也是
为什么这里刻意不写逐宫门/星/神的宫号。
"""

from datetime import date, datetime
from typing import NamedTuple

import pytest
from fastapi.testclient import TestClient

from app.content.qimen_plain import door_key, god_key, star_key
from app.engines.plain_corpora import QIMEN
from app.engines.qimen import compute_qimen_chart

CAST = datetime(2024, 5, 15, 10, 30)

# 九星 / 八门 / 八神 的名目（手抄 classical 全表，用于「不重不漏」核对）。
NINE_STARS = {"天蓬", "天芮", "天冲", "天辅", "天禽", "天心", "天柱", "天任", "天英"}
EIGHT_DOORS = {"休门", "生门", "伤门", "杜门", "景门", "死门", "惊门", "开门"}
EIGHT_GODS = {"值符", "螣蛇", "太阴", "六合", "白虎", "玄武", "九地", "九天"}
# 九星洛书本宫（蓬1 芮2 冲3 辅4 禽5 心6 柱7 任8 英9）——「星携本宫地盘干」的手推依据。
STAR_HOME = {"天蓬": 1, "天芮": 2, "天冲": 3, "天辅": 4, "天禽": 5,
             "天心": 6, "天柱": 7, "天任": 8, "天英": 9}
GAN = "甲乙丙丁戊己庚辛壬癸"
ZHI = "子丑寅卯辰巳午未申酉戌亥"


class Anchor(NamedTuple):
    """One fully hand-derived 奇门 board. ``dipan`` is 宫 1..9；``*_palaces`` 为洛书宫号."""

    id: str
    cast: datetime
    pillars: tuple[str, str, str, str]      # 年 / 月 / 日 / 时
    jieqi: str
    yuan: str
    dun: str
    ju_number: int
    ju_name: str
    xunshou: str
    xunshou_yi: str
    zhifu_star: str
    zhishi_door: str
    zhifu_palace: int
    dipan: tuple[str, ...]                 # 戊己庚辛壬癸丁丙乙 布完后的 宫1→宫9
    kongwang: str
    yima: str
    kong_palaces: tuple[int, ...]
    yima_palaces: tuple[int, ...]

    @property
    def shi_gan(self) -> str:
        return self.pillars[3][0]


ANCHORS = (
    Anchor(
        id="A-立夏上元阳遁四局",
        cast=CAST,
        pillars=("甲辰", "己巳", "己卯", "己巳"),
        jieqi="立夏", yuan="上元", dun="阳遁", ju_number=4, ju_name="阳遁四局",
        xunshou="甲子", xunshou_yi="戊", zhifu_star="天辅", zhishi_door="杜门",
        zhifu_palace=2,
        dipan=("丁", "丙", "乙", "戊", "己", "庚", "辛", "壬", "癸"),
        kongwang="戌亥", yima="亥", kong_palaces=(6,), yima_palaces=(6,),
    ),
    Anchor(
        id="B-小寒中元阳遁八局",
        cast=datetime(2024, 1, 10, 8, 30),
        pillars=("癸卯", "乙丑", "癸酉", "丙辰"),
        jieqi="小寒", yuan="中元", dun="阳遁", ju_number=8, ju_name="阳遁八局",
        xunshou="甲寅", xunshou_yi="癸", zhifu_star="天辅", zhishi_door="杜门",
        zhifu_palace=6,
        dipan=("庚", "辛", "壬", "癸", "丁", "丙", "乙", "戊", "己"),
        kongwang="子丑", yima="寅", kong_palaces=(1, 8), yima_palaces=(8,),
    ),
    Anchor(
        id="C-处暑中元阴遁四局",
        cast=datetime(2024, 9, 6, 14, 30),
        pillars=("甲辰", "壬申", "癸酉", "己未"),
        jieqi="处暑", yuan="中元", dun="阴遁", ju_number=4, ju_name="阴遁四局",
        xunshou="甲寅", xunshou_yi="癸", zhifu_star="天任", zhishi_door="生门",
        zhifu_palace=3,
        dipan=("辛", "庚", "己", "戊", "乙", "丙", "丁", "癸", "壬"),
        kongwang="子丑", yima="巳", kong_palaces=(1, 8), yima_palaces=(4,),
    ),
    Anchor(
        id="D-冬至下元阳遁四局",
        cast=datetime(2024, 12, 22, 12, 30),
        pillars=("甲辰", "丙子", "庚申", "壬午"),
        jieqi="冬至", yuan="下元", dun="阳遁", ju_number=4, ju_name="阳遁四局",
        xunshou="甲戌", xunshou_yi="己", zhifu_star="天禽", zhishi_door="死门",
        zhifu_palace=8,
        dipan=("丁", "丙", "乙", "戊", "己", "庚", "辛", "壬", "癸"),
        kongwang="申酉", yima="申", kong_palaces=(2, 7), yima_palaces=(2,),
    ),
)

# 洛书宫所藏地支（坎子、艮丑寅、震卯、巽辰巳、中无、离午、坤未申、兑酉、乾戌亥）——
# 旬空宫 / 驿马宫 由它定。
PALACE_ZHI = {1: "子", 2: "未申", 3: "卯", 4: "辰巳", 5: "", 6: "戌亥", 7: "酉", 8: "丑寅", 9: "午"}


def _chart(cast: datetime = CAST):
    return compute_qimen_chart(cast_time=cast, question=None)


def _anchor(letter: str) -> Anchor:
    """按 id 前缀取锚。跨锚对照的测不许按位置取 —— ``ANCHORS`` 重排会让那条测静默换含义，
    而它的 docstring 讲的还是「A 与 D」。"""
    return next(anchor for anchor in ANCHORS if anchor.id.startswith(f"{letter}-"))


def _day_ganzhi_by_julian_day(d: date) -> str:
    """日干支，只依赖儒略日：干支序 = (JDN + 49) mod 60，0 = 甲子。

    与 lunar-python 完全无关的第二条路子，用来证明本文件的日柱不是「引擎说什么就抄什么」。
    """
    a = (14 - d.month) // 12
    y = d.year + 4800 - a
    m = d.month + 12 * a - 3
    jdn = d.day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045
    n = (jdn + 49) % 60
    return GAN[n % 10] + ZHI[n % 12]


@pytest.mark.parametrize("anchor", ANCHORS, ids=[a.id for a in ANCHORS])
def test_four_pillars(anchor: Anchor) -> None:
    """四柱逐柱钉住。年柱以**立春**为界，故 B（2024-01-10）仍是癸卯年而非甲辰。"""
    chart = _chart(anchor.cast)
    assert (chart.year_ganzhi, chart.month_ganzhi, chart.day_ganzhi, chart.time_ganzhi) \
        == anchor.pillars


@pytest.mark.parametrize("anchor", ANCHORS, ids=[a.id for a in ANCHORS])
def test_day_ganzhi_matches_an_independent_julian_day_formula(anchor: Anchor) -> None:
    """日柱用另一条算式（儒略日）复核；四锚均不在子时，无晚子换日歧义。"""
    assert _chart(anchor.cast).day_ganzhi == _day_ganzhi_by_julian_day(anchor.cast.date())
    assert anchor.pillars[2] == _day_ganzhi_by_julian_day(anchor.cast.date())


@pytest.mark.parametrize("anchor", ANCHORS, ids=[a.id for a in ANCHORS])
def test_ding_ju(anchor: Anchor) -> None:
    """拆补法定局：节气定阴阳遁与「上中下元」局数组，日干支符头（往前数到最近的甲/己日）
    的地支定元——子午卯酉上元、寅申巳亥中元、辰戌丑未下元。

    A 日己卯自坐符头，卯→上元，立夏「四一七」→ 阳遁四局。
    B、C 日同为癸酉（甲子旬第九位），符头己巳，巳→中元：小寒「二八五」→ 八局，
       处暑（阴遁）「一四七」→ 四局 —— 同一日柱因节气不同而异局，正压住「节气 + 符头」两把输入。
    D 日庚申（甲寅旬末），符头己未，未→下元，冬至「一七四」→ 阳遁四局。
    """
    chart = _chart(anchor.cast)
    assert chart.jieqi == anchor.jieqi
    assert chart.yuan == anchor.yuan
    assert chart.dun == anchor.dun
    assert chart.ju_number == anchor.ju_number
    assert chart.ju_name == anchor.ju_name


@pytest.mark.parametrize("anchor", ANCHORS, ids=[a.id for a in ANCHORS])
def test_zhifu_zhishi_and_xunshou(anchor: Anchor) -> None:
    """时辰旬首遁六仪（甲子戊 甲戌己 甲申庚 甲午辛 甲辰壬 甲寅癸），该仪地盘宫定二使。

    A 己巳在甲子旬→遁戊，戊在四宫→值符天辅、值使杜门；D 壬午在甲戌旬→遁己，己在五宫→
    值符天禽，中五无门故值使寄坤二取死门。旬空为该旬轮空二支，驿马取时支三合局冲处
    （A 巳→亥，B/D 申→寅 / 午→申，C 未→巳）。
    """
    chart = _chart(anchor.cast)
    assert chart.xunshou == anchor.xunshou
    assert chart.xunshou_yi == anchor.xunshou_yi
    assert chart.zhifu_star == anchor.zhifu_star
    assert chart.zhishi_door == anchor.zhishi_door
    assert chart.kongwang == anchor.kongwang
    assert chart.yima == anchor.yima


@pytest.mark.parametrize("anchor", ANCHORS, ids=[a.id for a in ANCHORS])
def test_dipan_matches_the_hand_laid_plate(anchor: Anchor) -> None:
    """逐宫对拍地盘：戊起局数宫，阳遁顺洛书数、阴遁逆行，六仪（戊己庚辛壬癸）毕而布三奇（丁丙乙）。

    A/D 阳遁四局 4戊5己6庚7辛8壬9癸1丁2丙3乙；B 阳遁八局 8戊9己1庚2辛3壬4癸5丁6丙7乙；
    C 阴遁四局逆行 4戊3己2庚1辛9壬8癸7丁6丙5乙。
    """
    chart = _chart(anchor.cast)
    by_number = {p.number: p.dipan_gan for p in chart.palaces}
    assert [by_number[n] for n in range(1, 10)] == list(anchor.dipan)


def test_dipan_is_a_function_of_the_ju_number_only() -> None:
    """A 与 D 同为阳遁四局（节气不同、时辰不同），地盘必须逐宫相同——盘不因时辰而移。"""
    first = {p.number: p.dipan_gan for p in _chart(_anchor("A").cast).palaces}
    last = {p.number: p.dipan_gan for p in _chart(_anchor("D").cast).palaces}
    assert first == last
    assert first[4] == "戊" and first[5] == "己"


@pytest.mark.parametrize("anchor", ANCHORS, ids=[a.id for a in ANCHORS])
def test_zhifu_palace_is_the_time_gan_dipan_palace(anchor: Anchor) -> None:
    """值符随时干：时干落地盘之宫即值符星落宫；落中五则寄坤二（A 时干己正压此路）。"""
    chart = _chart(anchor.cast)
    palace_of_shi_gan = anchor.dipan.index(anchor.shi_gan) + 1
    expected = 2 if palace_of_shi_gan == 5 else palace_of_shi_gan
    assert chart.zhifu_palace == expected == anchor.zhifu_palace


@pytest.mark.parametrize("anchor", ANCHORS, ids=[a.id for a in ANCHORS])
def test_kongwang_and_yima_land_on_the_palaces_holding_those_branches(anchor: Anchor) -> None:
    """旬空宫 / 驿马宫由宫内地支决定：中宫无支故永不空、永不马。"""
    chart = _chart(anchor.cast)
    kong = set(anchor.kongwang)
    expected_kong = sorted(n for n, zs in PALACE_ZHI.items() if any(z in kong for z in zs))
    expected_ma = sorted(n for n, zs in PALACE_ZHI.items() if anchor.yima in zs)
    assert sorted(p.number for p in chart.palaces if p.kong) == expected_kong
    assert expected_kong == list(anchor.kong_palaces)
    assert sorted(p.number for p in chart.palaces if p.ma) == expected_ma
    assert expected_ma == list(anchor.yima_palaces)


@pytest.mark.parametrize("anchor", ANCHORS, ids=[a.id for a in ANCHORS])
def test_zhifu_star_and_zhifu_god_stand_in_the_same_palace(anchor: Anchor) -> None:
    """值符神随值符星落宫（与用哪一环无关）；且全盘只有一颗星、只有一宫被标为值符宫。"""
    chart = _chart(anchor.cast)
    landing = next(p for p in chart.palaces if p.number == chart.zhifu_palace)
    assert chart.zhifu_star in [s.name for s in landing.stars]
    assert landing.god is not None and landing.god.name == "值符"
    assert landing.is_zhifu_palace
    assert sum(1 for p in chart.palaces if p.is_zhifu_palace) == 1
    assert [p.number for p in chart.palaces for s in p.stars if s.is_zhifu] == [chart.zhifu_palace]


@pytest.mark.parametrize("anchor", ANCHORS, ids=[a.id for a in ANCHORS])
def test_zhishi_door_stands_in_the_palace_the_chart_reports(anchor: Anchor) -> None:
    """值使落宫之「宫」不钉（见模块 docstring），但盘面与声明必须自洽：声明之宫里就是该门，
    且中五无门、八门不重不漏。"""
    chart = _chart(anchor.cast)
    assert chart.zhishi_palace != 5
    landing = next(p for p in chart.palaces if p.number == chart.zhishi_palace)
    assert landing.door is not None and landing.door.name == chart.zhishi_door
    assert landing.is_zhishi_palace
    assert sum(1 for p in chart.palaces if p.is_zhishi_palace) == 1
    assert [p.number for p in chart.palaces if p.door and p.door.is_zhishi] == [chart.zhishi_palace]


@pytest.mark.parametrize("anchor", ANCHORS, ids=[a.id for a in ANCHORS])
def test_every_star_carries_its_home_palace_dipan_gan(anchor: Anchor) -> None:
    """天盘随时干：每宫所临之星必带上其本宫的地盘干（天禽带中宫干）。

    这是环无关的星—干同行关系：换成任何一环都成立，但星盘与干盘若各用各的偏移就会红。
    """
    chart = _chart(anchor.cast)
    dipan = {p.number: p.dipan_gan for p in chart.palaces}
    for palace in chart.palaces:
        if palace.is_center:
            continue
        assert len(palace.stars) == len(palace.tianpan_gan) >= 1
        for star, gan in zip(palace.stars, palace.tianpan_gan, strict=True):
            assert gan == dipan[STAR_HOME[star.name]], (palace.number, star.name)


@pytest.mark.parametrize("anchor", ANCHORS, ids=[a.id for a in ANCHORS])
def test_tianqin_rides_on_tianrui_with_the_center_gan(anchor: Anchor) -> None:
    """中五之禽寄坤二：天禽与天芮恒同宫，该宫因此带两枚天盘干——坤二之本宫干 + 中宫之地盘干。"""
    chart = _chart(anchor.cast)
    hosts = [p for p in chart.palaces if any(s.name == "天禽" for s in p.stars)]
    assert len(hosts) == 1
    host = hosts[0]
    assert [s.name for s in host.stars] == ["天芮", "天禽"]
    assert not host.is_center
    dipan = {p.number: p.dipan_gan for p in chart.palaces}
    assert host.tianpan_gan == [dipan[2], dipan[5]]


def test_nine_palaces_center_empty_others_populated() -> None:
    chart = _chart()
    assert len(chart.palaces) == 9
    assert sorted(p.number for p in chart.palaces) == list(range(1, 10))
    centers = [p for p in chart.palaces if p.is_center]
    assert len(centers) == 1 and centers[0].number == 5
    center = centers[0]
    assert center.door is None and center.god is None and center.stars == []
    assert center.dipan_gan == "己"          # 阳遁四局：戊四顺行第五宫
    assert center.tianpan_gan == []
    assert center.zhi == "" and not center.kong and not center.ma
    for palace in chart.palaces:
        if not palace.is_center:
            assert palace.door is not None
            assert palace.god is not None
            assert len(palace.stars) >= 1


def test_all_stars_doors_gods_laid_exactly_once() -> None:
    """三盘各不重不漏：九星 9 枚（一宫双星者唯坤二之禽芮）、八门 8 枚、八神 8 枚，中宫无门神。"""
    chart = _chart()
    stars = [s.name for p in chart.palaces for s in p.stars]
    doors = [p.door.name for p in chart.palaces if p.door]
    gods = [p.god.name for p in chart.palaces if p.god]
    assert set(stars) == NINE_STARS
    assert len(stars) == len(set(stars)) == 9
    assert sum(1 for p in chart.palaces if len(p.stars) == 2) == 1
    assert set(doors) == EIGHT_DOORS and len(doors) == 8
    assert set(gods) == EIGHT_GODS and len(gods) == 8
    # 八门与八神各占八方：每个非中宫恰一门、恰一神。
    assert all(p.door is not None for p in chart.palaces if not p.is_center)
    assert len({p.door.name for p in chart.palaces if p.door}) == 8
    assert len({p.god.name for p in chart.palaces if p.god}) == 8


def test_zhifu_zhishi_palace_flags_are_unique() -> None:
    chart = _chart()
    assert sum(1 for p in chart.palaces if p.is_zhifu_palace) == 1
    assert sum(1 for p in chart.palaces if p.is_zhishi_palace) == 1
    assert chart.zhifu_palace in PALACE_ZHI and chart.zhishi_palace in PALACE_ZHI
    assert chart.zhifu_palace != 5 and chart.zhishi_palace != 5


def test_zhishi_landing_stays_unpinned_until_the_ring_ruling_lands() -> None:
    """值使门落宫（以及逐宫星/门/神）**刻意不钉值**——findings F-A1-6。

    手推杜门（本宫四）顺行五个时辰（己巳在甲子旬第六位，旬首甲子数起 n=5）：沿洛书数序且
    中五计一宫 → 离九；沿八宫环（去中五）→ 坎一。引擎取后者（`content/qimen.py:55` 的
    ``RING8`` 是洛书数升序去中五，`engines/qimen.py:136` 依它走宫），故本盘两派候选为 {9, 1}
    而确实不同宫；钉任何一边都是替口径裁定做主。这里只钉「落在两派候选之内」，盘面自洽由
    :func:`test_zhishi_door_stands_in_the_palace_the_chart_reports` 管；值符落宫一侧两派一致
    （时干己落中五 → 寄坤二），故钉死。
    """
    chart = _chart()
    assert chart.zhishi_palace in {1, 9}
    assert chart.zhishi_door == "杜门"
    assert chart.zhifu_palace == 2


def test_qimen_endpoint(client: TestClient) -> None:
    response = client.post("/api/v1/qimen/chart", json={"cast_time": "2024-05-15T10:30:00"})
    assert response.status_code == 200
    body = response.json()
    assert body["ju_name"] == "阳遁四局"
    assert body["zhifu_star"] == "天辅"
    assert body["zhifu_palace"] == 2
    assert body["kongwang"] == "戌亥"
    assert len(body["palaces"]) == 9
    assert body["engine"] == "qimen-luoshu-rotating"


def test_qimen_endpoint_defaults_cast_time_to_now(client: TestClient) -> None:
    response = client.post("/api/v1/qimen/chart", json={})
    assert response.status_code == 200
    body = response.json()
    assert len(body["palaces"]) == 9
    assert body["ju_number"] in range(1, 10)
    assert body["dun"] in {"阳遁", "阴遁"}


# ------------------------------------------------- 白话转述（多系统白话 spec §8 丙组 · 奇门行）


@pytest.mark.parametrize("anchor", ANCHORS, ids=[a.id for a in ANCHORS])
def test_the_center_palace_is_the_opener_alone(anchor: Anchor) -> None:
    """中五宫不坐星不配门不配神（`engines/qimen.py:152-163` 的支路），段里就只有开篇句。

    `:302-317` 已钉中宫的 `stars/door/god` 皆空；这里钉的是**那一格的白话只剩一句**，
    是同一个事实的另一半（`compose()` 的 `items=[]` 分支）。有人给中宫塞了条目即红。
    """
    center = next(p for p in _chart(anchor.cast).palaces if p.number == 5)
    assert center.plain == QIMEN.openers["中"]
    assert len(center.plain.split("\n")) == 1


@pytest.mark.parametrize("anchor", ANCHORS, ids=[a.id for a in ANCHORS])
def test_each_palace_line_count_equals_one_opener_plus_its_own_seats(anchor: Anchor) -> None:
    """G27 的奇门版等式：行数 == 1 + 星数 + 有无门 + 有无神。

    spec §11 原写「段内行数 ≥3」，中宫只有 1 行（偏差表第 4 行），等式才两头都成立。
    """
    for palace in _chart(anchor.cast).palaces:
        lines = palace.plain.split("\n")
        seats = len(palace.stars) + (1 if palace.door else 0) + (1 if palace.god else 0)
        assert len(lines) == 1 + seats, (palace.number, palace.gua, len(lines), seats)
        assert lines[0] == QIMEN.openers[palace.gua], palace.gua


@pytest.mark.parametrize("anchor", ANCHORS, ids=[a.id for a in ANCHORS])
def test_the_board_prints_nine_openers_nine_stars_eight_doors_eight_gods(anchor: Anchor) -> None:
    """整盘等式 9 + 9 + 8 + 8 = 34 行：开篇句九句、九星九枚（天禽随天芮那一枚亦落段）、
    八门八位、八神八位。`:320-334` 钉的是三盘各不重不漏，本条钉的是段里真的各落一行——
    白话侧新增的丢句只有这一条兜得住，所以四张锚盘各跑一遍而不是只跑 A。
    """
    assert sum(len(p.plain.split("\n")) for p in _chart(anchor.cast).palaces) == 34


@pytest.mark.parametrize("anchor", ANCHORS, ids=[a.id for a in ANCHORS])
def test_each_palace_says_only_the_stars_door_and_god_seated_there(anchor: Anchor) -> None:
    """反向对账：段里出现的条目键，必须真是这一宫的星/门/神（借宫、漏装都在此红）。"""
    for palace in _chart(anchor.cast).palaces:
        expected = {star_key(star.name) for star in palace.stars}
        if palace.door:
            expected.add(door_key(palace.door.name))
        if palace.god:
            expected.add(god_key(palace.god.name))
        printed = {key for key, text in QIMEN.entries.items() if text in palace.plain.split("\n")}
        assert printed == expected, (palace.number, printed ^ expected)


@pytest.mark.parametrize("anchor", ANCHORS, ids=[a.id for a in ANCHORS])
def test_palace_lines_follow_the_gua_opener_then_star_door_god(anchor: Anchor) -> None:
    """`keep` 的两条次序（G21）：宫与宫按装配序 1→9（`:305` 钉的是集合，这里钉的是**次序**），
    段内按读盘序「星→门→神」。段内每一行的对账都环无关——它拿的是这一宫自己报出的
    星/门/神，不预设它们该落哪一宫（F-A1-6 的留白一寸没踩）。

    寄坤二那一宫带两枚星（`:290-299` 钉的 `[天芮, 天禽]`），所以段内星区间的长度随宫而变，
    定死的 `-3` 偏移会把那一格写成「最后一枚星 = 第一枚星」而当场红；这里逐枚对账整段，
    单子星的八宫照旧被钉住，双星那一格多钉的一行是白送的力量。
    """
    chart = _chart(anchor.cast)
    assert [p.number for p in chart.palaces] == [1, 2, 3, 4, 5, 6, 7, 8, 9]
    for palace in chart.palaces:
        if palace.door is None or palace.god is None or not palace.stars:
            continue
        lines = palace.plain.split("\n")
        assert lines[1:-2] == [QIMEN.entries[star_key(star.name)] for star in palace.stars]
        assert lines[-2] == QIMEN.entries[door_key(palace.door.name)]
        assert lines[-1] == QIMEN.entries[god_key(palace.god.name)]
