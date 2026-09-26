"""雷诺曼 (Lenormand) 36-card deck and spread (牌阵) library.

The Petit Lenormand deck is 36 fixed picture cards, each carrying a number, a
bilingual name, a traditional positive/negative polarity, core keywords, a
one-line meaning, a short ``essence`` (名词核心) and an ``as_modifier`` phrase
(形容词性修饰). Nothing is generated at runtime (PRD no-mock rule).

Lenormand reads by **combination**, not by single card + fixed position the way
tarot does: in a pair ``A → B`` the first card is the *subject* (名词) and the
second is the *modifier* (形容词), so the phrase is ``B.as_modifier + A.essence``
(e.g. 骑士 × 三叶草 → "幸运的消息"). Cards are **never reversed** — every card is
read upright, which is a defining difference from tarot.

Spreads define the ordered positions a draw fills. Grid spreads (九宫阵 / 大桌)
carry a row/col so the frontend can lay them out; the 大桌 is the traditional
4×8 (cards 01–32) plus a final row of 4 (33–36).
"""

from dataclasses import dataclass

LENORMAND_SOURCE = "Petit Lenormand 36 张通行牌义 · 雷诺曼大桌全景（Grand Tableau）组合直读体系"


# --- Card model -------------------------------------------------------------

@dataclass(frozen=True)
class LenormandCard:
    """One of the 36 Petit Lenormand cards (always read upright)."""

    number: int
    id: str
    name: str           # English name
    name_zh: str        # Chinese name
    polarity: int       # +1 积极 | 0 中性 | -1 消极
    keywords: tuple[str, ...]
    meaning: str        # one-line core meaning
    essence: str        # 名词核心，用于组合直读的主词
    as_modifier: str    # 形容词性修饰，用于组合直读的修饰词


def _card(
    number: int,
    name: str,
    name_zh: str,
    polarity: int,
    keywords: tuple[str, ...],
    meaning: str,
    essence: str,
    as_modifier: str,
) -> LenormandCard:
    return LenormandCard(
        number=number,
        id=f"lenormand-{number:02d}",
        name=name,
        name_zh=name_zh,
        polarity=polarity,
        keywords=keywords,
        meaning=meaning,
        essence=essence,
        as_modifier=as_modifier,
    )


