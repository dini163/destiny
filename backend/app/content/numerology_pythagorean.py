"""毕达哥拉斯字母映射表 —— 数字命理的唯一取数入口（spec §5.1）。

本模块只放**表**，不放算法：约简、求和、分账全归 `engines/numerology.py`。
字母→数字是整套系统的地基，PRD §6.9 要求「字母→数字映射表显式写死并单测」，故
26 个键逐个列出，不用 `(ord(c) - 65) % 9 + 1` 之类的算式生成 —— 算式生成会把一处
笔误变成一张看不出错表的表（spec 决策 2）。`LETTER_VALUES` 与 `VALUE_GROUPS` 由
`tests/content/test_numerology_corpora.py` 双向锁死，两处不许各自漂移。

出处诚实：西式毕达哥拉斯数理没有古籍，只有现代整理稿。字母表这一层各家完全一致，
无分歧可记；出处字符串自认「非古籍」。
"""

from __future__ import annotations

#: 书级出处：自认是通行表整理，不是古籍。
PYTHAGOREAN_SOURCE = "西方毕达哥拉斯数理通行字母映射表（现代整理，非古籍）"

#: A–Z 逐格写死，按字母序排，便于逐格核对单个字母。
#: 26 = 9 + 9 + 8：第三轮只到 S..Z 八个字母，故映射到 9 的只有 I、R 两个字母。
#: 这是该表的固有形状，不是缺漏 —— 别照"每组三个"的直觉去补一个不存在的字母。
LETTER_VALUES: dict[str, int] = {
    "A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "F": 6, "G": 7, "H": 8, "I": 9,
    "J": 1, "K": 2, "L": 3, "M": 4, "N": 5, "O": 6, "P": 7, "Q": 8, "R": 9,
    "S": 1, "T": 2, "U": 3, "V": 4, "W": 5, "X": 6, "Y": 7, "Z": 8,
}

#: 九组倒排（1→A,J,S …），照 spec §2.5 抄。前端字母映射表直接渲染它，省得在前端
#: 把 `LETTER_VALUES` 再倒排一遍 —— 倒排逻辑存在两处，就会有两处可能错。
VALUE_GROUPS: tuple[tuple[int, tuple[str, ...]], ...] = (
    (1, ("A", "J", "S")),
    (2, ("B", "K", "T")),
    (3, ("C", "L", "U")),
    (4, ("D", "M", "V")),
    (5, ("E", "N", "W")),
    (6, ("F", "O", "X")),
    (7, ("G", "P", "Y")),
    (8, ("H", "Q", "Z")),
    (9, ("I", "R")),
)

#: 元音集合。Y **不在内**（spec 决策 7）：英文里 Y 算不算元音取决于它在音节里的
#: 实际发音（`Lynn` 算、`Yolanda` 不算），而音节切分不可判定也不可单测。故默认按
#: 辅音，把决定权交给入参 `y_as_vowel`；这条**规则**在引擎里，不在语料里。
VOWELS: frozenset[str] = frozenset({"A", "E", "I", "O", "U"})

#: 主数：永不约简（spec 决策 3）。唯一例外是四挑战，由引擎显式传 `keep_master=False`。
MASTER_NUMBERS: frozenset[int] = frozenset({11, 22, 33})

#: 业力债数：约简**途中**出现的双位数落在这四个上就报出（spec 决策 6）。
KARMIC_DEBT_NUMBERS: frozenset[int] = frozenset({13, 14, 16, 19})


def letter_value(char: str) -> int:
    """取单个字母的数。大小写不敏感；非 A–Z 一律 `KeyError`。

    抛错而不返回 0 是刻意的：静默返回 0 会让"名字里没有拉丁字母"变成一次看似成功的
    全零计算（spec 决策 8）。过滤非字母字符是引擎的职责，它必须先过滤再调本函数。
    """
    return LETTER_VALUES[char.upper()]
