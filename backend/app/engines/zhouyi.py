"""Zhouyi / Liuyao (周易六爻) casting and derivation engine.

The engine casts six lines, resolves them to a hexagram via the curated tables,
and dresses the primary (本卦) hexagram with 纳甲 (stem/branch), 六亲, 六神,
世应 and the classical 卦辞/爻辞. It also derives the changed (变卦) and nuclear
(互卦) hexagrams. Three casting methods are supported (PRD 6.x):

* ``three_coin`` — six throws of three coins, simulated with :mod:`secrets`.
* ``manual``     — the caller supplies the six throws of three coins.
* ``time``       — 梅花易数 plum-blossom casting from the lunar date/time.

All hexagram, najia and palace structure comes from the content tables; the
day pillar (for 六神) and the lunar numbers (for the time method) come from
``lunar-python``. The engine performs no HTTP or I/O beyond these pure lookups.

The 卦辞/爻辞 vernacular retellings are looked up one key at a time (``reading``);
the whole-hexagram reading is likewise a lookup (one table row per King Wen number),
and the only formatting is the moving-line frame that states how many lines moved.

旧裁定（丁组 spec §7 规则 5「六爻无分数、无档位，白话层不新建判断」）已于 verdict
轮推翻：白话块本身仍不合成排名（450 条逐爻今译无物可合并），综合吉凶改由独立的
结论卡片承担——断辞词频净值经受控词表（``content/zhouyi_duanci.py``）折算成 0-100
倾向分，再交共享 ``grade_for`` 换档，判定层与今译白话层分开。
"""

from datetime import datetime
import secrets

from lunar_python import Solar

from app.content import CONTENT_VERSION, ZHOUYI_CONTENT_SOURCES, zhouyi_text
from app.content.wuxing import CONTROLLED_BY, GENERATES, GENERATED_BY, ZHI_ELEMENT
from app.content.zhouyi_duanci import NEGATIVE_WORDS, POSITIVE_WORDS
from app.content.zhouyi_hexagrams import Hexagram, hexagram_from_lines, hexagram_from_trigrams
from app.content.zhouyi_najia import liushen_for_day_gan, najia_for_hexagram
from app.content.zhouyi_plain import (
    ZHOUYI_MOVE_FRAME,
    ZHOUYI_VERDICT_ADVICE,
    ZHOUYI_VERDICT_OUTLOOK,
    ZHOUYI_VERDICT_SUMMARY_FRAME,
    gua_ci_key,
    overall_key,
    yao_ci_key,
    yong_ci_key,
)
from app.content.zhouyi_trigrams import TRIGRAM_BY_KEY, TRIGRAM_BY_MEIHUA
from app.core.errors import InvalidCastInputError
from app.core.provenance import MODEL_PARAM_SOURCE
# 同层 engines 互引合规（AGENTS §1 只禁 `engines → api`），先例 `engines/qimen.py:50-51`。
from app.engines.plain_compose import overview, reading
from app.engines.plain_corpora import ZHOUYI
from app.engines.verdict import grade_for
from app.schemas.common import PlainSection, ProvenanceTable, Verdict
from app.schemas.zhouyi import CastMethod, HexagramInfo, ZhouyiCast, ZhouyiLine, ZhouyiProvenance

# An OS-backed CSPRNG (never the ``random`` module) for coin/time casting.
_RNG = secrets.SystemRandom()

# Coin faces: 2 (阴面/字) or 3 (阳面/背). A throw of three sums to 6/7/8/9.
_COIN_FACES = (2, 3)
_COINS_PER_THROW = 3
_THROWS_PER_CAST = 6

# Line value semantics (三枚铜钱):
_YANG_VALUES = frozenset({7, 9})    # a yang (阳) line
_MOVING_VALUES = frozenset({6, 9})  # old yin (6) / old yang (9) — the moving lines (动爻)

_LINE_SYMBOL = {1: "⚊", 0: "⚋"}
_BRANCH_ORDER = "子丑寅卯辰巳午未申酉戌亥"

# 六亲 names, keyed by the branch element's relation to the palace element (我).
_LIUQIN_PARENT = "父母"      # 生我者
_LIUQIN_BROTHER = "兄弟"     # 同我者
_LIUQIN_OFFSPRING = "子孙"   # 我生者
_LIUQIN_WEALTH = "妻财"      # 我克者
_LIUQIN_OFFICER = "官鬼"     # 克我者


