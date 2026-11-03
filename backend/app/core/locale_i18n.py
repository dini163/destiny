"""后端响应文案的本地化层（cross-cutting，`core/` 底层，任何层可引）。

形状与前端 `i18n/messages.ts` 一致：**源简体字符串当 key**，命中即替换，未命中回落源文。
区别只在挂载点——判语正文是引擎现拼的长句，做不了 key，所以这一层今天只覆盖**有界、高复用
的结构化标签**：结论卡片的五档档位词、白话块的小节标题。深判语与卡牌/星曜等专名词表是后续
内容批次，往 `LABELS` 里加键即可，不改机制。

三条立身规矩（对齐 AGENTS.md）：
① `zh-Hans`（默认）与任何未知 locale 一律原样返回，一个字节都不动——`tests/` 的 HTTP golden
   与 `scripts/record_frontend_fixtures.py` 录的真响应因此恒绿，本地化只发生在显式请求
   `?locale=zh-Hant|en` 时；
② 只做**整串精确匹配**，绝不子串替换：命盘里的「吉」是档位词要译，判语段落里出现的「吉」是
   长句的一分子，不能被单独换掉，精确匹配天然挡住这件事；
③ 表是纯数据、`localize` 是纯函数，不认识任何系统，也不产新句子（宁缺勿造，同 §9 不 mock）。
"""

from __future__ import annotations

from typing import Any, Final

#: 源简体的规范拼写；命中这些之外的 locale 值一律走原样返回路径。
DEFAULT_LOCALE: Final[str] = "zh-Hans"

#: 需要改写字节的 locale——只有落在这里才进本地化路径，`zh-Hans` 恒走透传。
ACTIVE_LOCALES: Final[frozenset[str]] = frozenset({"zh-Hant", "en"})

