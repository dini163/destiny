"""干支关系表：只记"哪两个字算这种关系"与"这一条怎么说"。

推表时按"古籍怎么说为准"处理了两处分歧，留在这里免得后来人以为漏写：

- 地支六破：《三命通会·卷三·总论诸神煞》只立四对，并明言寅申巳亥"原破，却三合，故不取"
  —— 因寅亥、巳申本身是地支六合。本表从古籍取四对，故 寅亥 既是六合就不又是破。
- 地支六合的"化气五行"：《论支元六合》只给合与"福轻/福盛"之分，未配五行；通行那套
  （子丑化土、寅亥化木…）出自五运六气，不在本轮允许语料内。所以本表只填 `天干五合` 的
  `element`（出处是《论十干化气》），`地支六合` 的 `element` 留 `None`。

`scope` 决定引擎怎么扫：`stem` 比四干、`branch` 比四支、`group` 找同一局的多个支、
`pillar` 比整柱干支（伏吟/反吟没有字表，只有 `reading` 与 `source`，判定在 engines）。
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class RelationRule:
    """一种干支关系：参与的字（或局）、这一条怎么说、出处。"""

    kind: str
    scope: str                     # stem | branch | pillar | group
    side: str | None               # 仅 stem/branch 用：gan | zhi
    pairs: frozenset[tuple[str, str]]      # 无向表，两个方向都登记
    element: dict[str, str] | None         # 合类的"合化目标"，非已化
    groups: dict[str, str] | None          # 仅 group 类：字模式 -> 五行
    peaks: dict[str, str] | None           # 仅 半合：字模式 -> 旺支
    reading: str
    source: str


SAN_HE_ELEMENTS: dict[str, str] = {
    "申子辰": "水", "寅午戌": "火", "巳酉丑": "金", "亥卯未": "木",
}
SAN_HE_PEAKS: dict[str, str] = {
    "申子辰": "子", "寅午戌": "午", "巳酉丑": "酉", "亥卯未": "卯",
}
SAN_HUI_ELEMENTS: dict[str, str] = {
    "寅卯辰": "木", "巳午未": "火", "申酉戌": "金", "亥子丑": "水",
}


def _both(*pairs: tuple[str, str]) -> frozenset[tuple[str, str]]:
    """把无向表的两端一次写全，避免"只写一遍"的漏查。"""
    return frozenset({p for a, b in pairs for p in ((a, b), (b, a))})


RELATION_TABLES: dict[str, RelationRule] = {
    "天干五合": RelationRule(
        kind="天干五合", scope="stem", side="gan",
        pairs=_both(("甲", "己"), ("乙", "庚"), ("丙", "辛"), ("丁", "壬"), ("戊", "癸")),
        element={"甲己": "土", "乙庚": "金", "丙辛": "水", "丁壬": "木", "戊癸": "火"},
        groups=None, peaks=None,
        reading="阳见阴、阴见阳为合，如男女相合而成夫妇之道；甲己中正、乙庚仁义、丙辛威制、"
                "丁壬淫慝、戊癸无情。所带五行是合化目标，非已化（须月令得旺气方论化）。",
        source="《三命通会·论十干合》《论十干化气》",
    ),
    "天干相冲": RelationRule(
        kind="天干相冲", scope="stem", side="gan",
        pairs=_both(("甲", "庚"), ("乙", "辛"), ("丙", "壬"), ("丁", "癸")),
        element=None, groups=None, peaks=None,
        reading="地支取七位为冲，犹天干取七位为煞之义，如甲逢庚为煞、甲至庚七数；"
                "两干之禄居对冲之地，故相冲。戊己居中央，无对，故干不冲土。",
        source="《三命通会·论冲击》七位之说（戊己中央不冲为本系统取法）",
    ),
    "地支六冲": RelationRule(
        kind="地支六冲", scope="branch", side="zhi",
        pairs=_both(("子", "午"), ("丑", "未"), ("寅", "申"), ("卯", "酉"),
                    ("辰", "戌"), ("巳", "亥")),
        element=None, groups=None, peaks=None,
        reading="地支取七位为冲，十二支战击之神，大概为凶；然冲破有吉有凶，不可概论。"
                "冲处相生与冲处相克，判法不同。",
        source="《三命通会·论冲击》（查表同 LunarUtil.CHONG）",
    ),
    "地支六合": RelationRule(
        kind="地支六合", scope="branch", side="zhi",
        pairs=_both(("子", "丑"), ("寅", "亥"), ("卯", "戌"),
                    ("辰", "酉"), ("巳", "申"), ("午", "未")),
        element=None, groups=None, peaks=None,
        reading="合者，和也，乃阴阳相和，其气自合；夫合有合禄、合马、合贵之说。"
                "经云：明合不如暗合，拱实不拱虚。",
        source="《三命通会·论支元六合》",
    ),
    "地支六害": RelationRule(
        kind="地支六害", scope="branch", side="zhi",
        pairs=_both(("子", "未"), ("丑", "午"), ("寅", "巳"),
                    ("卯", "辰"), ("申", "亥"), ("酉", "戌")),
        element=None, groups=None, peaks=None,
        reading="因六合而生六害，六害者，十二支凌战之辰。六，六亲；害，损也。"
                "犯之主六亲上有损克，故谓六害；大率主妨害孤独，骨肉参商。",
        source="《三命通会·论六害》",
    ),
    "地支六破": RelationRule(
        kind="地支六破", scope="branch", side="zhi",
        pairs=_both(("卯", "午"), ("丑", "辰"), ("子", "酉"), ("未", "戌")),
        element=None, groups=None, peaks=None,
        reading="破煞，卯与午、丑与辰、子与酉、未与戌皆相破；惟寅申巳亥原破、却与合，故不取。"
                "犯者主少年灾滞，财产耗散，兼有折伤之灾。",
        source="《三命通会·卷三·总论诸神煞》破煞",
    ),
    "三合": RelationRule(
        kind="三合", scope="group", side=None,
        pairs=frozenset(), element=None, groups=dict(SAN_HE_ELEMENTS), peaks=None,
        reading="三合者，如人一身之运用：生即产，旺即成，库即收，有生有成有收，"
                "万物得始得终，乃自然之理。凡命有合，要得局为佳。",
        source="《三命通会·论支元三合》",
    ),
    "半合": RelationRule(
        kind="半合", scope="group", side=None,
        pairs=frozenset(), element=None, groups=dict(SAN_HE_ELEMENTS),
        peaks=dict(SAN_HE_PEAKS),
        reading="三合局中见二字且含旺支（即三合中位），本系统以半合标之。"
                "《三命通会·论支元三合》明言『若三字缺一则化不成局，不可以三合化局论』，"
                "故此条只记局势之半，不论其化。",
        source="《三命通会·论支元三合》（半合之名为本系统标法，古籍不以半合论化局）",
    ),
    "三会": RelationRule(
        kind="三会", scope="group", side=None,
        pairs=frozenset(), element=None, groups=dict(SAN_HUI_ELEMENTS), peaks=None,
        reading="方是方兮局是局，方要得方莫混局。如寅卯辰，东方也，杂以亥卯未则太过，"
                "岂不为混局哉；三会者，一方专气之全。",
        source="《滴天髓·方局论》",
    ),
    "无恩之刑": RelationRule(
        kind="无恩之刑", scope="branch", side="zhi",
        pairs=_both(("寅", "巳"), ("巳", "申"), ("申", "寅")),
        element=None, groups=None, peaks=None,
        reading="三刑生于二合。寅巳申何以谓之无恩？寅有生火刑巳上生金，巳上寄生之土刑申上"
                "长生之水，申中生水刑寅中生火，不恤所生，遥相克制，故曰无恩。"
                "生旺主人持重少语，寡欲无情。",
        source="《三命通会·论三刑》",
    ),
    "恃势之刑": RelationRule(
        kind="恃势之刑", scope="branch", side="zhi",
        pairs=_both(("丑", "戌"), ("戌", "未"), ("未", "丑")),
        element=None, groups=None, peaks=None,
        reading="丑戌未何以谓之恃势？丑恃旺水以刑戌中之墓火，戌恃六甲之尊以刑未六癸之卑，"
                "未有旺土复恃势以刑丑中之旺水。生旺主人精神意气雄豪，以直交人。",
        source="《三命通会·论三刑》",
    ),
    "无礼之刑": RelationRule(
        kind="无礼之刑", scope="branch", side="zhi",
        pairs=_both(("子", "卯")),
        element=None, groups=None, peaks=None,
        reading="子属水，卯属木，水能生木，则子水为母、卯木为子，子母自相刑；又子卯角立，"
                "无钦卑之道，不恤所以相生，进相刑害，故曰无礼。生旺主人威肃，面无和气。",
        source="《三命通会·论三刑》",
    ),
    "自刑": RelationRule(
        kind="自刑", scope="branch", side="zhi",
        pairs=_both(("辰", "辰"), ("午", "午"), ("酉", "酉"), ("亥", "亥")),
        element=None, groups=None, peaks=None,
        reading="辰午酉亥何以谓之自刑？无别物相加，乃曰自也。辰者水之墓，滔则盈；午者火之旺，"
                "暴则焚；酉者金之位，刚则缺；亥者水之生，旺则朽，各禀已盛太过之气而自致祸。",
        source="《三命通会·论三刑》",
    ),
    "伏吟": RelationRule(
        kind="伏吟", scope="pillar", side=None,
        pairs=frozenset(), element=None, groups=None, peaks=None,
        reading="岁运压日，谓之伏吟，不利六亲，非横破财，不为吉兆。本系统把同一取法用于"
                "四柱与大运之间：两柱干支全同即为伏吟。",
        source="《三命通会·卷二·总论岁运》（用于柱与柱为本系统扩用）",
    ),
    "反吟": RelationRule(
        kind="反吟", scope="pillar", side=None,
        pairs=frozenset(), element=None, groups=None, peaks=None,
        reading="若岁运与日相对，谓之返吟。本系统取窄口径：天干相冲且地支六冲方为反吟，"
                "阴阳相克而不冲者不算。阳刃忌反吟、伏吟。",
        source="《三命通会·卷二·总论岁运》《渊海子平·论阳刃》（窄口径为本系统取法）",
    ),
}
RELATION_COUNT = len(RELATION_TABLES)


def relation_pairs(key: str) -> frozenset[tuple[str, str]]:
    """The bidirectional character pairs of one relation rule."""
    try:
        return RELATION_TABLES[key].pairs
    except KeyError:
        raise KeyError(f"Unknown relation: {key}") from None


def transforming_element(kind: str, a: str, b: str) -> str | None:
    """这一对字的合化目标（非已化）；该关系不配五行或未记出处时为 None。"""
    element = RELATION_TABLES[kind].element
    if element is None:
        return None
    return element.get(a + b) or element.get(b + a)
