"""西洋合盘白话转述表（多系统白话 spec §6）：22 条 + 1 开篇句 + 4 档位收尾句，纯表零逻辑。

合盘是本轮唯一不能用「命中键 → 整句」直映的系统：人对人相位是 12 个点两两相比再乘 5
种相位，按源表口径 720 键。本表因此拆成两层，逐条可审的句子只有 22 条：

* `SYNASTRY_POINT_MEANINGS` —— 12 条**槽位词表**（名词短语，不带判断、不带句号），
  由 `tests/test_plain_corpora.py` 按 `slot_prefixes` 的短口径机检。
* `SYNASTRY_ASPECT_FRAMES` —— 5 条相位框架句，只述机制（叠在同一处 / 相隔六十度 /
  互相顶着走……），结论由档位收尾句携带（G2）。
* `SYNASTRY_BOND_READINGS` —— 5 条核心羁绊整句，走全句口径，只服务响应级总论。

三条 frame 的排版裁定：「你的{a}，与对方的{b}」中间那个**逗号不许省**。点义自带「与」
（「执念与翻覆的深处」「突变与独立的一面」），无逗号时「你的执念与翻覆的深处与对方的…」
连出三个「与」，读的人分不清哪一段属于哪一侧。这是本表唯一一处版式取舍，改动要重跑
Step 8 的逐条人审。

刑与冲的白话**如实保留表的严重度**：表的口径是「挑战」，转述写成「互相顶着走」「要不断
调整姿势才站得稳」，并各带一句「别扭是它本来的形状，不是谁做错了什么」——这句不是安慰，
是把「挑战」这个词的字面误读（谁做错了）排除掉，严重度一个字没减。
"""

#: 全表出处（与姓名学那条形同：说清这些句子逐字对应哪张受控表）。
SYNASTRY_PLAIN_SOURCE = "本系统白话转述 · 逐条对应 synastry_scoring 的相位轴与核心羁绊"


def point_key(name: str) -> str:
    """点义槽位键的唯一构造式；`name` 是引擎侧那个英文点名（Sun…Pluto、ASC、MC）。"""
    return f"synastry.point.{name}"


def aspect_frame_key(aspect_type: str) -> str:
    """相位框架句键；`aspect_type` 逐字取 `western.ASPECTS` 的名字，不另造转写。"""
    return f"synastry.aspect.{aspect_type}"


def bond_key(point_a: str, point_b: str) -> str:
    """核心羁绊键：两端**排序后**拼，因为 `SYNASTRY_CORE_BONDS` 本身是无序对
    （`engines/synastry.py` 的 `_synastry_aspects` 里那句 `tuple(sorted((name_a, name_b)))`），
    甲月对乙金与甲金对乙月是同一条轴。
    """
    first, second = sorted((point_a, point_b))
    return f"synastry.bond.{first}-{second}"


#: 12 个点的名词短语释义。十颗行星的名字来自 `engines/western.PLANETS`，两轴来自
#: `engines/synastry._AXIS_ZH` 的键集合（那个集合今天就是 ASC/MC，本表另有一条款测试钉它）。
SYNASTRY_POINT_MEANINGS: dict[str, str] = {
    "Sun": "自我与生命方向",
    "Moon": "情绪与安全感",
    "Mercury": "言语与消息往来",
    "Venus": "喜好与亲近方式",
    "Mars": "行动与脾气",
    "Jupiter": "扩张与机会之门",
    "Saturn": "约束与责任之分",
    "Uranus": "突变与独立的一面",
    "Neptune": "想象与含混的一面",
    "Pluto": "执念与翻覆的深处",
    "ASC": "待人接物的门面",
    "MC": "对外站立的方向",
}

