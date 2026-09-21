"""神煞查表与释义：《三命通会》《渊海子平》的通行取法，逐条署名。

每条只记"怎么查 + 查到什么 + 怎么说"，不含推算逻辑（推算在 engines/bazi_rules.py）。

转录期间发现的三处分歧，按"古籍怎么说是准"处理并留在此处，避免后来人以为漏写：

- 文昌贵人：《三命通会·卷三》自带的"文昌贵"韵文是另一套表（甲巳 乙亥 丙戌 丁辰 戊申
  己午 庚寅 辛未 壬卯 癸丑），《渊海子平》全篇无文昌。本系统取通行表，它恰好等于
  日干禄顺数第三辰（见 `建禄`），即与羊刃"禄前一辰"、金舆"禄前二辰"同族；出处因此
  记在禄表上，而不是那句韵文上。
- 羊刃：《三命通会》作"羊刃"、《渊海子平》作"阳刃"，同一神煞两名；取法一致（禄前一辰、
  只有五阳干有刃）。
- 十二长生：它出现在下表是为了让 UI 有处取释义，**不作为神煞命中行输出** —— 逐柱取值
  已在 `BaziPillar.di_shi`，神煞行再复读一遍就是同一事实两处口径。
"""

from dataclasses import dataclass

_BRANCH_ORDER = "子丑寅卯辰巳午未申酉戌亥"

SAN_HE_GROUPS: tuple[tuple[str, str, str], ...] = (
    ("申", "子", "辰"), ("亥", "卯", "未"), ("寅", "午", "戌"), ("巳", "酉", "丑"),
)


@dataclass(frozen=True)
class ShenShaRule:
    """一条神煞的取法：拿什么去查（lookup）、查到的字符匹配什么（target）、怎么说（meaning）。

    ``lookup`` ∈ day_gan | month_zhi | month_zhi_group | year_and_day_group | day_pillar
    | void | life_stage；``target`` ∈ gan | zhi | gan_or_zhi | pillar | none。
    两轴必须各自明确：天德以月支查、查出来可能是天干也可能是支；咸池以三合局查、查出来是支。
    """

    name: str
    lookup: str
    target: str
    quality: str  # 吉 | 凶 | 中性 —— 本系统对三值的归并口径，吉凶在此不赋分
    table: dict[str, tuple[str, ...]] | tuple[str, ...]
    meaning: str
    source: str


def san_he_group(zhi: str) -> str | None:
    """该支所属的三合局，如 '申子辰'；不在任何一局则 None（十二支恒有值）。"""
    return next(("".join(group) for group in SAN_HE_GROUPS if zhi in group), None)


def _advance(zhi: str, steps: int) -> str:
    """支序上前移若干辰，用于按'禄前 n 辰'一族规则铺表。"""
    return _BRANCH_ORDER[(_BRANCH_ORDER.index(zhi) + steps) % len(_BRANCH_ORDER)]


_LU_BY_GAN: dict[str, str] = {
    "甲": "寅", "乙": "卯", "丙": "巳", "丁": "午", "戊": "巳",
    "己": "午", "庚": "申", "辛": "酉", "壬": "亥", "癸": "子",
}

