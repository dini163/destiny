"""周易占断辞的受控词表（verdict 判定层的锚；古典可署名，纯表零逻辑）。

《周易》通行本（王弼注本）的卦辞、爻辞自带一套断占语：彖/爻占辞里「吉、亨、利、
无咎」属正向，「凶、吝、悔、咎、厉」属负向——这是句读卦爻辞自古相传的占辞分类，
不是本平台新造的吉凶词。本词表只收这九个受控词，引擎按文本中的出现次数净值折算
倾向分；词表之外的字（包括卦名、象喻）一律不参与计分，引擎不现编任何吉凶判断。

出处到章不到书（R46 诚实口径）：分类依据就是通行本上经三十卦、下经三十四卦
卦爻辞自身的断占语系统，不另立书名引文；「无咎」是一个完整占辞，必须先于裸「咎」
匹配，否则无咎被拆成「无 + 咎」双记（装配侧的匹配顺序由引擎自守，本表只管词集）。
"""

from dataclasses import dataclass

#: 断占语所属的章：通行本上经三十卦、下经三十四卦的卦辞与爻辞（含乾用九、坤用六）。
_CHAPTER = "《周易》通行本（王弼注本）上经三十卦、下经三十四卦卦辞与爻辞断占语"


@dataclass(frozen=True)
class DuanCi:
    """一个受控占断辞：词面、极性、章属出处。"""

    word: str
    polarity: str  # "positive" | "negative"
    source: str


#: 正向占断辞四条。词面顺序即引擎剔词顺序：先数「无咎」并从文本剔除，再数 吉/亨/利。
POSITIVE_DUANCI: tuple[DuanCi, ...] = (
    DuanCi("无咎", "positive", f"{_CHAPTER}·无咎"),
    DuanCi("吉", "positive", f"{_CHAPTER}·吉"),
    DuanCi("亨", "positive", f"{_CHAPTER}·亨"),
    DuanCi("利", "positive", f"{_CHAPTER}·利"),
)

#: 负向占断辞五条。「咎」在此是裸咎（灾祸/过咎），不含已被剔出的「无咎」。
NEGATIVE_DUANCI: tuple[DuanCi, ...] = (
    DuanCi("凶", "negative", f"{_CHAPTER}·凶"),
    DuanCi("吝", "negative", f"{_CHAPTER}·吝"),
    DuanCi("悔", "negative", f"{_CHAPTER}·悔"),
    DuanCi("咎", "negative", f"{_CHAPTER}·咎"),
    DuanCi("厉", "negative", f"{_CHAPTER}·厉"),
)

#: 登记表（`content/__init__.py::ZHOUYI_CONTENT_SOURCES`）用的书级出处串。
DUANCI_SOURCE = (
    "《周易》通行本（王弼注本）上经、下经卦辞与爻辞断占语分类："
    "吉/亨/利/无咎为正向，凶/吝/悔/咎/厉为负向，依据卦爻辞自身的占辞系统，非平台新造吉凶词。"
)

#: 正向词面（装配侧计数用；首项「无咎」必须先剔）。
POSITIVE_WORDS: tuple[str, ...] = tuple(entry.word for entry in POSITIVE_DUANCI)

#: 负向词面。
NEGATIVE_WORDS: tuple[str, ...] = tuple(entry.word for entry in NEGATIVE_DUANCI)
