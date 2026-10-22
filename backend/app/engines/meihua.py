"""梅花易数 (Plum Blossom Numerology) raising and 体用 derivation engine.

梅花易数 (邵雍《梅花易数》) raises a hexagram from a moment or from reported numbers,
then reads it through 体用生克 rather than 六爻纳甲:

* 起卦 — ``time`` uses (年支序 + 农历月 + 农历日 [ + 时辰序 ]) with the 先天 (Fu Xi)
  trigram ordinals; ``number`` uses one to three reported integers. Both reduce
  mod 8 for the two trigrams and mod 6 for the single moving line.
* 体用 — the trigram *without* the moving line is 体 (body / self / 主), the one
  *with* it is 用 (use / affair / 客). Their 五行生克 is the primary verdict.
* 卦气 — the 体/用 elements are weighed by 旺相休囚死 under the 月令 (season).
* 互变 — the 互卦 (过程) and 变卦 (结局) trigrams' 生克 toward 体 refine the reading.

Calendar facts (lunar year/month/day, 时辰, 月建) come from ``lunar-python``; the
hexagram structure and 卦辞 come from the shared Zhouyi content tables; the 五行
cycles and the reference imagery/judgements come from :mod:`app.content`. The
``plain_summary`` paragraph is assembled by :func:`app.engines.plain_compose.compose`
out of :mod:`app.content.meihua_plain` sentences moved verbatim — this module adds no
prose of its own (多系统白话 spec §5). The engine is pure: no HTTP, no I/O, and no
randomness (梅花 raising is deterministic).
"""

from datetime import datetime

from lunar_python import Solar

from app.content import CONTENT_VERSION, MEIHUA_CONTENT_SOURCES, zhouyi_text
from app.content.meihua import (
    SEASON_BY_MONTH_ZHI,
    TIYONG_RELATIONS,
    WANGSHUAI_TEXT,
    leixiang_summary,
    wangshuai_state,
)
from app.content.meihua_plain import (
    MEIHUA_TIER_ADVICE,
    MEIHUA_VERDICT_ADVICE_FRAME,
    MEIHUA_VERDICT_FRAME,
    MEIHUA_VERDICT_OUTLOOK,
    leixiang_key,
    tiyong_key,
    wangshuai_key,
)
from app.content.wuxing import CONTROLS, GENERATES, ZHI_ELEMENT
from app.content.zhouyi_hexagrams import (
    HEXAGRAM_BY_TRIGRAMS,
    Hexagram,
    hexagram_from_lines,
    hexagram_from_trigrams,
)
from app.content.zhouyi_trigrams import TRIGRAM_BY_KEY, TRIGRAM_BY_MEIHUA, Trigram
from app.core.errors import InvalidCastInputError
from app.core.provenance import MODEL_PARAM_SOURCE
from app.engines.plain_compose import compose, dedupe, overview
from app.engines.plain_corpora import MEIHUA
from app.schemas.common import ProvenanceTable, Verdict
from app.schemas.meihua import (
    MeihuaCast,
    MeihuaDerivation,
    MeihuaHexagram,
    MeihuaMethod,
    MeihuaProvenance,
    MeihuaTrigram,
    ScoreFactor,
    TiYongParty,
    TiYongVerdict,
    WangshuaiInfo,
)

_BRANCH_ORDER = "子丑寅卯辰巳午未申酉戌亥"
_MAX_NUMBERS = 3

