"""Pydantic schemas for the Zhouyi / Liuyao (周易六爻) system.

Field names are snake_case end-to-end. The primary (本卦) hexagram's six lines
are fully dressed with 纳甲 (stem/branch), 六亲, 六神, 世应 and the classical
爻题/爻辞; the changed (变卦) and nuclear (互卦) hexagrams are reported
structurally. Every hexagram carries its 卦辞, and 乾/坤 additionally carry the
用九/用六 line.

Each 卦辞 / 爻辞 / 用九·用六 is paired with a vernacular retelling (`plain_*`), taken
row-by-row from the curated table `content/zhouyi_plain.py`; the 用 fields are null for
the 62 hexagrams that have no 用九/用六.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from app.schemas.common import ProvenanceTable


class CastMethod(str, Enum):
    """How the hexagram is cast."""

    THREE_COIN = "three_coin"   # engine simulates six throws of three coins
    MANUAL = "manual"           # caller supplies the six throws of three coins
    TIME = "time"               # 梅花易数 plum-blossom time casting


class ZhouyiCastRequest(BaseModel):
    """Input for a Zhouyi cast.

    ``manual_coins`` is required only for the ``manual`` method: six throws, each
    a list of three coin faces where a face is ``3`` (字背/阳) or ``2`` (阴), so
    each throw sums to 6/7/8/9. ``cast_time`` defaults to the current moment and
    supplies the day pillar (for 六神) and, for the ``time`` method, the lunar
    year/month/day/hour numbers.
    """

    method: CastMethod = Field(default=CastMethod.THREE_COIN)
    manual_coins: list[list[int]] | None = Field(
        default=None, description="Manual method only: six throws of three coin faces (2 or 3)."
    )
    question: str | None = Field(default=None, description="Optional question the divination addresses.")
    cast_time: datetime | None = Field(default=None, description="Cast moment; defaults to now.")


class ZhouyiLine(BaseModel):
    """One dressed line (爻) of the primary hexagram, bottom-to-top."""

    position: int = Field(description="Line position 1-6, bottom to top.")
    value: int = Field(description="Coin-sum value: 6 old yin, 7 young yang, 8 young yin, 9 old yang.")
    yin_yang: str = Field(description="yin | yang")
    symbol: str = Field(description="Line glyph: ⚊ (yang) or ⚋ (yin).")
    moving: bool = Field(description="Whether this line is a moving line (动爻).")
    stem: str = Field(description="纳甲 heavenly stem.")
    branch: str = Field(description="纳甲 earthly branch.")
    branch_element: str = Field(description="Five-element of the branch.")
    liuqin: str = Field(description="六亲 relative to the palace element: 父母/兄弟/子孙/妻财/官鬼.")
    liushen: str = Field(description="六神 assigned from the day stem.")
    is_shi: bool = Field(description="Whether this is the 世 (self) line.")
    is_ying: bool = Field(description="Whether this is the 应 (response) line.")
    yao_name: str = Field(description="爻题 — classical line title, e.g. 初九 / 六二 / 上六.")
    yao_ci: str = Field(description="爻辞 — the classical line statement of the primary hexagram.")
    plain_yao_ci: str = Field(description="爻辞的白话今译，逐键取自 content/zhouyi_plain.py（丁组 spec §5）。")


class HexagramInfo(BaseModel):
    """Structural identity of a hexagram plus its classical 卦辞 and the 今译 pair."""

    number: int = Field(description="King Wen sequence number 1-64.")
    name_zh: str = Field(description="Short name, e.g. 屯.")
    full_name_zh: str = Field(description="Trigram-encoded name, e.g. 水雷屯.")
    pinyin: str
    name_en: str
    symbol: str = Field(description="Unicode hexagram glyph, e.g. ䷂.")
    lines: list[int] = Field(description="Six lines bottom-to-top, 1=yang 0=yin.")
    lower: str = Field(description="Lower (inner) trigram key.")
    lower_name_zh: str
    lower_nature_zh: str
    upper: str = Field(description="Upper (outer) trigram key.")
    upper_name_zh: str
    upper_nature_zh: str
    palace: str = Field(description="Palace trigram key (八宫).")
    palace_name_zh: str = Field(description="Palace name, e.g. 坎宫.")
    palace_element: str = Field(description="Five-element governing 六亲.")
    generation: str = Field(description="本宫/一世…五世/游魂/归魂.")
    shi: int = Field(description="世 line position 1-6.")
    ying: int = Field(description="应 line position 1-6.")
    gua_ci: str = Field(description="卦辞 — the classical hexagram judgment.")
    plain_gua_ci: str = Field(description="卦辞的白话今译，逐键取自 content/zhouyi_plain.py。")
    yong_ci: str | None = Field(
        default=None, description="用九/用六 line (乾/坤 only); null for the other 62 hexagrams."
    )
    plain_yong_ci: str | None = Field(
        default=None,
        description="用九/用六的今译；其余 62 卦为 None 是忠实的缺席（丁组 spec §5），不是缺字段。",
    )


class ZhouyiProvenance(BaseModel):
    """出处块：历法来源一个短值 + 本页真读到的五张语料表（丁组 spec §5）。

    顶层 `ZhouyiCast.engine`（恒为 `liuyao-najia`）是**本端点的推导器名**，本块的 `engine`
    是**历法事实来自哪个库**——日柱（定六神）与时间起卦的农历数都由它给出。两个键同名不同职，
    这条限度与 `schemas/meihua.py` 的 `MeihuaProvenance` 同文；`content_version` 那一格照
    后四家（`schemas/tarot.py:27`、`schemas/lenormand.py`、`schemas/ziwei.py`、`schemas/qimen.py`）
    的新形状。`MeihuaProvenance` 多的那一格 `method` 这里不收：梅花要说清「起卦与卦气的算式口径」，
    周易的装卦口径已经在 `ZhouyiCast.method` 与每爻的纳甲字段里，本块不重复一遍。
    """

    engine: str = Field(description="历法来源引擎，恒为 lunar-python。")
    content_version: str = Field(description="语料滚动版本，全表共用 content.CONTENT_VERSION。")
    tables: list[ProvenanceTable] = Field(description="本页真正读到的五张表，来自 ZHOUYI_CONTENT_SOURCES。")


class ZhouyiCast(BaseModel):
    """Complete Zhouyi cast produced by :mod:`app.engines.zhouyi`."""

    # Provenance
    method: str = Field(description="three_coin | manual | time")
    question: str | None = Field(description="The question echoed back, if provided.")
    cast_time: str = Field(description="Cast moment used, e.g. 2024-05-15 10:30.")
    day_ganzhi: str = Field(description="Day pillar (日柱) that fixes the 六神.")

    # Hexagrams
    ben: HexagramInfo = Field(description="本卦 — the primary hexagram as cast.")
    bian: HexagramInfo | None = Field(description="变卦 — after moving lines change; null if none move.")
    hu: HexagramInfo = Field(description="互卦 — the nuclear hexagram from lines 2-3-4 / 3-4-5.")

    # Lines
    moving_positions: list[int] = Field(description="Moving-line positions (1-6, bottom-to-top).")
    lines: list[ZhouyiLine] = Field(description="The six dressed lines of the primary hexagram.")

    provenance: ZhouyiProvenance = Field(description="出处块：五张表 + 历法来源 + 语料版本。")

    rng: str = Field(default="secrets", description="Randomness source for coin/time casting (CSPRNG).")
    engine: str = Field(default="liuyao-najia", description="Derivation engine name.")
