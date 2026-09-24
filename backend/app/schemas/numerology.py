"""`POST /api/v1/numerology/chart` 的请求与响应契约（spec §7）。

字段名 snake_case 直通前端，没有映射层。三条纪律贯穿全文件：

1. **没有 `score` 字段**（spec 决策 14）。毕达哥拉斯数理没有权威的吉凶总分传统，
   硬凑一个加权分等于让系统声称古籍替它赋过分。故本模块**不 import** `schemas/scoring`。
2. **没有「均衡度百分比」**（决策 13）。设计稿印的 82% 无任何权威定义。
3. **算不出就 `None`**，前端整块不渲染，绝不出现 `default=0` 这种"看着像值"的占位。
   唯一合法的 0 是挑战数（0 是它值域的真实成员）与九宫计数（0 次本身就是业力课）。

`steps` 是整套契约的核心：前端把设计稿的「约简运算阶梯」**直接渲染**它，不重算任何
算术（决策 5）。所以每一步都自带 `expression` 与 `total`，读者拿计算器就能复核。
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field

from app.schemas.common import ProvenanceTable


class NumerologyChartRequest(BaseModel):
    """入参。

    长度归 pydantic（回 FastAPI 的 `detail` 形状）；「名字里有没有拉丁字母」归引擎
    （回 422 + `numerology_no_latin_letters`），分工同 `NameAnalyzeRequest`。
    """

    full_name: str = Field(
        min_length=1,
        max_length=80,
        description="拉丁字母全名（拼音或英文名）。毕达哥拉斯映射只定义在 A–Z 上。",
    )
    name_zh: str | None = Field(
        default=None,
        max_length=20,
        description="中文名，**仅回显**，不参与任何计算（spec 决策 1）。",
    )
    birth_date: date = Field(description="公历生日。数字命理是西方体系，公历是其原生输入。")
    reference_date: date | None = Field(
        default=None,
        description="个人年/月/日的基准日，缺省取今天；golden 测试靠它固定。",
    )
    y_as_vowel: bool = Field(
        default=False,
        description="Y 是否计入元音（决策 7）。默认按辅音；音节判断不可单测，故交给用户。",
    )


class ReductionStep(BaseModel):
    """约简账本的一行。

    `expression` 是读者能照着按计算器的那一串；`total` 是它加出来的原值；`reduced` 是
    约简后的值（保留主数，除非该行属挑战链）。
    """

    label: str = Field(description="这一行算的是什么：年 / 月 / 日 / 元音 / 辅音 / 相加 …")
    expression: str = Field(description="算式，如 '1+9+9+4'。")
    total: int = Field(description="该算式的和，如约简前的 23。")
    reduced: int = Field(description="约简结果；主数原样保留。")
    karmic_debt: bool = Field(
        default=False,
        description="`total` 是否落在 13/14/16/19 上（spec §6.8）。只在生命灵数链上判。",
    )


class LetterValue(BaseModel):
    """姓名逐字透视的一格（设计稿的「姓名逐字数理加权透视」直接由它渲染）。"""

    char: str = Field(description="大写归一后的字母。")
    value: int = Field(ge=1, le=9)
    is_vowel: bool = Field(description="按本次 `y_as_vowel` 判定；决定它进元音和还是辅音和。")


class CoreNumber(BaseModel):
    """一个核心数，连同它的释义与完整约简账本。

    `value` 可为 `None`（决策 17）：名为 `Lynn` 这种一个元音都没有的名字，灵魂冲动数
    的总和是 0，而 0 不在任何释义表的值域里。此时本卡保留占位（读者看得见"本来该有
    这个数"）、派生字段全为 `None`、`unavailable_reason` 说清原因，前端整块不渲染释义。
    形状沿用姓名学的 `NameGrid`：行恒在，值可缺，绝不填 0 充数。
    """

    key: str = Field(description="life_path / expression / soul_urge / personality / birthday / maturity。")
    label: str = Field(description="中英双名，如「生命灵数 Life Path」。")
    value: int | None = Field(default=None, description="约简后的值；主数原样保留（11 就是 11，不写成 2）。")
    root: int | None = Field(default=None, ge=1, le=9, description="数字根，永远是个位数。前端按 `value /root` 双数字版式渲染。")
    is_master: bool = Field(description="value 是否主数；value 为 None 时恒为 False。")
    master_title: str | None = Field(default=None, description="仅主数有，如「MASTER TEACHER · 精神导师」。")
    meaning: str | None = Field(default=None, description="中性本质释义；「作为生命灵数意味着什么」由前端卡片标题提供。")
    keywords: list[str] = Field(default_factory=list)
    talent: str | None = None
    challenge: str | None = None
    unavailable_reason: str | None = Field(
        default=None,
        description="仅当 `value` 为 None 时有值：说清为什么算不出，而不是静默少一张卡。",
    )
    steps: list[ReductionStep] = Field(default_factory=list)
    source: str


class KarmicDebt(BaseModel):
    """生命灵数约简途中撞上的一个业力债数（spec §6.8）。"""

    number: int = Field(description="13 / 14 / 16 / 19。")
    label: str = Field(description="它出现在哪一步，如「年月日相加」。")
    expression: str = Field(description="产生它的那条算式，供复核。")
    meaning: str
    source: str


class Pinnacle(BaseModel):
    """一程顶峰。`end_age` 为 `None` 表示"无终点"，不填 999 之类的假值（spec §6.3）。"""

    index: int = Field(ge=1, le=4)
    key: str = Field(description="first / second / third / fourth。")
    label: str
    value: int
    root: int = Field(ge=1, le=9)
    is_master: bool
    expression: str = Field(description="算式，如「月 5 + 日 5」。")
    start_age: int = Field(ge=0)
    end_age: int | None = Field(default=None, description="第四顶峰无终点，故为 None。")
    is_current: bool = Field(description="`reference_date` 落在这一段里。")
    meaning: str
    source: str


class Challenge(BaseModel):
    """一个挑战数。

    刻意**不带 `steps`**：挑战链是全系统唯一把主数约简掉的地方（决策 3 的例外），
    若与生命灵数共用同一套账本行，同一个「11 月」会在两处一处显示 11、一处显示 2，
    读者无从判断哪个才是对的。故这里把整条链压进 `expression` 一个字符串里
    （如 `|月 11→2 − 日 6| = 4`），例外本身就写在算式上，不必靠读者记住规则。
    """

    index: int = Field(ge=1, le=4)
    key: str = Field(description="first / second / main / fourth；main 即贯穿一生的主挑战。")
    label: str
    value: int = Field(ge=0, le=8, description="值域 0–8；0 是真实值，不是缺失。")
    expression: str = Field(description="完整链，含基底的主数约简，如 '|月 11→2 − 日 6| = 4'。")
    duration: str = Field(description="来源给的定性时段文本，**不是**精确年份（spec §5.3）。")
    meaning: str
    source: str


class PersonalCycle(BaseModel):
    """个人流年/流月/流日之一。"""

    key: str = Field(description="previous_year / year / next_year / month / day。")
    label: str
    period: str = Field(description="这一轮覆盖的时段，如 '2026' / '2026-09' / '2026-09-24'。")
    value: int
    root: int = Field(ge=1, le=9)
    is_master: bool
    meaning: str
    steps: list[ReductionStep]
    source: str


class PersonalCycles(BaseModel):
    """个人年三轮 + 流月 + 流日（spec 决策 11）。"""

    previous_year: PersonalCycle
    year: PersonalCycle
    next_year: PersonalCycle
    month: PersonalCycle
    day: PersonalCycle


class GridCell(BaseModel):
    """九宫的一格。

    `tokens` 是"这一格的计数是哪些东西贡献的"：姓名九宫里是实际字母（便于逐字复核），
    洛书九宫里是该数字来自生日的哪些位（决策 10：好让计数永远能被读者用生日逐位复核）。
    """

    digit: int = Field(ge=1, le=9)
    count: int = Field(ge=0, description="0 不是缺失值：姓名九宫里 0 次就是业力课。")
    tokens: list[str] = Field(default_factory=list)


class DigitMeaning(BaseModel):
    """一个数位配一句释义。姓名九宫用作业力课，洛书九宫用作缺数解读。"""

    digit: int = Field(ge=1, le=9)
    meaning: str
    source: str


class NumberGrid(BaseModel):
    """姓名天赋九宫（spec §6.5）。

    与 `LoshuGrid` **刻意分成两个模型**：两张九宫的输入不同（姓名字母 vs 生日数字）、
    传统不同（毕达哥拉斯业力课 vs 洛书平面）、缺数释义也不同。合成一张表就是设计稿
    犯的那个错，它因此同时印错了两处（决策 9、spec §2.4）。
    """

    cells: list[GridCell] = Field(description="按 1..9 升序；摆成洛书方阵是 `layout` 的事。")
    layout: list[list[int]] = Field(
        description="九宫的显示摆法（洛书 `4 9 2 / 3 5 7 / 8 1 6`）。由后端下发，"
        "免得前端自己排序时排出设计稿那个非幻方的升序摆法。"
    )
    total: int = Field(ge=0, description="计数合计，恒等于参与计算的字母数。")
    karmic_lessons: list[DigitMeaning] = Field(default_factory=list, description="`count == 0` 的数位。")
    source: str


class LoshuPlane(BaseModel):
    """洛书的一条线（行/列/对角线），即一个平面或箭矢。"""

    key: str = Field(description="mental / emotional / practical / thought / will / action / silver_yog / golden_yog。")
    name_zh: str
    name_en: str
    cells: list[int] = Field(description="构成数字，恒为洛书的一条线。")
    complete: bool = Field(description="三数是否齐备。")
    missing: list[int] = Field(default_factory=list, description="缺哪几个；齐备时为空。")
    text: str = Field(description="齐 → `present_text`，缺 → `missing_text`；引擎只选句，不组句。")
    source: str


class LoshuGrid(BaseModel):
    """生辰洛书九宫与八平面（spec §6.6）。"""

    cells: list[GridCell]
    layout: list[list[int]]
    total: int = Field(ge=0, description="计数合计，恒等于生日里非 0 数字字符的个数。")
    zero_count: int = Field(ge=0, description="生日里 0 的个数。洛书无 0 格，故不计入 `total`。")
    digits: list[int] = Field(default_factory=list, description="生日取出的全部数字字符（含 0），供逐位复核。")
    missing: list[DigitMeaning] = Field(default_factory=list, description="`count == 0` 的数位及其洛书解读。")
    planes: list[LoshuPlane] = Field(description="八个平面，顺序照语料。")
    line_sums: list[int] = Field(
        description="八条线各自的和，恒为 15。下发它是为了让决策 12 的幻方性质在响应里"
        "就可核对，而不只藏在后端单测里。"
    )
    source: str


class NumerologyInput(BaseModel):
    """回显与计数。让读者先看清"到底算了什么"，再看结果。"""

    full_name: str
    name_zh: str | None = Field(default=None, description="仅回显。")
    birth_date: date
    reference_date: date
    y_as_vowel: bool
    age_at_reference: int | None = Field(
        default=None,
        description="`reference_date` 时的周岁；基准日早于生日时为 None（不填负数或 0）。",
    )
    letter_count: int = Field(ge=0, description="参与计算的拉丁字母数。")
    skipped_count: int = Field(ge=0, description="被跳过的非字母字符数（决策 8：如实报，不偷偷算 0）。")
    skipped_chars: list[str] = Field(default_factory=list, description="去重后的被跳过字符，供用户看出漏了什么。")
    vowel_total: int = Field(ge=0, description="元音值总和（表达数不变式的一侧）。")
    consonant_total: int = Field(ge=0, description="辅音值总和（另一侧）。")
    letter_total: int = Field(ge=0, description="全字母值总和，恒 == 元音和 + 辅音和。")


class NumerologyProvenance(BaseModel):
    reference_date: date
    engine: str = Field(description="算法来源声明；本系统无历法库、无星历、无随机。")
    badge: str = Field(description="档案号，只印方法标识（决策 16：流水号无推导依据，不编）。")
    tables: list[ProvenanceTable] = Field(description="本端点真读到的四张语料表，不多不少。")
    method: str = Field(
        description="算法口径叙述：六个核心数的算式、顶峰年龄轴规则、挑战时段规则。"
        "把规则原文下发，读者才能拿它核对响应里的数字。"
    )


class NumerologyChart(BaseModel):
    """完整响应。**没有 `score`**（决策 14），也不含任何百分比（决策 13）。"""

    input: NumerologyInput
    letters: list[LetterValue]
    core: list[CoreNumber] = Field(description="固定序：生命灵数 → 表达 → 灵魂冲动 → 人格面具 → 生日 → 成熟。")
    karmic_debts: list[KarmicDebt] = Field(default_factory=list)
    pinnacles: list[Pinnacle]
    challenges: list[Challenge]
    personal_cycles: PersonalCycles
    name_grid: NumberGrid
    loshu_grid: LoshuGrid
    provenance: NumerologyProvenance
