"""Pydantic schemas for the Norse Runes (北欧卢恩) cast system.

Field names are snake_case end-to-end (the JSON contract mirrors these models)
so the frontend can consume responses without a mapping layer.

Two absences are deliberate and are guarded by the contract tests:

* **No ``score`` and no percentage field anywhere** (spec 决策 6/7). The mockup
  printed five percentages on this page. A rune cast takes neither a birth date
  nor a location, so there is nothing those numbers could have been computed
  from -- shipping any of them would mean inventing a figure and dressing it as
  a measurement.
* **No element, deity or timing-window field** (spec 决策 6/8/10). The mockup
  carried three mutually inconsistent element schemes, three deity attributions
  and a spring-equinox window. Nothing here can derive any of them.

What replaces them is provenance: every stone carries the ``source`` of the
corpus entry it came from, and ``RuneProvenance`` names the entropy source
honestly (决策 19) instead of the mockup's invented "quantum chaos" claim.
"""

from pydantic import BaseModel, Field

from app.content.rune_spreads import DEFAULT_SPREAD_ID
from app.schemas.common import ProvenanceTable

#: 徽标只印方法标识（决策 18）。设计稿的 `#RUNES-FUTHARK-2026-N09` 里那串流水号
#: 没有任何东西可以推导出来，故砍掉 —— 印一个编出来的编号等于假装有一本登记册。
RUNE_BADGE = "#RUNES-FUTHARK"

#: 熵源如实描述（决策 19）。设计稿写「量子混沌伪随机熵源」：「量子混沌」是假技术，
#: 「伪随机」也不准 —— `secrets` 走的是操作系统熵源，不是可复现的伪随机序列。
RUNE_RNG = "secrets"
RUNE_RNG_NOTE = "Python secrets（OS 熵源 CSPRNG），非 random、非可复现种子"

RUNE_ENGINE = "content-library"
RUNE_ENGINE_NOTE = "释义全部取自策展语料库；引擎只做选取与串接，不生成语料之外的形容词"


class RuneCastRequest(BaseModel):
    """一次铸石的输入。

    ``spread_id`` 选牌阵：``single``（1 枚）· ``three``（诺伦三女神，3 枚）·
    ``five``（卢恩十字，5 枚）。``include_wyrd`` 默认关（决策 3）：空白符是 1980 年代
    的商业增补，把它默认打开等于默认按现代牌组而非 Elder Futhark 起卦。

    卢恩铸石**不吃时间与地点** —— 这是它与八字、占星的根本差别，也是本页不可能
    有任何「时机」字段的原因（决策 10）。
    """

    spread_id: str = Field(default=DEFAULT_SPREAD_ID, description="single | three | five.")
    include_wyrd: bool = Field(
        default=False,
        description="Whether the blank stone (a modern addition) joins the 24-rune deck.",
    )
    allow_reversed: bool = Field(
        default=True,
        description="Whether stones may land reversed (merkstave). Symmetric runes never do.",
    )
    question: str | None = Field(
        default=None,
        max_length=120,
        description="Optional question, echoed back and used only to lead the synthesis.",
    )