CARDS: tuple[LenormandCard, ...] = (
    _card(1, "Rider", "骑士", 1, ("消息", "到来", "访客", "迅速"),
          "喜讯或访客迅速到来，事情即将启动。", "消息", "迅速到来、带来音讯的"),
    _card(2, "Clover", "三叶草", 1, ("好运", "机遇", "侥幸", "短暂"),
          "小幸运与机遇降临，宜即时把握。", "机遇", "幸运而短暂的"),
    _card(3, "Ship", "船", 1, ("远行", "迁移", "贸易", "交通工具"),
          "远行、迁移或贸易往来，事物在移动。", "远行", "来自远方、迁徙流动的"),
    _card(4, "House", "房屋", 1, ("家庭", "房产", "根基", "安稳"),
          "家庭、房产与稳固的根基，安稳所在。", "家庭", "安稳的、家庭根基的"),
    _card(5, "Tree", "树", 1, ("健康", "生命", "成长", "长久"),
          "健康与生命力，缓慢而长久的成长。", "健康", "关乎健康、缓慢生长的"),
    _card(6, "Clouds", "云", -1, ("疑虑", "混沌", "不明", "焦虑"),
          "疑虑与混沌，形势尚不明朗。", "迷雾", "模糊不清、令人困惑的"),
    _card(7, "Snake", "蛇", -1, ("复杂", "欺瞒", "迂回", "第三者"),
          "迂回复杂，或暗藏欺瞒与第三者。", "纠葛", "曲折复杂、暗藏欺瞒的"),
    _card(8, "Coffin", "棺材", -1, ("终结", "停摆", "关闭", "重病"),
          "终结与停摆，旧阶段就此关闭。", "终结", "走向终止、彻底关停的"),
    _card(9, "Bouquet", "花束", 1, ("礼物", "喜悦", "美好", "邀请"),
          "礼物与喜悦，美好的馈赠与邀请。", "喜悦", "愉悦美好、如礼物般的"),
    _card(10, "Scythe", "镰刀", -1, ("骤断", "决断", "意外", "收割"),
          "突如其来的切断或决断，快刀斩乱麻。", "骤断", "突发锋利、骤然了断的"),
    _card(11, "Birch", "鞭子", -1, ("争执", "反复", "口舌", "磨合"),
          "争执与反复，口舌之争或反复操练。", "争执", "争执反复、需要磨合的"),
    _card(12, "Birds", "鸟", -1, ("闲谈", "焦虑", "成双", "琐碎"),
          "纷杂的言语与小焦虑，成双的沟通。", "闲谈", "嘈杂琐碎、令人紧张的"),
    _card(13, "Child", "小孩", 1, ("新生", "单纯", "幼小", "开始"),
          "新的开始与单纯，小而初生之事。", "新生", "新生单纯、微小初始的"),
    _card(14, "Fox", "狐狸", -1, ("狡诈", "算计", "工作", "虚伪"),
          "狡诈与算计，或指工作雇佣，须防虚假。", "算计", "狡黠有所图、表里不一的"),
    _card(15, "Bear", "熊", 1, ("权威", "力量", "长辈", "财务"),
          "权威与力量，长辈、上司或财务主管。", "权威", "强势权威、雄厚有力的"),
    _card(16, "Stars", "星星", 1, ("希望", "指引", "众多", "灵感"),
          "希望与指引，众多而明晰的灵感。", "希望", "充满希望、众多明晰的"),
    _card(17, "Stork", "鹳", 1, ("变动", "提升", "迁移", "新生"),
          "变动与提升，迁移或新生降临。", "变动", "变动向好、迁移新生的"),
    _card(18, "Dog", "狗", 1, ("忠诚", "友谊", "信任", "伙伴"),
          "忠诚与友谊，可信赖的伙伴。", "友谊", "忠诚友善、可信赖的"),
    _card(19, "Tower", "塔", -1, ("官方", "机构", "孤高", "法务"),
          "官方机构或孤高独立，权威与距离。", "官方", "官方孤立、高不可攀的"),
    _card(20, "Garden", "花园", 1, ("公众", "社交", "聚会", "群体"),
          "公众场合与社交聚会，群体活动。", "社交", "公开社交、群体聚集的"),
    _card(21, "Mountain", "山", -1, ("阻碍", "重压", "延迟", "难关"),
          "阻碍与重压，事情受阻需时突破。", "阻碍", "受阻沉重、延迟难越的"),
    _card(22, "Crossroad", "岔路", -1, ("选择", "分岔", "游移", "转折"),
          "选择与分岔，多种可能尚待决断。", "选择", "多选择、游移分岔的"),
    _card(23, "Mice", "老鼠", -1, ("损耗", "焦虑", "侵蚀", "削减"),
          "损耗与焦虑，事物被侵蚀削减。", "损耗", "损耗削减、令人焦虑的"),
    _card(24, "Heart", "心", 1, ("爱", "热忱", "情感", "真心"),
          "爱与热忱，情感的核心所在。", "爱意", "充满爱意、发自真心的"),
    _card(25, "Ring", "戒指", 1, ("承诺", "婚约", "合约", "伙伴"),
          "承诺与结合，婚约、合约或伙伴关系。", "承诺", "承诺缔结、循环相连的"),
    _card(26, "Book", "书", -1, ("秘密", "学问", "未知", "隐秘"),
          "秘密与学问，尚未揭晓的信息。", "秘密", "隐秘未晓、需要研读的"),
    _card(27, "Letter", "信", 1, ("文书", "信件", "讯息", "契约"),
          "文书与信件，白纸黑字的消息。", "文书", "书面传达、文书相关的"),
    _card(28, "Man", "男人", 0, ("男性", "当事人", "指示牌", "问卜者"),
          "男性问卜者，或对其重要的男性（指示牌）。", "男性当事人", "指向男性当事人的"),
    _card(29, "Woman", "女人", 0, ("女性", "当事人", "指示牌", "问卜者"),
          "女性问卜者，或对其重要的女性（指示牌）。", "女性当事人", "指向女性当事人的"),
    _card(30, "Lily", "百合", 1, ("平和", "成熟", "智慧", "长辈"),
          "平和与成熟，智慧、长辈与家庭和谐。", "平和", "平和成熟、德高望重的"),
    _card(31, "Sun", "太阳", 1, ("成功", "喜悦", "光明", "胜利"),
          "成功与喜悦，光明胜利的大吉之象。", "成功", "光明成功、喜悦充沛的"),
    _card(32, "Moon", "月亮", 1, ("名声", "直觉", "情感", "创意"),
          "名声与直觉，情感与创意受到瞩目。", "名声", "声名情感、直觉浪漫的"),
    _card(33, "Key", "钥匙", 1, ("确定", "命定", "解答", "关键"),
          "确定与命定，解锁答案的关键吉兆。", "关键", "确定无疑、解锁关键的"),
    _card(34, "Fish", "鱼", 1, ("财富", "丰饶", "金钱", "流动"),
          "财富与丰饶，金钱业务的流动。", "财富", "丰饶富足、财务流动的"),
    _card(35, "Anchor", "锚", 1, ("稳定", "坚守", "扎根", "达标"),
          "稳定与坚守，扎根不移终抵目标。", "稳定", "稳固坚守、扎根不移的"),
    _card(36, "Cross", "十字架", -1, ("重担", "考验", "业力", "命定"),
          "重担与考验，命定的苦楚与业力。", "重担", "背负重担、命定考验的"),
)

DECK_SIZE = 36
CARDS_BY_ID: dict[str, LenormandCard] = {c.id: c for c in CARDS}
CARDS_BY_NUMBER: dict[int, LenormandCard] = {c.number: c for c in CARDS}

#: 指示牌（significator）——问卜者的性别对应牌。
SIGNIFICATOR_BY_GENDER: dict[str, int] = {"male": 28, "female": 29}