#: 5 条相位框架句：{a} 恒填甲方点义、{b} 恒填乙方点义，方向不许对调（前端那行也按这个次序排）。
SYNASTRY_ASPECT_FRAMES: dict[str, str] = {
    "conjunction": "你的{a}，与对方的{b}叠在圆环的同一处，两股东西并成一股来用，你在这一段上分不太清哪一半是自己，熟也是先熟在这里。",
    "sextile": "你的{a}，与对方的{b}相隔六十度，两不相抢也接得上手，这一段要有人先开口才走得动，你不去用它，它就一直停在原地等着。",
    "trine": "你的{a}，与对方的{b}相隔一百二十度，气性本属一路，流过去不费力，你在这一段上很少遇到阻力，也因此最容易把它当成本来就有。",
    "square": "你的{a}，与对方的{b}成九十度直角，两股力气互相顶着走，你在这一段上要不断调整姿势才站得稳，别扭是它本来的形状，不是谁做错了什么。",
    "opposition": "你的{a}，与对方的{b}落在圆环的两头，隔着一百八十度对望，各是对方那一面的镜子，你在这一段上要来回对齐几趟才看得全。",
}

#: 5 条核心羁绊整句。键 = `bond_key` 对 `content/synastry.SYNASTRY_CORE_BONDS` 五个无序对的结果。
SYNASTRY_BOND_READINGS: dict[str, str] = {
    bond_key("Moon", "Sun"): "日月这一对是合盘里最主干的一条轴，你要的显与你要的安常常不在同一个时辰，这一段磨合的不是谁对谁错，是两个人一天里的时差。",
    bond_key("Mars", "Venus"): "金火这一对管的是被吸引与往前冲的那股劲，你在这条轴上感受最直接，来得也快，它给的是热度，把热度认成什么是后面的事。",
    bond_key("Moon", "Venus"): "月金这一对是情绪与喜好叠在一处，你在这条轴上容易觉得被照顾，也容易把照顾与心动放进同一个口袋，两者的分别要一段时间才分得开。",
    bond_key("Sun", "Sun"): "日日这一对是两个意志站在同一块地方，你在这条轴上不缺懂得，两个身份的走向常常撞到同一个点上，谁也没错，位置却只有一个。",
    bond_key("Moon", "Moon"): "月月这一对是两种情绪节奏并排走，你在这条轴上容易同步，高兴与低落都容易一起到来，一个人的天气会传染成两个人的天气。",
}

#: 响应级总论的开篇句（本系统只有这一个装配小节：逐行相位走 compose_template，不带小节开篇句，
#: 否则 56 行会重复 56 次同一句开场）。
SYNASTRY_SUMMARY_OPENER = "把账本里命中的核心羁绊合起来看，你这段关系最要紧的几条轴各落在顺的一侧还是费劲的一侧，下面按两侧重排一遍。"

#: 相契度四档收尾句。键 = `content/synastry.SYNASTRY_TIERS` 的档名，一个不多一个不少。
#: 措辞口径见 G14（裁定 R30）：相契度是逐条相位按「基准分 × 容许度权重 × 核心强调」累加后落阈值
#: （`content/synastry.py:synastry_tier`），**不是**顺/费劲相位的计数，所以收尾句只说档与表的措辞，
#: 不说「几条多于几条」——原稿这四句里有三句断言了相位条数构成，2026-09-30 由 Task 4 审阅判红后重写。
SYNASTRY_TIER_CLOSERS: dict[str, str] = {
    "相契甚深": "你这一份相契度落在最深的一档，表的措辞在这一档偏向顺遂，读它的方式是把整段当气象看，哪一条相位自己写着费劲，仍以它那句为准。",
    "和合互补": "你这一份相契度属和合互补，表的措辞在这一档以合为主而留着余地，不必拿单独一条相位的短处重估全盘，也不必让这一档替这段关系作保。",
    "中和可处": "你这一份相契度落在中和可处，表的措辞在这一档是平的，顺与费劲两边都读得进去，轻重由那几条相位自己说，不由这个档位替你定。",
    "磨合为宜": "你这一份相契度偏磨合为宜，表的措辞在这一档偏重费劲的那一面，它讲配置的次序，不讲这段关系该不该继续。",
}

#: 登记进 corpus 的 22 条 = 12 点义 + 5 框架句 + 5 羁绊句。三张源表都只存裸名字，
#: 键前缀在这里由构造式加上——`universe()`（Step 2）也用同一批构造式现算，两边不可能漂。
SYNASTRY_READINGS: dict[str, str] = {
    **{point_key(name): text for name, text in SYNASTRY_POINT_MEANINGS.items()},
    **{aspect_frame_key(name): text for name, text in SYNASTRY_ASPECT_FRAMES.items()},
    **SYNASTRY_BOND_READINGS,
}
