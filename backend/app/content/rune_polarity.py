"""24 枚 Elder Futhark 符文的吉凶倾向表（只按符文本身，不看朝向）与 verdict 框架句。

本表是卢恩 verdict 卡片的**唯一极性凭据**：`engines/runes.py` 只数本表给出的 +1/0/-1，
不运行时现判符文义。极性依据三份卢恩诗传统所载符文义——盎格鲁-撒克逊卢恩诗
（Anglo-Saxon Rune Poem, Exeter Book）、挪威卢恩诗（Norwegian Rune Poem）、
冰岛卢恩诗（Icelandic Rune Poem）：Fehu 牲畜/财富、Wynn 喜悦、Gyfu 赠礼为正向，
Hagalaz 冰雹损失、Nauthiz 困迫、Thurisaz 荆棘冲突为负向。三份诗只给定性释义、
不给分数，故每枚的 +1/0/-1 是**本表自持的归类（模型参数）**，出处诚实双署。

**朝向（正逆）不参与吉凶判定**（保留卢恩 spec 决策 6/7 与语料明令：逆位是反面参照，
不是另一次结果）：本表只有一列，`engines/runes.py` 计数时忽略 `orientation`。
Wyrd 空白符不在 24 枚之内，不入本表，计数时按中性处理。

本表**不进** `PlainCorpus`，verdict 框架句也不住白话登记表，故由
`tests/content/test_rune_verdict_corpus.py` 自守。
"""

#: 表级出处：三份卢恩诗所载符文义（到章不到书，按各诗该符文条目）+ 本表自持归类（模型参数）。
RUNE_POLARITY_SOURCE = (
    "三份卢恩诗所载符文义（盎格鲁-撒克逊 Exeter Book 卢恩诗、挪威卢恩诗、冰岛卢恩诗，"
    "各诗该符文条目）· 吉凶倾向为本表自持归类（模型参数，非古籍赋分）"
)

#: 符文 key → 极性（+1 积极 | 0 中性 | -1 消极），只按符文本身，与朝向无关。
#: 复测（24 全覆盖）：`cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c
#: "from app.content.rune_polarity import RUNE_POLARITY; from app.content.rune_futhark import DECK_24;
#: print(len(RUNE_POLARITY), set(RUNE_POLARITY) == {r.key for r in DECK_24})"` → `24 True`。
RUNE_POLARITY: dict[str, int] = {
    "fehu": 1,      # 牲畜/动产/财富流通
    "uruz": 1,      # 原牛/原始力量与耐力
    "thurisaz": -1,  # 荆棘/巨人/冲突与防卫
    "ansuz": 1,     # 神启/讯息/教诲与约定
    "raido": 1,     # 旅程/秩序/正道行进
    "kenaz": 1,     # 火炬/技艺/灵感
    "gebo": 1,      # 赠礼/盟约/平衡交换
    "wunjo": 1,     # 喜悦/和谐
    "hagalaz": -1,  # 冰雹/突变损失
    "nauthiz": -1,  # 必需/困迫/约束
    "isa": 0,       # 冰/停滞守成，等而不动
    "jera": 1,      # 收成/周期回报
    "eihwaz": 0,    # 紫杉/韧性与转化之桥，中性
    "perthro": 0,   # 签筒/机运未知，不定吉凶
    "algiz": 1,     # 护持/警戒/庇荫
    "sowilo": 1,    # 太阳/全胜/目标达成
    "tiwaz": 1,     # 公义/荣誉/决断
    "berkana": 1,   # 新生/孕育/成长
    "ehwaz": 1,     # 同行/信义/协力
    "mannaz": 0,    # 人/社群/本分，中性
    "laguz": 0,     # 水/直觉/顺势，中性
    "ingwaz": 1,    # 内孕/圆满/收束
    "dagaz": 1,     # 破晓/转折/苦尽
    "othala": 0,    # 祖产/故土/传承，得失两依，中性
}


#: 总论框架句：档位词 + 积极/消极/中性三计数 + 一句取向。
#: `{grade}` 取 `verdict.grade_for` 的档位词；三个计数是引擎数出的已落符文；
#: `{outlook}` 取 `RUNE_VERDICT_OUTLOOK[grade]`。本表不写死任何数字。
RUNE_VERDICT_FRAME = (
    "你这一阵落下的符文属{grade}：积极符{positive}枚、消极符{negative}枚、中性符{neutral}枚，"
    "{outlook}。"
)

#: 各档位收束取向，键 = `app/engines/verdict.GRADE_BANDS` 五档档位词。
#: 槽位词条：不成句、不带「。」、不带建议词（档位词本身由 {grade} 槽注入）。
RUNE_VERDICT_OUTLOOK: dict[str, str] = {
    "大吉": "正向符文占了上风，顺势推进",
    "吉": "积极的一面占优，值得把握",
    "平": "好坏大致相抵，稳住节奏再看",
    "小凶": "拖累的一面更多，先看清楚再动",
    "凶": "先把基本盘稳住，别急着出手",
}

#: 建议句框架：净计数非负走「相抵有余」，净计数为负走「负向偏多」。`{advice}` 取
#: `RUNE_VERDICT_ADVICE[键]`，键由引擎按净计数选定。
RUNE_VERDICT_ADVICE_FRAME = (
    "综合建议：你这一阵落下的符文已经摆在眼前，{advice}。"
)

#: 两档建议词条，键 = 引擎净计数分支名；槽位词条不成句、不带「。」、不带建议词。
RUNE_VERDICT_ADVICE: dict[str, str] = {
    "favorable": "积极与拖累相抵有余，按自己的节奏往下走即可",
    "adverse": "负向符偏多，先把眼前的阻滞看清楚，暂缓推进",
}