# --- Casting: produce six line values (6/7/8/9) -----------------------------


def _cast_three_coin() -> list[int]:
    """Simulate six throws of three coins with a cryptographically secure RNG."""
    return [sum(_RNG.choice(_COIN_FACES) for _ in range(_COINS_PER_THROW)) for _ in range(_THROWS_PER_CAST)]


def _cast_manual(manual_coins: list[list[int]] | None) -> list[int]:
    """Validate caller-supplied throws (six throws of three faces, each 2 or 3)."""
    if manual_coins is None:
        raise InvalidCastInputError("The manual method requires manual_coins (six throws of three coin faces).")
    if len(manual_coins) != _THROWS_PER_CAST:
        raise InvalidCastInputError(f"manual_coins must contain exactly {_THROWS_PER_CAST} throws, got {len(manual_coins)}.")
    values: list[int] = []
    for index, throw in enumerate(manual_coins, start=1):
        if len(throw) != _COINS_PER_THROW or any(coin not in _COIN_FACES for coin in throw):
            raise InvalidCastInputError(f"Throw {index} must be {_COINS_PER_THROW} coin faces, each 2 or 3.")
        values.append(sum(throw))
    return values


def _cast_time(lunar: object) -> list[int]:
    """梅花易数 time casting from lunar year/month/day/hour numbers.

    Upper trigram = (year + month + day) mod 8; lower trigram = (year + month +
    day + hour) mod 8; moving line = (year + month + day + hour) mod 6 (0 maps to
    8 / 6 respectively). Trigram numbers use the Fu Xi (先天) ordinal.
    """
    year = _BRANCH_ORDER.index(lunar.getYearZhi()) + 1
    month = abs(lunar.getMonth())
    day = lunar.getDay()
    hour = _BRANCH_ORDER.index(lunar.getTimeZhi()) + 1

    upper_number = (year + month + day) % 8 or 8
    lower_number = (year + month + day + hour) % 8 or 8
    moving_position = (year + month + day + hour) % 6 or 6

    lower_binary = TRIGRAM_BY_KEY[TRIGRAM_BY_MEIHUA[lower_number]].binary
    upper_binary = TRIGRAM_BY_KEY[TRIGRAM_BY_MEIHUA[upper_number]].binary
    bits = list(lower_binary) + list(upper_binary)

    # Encode the single moving line as an old value, all others as young.
    return [
        (9 if bit else 6) if position == moving_position else (7 if bit else 8)
        for position, bit in enumerate(bits, start=1)
    ]


def _cast_values(method: CastMethod, manual_coins: list[list[int]] | None, lunar: object) -> list[int]:
    if method is CastMethod.THREE_COIN:
        return _cast_three_coin()
    if method is CastMethod.MANUAL:
        return _cast_manual(manual_coins)
    return _cast_time(lunar)


# --- Derivation -------------------------------------------------------------


def _split_values(values: list[int]) -> tuple[list[int], list[int]]:
    """Return the six yin/yang bits (1/0) and the moving-line positions (1-6)."""
    bits = [1 if value in _YANG_VALUES else 0 for value in values]
    moving = [position for position, value in enumerate(values, start=1) if value in _MOVING_VALUES]
    return bits, moving


def _apply_moving_lines(bits: list[int], moving_positions: list[int]) -> list[int]:
    """Flip the moving lines to build the changed (变卦) hexagram's bits."""
    changed = list(bits)
    for position in moving_positions:
        changed[position - 1] ^= 1
    return changed


def _liuqin(palace_element: str, branch_element: str) -> str:
    """Classify a line's 六亲 from its branch element vs. the palace element (我)."""
    if branch_element == palace_element:
        return _LIUQIN_BROTHER
    if branch_element == GENERATED_BY[palace_element]:
        return _LIUQIN_PARENT
    if branch_element == GENERATES[palace_element]:
        return _LIUQIN_OFFSPRING
    if branch_element == CONTROLLED_BY[palace_element]:
        return _LIUQIN_OFFICER
    return _LIUQIN_WEALTH  # 我克者妻财 (the remaining relation)


