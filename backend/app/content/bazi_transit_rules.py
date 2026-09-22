"""岁运规则表（spec §6.2）：46 条、9 族，只定价与断语，不含命中逻辑。

条件全在别处已经推出来的事实上：`derive_relations` 的 15 种关系、
`derive_branch_groups` 的三合/半合/三会、`derive_shensha` 的落点、合成柱自带的
`di_shi` 与十神、`select_yongshen` 的喜忌集。本表不碰历法，所以它不需要第二条
真值来源；键序即账本序，`engines/bazi_transit._PREDICATES` 一项对一行。

`scopes` 是粒度域：`taisui`（太岁只论年支）与 `dayun`（大运只与流年论生克）不参与
流月与流日，其余 35 条岁、月、日通用。中性神煞一律不定价 —— 给中性者定价等于凭空
发明吉凶（见 §6.2 表末说明），它们仍随 `ShenShaEntry` 呈现。

术语口径：**除 `dayun` 族外，本表的「运」恒指当前粒度那一根岁运柱** —— 年卡指流年、
月卡指流月、日卡指流日。短名不随粒度 fork，靠 `（流月）`/`（流日）` 后缀与段名消歧
（spec §6.4 决策 10 展开三条路与代价）。

delta 与 `DimensionRule` 同理，全是本系统模型参数：四书只给定性条件，从不给数。
判语为单句、不带句读，引文从署名章里截取到可读的最短一段。
"""

from pydantic import BaseModel, ConfigDict, Field

#: 岁运基准分，含义同 `DIMENSION_BASE`：中性的起评，不是"及格"。
TRANSIT_BASE = 50.0

TRANSIT_RULE_SOURCE = (
    "命中条件与判语引《三命通会》《渊海子平》《滴天髓》；"
    "赋分为本系统模型参数（古籍只给喜忌序，从不给数）"
)


class TransitRule(BaseModel):
    model_config = ConfigDict(frozen=True)

    key: str = Field(description="机器可读规则键，同时是 ScoreFactor.rule。")
    label: str = Field(description="账本行短名；神煞族逐字等于 SHENSHA_RULES 的神煞名。")
    family: str = Field(description="九族之一，键的前缀必须与之一致。")
    delta: float = Field(description="分值增减，本系统模型参数（古籍不给数）。")
    scopes: tuple[str, ...] = Field(description='粒度域："sui" 流年、"yue" 流月、"ri" 流日。')
    reading: str = Field(description="单句判语，无句读，末尾自署四书或'本系统'。")


def _rule(key: str, label: str, family: str, delta: float, scopes: tuple[str, ...], reading: str) -> TransitRule:
    return TransitRule(
        key=key, label=label, family=family, delta=delta, scopes=scopes, reading=reading
    )


_BOTH = ("sui", "yue", "ri")  # 35 条：岁、月、日通用（spec §6.1）
_SUI = ("sui",)  # 11 条：太岁 6 + 大运 5，只论年

