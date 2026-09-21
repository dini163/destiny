"""月令旺相休囚死：等第次序有出处，百分数没有。

《三命通会·论五行旺相休囚死并寄生十二宫》逐季给出五等第的所以然 —— "盛德乘时
曰旺……子乘父业故火相……生我者当知退故水休……被火克制不能施设故金囚……春木克土
则死"，四季皆然。本模块的 `wang_shuai` 就是这段话的可执行形式（五行生克取自
``app.content.wuxing``，不在这里重抄）。

等第之上的百分数是本系统的离散化选择：相邻等第取 25 分间距，古籍只给"旺于春、
相于夏"这类定性描述，从不给数字。因此由它派生的账本 `source` 一律写
``MODEL_PARAM_SOURCE``，UI 溯源面板照此展示。
"""

from app.content.wuxing import CONTROLS, GENERATES

#: 五等第 → 本系统赋分（模型参数，见模块 docstring）。
WANG_SHUAI_VALUE: dict[str, float] = {
    "旺": 100.0, "相": 75.0, "休": 50.0, "囚": 30.0, "死": 15.0,
}


def wang_shuai(element: str, month_element: str) -> str:
    """Return the 旺相休囚死 grade of ``element`` under a season's element."""
    if element == month_element:
        return "旺"
    if GENERATES[month_element] == element:
        return "相"
    if GENERATES[element] == month_element:
        return "休"
    if CONTROLS[element] == month_element:
        return "囚"
    return "死"