def _hexagram_info(hexagram: Hexagram) -> HexagramInfo:
    """Project a content :class:`Hexagram` into its response schema."""
    lower = TRIGRAM_BY_KEY[hexagram.lower]
    upper = TRIGRAM_BY_KEY[hexagram.upper]
    yong = zhouyi_text.yong_ci(hexagram.number)   # (title, text) for 乾/坤, else None
    return HexagramInfo(
        number=hexagram.number,
        name_zh=hexagram.name_zh,
        full_name_zh=hexagram.full_name_zh,
        pinyin=hexagram.pinyin,
        name_en=hexagram.name_en,
        symbol=hexagram.symbol,
        lines=list(hexagram.lines),
        lower=hexagram.lower,
        lower_name_zh=lower.name_zh,
        lower_nature_zh=lower.nature_zh,
        upper=hexagram.upper,
        upper_name_zh=upper.name_zh,
        upper_nature_zh=upper.nature_zh,
        palace=hexagram.palace,
        palace_name_zh=TRIGRAM_BY_KEY[hexagram.palace].name_zh + "宫",
        palace_element=hexagram.palace_element,
        generation=hexagram.generation,
        shi=hexagram.shi,
        ying=hexagram.ying,
        gua_ci=zhouyi_text.gua_ci(hexagram.number),
        plain_gua_ci=reading(ZHOUYI, gua_ci_key(hexagram.number)),
        yong_ci=yong[1] if yong is not None else None,
        plain_yong_ci=reading(ZHOUYI, yong_ci_key(hexagram.number)) if yong is not None else None,
    )


# --- 综合结论卡片（verdict）：断辞词频净值 → 倾向分 → 共享五档 -----------------

#: 每条净断辞的倾向分步进。古籍只给定性吉凶、不给数，故为本系统模型参数（同
#: `MODEL_PARAM_SOURCE` 口径），不是古籍赋分；阈值换档交给共享 `grade_for`。
_DUANCI_WEIGHT = 6.0
_DUANCI_BASE = 50.0


def _duanci_counts(text: str) -> tuple[int, int]:
    """统计一段经文里正向/负向受控断辞的条数。

    「无咎」是一个完整占辞，先数并从文本剔除，裸「咎」才归负向，否则无咎被双记；
    其余正向词（吉/亨/利）与负向词（凶/吝/悔/咎/厉）各自按出现次数累加。
    """
    working = text
    positive = working.count(POSITIVE_WORDS[0])  # 首项恒为「无咎」
    working = working.replace(POSITIVE_WORDS[0], "")
    for word in POSITIVE_WORDS[1:]:
        positive += working.count(word)
    negative = sum(working.count(word) for word in NEGATIVE_WORDS)
    return positive, negative


def _build_verdict(*, ben: HexagramInfo, lines: list[ZhouyiLine]) -> Verdict:
    """装配结论卡片：卦辞（含用九用六）+ 动爻爻辞的断辞净值折算倾向分。

    无动爻时只数卦辞（丁组 spec 旧裁定「无动爻只用卦辞」的沿用）；headline/advice
    全部来自 `zhouyi_plain` 的受控框架句，本函数不现编中文。
    """
    gua_pos, gua_neg = _duanci_counts(ben.gua_ci + (ben.yong_ci or ""))
    moving_text = "".join(line.yao_ci for line in lines if line.moving)
    yao_pos, yao_neg = _duanci_counts(moving_text) if moving_text else (0, 0)
    net = (gua_pos + yao_pos) - (gua_neg + yao_neg)
    score = min(100.0, max(0.0, _DUANCI_BASE + net * _DUANCI_WEIGHT))
    grade, stars = grade_for(score)
    headline = overview(ZHOUYI_VERDICT_SUMMARY_FRAME, {
        "grade": grade,
        "gua_pos": str(gua_pos),
        "gua_neg": str(gua_neg),
        "yao_pos": str(yao_pos),
        "yao_neg": str(yao_neg),
        "outlook": ZHOUYI_VERDICT_OUTLOOK[grade],
    })
    points = [
        f"卦辞断辞：正向{gua_pos}条、负向{gua_neg}条",
        (f"动爻爻辞断辞：正向{yao_pos}条、负向{yao_neg}条" if moving_text
         else "六爻安静：无动爻爻辞可断"),
        f"正向合计{gua_pos + yao_pos}条、负向合计{gua_neg + yao_neg}条，净值{net:+d}",
    ]
    return Verdict(
        grade=grade,
        stars=stars,
        headline=headline,
        points=points,
        advice=ZHOUYI_VERDICT_ADVICE[grade],
    )


# --- Public entry point -----------------------------------------------------