class DrawnRune(BaseModel):
    """一枚抽进某个位次的符文。

    `keywords` 与 `meaning` 是**按本次朝向取用后的那一份**，不是两面都给：给了两面，
    读者就无从知道引擎究竟读了哪一面，卡上的逆位徽标也就失去了对应的文字。
    想看另一面去 `shadow_counsel`，那里明说是反面参照。
    """

    position_index: int = Field(description="Zero-based order of the position in the spread.")
    position_key: str = Field(description="Stable position identifier, e.g. urd.")
    position_label: str = Field(description="English position label.")
    position_label_zh: str = Field(description="Chinese position label.")
    position_meaning: str = Field(description="What this position reveals.")

    order: int = Field(description="Kylver order 1-24; the blank stone is 25.")
    key: str = Field(description="Stable rune identifier, e.g. fehu.")
    glyph: str = Field(description="The runic character; empty string for the blank stone.")
    name: str
    name_zh: str
    transliteration: str
    name_meaning: str = Field(description="Reconstructed Proto-Germanic sense of the rune name.")
    name_meaning_uncertain: bool = Field(
        description="True where the etymology is contested or the name is a modern borrowing."
    )
    aett: str | None = Field(description="freyja | heimdall | tyr; null for the blank stone.")
    aett_zh: str | None
    reversible: bool = Field(
        description="False for the eight rotationally symmetric runes; "
        "they have no reversed reading."
    )
    is_wyrd: bool = Field(description="True only for the blank stone.")
    orientation: str = Field(
        description="upright | reversed. Never reversed when reversible is false."
    )
    keywords: list[str] = Field(description="Keywords for the drawn orientation.")
    meaning: str = Field(description="Interpretation for the drawn orientation.")
    source: str = Field(description="Entry-level provenance for this rune's text.")


class AettCount(BaseModel):
    """一组（ætt）在本次铸石里的实际枚数。

    第四行是「不入三组」的桶，只装 Wyrd。它 `aett is None`，但抽到的枚数总得有个去处 ——
    否则「三组之和 + Wyrd == 抽到枚数」这条会计等式在开着空白符时就不成立（§9.2）。

    count 为 0 的行照样列出：0 是真实值，不是缺失（与数字命理九宫计数同一条纪律）。
    少一行会让「这次一枚都没落在提尔之族」与「引擎忘了算这一组」在响应里长得一样。
    """

    key: str = Field(description="freyja | heimdall | tyr | wyrd.")
    name: str
    name_zh: str
    count: int = Field(description="How many drawn stones fall in this group; 0 is a real value.")


class ShadowNote(BaseModel):
    """一条阴影参照（决策 17）。

    这一块**不是**额外算出来的凶兆，只是把语料里本来就有的另一面摊开给读者看。
    故 `drawn_orientation` 必须在场：少了它，读者会把一段反面参照误读成对本次结果的断言。
    """

    key: str
    name: str
    name_zh: str
    glyph: str
    position_key: str = Field(description="Which spread position this stone fell in.")
    position_label_zh: str
    drawn_orientation: str = Field(
        description="upright | reversed -- what this cast actually gave."
    )
    shadow_keywords: list[str] = Field(description="The reversed-side keywords, as a contrast.")
    shadow_meaning: str = Field(description="The reversed-side reading, as a contrast.")
    note: str = Field(description="Says in words that this is the other side, not the result.")


class CodexRune(BaseModel):
    """全典抽屉里的一枚符文 —— 参考资料，不是本次结果。

    比 `DrawnRune` 多三样：`codepoint` 与 `unicode_name`（全典抽屉的宽表逐枚印「码位」与
    「Unicode 官方名」，即 §8 说的「Unicode 码位锚点」—— 字形对错不靠肉眼，读者可以自己拿
    这两个字段核；它为何落在抽屉而非出处卡，见 spec §11 偏差 U），以及正逆**两面都带齐**
    （抽屉是查阅用的，只带一面就没法当参考）。
    """

    order: int
    key: str
    glyph: str
    codepoint: int | None = Field(description="Unicode scalar; null for the blank stone.")
    unicode_name: str | None = Field(description="Official Unicode character name; null for Wyrd.")
    name: str
    name_zh: str
    transliteration: str
    phoneme: str = Field(description="Sound value, or a note that the stone has none.")
    name_meaning: str
    name_meaning_uncertain: bool
    aett: str | None
    aett_zh: str | None
    reversible: bool
    is_wyrd: bool
    upright_keywords: list[str]
    reversed_keywords: list[str] | None = Field(description="Null for the eight symmetric runes.")
    upright_meaning: str
    reversed_meaning: str | None = Field(description="Null for the eight symmetric runes.")
    source: str


