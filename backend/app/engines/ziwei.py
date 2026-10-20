"""紫微斗数 (Zi Wei Dou Shu) chart engine — deterministic 安星 on lunar-python.

紫微斗数 is not astronomy: it is a fixed placement algebra over the 农历 birth data.
This module reads the 农历年干支 / 月 / 日 / 时支 from ``lunar-python`` (after the
same True Solar Time correction 八字 uses, so the 时辰 is honest), then walks the
classical 安星 rules — 命宫 / 身宫 by 生月+生时, 五行局 by 命宫纳音, 紫微 by 局数+生日,
天府 by the 寅申 reflection, the fourteen 主星 by their fixed 顺逆 offsets, the 乙级
吉煞 by 年干支/月/时, the 生年干 四化 and the 大限 ranges — into the twelve 地支 palaces.

Every position is derived; none is invented at runtime (PRD no-mock rule). The
algorithms reproduce the published 安紫微诀 tables (e.g. 火六局 初一→酉、初二→午、
初三→亥、初四→辰、初五→丑) and the 紫微天府 twelve-pair symmetry exactly.
"""

from datetime import date, time

from app.content import CONTENT_VERSION, ZIWEI_CONTENT_SOURCES, ZIWEI_SOURCE, ziwei_plain
from app.content.ziwei_plain import ZIWEI_LUCK_FRAME, ZIWEI_MING_FRAME, overall_key
from app.content.bazi_nayin import nayin_meaning
from app.content.ziwei import (
    GAN,
    GAN_INDEX,
    HUOXING_BASE,
    LINGXING_BASE,
    LUCUN_BY_YEAR_GAN,
    MAJOR_STARS,
    MING_ZHU,
    MINOR_STARS,
    PALACE_NAMES,
    SHEN_ZHU,
    SIHUA,
    TIANFU_SERIES,
    TIANMA_BY_YEAR_ZHI,
    TIANKUI_TIANYUE,
    WUXING_JU,
    YIN_GAN_BY_YEAR_GAN,
    ZHI,
    ZHI_INDEX,
    ZIWEI_SERIES,
)
from app.engines.bazi_moment import resolve_natal_moment
from app.engines.plain_compose import compose, overview, reading
from app.engines.plain_corpora import ZIWEI
from app.schemas.common import CalendarType, Gender, PlainSection, ProvenanceTable
from app.schemas.ziwei import (
    Palace,
    SiHuaInfo,
    StarPlacement,
    ZiweiChart,
    ZiweiProvenance,
)

SCHOOL_NOTE = (
    "四化取《紫微斗数全书》通行本（庚干太阴化科、壬干左辅化科；他派或有天府/天相化科之异，此盘从全书派）。"
    "命宫五行局以命宫干支纳音定；大限从「阳男阴女顺行、阴男阳女逆行」，顺行即自命宫沿地支顺行（命→父母→福德→田宅…）推进，逆行则沿十二宫名次序（命→兄弟→夫妻→子女…）。"
    "闰月依同号起命，不作上下半月拆分。"
)

# Display order within a palace: 紫微系 → 天府系 → 六吉 → 禄马 → 六煞.
STAR_ORDER: tuple[str, ...] = (
    "紫微", "天机", "太阳", "武曲", "天同", "廉贞",
    "天府", "太阴", "贪狼", "巨门", "天相", "天梁", "七杀", "破军",
    "左辅", "右弼", "文昌", "文曲", "天魁", "天钺",
    "禄存", "天马",
    "擎羊", "陀罗", "火星", "铃星", "地空", "地劫",
)