#: 溯源两句话。**历法库这一格照八字写成一个短值**（`engines/bazi.py:352` 的
#: `engine="lunar-python"`、`schemas/bazi_breakdown.py:34` 的「四柱来源引擎，恒为
#: lunar-python」），不要学 `numerology.py:146` 那句整段散文——那是不读历法库的系统才
#: 写得出的口径。梅花读 lunar-python（本模块 `cast_meihua` 里的 `Solar.fromDate(...).getLunar()`
#: 与 `eight_char.getMonthZhi()`），不写它就是读了不认账（AGENTS.md §7）；写成整句则会与
#: 前端 `meta` 行的短值版式相抵（BaziNatalPage.tsx:301 是 `{label: '排盘引擎', value: ...}`）。
#: 释义归 `METHOD_STATEMENT`，它只重述算式与取数之界（历数 vs 节令月），不带断语。
ENGINE_LUNAR = "lunar-python"
METHOD_STATEMENT = (
    "体用法出自邵雍《梅花易数》。时间法：上卦 = (年支序 + 农历月 + 农历日) mod 8、"
    "下卦 = 再加时辰序 mod 8、动爻 = 下卦之和 mod 6；报数法：两数或以上以首数定上卦、"
    "次数定下卦、诸数合计定动爻，单守则加时辰序。余零作除数本身；先天卦数 "
    "1乾 2兑 3离 4震 5巽 6坎 7艮 8坤；互卦取二三四与三四五爻，变卦只改动爻；"
    "无动爻之卦为体、有动爻之卦为用。卦气的月建取节气月（`getMonthZhi()`），"
    "与起卦所用的农历年月日各自一届，立春与春节之间的日子两套历法各取其界。"
    "起卦与体用推算是确定性运算，无随机。"
)


# --- 起卦: derive the two trigram numbers and the moving line ----------------


def _mod(number: int, modulus: int) -> int:
    """Reduce to 1..modulus (a zero remainder maps to the modulus itself)."""
    return number % modulus or modulus


def _derive_time(lunar: object) -> MeihuaDerivation:
    """年月日时起卦: 年支序 + 农历月 + 农历日 (+ 时辰序), Fu Xi ordinals."""
    year_number = _BRANCH_ORDER.index(lunar.getYearZhi()) + 1
    month = abs(lunar.getMonth())
    day = lunar.getDay()
    hour_number = _BRANCH_ORDER.index(lunar.getTimeZhi()) + 1

    upper_sum = year_number + month + day
    lower_sum = upper_sum + hour_number
    upper_number = _mod(upper_sum, 8)
    lower_number = _mod(lower_sum, 8)
    moving_position = _mod(lower_sum, 6)
    return MeihuaDerivation(
        upper_number=upper_number,
        lower_number=lower_number,
        moving_position=moving_position,
        formula=(
            f"(年{year_number}+月{month}+日{day})={upper_sum}，÷8余{upper_number}为上卦；"
            f"再加时{hour_number}={lower_sum}，÷8余{lower_number}为下卦、÷6余{moving_position}为动爻"
        ),
        inputs=f"农历年支序{year_number}、月{month}、日{day}、时辰序{hour_number}（{lunar.getTimeZhi()}时）",
    )


def _derive_numbers(numbers: list[int], lunar: object) -> MeihuaDerivation:
    """报数起卦: 1 number uses the 时辰; 2 numbers split upper/lower; 3 sums for the line."""
    if not numbers or len(numbers) > _MAX_NUMBERS or any(n <= 0 for n in numbers):
        raise InvalidCastInputError(f"number 起卦需 1 至 {_MAX_NUMBERS} 个正整数，收到 {numbers}。")

    if len(numbers) == 1:
        hour_number = _BRANCH_ORDER.index(lunar.getTimeZhi()) + 1
        n = numbers[0]
        upper_number = _mod(n, 8)
        lower_number = _mod(n + hour_number, 8)
        moving_position = _mod(n + hour_number, 6)
        formula = (
            f"报数{n}，÷8余{upper_number}为上卦；加时辰{hour_number}={n + hour_number}，"
            f"÷8余{lower_number}为下卦、÷6余{moving_position}为动爻"
        )
        inputs = f"报数 {n}、时辰序 {hour_number}（{lunar.getTimeZhi()}时）"
    else:
        upper_number = _mod(numbers[0], 8)
        lower_number = _mod(numbers[1], 8)
        total = sum(numbers)
        moving_position = _mod(total, 6)
        formula = (
            f"首数{numbers[0]}÷8余{upper_number}为上卦、次数{numbers[1]}÷8余{lower_number}为下卦；"
            f"诸数合计{total}÷6余{moving_position}为动爻"
        )
        inputs = "报数 " + "、".join(str(n) for n in numbers)

    return MeihuaDerivation(
        upper_number=upper_number,
        lower_number=lower_number,
        moving_position=moving_position,
        formula=formula,
        inputs=inputs,
    )


# --- Projections -------------------------------------------------------------


def _trigram(trigram: Trigram, position: str) -> MeihuaTrigram:
    return MeihuaTrigram(
        key=trigram.key,
        name_zh=trigram.name_zh,
        symbol=trigram.symbol,
        nature_zh=trigram.nature_zh,
        element=trigram.element,
        position=position,
    )


