"""季节调候纲要：只在寒暑失序时下处方，春秋平气不干预。

这是本系统的简化纲要，不是古籍原表 —— 《穷通宝鉴》逐月调候 120 条要的是"何干生于
何月"的全表查（日干×月支＝120 格），本切片按 spec §4.2 只取"寒者暖之、暑者清之"
这条共识，因此 ``TIAOHOU_SOURCE`` 明写本系统纲要、不冒充《穷通宝鉴》。日后若要升格
为逐月表，替换本模块即可，``engines/bazi_yongshen`` 的调用形状不变。
"""

#: 月支 → 季节（寅月起春，与 `bazi_wangshuai` 的月令口径同一套分法）。
SEASON_BY_MONTH_ZHI: dict[str, str] = {
    "寅": "spring", "卯": "spring", "辰": "spring",
    "巳": "summer", "午": "summer", "未": "summer",
    "申": "autumn", "酉": "autumn", "戌": "autumn",
    "亥": "winter", "子": "winter", "丑": "winter",
}
# None = 平气，不开处方（spec §6.5 规则 3：春秋两季也要记录"未触发"，不能沉默）。
TIAOHOU_PRESCRIPTION: dict[str, str | None] = {
    "winter": "火", "summer": "水", "spring": None, "autumn": None,
}
TIAOHOU_SOURCE: str = "本系统季节纲要（未采用《穷通宝鉴》逐月表）"
