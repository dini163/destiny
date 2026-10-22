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
from app.content.ziwei_plain import (
    ZIWEI_COMPONENT_ADVICE,
    ZIWEI_LUCK_FRAME,
    ZIWEI_MING_FRAME,
    ZIWEI_VERDICT_ADVICE_FRAME,
    ZIWEI_VERDICT_BALANCED_FRAME,
    ZIWEI_VERDICT_FRAME,
    ZIWEI_VERDICT_OUTLOOK,
    overall_key,
)
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
from app.core.provenance import MODEL_PARAM_SOURCE
from app.engines.bazi_moment import resolve_natal_moment
from app.engines.plain_compose import compose, overview, reading
from app.engines.plain_corpora import ZIWEI
from app.engines.verdict import grade_for
from app.schemas.common import CalendarType, Gender, PlainSection, ProvenanceTable, Verdict
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

# --- 综合结论 verdict（2026-10-22 verdict-card spec §2b：无账本系统的新增判定层） ---
# 定性档（吉/平/动/忌）在 `content/ziwei.py::MajorStar.tendency`，逐星古籍出处在
# `tendency_source`；下面把档换算成分数的**数字权重全是模型参数**（古籍只给定性、不给数，
# 口径同 `MODEL_PARAM_SOURCE`），不是古籍赋分。三方四正 = 命宫 + 官禄(+4) + 迁移(+6)
# + 财帛(+8)（`ZIWEI_MING_FRAME` 同偏移），只评主舞台四格，其余八宫不入总分。

#: 主星倾向档 → 分（模型参数，MODEL_PARAM_SOURCE）。复测：
#: `cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "from app.engines.ziwei import MAJOR_TENDENCY_WEIGHT; print(MAJOR_TENDENCY_WEIGHT)"`
MAJOR_TENDENCY_WEIGHT: dict[str, float] = {"吉": 6.0, "平": 0.0, "动": 2.0, "忌": -6.0}

#: 乙级星 kind → 分（模型参数，MODEL_PARAM_SOURCE）：六吉助力、禄马次之、六煞牵制。
MINOR_KIND_WEIGHT: dict[str, float] = {"吉": 2.5, "禄马": 2.0, "煞": -2.5}

#: 生年四化标记 → 分（模型参数，MODEL_PARAM_SOURCE；禄权科为吉、化忌为凶是斗数通行口径）。
SIHUA_WEIGHT: dict[str, float] = {"化禄": 2.5, "化权": 2.5, "化科": 2.5, "化忌": -4.0}

#: 中性起点（模型参数，MODEL_PARAM_SOURCE）：50 为五档「平」带中位，加分上抬、减分下压。
VERDICT_BASE: float = 50.0

#: 上面四张权重表与起点的共同署名：模型参数（非古籍赋分），古籍只给定性档不给分数。
VERDICT_WEIGHT_SOURCE = MODEL_PARAM_SOURCE

#: 三环节名（建议句 `{component}` 槽与 `ZIWEI_COMPONENT_ADVICE` 的键一一对应）。
COMPONENT_MAJOR = "主星格局"
COMPONENT_MINOR = "辅佐煞曜"
COMPONENT_SIHUA = "生年四化"
#: 三环贡献都不为负时的中性维护建议键（`ZIWEI_COMPONENT_ADVICE["整体"]`）。
COMPONENT_BALANCED = "整体"


def _stage_palaces(ming_index: int) -> tuple[int, int, int, int]:
    """命宫三方四正的地支 index：命宫、官禄(+4)、迁移(+6)、财帛(+8)。"""
    return (
        ming_index,
        (ming_index + 4) % 12,
        (ming_index + 6) % 12,
        (ming_index + 8) % 12,
    )


def build_verdict(palaces: list[Palace], ming_index: int) -> Verdict:
    """从盘面已有事实确定性合成综合结论卡片（verdict-card spec §2b）。

    只读四格内已落座的星与四化标记，不重新判命、不现编中文：档位/星级由
    `grade_for(总分)` 派生，headline/advice 套 `ziwei_plain` 的框架句，points 是盘面
    事实计数。三环节贡献各自累加，建议句只指向贡献为负的最弱一环；三环都不为负时走
    中性维护句，不在没有短板的盘上虚构问题。
    """
    stage = set(_stage_palaces(ming_index))
    major_contrib = minor_contrib = sihua_contrib = 0.0
    major_ji = major_ji2 = minor_ji = minor_sha = lqk = ji_mark = 0
    for palace in palaces:
        if palace.index not in stage:
            continue
        for star in palace.stars:
            if star.kind == "主星":
                tendency = MAJOR_STARS[star.name].tendency
                major_contrib += MAJOR_TENDENCY_WEIGHT[tendency]
                if tendency == "吉":
                    major_ji += 1
                elif tendency == "忌":
                    major_ji2 += 1
            elif star.kind in MINOR_KIND_WEIGHT:
                minor_contrib += MINOR_KIND_WEIGHT[star.kind]
                if star.kind == "吉":
                    minor_ji += 1
                elif star.kind == "煞":
                    minor_sha += 1
            if star.sihua is not None:
                sihua_contrib += SIHUA_WEIGHT[star.sihua]
                if star.sihua == "化忌":
                    ji_mark += 1
                else:
                    lqk += 1

    score = max(0.0, min(100.0, VERDICT_BASE + major_contrib + minor_contrib + sihua_contrib))
    grade, stars = grade_for(score)

    # 建议句指向真正为负的一环（贡献最低的负项）；三环都不为负时走中性维护建议，
    # 不在没有化忌的盘上虚构「化忌反复回头」（同 bazi 指向最弱一维，但只在有短板时指）。
    contributions = [
        (COMPONENT_MAJOR, major_contrib),
        (COMPONENT_MINOR, minor_contrib),
        (COMPONENT_SIHUA, sihua_contrib),
    ]
    drags = [(name, value) for name, value in contributions if value < 0]
    if drags:
        weakest = min(drags, key=lambda item: item[1])[0]
        advice = overview(ZIWEI_VERDICT_ADVICE_FRAME, {
            "component": weakest,
            "component_advice": ZIWEI_COMPONENT_ADVICE[weakest],
        })
    else:
        advice = overview(ZIWEI_VERDICT_BALANCED_FRAME, {
            "component_advice": ZIWEI_COMPONENT_ADVICE[COMPONENT_BALANCED],
        })

    auspicious = major_ji + minor_ji
    malefic = major_ji2 + minor_sha + ji_mark
    headline = overview(ZIWEI_VERDICT_FRAME, {
        "grade": grade,
        "auspicious": str(auspicious),
        "malefic": str(malefic),
        "outlook": ZIWEI_VERDICT_OUTLOOK[grade],
    })
    return Verdict(
        grade=grade,
        stars=stars,
        headline=headline,
        points=[
            f"主星格局：吉{major_ji} · 忌{major_ji2}",
            f"辅佐煞曜：吉{minor_ji} · 煞{minor_sha}",
            f"生年四化：禄权科{lqk} · 化忌{ji_mark}",
        ],
        advice=advice,
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

    # 综合结论卡片：只读上面排好的四格盘面事实，不重新判命（verdict-card spec §2b）。
    verdict = build_verdict(palaces, ming_index)

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
        verdict=verdict,
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
