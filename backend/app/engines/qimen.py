"""奇门遁甲 (Qi Men Dun Jia) chart engine — 时家奇门 · 转盘法 · 拆补起局.

奇门 is not astronomy: it is a fixed placement algebra over the 用事时刻. From the
年月日时干支 that ``lunar-python`` derives from the cast moment this module:

1. **定局** — takes the governing 节气 (阳遁 winter→summer, 阴遁 summer→winter) and the
   三元 (from the 日干支符头, 拆补法), and reads the 局数 from the classical 歌诀 table.
2. **布地盘** — lays 戊己庚辛壬癸丁丙乙 into the 洛书九宫 from the 局数 palace, 阳遁顺行
   阴遁逆行 (中五宫亦得一枚，寄坤二).
3. **定值符值使** — the 时辰旬首 hides under a 六仪; that 六仪's 地盘宫 gives the 值符星
   and 值使门.
4. **转天盘** — 值符星 flies to the 时干's 地盘宫, dragging the 九星 and 天盘三奇六仪
   around the eight-palace ring (天禽寄坤二 travels with 天芮).
5. **转人盘** — the 值使门 walks N palaces (N = 时辰在旬中的序) 阳顺阴逆, the 八门 rotate
   rigidly with it.
6. **布神盘** — 值符神 sits where the 值符星 landed; the 八神 fill the ring 阳顺阴逆.

Every position is derived; none is invented at runtime (PRD no-mock rule).
"""

from datetime import datetime

from lunar_python import Solar

from app.content import CONTENT_VERSION, QIMEN_CONTENT_SOURCES
from app.content.qimen import (
    DOOR_BY_HOME,
    EIGHT_GODS,
    GOD_LUCK,
    GOD_NATURE,
    JIAZI,
    JIAZI_INDEX,
    LUOSHU,
    QIMEN_SOURCE,
    RING8,
    RING8_POS,
    STAR_BY_HOME,
    STAR_BY_NAME,
    XUNKONG_BY_XUNSHOU,
    XUNSHOU_INDEX_TO_YI,
    YANG_JU,
    YIMA_BY_ZHI,
    YIN_JU,
    YUAN_BY_ZHI,
    YUAN_NAMES,
    ZHI,
    DIPAN_SEQUENCE,
)
from app.content.qimen_plain import (
    QIMEN_VERDICT_ADVICE,
    QIMEN_VERDICT_ADVICE_FRAME,
    QIMEN_VERDICT_FRAME,
    QIMEN_VERDICT_OUTLOOK,
    door_key,
    god_key,
    overview_key,
    star_key,
)
from app.core.provenance import MODEL_PARAM_SOURCE
from app.engines.plain_compose import compose, compose_template, overview, reading
from app.engines.plain_corpora import QIMEN
from app.engines.verdict import grade_for
from app.schemas.common import PlainSection, ProvenanceTable, Verdict
from app.schemas.qimen import (
    DoorInfo,
    GodInfo,
    QimenChart,
    QimenPalace,
    QimenProvenance,
    StarInfo,
)

SCHOOL_NOTE = (
    "起局用拆补法（以日干支符头定上中下元），非置闰超神接气法；排盘用转盘法（天盘/人盘整体旋转），"
    "非飞宫飞盘法。中五宫无门无神，天禽星与中宫地盘干寄坤二宫（转盘通行寄法）。"
    "八神取值符·螣蛇·太阴·六合·白虎·玄武·九地·九天八将（他派或以勾陈代白虎、朱雀代玄武）。"
    "时辰径取输入钟点，未作真太阳时校正；临界时辰请以校正后时间起局。"
)

#: Board output order — 洛书数 1→9 (the frontend places each by its grid row/col).
_PALACE_ORDER: tuple[int, ...] = (1, 2, 3, 4, 5, 6, 7, 8, 9)


def _ring_pos(palace: int) -> int:
    """Ring position on the eight-palace rotation ring; 中五宫 寄坤二."""
    return RING8_POS[2 if palace == 5 else palace]


# --- 综合结论 verdict（2026-10-22 verdict-card spec §2b：无账本系统的新增判定层） ---
#: 洛书数 → 中文宫名（headline/points 用）。
_PALACE_CN: dict[int, str] = {1: "一", 2: "二", 3: "三", 4: "四", 5: "五", 6: "六", 7: "七", 8: "八", 9: "九"}

