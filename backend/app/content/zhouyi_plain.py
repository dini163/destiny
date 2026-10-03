"""周易今译的聚合面（丁组 spec §4.3）：键构造器 + 两张投影（anchor 表与今译表）。

形状照 `content/zhouyi_text.py` 那一刀：源表分三部（卦辞、上经爻辞、下经爻辞），本表也
分三部聚。键**只**由下面三个具名函数产出，键全集由本文件下方的 `plain_universe` 用同一批
构造器现算，`engines/plain_corpora.py` 的 `ZHOUYI` 登记只引用这个函数对象、不另拼一份字符串
——两处各拼一份，改编号宽度时就会漂（多系统 spec §4）。

工厂吃的只有 `ZHOUYI_READINGS`（今译那一半）。`ZHOUYI_ANCHORS` 是校对用的另一半，
它进不了 `entries`：原文「元亨利贞。」既不满 40 字也不含「你」（spec §4.2 门 2）。
"""

from app.content.zhouyi_guaci import GUA_CI, YONG_CI
from app.content.zhouyi_guaci_plain import GUACI_PLAIN, YONG_PLAIN
from app.content.zhouyi_text import YAO_CI
from app.content.zhouyi_yaoci_plain_lower import YAOCI_PLAIN_LOWER
from app.content.zhouyi_yaoci_plain_upper import YAOCI_PLAIN_UPPER

#: 全表出处：逐条对应 `zhouyi_guaci.py` 与 `zhouyi_yaoci_*.py` 的通行本原文。
ZHOUYI_PLAIN_SOURCE = "本系统白话今译 · 逐条对应 zhouyi_guaci 与 zhouyi_yaoci_upper/lower 的原文"


def gua_ci_key(number: int) -> str:
    """卦辞键；`number` 是 King Wen 序 int，不补零（源表键就是 int，spec §4.3 判据②）。"""
    return f"zhouyi.gua.{number}"


def yao_ci_key(number: int, position: int) -> str:
    """爻辞键；`position` 是 1-6 下→上，与源表 `tuple[position-1]` 同一条换算。"""
    return f"zhouyi.yao.{number}.{position}"


def yong_ci_key(number: int) -> str:
    """用九/用六键；只有乾(1)/坤(2) 有，别给其余 62 卦建键（spec §4.3 判据③）。"""
    return f"zhouyi.yong.{number}"


def plain_universe() -> set[str]:
    """450 键的**全集**，从三张源表现算（少建/多建由工厂的键全集门双向红）。

    复测：`cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "from app.content.zhouyi_plain import plain_universe; print(len(plain_universe()))"` → 450。
    """
    keys = {gua_ci_key(number) for number in GUA_CI}
    keys |= {yong_ci_key(number) for number in YONG_CI}
    keys |= {
        yao_ci_key(number, position)
        for number in YAO_CI
        for position in range(1, len(YAO_CI[number]) + 1)
    }
    return keys


ANCHOR_PAIRS: dict[str, tuple[str, str]] = {
    gua_ci_key(number): pair for number, pair in GUACI_PLAIN.items()
}
ANCHOR_PAIRS |= {yong_ci_key(number): pair for number, pair in YONG_PLAIN.items()}
ANCHOR_PAIRS |= {
    yao_ci_key(number, position): pair
    for table in (YAOCI_PLAIN_UPPER, YAOCI_PLAIN_LOWER)
    for number, rows in table.items()
    for position, pair in enumerate(rows, 1)
}

#: anchor 半边（逐字源文）。只给测与人工校对用，不进 `PlainCorpus.entries`。
ZHOUYI_ANCHORS: dict[str, str] = {key: anchor for key, (anchor, _plain) in ANCHOR_PAIRS.items()}

#: 今译半边（工厂吃的就是这一张）。
ZHOUYI_READINGS: dict[str, str] = {key: plain for key, (_anchor, plain) in ANCHOR_PAIRS.items()}
