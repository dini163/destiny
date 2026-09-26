"""西洋合盘相契度赋分表：本系统模型参数，非古籍赋分。

西洋合盘（Synastry）与组合盘（Composite）没有统一的古籍赋分标准 —— 相位的吉凶是
现代占星的定性共识（合=融合、六合与拱=和谐、刑与冲=挑战），而"给几分"从来无人定数。
本表把这份定性共识落成可核对的权重：每种相位的基准增减、核心羁绊的强调系数、
容许度衰减的下限，以及四档分界。数值一律是本系统模型参数，每条 `ScoreFactor.source`
逐字署 `MODEL_PARAM_SOURCE`，绝不冒充古籍。

组合盘（Composite）取两造同名行星与宫头的「短弧中点」，纯几何、可复算，本身不赋分 ——
它只呈现关系合力的落点，不进相契度账本。相契度只由「人对人」的合盘相位决定，且只计
两端皆为个人点（日月水金火与上升）者：外行星之间及其单独与四轴的相位是世代/背景议题，
仍随相位表呈现，但不进总分。
"""

from app.core.provenance import MODEL_PARAM_SOURCE

#: 相契度基准分：中性的起评，不是"及格"（含义同合婚与岁运的 base）。
SYNASTRY_BASE = 50.0

#: 全表出处：西洋合盘赋分是本系统模型参数，无古籍可引。
SYNASTRY_SOURCE = MODEL_PARAM_SOURCE

#: 相位类型 → 基准增减。和谐为正、挑战为负；合相本身吉凶由所合之星定，
#: 这里只给一个中性的轻微正分（融合），核心羁绊另有强调系数放大。
SYNASTRY_ASPECT_DELTA: dict[str, float] = {
    "conjunction": 1.5,
    "sextile": 2.0,
    "trine": 3.0,
    "square": -2.5,
    "opposition": -2.0,
}

#: 相位类型 → 中文简称（账本行短名用，如「太阳拱月亮」）。
SYNASTRY_ASPECT_ZH: dict[str, str] = {
    "conjunction": "合",
    "sextile": "六合",
    "square": "刑",
    "trine": "拱",
    "opposition": "冲",
}

#: 参与计分的个人点：只有**两端都**落在这组里的相位才进相契度账本。
#: 外行星（木土天海冥）之间及其单独与中天/下降的相位更多是世代与背景议题，
#: 仍列入相位表呈现，但不进个人相契度总分（口径见 `SYNASTRY_METHOD`）。
SYNASTRY_PERSONAL_POINTS: frozenset[str] = frozenset(
    {"Sun", "Moon", "Mercury", "Venus", "Mars", "ASC"}
)

#: 核心羁绊（无序对；两端同名者写作 ("Sun","Sun")）：这几对星的相位最能定关系基调，
#: 命中时以 `SYNASTRY_CORE_EMPHASIS` 放大。取自现代合盘公认的几条关系主轴。
SYNASTRY_CORE_BONDS: frozenset[tuple[str, str]] = frozenset(
    {
        ("Moon", "Sun"),  # 日月：经典婚姻/互补轴
        ("Mars", "Venus"),  # 金火：吸引与激情轴
        ("Moon", "Venus"),  # 月金：情感与亲昵轴
        ("Sun", "Sun"),  # 日日：意志与身份共振
        ("Moon", "Moon"),  # 月月：情绪同频
    }
)

#: 核心羁绊的强调系数。
SYNASTRY_CORE_EMPHASIS = 1.5

#: 容许度衰减：相位越紧（orb→0）权重越接近 1，最松（orb→orb_limit）时降到 (1-衰减)。
SYNASTRY_ORB_DECAY = 0.5

#: 相契度四档（降序阈值 → 档名）。与八字合婚的四档刻意不同名，免得两套合婚混淆。
SYNASTRY_TIERS: tuple[tuple[float, str], ...] = (
    (75.0, "相契甚深"),
    (60.0, "和合互补"),
    (45.0, "中和可处"),
    (0.0, "磨合为宜"),
)

#: 方法声明，回显在 `provenance.method`。
SYNASTRY_METHOD = (
    "相契度以 50 分为中性起评，逐条累加「人对人」的合盘相位：每条增减 = 相位基准分 × "
    "容许度权重（相位越紧权重越高，最松降到一半）× 核心羁绊强调（日月/金火/月金/日日/月月 1.5 倍）；"
    "只有两端皆为个人点（日月水金火与上升）的相位计入，外行星之间及其单独与中天的世代相位不计。"
    "总分截断到 0–100，截断本身记为一行账。四档：≥75 相契甚深 · 60–74 和合互补 · "
    "45–59 中和可处 · <45 磨合为宜。组合盘（Composite）另取两造同名行星与宫头的短弧中点，"
    "纯几何可复算，只呈现关系合力落点，不进相契度账本。赋分全为本系统模型参数，无古籍可引。"
)


def synastry_tier(value: float) -> str:
    """按相契度总分取档名。阈值降序，落到第一个 `value >= 阈值` 的档。"""
    for threshold, label in SYNASTRY_TIERS:
        if value >= threshold:
            return label
    return SYNASTRY_TIERS[-1][1]