#: 用神宫吉凶计数权重（模型参数，MODEL_PARAM_SOURCE）：值符宫、值使宫内每枚「吉」星/门/神 +k、
#: 每枚「凶」−k，「中平」0。为什么只数这两宫而不是全盘：九星/八门/八神在每一局都各出现一次，
#: 全盘吉凶总数随旋转恒定，数全盘每局同分、档位永不变化；值符（天盘主）、值使（人盘主）才是
#: 转盘法读局的用神宫，落点随用事时刻变。传统只给定性吉凶（`content/qimen.py` 的 luck），
#: 不给数字，故 k 自署模型参数。复测：
#: `cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "from app.engines.qimen import LUCK_WEIGHT; print(LUCK_WEIGHT)"` → `4.0`。
LUCK_WEIGHT: float = 4.0

#: 中性起点（模型参数，MODEL_PARAM_SOURCE）：50 为五档「平」带中位。
VERDICT_BASE: float = 50.0

#: 上面权重与起点的共同署名：模型参数（非古籍赋分），传统只给定性吉凶不给分数。
VERDICT_WEIGHT_SOURCE = MODEL_PARAM_SOURCE


def _palace_luck(palace: QimenPalace) -> tuple[int, int]:
    """一宫内星/门/神的吉、凶枚数（中平不计）。"""
    good = sum(1 for star in palace.stars if star.luck == "吉")
    bad = sum(1 for star in palace.stars if star.luck == "凶")
    if palace.door:
        good += 1 if palace.door.luck == "吉" else 0
        bad += 1 if palace.door.luck == "凶" else 0
    if palace.god:
        good += 1 if palace.god.luck == "吉" else 0
        bad += 1 if palace.god.luck == "凶" else 0
    return good, bad


def build_verdict(palaces: list[QimenPalace]) -> Verdict:
    """从值符/值使两宫的吉凶计数确定性合成综合结论卡片（verdict-card spec §2b）。

    不重新判局、不现编中文：档位/星级由 `grade_for(50 + k×(吉−凶))` 派生，headline/advice
    套 `qimen_plain` 的框架句，points 是两宫各自的吉凶枚数。
    """
    zhifu = next(p for p in palaces if p.is_zhifu_palace)
    zhishi = next(p for p in palaces if p.is_zhishi_palace)
    same = zhifu.number == zhishi.number
    zhi_good, zhi_bad = _palace_luck(zhifu)
    shi_good, shi_bad = _palace_luck(zhishi)
    # 值符值使同宫时只数一遍：两旗标指同一宫，重复计数会把该宫净值翻倍。
    net = (zhi_good - zhi_bad) if same else (zhi_good - zhi_bad) + (shi_good - shi_bad)
    score = max(0.0, min(100.0, VERDICT_BASE + LUCK_WEIGHT * net))
    grade, stars = grade_for(score)
    same = zhifu.number == zhishi.number
    zhi_label = f"{_PALACE_CN[zhifu.number]}宫"
    shi_label = f"{_PALACE_CN[zhishi.number]}宫"
    headline = overview(QIMEN_VERDICT_FRAME, {
        "grade": grade,
        "zhi": zhi_label,
        "shi": shi_label,
        "outlook": QIMEN_VERDICT_OUTLOOK[grade],
    })
    advice_key = "favorable" if net >= 0 else "adverse"
    advice = overview(QIMEN_VERDICT_ADVICE_FRAME, {"advice": QIMEN_VERDICT_ADVICE[advice_key]})
    if same:
        points = [f"值符值使同落{zhi_label}：吉{zhi_good} · 凶{zhi_bad}"]
    else:
        points = [
            f"值符落{zhi_label}：吉{zhi_good} · 凶{zhi_bad}",
            f"值使落{shi_label}：吉{shi_good} · 凶{shi_bad}",
        ]
    return Verdict(grade=grade, stars=stars, headline=headline, points=points, advice=advice)


