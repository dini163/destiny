"""Golden tests for the 紫微斗数 (Zi Wei Dou Shu) chart engine.

Reference birth: 2000-08-16 12:00 (solar), Beijing longitude, male, True Solar Time off.
The chart is fully deterministic from the 农历 data, and every value below is walked from
the classical 安星 tables and independently checkable: 庚辰年七月十七午时 puts 命宫在寅
(寅起正月顺数至七月得申，再从申起子时逆数至午时得寅); 五虎遁 庚年正月起戊寅 → 命宫戊寅
(纳音城头土); 庚干四化 = 太阳禄 / 武曲权 / 太阴科 / 天同忌; 庚(阳干)+男 → 阳男大限顺行,
起运虚岁 = 局数.
"""

from datetime import date, time

import pytest
from fastapi.testclient import TestClient

from app.content.ziwei import MAJOR_STARS, MINOR_STARS
from app.engines.ziwei import compute_ziwei_chart
from app.schemas.common import CalendarType, Gender

BIRTH = date(2000, 8, 16)
BTIME = time(12, 0)

# 第二张锚盘：2006-09-02 12:00（丙戌年**闰**七月初十午时，男）。
# 挑它是因为它同时压着三条参考盘压不到的路：闰月取同号、借数为偶数时紫微**进**宫、
# 以及一个不同的五行局（木三局）。
LEAP_BIRTH = date(2006, 9, 2)


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


# ============================================================================
# 手推锚（Task 5 · 轴 1 功能准确性）
#
# 下面每一份常量的值都是照《紫微斗数全书》的安星诀**手推**出来的，推演链抄在
# 用到它的那条 docstring 里；值不是从引擎输出回填的（引擎只该是这张手推表的执行者）。
# 首盘：2000-08-16 12:00 男，庚辰年七月十七午时。
# ============================================================================

#: 十四主星落宫。紫微 17÷5 商 3 余 2 → 自寅第 3 宫辰进一宫巳、借数 5-2=3 奇 → 退三宫 = 寅；
#: 天府按寅申轴镜像同在寅；紫微系自紫微逆行、天府系自天府顺行。
MAJOR_STAR_ZHI: dict[str, str] = {
    "紫微": "寅", "天机": "丑", "太阳": "亥", "武曲": "戌", "天同": "酉", "廉贞": "午",
    "天府": "寅", "太阴": "卯", "贪狼": "辰", "巨门": "巳", "天相": "午", "天梁": "未",
    "七杀": "申", "破军": "子",
}

#: 十四颗乙级星落宫（辅弼逐生月、昌曲空劫逐生时、魁钺禄存逐年干、羊陀随禄存、
#: 马火铃逐年支三合局）。
MINOR_STAR_ZHI: dict[str, str] = {
    "左辅": "戌", "右弼": "辰", "文昌": "辰", "文曲": "戌", "天魁": "丑", "天钺": "未",
    "禄存": "申", "擎羊": "酉", "陀罗": "未", "天马": "寅", "火星": "申", "铃星": "辰",
    "地空": "巳", "地劫": "巳",
}

#: 十二宫 → (宫干支, 宫名, 大限)。宫名自命宫逆布、宫干自五虎遁顺布、大限阳男顺行。
PALACE_ANCHORS: dict[str, tuple[str, str, str]] = {
    "寅": ("戊寅", "命宫", "5-14"),
    "卯": ("己卯", "父母", "15-24"),
    "辰": ("庚辰", "福德", "25-34"),
    "巳": ("辛巳", "田宅", "35-44"),
    "午": ("壬午", "官禄", "45-54"),
    "未": ("癸未", "仆役", "55-64"),
    "申": ("甲申", "迁移", "65-74"),
    "酉": ("乙酉", "疾厄", "75-84"),
    "戌": ("丙戌", "财帛", "85-94"),
    "亥": ("丁亥", "子女", "95-104"),
    "子": ("戊子", "夫妻", "105-114"),
    "丑": ("己丑", "兄弟", "115-124"),
}

#: 庚干四化 → (化名, 落宫地支, 落宫宫名)。
SIHUA_ANCHORS: dict[str, tuple[str, str, str]] = {
    "太阳": ("化禄", "亥", "子女"),
    "武曲": ("化权", "戌", "财帛"),
    "太阴": ("化科", "卯", "父母"),
    "天同": ("化忌", "酉", "疾厄"),
}


def _seated(chart, only_major: bool) -> dict[str, str]:
    """星名 → 所落地支宫。"""
    return {
        star.name: palace.zhi
        for palace in chart.palaces
        for star in palace.stars
        if (star.kind == "主星") == only_major
    }


