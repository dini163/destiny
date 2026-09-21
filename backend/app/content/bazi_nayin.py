"""三十组纳音取象（不可变古典表，非运行时产物）。

取象句逐字转录自《三命通会·卷一·释六十甲子性质吉凶》（公版，四库全书本系统），
转排为简体；原书衍夺与不可辨之字以 `□` 标出，不作补字。每组只取该条首句 —— 原书
首句即"X者，……"的取象正文，其后的喜忌论述属格局推断，归 Task 9 的规则表而不归语料。

两处必要的说明：

* 原书三十条按 金火木土水 六组排列，本表按六十甲子顺序重排，文本不受影响。
* `nayin` 一名从排盘引擎（lunar-python）的用字，以便与盘面直接对照；原书用字不同时，
  `imagery` 仍照原书。三处差异：金泊金／金箔金、砂中金与砂中土／沙中金与沙中土、
  井泉水／泉中水。
"""

from dataclasses import dataclass, field

NAYIN_SOURCE = "《三命通会·卷一·释六十甲子性质吉凶》"


@dataclass(frozen=True)
class NayinCorpus:
    """Reference text for one 纳音 pair."""

    nayin: str                  # 三命通会/引擎通用名，如 大林木
    element: str                # 纳音五行
    imagery: str                # 原书取象首句，逐字转录
    source: str = NAYIN_SOURCE  # 全表同源，逐条重复只会稀释出处


