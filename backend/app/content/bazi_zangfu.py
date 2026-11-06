"""八字子午流注与脏腑经络映射表（源自中医五行与子午流注养生体系）。

用于八字命理中根据四柱地支刑冲破害及五行偏亢偏衰，推断对应的脏腑、经络负荷及调养建议。
"""

from typing import Any
from app.content.ziwei_db.chart_tables import ZANGFU_DB

#: 地支配属脏腑经络（子午流注）
BRANCH_ZANGFU = ZANGFU_DB

#: 地支六冲对应的脏腑经络负荷警示
BRANCH_CLASH_ZANGFU: dict[str, dict[str, Any]] = {
    "子午冲": {
        "branches": ("子", "午"),
        "organs": ("胆", "心"),
        "meridians": ("足少阳胆经", "手少阴心经"),
        "focus": "水火相战，易波及心气、血液循环与胆气决断，需防心悸、睡眠不安与情绪虚惊。",
        "advice": "子时（23-1点）务必安卧养胆，午时（11-13点）宜小憩养心气，避免午夜熬夜及情绪过激。",
    },
    "丑未冲": {
        "branches": ("丑", "未"),
        "organs": ("肝", "小肠"),
        "meridians": ("足厥阴肝经", "手太阳小肠经"),
        "focus": "湿土与燥土相击，易波及脾胃纳运、小肠吸收与肝经疏泄，多见腹胀、消化失调或腹痛。",
        "advice": "丑时（1-3点）熟睡以利肝经藏血，未时（13-15点）后勿暴饮暴食，饮食宜温润清淡忌寒凉。",
    },
    "寅申冲": {
        "branches": ("寅", "申"),
        "organs": ("肺", "膀胱"),
        "meridians": ("手太阴肺经", "足太阳膀胱经"),
        "focus": "金木交战，气机升降受阻，易累及肺经呼吸系统、皮肤与膀胱水液代谢，亦须留意外伤筋骨。",
        "advice": "寅时（3-5点）气血流注肺经宜空气清新，申时（15-17点）多补充温水以助膀胱经代谢。",
    },
    "卯酉冲": {
        "branches": ("卯", "酉"),
        "organs": ("大肠", "肾"),
        "meridians": ("手阳明大肠经", "足少阴肾经"),
        "focus": "金木相克，易损及大肠传导与肾阴肾阳，常见腰膝酸软、下焦不固或肠道排泄不调。",
        "advice": "卯时（5-7点）起床规律饮温水助大肠排毒，酉时（17-19点）宜放松清淡进食，慎防过劳损肾。",
    },
    "辰戌冲": {
        "branches": ("辰", "戌"),
        "organs": ("胃", "心包"),
        "meridians": ("足阳明胃经", "手厥阴心包经"),
        "focus": "土气相撞，气血运化迟滞，易涉及胃气受纳与心包胸阳，多见胃脘胀闷、气滞或胸闷心烦。",
        "advice": "辰时（7-9点）务必吃好温热早餐充实胃经，戌时（19-21点）宜静心散步舒畅心包经气血。",
    },
    "巳亥冲": {
        "branches": ("巳", "亥"),
        "organs": ("脾", "三焦"),
        "meridians": ("足太阴脾经", "手少阳三焦经"),
        "focus": "水火相荡，易致脾阳虚弱与三焦水道不调，多见湿重倦怠、水液代谢运化迟滞或腹泻。",
        "advice": "巳时（9-11点）健脾助运，亥时（21-23点）宜安静调息准备入眠以利三焦调和百脉。",
    },
}


def get_bazi_zangfu_guidance(branches: list[str]) -> list[dict[str, Any]]:
    """根据八字四柱地支及地支六冲，推导经方子午流注对应的脏腑经络养生要点。"""
    branch_set = set(branches)
    results: list[dict[str, Any]] = []

    # 1. 检查地支六冲
    checked_clashes = set()
    for clash_name, data in BRANCH_CLASH_ZANGFU.items():
        b1, b2 = data["branches"]
        if b1 in branch_set and b2 in branch_set and clash_name not in checked_clashes:
            checked_clashes.add(clash_name)
            results.append({
                "type": "clash",
                "label": f"四柱见【{clash_name}】",
                "organs": "、".join(data["organs"]),
                "meridians": "、".join(data["meridians"]),
                "focus": data["focus"],
                "advice": data["advice"],
            })

    # 2. 统计出现频率最高的地支（偏旺）
    counts: dict[str, int] = {}
    for b in branches:
        counts[b] = counts.get(b, 0) + 1
    for b, cnt in counts.items():
        if cnt >= 2 and b in BRANCH_ZANGFU:
            zf = BRANCH_ZANGFU[b]
            results.append({
                "type": "excess",
                "label": f"四柱【{b}】支重叠（{cnt}重）",
                "organs": zf.get("organ_full", zf.get("organ_short", "")),
                "meridians": zf.get("meridian", ""),
                "focus": f"地支【{b}】本气聚敛偏旺，对应脏腑负荷增大。",
                "advice": f"旺时在【{zf.get('hours', '')}】，{zf.get('tip', '')}",
            })

    return results