def test_fourteen_major_stars_land_on_the_hand_derived_branches() -> None:
    """紫微系逆行、天府系顺行，十四颗一颗都不能挪。

    紫微：17 ÷ 5 = 商 3 余 2；有余则自寅起第 3 宫（辰）再进一宫（巳），借数 = 5 - 2 = 3，
    奇数退三宫 → 紫微在寅。天府与紫微关于寅申轴对称（对照表「紫微在寅 → 天府在寅」）。
    紫微系自寅退：天机 1 宫 = 丑、太阳 3 宫 = 亥、武曲 4 宫 = 戌、天同 5 宫 = 酉、
    廉贞 8 宫 = 午。天府系自寅进：太阴 1 = 卯、贪狼 2 = 辰、巨门 3 = 巳、天相 4 = 午、
    天梁 5 = 未、七杀 6 = 申、破军 10 = 子。
    """
    chart = _chart()
    assert chart.ziwei_zhi == "寅" and chart.tianfu_zhi == "寅"
    assert _seated(chart, only_major=True) == MAJOR_STAR_ZHI


def test_yi_level_stars_land_on_the_hand_derived_branches() -> None:
    """乙级十四颗各按自己的诀，逐颗推演（生月七月、生时午、年干庚、年支辰）：

    左辅 辰起正月顺数至七月 = 戌；右弼 戌起正月逆数至七月 = 辰；
    文昌 戌起子时逆数至午 = 辰；文曲 辰起子时顺数至午 = 戌；
    天魁/天钺 庚干贵人歌「甲戊庚牛羊」→ 丑 / 未；
    禄存 庚禄在申；擎羊居禄存前一宫 = 酉、陀罗居后一宫 = 未（羊陀夹禄）；
    天马 年支辰属申子辰局 → 马在寅；火星 申子辰起寅顺数至午 = 申；
    铃星 寅午戌起卯、余皆戌 → 辰人起戌顺数至午 = 辰；
    地劫 亥起子时顺数至午 = 巳；地空 亥起子时逆数至午 = 巳。
    """
    chart = _chart()
    assert _seated(chart, only_major=False) == MINOR_STAR_ZHI


def test_palace_names_ganzhi_and_dayun_walk_out_from_the_ming_palace() -> None:
    """十二宫的三件事同时钉住：宫名逆布、宫干五虎遁、大限顺行十年一宫。

    命宫在寅 → 宫名自寅**逆布**：丑兄弟、子夫妻、亥子女、戌财帛、酉疾厄、申迁移、
    未仆役、午官禄、巳田宅、辰福德、卯父母；迁移恒在命宫对宫（寅 ↔ 申）。
    五虎遁「乙庚之岁戊为头」→ 寅宫戊，逐宫顺推：戊寅 己卯 庚辰 辛巳 壬午 癸未
    甲申 乙酉 丙戌 丁亥 戊子 己丑。
    庚为阳干、男命 → 阳男顺行，起运虚岁 = 局数 5 → 寅 5-14、卯 15-24 …… 丑 115-124。
    """
    chart = _chart()
    by_zhi = {palace.zhi: palace for palace in chart.palaces}
    assert set(by_zhi) == set(PALACE_ANCHORS)
    for zhi, (ganzhi, name, dayun) in PALACE_ANCHORS.items():
        palace = by_zhi[zhi]
        assert (palace.ganzhi, palace.name, palace.dayun) == (ganzhi, name, dayun)
    assert by_zhi["寅"].is_ming and not by_zhi["申"].is_ming


def test_sihua_marks_exactly_four_stars_with_label_and_palace() -> None:
    """庚干诀「庚阳武阴同」→ 太阳化禄落亥宫（子女）、武曲化权落戌宫（财帛）、
    太阴化科落卯宫（父母）、天同化忌落酉宫（疾厄）；全盘带化的星只能有这四颗。
    """
    chart = _chart()
    marked = {
        star.name: (star.sihua, palace.zhi, palace.name)
        for palace in chart.palaces
        for star in palace.stars
        if star.sihua
    }
    assert marked == SIHUA_ANCHORS


def test_shen_gong_of_a_wu_hour_sits_in_the_ming_palace() -> None:
    """身宫诀：寅起正月顺数至七月得申，自申起子时**顺**数至午时 → 寅。

    与命宫同支（身命同宫），故 `shen_gong_name` 必须写成它落的宫名「命宫」，
    且全盘只有一宫标 `is_shen`。
    """
    chart = _chart()
    shen = [palace for palace in chart.palaces if palace.is_shen]
    assert len(shen) == 1
    assert shen[0].zhi == "寅" and shen[0].name == "命宫"
    assert chart.shen_gong_zhi == "寅" and chart.shen_gong_name == "命宫"


