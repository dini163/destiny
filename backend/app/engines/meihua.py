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
engine is pure: no HTTP, no I/O, and no randomness (梅花 raising is deterministic).
"""

from datetime import datetime

from lunar_python import Solar

from app.content import zhouyi_text
from app.content.meihua import (
    SEASON_BY_MONTH_ZHI,
    TIYONG_RELATIONS,
    WANGSHUAI_TEXT,
    leixiang_summary,
    wangshuai_state,
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
from app.schemas.meihua import (
    MeihuaCast,
    MeihuaDerivation,
    MeihuaHexagram,
    MeihuaMethod,
    MeihuaTrigram,
    ScoreFactor,
    TiYongParty,
    TiYongVerdict,
    WangshuaiInfo,
)

_BRANCH_ORDER = "子丑寅卯辰巳午未申酉戌亥"
_MAX_NUMBERS = 3


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
        verdict=verdict,
        summary=summary,
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


def _wangshuai_delta(state: str) -> int:
    """Signed 卦气 contribution: 旺/相 strengthen, 囚/死 weaken the 体卦."""
    return {"旺": 8, "相": 5, "休": 0, "囚": -5, "死": -8}[state]


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