def _hexagram(hexagram: Hexagram) -> MeihuaHexagram:
    return MeihuaHexagram(
        number=hexagram.number,
        name_zh=hexagram.name_zh,
        full_name_zh=hexagram.full_name_zh,
        symbol=hexagram.symbol,
        lines=list(hexagram.lines),
        lower=_trigram(TRIGRAM_BY_KEY[hexagram.lower], "lower"),
        upper=_trigram(TRIGRAM_BY_KEY[hexagram.upper], "upper"),
        gua_ci=zhouyi_text.gua_ci(hexagram.number),
    )


def _relation_key(ti_element: str, yong_element: str) -> str:
    """Classify the 体用 relation from the two elements."""
    if ti_element == yong_element:
        return "bi_he"
    if GENERATES[yong_element] == ti_element:
        return "yong_sheng_ti"     # 用生体
    if GENERATES[ti_element] == yong_element:
        return "ti_sheng_yong"     # 体生用
    if CONTROLS[ti_element] == yong_element:
        return "ti_ke_yong"        # 体克用
    return "yong_ke_ti"            # 用克体 (the remaining relation)


def _relation_to_ti(ti_element: str, other_element: str) -> tuple[str, int]:
    """Return (short label, signed weight) of another element acting on the 体卦."""
    if other_element == ti_element:
        return "比和体", 3
    if GENERATES[other_element] == ti_element:
        return "生体", 4
    if CONTROLS[other_element] == ti_element:
        return "克体", -5
    if GENERATES[ti_element] == other_element:
        return "体生之(泄)", -2
    return "体克之(耗)", -1


# --- Public entry point ------------------------------------------------------