#: 同一生日的女命十二宫大限：庚为阳干、女命 → 阴女逆行（「阳男阴女顺行、阴男阳女逆行」）。
#: 逆行即自命宫沿**宫名次序**推进（命→兄弟→夫妻→子女…），起运虚岁仍是局数 5：
#: 寅命宫 5-14、丑兄弟 15-24、子夫妻 25-34、亥子女 35-44、戌财帛 45-54、酉疾厄 55-64、
#: 申迁移 65-74、未仆役 75-84、午官禄 85-94、巳田宅 95-104、辰福德 105-114、卯父母 115-124。
FEMALE_DAYUN_ANCHORS: dict[str, tuple[str, str]] = {
    "寅": ("命宫", "5-14"),
    "丑": ("兄弟", "15-24"),
    "子": ("夫妻", "25-34"),
    "亥": ("子女", "35-44"),
    "戌": ("财帛", "45-54"),
    "酉": ("疾厄", "55-64"),
    "申": ("迁移", "65-74"),
    "未": ("仆役", "75-84"),
    "午": ("官禄", "85-94"),
    "巳": ("田宅", "95-104"),
    "辰": ("福德", "105-114"),
    "卯": ("父母", "115-124"),
}


def test_a_female_chart_runs_the_dayun_counterwise_through_the_palace_order() -> None:
    """性别只翻大限方向，不翻星位：同一生日的女命十二宫大限逐宫手推。

    方向由「阳男阴女顺行、阴男阳女逆行」定：庚为阳干，故男顺女逆。
    逆行走的是宫名次序（命→兄弟→夫妻→…），即地支**递减**，与上面 `PALACE_ANCHORS`
    的顺行（地支递增）互为镜像；两版的起运虚岁都还是局数 5。
    """
    chart = _chart(gender=Gender.FEMALE)
    assert chart.dayun_direction == "逆行" and chart.dayun_start_age == 5
    by_zhi = {palace.zhi: palace for palace in chart.palaces}
    for zhi, (name, dayun) in FEMALE_DAYUN_ANCHORS.items():
        palace = by_zhi[zhi]
        assert (palace.name, palace.dayun) == (name, dayun)
    # 星位与性别无关：换个性别，十四颗主星该一颗都不动。
    assert _seated(chart, only_major=True) == MAJOR_STAR_ZHI


def test_lunar_date_string_reads_the_hand_derived_lunar_fact() -> None:
    """2000-08-16 = 庚辰年七月十七，且 2000 年**没有**闰七月（该闰月落在 2006 年）→
    中文串既不带「闰」字也不带「初」以外的装饰：「庚辰年七月十七」。
    """
    assert _chart().lunar_date == "庚辰年七月十七"


def test_ming_zhu_stays_unpinned_until_the_school_ruling_lands() -> None:
    """命主有两版歌诀，本盘两版给出不同星，故**刻意不钉值**（findings F-A1-4）。

    逐年支：庚辰 → 辰 → 廉贞；逐命宫支：命宫寅 → 禄存。表体（十二支 → 星）本身
    两版一致，见 `tests/content/test_ziwei_corpus.py`；分歧只在**取哪一支**，
    而引擎 `app/engines/ziwei.py:208` 取年支、`ZIWEI_SOURCE` 未声明此口径。
    钉任何一版都是替裁定做主，这里只钉「它是斗数星名之一，且落在两版候选之内」。
    """
    chart = _chart()
    assert chart.ming_zhu in set(MAJOR_STARS) | set(MINOR_STARS)
    assert chart.ming_zhu in {"廉贞", "禄存"}  # 年支版 / 命宫支版
    # 两版候选在本盘确实不同星不同宫（廉贞在午·官禄、禄存在申·迁移），换口径等于换宫：
    assert MAJOR_STAR_ZHI["廉贞"] == "午" and MINOR_STAR_ZHI["禄存"] == "申"


# ------------------------------------------------------- 第二张锚盘（闰月 + 偶借数）

#: 闰七月初十午时盘的十四主星：紫微在未（借数 2 偶 → 进）、天府在酉。
LEAP_MAJOR_STAR_ZHI: dict[str, str] = {
    "紫微": "未", "天机": "午", "太阳": "辰", "武曲": "卯", "天同": "寅", "廉贞": "亥",
    "天府": "酉", "太阴": "戌", "贪狼": "亥", "巨门": "子", "天相": "丑", "天梁": "寅",
    "七杀": "卯", "破军": "未",
}

