"""梅花易数 (Plum Blossom Numerology) curated reference content.

梅花易数 断卦 rests on two curated, public-domain reference sets (PRD 8: 解读文案
来自内容库；排盘算法与结构必须准确可校验):

* 八卦万物类象 (《说卦传》) — each trigram's 人物 / 身体 / 动物 / 方位 / 物象 /
  性情 correspondences, used to colour a reading with concrete imagery.
* 体用生克 — the five relations between 体卦 (body) and 用卦 (use) with their
  verdict, ordinal grade and classical judgement text.

The *structural* derivations (起卦数, 本/互/变卦, 体用定位, 卦气旺衰, 吉凶指数) are
computed by :mod:`app.engines.meihua` from lunar-python calendar data and the
shared 五行 cycles in :mod:`app.content.wuxing`; this module holds only static
reference text and imagery, never a runtime computation.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class BaguaImage:
    """八卦万物类象 — the classical correspondences of one trigram (《说卦传》)."""

    person: str      # 人物
    body: str        # 身体
    animal: str      # 动物
    direction: str   # 方位
    obj: str         # 物象
    temper: str      # 性情


# Keyed by the trigram key used across the Zhouyi content tables (qian/kun/…).
BAGUA_IMAGE: dict[str, BaguaImage] = {
    "qian": BaguaImage("父、老人、长者、领导、贵人", "头、首、骨、肺", "马、龙、天鹅", "西北", "金玉、宝珠、镜、圆物", "刚健、尊贵、清高、果决"),
    "kun":  BaguaImage("母、老母、众人、农民、群众", "腹、脾、胃、肉", "牛、百兽、母马", "西南", "布帛、五谷、车、方物", "柔顺、厚德、承载、吝啬"),
    "zhen": BaguaImage("长男、壮男、将帅、警察", "足、肝、声音、发", "龙、蛇、百虫、鹤", "东", "木竹、花草、鼓、蔬果", "奋发、躁动、进取、易怒"),
    "xun":  BaguaImage("长女、僧道、工匠、商人", "股、气、风疾、发", "鸡、飞虫、飞禽", "东南", "木香、绳索、风扇、长物", "入内、柔顺、进退、不果"),
    "kan":  BaguaImage("中男、渔人、盗匪、江湖", "耳、血、肾、泌尿", "豕、鱼、水中之物", "北", "水、沟渠、酒、舟轮", "险陷、隐伏、智慧、劳苦"),
    "li":   BaguaImage("中女、文人、军人、美人", "目、心、血脉", "雉、龟、蟹、孔雀", "南", "火、书画、甲胄、文明", "附丽、光明、外明、性急"),
    "gen":  BaguaImage("少男、童子、山人、僧道", "手、指、背、鼻", "狗、虎、鼠、熊", "东北", "山石、门阙、果实、床", "静止、稳重、固执、终止"),
    "dui":  BaguaImage("少女、歌伎、巫师、说客", "口、舌、喉、肺", "羊、鱼、水鸟", "西", "泽、金刃、乐器、缺物", "喜悦、言说、毁折、谗口"),
}


def leixiang_summary(trigram_key: str, name_zh: str, nature_zh: str) -> str:
    """Return a one-line 万物类象 summary for a trigram, e.g. ``乾为天：人物父老…``."""
    image = BAGUA_IMAGE[trigram_key]
    return (
        f"{name_zh}为{nature_zh}：人物{image.person}；身体{image.body}；"
        f"方位{image.direction}；物象{image.obj}；性情{image.temper}。"
    )


@dataclass(frozen=True)
class TiYongRelation:
    """One 体用生克 relation with its verdict, ordinal grade and judgement text."""

    key: str          # machine key, e.g. "yong_sheng_ti"
    name_zh: str      # 用生体 / 体克用 / 比和 / 体生用 / 用克体
    verdict: str      # 大吉 / 吉 / 小吉 / 小凶 / 大凶
    grade: int        # ordinal for ranking: +2 best … −2 worst
    base_score: int   # 吉凶指数 base (0-100) before 卦气/互变 adjustment
    text: str         # classical-flavoured judgement


# The five 体用生克 relations, keyed by relation name.
TIYONG_RELATIONS: dict[str, TiYongRelation] = {
    "yong_sheng_ti": TiYongRelation(
        "yong_sheng_ti", "用生体", "大吉", 2, 88,
        "用卦生扶体卦，外境助我、来意生身，谋为得利，所求顺遂，主有贵人财物之益，客反养主。",
    ),
    "bi_he": TiYongRelation(
        "bi_he", "体用比和", "吉", 1, 78,
        "体用五行比和，内外同心、主客相得，谋为顺遂，事易成就，彼此扶持而无相害。",
    ),
    "ti_ke_yong": TiYongRelation(
        "ti_ke_yong", "体克用", "小吉", 1, 68,
        "体卦克制用卦，我掌握主动、事在掌握，所求可成，惟须费力经营，稍迟乃得，主胜客。",
    ),
    "ti_sheng_yong": TiYongRelation(
        "ti_sheng_yong", "体生用", "小凶", -1, 42,
        "体卦生助用卦，我气外泄、精力耗散，谋事多付出而少收获，主损耗，宜节流守成。",
    ),
    "yong_ke_ti": TiYongRelation(
        "yong_ke_ti", "用克体", "大凶", -2, 24,
        "用卦克制体卦，受制于人于事、外境侵身，谋为不利，主有忧损灾咎，宜守不宜进。",
    ),
}


# 五行旺相休囚死 states with their interpretive text (relative to 月令/当令五行).
WANGSHUAI_TEXT: dict[str, str] = {
    "旺": "体卦当令而旺，气势正盛，吉者愈增其吉，凶者亦可稍减其凶，谋为有力。",
    "相": "体卦得令气所生而相，气机方长，助力渐盛，吉事可成，谋为有继。",
    "休": "体卦生令气而休，气势退闲，力道平平，吉者力薄、凶者势缓，宜静养待时。",
    "囚": "体卦克令气而囚，气势受困，进退维谷，吉者打折、凶者受制，谋为多阻。",
    "死": "体卦被令气所克而死，气势衰绝，吉亦难显、凶愈深重，宜守不宜动。",
}


def wangshuai_state(element: str, commanding: str) -> str:
    """Return the 旺相休囚死 state of ``element`` under the season's ``commanding`` element.

    Standard 五行 seasonal strength: same as the commanding element is 旺; generated
    by it is 相; generates it is 休; controls it is 囚; controlled by it is 死.
    """
    from app.content.wuxing import CONTROLS, GENERATES

    if element == commanding:
        return "旺"
    if GENERATES[commanding] == element:      # 令气生我 → 相
        return "相"
    if GENERATES[element] == commanding:      # 我生令气 → 休
        return "休"
    if CONTROLS[element] == commanding:       # 我克令气 → 囚
        return "囚"
    return "死"                                # 令气克我 → 死


# 月支 → 季节名 (for the 卦气 display); the 当令五行 itself comes from ZHI_ELEMENT.
SEASON_BY_MONTH_ZHI: dict[str, str] = {
    "寅": "孟春", "卯": "仲春", "辰": "季春",
    "巳": "孟夏", "午": "仲夏", "未": "季夏",
    "申": "孟秋", "酉": "仲秋", "戌": "季秋",
    "亥": "孟冬", "子": "仲冬", "丑": "季冬",
}