_RULE_LIST: tuple[TransitRule, ...] = (
    # --- yongshen：喜忌直接取 select_yongshen 的合并结果，不重算 ---
    _rule(
        "yongshen.gan_favourable", "运干入喜用", "yongshen", 10.0, _BOTH,
        "岁运天干是我喜用之五行，所临之年月事来顺意（本系统喜忌由扶抑、通关、调候三法合出）",
    ),
    _rule(
        "yongshen.gan_unfavourable", "运干入忌", "yongshen", -10.0, _BOTH,
        "岁运天干是我忌神之五行，其干所临年月宜守不宜攻（本系统以喜忌集定向背）",
    ),
    _rule(
        "yongshen.zhi_favourable", "运支主气入喜用", "yongshen", 8.0, _BOTH,
        "支以本气为主，本气入喜用则其年月根基得助（本系统取藏干首位为本气，与赋分权重同源）",
    ),
    _rule(
        "yongshen.zhi_unfavourable", "运支主气入忌", "yongshen", -8.0, _BOTH,
        "支之本气为忌，其年月所临之地先失其据（本系统以喜忌集定向背）",
    ),
    # --- taisui：太岁只论流年支与生年支这一对 ---
    _rule(
        "taisui.chong", "冲太岁", "taisui", -10.0, _SUI,
        "岁支冲我生年支，谓之冲太岁，其年动摇（《三命通会·论冲击》）",
    ),
    _rule(
        "taisui.value", "值太岁", "taisui", -6.0, _SUI,
        "岁支与生年支同字谓之值太岁，其年为本命之年（本系统单判，四书无以同支论吉凶之明文）",
    ),
    _rule(
        "taisui.harm", "害太岁", "taisui", -5.0, _SUI,
        "岁支害我生年支，谓之害太岁，其年多口舌（《三命通会·论六害》）",
    ),
    _rule(
        "taisui.punish", "刑太岁", "taisui", -5.0, _SUI,
        "岁支与生年支构成三刑或自刑，谓之刑太岁（《三命通会·论三刑》）",
    ),
    _rule(
        "taisui.break", "破太岁", "taisui", -3.0, _SUI,
        "岁支破我生年支，破义轻于冲害，本系统只取古籍所立四对（《三命通会·卷三·总论诸神煞》破煞）",
    ),
    _rule(
        "taisui.combine", "合太岁", "taisui", 5.0, _SUI,
        "岁支与我生年支六合，其年得和（《三命通会·论支元六合》）",
    ),
    # --- palace：提纲与身宫为至近之地，权重高于余支 ---
    _rule(
        "palace.chong_month", "冲提纲", "palace", -8.0, _BOTH,
        "岁运之支冲月令，提纲为八柱之纲领，冲之则一年之令不专（《三命通会·论冲击》）",
    ),
    _rule(
        "palace.chong_day", "冲本身宫", "palace", -8.0, _BOTH,
        "岁运之支冲日支，日为身宫，冲之则一身不安（《三命通会·论冲击》）",
    ),
    _rule(
        "palace.punish_month", "刑提纲", "palace", -5.0, _BOTH,
        "岁运之支与月支构成三刑，所刑在提纲（《三命通会·论三刑》）",
    ),
    _rule(
        "palace.punish_day", "刑本身宫", "palace", -5.0, _BOTH,
        "岁运之支与日支构成三刑，所刑在身宫与配偶之宫（《三命通会·论三刑》）",
    ),
    _rule(
        "palace.combine_month", "合提纲", "palace", 4.0, _BOTH,
        "岁运之支与月支六合，提纲被合则其令有所牵（《三命通会·论支元六合》）",
    ),
    _rule(
        "palace.combine_day", "合本身宫", "palace", 5.0, _BOTH,
        "岁运之支与日支六合，身宫得合则其年和缓（《三命通会·论支元六合》）",
    ),
    _rule(
        "palace.harm_month", "害提纲", "palace", -4.0, _BOTH,
        "岁运之支害月支，六害之及于提纲（《三命通会·论六害》）",
    ),
    _rule(
        "palace.harm_day", "害本身宫", "palace", -4.0, _BOTH,
        "岁运之支害日支，六害之及于身宫（《三命通会·论六害》）",
    ),
    # --- heyue：合出的五行本身不论吉凶，向背一律由喜忌定 ---
    _rule(
        "heyue.sanhe_favourable", "三合成喜用", "heyue", 6.0, _BOTH,
        "岁运之支与我两支三支齐见合成一局，所化之五行入喜用（《三命通会·论支元三合》）",
    ),
    _rule(
        "heyue.sanhe_unfavourable", "三合成忌", "heyue", -6.0, _BOTH,
        "三支齐见合成一局而所化入忌，其年聚于我所恶（《三命通会·论支元三合》）",
    ),
    _rule(
        "heyue.anhe_favourable", "半合喜用", "heyue", 3.0, _BOTH,
        "岁运之支与我一支得局中旺支而成半合，其五行入喜用（半合之名为本系统标法，出处见《三命通会·论支元三合》）",
    ),
    _rule(
        "heyue.anhe_unfavourable", "半合忌", "heyue", -3.0, _BOTH,
        "半合所聚之气入忌，其年月聚而不化（本系统以半合须含旺支为判，向背取自喜忌集）",
    ),
    _rule(
        "heyue.sanhui_favourable", "三会喜用", "heyue", 5.0, _BOTH,
        "岁运之支与我两支成一方之气，所会五行入喜用（《滴天髓·方局论》）",
    ),
    _rule(
        "heyue.sanhui_unfavourable", "三会忌", "heyue", -5.0, _BOTH,
        "一方之气会成忌神，其年月气势虽盛反为累（《滴天髓·方局论》）",
    ),
    # --- ganzhi：天干只与日主论合冲 ---
    _rule(
        "ganzhi.combine_day_master", "运干合日主", "ganzhi", 5.0, _BOTH,
        "岁运天干与日主成天干五合，其年有相引之情（《三命通会·论十干合》）",
    ),
    _rule(
        "ganzhi.chong_day_master", "运干冲日主", "ganzhi", -5.0, _BOTH,
        "岁运天干与日主七位相冲，其年正面相抗（《三命通会·论冲击》，戊己中央不冲为本系统取法）",
    ),
    # --- fuyin：整柱比较，extra 已参与扫描 ---
    _rule(
        "fuyin.fuyin", "伏吟", "fuyin", -5.0, _BOTH,
        "岁运之柱与命局一柱干支全同，谓之伏吟，其年重复难进（《三命通会·卷二·总论岁运》）",
    ),
    _rule(
        "fuyin.fanyin", "反吟", "fuyin", -8.0, _BOTH,
        "岁运之柱与命局一柱天干相冲、地支六冲，谓之反吟（《三命通会·卷二·总论岁运》，窄口径为本系统取法）",
    ),
    # --- dayun：只与流年论，童年段大运无干支故整族不评估 ---
    _rule(
        "dayun.binglin", "岁运并临", "dayun", -8.0, _SUI,
        "流年干支与大运干支全同，谓之岁运并临（《三命通会·卷二·总论岁运》）",
    ),
    _rule(
        "dayun.fanyin", "运年反吟", "dayun", -8.0, _SUI,
        "大运之柱与流年之柱天干相冲、地支六冲，谓之运年反吟（《三命通会·卷二·总论岁运》）",
    ),
    _rule(
        "dayun.yun_sheng_sui", "运生岁", "dayun", 4.0, _SUI,
        "大运之五行生流年之五行，其年得运之力（本系统以五行相生定运岁关系）",
    ),
    _rule(
        "dayun.sui_sheng_yun", "岁生运", "dayun", 4.0, _SUI,
        "流年之五行生大运之五行，运受岁之养而气不壅（本系统以五行相生定运岁关系）",
    ),
    _rule(
        "dayun.gan_he", "运岁干合", "dayun", 4.0, _SUI,
        "大运天干与流年天干成五合，运岁相合其年有情（《三命通会·论十干合》）",
    ),
    # --- dishi：日主在岁运支上的十二长生，沐浴一书两说故不定价 ---
    _rule(
        "dishi.prosperous", "日主临官帝旺", "dishi", 7.0, _BOTH,
        "岁运之支为日主临官、帝旺之地，其年月得地（《三命通会·论五行旺相休囚死并寄生十二宫》）",
    ),
    _rule(
        "dishi.supportive", "日主临长生冠带胎养", "dishi", 4.0, _BOTH,
        "岁运之支在日主长生、冠带、胎、养四位，其年月气方长（《三命通会·论五行旺相休囚死并寄生十二宫》）",
    ),
    _rule(
        "dishi.decaying", "日主临衰病死墓绝", "dishi", -6.0, _BOTH,
        "岁运之支在日主衰、病、死、墓、绝五位，其年月气退（《三命通会·论五行旺相休囚死并寄生十二宫》，沐浴两说故不定价）",
    ),
    # --- shensha：只给七吉三凶定价，label 逐字等于 SHENSHA_RULES 的神煞名 ---
    _rule(
        "shensha.tianyi", "天乙贵人", "shensha", 5.0, _BOTH,
        "贵人临岁运之支，其年月所至得贵人（《三命通会·论天乙贵人》）",
    ),
    _rule(
        "shensha.jiangxing", "将星", "shensha", 4.0, _BOTH,
        "将星入岁运之支，其年可得众（《三命通会·论将星华盖》）",
    ),
    _rule(
        "shensha.wenchang", "文昌贵人", "shensha", 4.0, _BOTH,
        "文昌临岁运，其年月文书可倚（《三命通会·论十干禄》禄前第三辰）",
    ),
    _rule(
        "shensha.tiande", "天德贵人", "shensha", 4.0, _BOTH,
        "天德在岁运之干支，其年有解（《三命通会·论天月德》）",
    ),
    _rule(
        "shensha.yuede", "月德贵人", "shensha", 4.0, _BOTH,
        "月德在岁运之干，其年月德神加临（《三命通会·论天月德》）",
    ),
    _rule(
        "shensha.jinyu", "金舆", "shensha", 3.0, _BOTH,
        "金舆临岁运之支，其年月出入安适（《三命通会·论金舆》）",
    ),
    _rule(
        "shensha.taiji", "太极贵人", "shensha", 3.0, _BOTH,
        "太极贵人临岁运，其年月心神清明（《三命通会·论太极贵》）",
    ),
    _rule(
        "shensha.yangren", "羊刃", "shensha", -6.0, _BOTH,
        "岁运之支为日主羊刃，刚刃易伤（《三命通会·论羊刃》，刃以日干取、五阳干方有）",
    ),
    _rule(
        "shensha.jiesha", "劫煞", "shensha", -5.0, _BOTH,
        "劫煞临岁运之支，其年月防夺（《三命通会·论劫煞亡神》）",
    ),
    _rule(
        "shensha.wangshen", "亡神", "shensha", -5.0, _BOTH,
        "亡神临岁运之支，其年月防失（《三命通会·论劫煞亡神》）",
    ),
)

#: key -> 规则行。**字典序即账本序**：`build_ledger` 按命中行的键回查本表，
#: 而 `_PREDICATES` 的枚举顺序与本表逐行对齐（§9.5 的完备性测钉住）。
TRANSIT_RULES: dict[str, TransitRule] = {rule.key: rule for rule in _RULE_LIST}

TRANSIT_RULE_COUNT = len(TRANSIT_RULES)
TRANSIT_FAMILIES: tuple[str, ...] = tuple(dict.fromkeys(rule.family for rule in _RULE_LIST))


def transit_rule(key: str) -> TransitRule:
    """按键回查规则行。键写错即报错，不许静默漏掉一条账本行。"""
    try:
        return TRANSIT_RULES[key]
    except KeyError:
        raise KeyError(f"Unknown transit rule: {key}") from None