#: 该盘十二宫 → (宫干支, 宫名, 大限)；丙年五虎遁起庚寅，木三局起运 3。
LEAP_PALACE_ANCHORS: dict[str, tuple[str, str, str]] = {
    "寅": ("庚寅", "命宫", "3-12"),
    "卯": ("辛卯", "父母", "13-22"),
    "辰": ("壬辰", "福德", "23-32"),
    "巳": ("癸巳", "田宅", "33-42"),
    "午": ("甲午", "官禄", "43-52"),
    "未": ("乙未", "仆役", "53-62"),
    "申": ("丙申", "迁移", "63-72"),
    "酉": ("丁酉", "疾厄", "73-82"),
    "戌": ("戊戌", "财帛", "83-92"),
    "亥": ("己亥", "子女", "93-102"),
    "子": ("庚子", "夫妻", "103-112"),
    "丑": ("辛丑", "兄弟", "113-122"),
}


def _leap_chart(gender: Gender = Gender.MALE):
    return compute_ziwei_chart(
        birth_date=LEAP_BIRTH,
        birth_time=BTIME,
        calendar=CalendarType.SOLAR,
        longitude=116.4074,
        gender=gender,
        apply_true_solar_time=False,
        name=None,
    )


def test_leap_month_chart_walks_the_even_borrow_and_a_different_ju() -> None:
    """2006-09-02 12:00 男 = 丙戌年闰七月初十午时，四件事一起复推：

    1. 闰月取同号（`provenance.school_note` 已声明的口径）→ 生月仍按 7 月起星，
       而 `lunar_leap` 独立为 True。
    2. 命宫：寅起顺数至 7 = 申，申起子时逆数至午 = 寅；身宫顺数亦在寅。
       五虎遁「丙辛必定寻庚起」→ 命宫庚寅；纳音「庚寅辛卯松柏木」→ 木 → 木三局，
       起运虚岁 3。丙阳干 + 男 → 顺行。
    3. 安紫微：10 ÷ 3 = 商 3 余 1 → 自寅第 3 宫辰、进一宫巳，借数 = 3 - 1 = 2，
       **偶数 → 进二宫** → 紫微在未（对照表「紫微在未 → 天府在酉」）。
       紫微系自未退：天机午、太阳辰、武曲卯、天同寅、廉贞亥；
       天府系自酉进：太阴戌、贪狼亥、巨门子、天相丑、天梁寅、七杀卯、破军未。
       （未宫紫微+破军、亥宫廉贞+贪狼、寅宫天同+天梁 —— 都是手册的双星同宫格。）
    4. 丙干四化诀「丙同机昌廉」→ 天同禄、天机权、文昌科、廉贞忌。
    """
    chart = _leap_chart()
    assert (chart.lunar_year_ganzhi, chart.lunar_month, chart.lunar_day) == ("丙戌", 7, 10)
    assert chart.lunar_leap is True
    # 页面直接印这一串（`ZiweiChart.lunar_date`），故逐字钉：`getMonthInChinese()` 对闰月
    # **自带**「闰」字（同 `app/schemas/bazi_liuri.py:64` 的声明），串里只能有一个「闰」。
    assert chart.lunar_date == "丙戌年闰七月初十"
    assert chart.time_zhi == "午"
    assert (chart.ming_gong_zhi, chart.ming_gong_ganzhi, chart.ming_gong_nayin) == (
        "寅",
        "庚寅",
        "松柏木",
    )
    assert (chart.wuxing_ju, chart.wuxing_ju_number, chart.dayun_start_age) == (
        "木三局",
        3,
        3,
    )
    assert (chart.ziwei_zhi, chart.tianfu_zhi, chart.dayun_direction) == ("未", "酉", "顺行")
    assert _seated(chart, only_major=True) == LEAP_MAJOR_STAR_ZHI
    by_zhi = {palace.zhi: palace for palace in chart.palaces}
    for zhi, (ganzhi, name, dayun) in LEAP_PALACE_ANCHORS.items():
        palace = by_zhi[zhi]
        assert (palace.ganzhi, palace.name, palace.dayun) == (ganzhi, name, dayun)
    marked = {
        star.name: star.sihua for palace in chart.palaces for star in palace.stars if star.sihua
    }
    assert marked == {"天同": "化禄", "天机": "化权", "文昌": "化科", "廉贞": "化忌"}


