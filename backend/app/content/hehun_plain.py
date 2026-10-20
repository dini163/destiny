"""合婚页的整体白话：七句档位 / 同频散文 + 三句报事实的框架句（批次二 spec §5）。

这里只有表，不组句、不判命：档位句由 `engines/plain_corpora.HEHUN` 登记进机检工厂，
框架句不进 entries（工厂会拿 40 字条目门打它们），由 `engines/bazi_hehun.hehun_plain()`
用 `overview()` 实例化（AGENTS §1：content 是纯表）。

**两条口径写在门面上**：
① 档位名与规则短名都不是散文材料。`hehun_tier` 的四档里最低那档自带「宜」字，29 条规则
   的 `label` 里有「我忌彼旺」这一类（复测见 `tests/content/test_hehun_plain_corpus.py`
   的第一条测），所以档位**用键挑句子**而不是把名字念进句子（spec §4.2）。
② 同频三档论的是**两造同年岁运分之差**，不是「两人档同不同」（本计划偏差表第 1 行）。
"""

HEHUN_PLAIN_SOURCE = (
    "本系统自撰白话 · 四档分界逐字取 content/bazi_hehun_rules.HEHUN_TOP_CUT 与 "
    "engines/bazi_strength 的 STRONG_CUT / WEAK_CUT，同频三档取 "
    "content/bazi_hehun_rules.HEHUN_SYNC_CLOSE / HEHUN_SYNC_WIDE，句子不引古籍"
)

#: 契合度四档 → 键。左列逐字取 `engines/bazi_hehun.hehun_tier` 的四个返回值；
#: 它们是账本词，不进散文（spec §4.2）。右列是本表唯一的键式。
HEHUN_TONE_KEYS: dict[str, str] = {
    "天作之合": "hehun.tone.top",
    "相得益彰": "hehun.tone.strong",
    "中和可处": "hehun.tone.middle",
    "欠和宜慎": "hehun.tone.low",
}

#: 同频三档 → 键。左列逐字取 `schemas.bazi_hehun.AxisSync` 的 `get_args` 结果。
HEHUN_SYNC_KEYS: dict[str, str] = {
    "同频": "hehun.sync.aligned",
    "半同步": "hehun.sync.half",
    "背离": "hehun.sync.apart",
}

#: 三节的标题（装配与 golden、前端 `pinLiteralOrder` 共用这一份，别处不再写第二遍）。
HEHUN_SECTION_TITLES: tuple[str, str, str] = ("契合分的来历", "五行互给", "同频的段落")

HEHUN_TONE_READINGS: dict[str, str] = {
    "hehun.tone.top": (
        "两条命盘的账并到一处，你看到同向的那几层彼此叠得上，加进来的笔数多、相互抵掉的少，"
        "整页读下来是一股往同一处使的劲，两边都省了来回拉扯的力气。"
    ),
    "hehun.tone.strong": (
        "你们两个人的账各自往前推，重合的那几笔不算多，彼此抵掉的更少，"
        "这一页读到的是两条线并行，各成各的事，谁也没拆谁的台。"
    ),
    "hehun.tone.middle": (
        "你们的账并在一起时，加成的与抵掉的那几笔都占得到位置，谁也没盖过谁，"
        "读出来是两边都在使劲、方向不完全一致的形状，事情能走但要有人中途调整。"
    ),
    "hehun.tone.low": (
        "两本账合起来看，抵掉的那几笔压过了加进来的那几笔，同一条线索在你们两边来回拉扯，"
        "事情并非不能成，只是每一步都得先问清谁来让一步。"
    ),
}

HEHUN_SYNC_READINGS: dict[str, str] = {
    "hehun.sync.aligned": (
        "同一年里你们各自的岁运分挨得很近，你读到的是同一件事同时压到两个人身上，"
        "节奏对得上，来了可以一起接，不必分成两趟去处理。"
    ),
    "hehun.sync.half": (
        "同一年的分差开了一些却没到两边，你们两个人的节奏一个快半拍一个慢半拍，"
        "同一桩事到来时中间空开一个时段，各自撞上的那一面并不完全一样。"
    ),
    "hehun.sync.apart": (
        "两人的岁运分在同一年差得远，你读到的是两条时间线各走各的，"
        "事情走到你们面前有先有后，这不是一方压住一方，只是两人身前的时候不同。"
    ),
}

HEHUN_READINGS: dict[str, str] = {**HEHUN_TONE_READINGS, **HEHUN_SYNC_READINGS}

HEHUN_SCORE_FRAME = (
    "你们这一页的契合分算下来是 {value} 分，整本账加的一共 {plus} 分、抵掉的一共 {minus} 分，"
    "每一笔都在下面的分项里列着，你先读完这两句再看分档。"
)

#: 互给节的框架句。五个槽位逐字来自 `HehunComplementView`（乾/坤各给什么、各阙什么）与
#: 两侧纳音合读的那一句，全是盘面名词，不含账本短名（spec §4.2 的禁插清单）。
HEHUN_COMPLEMENT_FRAME = (
    "乾方递给坤方的那一组五行是 {m_give}，自身阙的是 {m_thin}，"
    "坤方递回来的那一组是 {f_give}，自身阙的是 {f_thin}，两边纳音合读作 {nayin}，"
    "你把这五处对一遍就知道互给落在哪一路。"
)

#: 同频节的框架句。{best_start} / {best_end} 恒为年份串（`axis_years` 是 `ge=1` 的必填件，
#: 段落表不会为空，故没有「一年都没有」这一支），末句仍把「整段都不同频」的读法交代清楚。
HEHUN_AXIS_FRAME = (
    "从 {start} 年到 {end} 年，你们分差最近的一档有 {aligned} 个年头，中间一档 {half} 个，"
    "差得最远的一档 {apart} 个，挨得最齐的那一段起讫是 {best_start} 与 {best_end}，"
    "若整段都不同频，这两个年份报的就是最接近的一段。"
)
