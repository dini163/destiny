"""十神释义与六亲对应（不可变古典表，非运行时产物）。

释义逐字转录自《渊海子平》各专论（通行本，公版），转排为简体；剋作克、綬作绶，
异体字与衍夺一字未改，句读照原书。出处一律到章，不到书 —— 释义与出处必须同源，
见 spec §3 决策二。

两个不得不记在纸面上的事实：

* 《三命通会》没有 论比肩 / 论劫财 两门，只有 论正官、论偏官、论正财、论偏财、
  论印绶、论食神、论伤官；《渊海子平》补齐 劫财 与 偏印（论倒食），比肩 则由
  论兄弟姊妹 首句定义。十神因此全部出自同一部书，不出现跨书混搭。
* `six_relations` 不是"男命/女命"通表，而是《渊海子平·六亲总篇》原句的片段。
  该章只给出九神的男命格与四神的女命格；它没写的格子留空 dict，前端整行不显示。
  常见教科书把 食神 说成男命之"子"，而原章作"男孙"（子为七杀），以原章为准。
"""

from dataclasses import dataclass

SIX_RELATION_SOURCE = "《渊海子平·六亲总篇》"


@dataclass(frozen=True)
class TenGodCorpus:
    """Reference text for one 十神."""

    ten_god: str
    group: str                      # 比劫 / 食伤 / 财 / 官杀 / 印
    cardinals: str                  # 心性短标签，本系统给 UI 用，不要求出处
    six_relations: dict[str, str]   # 男命 / 女命 -> 原章句片段；缺格即无出处
    meaning: str
    source: str


TEN_GOD_MEANING: dict[str, TenGodCorpus] = {
    "比肩": TenGodCorpus(
        ten_god="比肩",
        group="比劫",
        cardinals="自尊自立、平行交友",
        six_relations={"男命": "比肩为兄弟姐妹也"},
        meaning="比肩者，兄弟也。且如，甲见甲为兄，乙为弟妹；寅卯亦然。",
        source="《渊海子平·论兄弟姊妹》",
    ),
    "劫财": TenGodCorpus(
        ten_god="劫财",
        group="比劫",
        cardinals="争夺分财、防小人",
        six_relations={},  # 六亲总篇未为劫财立格，留空而非以通识补
        meaning=(
            "亦名『逆刃』，如乙见甲为劫财。乙以庚为夫，见丙克庚，故克夫；男命则克妻。"
            "五阳见五阴为败财，主克妻害子。五阴见五阳为劫财，主破耗、防小人，不克妻。"
        ),
        source="《渊海子平·论劫财》",
    ),
    "食神": TenGodCorpus(
        ten_god="食神",
        group="食伤",
        cardinals="宽厚享福、优游自足",
        six_relations={"男命": "食神是男孙", "女命": "食神是男"},
        meaning="食神者，生我财神之谓也；如甲属木，丙属火，名盗气，故谓之『食神』。",
        source="《渊海子平·论食神》",
    ),
    "伤官": TenGodCorpus(
        ten_god="伤官",
        group="食伤",
        cardinals="多才艺、傲物气高",
        six_relations={"男命": "伤官是女孙及祖母也", "女命": "伤官是女"},
        meaning="伤官者，其验如神。伤官务要伤尽；伤之不尽，官来乘旺，其祸不可胜言。",
        source="《渊海子平·论伤官》",
    ),
    "偏财": TenGodCorpus(
        ten_god="偏财",
        group="财",
        cardinals="慷慨好施、多情多诈",
        six_relations={"男命": "偏财是父，乃母之夫星也，亦为偏妻"},
        meaning=(
            "何谓之偏财？盖阳见阳财，阴见阴财也。然而偏财者，乃众人之财也，"
            "只恐兄弟姊妹有夺之，则福不全；若有官星，祸患百出。"
        ),
        source="《渊海子平·论偏财》",
    ),
    "正财": TenGodCorpus(
        ten_god="正财",
        group="财",
        cardinals="勤谨朴直、惜福守成",
        six_relations={"男命": "正财为妻"},
        meaning="何谓之正财？犹如正官之意；是阴见阳财，阳见阴财。大抵正财，吾妻之财也。",
        source="《渊海子平·论正财》",
    ),
    "七杀": TenGodCorpus(
        ten_god="七杀",
        group="官杀",
        cardinals="刚断果敢、威逼自成",
        six_relations={"男命": "七杀是男", "女命": "七杀是偏夫"},
        meaning=(
            "夫七杀者，亦名偏官，喜身旺合杀、喜制伏、喜阳刃；忌身弱、忌见财，生忌无制。"
            "身旺有气为偏官，身弱无制为七杀。"
        ),
        source="《渊海子平·论七杀》",
    ),
    "正官": TenGodCorpus(
        ten_god="正官",
        group="官杀",
        cardinals="端重守分、贵气循理",
        six_relations={"男命": "正官是女", "女命": "取官星为夫星"},
        meaning=(
            "夫正官者，甲见辛之类；乃阴见阳为官，阳见阴为鬼，阴阳配合成其道也。"
            "大抵要行官旺乡，月令是也。"
        ),
        source="《渊海子平·正官论》",
    ),
    "偏印": TenGodCorpus(
        ten_god="偏印",
        group="印",
        cardinals="孤介多能、有始无终",
        six_relations={"男命": "偏印偏母及祖父也"},
        meaning="夫倒食者，冲财神之谓也；一名『吞啗煞』。用财神大忌见之，用食神亦忌见之。",
        source="《渊海子平·论倒食》",
    ),
    "正印": TenGodCorpus(
        ten_god="正印",
        group="印",
        cardinals="慈悲好学、受荫安享",
        six_relations={"男命": "正印正母"},
        meaning=(
            "所谓印？生我者，即印绶也，经曰：『有官无印，即非真官；有印无官，反成其福。』"
        ),
        source="《渊海子平·论印绶》",
    ),
}

TEN_GOD_COUNT = len(TEN_GOD_MEANING)


def ten_god_meaning(ten_god: str) -> TenGodCorpus:
    """Return the corpus entry for a ten-god name."""
    try:
        return TEN_GOD_MEANING[ten_god]
    except KeyError:  # pragma: no cover - guarded by the corpus-count test
        raise KeyError(f"Unknown ten-god: {ten_god}") from None
