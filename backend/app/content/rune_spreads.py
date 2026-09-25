"""三种卢恩牌阵：单枚、诺伦三女神、卢恩十字（卢恩 spec §5.2）。

**形状与塔罗 `content/tarot_deck.py` 的 `SpreadPosition` / `Spread` 同形，但刻意不 import 它**。
spec §2.7 说的「直接同形复用」，在这里落成「同一个形状」而非「同一个类」：本仓没有任何
content 模块 import 过 `tarot_deck`（`SpreadPosition` 只在它自己文件里用），卢恩不该为了两个
十四行的 frozen dataclass 破这个例 —— 那会让「塔罗模块改名或删掉」升级成卢恩的破坏性变更，
也让卢恩牌阵凭空多出一层塔罗血统。故就地重声明，字段名与 `size` property 逐字对齐，
读过塔罗的人不需要换脑子就能读这里。

与塔罗那一版有一处**故意的差别**：本模块的 `Spread` 多一个 `source` 字段，三种牌阵各带各的
出处串。理由是数字命理走查查出的缺陷：前端 `SourceNote` 对非古籍出处只印第一个「（」之前的
半句，若三种牌阵共用一个出处，页面上就会印出三个一模一样的角标，读者无从知道这一格引的是
哪一条。故条目名一律拼在限定语**之前**（与 `rune_futhark.runes_source` 同一手法）。

两处诚实补记，都写进出处限定语、也印到页面上：

* **三女神之名是真的，「过去/现在/将来」这个读法是今人的。** Urðr / Verðandi / Skuld
  确见于古埃达《女先知之歌》（Völuspá）第 20 节，是司命运的三位女神；但把她们派作牌阵的
  三个位次、逐一读成过去/现在/将来，是现代占卜的类比，不是古法。
* **卢恩十字是现代布局**，仿塔罗十字而来，无古铭文或埃达依据。设计稿管它叫「五行五元素阵」
  —— 那是把中国五行安到北欧系统上的范畴错误（spec 决策 13），故改名并如实标注。

单枚牌阵的副题沿用设计稿的 "Oðinn's Eye"：奥丁为求智慧把自己一只眼睛押给了密米尔之井
（Völuspá 28–29），故「一只眼、一枚符、一个答案」这个比喻站得住，不算编造。
"""

from __future__ import annotations

from dataclasses import dataclass

# --- 出处 -------------------------------------------------------------------

#: 书级出处。拆成「名 + 限定语」两半，理由同 `rune_futhark.RUNES_SOURCE_NAME`。
SPREADS_SOURCE_NAME = "北欧卢恩三种牌阵的位次与现代释义"
SPREADS_SOURCE_QUALIFIER = (
    "三女神之名出自古埃达《女先知之歌》第 20 节，奥丁押眼见同篇 28–29 节；"
    "但三位次读作过去/现在/将来、以及十字五位的布局，均为现代通行约定，非古法"
)

#: 整串出处，逐字等于拆分前那一串：语料测与响应里的 `provenance.tables` 都按整串核。
#:
#: **给 T7 的一个提醒**：上面那段限定语里引了《女先知之歌》，而前端 `citesBook()` 的判据
#: 就是「字符串里有没有《」。故牌阵的角标会走**书引分支**：印全文、素色散文样式，
#: 而不是走截断分支印成金色小药丸。这是故意的、也是更安全的一边：书引分支不截断，
#: 于是「均为现代通行约定、非古法」这句免责一定看得见；若走截断分支，它会被切掉。
#: 组件自己的注释也说了，混合出处宁可全文展示，不得降级。代价只是角标偏长，排版时留意。
#: （对比：`rune_futhark` 那两张出处串里**没有**《，故符文角标走截断分支、
#: 靠 `runes_source()` 把条目名拼在限定语之前来自证身份。两边机制不同，别拷错。）
SPREADS_SOURCE = f"{SPREADS_SOURCE_NAME}（{SPREADS_SOURCE_QUALIFIER}）"


def spreads_source(entry: str) -> str:
    """带条目名的出处，如 `…位次与现代释义·卢恩十字（三女神之名出自…）`。

    条目名拼在限定语**之前**，这样角标截断后仍自证身份、三种牌阵互不撞车。
    """
    return f"{SPREADS_SOURCE_NAME}·{entry}（{SPREADS_SOURCE_QUALIFIER}）"


# --- 数据模型（与塔罗同形，见模块 docstring） ------------------------------


@dataclass(frozen=True)
class SpreadPosition:
    """牌阵的一个位次，由恰好一枚抽出的符文填入。"""

    key: str          # 稳定的机器标识，如 "urd"
    label: str        # 英文位次名，如 "Urðr · What Has Become"
    label_zh: str     # 中文位次名，如 "乌尔德 · 源起"
    meaning: str      # 这一位要读出什么


@dataclass(frozen=True)
class Spread:
    """一种具名的符文布局，位次有序。

    比塔罗那一版多一个 `source`：三种牌阵各署各的名，免得前端印出三个一样的角标。
    """

    id: str
    name: str
    name_zh: str
    description: str
    positions: tuple[SpreadPosition, ...]
    source: str

    @property
    def size(self) -> int:
        """这种牌阵要抽几枚。"""
        return len(self.positions)


