"""月令旺相休囚死：等第序列是通行命理口径，百分数是本地模型参数。

《淮南子》《五行大义》给"旺相休囚死"五等第，不给百分数；相邻等第取 25 分间距
纯属本系统的离散化选择，因此账本的 `source` 写"模型参数"，不写古籍名。
"""

WANG_SHUAI_VALUE: dict[str, float] = {
    "旺": 100.0, "相": 75.0, "休": 50.0, "囚": 30.0, "死": 15.0,
}

GENERATES = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
CONTROLS = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}


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
