"""塔罗 78 张牌的吉凶倾向表（正位 / 逆位两列）与综合结论卡片框架句。

本表是 verdict 卡片的**唯一极性凭据**：`engines/tarot.py` 只数本表给出的 +1/0/-1，
不运行时现判牌义。极性按伟特体系（A. E. Waite, *The Pictorial Key to the Tarot*, 1910）
大牌章与权杖/圣杯/宝剑/星币四花色小牌章的通行牌义归类；伟特只给定性牌义、不给分数，
故每枚的 +1/0/-1 是**本表自持的归类（模型参数）**，不是古籍赋分，出处诚实双署。

形状：`TAROT_POLARITY[card_id] = (upright, reversed, chapter)`，两列各 ∈ {+1, 0, -1}：
+1 积极、0 中性、-1 消极。逆位单列是因为伟特体系里逆位不是「同一张牌反过来」，
而是该牌能量被阻滞、内收或转向（如 Devil 逆位为解绑、Moon 逆位为迷雾散开），
故正逆两列分别归类，不做「逆位一律取反」的机械翻转。

本表**不进** `PlainCorpus`（丁组 spec §11 拒绝项⑤：塔罗无分带、正逆位翻倍键空间），
verdict 框架句也不住白话登记表，故由 `tests/content/test_tarot_verdict_corpus.py` 自守。
"""

#: 表级出处：伟特牌义章节（到章不到书）+ 本表自持归类（模型参数），两段都署。
TAROT_POLARITY_SOURCE = (
    "伟特体系通行牌义（A. E. Waite《The Pictorial Key to the Tarot》1910：大牌章、"
    "权杖/圣杯/宝剑/星币四花色小牌章）· 吉凶倾向为本表自持归类（模型参数，非古籍赋分）"
)

#: card_id → (正位极性, 逆位极性, 牌章)。chapter 只用于逐条到章，不进响应。
#: 复测（78 全覆盖）：`cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c
#: "from app.content.tarot_polarity import TAROT_POLARITY; from app.content.tarot_deck import DECK;
#: print(len(TAROT_POLARITY), set(TAROT_POLARITY) == {c.id for c in DECK})"` → `78 True`。
TAROT_POLARITY: dict[str, tuple[int, int, str]] = {
    # --- 22 大牌（Major Arcana） ---
    "major-00": (1, -1, "大牌章"),
    "major-01": (1, -1, "大牌章"),
    "major-02": (0, -1, "大牌章"),
    "major-03": (1, -1, "大牌章"),
    "major-04": (1, -1, "大牌章"),
    "major-05": (0, 0, "大牌章"),
    "major-06": (1, -1, "大牌章"),
    "major-07": (1, -1, "大牌章"),
    "major-08": (1, -1, "大牌章"),
    "major-09": (0, -1, "大牌章"),
    "major-10": (1, -1, "大牌章"),
    "major-11": (1, -1, "大牌章"),
    "major-12": (0, -1, "大牌章"),
    "major-13": (0, -1, "大牌章"),
    "major-14": (1, -1, "大牌章"),
    "major-15": (-1, 1, "大牌章"),
    "major-16": (-1, 0, "大牌章"),
    "major-17": (1, -1, "大牌章"),
    "major-18": (-1, 1, "大牌章"),
    "major-19": (1, 0, "大牌章"),
    "major-20": (1, -1, "大牌章"),
    "major-21": (1, -1, "大牌章"),
    # --- 权杖（Wands · 火） ---
    "wands-01": (1, -1, "权杖小牌章"),
    "wands-02": (1, -1, "权杖小牌章"),
    "wands-03": (1, -1, "权杖小牌章"),
    "wands-04": (1, -1, "权杖小牌章"),
    "wands-05": (0, 0, "权杖小牌章"),
    "wands-06": (1, -1, "权杖小牌章"),
    "wands-07": (0, -1, "权杖小牌章"),
    "wands-08": (1, -1, "权杖小牌章"),
    "wands-09": (0, -1, "权杖小牌章"),
    "wands-10": (-1, 1, "权杖小牌章"),
    "wands-11": (1, -1, "权杖小牌章"),
    "wands-12": (0, -1, "权杖小牌章"),
    "wands-13": (1, -1, "权杖小牌章"),
    "wands-14": (1, -1, "权杖小牌章"),
    # --- 圣杯（Cups · 水） ---
    "cups-01": (1, -1, "圣杯小牌章"),
    "cups-02": (1, -1, "圣杯小牌章"),
    "cups-03": (1, 0, "圣杯小牌章"),
    "cups-04": (0, 1, "圣杯小牌章"),
    "cups-05": (-1, 1, "圣杯小牌章"),
    "cups-06": (0, 0, "圣杯小牌章"),
    "cups-07": (0, 1, "圣杯小牌章"),
    "cups-08": (0, 0, "圣杯小牌章"),
    "cups-09": (1, 0, "圣杯小牌章"),
    "cups-10": (1, -1, "圣杯小牌章"),
    "cups-11": (1, -1, "圣杯小牌章"),
    "cups-12": (0, -1, "圣杯小牌章"),
    "cups-13": (1, -1, "圣杯小牌章"),
    "cups-14": (1, -1, "圣杯小牌章"),
    # --- 宝剑（Swords · 风） ---
    "swords-01": (1, -1, "宝剑小牌章"),
    "swords-02": (0, 0, "宝剑小牌章"),
    "swords-03": (-1, 1, "宝剑小牌章"),
    "swords-04": (0, -1, "宝剑小牌章"),
    "swords-05": (-1, 1, "宝剑小牌章"),
    "swords-06": (0, -1, "宝剑小牌章"),
    "swords-07": (-1, 0, "宝剑小牌章"),
    "swords-08": (-1, 1, "宝剑小牌章"),
    "swords-09": (-1, 0, "宝剑小牌章"),
    "swords-10": (-1, 1, "宝剑小牌章"),
    "swords-11": (0, -1, "宝剑小牌章"),
    "swords-12": (0, -1, "宝剑小牌章"),
    "swords-13": (1, -1, "宝剑小牌章"),
    "swords-14": (1, -1, "宝剑小牌章"),
    # --- 星币（Pentacles · 土） ---
    "pentacles-01": (1, -1, "星币小牌章"),
    "pentacles-02": (1, -1, "星币小牌章"),
    "pentacles-03": (1, -1, "星币小牌章"),
    "pentacles-04": (0, -1, "星币小牌章"),
    "pentacles-05": (-1, 1, "星币小牌章"),
    "pentacles-06": (1, 0, "星币小牌章"),
    "pentacles-07": (0, -1, "星币小牌章"),
    "pentacles-08": (1, 0, "星币小牌章"),
    "pentacles-09": (1, -1, "星币小牌章"),
    "pentacles-10": (1, -1, "星币小牌章"),
    "pentacles-11": (1, -1, "星币小牌章"),
    "pentacles-12": (0, -1, "星币小牌章"),
    "pentacles-13": (1, -1, "星币小牌章"),
    "pentacles-14": (1, -1, "星币小牌章"),
}