def cast_hexagram(
    *,
    method: CastMethod | str,
    manual_coins: list[list[int]] | None = None,
    question: str | None = None,
    cast_time: datetime,
) -> ZhouyiCast:
    """Cast a hexagram and return the full Liuyao derivation.

    ``cast_time`` is required so the engine stays deterministic and pure; the
    HTTP adapter supplies the caller's time or the current moment. It fixes the
    day pillar (for 六神) and, for the ``time`` method, the lunar numbers.
    """
    method = CastMethod(method)

    lunar = Solar.fromDate(cast_time).getLunar()
    day_ganzhi = lunar.getDayInGanZhi()
    day_gan = day_ganzhi[0]

    values = _cast_values(method, manual_coins, lunar)
    bits, moving_positions = _split_values(values)

    ben = hexagram_from_lines(tuple(bits))
    bian = hexagram_from_lines(tuple(_apply_moving_lines(bits, moving_positions))) if moving_positions else None
    # 互卦: nuclear trigrams from lines 2-3-4 (lower) and 3-4-5 (upper).
    hu = hexagram_from_trigrams(tuple(bits[1:4]), tuple(bits[2:5]))

    najia = najia_for_hexagram(ben.lower, ben.upper)
    liushen = liushen_for_day_gan(day_gan)

    lines = [
        ZhouyiLine(
            position=position,
            value=value,
            yin_yang="yang" if bit else "yin",
            symbol=_LINE_SYMBOL[bit],
            moving=position in moving_positions,
            stem=najia[position - 1][0],
            branch=najia[position - 1][1],
            branch_element=ZHI_ELEMENT[najia[position - 1][1]],
            liuqin=_liuqin(ben.palace_element, ZHI_ELEMENT[najia[position - 1][1]]),
            liushen=liushen[position - 1],
            is_shi=position == ben.shi,
            is_ying=position == ben.ying,
            yao_name=zhouyi_text.line_name(position, bool(bit)),
            yao_ci=zhouyi_text.yao_ci(ben.number, position),
            plain_yao_ci=reading(ZHOUYI, yao_ci_key(ben.number, position)),
        )
        for position, (value, bit) in enumerate(zip(values, bits), start=1)
    ]

    # 整卦白话先于逐爻细节：一段本卦总论；有动爻时再补一段「转过去之后」的变卦总论。
    plain = [
        PlainSection(
            title="本卦总论",
            text=reading(ZHOUYI, overall_key(ben.number)),
        )
    ]
    if bian is not None:
        count = ("一", "两", "三", "四", "五", "六")[len(moving_positions) - 1]
        plain.append(
            PlainSection(
                title="变卦去向",
                text=overview(ZHOUYI_MOVE_FRAME, {"count": count})
                + "\n"
                + reading(ZHOUYI, overall_key(bian.number)),
            )
        )

    ben_info = _hexagram_info(ben)
    return ZhouyiCast(
        method=method.value,
        question=question,
        cast_time=cast_time.strftime("%Y-%m-%d %H:%M"),
        day_ganzhi=day_ganzhi,
        ben=ben_info,
        bian=_hexagram_info(bian) if bian is not None else None,
        hu=_hexagram_info(hu),
        plain=plain,
        moving_positions=moving_positions,
        lines=lines,
        verdict=_build_verdict(ben=ben_info, lines=lines),
        provenance=zhouyi_provenance(),
    )


def zhouyi_provenance() -> ZhouyiProvenance:
    """响应自带出处：五张表全取自 `ZHOUYI_CONTENT_SOURCES`，本模块不列第二遍表名。

    `engine` 这一格写的是历法事实来自哪个库，不是本端点的推导器名（那是顶层
    `ZhouyiCast.engine`）；值取内联字面量而不学 `engines/meihua.py` 提一个 `ENGINE_LUNAR`——
    三处八字装配都是内联写法（`engines/bazi.py:352`、`engines/bazi_liuri.py:285`、
    `engines/bazi_transit.py:793`），为一个 12 字符串改 `core/provenance.py` 是拿跨层依赖换
    一个常量（AGENTS §1），复测：`cd backend && grep -rn 'engine="lunar-python"' app/engines/bazi*.py`。
    """
    return ZhouyiProvenance(
        engine="lunar-python",
        content_version=CONTENT_VERSION,
        tables=[
            ProvenanceTable(name=module, version=CONTENT_VERSION, source=source)
            for module, source in ZHOUYI_CONTENT_SOURCES
        ],
    )