# 键为两句干支连写（甲子乙丑），查表时亦可给单柱干支（甲子）；顺序即六十甲子顺序。
NAYIN_MEANING: dict[str, NayinCorpus] = {
    "甲子乙丑": NayinCorpus(
        nayin="海中金",
        element="金",
        imagery="海中金者，宝藏龙宫，珠孕蛟宝，出现虽假于空冲，成器无借乎火力，故东方朔以蛤蚌名之，良有理也。",
    ),
    "丙寅丁卯": NayinCorpus(
        nayin="炉中火",
        element="火",
        imagery="炉中火者，天地为炉，阴阳为炭，腾光辉于宇宙，成陶冶于乾坤。",
    ),
    "戊辰己巳": NayinCorpus(
        nayin="大林木",
        element="木",
        imagery="大林木者，枝干撼风，柯条撑月，耸壑昂霄之德，凌云蔽日之功。",
    ),
    "庚午辛未": NayinCorpus(
        nayin="路旁土",
        element="土",
        imagery="路旁土者，大地连途，平田万顷，禾稼赖以资生，草木由之畅茂。",
    ),
    "壬申癸酉": NayinCorpus(
        nayin="剑锋金",
        element="金",
        imagery="剑锋金者，白帝司权，刚由百炼，红光射于斗牛，白刃凝于霜雪。",
    ),
    "甲戌乙亥": NayinCorpus(
        nayin="山头火",
        element="火",
        imagery="山头火者，野焚燎原，延烧极目，依稀天际斜晖，仿佛山头落日，此乃九月烧荒，衰草尽烬之火也。",
    ),
    "丙子丁丑": NayinCorpus(
        nayin="涧下水",
        element="水",
        imagery="涧下水者，山环细浪，雪涌飞端，相连南北之流，对峙坎离之脉。",
    ),
    "戊寅己卯": NayinCorpus(
        nayin="城头土",
        element="土",
        imagery="城头土者，天京玉垒，帝里金城，龙盘千里之形，虎踞四维之势。",
    ),
    "庚辰辛巳": NayinCorpus(
        nayin="白蜡金",
        element="金",
        imagery="白蜡金者，昆山片玉，洛浦遗金，交栖日月之光，凝聚阴阳之气，形明体洁，乃金之正色也。",
    ),
    "壬午癸未": NayinCorpus(
        nayin="杨柳木",
        element="木",
        imagery="杨柳木者，隋堤袅娜，汉苑轻盈，万缕不蚕之丝，千条不针之带，午未木之死墓，壬癸木之滋润。",
    ),
    "甲申乙酉": NayinCorpus(
        nayin="泉中水",
        element="水",
        imagery="井泉水者，寒泉清冽，取养不穷，八家凿之以同饮，万民资之以生活。",
    ),
    "丙戌丁亥": NayinCorpus(
        nayin="屋上土",
        element="土",
        imagery="屋上土者，埏埴为林，水火既济，盖蔽雪霜之积，震凌风雨之功，此土瓦也。",
    ),
    "戊子己丑": NayinCorpus(
        nayin="霹雳火",
        element="火",
        imagery="霹雳火者，一缕毫光，九天号令，电掣金蛇之势，云驱铁马之奔。",
    ),
    "庚寅辛卯": NayinCorpus(
        nayin="松柏木",
        element="木",
        imagery="松柏木者，泼雪凑霜，参天覆地，风撼笙篁之奏，雨余旌旆之张。",
    ),
    "壬辰癸巳": NayinCorpus(
        nayin="长流水",
        element="水",
        imagery="长流水者，混混无穷，滔滔不竭，就下必纳于东南，顺流自归于辰巳。",
    ),
    "甲午乙未": NayinCorpus(
        nayin="沙中金",
        element="金",
        imagery="砂中金者，刚形布地，宝质藏砂，直教陶洗为珍，必须因人始贵。",
    ),
    "丙申丁酉": NayinCorpus(
        nayin="山下火",
        element="火",
        imagery="山下火者，草间熠耀，花理荧煌，寒林缀叶之光，隔幔点衣之彩，方朔以荧火名之……",
    ),
    "戊戌己亥": NayinCorpus(
        nayin="平地木",
        element="木",
        imagery="平地木者，初生萌蘖，始发枝条，唯资雨露之功，不喜雪霜之积，此乃地上之茂材，人间之屋木。",
    ),
    "庚子辛丑": NayinCorpus(
        nayin="壁上土",
        element="土",
        imagery="壁上土者，恃栋依梁，兴门立户，却暑御寒之德，遮霜护雪之功。",
    ),
    "壬寅癸卯": NayinCorpus(
        nayin="金箔金",
        element="金",
        imagery="金泊金者，润色杯盘，增光宫室，打薄须借乎别金，描彩必假乎水力。",
    ),
    "甲辰乙巳": NayinCorpus(
        nayin="覆灯火",
        element="火",
        imagery="覆灯火者，金盏光，玉台吐艳，照日月不照之处，明天地未明之时。",
    ),
    "丙午丁未": NayinCorpus(
        nayin="天河水",
        element="水",
        imagery="天河水者，乱洒六野，密沛千郊，淋淋泻下银河，细细飞来碧落，此乃天上雨露，发生万物，无不赖之。",
    ),
    "戊申己酉": NayinCorpus(
        nayin="大驿土",
        element="土",
        imagery="大驿土者，堂堂大道，坦坦平途，九州无所不通，万国无所不至，此乃位属坤方，德乃厚载，轮天转日，负海乘山之土也。",
    ),
    "庚戌辛亥": NayinCorpus(
        nayin="钗钏金",
        element="金",
        imagery="钗钏金者，美容首饰，增光腻肌，偎红倚翠之珍，枕玉眠香之宝，此金藏之闺阁，唯宜静水……",
    ),
    "壬子癸丑": NayinCorpus(
        nayin="桑柘木",
        element="木",
        imagery="桑柘木者，缯彩□□基，绮罗根本，士民飘飘之袂，圣贤楚楚之衣，此木供蚕为弧，其用甚大。",
    ),
    "甲寅乙卯": NayinCorpus(
        nayin="大溪水",
        element="水",
        imagery="大溪水者，惊涛薄岸，骇浪浮天，光涵万里之宽，碧倒千山之影，最喜有归有养……",
    ),
    "丙辰丁巳": NayinCorpus(
        nayin="沙中土",
        element="土",
        imagery="砂中土者，浪回所积，波渚而成，龙蛇盘隐之宫，陵谷变迁之地。",
    ),
    "戊午己未": NayinCorpus(
        nayin="天上火",
        element="火",
        imagery="天上火者，温暖山海，辉光宇宙，阳德丽天之照，阴精离海之明……",
    ),
    "庚申辛酉": NayinCorpus(
        nayin="石榴木",
        element="木",
        imagery="石榴木者，性辛如姜，花红似火，数颗枝头，累累多子，房内莹莹，干支纯金而纳音属木，乃木之变者也。",
    ),
    "壬戌癸亥": NayinCorpus(
        nayin="大海水",
        element="水",
        imagery="大海水者，总纳百川，汪洋无际，包括乾坤之大，升沉日月之光。",
    ),
}

NAYIN_COUNT = len(NAYIN_MEANING)

# 单柱干支 -> 成组条目；排盘给出的是 戊辰 这样的单柱，语料按 戊辰己巳 成组。
_BY_GANZHI: dict[str, NayinCorpus] = {
    text: entry
    for pair, entry in NAYIN_MEANING.items()
    for text in (pair, pair[:2], pair[2:])
}


def nayin_meaning(ganzhi: str) -> NayinCorpus:
    """Return the corpus entry for a 纳音 pair text or either of its two pillars."""
    try:
        return _BY_GANZHI[ganzhi]
    except KeyError:  # pragma: no cover - guarded by the corpus-count test
        raise KeyError(f"Unknown nayin pair: {ganzhi}") from None
