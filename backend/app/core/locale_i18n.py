"""后端响应文案的本地化层（cross-cutting，`core/` 底层，任何层可引）。

形状与前端 `i18n/messages.ts` 一致：**源简体字符串当 key**，命中即替换，未命中回落源文。
挂载点是已序列化的 JSON 响应叶子，做两层精确匹配（`localize`→`_localize_leaf`）：整串命中优先；
未命中且该串含 `\n`（`plain_compose` 用换行把开篇句/条目/收尾句拼成一段），则**逐行**精确查表后
拼回——合成段落里的每一行仍要求逐字等于某个 key，不是子串替换。这一层覆盖有界、高复用的结构化
标签（档位词、小节标题、专名词表），深判语则是把这些固定行与逐条转述句登记进 `LABELS` 的内容批次。

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
        # 数理数字繁体（与上同源）：仅登记字形有差且无一对多歧义字者。
        "个人年根": "個人年根", "个人月根": "個人月根", "个人流年（前一年）": "個人流年（前一年）", "个人流年（本年）": "個人流年（本年）",
        "个人流年（次年）": "個人流年（次年）", "个人流日（今日）": "個人流日（今日）", "个人流月（本月）": "個人流月（本月）", "主挑战 Main Challenge": "主挑戰 Main Challenge",
        "乐观": "樂觀", "人格面具数 Personality": "人格面具數 Personality", "先驱": "先驅", "关爱": "關愛",
        "冒险": "冒險", "决断": "決斷", "创造": "創造", "务实": "務實",
        "变动": "變動", "启示": "啟示", "奉献": "奉獻", "宏图": "宏圖",
        "实务平面": "實務平面", "开创": "開創", "引领": "引領", "悲悯": "悲憫",
        "成熟数 Maturity": "成熟數 Maturity", "才艺": "才藝", "教导": "教導", "服务": "服務",
        "权威": "權威", "灵感": "靈感", "灵魂冲动数 Soul Urge": "靈魂衝動數 Soul Urge", "独处": "獨處",
        "独立": "獨立", "生命灵数 Life Path": "生命靈數 Life Path", "生日数 Birthday": "生日數 Birthday", "疗愈": "療愈",
        "直觉": "直覺", "第一挑战 First Challenge": "第一挑戰 First Challenge", "第一顶峰 First Pinnacle": "第一頂峰 First Pinnacle", "第三顶峰 Third Pinnacle": "第三頂峰 Third Pinnacle",
        "第二挑战 Second Challenge": "第二挑戰 Second Challenge", "第二顶峰 Second Pinnacle": "第二頂峰 Second Pinnacle", "第四挑战 Fourth Challenge": "第四挑戰 Fourth Challenge", "第四顶峰 Fourth Pinnacle": "第四頂峰 Fourth Pinnacle",
        "系统": "系統", "经营": "經營", "结构": "結構", "自我主张": "自我主張",
        "行动平面": "行動平面", "表达": "表達", "表达数 Expression": "表達數 Expression", "调和": "調和",
        "责任": "責任", "贯穿一生": "貫穿一生",
        # 岁运规则短名繁体（与上同源；干保留天干之干，冲取六冲之沖）。
        "三会喜用": "三會喜用", "三会忌": "三會忌", "值太岁": "值太歲",
        "冲太岁": "沖太歲", "冲提纲": "沖提綱", "冲本身宫": "沖本身宮",
        "刑太岁": "刑太歲", "刑提纲": "刑提綱", "刑本身宫": "刑本身宮",
        "合太岁": "合太歲", "合提纲": "合提綱", "合本身宫": "合本身宮",
        "大运": "大運", "害太岁": "害太歲", "害提纲": "害提綱",
        "害本身宫": "害本身宮", "小运": "小運", "岁生运": "歲生運",
        "岁运并临": "歲運並臨", "日主临官帝旺": "日主臨官帝旺", "日主临衰病死墓绝": "日主臨衰病死墓絕",
        "日主临长生冠带胎养": "日主臨長生冠帶胎養", "流时": "流時", "破太岁": "破太歲",
        "运岁干合": "運歲干合", "运干入喜用": "運干入喜用", "运干入忌": "運干入忌",
        "运干冲日主": "運干沖日主", "运干合日主": "運干合日主", "运年反吟": "運年反吟",
        "运支主气入喜用": "運支主氣入喜用", "运支主气入忌": "運支主氣入忌", "运生岁": "運生歲", "辅音": "輔音", "远见": "遠見",
        "适应": "適應", "银弓（财富之箭）": "銀弓（財富之箭）", "领导": "領導",
        # 二十四节气繁体（与上同源）：仅登记字形有差者（惊/蛰/种/满/处转形）。
        "处暑": "處暑", "小满": "小滿", "惊蛰": "驚蟄", "芒种": "芒種",
        # 紫微乙级星 kind / 阴阳 / 顺逆行 + 奇门遁局 + 梅花体用小节/关系/旺衰档位（仅字形有差者登记，繁简同形回落源文）。
        "禄马": "祿馬", "顺行": "順行", "阳": "陽",
        "阴": "陰", "阳遁": "陽遁", "阴遁": "陰遁",
        "体用生克": "體用生克", "卦气旺衰": "卦氣旺衰", "互卦(过程)": "互卦(過程)",
        "变卦(结局)": "變卦(結局)", "用生体": "用生體", "体用比和": "體用比和",
        "体克用": "體克用", "体生用": "體生用", "用克体": "用克體",
        # 奇门局名（阳遁/阴遁 × 一..九局，仅阳->陽/阴->陰转形）；旬空/宫位地支二支对繁简同形，回落源文。
        "阳遁一局": "陽遁一局", "阳遁二局": "陽遁二局", "阳遁三局": "陽遁三局",
        "阳遁四局": "陽遁四局", "阳遁五局": "陽遁五局", "阳遁六局": "陽遁六局",
        "阳遁七局": "陽遁七局", "阳遁八局": "陽遁八局", "阳遁九局": "陽遁九局",
        "阴遁一局": "陰遁一局", "阴遁二局": "陰遁二局", "阴遁三局": "陰遁三局",
        "阴遁四局": "陰遁四局", "阴遁五局": "陰遁五局", "阴遁六局": "陰遁六局",
        "阴遁七局": "陰遁七局", "阴遁八局": "陰遁八局", "阴遁九局": "陰遁九局",
        # 紫微十四主星 + 奇门九星/八门/八神 类象 nature（逐条 curated 繁体；同形者透传）。
        "帝座·尊贵领导": "帝座·尊貴領導",
        "智慧·谋略机变": "智慧·謀略機變",
        "光明·博爱贵气": "光明·博愛貴氣",
        "财帛·刚毅果决": "財帛·剛毅果決",
        "财库·稳重保守": "財庫·穩重保守",
        "田宅·富洁母性": "田宅·富潔母性",
        "桃花·欲望才艺": "桃花·欲望才藝",
        "印星·辅佐公正": "印星·輔佐公正",
        "荫星·长寿消解": "蔭星·長壽消解",
        "将星·冲劲肃杀": "將星·衝勁肅殺",
        "耗星·破旧立新": "耗星·破舊立新",
        "贪狼·暗昧盗贼": "貪狼·暗昧盜賊",
        "巨门·疾病瘟癀": "巨門·疾病瘟癀",
        "禄存·雷厉武动": "祿存·雷厲武動",
        "文曲·文教辅助": "文曲·文教輔助",
        "廉贞·中正仁和": "廉貞·中正仁和",
        "武曲·医药谋略": "武曲·醫藥謀略",
        "破军·毁折口舌": "破軍·毀折口舌",
        "左辅·诚信敦厚": "左輔·誠信敦厚",
        "休养生息·谒贵求财": "休養生息·謁貴求財",
        "死寂闭塞·吊丧田猎": "死寂閉塞·弔喪田獵",
        "伤害竞争·捕猎索债": "傷害競爭·捕獵索債",
        "杜藏闭塞·隐身躲避": "杜藏閉塞·隱身躲避",
        "开通发达·求财赴任": "開通發達·求財赴任",
        "惊恐忧疑·官讼口舌": "驚恐憂疑·官訟口舌",
        "生发兴隆·求财营造": "生發興隆·求財營造",
        "光明文书·宴乐奏章": "光明文書·宴樂奏章",
        "贵人首领·百恶不侵": "貴人首領·百惡不侵",
        "虚惊怪异·缠绕不定": "虛驚怪異·纏繞不定",
        "阴私暗助·隐秘谋划": "陰私暗助·隱秘謀劃",
        "刚猛道路·凶伤血光": "剛猛道路·凶傷血光",
        "盗贼暧昧·欺瞒暗昧": "盜賊曖昧·欺瞞暗昧",
        "沉静厚载·守藏屯兵": "沉靜厚載·守藏屯兵",
        "扬动高远·出行扩张": "揚動高遠·出行擴張",
        # 十二生肖（.zodiac，lunar-python 立春生肖）：仅龙/马/鸡/猪字形有差，余同形回落源文。
        "龙": "龍", "马": "馬", "鸡": "雞", "猪": "豬",
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
        # 岁运账本规则短名（`content/bazi_transit_rules.TRANSIT_RULES` label 列，除已登记神煞/伏反吟）＋岁运粒度名。
        "运干入喜用": "Luck Stem Enters Favorable", "运干入忌": "Luck Stem Enters Taboo", "运支主气入喜用": "Luck Branch Primary Qi Enters Favorable",
        "运支主气入忌": "Luck Branch Primary Qi Enters Taboo", "冲太岁": "Clashing Tai Sui", "值太岁": "Encountering Tai Sui",
        "害太岁": "Harming Tai Sui", "刑太岁": "Punishing Tai Sui", "破太岁": "Breaking Tai Sui",
        "合太岁": "Combining with Tai Sui", "冲提纲": "Clashing the Month Command", "冲本身宫": "Clashing the Body Palace",
        "刑提纲": "Punishing the Month Command", "刑本身宫": "Punishing the Body Palace", "合提纲": "Combining the Month Command",
        "合本身宫": "Combining the Body Palace", "害提纲": "Harming the Month Command", "害本身宫": "Harming the Body Palace",
        "三合成喜用": "Three-Harmony Forms Favorable", "三合成忌": "Three-Harmony Forms Taboo", "半合喜用": "Half-Combine Favorable",
        "半合忌": "Half-Combine Taboo", "三会喜用": "Three-Assembly Favorable", "三会忌": "Three-Assembly Taboo",
        "运干合日主": "Luck Stem Combines with Day Master", "运干冲日主": "Luck Stem Clashes Day Master", "岁运并临": "Luck and Year Arrive Together",
        "运年反吟": "Luck-Year Reverse Chant", "运生岁": "Luck Generates the Year", "岁生运": "Year Generates the Luck",
        "运岁干合": "Luck-Year Stem Combine", "日主临官帝旺": "Day Master at Office and Peak", "日主临长生冠带胎养": "Day Master at Growth, Capping, Conception, Nurturing",
        "日主临衰病死墓绝": "Day Master at Decline, Illness, Death, Tomb, Extinction", "流年": "Flowing Year", "流月": "Flowing Month",
        "流日": "Flowing Day", "流时": "Flowing Hour", "大运": "Major Luck Cycle",
        "小运": "Minor Luck Cycle",
        # 数理数字（numerology）显示名：核心/顶峰/挑战/周期标签、洛书八平面、核心数关键词、账本角色。
        "生命灵数 Life Path": "Life Path", "表达数 Expression": "Expression", "灵魂冲动数 Soul Urge": "Soul Urge", "人格面具数 Personality": "Personality",
        "生日数 Birthday": "Birthday", "成熟数 Maturity": "Maturity", "第一顶峰 First Pinnacle": "First Pinnacle", "第二顶峰 Second Pinnacle": "Second Pinnacle",
        "第三顶峰 Third Pinnacle": "Third Pinnacle", "第四顶峰 Fourth Pinnacle": "Fourth Pinnacle", "第一挑战 First Challenge": "First Challenge", "第二挑战 Second Challenge": "Second Challenge",
        "主挑战 Main Challenge": "Main Challenge", "第四挑战 Fourth Challenge": "Fourth Challenge", "个人流年（前一年）": "Personal Year (Previous)", "个人流年（本年）": "Personal Year (Current)",
        "个人流年（次年）": "Personal Year (Next)", "个人流月（本月）": "Personal Month (Current)", "个人流日（今日）": "Personal Day (Today)", "心智平面": "Mental Plane",
        "情感平面": "Emotional Plane", "实务平面": "Practical Plane", "思想平面": "Plane of Thought", "意志之箭": "Plane of Will",
        "行动平面": "Plane of Action", "银弓（财富之箭）": "Silver Yog", "金弓（成功之箭）": "Golden Yog", "乐观": "Optimistic",
        "先驱": "Pioneer", "关爱": "Caring", "典范": "Exemplar", "内省": "Introspective",
        "冒险": "Adventurous", "决断": "Decisive", "创造": "Creative", "务实": "Practical",
        "勤勉": "Diligent", "变动": "Changeable", "可靠": "Reliable", "合作": "Cooperative",
        "启示": "Inspiration", "外交": "Diplomatic", "多才": "Versatile", "奉献": "Dedication",
        "完成": "Completion", "宏图": "Grand Vision", "实干": "Hands-on", "家庭": "Family",
        "开创": "Initiating", "引领": "Guiding", "悲悯": "Compassion", "慈悲": "Mercy",
        "成就": "Achievement", "才艺": "Talent", "敏感": "Sensitive", "教导": "Teaching",
        "普世": "Universal", "服务": "Service", "权威": "Authority", "格局": "Overview",
        "求真": "Truth-seeking", "灵感": "Insight", "独处": "Solitude", "独立": "Independent",
        "理想": "Idealistic", "疗愈": "Healing", "直觉": "Intuition", "研究": "Research",
        "社交": "Sociable", "秩序": "Order", "系统": "System", "经营": "Management",
        "结构": "Structure", "美感": "Aesthetics", "耐心": "Patience", "自我主张": "Self-assertion",
        "自由": "Freedom", "舍予": "Giving", "落地": "Grounding", "表达": "Expression",
        "调和": "Harmonizing", "责任": "Responsibility", "远见": "Foresight", "适应": "Adaptable",
        "领导": "Leadership", "元音": "Vowels", "辅音": "Consonants", "全字母": "All Letters",
        "相加": "Sum", "成熟": "Maturity", "个人年根": "Personal Year Root", "个人月根": "Personal Month Root",
        "出生日": "Birth Day", "出生月": "Birth Month", "贯穿一生": "Across a Lifetime", "年": "Year",
        "月": "Month", "日": "Day",
        # 月令旺相休囚死（`content/bazi_wangshuai.WANG_SHUAI_VALUE` keys）＋奇门三元（`content/qimen.YUAN_NAMES`）：均繁简同形，仅登 en（死复用十二长生 Death）。
        "旺": "Prosperous", "相": "Viable", "休": "Resting", "囚": "Imprisoned", "上元": "Upper Yuan", "中元": "Middle Yuan", "下元": "Lower Yuan",
        # 紫微 kind/阴阳/顺逆行、奇门阳遁阴遁、梅花体用小节标签/体用关系/月令季节/旺衰档位（p15 有界专名族）。
        "主星": "Major Star", "煞": "Malefic", "禄马": "Prosperity & Horse",
        "顺行": "Forward Progression", "逆行": "Retrograde Progression", "阳": "Yang",
        "阴": "Yin", "阳遁": "Yang Dun", "阴遁": "Yin Dun",
        "体用生克": "Ti-Yong Interaction", "卦气旺衰": "Hexagram Qi Strength", "互卦(过程)": "Nuclear Hexagram (Process)",
        "变卦(结局)": "Changed Hexagram (Outcome)", "上吉": "Supreme Fortune", "小吉": "Minor Fortune",
        "大凶": "Great Misfortune", "用生体": "Yong Generates Ti", "体用比和": "Ti & Yong Harmonious",
        "体克用": "Ti Controls Yong", "体生用": "Ti Generates Yong", "用克体": "Yong Controls Ti",
        "孟春": "Early Spring", "仲春": "Mid Spring", "季春": "Late Spring",
        "孟夏": "Early Summer", "仲夏": "Mid Summer", "季夏": "Late Summer",
        "孟秋": "Early Autumn", "仲秋": "Mid Autumn", "季秋": "Late Autumn",
        "孟冬": "Early Winter", "仲冬": "Mid Winter", "季冬": "Late Winter",
        # 奇门局名（Yang/Yin Dun Ju 1-9）＋宫位/旬空地支二支对（pinyin，与单支同表派生）。
        "丑寅": "Chou & Yin", "午未": "Wu & Wei", "子丑": "Zi & Chou",
        "寅卯": "Yin & Mao", "戌亥": "Xu & Hai", "未申": "Wei & Shen",
        "申酉": "Shen & You", "辰巳": "Chen & Si", "阳遁一局": "Yang Dun Ju 1",
        "阳遁二局": "Yang Dun Ju 2", "阳遁三局": "Yang Dun Ju 3", "阳遁四局": "Yang Dun Ju 4",
        "阳遁五局": "Yang Dun Ju 5", "阳遁六局": "Yang Dun Ju 6", "阳遁七局": "Yang Dun Ju 7",
        "阳遁八局": "Yang Dun Ju 8", "阳遁九局": "Yang Dun Ju 9", "阴遁一局": "Yin Dun Ju 1",
        "阴遁二局": "Yin Dun Ju 2", "阴遁三局": "Yin Dun Ju 3", "阴遁四局": "Yin Dun Ju 4",
        "阴遁五局": "Yin Dun Ju 5", "阴遁六局": "Yin Dun Ju 6", "阴遁七局": "Yin Dun Ju 7",
        "阴遁八局": "Yin Dun Ju 8", "阴遁九局": "Yin Dun Ju 9",
        # 紫微十四主星 + 奇门九星/八门/八神 类象 nature 英译（p15 星曜专名词表，39 条）。
        "帝座·尊贵领导": "Imperial Seat · Noble Leadership",
        "智慧·谋略机变": "Wisdom · Strategic Adaptability",
        "光明·博爱贵气": "Radiance · Universal Benevolence",
        "财帛·刚毅果决": "Wealth · Resolute Decisiveness",
        "福禄·温和享受": "Fortune & Emolument · Gentle Comfort",
        "次桃花·政令囚星": "Secondary Peach Blossom · Decree and Confinement",
        "财库·稳重保守": "Treasury · Steady and Prudent",
        "田宅·富洁母性": "Property · Pure Nurturing",
        "桃花·欲望才艺": "Peach Blossom · Desire and Talent",
        "口舌·是非研究": "Speech · Discerning Right and Wrong",
        "印星·辅佐公正": "Seal Star · Support and Justice",
        "荫星·长寿消解": "Sheltering Star · Longevity and Relief",
        "将星·冲劲肃杀": "General Star · Bold Vigor and Austerity",
        "耗星·破旧立新": "Depletion Star · Breaking Old, Making New",
        "贪狼·暗昧盗贼": "Covetous Wolf · Darkness and Theft",
        "巨门·疾病瘟癀": "Huge Gate · Illness and Plague",
        "禄存·雷厉武动": "Prosperity Keeper · Thunderous Vigor",
        "文曲·文教辅助": "Literary Star · Education and Aid",
        "廉贞·中正仁和": "Upright Chastity · Centered Benevolence",
        "武曲·医药谋略": "Martial Star · Medicine and Strategy",
        "破军·毁折口舌": "Breaking Army · Damage and Dispute",
        "左辅·诚信敦厚": "Left Assistant · Sincere Generosity",
        "右弼·血光浮躁": "Right Flanker · Bloodshed and Restlessness",
        "休养生息·谒贵求财": "Rest and Renewal · Audience for Gain",
        "死寂闭塞·吊丧田猎": "Deathly Silence · Mourning and Hunting",
        "伤害竞争·捕猎索债": "Harm and Rivalry · Hunting and Debt-Collection",
        "杜藏闭塞·隐身躲避": "Seclusion and Blocking · Concealment and Avoidance",
        "开通发达·求财赴任": "Opening and Advancement · Wealth and Office",
        "惊恐忧疑·官讼口舌": "Fear and Doubt · Lawsuits and Disputes",
        "生发兴隆·求财营造": "Growth and Prosperity · Wealth and Building",
        "光明文书·宴乐奏章": "Bright Documents · Feasts and Memorials",
        "贵人首领·百恶不侵": "Noble Chief · Impervious to Evil",
        "虚惊怪异·缠绕不定": "False Alarms and Strangeness · Restless Entanglement",
        "阴私暗助·隐秘谋划": "Private Secrets · Hidden Aid and Planning",
        "和合婚姻·交易中介": "Harmony and Marriage · Trade Brokerage",
        "刚猛道路·凶伤血光": "Fierce Roads · Injury and Bloodshed",
        "盗贼暧昧·欺瞒暗昧": "Thieves and Ambiguity · Deceit and Darkness",
        "沉静厚载·守藏屯兵": "Quiet Depth that Bears All · Guarding and Mustering",
        "扬动高远·出行扩张": "Soaring High and Far · Travel and Expansion",
        # 十二生肖（.zodiac）英译（p15 有界专名族；狗复用 lenormand Dog）。
        "鼠": "Rat", "牛": "Ox", "虎": "Tiger", "兔": "Rabbit",
        "龙": "Dragon", "马": "Horse", "羊": "Goat", "猴": "Monkey",
        "鸡": "Rooster", "猪": "Pig",
        # p16 深判语·有界固定行（各系统小节开篇句 / 档位收尾句，compose 以 \n 拼段）英译。
        "事业看的是你的位置和担当：责任压不压身、位置稳不稳，都在这一个维度里说。": "Career reads your position and the weight you carry: whether responsibility presses down and whether your standing holds is all told in this single dimension.",
        "财运看的是你担不担得住钱、钱从哪里来：进得来又留得住，才是好配置。": "Wealth reads whether you can hold money and where it comes from: only what flows in and stays in makes a good configuration.",
        "婚姻看的是你的配偶星和配偶宫：星强宫稳，感情的基本盘就好。": "Marriage reads your spouse star and spouse palace: a strong star and a steady palace mean a sound foundation for your relationships.",
        "健康看的是你盘里五行的分布和流转：气顺不偏，精力就耐用。": "Health reads how the five elements are spread and circulate in your chart: when the qi runs even and unbiased, your energy lasts.",
        "学业看的是你的吸收和输出：学得进、用得出，两头都强才占便宜。": "Studies read your intake and your output: taking in well and applying well - strong at both ends is where the advantage lies.",
        "人际看的是你身边的贵人和同气：肯帮你的人多、消耗你的人少，就是好圈子。": "Relations read the noble helpers and kindred spirits around you: many who lift you, few who drain you - that is a good circle.",
        "这一维是你的优势项：机会给得起，你也接得住，按自己的节奏往前推进就行。": "This dimension is your strength: opportunity is offered and you can take it - simply advance at your own pace.",
        "这一维不功不过：有利的和吃力的基本相抵，你稳着走不会出大问题，想再进一步就得在细节上多用功。": "This dimension is neither credit nor fault: the favorable and the strained largely offset, so moving steadily brings no big trouble; to advance further, put more work into the details.",
        "这一维是你的短板：急不来，把该补的补扎实再谈提速，比硬冲划算得多。": "This dimension is your weak spot: it cannot be rushed - shore up what needs mending before speaking of speed, which pays far better than forcing a charge.",
        "天格看的是你与长辈、门第这一段的关系，它由姓的那一端算出来，是你出生时就带着的部分。": "The Heaven Grid reads your bond with elders and family standing; it is computed from the surname side and is the part you carry from birth.",
        "人格是五格里最贴近当下你自己的那一格，你办事时别人感受到的，多半是这一格的数。": "The Person Grid is the cell closest to who you are right now; what others sense when you act is mostly the number of this cell.",
        "地格由名的笔画合成，看的是你脚下一段的基础与早年的际遇，你从什么地方起步由它说。": "The Earth Grid is built from the strokes of the given name and reads the foundation beneath your feet and your early fortunes - it tells where you set off from.",
        "外格算的是总格与人格之差再加一，你在自家圈子之外怎么被人接住，看的是这一格。": "The Outer Grid is the Total minus the Person, plus one; how you are received beyond your own circle is read in this cell.",
        "总格是全部笔画之和，你走完一圈之后落在什么气象上，五格里由它负责那个整体。": "The Total Grid is the sum of all strokes; the tenor you land on after a full round is its charge among the five cells - it governs the whole.",
        "三才配置看天、人、地三格五行之间谁生谁克，这一段说的是你身上三股力气处得顺不顺。": "The Three Talents configuration reads which of the Heaven, Person, and Earth cells generate or restrain one another in the five elements; this passage tells whether the three forces in you get along.",
        "把五格合起来看，你手上的顺与吃力就有了次序，这一段按两侧重排一遍已经说过的话。": "Taken together, the five cells give an order to the smooth and the strained you hold; this passage rearranges what was already said into the two sides.",
        "你这份五格配置在姓名学里属上等一档，表的措辞在这一档偏向顺遂，读的时候以这一档的气象为主，哪一格自己写着难处，仍以它那句为准。": "Your five-grid configuration falls in the upper tier of name numerology; the table's wording in this tier leans toward smoothness - read it with this tier's tenor as the frame, yet whichever cell itself notes a difficulty still stands by its own sentence.",
        "你这份配置落在中上档，表的措辞以顺为主而留着余地，不必拿单格那句短处重估全盘，也不必让这一档替五格作保。": "Your configuration falls in the upper-middle tier; the table's wording is mostly smooth but leaves room - there is no need to rejudge the whole by one cell's shortcoming, nor to let this tier vouch for all five cells.",
        "你这份配置属中档，表的措辞在这一档是平的，顺与吃力两句都读得进去，轻重由那五格自己说，不由这个档位替你定。": "Your configuration belongs to the middle tier; the table's wording here is even, and both the smooth and the strained sentences read true - the weight is told by those five cells themselves, not set for you by this tier.",
        "你这份配置偏中下档，表的措辞在这一档偏重吃力的那一面，它说的是气象分布，不是你该改什么，也不替你判人。": "Your configuration leans to the lower-middle tier; the table's wording here stresses the strained side. It speaks of how the tenor is distributed, not of what you should change, and it does not pass judgment on people for you.",
        "你这份配置落在下档，表的措辞在这一档最重，读这段时把它当气象分布看，别当作对个人的判词。": "Your configuration falls in the lower tier, where the table's wording is at its heaviest; read this passage as a distribution of tenor, not as a verdict on the person.",
        "三对关系全是生与比，你身上的三股力气彼此扶持，内部不打架是这一段最实在的形容。": "All three pairings are generation and kinship: the three forces in you support one another, and 'no fighting inside' is this passage's truest description.",
        "三对里顺的多而克的一少，你的配置大体走得通，只在某一对上还留着要绕过去的地方。": "Among the three pairs the smooth outnumber the restraining, so your configuration largely works; only one pair still leaves a spot to route around.",
        "三对里克的多而生的少，你这一段上的难处来自互相牵制，不是来自缺少机会。": "Among the three pairs the restraining outnumber the generating, so the difficulty in this stretch comes from mutual restraint, not from a lack of opportunity.",
        "三对皆克，表把抑塞写在明处，它说的是配置之间的气路，不是你本人的成色。": "When all three pairs restrain, the table sets the blockage out in the open; it speaks of the qi-paths between the configurations, not of your own caliber.",
        "把账本里命中的核心羁绊合起来看，你这段关系最要紧的几条轴各落在顺的一侧还是费劲的一侧，下面按两侧重排一遍。": "Taken together, the core bonds struck in the ledger show whether the most critical axes of this relationship land on the smooth side or the effortful side; the two sides are rearranged below.",
        "这一盘没有检到计入账本的核心羁绊，所以这一段不逐条重排，只把档位那一句给你，两侧的相处仍按账本条目自己那句读。": "This chart found no core bond counted in the ledger, so this passage does not rearrange item by item; it gives you only the tier's sentence, and how the two sides get along is still read by each ledger entry's own line.",
        "你这一份相契度落在最深的一档，表的措辞在这一档偏向顺遂，读它的方式是把整段当气象看，哪一条相位自己写着费劲，仍以它那句为准。": "Your degree of attunement falls in the deepest tier; the table's wording here leans toward smoothness - read the whole passage as tenor, yet whichever aspect itself notes effort still stands by its own sentence.",
        "你这一份相契度属和合互补，表的措辞在这一档以合为主而留着余地，不必拿单独一条相位的短处重估全盘，也不必让这一档替这段关系作保。": "Your attunement is one of harmony and complementarity; the table's wording stresses union while leaving room - no need to rejudge the whole by a single aspect's shortcoming, nor to let this tier vouch for the relationship.",
        "你这一份相契度落在中和可处，表的措辞在这一档是平的，顺与费劲两边都读得进去，轻重由那几条相位自己说，不由这个档位替你定。": "Your attunement falls in a balanced, workable middle; the table's wording here is even, and both the smooth and the effortful sides read true - the weight is told by those aspects themselves, not set for you by this tier.",
        "你这一份相契度偏磨合为宜，表的措辞在这一档偏重费劲的那一面，它讲配置的次序，不讲这段关系该不该继续。": "Your attunement leans toward grinding into step; the table's wording here stresses the effortful side. It speaks of the order of the configuration, not of whether this relationship should continue.",
        "把这一卦按体、用两侧各读一遍：先说体用之间的生克，再顺着你这一侧的取象与卦气，然后是对方那一侧的，两侧同为一卦时只说一遍。": "Read this hexagram once on each side, Ti and Yong: first the generation and restraint between them, then the imagery and hexagram-qi on your side, then on the other's; when both sides are the same hexagram, it is said only once.",
        "合起来读，你这一卦的指数落在最上的一档，表的措辞在这一档最顺，读时以这一卦的整体气象为主，条目里若还写着费力的那几句，它们不因这一档消失。": "Read together, the index of your hexagram falls in the highest tier, where the table's wording is at its smoothest; read it with the hexagram's overall tenor as the frame, yet any effortful lines left in the entries do not vanish because of this tier.",
        "合起来读，你这一卦属吉的一档，表的措辞在这一档偏向顺，条目里若写着吃力，不拿它反推这一档，也不拿这一档抹掉它。": "Read together, your hexagram belongs to the auspicious tier, where the wording leans toward smoothness; if an entry notes strain, do not use it to overturn the tier, nor use the tier to erase it.",
        "合起来读，你这一卦是小吉，表的措辞在这一档是成而有限度，你读到的顺带着边界，与上吉那一档差的是力度不是方向。": "Read together, your hexagram is minor fortune; the table's wording here is success-with-limits - the smoothness you read comes with a boundary, and it differs from the supreme-fortune tier in force, not direction.",
        "合起来读，你这一卦落在中平，表的措辞在这一档不给你取向，顺与吃力都按条目自己那句读，这一档不替你判哪一边更重。": "Read together, your hexagram falls in even-plain; the wording here gives you no lean - smooth and strained alike are read by each entry's own line, and this tier does not judge for you which side weighs more.",
        "合起来读，你这一卦偏小凶，表的措辞在这一档偏重吃力的一面，它说的是这一卦当前的气象，不是对这件事的永久判词。": "Read together, your hexagram leans toward minor misfortune; the wording here stresses the strained side. It speaks of the hexagram's present tenor, not a permanent verdict on the matter.",
        "合起来读，你这一卦落在凶这一档，表的措辞在这一档最硬，读它时把它当作这一卦当前的阻力分布，不是说这件事永远不行。": "Read together, your hexagram falls in the misfortune tier, where the wording is at its hardest; read it as the hexagram's present distribution of resistance, not as saying the matter can never work.",
        "命宫这一格讲的是你这个人本身，你的底色、脾气与做事的起手式都先看这里。": "The Life Palace cell is about you yourself - your base tone, temperament, and the way you begin things all start with a reading here.",
        "兄弟宫这一格讲的是你和同辈手足之间的来往，也包括一路同行的伙伴。": "The Siblings Palace cell reads your dealings with same-generation kin, and it includes the companions who walk the road with you.",
        "夫妻宫这一格讲的是你和伴侣相处的方式，感情落到婚姻上的那份质感在这里看。": "The Spouse Palace cell reads how you and your partner get along; the texture your feelings take when they land in marriage is seen here.",
        "子女宫这一格讲的是你和子女、晚辈之间的缘分与相处方式。": "The Children Palace cell reads the bond and the way you relate to children and the younger generation.",
        "财帛宫这一格讲的是你怎么挣钱与用钱，钱财进出的格局在这里看。": "The Wealth Palace cell reads how you earn and spend; the pattern of money flowing in and out is seen here.",
        "疾厄宫这一格讲的是你身体素质的倾向，也就是盘上认为你更容易积累负荷的地方。": "The Illness Palace cell reads the tendency of your physical constitution - the places the chart thinks you are likelier to accumulate strain.",
        "迁移宫这一格讲的是你离开熟悉环境之后怎么被外界接住，出门在外的际遇在这里看。": "The Travel Palace cell reads how the outside world receives you once you leave familiar ground; the fortunes of being away from home are seen here.",
        "仆役宫这一格讲的是你和下属、朋友、合作方之间谁在为你出力。": "The Servants Palace cell reads, among your subordinates, friends, and partners, who is actually exerting themselves for you.",
        "官禄宫这一格讲的是你在事业这条路上的格局，做事的路子与能被看见的成果都看这里。": "The Career Palace cell reads the pattern of your road through work - how you get things done and the results others can see are both read here.",
        "田宅宫这一格讲的是你和家宅田产的关系，你安身的那个地方是什么样子。": "The Property Palace cell reads your relation to home and land - what the place where you settle yourself looks like.",
        "福德宫这一格讲的是你内在的享受与精神生活的质地，心里安不安稳在这里看。": "The Fortune-Virtue Palace cell reads your inner enjoyment and the texture of your spiritual life; whether your heart feels steady is seen here.",
        "父母宫这一格讲的是你和父母长辈的缘分与相处，也讲到你能从长辈那里接住多少庇护。": "The Parents Palace cell reads your bond and dealings with parents and elders, and how much shelter you can receive from them.",
        "巽四宫在盘上占东南一角，卦名巽、五行属木，地支管辰巳，你在这格看到的组合都归东南这个方位。": "The Xun (4th) Palace holds the southeast corner of the chart: hexagram Xun, element Wood, earthly branches Chen and Si under its charge - every combination you see in this cell belongs to the southeast.",
        "离九宫在正南，卦名离、属火，地支为午，你在这一格读到的是南面那一片天地怎么落子。": "The Li (9th) Palace sits due south: hexagram Li, element Fire, branch Wu - what you read in this cell is how that southern stretch of sky and ground plays its pieces.",
        "坤二宫在西南，卦名坤、属土，地支管未申，天禽也寄在这一格，你读到的是西南这一方的布置。": "The Kun (2nd) Palace lies southwest: hexagram Kun, element Earth, branches Wei and Shen, and the star Tianqin also lodges here - what you read is the arrangement of the southwest quarter.",
        "震三宫在正东，卦名震、属木，地支为卯，你在这一格看到的是东面这一方的动静。": "The Zhen (3rd) Palace lies due east: hexagram Zhen, element Wood, branch Mao - what you see in this cell is the stir of the eastern quarter.",
        "中五宫落在盘的正中央，卦名写作中、属土，按这派安法它不坐星、不配门也不配神，你在盘上看到的是这一格被留空。": "The Center (5th) Palace falls at the chart's very middle: its hexagram is written Center, element Earth; by this school's placement it seats no star, is matched with no door and no deity - so what you see on the chart is this cell left blank.",
        "兑七宫在正西，卦名兑、属金，地支为酉，你在这一格读到的是西面这一方的布置。": "The Dui (7th) Palace lies due west: hexagram Dui, element Metal, branch You - what you read in this cell is the arrangement of the western quarter.",
        "艮八宫在东北，卦名艮、属土，地支管丑寅，你读到的是东北这一方的安排。": "The Gen (8th) Palace lies northeast: hexagram Gen, element Earth, branches Chou and Yin - what you read is the arrangement of the northeast quarter.",
        "坎一宫在正北，卦名坎、属水，地支为子，你在这一格看到的是北面这一方的动静与去处。": "The Kan (1st) Palace lies due north: hexagram Kan, element Water, branch Zi - what you see in this cell is the stir and the going-forth of the northern quarter.",
        "乾六宫在西北，卦名乾、属金，地支管戌亥，你在这一格读到的是西北这一方的格局。": "The Qian (6th) Palace lies northwest: hexagram Qian, element Metal, branches Xu and Hai - what you read in this cell is the pattern of the northwest quarter.",
        "这一盘只发单张牌，你读的是它给出的一句话提点，不必往前后找搭配。": "This spread deals a single card: you read the one line of guidance it gives, with no need to look before or after for pairings.",
        "三张线性是把三张牌读成一句话，前一张是主词、后一张给它添形容，你按位置一路往下走。": "The Three-Card Line reads three cards as one sentence: the first is the subject, the next adds its description - follow the positions straight along.",
        "五行线阵是一条时间线，中间那张是你的核心现状，左边两张讲来路，右边两张讲去处。": "The Five-Element Line is a timeline: the middle card is your core present, the two on the left tell where you came from, the two on the right tell where you are heading.",
        "九宫阵把牌摆成三乘三，中心是你的核心，四周八格是环绕它的影响，读中心与每一方的搭配。": "The Nine-Palace Spread lays cards in three-by-three: the center is your core, the eight cells around it are the influences encircling it - read the center against each quarter's pairing.",
        "大桌把三十六张牌全铺开，以你的指示牌为中心，看它同行前后与同列上下，读的是整张盘的俯瞰。": "The Grand Tableau spreads all thirty-six cards, with your significator at the center: look at what shares its row before and after and its column above and below - you read an overview of the whole board.",
        "先说十颗星各自落在哪个星座，这一段讲的是你那十股力气各自习惯用什么方式出手。": "First, which constellation each of the ten stars sits in: this passage tells how each of your ten forces is in the habit of making its move.",
        "再说十颗星各自落在第几宫，宫位是舞台，这一段说的是你的这些力气主要在生活中哪一块使上劲。": "Next, which house each of the ten stars sits in - the house is the stage: this passage says in which area of life these forces chiefly exert themselves.",
        "接着看星与星之间成的相位，相位是你盘上几股力气之间的实际关系，这一段逐条说它们怎么配合或怎么拉扯。": "Then the aspects formed between stars: an aspect is the actual relation among several forces in your chart - this passage tells, line by line, how they cooperate or tug against each other.",
        "这张盘上十颗星之间没有达到经典容许度的主要相位，这一段今天没有可逐条说的关系句，落座与落宫仍是你盘的事实。": "On this chart no major aspect among the ten stars reaches the classic orb, so today this passage has no relation-lines to state item by item; the signs and houses are still the facts of your chart.",
        "再看逆行，逆行只说明从地球上看这颗星在往回走，它给你的是一种反复、内转的节奏，不是残缺。": "Then retrograde: retrograde only means that, seen from Earth, this star appears to move backward. It gives you a rhythm of revisiting and turning inward, not a deficiency.",
        "十颗行星在你盘上都不逆行，这一段没有要逐条解释的逆行节奏，你的十股力气都是直接朝外用的。": "None of the ten planets is retrograde in your chart, so this passage has no retrograde rhythm to explain item by item; your ten forces are all directed straight outward.",
        "上升与天顶是你这张盘立起来的两根轴，一个是对外的入口，一个是对上的方向。": "The Ascendant and the Midheaven are the two axes your chart stands on: one is your entry to the outside, the other your direction upward.",
        "北交点在盘上只有一个点，传统把它读作你后半程要往那边走的方向，这里按它落的座与宫逐条说。": "The North Node is a single point in the chart; tradition reads it as the direction you are to move toward in the second half of the road, and here it is told line by line by the sign and house it falls in.",
        "十二宫各管生活中的一块，这一段按宫序把十二块各自管什么说清楚，好让你读前面那些落宫时有对照。": "The twelve houses each govern an area of life; in house order this passage makes clear what each of the twelve governs, so you have a reference when reading the house placements above.",
        "最后是四元素与三形态在你这十颗星上的分布，它说的是整张盘的底色偏向哪一种运作方式，不是缺了什么。": "At last, the distribution of the four elements and three modalities across your ten stars: it tells which way of operating the whole chart's tone leans toward, not what is missing.",
        "先说行运这一层：目标日那天的十颗星此刻压在你本命盘的哪些点上，下面逐条说的是那一天哪股力气被外面的天带动。": "First the transit layer: on the target day, which points of your natal chart the ten stars are pressing on right now - what follows tells, line by line, which of your forces is stirred by the sky outside on that day.",
        "行运这一层在目标日没有任何一条达到经典容许度的相位，这一段没有可逐条说的话，你本命盘的落座与宫位仍是它的事实。": "The transit layer forms no aspect reaching the classic orb on the target day, so this passage has nothing to say line by item; the signs and houses of your natal chart remain its facts.",
        "再看次限这一层，它看的是把出生后的一天当一年推出来的那张盘，下面逐条说的是这张盘上的星与你的本命点成什么相。": "Then the secondary-direction layer: it reads the chart derived by counting one day after birth as one year - what follows tells, line by line, what aspects this chart's stars make with your natal points.",
        "次限这一层在目标日没有达到经典容许度的相位，这一段没有可逐条说的关系句，你推运盘上的落座与宫位仍是它的事实。": "The secondary-direction layer reaches no classic-orb aspect on the target day, so this passage has no relation-lines to state item by item; the signs and houses in your progressed chart remain its facts.",
        "太阳弧这一层把你本命每一颗星往前推同一段弧度，它说的是推前之后的那张盘与本命的关系，读的时候要连着前两段一起看。": "The solar-arc layer advances every natal star by the same arc: it speaks of the relation between the chart after that advance and your natal chart, so read it together with the two passages before it.",
        "太阳弧这一层在目标日没有达到经典容许度的相位，这一段没有可逐条说的话，你本命每一颗星被推进同一段弧度这件事仍是事实。": "The solar-arc layer reaches no classic-orb aspect on the target day, so this passage has nothing to say line by item; that every natal star has been advanced by the same arc is still a fact.",
        "次限的月亮是这张推运盘上最好读的一格，它在星座与你的本命宫之间慢慢挪，走到哪一格，生活里哪一块就近了些。": "The progressed Moon is the easiest cell to read on this chart: it drifts slowly among the signs and your natal houses, and whichever cell it reaches, that area of life comes a little closer.",
        "次限上升与次限天顶是你推运盘的两根轴，它们不由出生时刻锁死，会随年月一点点挪，这两格讲的是方向上的变化。": "The progressed Ascendant and progressed Midheaven are the two axes of your progressed chart: not locked by the moment of birth, they shift bit by bit with the years - these two cells tell of changes in direction.",
        "先说九曜落座这一层：九颗星各自停在哪个星座，决定了它们把你的力气往哪一处使，下面逐颗说的是你可以先认下的底色。": "First the layer of the nine grahas by sign: which constellation each of the nine stars rests in decides where each puts your force; what follows speaks star by star of the base tone you can first take in.",
        "再看九曜落宫这一层：整宫制把十二个星座依次安在十二个宫位上，星落在第几宫，说的就是它在你的生活里偏向哪一块。": "Then the nine grahas by house: the whole-sign system sets the twelve constellations in turn into the twelve houses, and which house a star falls in tells which area of your life it leans toward.",
        "最后看星宿这一层：九曜与上升各自落在二十七宿的哪一宿，下面把这些宿的底色逐条说给你听，同一宿只讲一次。": "At last the nakshatra layer: which of the twenty-seven mansions each of the nine grahas and the Ascendant falls in - their base tones are told to you line by line below, each mansion spoken only once.",
        "最后看现行的大运与小运：两层主星各自带着一段时期的底色，下面把这两颗主事星各说一句，你可以对着上面的时间轴读。": "At last the current major and minor periods: the ruling stars of the two layers each carry the tone of a span of time; the two presiding stars are each given one line below, and you can read them against the timeline above.",
        "目标日已经落在这一百二十年的运程之外，这张盘的时间轴没有当下正在走的大运与小运，这一段就没有可说的主事星，你仍可以按上面的顺序回看每一段。": "The target day already falls outside this one-hundred-and-twenty-year cycle of periods; the chart's timeline has no major or minor period being walked right now, so this passage has no presiding star to speak of, yet you can still review each span in the order above.",
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


def _localize_leaf(value: str, table: dict[str, str]) -> str:
    """字符串叶子的本地化：整串命中优先；未命中且含换行则逐行精确查表后拼回。

    合成段落（`plain_compose.compose` 以 `\n` 连接开篇句 / 条目 / 收尾句）作为一个叶子出现，
    整串不可能是固定 key；行级仍是**整行精确匹配**（一行必须逐字等于某个 key），不是子串替换，
    所以机制规矩 ② 不变。没有任何一行命中时原样返回——保证未登记的段落一个字节都不动。
    """
    hit = table.get(value)
    if hit is not None:
        return hit
    if "\n" in value:
        lines = value.split("\n")
        mapped = [table.get(line, line) for line in lines]
        if mapped != lines:
            return "\n".join(mapped)
    return value


def localize(value: Any, locale: str) -> Any:
    """递归遍历已序列化的 JSON 载荷，对每个字符串叶子做精确查表替换（整串→行级回退）。

    结构（dict/list 的键与形状、数字、布尔、null）一概不动，只换字符串叶子的值——所以
    snake_case 契约（AGENTS §3）与字段名不受影响，前端照旧原样消费。`table` 为空（`zh-Hans` /
    未知 locale）时直接透传，绝不进入替换路径。
    """
    table = LABELS.get(locale)
    if not table:
        return value
    if isinstance(value, str):
        return _localize_leaf(value, table)
    if isinstance(value, dict):
        return {k: localize(v, locale) for k, v in value.items()}
    if isinstance(value, list):
        return [localize(v, locale) for v in value]
    return value
