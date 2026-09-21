"""六维详批规则表（spec §6.6）：39 条命中条件背后的判语与分值，逐条署名。

本表只记"这一条怎么说、记几分"，不含命中逻辑（条件在 `engines/bazi_interpret.py`）。

三条写在纸面上的取舍：

- delta 全是本系统模型参数：古籍只给定性条件（"身旺任财""财多身弱"），从不给数，
  所以 `ScoreFactor.source` 整表恒为 ``MODEL_PARAM_SOURCE``，不在此逐条重复。
- 判语是**单句**，不带句读（无。无；），引文从署名章里截取到可读的最短一段，
  截取处不补字、不改字，句读与原文一致。
- 五行配脏腑/经络出自《黄帝内经》，不在本项目允许署名的四本公版语料内，
  故健康维各句只署"本系统"，不冒充医经出处。
"""

from pydantic import BaseModel, ConfigDict, Field


class DimensionRule(BaseModel):
    model_config = ConfigDict(frozen=True)

    key: str = Field(description="机器可读规则键，同时是 ScoreFactor.rule。")
    label: str = Field(description="账本与 strengths/cautions 用的短名。")
    delta: float = Field(description="分值增减，本系统模型参数（古籍不给数）。")
    reading: str = Field(description="单句判语，无句读，末尾自署四书或'本系统'。")


DIMENSION_ORDER = ("事业", "财运", "婚姻", "健康", "学业", "人际")
DIMENSION_BASE = 50.0