POLARITY_LABEL: dict[int, str] = {1: "积极", 0: "中性", -1: "消极"}


# --- Spreads ----------------------------------------------------------------

@dataclass(frozen=True)
class LenormandPosition:
    """One slot of a spread, filled by exactly one drawn card."""

    key: str
    label_zh: str
    meaning: str
    row: int            # grid row (0-based); line spreads use row 0
    col: int            # grid column (0-based)


@dataclass(frozen=True)
class LenormandSpread:
    """A named Lenormand layout with ordered positions."""

    id: str
    name_zh: str
    name_en: str
    description: str
    layout: str         # "line" | "box" | "tableau"
    positions: tuple[LenormandPosition, ...]

    @property
    def size(self) -> int:
        return len(self.positions)


def _line_spread(
    id: str, name_zh: str, name_en: str, description: str,
    positions: tuple[tuple[str, str, str], ...],
) -> LenormandSpread:
    """Build a single-row spread from (key, label_zh, meaning) tuples."""
    return LenormandSpread(
        id=id, name_zh=name_zh, name_en=name_en, description=description, layout="line",
        positions=tuple(
            LenormandPosition(key, label_zh, meaning, 0, col)
            for col, (key, label_zh, meaning) in enumerate(positions)
        ),
    )


_SINGLE = _line_spread(
    "single", "单张牌", "Single Card",
    "一张牌作即时聚焦的提点，或对某问题的一句话回答。",
    (("guidance", "指引", "当下最核心的提示或答案。"),),
)

_THREE_CARD = _line_spread(
    "three_card", "三张线性", "Three-Card Line",
    "三张牌读成一句话：主词 → 修饰 → 结果，雷诺曼最经典的线性组合。",
    (
        ("subject", "主因", "事情的主体与起点。"),
        ("focus", "现况", "当前作用力，修饰主因。"),
        ("outcome", "走向", "顺此而行的结果。"),
    ),
)

_FIVE_CARD = _line_spread(
    "five_card", "五行线阵", "Five-Card Line",
    "五张牌成一条时间线，中央为核心现状，左右为过去与未来的影响，可两两镜像组合。",
    (
        ("past_far", "远因", "较早的背景影响。"),
        ("past_near", "近因", "紧邻核心的过去。"),
        ("heart", "核心", "此刻事情的中心。"),
        ("future_near", "近果", "紧邻核心的将来。"),
        ("future_far", "远果", "较远的发展方向。"),
    ),
)


def _nine_card() -> LenormandSpread:
    """3×3 box: the centre (position 4) is the heart, ringed by eight influences."""
    labels = (
        ("past", "过去", "左上：远去的背景。"),
        ("present_top", "显象", "上中：浮现于表面的事。"),
        ("future", "未来", "右上：正在接近的势。"),
        ("past_side", "内因", "左中：内在的推动。"),
        ("heart", "核心", "正中：事情的心脏。"),
        ("future_side", "外缘", "右中：外来的助力或干扰。"),
        ("root", "根基", "左下：深藏的根由。"),
        ("subconscious", "隐情", "下中：未言明的底层。"),
        ("outcome", "归宿", "右下：最终的落点。"),
    )
    positions = tuple(
        LenormandPosition(key, label_zh, meaning, row, col)
        for index, (key, label_zh, meaning) in enumerate(labels)
        for row, col in [(index // 3, index % 3)]
    )
    return LenormandSpread(
        id="nine_card", name_zh="九宫阵", name_en="Three-by-Three Box",
        description="九张牌摆成三乘三方阵，中心为核心，四正四隅为环绕的影响，读中心与各方的组合。",
        layout="box", positions=positions,
    )


def _grand_tableau() -> LenormandSpread:
    """Traditional 大桌：4 rows of 8 (cards 01–32 in position order) + a row of 4."""
    positions: list[LenormandPosition] = []
    for index in range(36):
        if index < 32:
            row, col = index // 8, index % 8
        else:
            row, col = 4, index - 32
        positions.append(
            LenormandPosition(
                key=f"seat-{index + 1:02d}",
                label_zh=f"第{index + 1}位",
                meaning="大桌全景中的一席，其义由所在行列与指示牌的相对位置定。",
                row=row, col=col,
            )
        )
    return LenormandSpread(
        id="grand_tableau", name_zh="大桌全景", name_en="Grand Tableau",
        description="三十六张牌尽数铺开（四行八张外加末行四张），以指示牌为中心，读其行列、前后、四隅与关键组合，作全景式命运俯瞰。",
        layout="tableau", positions=tuple(positions),
    )


_NINE = _nine_card()
_TABLEAU = _grand_tableau()

SPREADS: dict[str, LenormandSpread] = {
    spread.id: spread
    for spread in (_SINGLE, _THREE_CARD, _FIVE_CARD, _NINE, _TABLEAU)
}


def get_spread(spread_id: str) -> LenormandSpread | None:
    """Return the spread with ``spread_id`` or ``None`` if it is not defined."""
    return SPREADS.get(spread_id)