#: `[locale][源简体整串] = 译文`。zh-Hant 只登记「繁简确有字形差」的条目（同形字如
#: 「主要相位」不登记，回落源文即已是正体，省得把同一串写两遍）。
LABELS: Final[dict[str, dict[str, str]]] = {
    "zh-Hant": {
        # 结论卡片档位词：大吉/吉/平/小凶/凶 繁简同形，无需登记。
        # 西洋本命小节标题
        "十星落宫": "十星落宮",
        "逆行诸星": "逆行諸星",
        "上升与天顶": "上升與天頂",
        "北交点": "北交點",
        "十二宫主题": "十二宮主題",
        "元素与形态": "元素與形態",
        # 吠陀小节标题
        "九曜落宫": "九曜落宮",
        "星宿落点": "星宿落點",
        "现行大运与小运": "現行大運與小運",
        # 行运小节标题
        "行运对本命相位": "行運對本命相位",
        "次限对本命相位": "次限對本命相位",
        "太阳弧对本命相位": "太陽弧對本命相位",
        "次限上升与天顶": "次限上升與天頂",
        # 合婚小节标题
        "契合分的来历": "契合分的來歷",
        "五行互给": "五行互給",
        "同频的段落": "同頻的段落",
        # 卡巴拉小节标题
        "全树读法": "全樹讀法",
        "三柱与四界": "三柱與四界",
        "光流与深渊": "光流與深淵",
        # 八字岁运 / 流日 / 流时小节标题
        "区间总览": "區間總覽",
        "岁运主线": "歲運主線",
        "流年十二个月": "流年十二個月",
        "本月总览": "本月總覽",
        "本日总览": "本日總覽",
        "十二时辰": "十二時辰",
        "聚焦时辰": "聚焦時辰",
        # 奇门小节标题
        "值符主线": "值符主線",
        "值使门线": "值使門線",
        "时干落宫": "時干落宮",
        "旬空与驿马": "旬空與驛馬",
        # 紫微小节标题
        "全盘气象": "全盤氣象",
        "命宫与三方四正": "命宮與三方四正",
        "运限与四化": "運限與四化",
        # 周易小节标题
        "本卦总论": "本卦總論",
        "变卦去向": "變卦去向",
        # 黄道十二星座（sign_zh 叶值）：仅登记繁简字形有差者，同形回落源文。
        "狮子": "獅子",
        "处女": "處女",
        "天蝎": "天蠍",
        "双鱼": "雙魚",
    },
    "en": {
        # 结论卡片档位词（与 `engines/verdict.GRADE_BANDS` 同源五档）。
        "大吉": "Great Fortune",
        "吉": "Fortune",
        "平": "Neutral",
        "小凶": "Minor Setback",
        "凶": "Setback",
        # 西洋本命小节标题
        "十星落座": "Planets in Signs",
        "十星落宫": "Planets in Houses",
        "主要相位": "Major Aspects",
        "逆行诸星": "Retrograde Planets",
        "上升与天顶": "Ascendant & Midheaven",
        "北交点": "North Node",
        "十二宫主题": "House Themes",
        "元素与形态": "Elements & Modalities",
        # 吠陀小节标题
        "九曜落座": "Grahas in Signs",
        "九曜落宫": "Grahas in Houses",
        "星宿落点": "Nakshatra Placement",
        "现行大运与小运": "Running Dasha Periods",
        # 行运小节标题
        "行运对本命相位": "Transit Aspects",
        "次限对本命相位": "Progressed Aspects",
        "太阳弧对本命相位": "Solar Arc Aspects",
        "次限月亮": "Progressed Moon",
        "次限上升与天顶": "Progressed Angles",
        # 合婚小节标题
        "契合分的来历": "How the Score Arises",
        "五行互给": "Five-Element Exchange",
        "同频的段落": "Shared-Frequency Windows",
        # 卡巴拉小节标题
        "全树读法": "Reading the Whole Tree",
        "三柱与四界": "Three Pillars & Four Worlds",
        "光流与深渊": "Light Flow & the Abyss",
        # 八字岁运 / 流日 / 流时小节标题
        "区间总览": "Range Overview",
        "岁运主线": "Yearly Luck Threads",
        "流年十二个月": "Twelve Solar Months",
        "本月总览": "Month Overview",
        "逐日分布": "Day-by-Day Spread",
        "聚焦之日": "Focused Day",
        "本日总览": "Day Overview",
        "十二时辰": "Twelve Double-Hours",
        "聚焦时辰": "Focused Hour",
        # 奇门小节标题
        "值符主线": "Duty Star Line",
        "值使门线": "Duty Door Line",
        "时干落宫": "Hour Stem Palace",
        "旬空与驿马": "Void & Travel Horse",
        # 紫微小节标题
        "全盘气象": "Whole-Chart Climate",
        "命宫与三方四正": "Life Palace & Trinity",
        "运限与四化": "Limits & Four Transformations",
        # 周易小节标题
        "本卦总论": "Primary Hexagram Overview",
        "变卦去向": "Changed Hexagram Direction",
        # 黄道十二星座（sign_zh 叶值，与 `engines/western.SIGNS_ZH` 同源十二名）。
        "白羊": "Aries",
        "金牛": "Taurus",
        "双子": "Gemini",
        "巨蟹": "Cancer",
        "狮子": "Leo",
        "处女": "Virgo",
        "天秤": "Libra",
        "天蝎": "Scorpio",
        "射手": "Sagittarius",
        "摩羯": "Capricorn",
        "水瓶": "Aquarius",
        "双鱼": "Pisces",
    },
}


def resolve_locale(raw: str | None) -> str:
    """把请求带来的 locale 串归一到受支持值；None / 未知一律回 `zh-Hans`（透传）。"""
    if raw is None:
        return DEFAULT_LOCALE
    value = raw.strip()
    return value if value in ACTIVE_LOCALES else DEFAULT_LOCALE


def localize_str(source: str, locale: str) -> str:
    """单个字符串按 locale 精确查表，未命中回落源文。`zh-Hans` / 未知 locale 原样返回。"""
    table = LABELS.get(locale)
    if not table:
        return source
    return table.get(source, source)


def localize(value: Any, locale: str) -> Any:
    """递归遍历已序列化的 JSON 载荷，对每个字符串叶子做精确查表替换。

    结构（dict/list 的键与形状、数字、布尔、null）一概不动，只换字符串叶子的值——所以
    snake_case 契约（AGENTS §3）与字段名不受影响，前端照旧原样消费。
    """
    table = LABELS.get(locale)
    if not table:
        return value
    if isinstance(value, str):
        return table.get(value, value)
    if isinstance(value, dict):
        return {k: localize(v, locale) for k, v in value.items()}
    if isinstance(value, list):
        return [localize(v, locale) for v in value]
    return value