def _spread(
    id: str,
    name: str,
    name_zh: str,
    description: str,
    source_entry: str,
    positions: tuple[tuple[str, str, str, str], ...],
) -> Spread:
    """由 `(key, label, label_zh, meaning)` 生料拼出一种牌阵。

    `source_entry` 单列一参而不给默认值，是为了逼每处调用都写清自己引的是哪一条：
    漏写是 `TypeError`，而不是悄悄退回一个与兄弟撞车的角标（数字命理走查的教训）。
    """
    return Spread(
        id=id,
        name=name,
        name_zh=name_zh,
        description=description,
        positions=tuple(SpreadPosition(*p) for p in positions),
        source=spreads_source(source_entry),
    )


# --- 三种牌阵 ---------------------------------------------------------------

_SINGLE = _spread(
    "single", "Oðinn's Eye", "单枚每日启示",
    "One rune for a daily reflection or a single, focused question.",
    "单枚每日启示",
    (
        (
            "guidance", "Guidance", "当下启示",
            "这一枚直接答你问的那件事，或作为今日的要点。现代通行约定：单枚不设位次之别，"
            "全部重量都落在这一枚符文自身的正逆位释义上，没有旁位可推诿，也没有旁位可印证。",
        ),
    ),
)

_THREE = _spread(
    "three", "The Three Norns", "诺伦三女神运命之阵",
    "Three runes woven as fate: what has become, what is becoming, what shall be.",
    "诺伦三女神运命之阵",
    (
        (
            "urd", "Urðr · What Has Become", "乌尔德 · 源起",
            "已经织成的那一段：事情从何而来，哪些已成定局、不可再改。"
            "Urðr 之名出自古埃达《女先知之歌》第 20 节，本义近「已发生之事」；"
            "但把它当牌阵位次读作「过去」，是现代占卜的类比。",
        ),
        (
            "verdandi", "Verðandi · What Is Becoming", "薇尔丹蒂 · 显相",
            "正在织的那一段：此刻还在成形、仍有转圜的力量与状态。"
            "Verðandi 本义近「正在发生之事」—— 这一位是三枚里唯一还改得动的，"
            "故现代读法把它当「现在」，也当可以下手的地方。",
        ),
        (
            "skuld", "Skuld · What Shall Be", "诗蔻蒂 · 必然",
            "尚未织成的那一段：照现在的走法，接下来会落到哪里。"
            "Skuld 与「债、该当」同源 —— 故这一位读出的不是天降的判词，"
            "而是前面两枚欠下、到这一枚要还的账。",
        ),
    ),
)

_FIVE = _spread(
    "five", "Runic Cross", "卢恩十字",
    "Five runes laid as a cross: the core, the way in, the way out, "
    "what it rests on and what it becomes.",
    "卢恩十字",
    (
        (
            "center", "Center · The Core", "中心 · 当下核心",
            "这件事此刻的核心，其余四位都围着它读。现代布局：十字五位仿塔罗十字而来，"
            "无古铭文或埃达依据 —— 它是个好用的读法框架，不是一件文物。",
        ),
        (
            "left", "Left · Where It Came From", "左 · 来处",
            "把局面推到此地的来路：已经发生的事与既成的条件。"
            "与三女神阵的 Urðr 位相通，但这里它只是核心的一个侧面，不是独立的一段时间。",
        ),
        (
            "right", "Right · Where It Goes", "右 · 去向",
            "照现在的势头往下走的去向。读作趋势而非定数：势头改，这一位也就跟着改。",
        ),
        (
            "below", "Below · What It Rests On", "下 · 根基",
            "托着这件事的底：未必显眼，却决定上面几位能走多远。"
            "常是资源、体质、旧关系一类「不在讨论里但一直在起作用」的东西。",
        ),
        (
            "above", "Above · What It Becomes", "上 · 所成",
            "落到实处的结果：前四位合起来最后成个什么样子。"
            "这一位是汇总，不是新增的一条独立预言 —— 若它与前四位相左，该疑的是前四位的读法。",
        ),
    ),
)

SPREADS: dict[str, Spread] = {
    spread.id: spread
    for spread in (
        _SINGLE,
        _THREE,
        _FIVE,
    )
}

#: 牌阵 id 的规范顺序，供 schema 的字面量与前端下拉框共用同一份真相。
SPREAD_IDS: tuple[str, ...] = ("single", "three", "five")

#: 未指定牌阵时用这一种：`RuneCastRequest.spread_id` 的默认值，前端控制台的初始态同取三石阵。
#: 三枚是默认的一档 —— 单枚只够一句启示，五枚要读者先懂十字五位，三枚居中。
DEFAULT_SPREAD_ID = "three"


def get_spread(spread_id: str) -> Spread | None:
    """按 id 取牌阵，未知则回 `None` —— 由引擎抛 `UnsupportedMethodError`（与塔罗同一约定）。

    这里**不抛**：语料层只负责「有没有这条」，把它翻译成什么 HTTP 状态码是引擎与路由的事。
    """
    return SPREADS.get(spread_id)