def compute_ziwei_chart(
    *,
    birth_date: date,
    birth_time: time,
    calendar: CalendarType,
    longitude: float,
    gender: Gender,
    apply_true_solar_time: bool,
    name: str | None = None,
) -> ZiweiChart:
    """Chart a 紫微斗数 board from birth data (deterministic, no RNG)."""
    moment = resolve_natal_moment(
        birth_date=birth_date,
        birth_time=birth_time,
        calendar=calendar,
        longitude=longitude,
        apply_true_solar_time=apply_true_solar_time,
    )
    lunar = moment.lunar

    # --- 农历 birth facts (the real 安星 inputs) ---
    year_ganzhi = lunar.getYearInGanZhi()  # 正月初一 boundary, as 斗数 uses
    year_gan, year_zhi = year_ganzhi[0], year_ganzhi[1]
    raw_month = lunar.getMonth()
    lunar_leap = raw_month < 0
    lunar_month = abs(raw_month)
    lunar_day = lunar.getDay()
    time_zhi = lunar.getTimeZhi()
    hour_index = ZHI_INDEX[time_zhi]

    # --- 命宫 / 身宫 ---
    ming_index = (lunar_month + 1 - hour_index) % 12
    shen_index = (lunar_month + 1 + hour_index) % 12

    # --- 五虎遁: palace 天干 from 生年干 ---
    yin_gan_index = GAN_INDEX[YIN_GAN_BY_YEAR_GAN[year_gan]]

    def palace_gan(zhi_index: int) -> str:
        return GAN[(yin_gan_index + ((zhi_index - 2) % 12)) % 10]

    ming_gan = palace_gan(ming_index)
    ming_gong_ganzhi = ming_gan + ZHI[ming_index]
    ming_nayin = nayin_meaning(ming_gong_ganzhi)
    ju_number, ju_name = WUXING_JU[ming_nayin.element]

    # --- 安紫微 / 天府 / 十四主星 ---
    ziwei_index = _ziwei_index(lunar_day, ju_number)
    tianfu_index = (4 - ziwei_index) % 12

    placements: dict[str, int] = {}
    for star_name, offset in ZIWEI_SERIES:
        placements[star_name] = (ziwei_index + offset) % 12
    for star_name, offset in TIANFU_SERIES:
        placements[star_name] = (tianfu_index + offset) % 12

    # --- 乙级 吉煞 ---
    lucun = ZHI_INDEX[LUCUN_BY_YEAR_GAN[year_gan]]
    kui_zhi, yue_zhi = TIANKUI_TIANYUE[year_gan]
    placements["左辅"] = (4 + lunar_month - 1) % 12
    placements["右弼"] = (10 - (lunar_month - 1)) % 12
    placements["文昌"] = (10 - hour_index) % 12
    placements["文曲"] = (4 + hour_index) % 12
    placements["天魁"] = ZHI_INDEX[kui_zhi]
    placements["天钺"] = ZHI_INDEX[yue_zhi]
    placements["禄存"] = lucun
    placements["擎羊"] = (lucun + 1) % 12
    placements["陀罗"] = (lucun - 1) % 12
    placements["天马"] = ZHI_INDEX[TIANMA_BY_YEAR_ZHI[year_zhi]]
    placements["火星"] = (ZHI_INDEX[HUOXING_BASE[year_zhi]] + hour_index) % 12
    placements["铃星"] = (ZHI_INDEX[LINGXING_BASE[year_zhi]] + hour_index) % 12
    placements["地劫"] = (11 + hour_index) % 12
    placements["地空"] = (11 - hour_index) % 12

    # --- 生年干 四化 ---
    lu, quan, ke, ji = SIHUA[year_gan]
    sihua_of = {lu: "化禄", quan: "化权", ke: "化科", ji: "化忌"}

    # --- 十二宫名 (逆行 from 命宫) ---
    def palace_name(zhi_index: int) -> str:
        return PALACE_NAMES[(ming_index - zhi_index) % 12]

    # --- 大限 (阳男阴女顺行=自命宫依宫次序命兄夫子…推进；阴男阳女逆行) ---
    yang_year = GAN_INDEX[year_gan] % 2 == 0
    forward = (gender == Gender.MALE) == yang_year
    dayun_by_index: dict[int, str] = {}
    for step in range(12):
        zhi_index = (ming_index + step) % 12 if forward else (ming_index - step) % 12
        start_age = ju_number + 10 * step
        dayun_by_index[zhi_index] = f"{start_age}-{start_age + 9}"

    # --- Assemble the twelve palaces, ordered by 地支 index for grid layout ---
    palaces: list[Palace] = []
    for zhi_index in range(12):
        gan = palace_gan(zhi_index)
        stars = [
            _star(star_name, sihua_of)
            for star_name in STAR_ORDER
            if placements[star_name] == zhi_index
        ]
        palace = palace_name(zhi_index)
        # 本表不分带（G21）：斗数没有任何符号可传，符号位一律 0 由 `grouping="keep"` 忽略。
        # 此处不可能同键（偏差表第 8 行）：`STAR_ORDER` 逐星放置，一宫之内星名唯一；四化句
        # 按标记词（化禄/化权/化科/化忌）入键，而一星至多带一枚标记，所以一格一标记、键不撞，
        # 不调 `dedupe()`。（一宫可以有两枚以上的四化——它们各自入键，仍然不撞。）
        items: list[tuple[str, int]] = []
        for star in stars:
            items.append((ziwei_plain.star_key(star.name), 0))
            if star.sihua is not None:
                items.append((ziwei_plain.sihua_key(star.sihua), 0))
        palaces.append(
            Palace(
                index=zhi_index,
                zhi=ZHI[zhi_index],
                gan=gan,
                ganzhi=gan + ZHI[zhi_index],
                name=palace,
                is_ming=zhi_index == ming_index,
                is_shen=zhi_index == shen_index,
                dayun=dayun_by_index[zhi_index],
                stars=stars,
                plain=compose(ZIWEI, palace, items),
            )
        )

    month_cn = lunar.getMonthInChinese()
    day_cn = lunar.getDayInChinese()
    # `getMonthInChinese()` 对闰月**自带**「闰」字（返回「闰七」），所以这里不能再按
    # `lunar_leap` 补一次 —— 补了页面就印「闰闰七月」。同一事实的第二种写法见
    # `app/schemas/bazi_liuri.py:64`。闰与否的机器字段另有 `lunar_leap`。
    lunar_date = f"{year_ganzhi}年{month_cn}月{day_cn}"

    def stars_at(zhi_index: int) -> str:
        names = [name for name in STAR_ORDER if placements[name] == zhi_index]
        return "、".join(names) if names else "空宫"

    plain = [
        PlainSection(
            title="全盘气象",
            text=reading(ZIWEI, overall_key(ZHI[ziwei_index])),
        ),
        PlainSection(
            title="命宫与三方四正",
            text=overview(ZIWEI_MING_FRAME, {
                "ming_zhi": ZHI[ming_index],
                "ming_stars": stars_at(ming_index),
                "career_stars": stars_at((ming_index + 4) % 12),
                "travel_stars": stars_at((ming_index + 6) % 12),
                "wealth_stars": stars_at((ming_index + 8) % 12),
            }),
        ),
        PlainSection(
            title="运限与四化",
            text=overview(ZIWEI_LUCK_FRAME, {
                "wuxing_ju": ju_name,
                "start_age": str(ju_number),
                "shen_gong": palace_name(shen_index),
                "year_gan": year_gan,
                "lu": lu,
                "quan": quan,
                "ke": ke,
                "ji": ji,
                "direction": "顺行" if forward else "逆行",
            }),
        ),
    ]

    return ZiweiChart(
        name=name,
        gender=gender.value,
        calendar=calendar.value,
        standard_datetime=moment.standard_datetime.strftime("%Y-%m-%d %H:%M"),
        true_solar_time=moment.true_solar_time_text,
        tst_applied=apply_true_solar_time,
        tst_offset_minutes=moment.offset_minutes,
        longitude=moment.longitude_used,
        lunar_date=lunar_date,
        lunar_year_ganzhi=year_ganzhi,
        lunar_month=lunar_month,
        lunar_day=lunar_day,
        lunar_leap=lunar_leap,
        time_zhi=time_zhi,
        ming_gong_zhi=ZHI[ming_index],
        ming_gong_ganzhi=ming_gong_ganzhi,
        ming_gong_nayin=ming_nayin.nayin,
        shen_gong_zhi=ZHI[shen_index],
        shen_gong_name=palace_name(shen_index),
        wuxing_ju=ju_name,
        wuxing_ju_number=ju_number,
        ming_zhu=MING_ZHU[year_zhi],
        shen_zhu=SHEN_ZHU[year_zhi],
        ziwei_zhi=ZHI[ziwei_index],
        tianfu_zhi=ZHI[tianfu_index],
        palaces=palaces,
        sihua=SiHuaInfo(year_gan=year_gan, lu=lu, quan=quan, ke=ke, ji=ji),
        plain=plain,
        dayun_direction="顺行" if forward else "逆行",
        dayun_start_age=ju_number,
        provenance=ZiweiProvenance(
            engine="ziwei-deterministic",
            content_version=CONTENT_VERSION,
            source=ZIWEI_SOURCE,
            school_note=SCHOOL_NOTE,
            tables=_tables(),
        ),
    )