def test_leap_month_chart_shen_zhu_follows_the_year_branch() -> None:
    """身主诀「卯酉天同身主是，巳亥天机辰戌昌」→ 年支戌 → 文昌（此条两版无异说）。"""
    assert _leap_chart().shen_zhu == "文昌"
    assert _chart().shen_zhu == "文昌"  # 首盘年支辰，同诀亦主文昌


# ------------------------------------------------- 扫盘：大限平铺与身宫落点（结构不变量）

#: 七张实盘，五行局五种全覆盖（水二、木三、金四、土五、火六）、两种大限方向、
#: 闰月与两个日期端点。每张盘的局数与起运在别处已有手推锚，这里取其内部一致性。
SWEPT_BIRTHS: list[tuple[str, str, Gender]] = [
    ("2000-08-16", "12:00", Gender.MALE),     # 土五局 · 顺行
    ("2000-08-16", "12:00", Gender.FEMALE),   # 同上，逆行
    ("2006-09-02", "12:00", Gender.MALE),     # 木三局 · 闰七月 · 顺行
    ("1900-01-31", "12:00", Gender.MALE),     # 水二局 · 庚子年正月初一
    ("1970-01-01", "05:15", Gender.MALE),     # 金四局 · 逆行 · 卯时
    ("2100-12-31", "12:00", Gender.FEMALE),   # 木三局 · 日期上端
    ("1992-10-03", "12:00", Gender.MALE),     # 火六局 · 阳男顺行（五行局里唯一没被别处压到的一局）
]

#: 身宫只由生时决定落在哪一格（诀：「子午命宫、丑未福德、寅申官禄、卯酉迁移、
#: 辰戌财帛、巳亥夫妻」），与生月无关 —— 生月只决定从哪一宫起数。
CLASSICAL_SHEN_GONG: dict[str, str] = {
    "子": "命宫", "午": "命宫",
    "丑": "福德", "未": "福德",
    "寅": "官禄", "申": "官禄",
    "卯": "迁移", "酉": "迁移",
    "辰": "财帛", "戌": "财帛",
    "巳": "夫妻", "亥": "夫妻",
}


def _swept_chart(birth: str, hour: str, sex: Gender):
    return compute_ziwei_chart(
        birth_date=date.fromisoformat(birth),
        birth_time=time.fromisoformat(hour),
        calendar=CalendarType.SOLAR,
        longitude=116.4074,
        gender=sex,
        apply_true_solar_time=False,
        name=None,
    )


@pytest.mark.parametrize(("birth", "hour", "sex"), SWEPT_BIRTHS)
def test_the_twelve_dayun_blocks_tile_the_lifespan_without_gaps(
    birth: str, hour: str, sex: Gender
) -> None:
    """十二段大限摊在一条数轴上必须无缝、不重叠、每段十年、起运即局数。

    这是「大限」唯一的算术不变量：局数错一格、或某一段被写成九年，一生十二段运气
    当场平移或留缝，而 JSON 上每宫仍各有一个区间。逐宫点名的锚在 `PALACE_ANCHORS`
    与 `FEMALE_DAYUN_ANCHORS`，本条把它推广到任意盘（顺逆两行、五行局五种全覆盖）。
    """
    chart = _swept_chart(birth, hour, sex)
    starts = []
    for palace in chart.palaces:
        assert palace.dayun is not None, f"{palace.zhi} 宫没有大限"
        start, _, end = palace.dayun.partition("-")
        starts.append(int(start))
        assert int(end) - int(start) == 9, f"{palace.zhi} 宫大限不是十年: {palace.dayun}"
    assert len(starts) == 12
    assert sorted(starts) == list(range(min(starts), min(starts) + 120, 10))  # 无缝不重叠
    assert min(starts) == chart.dayun_start_age == chart.wuxing_ju_number  # 起运即局数


@pytest.mark.parametrize(("birth", "hour", "sex"), SWEPT_BIRTHS)
def test_the_shen_palace_lands_where_the_hour_says(birth: str, hour: str, sex: Gender) -> None:
    """身宫所落的**宫名**只认生时：午时 → 命宫、卯时 → 迁移……（六格诀表）。

    首盘午时身命同宫；1970-01-01 05:15 属卯时，故身宫该落在迁移宫。
    """
    chart = _swept_chart(birth, hour, sex)
    shen = [palace for palace in chart.palaces if palace.is_shen]
    assert len(shen) == 1, f"身宫标记应当只有一宫: {[(p.zhi, p.is_shen) for p in chart.palaces]}"
    assert shen[0].zhi == chart.shen_gong_zhi
    assert shen[0].name == chart.shen_gong_name == CLASSICAL_SHEN_GONG[chart.time_zhi]
