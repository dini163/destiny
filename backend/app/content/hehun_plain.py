"""合婚页的整体白话：七句档位 / 同频散文 + 三句报事实的框架句（批次二 spec §5）。

这里只有表，不组句、不判命：档位句由 `engines/plain_corpora.HEHUN` 登记进机检工厂，
框架句不进 entries（工厂会拿 40 字条目门打它们），由 `engines/bazi_hehun.hehun_plain()`
用 `overview()` 实例化（AGENTS §1：content 是纯表）。

**四条口径写在门面上**：
① 档位名与规则短名都不是散文材料。`hehun_tier` 的四档里最低那档自带「宜」字，29 条规则
   的 `label` 里有「我忌彼旺」这一类，所以档位**用键挑句子**而不是把名字念进句子（spec §4.2）。
   复测：`tests/content/test_hehun_plain_corpus.py::test_entries_clear_every_local_gate`
   扫十七串零命中，`::test_the_source_string_names_the_cuts_it_claims` 扫本串点名的五处常量；
   「29」这个数的正主是 `len(HEHUN_RULES)`，不在本文件。
② 同频三档论的是**同一年内两造岁运分的差**（`axis_sync` 吃的是 `abs` 差值），既不是「两人档同
   不同」，也**不是时序先后**（本计划偏差表第 1 行 + J-T1 评审轮 I5）：数据里没有任何时间偏移，
   所以句子只说分量轻重，不说谁先谁后。
③ 档位只认识净额（`value = 起点分 + Σdelta` 再截断），不认识账本的**行数与幅度**（评审轮 I2）：
   跨档的「谁抵得更多」这类比较不进句子，`中和可处` 那一档容得下「一条命中都没有、只剩起点那一笔」
   这一页，所以这一支由那句自己说出来，不留给读者想象。
④ 抵回去的那一边**可以一个也没有**（`plus` 含起点那一笔且 `minus` 可为零，90/0 就是天作之合），
   所以 top/strong/middle 不许写成「抵掉的那几笔没能…」这种预设它存在的句式（评审轮 round 2 D）；
   `low` 只许说「那几笔确实存在、净额被带到了起点那一笔之下」——那是定理（`value < 45` 而
   `plus ≥ 50` ⇒ `minus > 5`），但**不许**说这一边「占了上风」：`value = plus − minus` 非负
   ⇒ `plus ≥ minus` 在**每一页**都成立，且 `value == 0` 那一页两边**相等**（所以连「更大」也不许说，
   只许说「不小于」），而同一节上面那行就把这两个合计并排印给读者（round 3 F-2 改的就是这半句）。
   复测（90/0 落最高档）：`cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "from app.engines.bazi_hehun import hehun_tier; print(hehun_tier(90.0))"` → `天作之合`；
   复测（最低档里加的那一边仍然不小于抵的那一边）：`cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "from app.engines.bazi_hehun import HehunRow, hehun_ledger; s = hehun_ledger([HehunRow('r1', 'L1', 'f', 'both', 10.0), HehunRow('r2', 'L2', 'f', 'both', -10.0), HehunRow('r3', 'L3', 'f', 'both', -10.0)]); print(s.value, sum(f.delta for f in s.factors if f.delta > 0), sum(-f.delta for f in s.factors if f.delta < 0), s.tier)"` → `40.0 60.0 20.0 欠和宜慎`；
   复测（`value == 0` 那一页两边相等 ⇒ 「更大」为假）：`cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "from app.engines.bazi_hehun import HehunRow, hehun_ledger; s = hehun_ledger([HehunRow('r%d' % i, 'L%d' % i, 'f', 'both', -10.0) for i in range(7)]); print(s.value, sum(f.delta for f in s.factors if f.delta > 0), sum(-f.delta for f in s.factors if f.delta < 0), s.tier)"` → `0.0 70.0 70.0 欠和宜慎`。
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
        "两条命盘的账并到一处，净额顶在整把尺的高段，加的那一边压过了所有往回拽的力量，你读到的是"
        "合起来剩下的一大片同向，即便真有抵回去的那几笔，也没能把它拽下这条线。"
    ),
    "hehun.tone.strong": (
        "合起来看，净额仍然偏往加的那一边，站在高段那一条线之下、却稳稳在起点那一笔之上，你读到的"
        "是两条线各自成事、叠上去的那几笔够分量，抵回去的力量不足以把总数带回起点以下。"
    ),
    "hehun.tone.middle": (
        "把两本账的净额放到整把尺上看，它落在中间那一段，离起点那一笔并不远，你读到的是两条年头的"
        "方向不完全一致，这一页一条命中都没有、只剩起点那一笔时也是这一档。"
    ),
    "hehun.tone.low": (
        "这一页上，相互抵掉的那几笔确实存在，还把净额带到了起点那一笔之下，你读到的是同一条线索"
        "在你们两边来回拉扯，两边的账眼下对不齐，它落在整把尺的最低那一段。"
    ),
}

HEHUN_SYNC_READINGS: dict[str, str] = {
    "hehun.sync.aligned": (
        "同一年里你们两人的岁运分没有越过最窄那一条线，你读到的是同一年的岁运落到两个人身上分量"
        "相近，两条年头的轻重挨在一起，这一年谁也不比谁轻多少。"
    ),
    "hehun.sync.half": (
        "年份还是同一个，两边的岁运分却差开了一些，落在最窄与最宽两条线之间，你读到的是同一年的"
        "岁运落到两个人身上并不等重，轻重隔开了一层。"
    ),
    "hehun.sync.apart": (
        "两人同一年的岁运分相减，得数已经越过最宽那一条线，两条年头差得开，你读到的是轻重很不"
        "一样，这一把尺量的是差的大小，说不出哪一头更重。"
    ),
}

HEHUN_READINGS: dict[str, str] = {**HEHUN_TONE_READINGS, **HEHUN_SYNC_READINGS}

#: 契合分节的框架句。`{plus}` / `{minus}` 是对 `score.factors[].delta` 按符号求和：起点那一笔
#: 是 `build_ledger` 放进账本的**一行正数**（`schemas/scoring.py:55-58`），所以它只进 `{plus}`，
#: 永不出现在 `{minus}` 里——正因如此「一减正是 `{value}`」才成立（评审轮 round 2 A：
#: 写成「两笔合计里都含着起点分」就是假话，那样差值应是 `value − 50`）。
#: 逐条规则的贡献不在这句话里重述，页面上方那张总账本就一行一笔（spec §9.3:445 的挂点顺序；
#: §4.3 管的是槽值取法，不是版面）。
HEHUN_SCORE_FRAME = (
    "你们这一页的契合分算下来是 {value} 分，往一处加的合计 {plus} 分、相互抵掉的合计 {minus} 分，"
    "起点那一笔算在加的这一边，两边一减就是前面那个数，至于哪一条规则各占多少，"
    "上方那张总账本一行一笔写着。"
)

#: 互给节的框架句。槽位逐字来自 `HehunComplementView` 的两视角 补 / 阙 格与纳音合读那一句，
#: 全是盘面名词，不含账本短名（spec §4.2 的禁插清单）。
#: **尺写在这里**：`{m_*}` 取 `viewer == "male"`（乾视坤）那一视角，而该视角的象限是以**乾的喜忌**
#: 配**坤盘里的旺弱**（`engines/bazi_hehun.py:_one_view_facts`），所以 `m_give` 是坤递给乾、
#: `m_thin` 是乾想要而坤给不出；`{f_*}` 同理取 `viewer == "female"`。句子按视角说话，
#: 不写成主语相对，否则两个前缀的默认读法与实际取数正好相反（J-T1 评审轮 C1）。
HEHUN_COMPLEMENT_FRAME = (
    "从乾这一侧看过去，坤递过来的那组五行是 {m_give}，乾想要而坤给不出的是 {m_thin}，"
    "从坤这一侧看回去，乾递过来的那组是 {f_give}，坤想要而乾给不出的是 {f_thin}，"
    "两边纳音合读作 {nayin}，你把这五处对一遍就知道互给落在哪一路。"
)

#: 同频节的框架句。{best_start} / {best_end} 恒为年份串（`axis_years` 是 `ge=1` 的必填件，
#: 段落表不会为空，所以没有「一年都数不出」这一支）。这一对的尺是 spec §4.3 那一行：逐段数
#: `同频` 行取 max、段按 `start_year` 升序、**平局取最早那一段**；于是整段都数不出同频时，
#: 报出的就是最早那一段，与「接近」无关（J-T1 评审轮 C2 改的就是这半句）。
HEHUN_AXIS_FRAME = (
    "从 {start} 年到 {end} 年，你们分差最近的一档有 {aligned} 个年头，中间一档 {half} 个，"
    "差得最远的一档 {apart} 个，同频那一行最多的段落起讫是 {best_start} 与 {best_end}，"
    "整段里一年都不落同频时，这两个年份报的就是最早的那一段。"
)

#: 结论卡片（verdict-card spec §4）建议句框架与档位建议，**不进** `HEHUN_READINGS`（工厂登记
#: 仍为 7 条 = 4 档位 + 3 同频），由引擎用 `overview()` 实例化，工厂条目门扫不到它们；四档→星级
#: 映射是署名模型参数，住引擎侧（档位只给定性、不给星），不在本表。
#: `{plus}` / `{minus}` 同 `HEHUN_SCORE_FRAME` 的按符号求和口径，`{value}` 是截断后净额。
HEHUN_VERDICT_ADVICE_FRAME = (
    "综合建议：往一处加 {plus} 分、相互抵掉 {minus} 分，净额 {value} 分，{tier_advice}。"
)

#: 四档各自的一句口语建议，键同 `hehun_tier`。槽位词条不成句、不带「。」。
HEHUN_TIER_ADVICE: dict[str, str] = {
    "天作之合": "合处已足，不必另作改动",
    "相得益彰": "把叠上去的一面接住，留一分余地",
    "中和可处": "顺与相抵相抵，稳住节奏相处",
    "欠和宜慎": "先把拉扯的那几笔对齐，缓一步再求合",
}
