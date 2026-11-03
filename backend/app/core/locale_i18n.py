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
        # 八卦卦名 / 卦象（zhouyi lower_name_zh、upper_name_zh、*_nature_zh 叶值）：仅登记字形有差者。
        "兑": "兌",
        "离": "離",
        "泽": "澤",
        "风": "風",
        # 吠陀九曜（VedicPlanet.name_zh 叶值）：仅登记字形有差者。
        "太阳": "太陽",
        "太阴": "太陰",
        "罗睺": "羅睺",
        "计都": "計都",
        # 六神 / 六亲（zhouyi liushen、liuqin 叶值）：仅登记字形有差者。
        "青龙": "青龍",
        "勾陈": "勾陳",
        "子孙": "子孫",
        "妻财": "妻財",
        # 紫微十二宫（ziwei palace name 叶值）：仅登记字形有差者。
        "命宫": "命宮",
        "财帛": "財帛",
        "迁移": "遷移",
        "仆役": "僕役",
        "官禄": "官祿",
        # 奇门八门 / 方位（qimen door、direction 叶值）：仅登记字形有差者。
        "休门": "休門",
        "死门": "死門",
        "伤门": "傷門",
        "杜门": "杜門",
        "开门": "開門",
        "惊门": "驚門",
        "生门": "生門",
        "景门": "景門",
        "东": "東",
        "东南": "東南",
        "东北": "東北",
        "中宫": "中宮",
        # 卡巴拉三柱 / 隐藏原质 Daath（kabbalah pillar.name_zh、DAATH.name_zh 叶值）：仅登记字形有差者。
        # 慈悲之柱 / 中柱·平衡 繁简同形，回落源文。
        "严厉之柱": "嚴厲之柱",
        "知识（隐藏）": "知識（隱藏）",
        # 塔罗 / 雷诺曼牌名繁体（与上 en 牌名同源）：牌名为汉语常用词，繁简有差者才登记。
        # 卢恩符文名为音译专名、无权威繁体，不入表（同 en-only 裁定）。
        "魔术师": "魔術師",
        "恋人": "戀人",
        "战车": "戰車",
        "隐士": "隱士",
        "命运之轮": "命運之輪",
        "正义": "正義",
        "节制": "節制",
        "恶魔": "惡魔",
        "审判": "審判",
        "权杖王牌": "權杖王牌", "权杖二": "權杖二", "权杖三": "權杖三",
        "权杖四": "權杖四", "权杖五": "權杖五", "权杖六": "權杖六",
        "权杖七": "權杖七", "权杖八": "權杖八", "权杖九": "權杖九",
        "权杖十": "權杖十", "权杖侍从": "權杖侍從", "权杖骑士": "權杖騎士",
        "权杖王后": "權杖王后", "权杖国王": "權杖国王",
        "圣杯王牌": "聖杯王牌", "圣杯二": "聖杯二", "圣杯三": "聖杯三",
        "圣杯四": "聖杯四", "圣杯五": "聖杯五", "圣杯六": "聖杯六",
        "圣杯七": "聖杯七", "圣杯八": "聖杯八", "圣杯九": "聖杯九",
        "圣杯十": "聖杯十", "圣杯侍从": "聖杯侍從", "圣杯骑士": "聖杯騎士",
        "圣杯王后": "聖杯王后", "圣杯国王": "聖杯国王",
        "宝剑王牌": "寶劍王牌", "宝剑二": "寶劍二", "宝剑三": "寶劍三",
        "宝剑四": "寶劍四", "宝剑五": "寶劍五", "宝剑六": "寶劍六",
        "宝剑七": "寶劍七", "宝剑八": "寶劍八", "宝剑九": "寶劍九",
        "宝剑十": "寶劍十", "宝剑侍从": "寶劍侍從", "宝剑骑士": "寶劍騎士",
        "宝剑王后": "寶劍王后", "宝剑国王": "寶劍国王",
        "星币王牌": "星幣王牌", "星币二": "星幣二", "星币三": "星幣三",
        "星币四": "星幣四", "星币五": "星幣五", "星币六": "星幣六",
        "星币七": "星幣七", "星币八": "星幣八", "星币九": "星幣九",
        "星币十": "星幣十", "星币侍从": "星幣侍從", "星币骑士": "星幣騎士",
        "星币王后": "星幣王后", "星币国王": "星幣国王",
        "骑士": "騎士", "三叶草": "三葉草", "云": "雲", "镰刀": "鐮刀",
        "鹳": "鸛", "钥匙": "鑰匙", "锚": "錨",
        # 六十四卦全名 / 短名 / 世次繁体（与上 en 卦名同源）：繁简有差者才登记。
        "乾为天": "乾為天", "坤为地": "坤為地", "天水讼": "天水訟", "地水师": "地水師",
        "风天小畜": "風天小畜", "天泽履": "天澤履", "地山谦": "地山謙", "泽雷随": "澤雷隨",
        "山风蛊": "山風蠱", "地泽临": "地澤臨", "风地观": "風地觀", "山火贲": "山火賁",
        "山地剥": "山地剝", "地雷复": "地雷復", "天雷无妄": "天雷無妄", "泽风大过": "澤風大過",
        "坎为水": "坎為水", "离为火": "離為火", "泽山咸": "澤山咸", "雷风恒": "雷風恒",
        "火地晋": "火地晉", "风火家人": "風火家人", "火泽睽": "火澤睽", "山泽损": "山澤損",
        "风雷益": "風雷益", "泽天夬": "澤天夬", "天风姤": "天風姤", "泽地萃": "澤地萃",
        "地风升": "地風升", "泽水困": "澤水困", "水风井": "水風井", "泽火革": "澤火革",
        "火风鼎": "火風鼎", "震为雷": "震為雷", "艮为山": "艮為山", "风山渐": "風山漸",
        "雷泽归妹": "雷澤歸妹", "雷火丰": "雷火豐", "巽为风": "巽為風", "兑为泽": "兌為澤",
        "风水涣": "風水渙", "水泽节": "水澤節", "风泽中孚": "風澤中孚", "雷山小过": "雷山小過",
        "水火既济": "水火既濟", "火水未济": "火水未濟",
        "讼": "訟", "师": "師", "谦": "謙", "随": "隨", "蛊": "蠱", "临": "臨",
        "观": "觀", "贲": "賁", "剥": "剝", "复": "復", "无妄": "無妄", "大过": "大過",
        "晋": "晉", "损": "損", "渐": "漸", "归妹": "歸妹", "丰": "豐", "涣": "渙",
        "节": "節", "小过": "小過", "既济": "既濟", "未济": "未濟",
        "本宫": "本宮", "归魂": "歸魂",
        # 紫微星名 / 四化繁体（与上 en 星名同源）：仅登记字形有差者。
        "廉贞": "廉貞", "巨门": "巨門", "破军": "破軍", "左辅": "左輔",
        "铃星": "鈴星", "陀罗": "陀羅", "天钺": "天鉞", "禄存": "祿存",
        "化禄": "化祿", "化权": "化權",
        # 八字十神繁体（与上 en 十神同源）：仅登记字形有差者。
        "劫财": "劫財", "伤官": "傷官", "偏财": "偏財", "正财": "正財", "七杀": "七殺",
        # 八字辅助专名繁体（与上 en 同源）：仅登记字形有差者，同形回落源文。
        "事业": "事業", "财运": "財運", "学业": "學業", "人际": "人際",
        "时柱": "時柱", "本气": "本氣", "中气": "中氣", "余气": "餘氣", "身强": "身強",
        "长生": "長生", "冠带": "冠帶", "临官": "臨官", "绝": "絕", "养": "養",
        "七杀格": "七殺格", "伤官格": "傷官格", "正财格": "正財格", "偏财格": "偏財格", "建禄格": "建祿格",
        # 神煞/纳音繁体（与上同源）：仅登记字形有差者。
        "天乙贵人": "天乙貴人", "文昌贵人": "文昌貴人", "太极贵人": "太極貴人",
        "天德贵人": "天德貴人", "月德贵人": "月德貴人", "建禄": "建祿",
        "金舆": "金輿", "驿马": "驛馬", "华盖": "華蓋", "将星": "將星",
        "炉中火": "爐中火", "剑锋金": "劍鋒金", "山头火": "山頭火", "城头土": "城頭土",
        "涧下水": "澗下水", "白蜡金": "白蠟金", "杨柳木": "楊柳木", "霹雳火": "霹靂火",
        "长流水": "長流水", "覆灯火": "覆燈火", "大驿土": "大驛土", "钗钏金": "釵釧金",
        # 干支关系枚举繁体（与上同源）：仅登记字形有差者（六冲取沖，会/势/无/礼转形）。
        "三会": "三會", "地支六冲": "地支六沖", "天干相冲": "天干相沖",
        "恃势之刑": "恃勢之刑", "无恩之刑": "無恩之刑", "无礼之刑": "無禮之刑",
        # 八字结构化标签繁体（与上同源）：仅登记字形有差者。
        "通关": "通關", "调候": "調候", "紧临": "緊臨", "远位": "遠位", "滞": "滯", "基准分": "基準分",
        # 二十四节气繁体（与上同源）：仅登记字形有差者（惊/蛰/种/满/处转形）。
        "处暑": "處暑", "小满": "小滿", "惊蛰": "驚蟄", "芒种": "芒種",
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
        # 八卦卦名（name_zh 叶值）取邵雍先天罗马音；卦象（nature_zh）取义译。
        "乾": "Qian",
        "兑": "Dui",
        "离": "Li",
        "震": "Zhen",
        "巽": "Xun",
        "坎": "Kan",
        "艮": "Gen",
        "坤": "Kun",
        "天": "Heaven",
        "泽": "Lake",
        "雷": "Thunder",
        "山": "Mountain",
        "地": "Earth",
        "风": "Wind",
        # 五行（element 叶值）；火/水与卦象同词同译，共用下面两个键。
        "木": "Wood",
        "火": "Fire",
        "土": "Earth",
        "金": "Metal",
        "水": "Water",
        # 吠陀九曜（VedicPlanet.name_zh 叶值，与 `content/vedic.GRAHAS` 同源）。
        "太阳": "Sun",
        "太阴": "Moon",
        "火星": "Mars",
        "水星": "Mercury",
        "木星": "Jupiter",
        "金星": "Venus",
        "土星": "Saturn",
        "罗睺": "Rahu",
        "计都": "Ketu",
        # 六神（liushen 叶值，与 `content/zhouyi_najia.LIUSHEN_ORDER` 同源）。
        "青龙": "Azure Dragon",
        "朱雀": "Vermilion Bird",
        "勾陈": "Hook Serpent",
        "螣蛇": "Flying Serpent",
        "白虎": "White Tiger",
        "玄武": "Black Tortoise",
        # 六亲（liuqin 叶值；紫微十二宫中的父母/兄弟同词同义，共用）。
        "父母": "Parents",
        "兄弟": "Siblings",
        "子孙": "Offspring",
        "妻财": "Wealth",
        "官鬼": "Officers",
        # 紫微十二宫（palace name 叶值，与 `content/ziwei.PALACE_NAMES` 同源）；
        # 兄弟/父母与六亲同词同译，不重复登记。宫位网格以裸名作标，语境已供“宫”义。
        "命宫": "Life",
        "夫妻": "Spouse",
        "子女": "Children",
        "财帛": "Wealth",
        "疾厄": "Health",
        "迁移": "Travel",
        "仆役": "Servants",
        "官禄": "Career",
        "田宅": "Property",
        "福德": "Blessing",
        # 十天干 / 十二地支（单字 stem/branch 叶值，najia・八字・奇门共用）：取拼音转写。
        # 地支「丑」作支名繁简同形（≠醜），天干地支均无字形差，zh-Hant 无需登记。
        "甲": "Jia", "乙": "Yi", "丙": "Bing", "丁": "Ding", "戊": "Wu",
        "己": "Ji", "庚": "Geng", "辛": "Xin", "壬": "Ren", "癸": "Gui",
        "子": "Zi", "丑": "Chou", "寅": "Yin", "卯": "Mao", "辰": "Chen", "巳": "Si",
        "午": "Wu", "未": "Wei", "申": "Shen", "酉": "You", "戌": "Xu", "亥": "Hai",
        # 奇门九星（name 叶值，与 `content/qimen.NINE_STARS` 同源）：取拼音转写。
        "天蓬": "Tianpeng", "天芮": "Tianrui", "天冲": "Tianchong", "天辅": "Tianfu",
        "天禽": "Tianqin", "天心": "Tianxin", "天柱": "Tianzhu", "天任": "Tianren", "天英": "Tianying",
        # 奇门八门（与 `content/qimen.EIGHT_DOORS` 同源）。
        "休门": "Rest Door", "死门": "Death Door", "伤门": "Harm Door", "杜门": "Block Door",
        "开门": "Open Door", "惊门": "Fear Door", "生门": "Life Door", "景门": "View Door",
        # 奇门八神（与 `content/qimen.EIGHT_GODS` 同源；螣蛇/白虎/玄武沿用六神译，太阴沿用九曜 Moon）。
        "值符": "Chief Deity", "六合": "Six Harmony", "九地": "Nine Earth", "九天": "Nine Heaven",
        # 洛书方位（direction 叶值）。
        "东": "East", "南": "South", "西": "West", "北": "North",
        "东北": "Northeast", "东南": "Southeast", "西南": "Southwest", "西北": "Northwest",
        "中": "Center", "中宫": "Center Palace",
        # 奇门吉凶档（luck 叶值；吉/凶沿用结论档位）。
        "中平": "Balanced",
        # 卢恩符文名（rune name_zh 叶值，与 `content/rune_futhark.DECK_25` 同源）：
        # 系音译专名，无权威繁体写法，zh-Hant 回落源简体；en 取牌组自带的拉丁名。
        "费胡": "Fehu", "乌鲁兹": "Uruz", "图里萨兹": "Thurisaz", "安苏兹": "Ansuz",
        "莱多": "Raido", "肯纳兹": "Kenaz", "盖博": "Gebo", "温乔": "Wunjo",
        "哈加拉兹": "Hagalaz", "瑙提兹": "Nauthiz", "伊萨": "Isa", "杰拉": "Jera",
        "艾赫瓦兹": "Eihwaz", "佩尔索": "Perthro", "阿尔吉兹": "Algiz", "索维洛": "Sowilo",
        "提瓦兹": "Tiwaz", "贝尔卡纳": "Berkana", "埃瓦兹": "Ehwaz", "曼纳兹": "Mannaz",
        "拉古兹": "Laguz", "英瓦兹": "Ingwaz", "达加兹": "Dagaz", "欧瑟拉": "Othala",
        "空白符": "Wyrd",
        # 塔罗牌名（name_zh 叶值，与 `content/tarot_deck.DECK` 同源）：en 取牌组自带英文名。
        # 跨系统同形异义（太阳/月亮/星星/塔）因全局单表不能区分牌系统，取一个共值：
        # 太阳→Sun（已入九曜）、山→Mountain（已入卦象），月亮/星星/塔在此定一。
        "愚人": "The Fool", "魔术师": "The Magician", "女祭司": "The High Priestess",
        "皇后": "The Empress", "皇帝": "The Emperor", "教皇": "The Hierophant",
        "恋人": "The Lovers", "战车": "The Chariot", "力量": "Strength", "隐士": "The Hermit",
        "命运之轮": "Wheel of Fortune", "正义": "Justice", "倒吊人": "The Hanged Man",
        "死神": "Death", "节制": "Temperance", "恶魔": "The Devil", "塔": "Tower",
        "星星": "Star", "月亮": "Moon", "审判": "Judgement", "世界": "The World",
        "权杖王牌": "Ace of Wands", "权杖二": "Two of Wands", "权杖三": "Three of Wands",
        "权杖四": "Four of Wands", "权杖五": "Five of Wands", "权杖六": "Six of Wands",
        "权杖七": "Seven of Wands", "权杖八": "Eight of Wands", "权杖九": "Nine of Wands",
        "权杖十": "Ten of Wands", "权杖侍从": "Page of Wands", "权杖骑士": "Knight of Wands",
        "权杖王后": "Queen of Wands", "权杖国王": "King of Wands",
        "圣杯王牌": "Ace of Cups", "圣杯二": "Two of Cups", "圣杯三": "Three of Cups",
        "圣杯四": "Four of Cups", "圣杯五": "Five of Cups", "圣杯六": "Six of Cups",
        "圣杯七": "Seven of Cups", "圣杯八": "Eight of Cups", "圣杯九": "Nine of Cups",
        "圣杯十": "Ten of Cups", "圣杯侍从": "Page of Cups", "圣杯骑士": "Knight of Cups",
        "圣杯王后": "Queen of Cups", "圣杯国王": "King of Cups",
        "宝剑王牌": "Ace of Swords", "宝剑二": "Two of Swords", "宝剑三": "Three of Swords",
        "宝剑四": "Four of Swords", "宝剑五": "Five of Swords", "宝剑六": "Six of Swords",
        "宝剑七": "Seven of Swords", "宝剑八": "Eight of Swords", "宝剑九": "Nine of Swords",
        "宝剑十": "Ten of Swords", "宝剑侍从": "Page of Swords", "宝剑骑士": "Knight of Swords",
        "宝剑王后": "Queen of Swords", "宝剑国王": "King of Swords",
        "星币王牌": "Ace of Pentacles", "星币二": "Two of Pentacles", "星币三": "Three of Pentacles",
        "星币四": "Four of Pentacles", "星币五": "Five of Pentacles", "星币六": "Six of Pentacles",
        "星币七": "Seven of Pentacles", "星币八": "Eight of Pentacles", "星币九": "Nine of Pentacles",
        "星币十": "Ten of Pentacles", "星币侍从": "Page of Pentacles", "星币骑士": "Knight of Pentacles",
        "星币王后": "Queen of Pentacles", "星币国王": "King of Pentacles",
        # 雷诺曼牌名（name_zh 叶值，与 `content/lenormand.CARDS` 同源）；山/太阳与上面同词同译不重复。
        "骑士": "Rider", "三叶草": "Clover", "船": "Ship", "房屋": "House",
        "树": "Tree", "云": "Clouds", "蛇": "Snake", "棺材": "Coffin", "花束": "Bouquet",
        "镰刀": "Scythe", "鞭子": "Birch", "鸟": "Birds", "小孩": "Child", "狐狸": "Fox",
        "熊": "Bear", "鹳": "Stork", "狗": "Dog", "花园": "Garden", "岔路": "Crossroad",
        "老鼠": "Mice", "心": "Heart", "戒指": "Ring", "书": "Book", "信": "Letter",
        "男人": "Man", "女人": "Woman", "百合": "Lily", "钥匙": "Key", "鱼": "Fish",
        "锚": "Anchor", "十字架": "Cross",
        # 六十四卦（zhouyi full_name_zh / name_zh 叶值，与 `content/zhouyi_hexagrams.KING_WEN_SEQUENCE` 同源）：
        # en 取同一表自带的英文卦名（name_en）。八卦卦名（乾坤震巽坎离艮兑）已入上表（p15-a），此处只补
        # 其余卦短名；全局单表整串精确匹配，长句判语（如「倾否，先否后喜。」）不会被单字短名命中。
        "乾为天": "Heaven (The Creative)", "坤为地": "Earth (The Receptive)",
        "水雷屯": "Difficulty at the Beginning", "山水蒙": "Youthful Folly",
        "水天需": "Waiting", "天水讼": "Conflict", "地水师": "The Army",
        "水地比": "Holding Together", "风天小畜": "The Taming Power of the Small",
        "天泽履": "Treading", "地天泰": "Peace", "天地否": "Standstill",
        "天火同人": "Fellowship with Others", "火天大有": "Possession in Great Measure",
        "地山谦": "Modesty", "雷地豫": "Enthusiasm", "泽雷随": "Following",
        "山风蛊": "Work on What Has Been Spoiled", "地泽临": "Approach",
        "风地观": "Contemplation", "火雷噬嗑": "Biting Through", "山火贲": "Grace",
        "山地剥": "Splitting Apart", "地雷复": "Return", "天雷无妄": "Innocence",
        "山天大畜": "The Taming Power of the Great", "山雷颐": "The Corners of the Mouth",
        "泽风大过": "Preponderance of the Great", "坎为水": "The Abysmal (Water)",
        "离为火": "The Clinging (Fire)", "泽山咸": "Influence", "雷风恒": "Duration",
        "天山遁": "Retreat", "雷天大壮": "The Power of the Great", "火地晋": "Progress",
        "地火明夷": "Darkening of the Light", "风火家人": "The Family",
        "火泽睽": "Opposition", "水山蹇": "Obstruction", "雷水解": "Deliverance",
        "山泽损": "Decrease", "风雷益": "Increase", "泽天夬": "Breakthrough",
        "天风姤": "Coming to Meet", "泽地萃": "Gathering Together",
        "地风升": "Pushing Upward", "泽水困": "Oppression", "水风井": "The Well",
        "泽火革": "Revolution", "火风鼎": "The Cauldron", "震为雷": "The Arousing (Thunder)",
        "艮为山": "Keeping Still (Mountain)", "风山渐": "Development",
        "雷泽归妹": "The Marrying Maiden", "雷火丰": "Abundance", "火山旅": "The Wanderer",
        "巽为风": "The Gentle (Wind)", "兑为泽": "The Joyous (Lake)",
        "风水涣": "Dispersion", "水泽节": "Limitation", "风泽中孚": "Inner Truth",
        "雷山小过": "Preponderance of the Small", "水火既济": "After Completion",
        "火水未济": "Before Completion",
        # 卦短名（name_zh 叶值，与所属卦同名同译）：
        "屯": "Difficulty at the Beginning", "蒙": "Youthful Folly", "需": "Waiting",
        "讼": "Conflict", "师": "The Army", "比": "Holding Together",
        "小畜": "The Taming Power of the Small", "履": "Treading", "泰": "Peace",
        "否": "Standstill", "同人": "Fellowship with Others",
        "大有": "Possession in Great Measure", "谦": "Modesty", "豫": "Enthusiasm",
        "随": "Following", "蛊": "Work on What Has Been Spoiled", "临": "Approach",
        "观": "Contemplation", "噬嗑": "Biting Through", "贲": "Grace",
        "剥": "Splitting Apart", "复": "Return", "无妄": "Innocence",
        "大畜": "The Taming Power of the Great", "颐": "The Corners of the Mouth",
        "大过": "Preponderance of the Great", "咸": "Influence", "恒": "Duration",
        "遁": "Retreat", "大壮": "The Power of the Great", "晋": "Progress",
        "明夷": "Darkening of the Light", "家人": "The Family", "睽": "Opposition",
        "蹇": "Obstruction", "解": "Deliverance", "损": "Decrease", "益": "Increase",
        "夬": "Breakthrough", "姤": "Coming to Meet", "萃": "Gathering Together",
        "升": "Pushing Upward", "困": "Oppression", "井": "The Well",
        "革": "Revolution", "鼎": "The Cauldron", "渐": "Development",
        "归妹": "The Marrying Maiden", "丰": "Abundance", "旅": "The Wanderer",
        "涣": "Dispersion", "节": "Limitation", "中孚": "Inner Truth",
        "小过": "Preponderance of the Small", "既济": "After Completion",
        "未济": "Before Completion",
        # 八宫宫名（palace_name_zh 叶值，与 `content/zhouyi_hexagrams.PALACES` 卦首同源）：
        # 宫以其卦首三画卦之象命名，故取卦象英译 + Palace，而非复用卦首六画卦全名。
        "乾宫": "Heaven Palace", "坎宫": "Water Palace", "艮宫": "Mountain Palace",
        "震宫": "Thunder Palace", "巽宫": "Wind Palace", "离宫": "Fire Palace",
        "坤宫": "Earth Palace", "兑宫": "Lake Palace",
        # 八宫世次（generation 叶值，与 `content/zhouyi_hexagrams.GENERATION_NAMES` 同源）。
        "本宫": "Original Palace", "一世": "First Generation", "二世": "Second Generation",
        "三世": "Third Generation", "四世": "Fourth Generation", "五世": "Fifth Generation",
        "游魂": "Wandering Soul", "归魂": "Returning Soul",
        # 卡巴拉三柱与隐藏原质 Daath（pillar.name_zh / DAATH.name_zh 叶值，与 `content/kabbalah.PILLARS` 同源）：
        # 只登记不与其它系统共形的专名复合词。十原质 name_zh（美/智慧/胜利…）与希伯来字母音译
        # （如 辛 即天干）都是共形常用词，全局单表无法按系统区分，故不入表（回落源文）。
        "慈悲之柱": "Pillar of Mercy", "严厉之柱": "Pillar of Severity",
        "中柱·平衡": "Pillar of Equilibrium", "知识（隐藏）": "Daath (Hidden)",
        # 二十七星宿（vedic nakshatra name_zh 叶值，与 `content/vedic.NAKSHATRAS` 同源）：
        # en 取同一表自带梵文拉丁转写（name_en）。星宿名系音译，无权威繁体，不入 zh-Hant（同符文裁定）。
        "阿湿毗尼": "Ashwini", "婆罗尼": "Bharani", "基栗底伽": "Krittika", "楼喜尼": "Rohini",
        "弥利迦奢罗": "Mrigashira", "阿陀罗": "Ardra", "布纳瓦苏": "Punarvasu", "布沙": "Pushya",
        "阿湿利沙": "Ashlesha", "摩伽": "Magha", "前发座": "Purva Phalguni", "后发座": "Uttara Phalguni",
        "哈斯塔": "Hasta", "质多罗": "Chitra", "室伐底": "Swati", "毗舍佉": "Vishakha",
        "阿努罗陀": "Anuradha", "耆宿": "Jyeshtha", "牟拉": "Mula", "前阿沙荼": "Purva Ashadha",
        "后阿沙荼": "Uttara Ashadha", "室罗伐那": "Shravana", "陀尼沙": "Dhanishta", "百药": "Shatabhisha",
        "前婆罗钵提": "Purva Bhadrapada", "后婆罗钵提": "Uttara Bhadrapada", "梨婆底": "Revati",
        # 三颗外行星（western/transit/synastry 行星中文名叶值，与 `engines/western.PLANETS` 同源）：
        # 日/月/水/金/火/木/土已由九曜入表，此处只补三颗天王/海王/冥王（繁体同形，不登 zh-Hant）。
        "天王星": "Uranus", "海王星": "Neptune", "冥王星": "Pluto",
        # 紫微十四主星（ziwei major star name 叶值，与 `content/ziwei.MAJOR_STARS.id` 同源）：
        # en 取同一表自带拼音 id（首字母大写）。太阳/太阴/火星已由九曜入表（同词同译），此处不重复。
        "紫微": "Ziwei", "天机": "Tianji", "武曲": "Wuqu", "天同": "Tiantong",
        "廉贞": "Lianzhen", "天府": "Tianfu", "贪狼": "Tanlang", "巨门": "Jumen",
        "天相": "Tianxiang", "天梁": "Tianliang", "七杀": "Qisha", "破军": "Pojun",
        # 紫微乙级星（minor star name 叶值，与 `content/ziwei.MINOR_STARS` 同源）：取拼音转写。
        "左辅": "Zuofu", "右弼": "Youbi", "文昌": "Wenchang", "文曲": "Wenqu",
        "天魁": "Tiankui", "天钺": "Tianyue", "禄存": "Lucun", "天马": "Tianma",
        "擎羊": "Qingyang", "陀罗": "Tuoluo", "铃星": "Lingxing", "地空": "Dikong", "地劫": "Dijie",
        # 生年四化（SIHUA_LABELS 叶值）与五行局（WUXING_JU）/星系标签：取拼音/直译。
        "化禄": "Hua Lu", "化权": "Hua Quan", "化科": "Hua Ke", "化忌": "Hua Ji",
        "水二局": "Water 2 Bureau", "木三局": "Wood 3 Bureau", "金四局": "Gold 4 Bureau",
        "土五局": "Earth 5 Bureau", "火六局": "Fire 6 Bureau",
        "紫微系": "Ziwei Group", "天府系": "Tianfu Group",
        # 八字十神（bazi shishen_gan / ten_god 叶值，与 `content/bazi_shishen.TEN_GOD_MEANING` 同源）：
        # 取拼音转写，与上面紫微星名同一口径（七杀已由紫微 Qisha 入表，同词同译，不重复）。
        "比肩": "Bijian", "劫财": "Jiecai", "食神": "Shishen", "伤官": "Shangguan",
        "偏财": "Piancai", "正财": "Zhengcai", "正官": "Zhengguan", "偏印": "Pianyin",
        "正印": "Zhengyin", "日主": "Day Master",
        # 八字辅助专名（bazi/natal 叶值）：维度类别、柱位、藏干层次、旺衰带。
        "事业": "Career", "财运": "Wealth", "婚姻": "Marriage",
        "健康": "Health", "学业": "Studies", "人际": "Relationships",
        "年柱": "Year Pillar", "月柱": "Month Pillar", "日柱": "Day Pillar", "时柱": "Hour Pillar",
        "本气": "Primary Qi", "中气": "Middle Qi", "余气": "Residual Qi",
        "身强": "Strong", "中和": "Balanced", "身弱": "Weak",
        # 十二长生（`content/bazi_changsheng.CHANG_SHENG_ORDER`）：五行寄生十二宫阶段名。
        "长生": "Growth", "沐浴": "Bathing", "冠带": "Capping", "临官": "Officing",
        "帝旺": "Peak", "衰": "Decline", "病": "Illness", "死": "Death",
        "墓": "Tomb", "绝": "Extinction", "胎": "Conception", "养": "Nurturing",
        # 八字格局（`content/bazi_geju.GEJU_RULES`）：十神拼音根 + Structure，与上十神同口径。
        "正官格": "Zhengguan Structure", "七杀格": "Qisha Structure",
        "正印格": "Zhengyin Structure", "偏印格": "Pianyin Structure",
        "食神格": "Shishen Structure", "伤官格": "Shangguan Structure",
        "正财格": "Zhengcai Structure", "偏财格": "Piancai Structure",
        "建禄格": "Jianlu Structure", "月刃格": "Yueren Structure",
        # 八字神煞（`content/bazi_shensha.SHENSHA_RULES` 叶值）：取意译，贵人一律 Noble。
        "天乙贵人": "Celestial Noble", "文昌贵人": "Literary Noble", "太极贵人": "Taiji Noble",
        "天德贵人": "Heavenly Virtue Noble", "月德贵人": "Lunar Virtue Noble",
        "建禄": "Established Prosperity", "羊刃": "Ram Blade", "金舆": "Golden Carriage",
        "咸池": "Xianchi Pool", "驿马": "Travel Horse", "华盖": "Imperial Canopy",
        "将星": "General Star", "劫煞": "Calamity Star", "亡神": "Hidden Foe",
        "魁罡": "Kuigang", "空亡": "Void",
        # 六十甲子纳音（`content/bazi_nayin` 30 组名）：五行后缀按元素意译。
        "海中金": "Gold in the Sea", "炉中火": "Fire in the Furnace", "大林木": "Forest Wood",
        "路旁土": "Roadside Earth", "剑锋金": "Sword-Edge Metal", "山头火": "Mountaintop Fire",
        "涧下水": "Valley Stream Water", "城头土": "City Wall Earth", "白蜡金": "White Wax Metal",
        "杨柳木": "Willow Wood", "泉中水": "Spring Water", "屋上土": "Rooftop Earth",
        "霹雳火": "Thunderbolt Fire", "松柏木": "Pine and Cypress Wood", "长流水": "Flowing Water",
        "沙中金": "Gold in the Sand", "山下火": "Fire Below the Mountain", "平地木": "Plain Wood",
        "壁上土": "Wall Earth", "金箔金": "Gold Foil Metal", "覆灯火": "Lantern Fire",
        "天河水": "Heavenly River Water", "大驿土": "Post-Station Earth", "钗钏金": "Hairpin Metal",
        "桑柘木": "Mulberry Wood", "大溪水": "Great Stream Water", "沙中土": "Sand Earth",
        "天上火": "Heavenly Fire", "石榴木": "Pomegranate Wood", "大海水": "Great Sea Water",
        # 六十甲子干支柱（bazi pillar 合成叶值）：天干拼音 + 地支拼音，与上单字同口径；皆繁简同形，无需繁体。
        "甲子": "Jia Zi", "乙丑": "Yi Chou", "丙寅": "Bing Yin", "丁卯": "Ding Mao",
        "戊辰": "Wu Chen", "己巳": "Ji Si", "庚午": "Geng Wu", "辛未": "Xin Wei",
        "壬申": "Ren Shen", "癸酉": "Gui You", "甲戌": "Jia Xu", "乙亥": "Yi Hai",
        "丙子": "Bing Zi", "丁丑": "Ding Chou", "戊寅": "Wu Yin", "己卯": "Ji Mao",
        "庚辰": "Geng Chen", "辛巳": "Xin Si", "壬午": "Ren Wu", "癸未": "Gui Wei",
        "甲申": "Jia Shen", "乙酉": "Yi You", "丙戌": "Bing Xu", "丁亥": "Ding Hai",
        "戊子": "Wu Zi", "己丑": "Ji Chou", "庚寅": "Geng Yin", "辛卯": "Xin Mao",
        "壬辰": "Ren Chen", "癸巳": "Gui Si", "甲午": "Jia Wu", "乙未": "Yi Wei",
        "丙申": "Bing Shen", "丁酉": "Ding You", "戊戌": "Wu Xu", "己亥": "Ji Hai",
        "庚子": "Geng Zi", "辛丑": "Xin Chou", "壬寅": "Ren Yin", "癸卯": "Gui Mao",
        "甲辰": "Jia Chen", "乙巳": "Yi Si", "丙午": "Bing Wu", "丁未": "Ding Wei",
        "戊申": "Wu Shen", "己酉": "Ji You", "庚戌": "Geng Xu", "辛亥": "Xin Hai",
        "壬子": "Ren Zi", "癸丑": "Gui Chou", "甲寅": "Jia Yin", "乙卯": "Yi Mao",
        "丙辰": "Bing Chen", "丁巳": "Ding Si", "戊午": "Wu Wu", "己未": "Ji Wei",
        "庚申": "Geng Shen", "辛酉": "Xin You", "壬戌": "Ren Xu", "癸亥": "Gui Hai",
        # 干支关系枚举名（`content/bazi_relations.RELATION_TABLES` keys）：合冲刑害会·伏反吟。
        "三会": "Branch Directional Union", "三合": "Branch Triple Harmony", "伏吟": "Fu Yin Repetition",
        "半合": "Half Harmony", "反吟": "Fan Yin Reverse", "地支六冲": "Six Branch Clashes",
        "地支六合": "Six Branch Combinations", "地支六害": "Six Branch Harms", "地支六破": "Six Branch Breaks",
        "天干五合": "Five Stem Combines", "天干相冲": "Stem Clashes", "恃势之刑": "Punishment by Power",
        "无恩之刑": "Ungrateful Punishment", "无礼之刑": "Discourteous Punishment", "自刑": "Self Punishment",
        # 八字结构化标签：用神三法（bazi_yongshen）、柱距力量档（bazi_rules STRENGTH_BY_DISTANCE）、岁运档位（顺/滞，平 已在结论档）、评分基准行。
        "扶抑": "Support-Suppress", "通关": "Mediation", "调候": "Climate Adjustment", "紧临": "Adjacent", "隔位": "Separated", "远位": "Distant", "顺": "Favorable", "滞": "Stagnant", "基准分": "Baseline Score",
        # 周易六爻爻题（`content/zhouyi_text.line_name`）：本卦/变卦六爻位置名，皆繁简同形无需繁体。
        "初九": "First Line (Yang)", "初六": "First Line (Yin)", "九二": "Second Line (Yang)",
        "六二": "Second Line (Yin)", "九三": "Third Line (Yang)", "六三": "Third Line (Yin)",
        "九四": "Fourth Line (Yang)", "六四": "Fourth Line (Yin)", "九五": "Fifth Line (Yang)",
        "六五": "Fifth Line (Yin)", "上九": "Top Line (Yang)", "上六": "Top Line (Yin)",
        # 二十四节气（`content/qimen.YANG_JU`+`YIN_JU` keys）：历法权威词，跨奇门/岁运/节气月出现。
        "冬至": "Winter Solstice", "处暑": "End of Heat", "夏至": "Summer Solstice", "大寒": "Major Cold",
        "大暑": "Major Heat", "大雪": "Major Snow", "寒露": "Cold Dew", "小寒": "Minor Cold",
        "小暑": "Minor Heat", "小满": "Grain Full", "小雪": "Minor Snow", "惊蛰": "Awakening of Insects",
        "春分": "Spring Equinox", "清明": "Clear and Bright", "白露": "White Dew", "秋分": "Autumn Equinox",
        "立冬": "Start of Winter", "立夏": "Start of Summer", "立春": "Start of Spring", "立秋": "Start of Autumn",
        "芒种": "Grain in Ear", "谷雨": "Grain Rain", "雨水": "Rain Water", "霜降": "Frost's Descent",
        # 月令旺相休囚死（`content/bazi_wangshuai.WANG_SHUAI_VALUE` keys）＋奇门三元（`content/qimen.YUAN_NAMES`）：均繁简同形，仅登 en（死复用十二长生 Death）。
        "旺": "Prosperous", "相": "Viable", "休": "Resting", "囚": "Imprisoned", "上元": "Upper Yuan", "中元": "Middle Yuan", "下元": "Lower Yuan",
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
