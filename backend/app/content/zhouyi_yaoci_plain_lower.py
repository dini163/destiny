"""下经 31-64 卦爻辞的今译表（丁组 spec §4.5）：每卦一个 6 元组，元素为 `(anchor, 今译)`。

元组的次序与源表 `zhouyi_yaoci_lower.py` 完全一致（下→上，位置 1-6），所以第几格翻的是
哪一爻不必再数一遍；键构造住在 `content/zhouyi_plain.py`，本文件不出现键字符串。
"""

#: King Wen 卦号 -> 六条 (爻辞 anchor, 今译)，下→上。
#: 空表是「还没建」而不是「没有这一层」：下经 31-64 的第一批今译落在 T7，在那之前本文件
#: 就是一份诚实的空表，所以聚合面 `zhouyi_plain.py` 对它不得做任何非空假设。T7 的所在卦段
#: 可复测：`cd . && grep -n "^## Task 7" docs/superpowers/plans/`
#: `2026-10-03-multi-system-plain-reading-plan-e.md` → 标题带「31-36」。
YAOCI_PLAIN_LOWER: dict[int, tuple[tuple[str, str], ...]] = {}