class AettGroup(BaseModel):
    """抽屉里的一组，八枚。`naming_note` 一并下发：ætt 这个称呼与三组的名字都是近代且各家不一。"""

    key: str
    name: str
    name_zh: str
    theme: str = Field(
        description="Modern reading of what this group is about; not ancient doctrine."
    )
    naming_note: str
    runes: list[CodexRune]


class RuneCodex(BaseModel):
    """全典 24+1 枚（决策 25）。

    恒为 25 条，**不随 `include_wyrd` 变**：那个开关管的是抽不抽得着空白符，
    不是它在不在典里。抽屉里 Wyrd 恒单独成条并标注现代增补。
    """

    aettir: list[AettGroup] = Field(description="The three groups, eight runes each.")
    wyrd: CodexRune = Field(description="Always present, always flagged modern by its source.")
    total: int = Field(description="24 real runes + 1 modern addition. Asserted by tests.")


class RuneProvenance(BaseModel):
    """出处卡的数据。每一条都是读者可以拿去核对的，没有一条是装饰。"""

    rng: str = Field(default=RUNE_RNG, description="Randomness source: Python secrets (CSPRNG).")
    rng_note: str = Field(default=RUNE_RNG_NOTE, description="Plain-language entropy statement.")
    engine: str = Field(
        default=RUNE_ENGINE, description="Interpretations come from the curated corpus."
    )
    engine_note: str = Field(default=RUNE_ENGINE_NOTE)
    badge: str = Field(
        default=RUNE_BADGE, description="Method identifier only; no invented serial number."
    )
    deck_size: int = Field(description="24, or 25 when the blank stone was enabled.")
    tables: list[ProvenanceTable] = Field(description="The two tables this endpoint really reads.")
    method: str = Field(
        description="Draw procedure in words: deck choice, sampling without replacement, "
        "the 180-degree criterion for reversals. Shipped so the reader can check the result."
    )
    naming_note: str = Field(description="Says the aett names are modern and vary between sources.")
    wyrd_note: str = Field(description="Says the blank stone is a 1980s addition, not ancient.")
    manuscript_note: str = Field(
        description="The two real credentials behind this page (the Kylver stone for the order, "
        "Codex Regius for the myth), plus which mockup claims were dropped for want of evidence."
    )


class RuneCastResponse(BaseModel):
    """完整响应。**没有 `score`，也没有任何百分比字段**（决策 6、7）。

    `aett_balance` 是本页唯一的「统计格」（决策 16）：它是**计数**，不是评分。
    数出「三组各落几枚」是对已发生事实的清点，读者可以自己数着核对；
    而设计稿那五个百分比是凭空来的，没有任何输入可以推出它们。
    """

    # 牌阵身份
    spread_id: str
    spread_name: str
    spread_name_zh: str
    spread_description: str
    question: str | None = Field(description="The question echoed back, if provided.")

    # 本次铸石
    stones: list[DrawnRune] = Field(description="Stones in spread-position order.")
    drawn_keys: list[str] = Field(
        description="Rune keys in position order; elements distinct (drawn without replacement)."
    )
    allow_reversed: bool = Field(description="Whether reversals were enabled for this draw.")
    include_wyrd: bool = Field(description="Whether the blank stone was in the deck for this draw.")

    # 由真内容确定性拼出
    aett_balance: list[AettCount] = Field(
        description="Four rows: the three groups plus the unassigned bucket. Counts, never scores."
    )
    synthesis: str = Field(
        description="Composed from corpus text only; names no rune that was not drawn."
    )
    shadow_counsel: list[ShadowNote] | None = Field(
        description="Reversed-side contrast for reversible runes drawn; null when there are none."
    )
    reversible_note: str = Field(
        description="The 180-degree criterion, printed for the reader to check."
    )

    # 全典与出处
    codex: RuneCodex
    provenance: RuneProvenance
