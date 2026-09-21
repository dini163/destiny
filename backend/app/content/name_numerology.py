"""熊崎氏八十一数理吉凶表 —— 姓名学的唯一断语来源。

录入流程（spec §5.3 铁律）：三份互相独立的公开整理稿逐行比对，分歧保留在注释里，
不静默取其一；表里出现的每一个字都是某份公开资料印过的字。本模块之外不得再有数理
断语；引擎只 `numerology_entry(n)` 取句子，绝不自己组句子。

三份稿子分两个词汇体系：

* 粗分稿（"暗示意义"十六字韵文）：美篇 52fqveoz（s1）、美篇 4mlii8p2（t5）、
  搜狐 680728521（s5）三站正文逐行一致，算一份，档位只有 `吉 / 半吉 / 凶` 三级。
* 细分稿（"一句话数 + 基业/家庭/健康/含义"）：GitHub cnk3x/bys（gh）、
  GPL 的 R 包 hongyuanjia/wuge 附带的 shuli.csv（wu），档位有 `大吉 / 吉 / 半吉 /
  凶 / 大凶 / 半吉半凶`。

档位词汇取自 `design/姓名学五格剖象/code.html` 已印出的四级（大吉 / 吉 / 半吉 / 凶），
细分稿的多出档位按下面这张表归并，被归并过的行在 `source` 里带"档位归并"字样：

  大凶 → 凶；半吉半凶 → 凶（都取保守一侧；粗分稿本就把这两档印成"凶"）
  粗分稿的"吉"是 大吉 与 吉 两档的合并桶，所以细分两稿同判 大吉 时不与之冲突

取值规则：格局名与十六字断语抄粗分稿（三站互证；gh 稿有字体反爬，把 61 的
"牡丹芙蓉" 印成了 "牡凡寿蓉"，可见其正文不可靠，只用作档位比对）；档位取细分两稿
中保守的一方，两稿一致即照抄。分歧不静默：每行的三份稿子各是什么档位都记在行尾
注释里，`source` 里再带上浓缩过的标记 —— "取保守" 是细分两稿分歧，"粗分稿作「X」"
是粗分稿与最终档位不同桶。全表 81 行无一行只有一个证人，也无一行出现吉/凶极性翻转；
细分两稿分歧的 20 行为 6 17 18 21 23 24 25 27 29 30 33 35 39 48 49 50 52 55 57 78。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

#: 书级出处：说清它是"通行表整理"，不是古籍原文。
NUMEROLOGY_SOURCE = "熊崎氏姓名学八十一数理（通行表整理，非古籍）"


class NameFortune(str, Enum):
    """吉凶等级；只允许设计稿印出的四级。"""

    DAJI = "大吉"
    JI = "吉"
    BANJI = "半吉"
    XIONG = "凶"


#: 枚举的唯一镜像，供测试与 UI 使用，防两处漂移。
FORTUNE_LEVELS: tuple[str, ...] = tuple(member.value for member in NameFortune)


@dataclass(frozen=True)
class NumerologyEntry:
    number: int
    fortune: str
    pattern_name: str
    verdict: str
    source: str


def _entry(
    number: int,
    fortune: NameFortune,
    pattern_name: str,
    verdict: str,
    note: str = "",
) -> NumerologyEntry:
    return NumerologyEntry(
        number=number,
        fortune=fortune.value,
        pattern_name=pattern_name,
        verdict=verdict,
        source=f"{NUMEROLOGY_SOURCE}·数理{number}{note}",
    )


NUMBERS: dict[int, NumerologyEntry] = {
# gh=cnk3x/bys=大吉 wu=R包wuge=大吉 粗=美篇x2+搜狐=吉，gh 别名「宇宙起源:」
        1: _entry(1, NameFortune.DAJI, '太极之数', '太极之数，万物开泰，生发无穷，利禄亨通', '·'),
# gh=cnk3x/bys=大凶 wu=R包wuge=大凶 粗=美篇x2+搜狐=凶，gh 别名「一身孤节」
        2: _entry(2, NameFortune.XIONG, '两仪之数', '两仪之数，混沌未开，进退保守，志望难达', '·档位归并大凶→凶'),
# gh=cnk3x/bys=大吉 wu=R包wuge=大吉 粗=美篇x2+搜狐=吉，gh 别名「吉祥」
        3: _entry(3, NameFortune.DAJI, '三才之数', '三才之数，天地人和，大事大业，繁荣昌隆', '·'),
# gh=cnk3x/bys=凶 wu=R包wuge=凶 粗=美篇x2+搜狐=凶，gh 别名「凶变」
        4: _entry(4, NameFortune.XIONG, '四象之数', '四象之数，待于生发，万事慎重，不具营谋', '·'),
# gh=cnk3x/bys=大吉 wu=R包wuge=大吉 粗=美篇x2+搜狐=吉，gh 别名「种竹成林」
        5: _entry(5, NameFortune.DAJI, '五行之数', '五行俱权，循环相生，圆通畅达，福祉无穷', '·'),
# gh=cnk3x/bys=大吉 wu=R包wuge=半吉 粗=美篇x2+搜狐=吉，gh 别名「安稳」
        6: _entry(6, NameFortune.BANJI, '六爻之数', '六爻之数，发展变化，天赋美德，吉祥安泰', '·gh=cnk3x/bys=大吉/wu=R包wuge=半吉 取保守·粗分稿作「吉」'),
# gh=cnk3x/bys=吉 wu=R包wuge=吉 粗=美篇x2+搜狐=吉，gh 别名「精悍」
        7: _entry(7, NameFortune.JI, '七政之数', '七政之数，精悍严谨，天赋之力，吉星照耀', '·'),
# gh=cnk3x/bys=吉 wu=R包wuge=吉 粗=美篇x2+搜狐=半吉，gh 别名「坚刚」
        8: _entry(8, NameFortune.JI, '八卦之数', '八卦之数，乾坎艮震，巽离坤兑，无穷无尽', '·粗分稿作「半吉」'),
# gh=cnk3x/bys=凶 wu=R包wuge=凶 粗=美篇x2+搜狐=凶，gh 别名「破舟进海」
        9: _entry(9, NameFortune.XIONG, '大成之数', '大成之数，蕴涵凶险，或成或败，难以把握', '·'),
# gh=cnk3x/bys=凶 wu=R包wuge=凶 粗=美篇x2+搜狐=凶，gh 别名「零暗」
        10: _entry(10, NameFortune.XIONG, '终结之数', '终结之数，雪暗飘零，偶或有成，回顾茫然', '·'),
# gh=cnk3x/bys=大吉 wu=R包wuge=大吉 粗=美篇x2+搜狐=吉，gh 别名「早苗逢雨」
        11: _entry(11, NameFortune.DAJI, '旱苗逢雨', '万物更新，调顺发达，恢弘泽世，繁荣富贵', '·'),
    12: _entry(12, NameFortune.XIONG, '掘井无泉', '无理之数，发展薄弱，虽生不足，难酬志向', '·'),  # gh=cnk3x/bys=凶 wu=R包wuge=凶 粗=美篇x2+搜狐=凶
# gh=cnk3x/bys=大吉 wu=R包wuge=大吉 粗=美篇x2+搜狐=吉，gh 别名「春阳牡丹」
        13: _entry(13, NameFortune.DAJI, '春日牡丹', '才艺多能，智谋奇略，忍柔当事，鸣奏大功', '·'),
    14: _entry(14, NameFortune.XIONG, '破兆', '家庭缘薄，孤独遭难，谋事不达，悲惨不测', '·'),  # gh=cnk3x/bys=凶 wu=R包wuge=凶 粗=美篇x2+搜狐=凶
    15: _entry(15, NameFortune.DAJI, '福寿', '福寿圆满，富贵荣誉，涵养雅量，德高望重', '·'),  # gh=cnk3x/bys=大吉 wu=R包wuge=大吉 粗=美篇x2+搜狐=吉
    16: _entry(16, NameFortune.DAJI, '厚重', '厚重载德，安富尊荣，财官双美，功成名就', '·'),  # gh=cnk3x/bys=大吉 wu=R包wuge=大吉 粗=美篇x2+搜狐=吉
# gh=cnk3x/bys=大吉 wu=R包wuge=半吉 粗=美篇x2+搜狐=半吉，gh 别名「坚操」
        17: _entry(17, NameFortune.BANJI, '刚强', '权威刚强，突破万难，如能容忍，必获成功', '·gh=cnk3x/bys=大吉/wu=R包wuge=半吉 取保守'),
# gh=cnk3x/bys=大吉 wu=R包wuge=吉 粗=美篇x2+搜狐=半吉
        18: _entry(18, NameFortune.JI, '铁镜重磨', '权威显达，博得名利，且养柔德，功成名就', '·gh=cnk3x/bys=大吉/wu=R包wuge=吉 取保守·粗分稿作「半吉」'),
    19: _entry(19, NameFortune.XIONG, '多难', '风云蔽日，辛苦重来，虽有智谋，万事挫折', '·'),  # gh=cnk3x/bys=凶 wu=R包wuge=凶 粗=美篇x2+搜狐=凶
    20: _entry(20, NameFortune.XIONG, '屋下藏金', '非业破运，灾难重重，进退维谷，万事难成', '·'),  # gh=cnk3x/bys=凶 wu=R包wuge=凶 粗=美篇x2+搜狐=凶
# gh=cnk3x/bys=大吉 wu=R包wuge=吉 粗=美篇x2+搜狐=吉
        21: _entry(21, NameFortune.JI, '明月中天', '光风霁月，万物确立，官运亨通，大搏名利。女性不宜此数', '·gh=cnk3x/bys=大吉/wu=R包wuge=吉 取保守'),
# gh=cnk3x/bys=凶 wu=R包wuge=凶 粗=美篇x2+搜狐=凶，gh 别名「秋草」
        22: _entry(22, NameFortune.XIONG, '秋草逢霜', '秋草逢霜，困难疾弱，虽出豪杰，人生波折', '·'),
# gh=cnk3x/bys=大吉 wu=R包wuge=吉 粗=美篇x2+搜狐=吉
        23: _entry(23, NameFortune.JI, '壮丽', '旭日东升，壮丽壮观，权威旺盛，功名荣达。女性不宜此数', '·gh=cnk3x/bys=大吉/wu=R包wuge=吉 取保守'),
# gh=cnk3x/bys=大吉 wu=R包wuge=吉 粗=美篇x2+搜狐=吉
        24: _entry(24, NameFortune.JI, '掘藏得金', '家门余庆，金钱丰盈，白手成家，财源广进', '·gh=cnk3x/bys=大吉/wu=R包wuge=吉 取保守'),
# gh=cnk3x/bys=大吉 wu=R包wuge=吉 粗=美篇x2+搜狐=半吉，gh 别名「英俊」
        25: _entry(25, NameFortune.JI, '荣俊', '资性英敏，才能奇特，克服傲慢，尚可成功', '·gh=cnk3x/bys=大吉/wu=R包wuge=吉 取保守·粗分稿作「半吉」'),
# gh=cnk3x/bys=半吉 wu=R包wuge=半吉 粗=美篇x2+搜狐=凶
        26: _entry(26, NameFortune.BANJI, '变怪', '变怪之谜，英雄豪杰，波澜重叠，而奏大功', '·粗分稿作「凶」'),
# gh=cnk3x/bys=凶 wu=R包wuge=半吉 粗=美篇x2+搜狐=凶
        27: _entry(27, NameFortune.XIONG, '增长', '欲望无止，自我强烈，多受毁谤，尚可成功', '·gh=cnk3x/bys=凶/wu=R包wuge=半吉 取保守'),
# gh=cnk3x/bys=凶 wu=R包wuge=凶 粗=美篇x2+搜狐=凶
        28: _entry(28, NameFortune.XIONG, '阔水浮萍', '遭难之数，豪杰气概，四海漂泊，终世浮躁。女性不宜此数', '·'),
# gh=cnk3x/bys=大吉 wu=R包wuge=半吉 粗=美篇x2+搜狐=吉，gh 别名「不平」
        29: _entry(29, NameFortune.BANJI, '智谋', '智谋优秀，财力归集，名闻海内，成就大业', '·gh=cnk3x/bys=大吉/wu=R包wuge=半吉 取保守·粗分稿作「吉」'),
# gh=cnk3x/bys=凶 wu=R包wuge=半吉 粗=美篇x2+搜狐=半吉
        30: _entry(30, NameFortune.XIONG, '非运', '沉浮不定，凶吉难变，若明若暗，大成大败', '·gh=cnk3x/bys=凶/wu=R包wuge=半吉 取保守·粗分稿作「半吉」'),
    31: _entry(31, NameFortune.DAJI, '春日花开', '智勇得志，博得名利，统领众人，繁荣富贵', '·'),  # gh=cnk3x/bys=大吉 wu=R包wuge=大吉 粗=美篇x2+搜狐=吉
    32: _entry(32, NameFortune.DAJI, '宝马金鞍', '侥幸多望，贵人得助，财帛如裕，繁荣至上', '·'),  # gh=cnk3x/bys=大吉 wu=R包wuge=大吉 粗=美篇x2+搜狐=吉
# gh=cnk3x/bys=大吉 wu=R包wuge=吉 粗=美篇x2+搜狐=吉，gh 别名「升天」
        33: _entry(33, NameFortune.JI, '旭日升天', '旭日升天，鸾凤相会，名闻天下，隆昌至极。女性不宜此数', '·gh=cnk3x/bys=大吉/wu=R包wuge=吉 取保守'),
# gh=cnk3x/bys=凶 wu=R包wuge=凶 粗=美篇x2+搜狐=凶，gh 别名「破字」
        34: _entry(34, NameFortune.XIONG, '破家', '破家之身，见识短小，辛苦遭逢，灾祸至极', '·'),
# gh=cnk3x/bys=大吉 wu=R包wuge=吉 粗=美篇x2+搜狐=吉
        35: _entry(35, NameFortune.JI, '高楼望月', '温和平静，智达通畅，文昌技艺，奏功洋洋', '·gh=cnk3x/bys=大吉/wu=R包wuge=吉 取保守'),
# gh=cnk3x/bys=凶 wu=R包wuge=凶 粗=美篇x2+搜狐=半吉，gh 别名「波澜」
        36: _entry(36, NameFortune.XIONG, '波澜重叠', '波澜重叠，沉浮万状，侠肝义胆，舍己成仁', '·粗分稿作「半吉」'),
# gh=cnk3x/bys=大吉 wu=R包wuge=大吉 粗=美篇x2+搜狐=吉，gh 别名「猛虎下山」
        37: _entry(37, NameFortune.DAJI, '猛虎出林', '权威显达，热诚忠信，宜着雅量，终身荣富', '·'),
# gh=cnk3x/bys=半吉 wu=R包wuge=半吉 粗=美篇x2+搜狐=半吉
        38: _entry(38, NameFortune.BANJI, '磨铁成针', '意志薄弱，刻意经营，才识不凡，技艺有成', '·'),
# gh=cnk3x/bys=大吉 wu=R包wuge=吉 粗=美篇x2+搜狐=半吉，gh 别名「富贵」
        39: _entry(39, NameFortune.JI, '富贵荣华', '富贵荣华，财帛丰盈，暗藏险象，德泽四方', '·gh=cnk3x/bys=大吉/wu=R包wuge=吉 取保守·粗分稿作「半吉」'),
    40: _entry(40, NameFortune.XIONG, '退安', '智谋胆力，冒险投机，沉浮不定，退保平安', '·'),  # gh=cnk3x/bys=凶 wu=R包wuge=凶 粗=美篇x2+搜狐=凶
# gh=cnk3x/bys=大吉 wu=R包wuge=大吉 粗=美篇x2+搜狐=吉
        41: _entry(41, NameFortune.DAJI, '有德', '纯阳独秀，德高望重，和顺畅达，博得名利。此数为最大好运数', '·'),
    42: _entry(42, NameFortune.XIONG, '寒蝉在柳', '博识多能，精通世情，如能专心，尚可成功', '·'),  # gh=cnk3x/bys=凶 wu=R包wuge=凶 粗=美篇x2+搜狐=凶
# gh=cnk3x/bys=凶 wu=R包wuge=凶 粗=美篇x2+搜狐=凶，gh 别名「散财」
        43: _entry(43, NameFortune.XIONG, '散财破产', '散财破产，诸事不遂，虽有智谋，财来财去', '·'),
    44: _entry(44, NameFortune.XIONG, '烦闷', '破家亡身，暗藏惨淡，事不如意，乱世怪杰', '·'),  # gh=cnk3x/bys=凶 wu=R包wuge=凶 粗=美篇x2+搜狐=凶
# gh=cnk3x/bys=大吉 wu=R包wuge=大吉 粗=美篇x2+搜狐=吉，gh 别名「顽风」
        45: _entry(45, NameFortune.DAJI, '顺风', '新生泰和，顺风扬帆，智谋经纬，富贵繁荣', '·'),
    46: _entry(46, NameFortune.XIONG, '浪里淘金', '载宝沉舟，浪里淘金，大难尝尽，大功有成', '·'),  # gh=cnk3x/bys=凶 wu=R包wuge=凶 粗=美篇x2+搜狐=凶
    47: _entry(47, NameFortune.DAJI, '点石成金', '花开之象，万事如意，祯祥吉庆，天赋幸福', '·'),  # gh=cnk3x/bys=大吉 wu=R包wuge=大吉 粗=美篇x2+搜狐=吉
# gh=cnk3x/bys=大吉 wu=R包wuge=吉 粗=美篇x2+搜狐=吉
        48: _entry(48, NameFortune.JI, '古松立鹤', '智谋兼备，德量荣达，威望成师，洋洋大观', '·gh=cnk3x/bys=大吉/wu=R包wuge=吉 取保守'),
# gh=cnk3x/bys=凶 wu=R包wuge=半吉 粗=美篇x2+搜狐=半吉
        49: _entry(49, NameFortune.XIONG, '转变', '吉临则吉，凶来则凶，转凶为吉，配好三才', '·gh=cnk3x/bys=凶/wu=R包wuge=半吉 取保守·粗分稿作「半吉」'),
# gh=cnk3x/bys=半吉半凶 wu=R包wuge=凶 粗=美篇x2+搜狐=半吉，gh 别名「小舟进海」
        50: _entry(50, NameFortune.XIONG, '小舟入海', '一成一败，吉凶参半，先得庇荫，后遭凄惨', '·gh=cnk3x/bys=半吉半凶/wu=R包wuge=凶 取保守·档位归并半吉半凶→凶·粗分稿作「半吉」'),
    51: _entry(51, NameFortune.BANJI, '沉浮', '盛衰交加，波澜重叠，如能慎始，必获成功', '·'),  # gh=cnk3x/bys=半吉 wu=R包wuge=半吉 粗=美篇x2+搜狐=半吉
# gh=cnk3x/bys=大吉 wu=R包wuge=吉 粗=美篇x2+搜狐=吉
        52: _entry(52, NameFortune.JI, '达眼', '卓识达眼，先见之明，智谋超群，名利双收', '·gh=cnk3x/bys=大吉/wu=R包wuge=吉 取保守'),
    53: _entry(53, NameFortune.XIONG, '曲卷难星', '外祥内患，外祸内安，先富后贫，先贫后富', '·'),  # gh=cnk3x/bys=凶 wu=R包wuge=凶 粗=美篇x2+搜狐=凶
# gh=cnk3x/bys=凶 wu=R包wuge=凶 粗=美篇x2+搜狐=凶，gh 别名「石上灾花」
        54: _entry(54, NameFortune.XIONG, '石上栽花', '石上栽花，难得有活，忧闷烦来，辛惨不绝', '·'),
# gh=cnk3x/bys=凶 wu=R包wuge=半吉 粗=美篇x2+搜狐=半吉
        55: _entry(55, NameFortune.XIONG, '善恶', '善善得恶，恶恶得善，吉到极限，反生凶险', '·gh=cnk3x/bys=凶/wu=R包wuge=半吉 取保守·粗分稿作「半吉」'),
# gh=cnk3x/bys=凶 wu=R包wuge=凶 粗=美篇x2+搜狐=凶，gh 别名「海里行舟」
        56: _entry(56, NameFortune.XIONG, '浪里行舟', '历尽艰辛，四周障碍，万事龃龌，做事难成', '·'),
# gh=cnk3x/bys=大吉 wu=R包wuge=吉 粗=美篇x2+搜狐=吉
        57: _entry(57, NameFortune.JI, '日照春松', '寒雪青松，夜莺吟春，必遭一过，繁荣白事', '·gh=cnk3x/bys=大吉/wu=R包wuge=吉 取保守'),
# gh=cnk3x/bys=半吉 wu=R包wuge=半吉 粗=美篇x2+搜狐=半吉，gh 别名「晚行碰月」
        58: _entry(58, NameFortune.BANJI, '晚行遇月', '沉浮多端，先苦后甜，宽宏扬名，富贵繁荣', '·'),
    59: _entry(59, NameFortune.XIONG, '寒蝉悲风', '寒蝉悲风，意志衰退，缺乏忍耐，苦难不休', '·'),  # gh=cnk3x/bys=凶 wu=R包wuge=凶 粗=美篇x2+搜狐=凶
    60: _entry(60, NameFortune.XIONG, '无谋', '无谋之人，漂泊不定，晦暝暗黑，动摇不安', '·'),  # gh=cnk3x/bys=凶 wu=R包wuge=凶 粗=美篇x2+搜狐=凶
# gh=cnk3x/bys=大吉 wu=R包wuge=大吉 粗=美篇x2+搜狐=吉，gh 别名「牡凡寿蓉」
        61: _entry(61, NameFortune.DAJI, '牡丹芙蓉', '牡丹芙蓉，花开富贵，名利双收，定享天赋', '·'),
# gh=cnk3x/bys=凶 wu=R包wuge=凶 粗=美篇x2+搜狐=凶，gh 别名「表败」
        62: _entry(62, NameFortune.XIONG, '衰败', '衰败之象，内外不和，志望难达，灾祸频来', '·'),
    63: _entry(63, NameFortune.DAJI, '舟归平海', '富贵荣华，身心安泰，雨露惠泽，万事亨通', '·'),  # gh=cnk3x/bys=大吉 wu=R包wuge=大吉 粗=美篇x2+搜狐=吉
    64: _entry(64, NameFortune.XIONG, '非命', '骨肉分离，孤独悲愁，难得心安，做事不成', '·'),  # gh=cnk3x/bys=凶 wu=R包wuge=凶 粗=美篇x2+搜狐=凶
# gh=cnk3x/bys=大吉 wu=R包wuge=大吉 粗=美篇x2+搜狐=吉，gh 别名「大流归海」
        65: _entry(65, NameFortune.DAJI, '巨流归海', '天长地久，家运隆昌，福寿绵长，事事成就', '·'),
    66: _entry(66, NameFortune.XIONG, '岩头步马', '进退维谷，艰难不堪，等待时机，一跃而起', '·'),  # gh=cnk3x/bys=凶 wu=R包wuge=凶 粗=美篇x2+搜狐=凶
# gh=cnk3x/bys=大吉 wu=R包wuge=大吉 粗=美篇x2+搜狐=吉，gh 别名「通达」
        67: _entry(67, NameFortune.DAJI, '顺风通达', '天赋幸运，四通八达，家道繁昌，富贵东来', '·'),
    68: _entry(68, NameFortune.DAJI, '顺风吹帆', '智虑周密，集众信达，发明能智，拓展昂进', '·'),  # gh=cnk3x/bys=大吉 wu=R包wuge=大吉 粗=美篇x2+搜狐=吉
    69: _entry(69, NameFortune.XIONG, '非业', '非业非力，精神迫滞，灾害交至，遍偿痛苦', '·'),  # gh=cnk3x/bys=凶 wu=R包wuge=凶 粗=美篇x2+搜狐=凶
    70: _entry(70, NameFortune.XIONG, '残菊逢霜', '残菊逢霜，寂寞无碍，惨淡忧愁，晚景凄凉', '·'),  # gh=cnk3x/bys=凶 wu=R包wuge=凶 粗=美篇x2+搜狐=凶
# gh=cnk3x/bys=半吉 wu=R包wuge=半吉 粗=美篇x2+搜狐=半吉
        71: _entry(71, NameFortune.BANJI, '石上金花', '石上金花，内心劳苦，贯彻始终，定可昌隆', '·'),
# gh=cnk3x/bys=凶 wu=R包wuge=凶 粗=美篇x2+搜狐=半吉
        72: _entry(72, NameFortune.XIONG, '劳苦', '荣苦相伴，阴云覆月，外表吉祥，内实凶祸', '·粗分稿作「半吉」'),
# gh=cnk3x/bys=半吉 wu=R包wuge=半吉 粗=美篇x2+搜狐=半吉，gh 别名「无难」
        73: _entry(73, NameFortune.BANJI, '无勇', '盛衰交加，徒有高志，天王福祉，终世平安', '·'),
    74: _entry(74, NameFortune.XIONG, '残菊经霜', '残菊经霜，秋叶寂寞，无能无智，辛苦繁多', '·'),  # gh=cnk3x/bys=凶 wu=R包wuge=凶 粗=美篇x2+搜狐=凶
# gh=cnk3x/bys=半吉 wu=R包wuge=半吉 粗=美篇x2+搜狐=凶
        75: _entry(75, NameFortune.BANJI, '退守', '退守保吉，发迹甚迟，虽有吉象，无谋难成', '·粗分稿作「凶」'),
    76: _entry(76, NameFortune.XIONG, '离散', '倾覆离散，骨肉分离，内外不和，虽劳无功', '·'),  # gh=cnk3x/bys=凶 wu=R包wuge=凶 粗=美篇x2+搜狐=凶
    77: _entry(77, NameFortune.BANJI, '半吉', '家庭有悦，半吉半凶，能获援护，陷落不幸', '·'),  # gh=cnk3x/bys=半吉 wu=R包wuge=半吉 粗=美篇x2+搜狐=半吉
# gh=cnk3x/bys=半吉 wu=R包wuge=凶 粗=美篇x2+搜狐=凶，gh 别名「无若」
        78: _entry(78, NameFortune.XIONG, '晚苦', '祸福参半，先天智能，中年发达，晚景困苦', '·gh=cnk3x/bys=半吉/wu=R包wuge=凶 取保守'),
    79: _entry(79, NameFortune.XIONG, '云头望月', '云头望月，身疲力尽，穷迫不伸，精神不定', '·'),  # gh=cnk3x/bys=凶 wu=R包wuge=凶 粗=美篇x2+搜狐=凶
    80: _entry(80, NameFortune.XIONG, '遁吉', '辛苦不绝，早入隐遁，安心立命，化凶转吉', '·'),  # gh=cnk3x/bys=凶 wu=R包wuge=凶 粗=美篇x2+搜狐=凶
    81: _entry(81, NameFortune.DAJI, '万物回春', '最吉之数，还本归元，吉祥重叠，富贵尊荣', '·'),  # gh=cnk3x/bys=大吉 wu=R包wuge=大吉 粗=美篇x2+搜狐=吉
}


def numerology_entry(number: int) -> NumerologyEntry:
    """取一个数理的三件套；越界即错，循环归一在引擎里做，不在这里兜。"""
    try:
        return NUMBERS[number]
    except KeyError:
        raise KeyError(f"八十一数理表只覆盖 1..81，收到 {number}") from None