SHENSHA_RULES: dict[str, ShenShaRule] = {
    "天乙贵人": ShenShaRule(
        name="天乙贵人", lookup="day_gan", target="zhi", quality="吉",
        table={"甲": ("丑", "未"), "戊": ("丑", "未"), "庚": ("丑", "未"),
               "乙": ("子", "申"), "己": ("子", "申"),
               "丙": ("亥", "酉"), "丁": ("亥", "酉"),
               "壬": ("卯", "巳"), "癸": ("卯", "巳"),
               "辛": ("午", "寅")},
        meaning="天乙者，乃天上之神，其神最尊贵，所至之处，一切凶煞隐然而避。",
        source="《三命通会·论天乙贵人》",
    ),
    "文昌贵人": ShenShaRule(
        name="文昌贵人", lookup="day_gan", target="zhi", quality="吉",
        table={gan: (_advance(zhi, 3),) for gan, zhi in _LU_BY_GAN.items()},
        meaning="文昌与天乙、太极同为贵神之类，主学业文思；本表以日干禄顺数第三辰取之。",
        source="《三命通会·论十干禄》禄表·禄前第三辰（《三命通会·卷三》文昌贵别本未采）",
    ),
    "太极贵人": ShenShaRule(
        name="太极贵人", lookup="day_gan", target="zhi", quality="吉",
        table={"甲": ("子", "午"), "乙": ("子", "午"),
               "丙": ("卯", "酉"), "丁": ("卯", "酉"),
               "戊": ("辰", "戌", "丑", "未"), "己": ("辰", "戌", "丑", "未"),
               "庚": ("寅", "亥"), "辛": ("寅", "亥"),
               "壬": ("巳", "申"), "癸": ("巳", "申")},
        meaning="太极者，太初也，始也，物造于初为太极，成也，收也；造化始终相保，乃曰太极贵也。",
        source="《三命通会·论太极贵》",
    ),
    "建禄": ShenShaRule(
        name="建禄", lookup="day_gan", target="zhi", quality="中性",
        table={gan: (zhi,) for gan, zhi in _LU_BY_GAN.items()},
        meaning="禄，爵禄也，当得势而享，乃谓之禄；十干就支神为禄，谓禄随旺行。",
        source="《三命通会·论十干禄》",
    ),
    "羊刃": ShenShaRule(
        name="羊刃", lookup="day_gan", target="zhi", quality="凶",
        table={gan: (_advance(_LU_BY_GAN[gan], 1),) for gan in ("甲", "丙", "戊", "庚", "壬")},
        meaning="羊言刚也，刃者取宰割之义；禄过则刃生，功成当退不退则过。"
                "甲丙戊庚壬五阳有刃，乙丁己辛癸五阴无刃。",
        source="《三命通会·论羊刃》（《渊海子平》作『论阳刃』）",
    ),
    "金舆": ShenShaRule(
        name="金舆", lookup="day_gan", target="zhi", quality="吉",
        table={gan: (_advance(zhi, 2),) for gan, zhi in _LU_BY_GAN.items()},
        meaning="舆者，车也，金者，贵之义也，譬之君子居官得禄，须坐车以载之，故金舆常居禄前二辰。"
                "主人性柔貌愿，举止温克；妇人逢之，不富即贵。",
        source="《三命通会·论金舆》",
    ),
    "咸池": ShenShaRule(
        name="咸池", lookup="year_and_day_group", target="zhi", quality="中性",
        table={"申子辰": ("酉",), "寅午戌": ("卯",), "巳酉丑": ("午",), "亥卯未": ("子",)},
        meaning="五行沐浴之地，名咸池，一名败神、一名桃花煞。生旺则美容仪，死绝则落魄不检；"
                "咸池非吉煞，日时与水命遇之尤凶。",
        source="《三命通会·论咸池》",
    ),
    "驿马": ShenShaRule(
        name="驿马", lookup="year_and_day_group", target="zhi", quality="中性",
        table={"申子辰": ("寅",), "寅午戌": ("申",), "巳酉丑": ("亥",), "亥卯未": ("巳",)},
        meaning="驿马者，三命中发用，喜庆之神。君子遇之常居荣位，小人主丰赡；"
                "凡柱中马，若不值空亡、破败、交退、伏神，须荣贵。",
        source="《三命通会·论驿马》",
    ),
    "华盖": ShenShaRule(
        name="华盖", lookup="year_and_day_group", target="zhi", quality="中性",
        table={"申子辰": ("辰",), "寅午戌": ("戌",), "巳酉丑": ("丑",), "亥卯未": ("未",)},
        meaning="华盖者，喻如宝盖，以三合底处得库谓之。凡人命得华盖，多主孤寡，"
                "总贵亦不免孤独，作僧道艺术论。",
        source="《三命通会·论将星华盖》",
    ),
    "将星": ShenShaRule(
        name="将星", lookup="year_and_day_group", target="zhi", quality="吉",
        table={"申子辰": ("子",), "寅午戌": ("午",), "巳酉丑": ("酉",), "亥卯未": ("卯",)},
        meaning="将星者，如将札中军也，故以三合中位谓之将星；常欲吉星相扶、贵煞加临乃为吉庆。",
        source="《三命通会·论将星华盖》",
    ),
    "劫煞": ShenShaRule(
        name="劫煞", lookup="year_and_day_group", target="zhi", quality="凶",
        table={"申子辰": ("巳",), "寅午戌": ("亥",), "巳酉丑": ("寅",), "亥卯未": ("申",)},
        meaning="劫者，夺也，自外夺之之谓夺；劫在五行绝处。"
                "古歌云：劫煞为灾不可当，徒然奔走名利场。",
        source="《三命通会·论劫煞亡神》",
    ),
    "亡神": ShenShaRule(
        name="亡神", lookup="year_and_day_group", target="zhi", quality="凶",
        table={"申子辰": ("亥",), "寅午戌": ("巳",), "巳酉丑": ("申",), "亥卯未": ("寅",)},
        meaning="亡者，失也，自内失之之谓亡；亡在五行临官。"
                "古歌云：亡神七煞祸非轻，用尽机关一不成。",
        source="《三命通会·论劫煞亡神》",
    ),
    "天德贵人": ShenShaRule(
        name="天德贵人", lookup="month_zhi", target="gan_or_zhi", quality="吉",
        table={"寅": ("丁",), "卯": ("申",), "辰": ("壬",), "巳": ("辛",), "午": ("亥",),
               "未": ("甲",), "申": ("癸",), "酉": ("寅",), "戌": ("丙",), "亥": ("乙",),
               "子": ("巳",), "丑": ("庚",)},
        meaning="天德者，神藏煞没之宫，能回凶作善。凡命中带凶煞得之，凶不为甚；"
                "凡人得之，一生安逸，不犯刑、不逢盗。",
        source="《三命通会·论天月德》",
    ),
    "月德贵人": ShenShaRule(
        name="月德贵人", lookup="month_zhi_group", target="gan", quality="吉",
        table={"寅午戌": ("丙",), "申子辰": ("壬",), "亥卯未": ("甲",), "巳酉丑": ("庚",)},
        meaning="月德者，乃三合所照之方、日月会合之辰。盖日月照临之宫，凡天曜地煞尽可制服，"
                "故可回凶作吉。",
        source="《三命通会·论天月德》",
    ),
    "魁罡": ShenShaRule(
        name="魁罡", lookup="day_pillar", target="pillar", quality="中性",
        table=("庚辰", "庚戌", "壬辰", "戊戌"),
        meaning="魁罡者有四：壬辰、庚戌、戊戌、庚辰日是也。主人性格聪明、文章振发、临事有断，"
                "惟是好杀；若四柱有财及官、或带刑杀，祸不可测。",
        source="《渊海子平·论魁罡》",
    ),
    "空亡": ShenShaRule(
        name="空亡", lookup="void", target="zhi", quality="中性",
        table={},
        meaning="空亡者，甲旬尽处也；有是位而无禄曰空，有支而无干曰亡。"
                "然空而有实，亡而有存，所以未可便为凶论。",
        source="《三命通会·论空亡》（查表沿用 LunarUtil.XUN_KONG）",
    ),
    "十二长生": ShenShaRule(
        name="十二长生", lookup="life_stage", target="none", quality="中性",
        table={},
        meaning="盛德乘时曰旺；长生、沐浴、冠带、临官、帝旺、衰、病、死、墓、绝、胎、养，"
                "逐宫而气不同。本系统只注其位，不作神煞命中行。",
        source="《三命通会·论五行旺相休囚死并寄生十二宫》",
    ),
}
SHENSHA_COUNT = len(SHENSHA_RULES)


def shen_sha_rule(name: str) -> ShenShaRule:
    """Return the lookup rule for a 神煞 by name."""
    try:
        return SHENSHA_RULES[name]
    except KeyError:
        raise KeyError(f"Unknown shen sha: {name}") from None