def cast_meihua(
    *,
    method: MeihuaMethod | str,
    numbers: list[int] | None = None,
    question: str | None = None,
    cast_time: datetime,
) -> MeihuaCast:
    """Raise a 梅花易数 hexagram and return the full 体用 derivation.

    ``cast_time`` is required so the engine stays pure; the HTTP adapter supplies the
    caller's time or the current moment. It provides the lunar numbers (time method /
    single-number method) and fixes the 月令 used for 卦气旺衰.
    """
    method = MeihuaMethod(method)
    lunar = Solar.fromDate(cast_time).getLunar()
    eight_char = lunar.getEightChar()

    derivation = _derive_time(lunar) if method is MeihuaMethod.TIME else _derive_numbers(numbers or [], lunar)

    upper_key = TRIGRAM_BY_MEIHUA[derivation.upper_number]
    lower_key = TRIGRAM_BY_MEIHUA[derivation.lower_number]
    ben = HEXAGRAM_BY_TRIGRAMS[(lower_key, upper_key)]
    bits = list(ben.lines)

    moving = derivation.moving_position
    changed = list(bits)
    changed[moving - 1] ^= 1
    bian = hexagram_from_lines(tuple(changed))
    hu = hexagram_from_trigrams(tuple(bits[1:4]), tuple(bits[2:5]))

    # 体用: the trigram without the moving line is 体, the one with it is 用.
    if moving <= 3:
        ti_key, yong_key, yong_position = upper_key, lower_key, "lower"
    else:
        ti_key, yong_key, yong_position = lower_key, upper_key, "upper"
    ti_trigram = TRIGRAM_BY_KEY[ti_key]
    yong_trigram = TRIGRAM_BY_KEY[yong_key]

    # 卦气 (月令): the season's commanding element from the 月建 branch.
    month_zhi = eight_char.getMonthZhi()
    commanding = ZHI_ELEMENT[month_zhi]
    season_zh = SEASON_BY_MONTH_ZHI[month_zhi]
    ti_state = wangshuai_state(ti_trigram.element, commanding)
    yong_state = wangshuai_state(yong_trigram.element, commanding)

    relation_key = _relation_key(ti_trigram.element, yong_trigram.element)
    relation = TIYONG_RELATIONS[relation_key]

    ti = TiYongParty(
        role="ti",
        trigram=_trigram(ti_trigram, "upper" if moving <= 3 else "lower"),
        leixiang=leixiang_summary(ti_trigram.key, ti_trigram.name_zh, ti_trigram.nature_zh),
        wangshuai=ti_state,
        wangshuai_text=WANGSHUAI_TEXT[ti_state],
    )
    yong = TiYongParty(
        role="yong",
        trigram=_trigram(yong_trigram, yong_position),
        leixiang=leixiang_summary(yong_trigram.key, yong_trigram.name_zh, yong_trigram.nature_zh),
        wangshuai=yong_state,
        wangshuai_text=WANGSHUAI_TEXT[yong_state],
    )
    tiyong = TiYongVerdict(
        relation=relation.key,
        relation_zh=relation.name_zh,
        verdict=relation.verdict,
        grade=relation.grade,
        text=relation.text,
    )

    hu_analysis, hu_delta = _hu_analysis(hu, ti_trigram.element)
    bian_analysis, bian_delta = _bian_analysis(ben, bian, yong_position, ti_trigram.element)

    factors = [
        ScoreFactor(
            label="体用生克",
            detail=f"{ti_trigram.name_zh}({ti_trigram.element})为体、{yong_trigram.name_zh}({yong_trigram.element})为用，{relation.name_zh}",
            delta=relation.base_score - 50,
        ),
        ScoreFactor(
            label="卦气旺衰",
            detail=f"体卦{ti_trigram.element}于{season_zh}（{commanding}当令）处「{ti_state}」",
            delta=_wangshuai_delta(ti_state),
        ),
        ScoreFactor(label="互卦(过程)", detail=hu_analysis, delta=hu_delta),
        ScoreFactor(label="变卦(结局)", detail=bian_analysis, delta=bian_delta),
    ]
    score = max(0, min(100, 50 + sum(factor.delta for factor in factors)))
    verdict = _verdict_band(score)
    plain_summary = meihua_plain_summary(ti, yong, relation.key, verdict)

    # 结论卡片（verdict-card spec §4）：档位词取 _verdict_band，星级取署名映射 MEIHUA_STARS，
    # headline/advice 套 meihua_plain 的框架句，points 是四本账 label + 净增减，引擎不现编中文。
    drag = min(factors, key=lambda factor: factor.delta)
    headline = overview(MEIHUA_VERDICT_FRAME, {
        "grade": verdict,
        "score": str(score),
        "outlook": MEIHUA_VERDICT_OUTLOOK[verdict],
    })
    advice = overview(MEIHUA_VERDICT_ADVICE_FRAME, {
        "drag": drag.label,
        "tier_advice": MEIHUA_TIER_ADVICE[verdict],
    })
    card = Verdict(
        grade=verdict,
        stars=MEIHUA_STARS[verdict],
        headline=headline,
        points=[f"{factor.label}（{factor.delta:+d}）" for factor in factors],
        advice=advice,
    )

    summary = (
        f"{verdict}。本卦{ben.full_name_zh}，{ti_trigram.name_zh}{ti_trigram.nature_zh}为体、"
        f"{yong_trigram.name_zh}{yong_trigram.nature_zh}为用，{relation.name_zh}——{relation.text}"
        f"体卦{ti_trigram.element}于{season_zh}（{commanding}令）处「{ti_state}」，{WANGSHUAI_TEXT[ti_state]}"
        f"过程看互卦：{hu_analysis}结局看变卦：{bian_analysis}"
        f"卦辞曰：「{zhouyi_text.gua_ci(ben.number)}」"
    )

    return MeihuaCast(
        method=method.value,
        question=question,
        cast_time=cast_time.strftime("%Y-%m-%d %H:%M"),
        derivation=derivation,
        ben=_hexagram(ben),
        hu=_hexagram(hu),
        bian=_hexagram(bian),
        moving_position=moving,
        ti=ti,
        yong=yong,
        tiyong=tiyong,
        wangshuai=WangshuaiInfo(month_zhi=month_zhi, season_zh=season_zh, commanding_element=commanding),
        hu_analysis=hu_analysis,
        bian_analysis=bian_analysis,
        score=score,
        score_factors=factors,
        verdict=card,
        summary=summary,
        plain_summary=plain_summary,
        provenance=meihua_provenance(),
    )