#: 总论框架句：档位词 + 积极/消极/中性三计数 + 大牌数 + 逆位数 + 一句取向。
#: `{grade}` 取 `verdict.grade_for` 的档位词；三个计数与大牌/逆位是引擎数出的盘面事实；
#: `{outlook}` 取 `TAROT_VERDICT_OUTLOOK[grade]`。本表不写死任何数字。
TAROT_VERDICT_FRAME = (
    "你这一阵抽出的牌属{grade}：积极牌{positive}张、消极牌{negative}张、中性牌{neutral}张，"
    "另有大牌{major}张、逆位{reversed}张，{outlook}。"
)

#: 各档位收束取向，键 = `app/engines/verdict.GRADE_BANDS` 五档档位词。
#: 槽位词条：不成句、不带「。」、不带建议词（档位词本身由 {grade} 槽注入）。
TAROT_VERDICT_OUTLOOK: dict[str, str] = {
    "大吉": "好牌占了上风，顺势推进",
    "吉": "积极的一面占优，值得把握",
    "平": "好坏大致相抵，稳住节奏再看",
    "小凶": "拖累的一面更多，先看清楚再动",
    "凶": "先把基本盘稳住，别急着出手",
}

#: 建议句框架：净计数非负走「相抵有余」，净计数为负走「负向偏多」。`{advice}` 取
#: `TAROT_VERDICT_ADVICE[键]`，键由引擎按净计数选定。
TAROT_VERDICT_ADVICE_FRAME = (
    "综合建议：你这一阵抽出的牌面已经摆在眼前，{advice}。"
)

#: 两档建议词条，键 = 引擎净计数分支名；槽位词条不成句、不带「。」、不带建议词。
TAROT_VERDICT_ADVICE: dict[str, str] = {
    "favorable": "积极与拖累相抵有余，按自己的节奏往下走即可",
    "adverse": "负向牌偏多，先把眼前的阻滞看清楚，暂缓推进",
}