DIMENSION_RULES: dict[str, tuple[DimensionRule, ...]] = {
    "事业": (
        DimensionRule(
            key="career.officer.present", label="官星有力", delta=10.0,
            reading="官为可任之事，一位纯粹最贵（《三命通会·论正官》『正官为六格之首，止许一位』）",
        ),
        DimensionRule(
            key="career.officer.favourable", label="官星为喜用", delta=12.0,
            reading="官星之五行又入日主喜用，则所任为名位而非负担（本系统喜忌出自扶抑通关调候三法）",
        ),
        DimensionRule(
            key="career.officer.unfavourable", label="官星为忌", delta=-10.0,
            reading="官星属忌，其克身为压力而非职分（本系统以喜忌集定官星向背）",
        ),
        DimensionRule(
            key="career.officer.restrained", label="杀有制化", delta=8.0,
            reading="七杀得食神制之则不为攻身之凶（《三命通会·论偏官》引古歌『身弱煞强无制神，多生灾祸不堪论』）",
        ),
        DimensionRule(
            key="career.structure.success", label="格局成格", delta=10.0,
            reading="月令所成之格得相喜之神则有用，所任之事有主（本系统按四书逐格相喜之神判成格）",
        ),
        DimensionRule(
            key="career.star.jiangxing", label="将星临命", delta=6.0,
            reading="将星如中军之札，主可得众（《三命通会·论将星华盖》『常欲吉星相扶、贵煞加临乃为吉庆』）",
        ),
        DimensionRule(
            key="career.star.wenchang", label="文昌照命", delta=4.0,
            reading="文昌居贵神之类，主文书可倚（《三命通会·论十干禄》禄前第三辰）",
        ),
        DimensionRule(
            key="career.body.weak-under-officer", label="身弱承压", delta=-12.0,
            reading="身弱而官杀有力，则受制而难任（《渊海子平·论七杀》『身旺有气为偏官，身弱无制为七杀』）",
        ),
    ),
    "财运": (
        DimensionRule(
            key="wealth.star.present", label="财星成形", delta=10.0,
            reading="财为养命之源，一位成形则财有可取（《渊海子平·论正财》『大抵正财，吾妻之财也』）",
        ),
        DimensionRule(
            key="wealth.star.favourable", label="财星为喜用", delta=12.0,
            reading="财星之五行入喜用，则财来养身而非耗身（本系统以喜忌集定财星向背）",
        ),
        DimensionRule(
            key="wealth.body.carries", label="身强任财", delta=10.0,
            reading="身旺乃可任财（《三命通会·论正财》『财须身旺方任，无官食为援则财孤』）",
        ),
        DimensionRule(
            key="wealth.body.overloaded", label="财多身弱", delta=-12.0,
            reading="财多而身不胜，是谓太过（《三命通会·论正财》引古歌『财多身弱，柱无印助』）",
        ),
        DimensionRule(
            key="wealth.source.output", label="食伤生财", delta=6.0,
            reading="我生之气能生我财，财源有续（《渊海子平·论食神》『食神者，生我财神之谓也』）",
        ),
        DimensionRule(
            key="wealth.robbing.parallel", label="比劫夺财", delta=-8.0,
            reading="同气多则财分，众人之财恐有夺之者（《渊海子平·论偏财》『只恐兄弟姊妹有夺之，则福不全』）",
        ),
        DimensionRule(
            key="wealth.guarded.officer", label="官星护财", delta=4.0,
            reading="财得其官则不为劫夺（《三命通会·论偏财》引古歌『偏财身旺要官星，运入乡发利名』）",
        ),
    ),
    "婚姻": (
        DimensionRule(
            key="marriage.star.present", label="配偶星有力", delta=10.0,
            reading="男以正财为妻、女取官星为夫星，星有力则婚姻有主（《渊海子平·六亲总篇》）",
        ),
        DimensionRule(
            key="marriage.star.favourable", label="星与身喜", delta=8.0,
            reading="配偶星之五行又为日主喜用，身与星不相背（本系统以喜忌集定星之向背）",
        ),
        DimensionRule(
            key="marriage.palace.intact", label="配偶宫无破", delta=8.0,
            reading="日支为配偶之宫，无冲无害无刑则宫安（本系统以日支为宫、以支系冲破刑害为破）",
        ),
        DimensionRule(
            key="marriage.palace.clashed", label="配偶宫逢冲", delta=-12.0,
            reading="宫位逢冲则气动不宁（《三命通会·论冲击》『十二支战击之神，大概为凶』）",
        ),
        DimensionRule(
            key="marriage.palace.bound", label="宫位有合", delta=5.0,
            reading="宫位有合则有牵系，福之轻重随所合而定（《三命通会·论支元六合》『合者，和也，乃阴阳相和，其气自合』）",
        ),
        DimensionRule(
            key="marriage.peachy.pool", label="咸池临命", delta=-5.0,
            reading="咸池为败神一名桃花煞（《三命通会·论咸池》『咸池非吉煞，日时与水命遇之尤凶』）",
        ),
        DimensionRule(
            key="marriage.output-hurts-officer", label="伤官见官", delta=-8.0,
            reading="女命以官为夫，伤官乘旺则夫星被克（《渊海子平·论伤官》『伤之不尽，官来乘旺，其祸不可胜言』）",
        ),
    ),
    "健康": (
        DimensionRule(
            key="health.balance.peaceful", label="气血平和", delta=10.0,
            reading="日主中和则气无偏胜（本系统三因子档位定中和，非古籍赋分）",
        ),
        DimensionRule(
            key="health.root.sturdy", label="根本有荫", delta=6.0,
            reading="印为生气、比劫为同气，二有力则根柢有荫（《三命通会·论印绶》『乃我气之源，为生气，为父母』）",
        ),
        DimensionRule(
            key="health.element.excessive", label="一行偏亢", delta=-8.0,
            reading="一行独居命局大半，其气偏亢（本系统按五行加权分占比判偏亢）",
        ),
        DimensionRule(
            key="health.element.lacking", label="一行全无", delta=-8.0,
            reading="一行全缺则其气不备（本系统按五行加权分为零判缺，五行配属亦为本系统归类）",
        ),
        DimensionRule(
            key="health.void.branch", label="空亡临支", delta=-4.0,
            reading="空亡在支，是有位而无禄（《三命通会·论空亡》『有是位而无禄曰空，有支而无干曰亡』）",
        ),
        DimensionRule(
            key="health.flow.unobstructed", label="五行流转", delta=6.0,
            reading="五行各得其气则流转不穷（本系统以五行加权分下限判流转）",
        ),
    ),
    "学业": (
        DimensionRule(
            key="study.seal.present", label="印星为学之本", delta=12.0,
            reading="印者，生我之名，学业有所受（《三命通会·论印绶》『印绶者，乃五行生我之名』）",
        ),
        DimensionRule(
            key="study.seal.favourable", label="印为喜用", delta=6.0,
            reading="印星之五行入喜用，则受荫而能化（本系统以喜忌集定印之向背）",
        ),
        DimensionRule(
            key="study.output.present", label="食伤吐秀", delta=8.0,
            reading="我生之气外发为才（《渊海子平·论食神》『名盗气，故谓之食神』）",
        ),
        DimensionRule(
            key="study.wenchang", label="文昌照命", delta=10.0,
            reading="文昌与天乙、太极同为贵神之类，主学业文思（《三命通会·论十干禄》禄前第三辰）",
        ),
        DimensionRule(
            key="study.dedi.firm", label="通根有力", delta=6.0,
            reading="日主通根于四支则气固（本系统三因子之一的得地分，非古籍赋分）",
        ),
    ),
    "人际": (
        DimensionRule(
            key="social.noble.tianyi", label="天乙照命", delta=12.0,
            reading="天乙所至，一切凶煞隐然而避（《三命通会·论天乙贵人》『其神最尊贵，所至之处，一切凶煞隐然而避』）",
        ),
        DimensionRule(
            key="social.noble.taiji", label="太极贵人", delta=6.0,
            reading="太极者物造于初，主始终相保（《三命通会·论太极贵》『物造于初为太极，成也，收也』）",
        ),
        DimensionRule(
            key="social.parallel.wide", label="同气相求", delta=6.0,
            reading="比肩为兄弟，同气易相聚（《渊海子平·论兄弟姊妹》『比肩者，兄弟也』）",
        ),
        DimensionRule(
            key="social.parallel.unchecked", label="比劫无制", delta=-8.0,
            reading="比劫多而无官星约束，主破耗、防小人（《渊海子平·论劫财》『五阴见五阳为劫财，主破耗、防小人』）",
        ),
        DimensionRule(
            key="social.officer.moderate", label="上下相维", delta=4.0,
            reading="官星一位得中，则上下相维而不迫（《三命通会·论正官》『阴阳配合，相制有用，成其道也』）",
        ),
        DimensionRule(
            key="social.harm.branch", label="六害临支", delta=-5.0,
            reading="六害者凌战之辰，大率主妨害（《三命通会·论六害》『六害者，十二支凌战之辰』）",
        ),
    ),
}
DIMENSION_RULE_COUNT = sum(len(rules) for rules in DIMENSION_RULES.values())

_BY_KEY = {rule.key: rule for rules in DIMENSION_RULES.values() for rule in rules}


def dim_rule(key: str) -> DimensionRule:
    """Return the rule behind a machine key; an unknown key is a programming error."""
    try:
        return _BY_KEY[key]
    except KeyError as exc:
        raise KeyError(f"未知六维规则键：{key}") from exc