def _hu_analysis(hu: Hexagram, ti_element: str) -> tuple[str, int]:
    """Summarise the 互卦 (过程) two trigrams' 生克 toward the 体卦."""
    lower = TRIGRAM_BY_KEY[hu.lower]
    upper = TRIGRAM_BY_KEY[hu.upper]
    parts: list[str] = []
    delta = 0
    for trigram, label in ((lower, "下互"), (upper, "上互")):
        rel, weight = _relation_to_ti(ti_element, trigram.element)
        delta += weight
        parts.append(f"{label}{trigram.name_zh}{trigram.element}{rel}")
    clamped = max(-6, min(6, delta))
    text = f"互卦{hu.full_name_zh}，{'、'.join(parts)}（过程助力{clamped:+d}）。"
    return text, clamped


def _bian_analysis(ben: Hexagram, bian: Hexagram, yong_position: str, ti_element: str) -> tuple[str, int]:
    """Summarise the 变卦 (结局) changed trigram's 生克 toward the 体卦."""
    changed_key = bian.upper if yong_position == "upper" else bian.lower
    origin_key = ben.upper if yong_position == "upper" else ben.lower
    changed = TRIGRAM_BY_KEY[changed_key]
    origin = TRIGRAM_BY_KEY[origin_key]
    rel, weight = _relation_to_ti(ti_element, changed.element)
    clamped = max(-6, min(6, weight))
    text = f"用方由{origin.name_zh}{origin.element}变{changed.name_zh}{changed.element}，{rel}（结局{clamped:+d}）。"
    return text, clamped


def meihua_plain_summary(ti: TiYongParty, yong: TiYongParty, relation_key: str, band: str) -> str:
    """体用两侧的五句白话收成一段（八纯卦时用 `dedupe` 收成三句正文）。

    符号一律传 0：`grouping="keep"` 不查符号，而类象两条与用侧卦气在账本里本就没有对应
    行（`score_factors` 只有体卦的卦气），传真数会传进三个假数、传假数又要人分辨真假，
    不如整列都是同一个占位符，把「本表不分带」这句话写在调用点上。
    """
    return compose(
        MEIHUA,
        "summary",
        dedupe(
            [
                (tiyong_key(relation_key), 0),
                (leixiang_key(ti.trigram.key), 0),
                (wangshuai_key(ti.wangshuai), 0),
                (leixiang_key(yong.trigram.key), 0),
                (wangshuai_key(yong.wangshuai), 0),
            ]
        ),
        band,
    )


def meihua_provenance() -> MeihuaProvenance:
    """响应自带出处：历法库一个短值，五张表全取自 `MEIHUA_CONTENT_SOURCES`，本模块不再列第二遍表名。"""
    return MeihuaProvenance(
        engine=ENGINE_LUNAR,
        method=METHOD_STATEMENT,
        tables=[
            ProvenanceTable(name=module, version=CONTENT_VERSION, source=source)
            for module, source in MEIHUA_CONTENT_SOURCES
        ],
    )


def _wangshuai_delta(state: str) -> int:
    """Signed 卦气 contribution: 旺/相 strengthen, 囚/死 weaken the 体卦."""
    return {"旺": 8, "相": 5, "休": 0, "囚": -5, "死": -8}[state]


#: 六档 → 星级（署名模型参数，`MODEL_PARAM_SOURCE`；古籍只给定性档、不给星，故这张映射
#: 自定且单调不减：分越高星越多，上吉 5 / 吉 4 / 小吉 3 / 中平 3 / 小凶 2 / 凶 1）。
#: 复测：`cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "from app.engines.meihua import MEIHUA_STARS; print([(k, MEIHUA_STARS[k]) for k in ('上吉','吉','小吉','中平','小凶','凶')])"`
#: → `[('上吉', 5), ('吉', 4), ('小吉', 3), ('中平', 3), ('小凶', 2), ('凶', 1)]`。
MEIHUA_STARS: dict[str, int] = {
    "上吉": 5,
    "吉": 4,
    "小吉": 3,
    "中平": 3,
    "小凶": 2,
    "凶": 1,
}


def _verdict_band(score: int) -> str:
    """Map the 0-100 吉凶指数 onto a verdict label."""
    if score >= 85:
        return "上吉"
    if score >= 70:
        return "吉"
    if score >= 55:
        return "小吉"
    if score >= 45:
        return "中平"
    if score >= 30:
        return "小凶"
    return "凶"