def _tables() -> list[ProvenanceTable]:
    """`ZIWEI_CONTENT_SOURCES` 的第一次被消费（G19）。

    复测（当前树）：`cd backend && grep -rn ZIWEI_CONTENT_SOURCES app/ tests/ --include=*.py` → 定义
    `content/__init__.py:144`、本模块 import `:17` 与消费 `:248`（行号随本注一起改，改动常量后重跑
    这条命令即得），测侧两处：`tests/content/test_ziwei_corpus.py:571` 逐字钉登记常量本身，
    `tests/test_ziwei_api.py:430-431` 拿活响应逐行对账。引擎不在此另列表名、不抄书名
    （同 `engines/kabbalah.py:60-70` 的写法）。
    """
    return [
        ProvenanceTable(name=module, version=CONTENT_VERSION, source=source)
        for module, source in ZIWEI_CONTENT_SOURCES
    ]


def _ziwei_index(day: int, ju: int) -> int:
    """安紫微诀: 生日 ÷ 局数, 商余定宫 (寅=2 起，借数奇逆偶顺).

    Reproduces the classical tables exactly — e.g. 火六局 初一→酉、初二→午、初三→亥、
    初四→辰、初五→丑、初六→寅, and 水二局 初一→丑、初二→寅、初三→寅、初四→卯.
    """
    quotient, remainder = divmod(day, ju)
    if remainder == 0:
        return (quotient + 1) % 12
    base = (quotient + 2) % 12
    borrow = ju - remainder
    return (base - borrow) % 12 if borrow % 2 == 1 else (base + borrow) % 12


def _star(name: str, sihua_of: dict[str, str]) -> StarPlacement:
    """Build a star placement, marking its 四化 when the 生年干 assigns one."""
    sihua = sihua_of.get(name)
    if name in MAJOR_STARS:
        star = MAJOR_STARS[name]
        return StarPlacement(
            name=name,
            kind="主星",
            element=star.element,
            yin_yang=star.yin_yang,
            group=star.group,
            nature=star.nature,
            sihua=sihua,
        )
    minor = MINOR_STARS[name]
    return StarPlacement(name=name, kind=minor.kind, element=minor.element, sihua=sihua)
