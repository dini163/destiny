"""毕达哥拉斯数字命理引擎（spec §6）。

纯函数：只做算术与选句。所有断语来自 `content/numerology_*`，本模块不组任何新句子；
所有约简都过 `reduce_number` 这**一个**入口，于是"主数在哪保留、在哪不保留"是一处
可审计的决定，而不是散落在各处的 `if n == 11`（决策 3）。

本系统无天文、无随机、无外部依赖：同一输入永远同一输出，且每一步都进账本、都能被
读者拿计算器复核（决策 5）。这也是它唯一真正的失效模式 —— 静默地印出一个看似合理的
错数 —— 的解药。设计稿就是活例：它把表达数、灵魂冲动数、人格面具数三个全印错了，
而每个数各自印出的算式与它自己的结论互相矛盾。

**不实现**"全数字累加法"的生命灵数变体。Decoz 明确判它为错法（spec §2.2）：末位数字
有时凑巧相同，但中间的双位数错了，于是会漏掉主数与业力债。不是"算了但不显示"，
而是根本不存在这个函数，免得日后有人误用。
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date

from app.content import CONTENT_VERSION, NUMEROLOGY_CONTENT_SOURCES
from app.content.numerology_cycles import (
    CHALLENGE_DURATION,
    CHALLENGE_DURATIONS,
    CHALLENGE_MEANINGS,
    PERSONAL_CYCLE_MEANINGS,
    PINNACLE_AGE_RULE,
    PINNACLE_MEANINGS,
    cycles_source,
)
from app.content.numerology_loshu import (
    LOSHU_SOURCE,
    LOSHU_SQUARE,
    MISSING_NUMBER_MEANINGS,
    PLANES,
    loshu_source,
)
from app.content.numerology_meanings import (
    CORE_MEANINGS,
    KARMIC_DEBT_MEANINGS,
    KARMIC_LESSONS,
    meanings_source,
)
from app.content.numerology_pythagorean import (
    KARMIC_DEBT_NUMBERS,
    LETTER_VALUES,
    MASTER_NUMBERS,
    PYTHAGOREAN_SOURCE,
    VALUE_GROUPS,
    VOWELS,
    letter_value,
)
from app.core.errors import NumerologyInputError
from app.engines.plain_compose import overview
from app.schemas.common import ProvenanceTable
from app.schemas.numerology import (
    Challenge,
    CoreNumber,
    DigitMeaning,
    GridCell,
    KarmicDebt,
    LetterMapGroup,
    LetterValue,
    LoshuGrid,
    LoshuPlane,
    NumberGrid,
    NumerologyChart,
    NumerologyInput,
    NumerologyProvenance,
    PersonalCycle,
    PersonalCycles,
    Pinnacle,
    ReductionStep,
)

#: 六个核心数的固定渲染序（spec §7）。前端照此序出卡，不自己排。
CORE_KEYS: tuple[str, ...] = (
    "life_path",
    "expression",
    "soul_urge",
    "personality",
    "birthday",
    "maturity",
)

CORE_LABELS: dict[str, str] = {
    "life_path": "生命灵数 Life Path",
    "expression": "表达数 Expression",
    "soul_urge": "灵魂冲动数 Soul Urge",
    "personality": "人格面具数 Personality",
    "birthday": "生日数 Birthday",
    "maturity": "成熟数 Maturity",
}

#: 总和为 0 时的留空理由（决策 17）。理由必须说清"为什么不是 0"，否则读者会以为
#: 系统漏算了；`SOUL_URGE_HINT` 只在 Y 按辅音处理时追加，因为那时它才是可操作的建议。
SOUL_URGE_UNAVAILABLE = "姓名里没有计入元音的字母，灵魂冲动数的总和为 0 —— 0 不在毕达哥拉斯释义体系的值域内，故不取数。"
SOUL_URGE_HINT = "若 Y 在此名中作元音用（如 Lynn、Bryan），可打开「Y 计为元音」重算。"
PERSONALITY_UNAVAILABLE = "姓名里没有辅音字母，人格面具数的总和为 0 —— 0 不在毕达哥拉斯释义体系的值域内，故不取数。"

#: 四顶峰 / 四挑战 / 个人周期的固定渲染序与中英双名。前端照此序出卡，不自己排。
PINNACLE_KEYS: tuple[str, ...] = ("first", "second", "third", "fourth")
PINNACLE_LABELS: dict[str, str] = {
    "first": "第一顶峰 First Pinnacle",
    "second": "第二顶峰 Second Pinnacle",
    "third": "第三顶峰 Third Pinnacle",
    "fourth": "第四顶峰 Fourth Pinnacle",
}

CHALLENGE_KEYS: tuple[str, ...] = ("first", "second", "main", "fourth")
CHALLENGE_LABELS: dict[str, str] = {
    "first": "第一挑战 First Challenge",
    "second": "第二挑战 Second Challenge",
    "main": "主挑战 Main Challenge",
    "fourth": "第四挑战 Fourth Challenge",
}

CYCLE_KEYS: tuple[str, ...] = ("previous_year", "year", "next_year", "month", "day")
CYCLE_LABELS: dict[str, str] = {
    "previous_year": "个人流年（前一年）",
    "year": "个人流年（本年）",
    "next_year": "个人流年（次年）",
    "month": "个人流月（本月）",
    "day": "个人流日（今日）",
}

#: 生日 `YYYY-MM-DD` 八个数位各自的位置名。洛书九宫的 `tokens` 用它，好让每格计数
#: 都能被读者拿自己的生日逐位复核（决策 10）—— 印一个光秃秃的数字等于没给凭据。
#: `date.isoformat()` 永远把年补到四位，故本表恒与数位一一对应。
LOSHU_POSITIONS: tuple[str, ...] = (
    "年千位",
    "年百位",
    "年十位",
    "年个位",
    "月十位",
    "月个位",
    "日十位",
    "日个位",
)

#: 溯源卡里的方法标识。决策 16：设计稿那个 `-9405` 流水号每人不同又无任何推导依据，
#: 只能靠编，编了就是 mock 数据，故只印方法名。
ARCHIVE_BADGE = "#NUMERO-PYTHAG"

ENGINE_STATEMENT = "毕达哥拉斯数理（本仓纯算术实现）：无历法库、无星历、无随机，同输入恒同输出。"

#: 方法声明。全模块**唯一**一处拼接文本，且只拼规则（算式与时段口径），不拼任何释义 ——
#: 把规则原文下发，读者才能拿它核对响应里的数字（决策 5）。
METHOD_STATEMENT = (
    "生命灵数 = reduce(月) + reduce(日) + reduce(年) 再约简（三个分量各自先约简，不用全数字"
    "累加法）；表达数 = 全字母值总和；灵魂冲动数 = 元音和；人格面具数 = 辅音和；"
    "生日数 = reduce(日)；成熟数 = reduce(生命灵数 + 表达数)。主数 11/22/33 一律保留，"
    "唯一例外是四挑战。" + PINNACLE_AGE_RULE + CHALLENGE_DURATION
)


@dataclass(frozen=True)
class Reduced:
    """一次约简的结果：保留主数的值、永远是个位的根、以及可复核的账本。"""

    value: int
    root: int
    steps: tuple[ReductionStep, ...]


def _is_terminal(total: int, keep_master: bool) -> bool:
    return total < 10 or (keep_master and total in MASTER_NUMBERS)


def _digits(total: int) -> list[int]:
    return [int(char) for char in str(total)]


def _row(label: str, expression: str, total: int, reduced: int, debt: bool) -> ReductionStep:
    return ReductionStep(
        label=label, expression=expression, total=total, reduced=reduced, karmic_debt=debt
    )


def reduce_number(
    total: int,
    *,
    keep_master: bool = True,
    label: str = "",
    expression: str | None = None,
    detect_karmic_debt: bool = False,
) -> Reduced:
    """全系统唯一的约简实现（spec §6.1）。

    * `keep_master=False` 是唯一的例外通道，只给四挑战用（决策 3）。
    * `label` 写进每一行账本；`expression` 只覆盖**第一行**的算式串 —— 生命灵数的相加行
      需要它：默认会把 15 拆成 `1+5`，而读者要验算的是 `5+5+5=15`，两个都对，但只有
      后者能对上上一行。
    * `detect_karmic_debt` 默认关。业力债只认生命灵数的**相加行**（spec §6.8）：
      1990 的年行中途会出现 19，若不关就会多报一个 Decoz 本人也没报的业力债。
    * `total < 1` 抛错而不返回 0（决策 17）：0 查无释义，静默返回它就等于印出一个
      不存在的数。

    `root` 由本函数自己再调一次 `keep_master=False` 得出，而不是另写一份取根逻辑 ——
    "引擎里不允许出现第二处约简实现"这条规矩对根同样适用。
    """
    if total < 1:
        raise ValueError(f"约简只接受正整数，收到 {total}（spec 决策 17）")

    steps: list[ReductionStep] = []
    override = expression
    current = total
    if _is_terminal(current, keep_master):
        steps.append(
            _row(
                label,
                override or str(current),
                current,
                current,
                detect_karmic_debt and current in KARMIC_DEBT_NUMBERS,
            )
        )
    while not _is_terminal(current, keep_master):
        nxt = sum(_digits(current))
        steps.append(
            _row(
                label,
                override or "+".join(str(digit) for digit in _digits(current)),
                current,
                nxt,
                detect_karmic_debt and current in KARMIC_DEBT_NUMBERS,
            )
        )
        current = nxt
        override = None

    root = current if current < 10 else reduce_number(current, keep_master=False).value
    return Reduced(value=current, root=root, steps=tuple(steps))


@dataclass(frozen=True)
class NameLetters:
    """姓名拆字的结果。`letter_total` 独立求和，不由两个分项相加得出。

    这不是冗余：`vowel_total + consonant_total == letter_total` 是毕达哥拉斯体系的
    结构性质，也是本切片最重要的一条不变式。若这里用加法赋值，那条测试就只是在
    验证 Python 会做加法。
    """

    letters: tuple[LetterValue, ...]
    skipped_chars: tuple[str, ...]
    skipped_count: int
    vowel_total: int
    consonant_total: int
    letter_total: int


def split_letters(full_name: str, *, y_as_vowel: bool = False) -> NameLetters:
    """把姓名拆成可计数的字母，并如实记下跳过了什么（决策 7/8）。

    一个拉丁字母都没有时报 422 域错误，而不是返回一份全零结果：那样一来"输错了"与
    "算出来了"在响应上完全同形，用户永远不会发现该改用拼音。
    """
    vowels = VOWELS | {"Y"} if y_as_vowel else VOWELS
    letters: list[LetterValue] = []
    skipped: list[str] = []
    for char in full_name:
        upper = char.upper()
        if upper not in LETTER_VALUES:
            skipped.append(char)
            continue
        letters.append(
            LetterValue(char=upper, value=letter_value(upper), is_vowel=upper in vowels)
        )

    if not letters:
        raise NumerologyInputError(
            f"「{full_name}」里没有可计算的拉丁字母。毕达哥拉斯 1–9 映射只定义在 A–Z 上，"
            "请改用拼音或英文名。",
            {"field": "full_name", "chars": list(full_name)},
        )

    return NameLetters(
        letters=tuple(letters),
        skipped_chars=tuple(sorted(set(skipped))),
        skipped_count=len(skipped),
        vowel_total=sum(item.value for item in letters if item.is_vowel),
        consonant_total=sum(item.value for item in letters if not item.is_vowel),
        letter_total=sum(item.value for item in letters),
    )


def _card(key: str, reduced: Reduced, *, lead: tuple[ReductionStep, ...] = ()) -> CoreNumber:
    """约简结果 → 一张核心数卡。释义只从 `CORE_MEANINGS` 取，本函数不组句。"""
    meaning = CORE_MEANINGS[reduced.value]
    return CoreNumber(
        key=key,
        label=CORE_LABELS[key],
        value=reduced.value,
        root=reduced.root,
        is_master=reduced.value in MASTER_NUMBERS,
        master_title=meaning.master_title,
        meaning=meaning.essence,
        keywords=list(meaning.keywords),
        talent=meaning.talent,
        challenge=meaning.challenge,
        steps=(*lead, *reduced.steps),
        source=meaning.source,
    )


def _blank(key: str, reason: str) -> CoreNumber:
    """总和为 0 时的占位卡：行恒在，值可缺（决策 17，形状沿用姓名学的 `NameGrid`）。"""
    return CoreNumber(
        key=key,
        label=CORE_LABELS[key],
        is_master=False,
        unavailable_reason=reason,
        source=PYTHAGOREAN_SOURCE,
    )


def _value_of(card: CoreNumber) -> int:
    """取一张卡的数值；为 `None` 就是本模块自己算错了。

    成熟数要把生命灵数与表达数相加，而两者的 `value` 在类型上都是 `int | None`
    （灵魂冲动数与人格面具数才真的可能为空）。与其把 `None` 默默传染成算术错误，
    不如在这里当场炸 —— 这两个数永远不该为空，一旦为空就是上游改了口径。
    """
    if card.value is None:
        raise AssertionError(f"{card.key} 的数值不该为空")
    return card.value


def life_path(birth_date: date) -> tuple[CoreNumber, tuple[KarmicDebt, ...]]:
    """生命灵数：先把月、日、年**各自**约简，再相加、再约简（spec §2.2 的唯一正确法）。

    账本行序与相加算式都按 Decoz 的 `M + D + Y`，不按日期的书写序 —— 让算式与来源
    逐字一致，读者拿他的原文就能核对。
    """
    month = reduce_number(birth_date.month, label="月")
    day = reduce_number(birth_date.day, label="日")
    year = reduce_number(birth_date.year, label="年")
    summed = reduce_number(
        month.value + day.value + year.value,
        label="相加",
        expression=f"{month.value}+{day.value}+{year.value}",
        detect_karmic_debt=True,
    )
    card = _card("life_path", summed, lead=(*month.steps, *day.steps, *year.steps))
    debts = tuple(
        KarmicDebt(
            number=step.total,
            label=step.label,
            expression=step.expression,
            meaning=KARMIC_DEBT_MEANINGS[step.total],
            source=meanings_source(f"业力债{step.total}"),
        )
        for step in summed.steps
        if step.karmic_debt
    )
    return card, debts


def _sum_card(
    key: str,
    total: int,
    label: str,
    addends: Sequence[int],
    unavailable: str = "",
) -> CoreNumber:
    """一类核心数的公共形状：总和为 0 就留空，否则把加数逐个印进算式里。

    `unavailable` 只给真的可能为 0 的两项（灵魂冲动数、人格面具数）；其余四项不传，
    因为它们为空就意味着上游已经算错了。
    """
    if total < 1:
        return _blank(key, unavailable)
    expression = "+".join(str(addend) for addend in addends)
    return _card(key, reduce_number(total, label=label, expression=expression))


@dataclass(frozen=True)
class CoreResult:
    letters: NameLetters
    core: tuple[CoreNumber, ...]
    karmic_debts: tuple[KarmicDebt, ...]


def core_numbers(
    full_name: str, birth_date: date, *, y_as_vowel: bool = False
) -> CoreResult:
    """六个核心数，固定序（spec §6.2）。

    成熟数吃的是生命灵数与表达数的 **`value`**（保留主数）而不是 `root`：6 与 5 相加
    得 11，11 是主数就不再约简，故主角的成熟数是 11/2 —— 设计稿印的 8 正是因为它喂了
    一个伪造的表达数 2（spec §2.4 偏差 B）。
    """
    letters = split_letters(full_name, y_as_vowel=y_as_vowel)
    life, debts = life_path(birth_date)

    soul_reason = SOUL_URGE_UNAVAILABLE + ("" if y_as_vowel else SOUL_URGE_HINT)
    expression = _sum_card(
        "expression",
        letters.letter_total,
        "全字母",
        [item.value for item in letters.letters],
    )
    soul_urge = _sum_card(
        "soul_urge",
        letters.vowel_total,
        "元音",
        [item.value for item in letters.letters if item.is_vowel],
        soul_reason,
    )
    personality = _sum_card(
        "personality",
        letters.consonant_total,
        "辅音",
        [item.value for item in letters.letters if not item.is_vowel],
        PERSONALITY_UNAVAILABLE,
    )
    birthday = _card("birthday", reduce_number(birth_date.day, label="日"))
    maturity = _sum_card(
        "maturity",
        _value_of(life) + _value_of(expression),
        "成熟",
        [_value_of(life), _value_of(expression)],
    )

    return CoreResult(
        letters=letters,
        core=(life, expression, soul_urge, personality, birthday, maturity),
        karmic_debts=debts,
    )


# ------------------------------------------------------------------ 周岁与四顶峰（§6.3）


def _base_part(raw: int, label: str, *, keep_master: bool) -> tuple[int, str]:
    """把一个日期分量约简成基底值，并给出可核对的算式片段。

    片段里印**完整约简链**（`年 1990→19→10→1`）而不是只印结果：顶峰与挑战两张卡都不带
    `steps`，账本压不进模型就必须压在算式里。少印一环，读者就得自己重算 —— 而「没人能
    复核」正是设计稿那些数一直没被抓住的原因（spec §2.4）。
    """
    reduced = reduce_number(raw, keep_master=keep_master, label=label)
    if reduced.value == raw:
        return raw, f"{label} {raw}"
    chain = "→".join([*(str(step.total) for step in reduced.steps), str(reduced.value)])
    return reduced.value, f"{label} {chain}"


def _sum_expression(left: str, right: str, total: int, value: int) -> str:
    """`A + B = 和`；和若还要再约就补一段 ` → 值`。主数是和本身时不补箭头。"""
    return f"{left} + {right} = {total}" + ("" if value == total else f" → {value}")


def age_at(birth_date: date, reference: date) -> int | None:
    """周岁。基准日早于生日时返回 `None`。

    不填 0 也不填负数：0 会读成「刚出生」，而一个负数年龄会一路流进顶峰年龄轴的判定里，
    最后印出「当前在第一顶峰」这种看着完全正常的错话。
    """
    if reference < birth_date:
        return None
    reached = (reference.month, reference.day) >= (birth_date.month, birth_date.day)
    return reference.year - birth_date.year - (0 if reached else 1)


def pinnacle_ages(life_path_root: int) -> tuple[tuple[int, int | None], ...]:
    """顶峰年龄轴的唯一实现（spec §6.3）。

    `first_end = 36 − 生命灵数之根`：Decoz 原文括注要求主数先约到个位，故这里吃的是
    `root` 而不是 `value`。第四程 `end_age` 是 `None`（「至终生」），不填 999 之类的假值。
    """
    first_end = 36 - life_path_root
    return (
        (0, first_end),
        (first_end + 1, first_end + 9),
        (first_end + 10, first_end + 18),
        (first_end + 19, None),
    )


def _segment_index(
    segments: Sequence[tuple[int, int | None]], age: int | None
) -> int | None:
    if age is None:
        return None
    for index, (start, end) in enumerate(segments):
        if start <= age and (end is None or age <= end):
            return index
    return None


def pinnacles(birth_date: date, *, reference_date: date | None = None) -> tuple[Pinnacle, ...]:
    """四顶峰（spec §6.3）：`P1=M+D`、`P2=D+Y`、`P3=P1+P2`、`P4=M+Y`，基底与各和都保留主数。

    年龄轴吃的生命灵数之根由 `reduce_number(月+日+年, keep_master=False)` 得出，而不是去
    拆 `life_path()` 那张卡：数字根对逐位相加是不变的，两条路必得同一个根，而单测正是拿
    两者对拍 —— 一旦有人改了其中一条口径，那条测试会先炸。
    """
    reference = reference_date or date.today()
    month, month_part = _base_part(birth_date.month, "月", keep_master=True)
    day, day_part = _base_part(birth_date.day, "日", keep_master=True)
    year, year_part = _base_part(birth_date.year, "年", keep_master=True)

    first = reduce_number(month + day, label="第一顶峰")
    second = reduce_number(day + year, label="第二顶峰")
    third = reduce_number(first.value + second.value, label="第三顶峰")
    fourth = reduce_number(month + year, label="第四顶峰")
    life_root = reduce_number(month + day + year, keep_master=False, label="生命灵数根").value

    segments = pinnacle_ages(life_root)
    current = _segment_index(segments, age_at(birth_date, reference))
    lefts = (month_part, day_part, f"第一顶峰 {first.value}", month_part)
    rights = (day_part, year_part, f"第二顶峰 {second.value}", year_part)
    reduced_values = (first, second, third, fourth)
    return tuple(
        Pinnacle(
            index=index + 1,
            key=key,
            label=PINNACLE_LABELS[key],
            value=reduced.value,
            root=reduced.root,
            is_master=reduced.value in MASTER_NUMBERS,
            expression=_sum_expression(
                lefts[index], rights[index], reduced.steps[0].total, reduced.value
            ),
            start_age=segments[index][0],
            end_age=segments[index][1],
            is_current=index == current,
            meaning=PINNACLE_MEANINGS[reduced.value],
            source=cycles_source(f"顶峰{reduced.value}"),
        )
        for index, (key, reduced) in enumerate(
            zip(PINNACLE_KEYS, reduced_values, strict=True)
        )
    )


def current_pinnacle(items: Sequence[Pinnacle], age: int | None) -> Pinnacle | None:
    """按响应里印出的年龄轴判当前段；周岁未知或落不到任何一段时返回 `None`。

    它读的是 `items` 自己的 `start_age/end_age`，而不是内部那份 `segments`：于是它同时也在
    核对「下发的年龄轴与 `is_current` 标记一致」。单测正是这么用它的 —— 只测标记就测不出
    轴算错了，只测查找就测不出标记错了。
    """
    if age is None:
        return None
    for item in items:
        if item.start_age <= age and (item.end_age is None or age <= item.end_age):
            return item
    return None


# ------------------------------------------------------------------ 四挑战（§6.4）


def challenges(birth_date: date) -> tuple[Challenge, ...]:
    """四挑战（spec §6.4）。全系统唯一把主数约简掉的地方：三个基底都传 `keep_master=False`。

    差值本身**不过 `reduce_number`**：`|5−5| = 0`，而 0 被那个入口拒收（决策 17）。但 0 在
    这里是值域的真实成员（Decoz：「The 0 (zero) Challenge is very common」），不是缺失值，
    故四张卡各自照样给释义。主角的月日年约简后同为 5，四挑战因此全 0 —— 设计稿印的
    1/0/1/0 不可能来自任何算式（spec §2.4）。
    """
    month, month_part = _base_part(birth_date.month, "月", keep_master=False)
    day, day_part = _base_part(birth_date.day, "日", keep_master=False)
    year, year_part = _base_part(birth_date.year, "年", keep_master=False)
    first = abs(month - day)
    second = abs(day - year)
    values = {
        "first": first,
        "second": second,
        "main": abs(first - second),
        "fourth": abs(month - year),
    }
    expressions = {
        "first": f"|{month_part} − {day_part}| = {first}",
        "second": f"|{day_part} − {year_part}| = {second}",
        "main": f"|第一挑战 {first} − 第二挑战 {second}| = {values['main']}",
        "fourth": f"|{month_part} − {year_part}| = {values['fourth']}",
    }
    return tuple(
        Challenge(
            index=index + 1,
            key=key,
            label=CHALLENGE_LABELS[key],
            value=values[key],
            expression=expressions[key],
            duration=CHALLENGE_DURATIONS[key],
            meaning=CHALLENGE_MEANINGS[values[key]],
            source=cycles_source(f"挑战{values[key]}"),
        )
        for index, key in enumerate(CHALLENGE_KEYS)
    )


# ------------------------------------------------------------------ 个人周期（§6.7）


def _personal_cycle(key: str, period: str, addends: Sequence[Reduced]) -> PersonalCycle:
    """一个个人周期：基底各自约简（保留主数），相加行也保留主数（决策 11）。

    相加行的算式印**各基底约简后的值**（`5+5+1`），与生命灵数相加行同一个理由：读者要能
    对上上一行（spec §6.1 补记）。释义三处共用 `PERSONAL_CYCLE_MEANINGS`：流月/流日只有
    两个加数，值域是流年的子集，故一张表就盖得住（由语料单测按算式反推锁死）。那张表的
    每条释义都是**尺度中立**的，尺度由本函数填的 `label` 提供 —— 出处后缀也跟着写
    「个人周期」而不是「流年」：它引的就是那张共用表，写成流年在流月卡上就是假话。
    """
    summed = reduce_number(
        sum(item.value for item in addends),
        label="相加",
        expression="+".join(str(item.value) for item in addends),
    )
    return PersonalCycle(
        key=key,
        label=CYCLE_LABELS[key],
        period=period,
        value=summed.value,
        root=summed.root,
        is_master=summed.value in MASTER_NUMBERS,
        meaning=PERSONAL_CYCLE_MEANINGS[summed.value],
        steps=[*(step for item in addends for step in item.steps), *summed.steps],
        source=cycles_source(f"个人周期{summed.value}"),
    )


def personal_cycles(birth_date: date, *, reference_date: date | None = None) -> PersonalCycles:
    """个人流年三轮 + 流月 + 流日（spec §6.7、决策 11）。

    `PM = root(PY) + reduce(目标月)`、`PD = root(PM) + reduce(目标日)`：链是真的接上的，故
    流月账本的第一行就是流年那个值被约成根 —— 读者能顺着账本一路走回生日。
    前后年三轮一并给，是为了让读者看出自己处在九年周期的哪一步（单给一年看不出）。
    """
    reference = reference_date or date.today()
    month = reduce_number(birth_date.month, label="出生月")
    day = reduce_number(birth_date.day, label="出生日")

    def year_cycle(key: str, target: int) -> PersonalCycle:
        return _personal_cycle(
            key,
            str(target),
            (month, day, reduce_number(target, label=f"目标年 {target}")),
        )

    year = year_cycle("year", reference.year)
    month_root = reduce_number(year.value, keep_master=False, label="个人年根")
    month_cycle = _personal_cycle(
        "month",
        f"{reference.year:04d}-{reference.month:02d}",
        (month_root, reduce_number(reference.month, label=f"目标月 {reference.month}")),
    )
    day_root = reduce_number(month_cycle.value, keep_master=False, label="个人月根")
    day_cycle = _personal_cycle(
        "day",
        reference.isoformat(),
        (day_root, reduce_number(reference.day, label=f"目标日 {reference.day}")),
    )
    return PersonalCycles(
        previous_year=year_cycle("previous_year", reference.year - 1),
        year=year,
        next_year=year_cycle("next_year", reference.year + 1),
        month=month_cycle,
        day=day_cycle,
    )


# ------------------------------------------------------------------ 两套九宫（§6.5/§6.6）


def _cells(tokens: dict[int, list[str]]) -> list[GridCell]:
    """九格的公共形状：按 1..9 升序，摆成洛书方阵是 `layout` 的事。"""
    return [
        GridCell(digit=digit, count=len(found), tokens=found) for digit, found in tokens.items()
    ]


def name_grid(letters: NameLetters) -> NumberGrid:
    """姓名天赋九宫与业力课（spec §6.5、决策 9）。

    与 `loshu_grid` **刻意分开**：这一张数的是姓名字母值，缺数叫业力课，释义取
    `KARMIC_LESSONS`；那一张数的是生日的字面数字，缺数取 `MISSING_NUMBER_MEANINGS`。
    合成一张表就是设计稿犯的那个错，它因此同时印错了两处（§2.4）。

    `total` 取的是字母数而不是各格计数之和：两者相等是本函数的不变式，用加法赋值
    就把那条测试降级成了「验证 Python 会做加法」（同 `NameLetters.letter_total` 的理由）。
    """
    tokens: dict[int, list[str]] = {digit: [] for digit in range(1, 10)}
    for item in letters.letters:
        tokens[item.value].append(item.char)
    cells = _cells(tokens)
    return NumberGrid(
        cells=cells,
        layout=[list(row) for row in LOSHU_SQUARE],
        total=len(letters.letters),
        karmic_lessons=[
            DigitMeaning(
                digit=cell.digit,
                meaning=KARMIC_LESSONS[cell.digit],
                source=meanings_source(f"业力课{cell.digit}"),
            )
            for cell in cells
            if cell.count == 0
        ],
        source=PYTHAGOREAN_SOURCE,
    )


def loshu_grid(birth_date: date) -> LoshuGrid:
    """生辰洛书九宫与八平面（spec §6.6、决策 10/12）。

    只吃生日的**字面数字**：有些流派会额外塞进约简后的生命灵数，各家不一，塞进来就
    再也无法用生日逐位复核了。0 不计（洛书无 0 格），但 `zero_count` 如实报出 —— 少一个 0
    与多一个 0 都会让读者对不上自己的生日。

    `line_sums` 一并下发：幻方性质不只藏在后端单测里，响应自己就能被核对（决策 12）。
    """
    digits = [int(char) for char in birth_date.isoformat() if char.isdigit()]
    tokens: dict[int, list[str]] = {digit: [] for digit in range(1, 10)}
    for position, digit in zip(LOSHU_POSITIONS, digits, strict=True):
        if digit:
            tokens[digit].append(f"{position} {digit}")
    cells = _cells(tokens)
    counts = {cell.digit: cell.count for cell in cells}

    planes: list[LoshuPlane] = []
    for plane in PLANES:
        missing = [digit for digit in plane.cells if not counts[digit]]
        planes.append(
            LoshuPlane(
                key=plane.key,
                name_zh=plane.name_zh,
                name_en=plane.name_en,
                cells=list(plane.cells),
                complete=not missing,
                missing=missing,
                # 引擎只选句：齐就读 `present_text`，缺就读 `missing_text`，不拼不改写。
                text=plane.present_text if not missing else plane.missing_text,
                source=plane.source,
            )
        )

    return LoshuGrid(
        cells=cells,
        layout=[list(row) for row in LOSHU_SQUARE],
        total=len([digit for digit in digits if digit]),
        zero_count=digits.count(0),
        digits=digits,
        missing=[
            DigitMeaning(
                digit=cell.digit,
                meaning=MISSING_NUMBER_MEANINGS[cell.digit],
                source=loshu_source(f"缺数{cell.digit}"),
            )
            for cell in cells
            if cell.count == 0
        ],
        planes=planes,
        line_sums=[sum(plane.cells) for plane in PLANES],
        source=LOSHU_SOURCE,
    )


# ------------------------------------------------------------------ 总装与溯源（§7）


def numerology_provenance(reference: date) -> NumerologyProvenance:
    """响应自带出处：语料版本 + 四张表，表列全部来自 `NUMEROLOGY_CONTENT_SOURCES`。

    不在此处把表名再列一次：语料模块里写一次、这里再写一次，两处就会各自漂移（同
    `NATAL_SOURCE_BY_MODULE` 的理由）。本端点无历法库，故 `version` 取本仓语料的滚动版本。
    """
    return NumerologyProvenance(
        reference_date=reference,
        engine=ENGINE_STATEMENT,
        badge=ARCHIVE_BADGE,
        tables=[
            ProvenanceTable(name=module, version=CONTENT_VERSION, source=source)
            for module, source in NUMEROLOGY_CONTENT_SOURCES
        ],
        method=METHOD_STATEMENT,
    )


#: 响应级总论框架句（spec §7 表行 1「全页无总论」的补法）。**本期零新语料**：
#: `{essence}` 逐字搬运 `core[].meaning`，其余三条只报数与位。
#:
#: 为什么不引顶峰/挑战/周期/洛书的原文（G18，用户 2026-10-01 裁定「事实句合并」）：那四类
#: 是建议句，搬进白话块就撞上 spec §5 规则 7「不给建议」，也与页脚免责声明相冲。
#: 实测条数（2026-10-01 实跑，`Liam Alexander Carter` / 1990-05-15）：**16 句**
#: （4 顶峰 + 4 挑战 + 8 洛书平面）里 **13 句**含「宜/忌/需/应」（「宜」9、「需」10，
#: 「忌」「应」各 0）；本段真正会报出的**流年/流月/流日 3 句全含**；六个核心数释义
#: **0/6 含**，所以只有它们能逐字进 `{essence}`。复测：
#: `cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "from app.engines.numerology import compute_chart;from datetime import date;c=compute_chart(full_name='Liam Alexander Carter',birth_date=date(1990,5,15));w=('宜','忌','需','应');s=[*(p.meaning for p in c.pinnacles),*(x.meaning for x in c.challenges),*(p.text for p in c.loshu_grid.planes),*(c.personal_cycles.year.meaning,c.personal_cycles.month.meaning,c.personal_cycles.day.meaning),*(x.meaning for x in c.core if x.meaning)];print(sum(1 for t in s[:16] if any(k in t for k in w)),'/',len(s[:16]));print(sum(1 for t in s[16:19] if any(k in t for k in w)),'/',3);print(sum(1 for t in s[19:] if any(k in t for k in w)),'/',len(s[19:]))"`
#: → `13 / 16`、`3 / 3`、`0 / 6`。
#:
#: 盘面形状复测（同一条输入）：
#: `cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "from app.engines.numerology import compute_chart;from datetime import date; c=compute_chart(full_name='Liam Alexander Carter', birth_date=date(1990,5,15)); print(len(c.core), len(c.pinnacles), len(c.challenges), len(c.loshu_grid.planes), sum(1 for p in c.loshu_grid.planes if p.complete), [x.digit for x in c.loshu_grid.missing])"`
#: → `6 4 4 8 1 [2, 3, 4, 6, 7, 8]`。计划草稿写过「17 条」，实测推翻为 16 句 / 13 含建议词。
#:
#: 段落框架句不住 `content/`（G16）：spec §9 明写本期 `NUMEROLOGY_CONTENT_SOURCES` 不加条目，
#: 而新建一个只装框架句的 content 模块就是「读了新表」。
NUMEROLOGY_SUMMARY_FRAME = (
    "合起来读这一段：\n{essence}\n"
    "顶峰四段的数依次是{pinnacles}。\n"
    "流年与流月、流日的数依次是{cycles}。\n"
    "洛书八条线齐备{loshu}条，缺的数位是{missing}。"
    "这一段只是把上面各栏已经写过的释义与数字重排一遍，没有新增判断，也不替你决定要做什么。"
)


def _essence_lines(core: Sequence[CoreNumber]) -> str:
    """六个核心数逐字搬运，同释义只说一次（R12）；`meaning is None` 的格跳过。

    跳过而不是兜一句：那一格的 `unavailable_reason` 已经写在卡上，白话块再讲一遍就是
    第二处说话的地方。生命灵数恒可算（由生日得），所以 `{essence}` 永不为空，无需 G15
    那条支路句——形状同卡巴拉的 33 格全覆盖。前提由
    `tests/test_numerology.py::test_summary_essence_openers_are_never_empty_so_no_branch_sentence_is_due`
    按名字矩阵逐条钉住，不靠本注释自证。
    """
    seen: dict[str, list[str]] = {}
    order: list[str] = []
    for card in core:
        if card.meaning is None:
            continue
        if card.meaning not in seen:
            seen[card.meaning] = []
            order.append(card.meaning)
        seen[card.meaning].append(f"{card.label} {card.value}")
    return "\n".join(f"{'、'.join(seen[meaning])}——{meaning}" for meaning in order)


def numerology_plain_summary(core: Sequence[CoreNumber], pinnacles: Sequence[Pinnacle],
                             cycles: PersonalCycles, loshu: LoshuGrid) -> str:
    """总论 = `overview(frame, parts)`。部件只含「已经印在别处的释义」与可数的事实。

    三处只报事实的取数口径：顶峰取 `value`（主数原样，11 不折成 2，与
    `schemas/numerology.py:103` 的 `CoreNumber.value` 同一条约定）；周期取 `previous_year`
    之外真正面向读者的三条（year/month/day）及其 `period` 与 `value`；洛书取 `complete`
    计数与 `missing` 的数位。为什么不写「当前落在第几顶峰」：
    `current_pinnacle()`(:541) 在周岁未知或年龄轴未覆盖时返回 `None`，那句话有一条空支路，
    而页面上的 `PinnacleLadder` 已经用 `is_current` 高亮了同一件事（G15 宁缺勿造）。
    """
    return overview(
        NUMEROLOGY_SUMMARY_FRAME,
        {
            "essence": _essence_lines(core),
            "pinnacles": "、".join(f"第 {item.index} 段 {item.value}" for item in pinnacles),
            "cycles": "、".join(
                # 三条事实必须是**序列**而不是一串拼好的文本：`"、".join(单个 f-string)`
                # 会把那个字符串逐字符切开，印出来的是一行乱码。
                (
                    f"{cycles.year.period} 年 {cycles.year.value}",
                    f"{cycles.month.period} 月 {cycles.month.value}",
                    f"{cycles.day.period} 日 {cycles.day.value}",
                )
            ),
            "loshu": str(sum(1 for plane in loshu.planes if plane.complete)),
            # 生日恒为 8 个数字字符，洛书数 1..9 共 9 格，抽屉原理保证缺至少一格，
            # 所以这里不需要「全齐」那条支路句（G15）。含 0 的生日只会缺得更多，
            # 因为洛书无 0 格（`loshu_grid()` 把 0 记进 `zero_count` 而不进九宫）。
            "missing": "、".join(str(item.digit) for item in loshu.missing),
        },
    )


def compute_chart(
    *,
    full_name: str,
    birth_date: date,
    name_zh: str | None = None,
    reference_date: date | None = None,
    y_as_vowel: bool = False,
) -> NumerologyChart:
    """总装（spec §7）。纯计算、无 IO，故 API 层只剩「请求 → 本函数」一层映射。

    本函数里没有任何算术，也没有任何分支（`reference_date or date.today()` 只是个缺省）：
    六段各自独立可测，这里只负责把它们摆进一个响应。一旦它开始长逻辑，就说明那段逻辑
    该挪回上面某个函数。顶峰与周期提成局部再传两遍（一次进响应、一次进白话装配器）不是
    分支也不是第二处计算 —— 白话块吃的必须是同一份 `pinnacles`/`personal_cycles` 产物，
    在构造调用里各写一遍才是两处口径。
    """
    reference = reference_date or date.today()
    result = core_numbers(full_name, birth_date, y_as_vowel=y_as_vowel)
    letters = result.letters
    name_panel = name_grid(letters)
    loshu_panel = loshu_grid(birth_date)
    pinnacle_panel = list(pinnacles(birth_date, reference_date=reference))
    cycle_panel = personal_cycles(birth_date, reference_date=reference)
    return NumerologyChart(
        input=NumerologyInput(
            full_name=full_name,
            name_zh=name_zh,
            birth_date=birth_date,
            reference_date=reference,
            y_as_vowel=y_as_vowel,
            age_at_reference=age_at(birth_date, reference),
            letter_count=len(letters.letters),
            skipped_count=letters.skipped_count,
            skipped_chars=list(letters.skipped_chars),
            vowel_total=letters.vowel_total,
            consonant_total=letters.consonant_total,
            letter_total=letters.letter_total,
        ),
        letters=list(letters.letters),
        # 映射表本身也下发（spec §5.1：`VALUE_GROUPS` 就是为前端那张九列表而存在的）。
        # 照搬语料里的倒排，不在此处由 `LETTER_VALUES` 重算 —— 两份表已由语料测双向锁死，
        # 在这里再推一次只会把「哪份才是真相」重新变成一个问题。
        letter_map=[
            LetterMapGroup(value=value, letters=list(group)) for value, group in VALUE_GROUPS
        ],
        core=list(result.core),
        karmic_debts=list(result.karmic_debts),
        pinnacles=pinnacle_panel,
        challenges=list(challenges(birth_date)),
        personal_cycles=cycle_panel,
        name_grid=name_panel,
        loshu_grid=loshu_panel,
        plain_summary=numerology_plain_summary(
            result.core, pinnacle_panel, cycle_panel, loshu_panel
        ),
        provenance=numerology_provenance(reference),
    )