def compute_qimen_chart(*, cast_time: datetime, question: str | None = None) -> QimenChart:
    """Cast a 时家奇门 board for a moment (deterministic, no RNG)."""
    solar = Solar.fromYmdHms(
        cast_time.year, cast_time.month, cast_time.day,
        cast_time.hour, cast_time.minute, cast_time.second,
    )
    lunar = solar.getLunar()

    year_gz = lunar.getYearInGanZhi()
    month_gz = lunar.getMonthInGanZhi()
    day_gz = lunar.getDayInGanZhi()
    time_gz = lunar.getTimeInGanZhi()

    # --- 1. 定局：节气定阴阳遁与三元局数组，日干支符头定元 ---
    jieqi = lunar.getPrevJieQi().getName()
    is_yang = jieqi in YANG_JU
    triple = YANG_JU.get(jieqi) or YIN_JU.get(jieqi)
    if triple is None:  # pragma: no cover — lunar-python always yields one of the 24
        raise ValueError(f"未识别的节气：{jieqi}")
    day_index = JIAZI_INDEX[day_gz]
    futou_index = (day_index // 5) * 5
    yuan = YUAN_BY_ZHI[ZHI[futou_index % 12]]
    ju_number = triple[yuan]
    dun = "阳遁" if is_yang else "阴遁"

    # --- 2. 布地盘：三奇六仪入九宫，阳遁顺行阴遁逆行 ---
    dipan: dict[int, str] = {}
    for offset, gan in enumerate(DIPAN_SEQUENCE):
        if is_yang:
            palace = ((ju_number - 1 + offset) % 9) + 1
        else:
            palace = ((ju_number - 1 - offset) % 9) + 1
        dipan[palace] = gan

    # --- 3. 值符值使：时辰旬首遁六仪，其地盘宫定值符星/值使门 ---
    time_index = JIAZI_INDEX[time_gz]
    xunshou_index = (time_index // 10) * 10
    xunshou_gz = JIAZI[xunshou_index]
    xunshou_yi = XUNSHOU_INDEX_TO_YI[xunshou_index]
    fu_palace = next(p for p, g in dipan.items() if g == xunshou_yi)
    zhifu_star = STAR_BY_HOME[fu_palace]                       # 中五宫 → 天禽
    zhishi_home = 2 if fu_palace == 5 else fu_palace           # 中五无门，寄坤二死门
    zhishi_door = DOOR_BY_HOME[zhishi_home]

    # 时干落地盘宫（甲遁旬首六仪，故甲子时值符伏吟于本宫）
    shi_gan = time_gz[0]
    shi_gan_palace = fu_palace if shi_gan == "甲" else next(p for p, g in dipan.items() if g == shi_gan)

    # --- 4. 转天盘：值符星飞临时干宫，九星与天盘干随环整体旋转 ---
    fu_pos = _ring_pos(fu_palace)
    shi_pos = _ring_pos(shi_gan_palace)
    d_star = (shi_pos - fu_pos) % 8
    zhifu_dest_palace = RING8[shi_pos]

    # --- 5. 转人盘：值使门自本宫数 N 时辰（阳顺阴逆），八门随之整体旋转 ---
    n_shichen = time_index % 10
    direction = 1 if is_yang else -1
    d_door = (direction * n_shichen) % 8
    zhishi_dest_palace = RING8[(fu_pos + d_door) % 8]

    # --- 6. 布神盘：值符神居值符星落宫，八神阳顺阴逆 ---
    zhifu_god_pos = shi_pos

    # --- 旬空 · 驿马 ---
    kongwang = XUNKONG_BY_XUNSHOU[xunshou_index]
    kong_zhi = set(kongwang)
    yima = YIMA_BY_ZHI[time_gz[1]]

    # --- Assemble the nine palaces ---
    palaces: list[QimenPalace] = []
    for number in _PALACE_ORDER:
        meta = LUOSHU[number]
        kong = any(z in kong_zhi for z in meta.zhi)
        ma = yima in meta.zhi
        if number == 5:
            palaces.append(
                QimenPalace(
                    number=5, gua=meta.gua, direction=meta.direction, element=meta.element,
                    zhi="", row=meta.row, col=meta.col, is_center=True,
                    dipan_gan=dipan[5], tianpan_gan=[], stars=[], door=None, god=None,
                    kong=False, ma=False, is_zhifu_palace=False, is_zhishi_palace=False,
                    # 中宫条目为零：`compose()` 的 `items=[]` 分支只递开篇句（G27 的 1 行段）。
                    plain=compose(QIMEN, meta.gua, []),
                )
            )
            continue

        j = RING8_POS[number]
        src_palace = RING8[(j - d_star) % 8]
        stars = [_star_info(src_palace, zhifu_star.name, number == zhifu_dest_palace)]
        tianpan = [dipan[src_palace]]
        if src_palace == 2:  # 坤二携天禽与中宫地盘干同行
            stars.append(_star_info(5, zhifu_star.name, number == zhifu_dest_palace))
            tianpan.append(dipan[5])

        door_src = RING8[(j - d_door) % 8]
        door = _door_info(door_src, number == zhishi_dest_palace)

        god_index = (direction * (j - zhifu_god_pos)) % 8
        god_name = EIGHT_GODS[god_index]
        god = GodInfo(name=god_name, luck=GOD_LUCK[god_name], nature=GOD_NATURE[god_name])

        # 本表不分带（G21 / 偏差表第 1 行）：奇门没有任何符号可传，符号位一律 0 由
        # `grouping="keep"` 忽略。次序 = 读盘序「星→门→神」；此处不可能同键（偏差表第 8 行：
        # 一环之星互不相同、门环与神环各自双射），所以不调 `dedupe()`。
        # （寄坤二那一格带天芮·天禽两枚星，也是两个不同星名各走一次 `star_key`，键仍不撞。）
        items: list[tuple[str, int]] = [(star_key(star.name), 0) for star in stars]
        items.append((door_key(door.name), 0))
        items.append((god_key(god_name), 0))

        palaces.append(
            QimenPalace(
                number=number, gua=meta.gua, direction=meta.direction, element=meta.element,
                zhi=meta.zhi, row=meta.row, col=meta.col, is_center=False,
                dipan_gan=dipan[number], tianpan_gan=tianpan, stars=stars, door=door, god=god,
                kong=kong, ma=ma,
                is_zhifu_palace=number == zhifu_dest_palace,
                is_zhishi_palace=number == zhishi_dest_palace,
                plain=compose(QIMEN, meta.gua, items),
            )
        )

    ju_name = f"{dun}{_cn_number(ju_number)}局"
    plain = [
        PlainSection(title="值符主线", text=compose_template(
            reading(QIMEN, overview_key("zhifu")),
            {"star": zhifu_star.name, "number": str(zhifu_dest_palace)})),
        PlainSection(title="值使门线", text=compose_template(
            reading(QIMEN, overview_key("zhishi")),
            {"door": zhishi_door.name, "number": str(zhishi_dest_palace)})),
        PlainSection(title="时干落宫", text=compose_template(
            reading(QIMEN, overview_key("shigan")),
            {"gan": shi_gan, "number": str(shi_gan_palace)})),
        PlainSection(title="旬空与驿马", text=compose_template(
            reading(QIMEN, overview_key("kongma")),
            {"kong": kongwang, "ma": yima})),
    ]
    return QimenChart(
        question=question,
        cast_time=cast_time.strftime("%Y-%m-%d %H:%M"),
        year_ganzhi=year_gz,
        month_ganzhi=month_gz,
        day_ganzhi=day_gz,
        time_ganzhi=time_gz,
        jieqi=jieqi,
        yuan=YUAN_NAMES[yuan],
        dun=dun,
        ju_number=ju_number,
        ju_name=ju_name,
        xunshou=xunshou_gz,
        xunshou_yi=xunshou_yi,
        zhifu_star=zhifu_star.name,
        zhishi_door=zhishi_door.name,
        zhifu_palace=zhifu_dest_palace,
        zhishi_palace=zhishi_dest_palace,
        kongwang=kongwang,
        yima=yima,
        palaces=palaces,
        plain=plain,
        verdict=build_verdict(palaces),
        provenance=QimenProvenance(
            engine="qimen-luoshu-rotating",
            content_version=CONTENT_VERSION,
            source=QIMEN_SOURCE,
            school_note=SCHOOL_NOTE,
            tables=_tables(),
        ),
    )


def _tables() -> list[ProvenanceTable]:
    """`QIMEN_CONTENT_SOURCES` 的第一次被消费（G19）。

    复测（当前树）：`cd backend && grep -rn QIMEN_CONTENT_SOURCES app/ tests/ --include=*.py` →
    定义处 `content/__init__.py:152`、本模块 import `:25` 与消费处 `:242`、`tests/content/
    test_qimen_corpus.py:299` 那条只钉形状的断言——改前只剩定义处与那条断言，是死登记。
    表名只这一处来源，引擎不再抄一份书名（同 `engines/ziwei.py:239-249` 的写法）。
    """
    return [
        ProvenanceTable(name=module, version=CONTENT_VERSION, source=source)
        for module, source in QIMEN_CONTENT_SOURCES
    ]


def _star_info(home: int, zhifu_name: str, at_zhifu_palace: bool) -> StarInfo:
    """Build a star placement, flagging the 值符星 where it landed."""
    star = STAR_BY_HOME[home] if home != 5 else STAR_BY_NAME["天禽"]
    return StarInfo(
        name=star.name,
        element=star.element,
        luck=star.luck,
        nature=star.nature,
        is_zhifu=(star.name == zhifu_name and at_zhifu_palace),
    )


def _door_info(home: int, is_zhishi: bool) -> DoorInfo:
    door = DOOR_BY_HOME[home]
    return DoorInfo(
        name=door.name, element=door.element, luck=door.luck,
        nature=door.nature, is_zhishi=is_zhishi,
    )


_CN = {1: "一", 2: "二", 3: "三", 4: "四", 5: "五", 6: "六", 7: "七", 8: "八", 9: "九"}


def _cn_number(n: int) -> str:
    return _CN.get(n, str(n))
