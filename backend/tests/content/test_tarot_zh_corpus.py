"""塔罗 `_zh` 正文表的措辞与覆盖门（丁组 spec §6.3、§8）。

本文件是塔罗这一家所有 `_zh` 文案的唯一机检住处：T1 管 529 条译词，T2 追加 156 句
牌义，T3 追加 35 句位置/描述。三条口径写在最前面，读测的人不必翻计划：

① 这不是白话转述层，是**补配对**（spec §6.1）：中文与英文是同一张表同一行的两半，
   所以本文件不查 `PLAIN_CORPORA`、不调 `compose()`、不看档位与开篇句（G7）。
② 禁字表与六字表一律**从 `tests.plain_wording` 导入**，不在这里抄一份（G8，R26 口径：
   抄一份就等于给「两处口径漂移」留出位置）。
③ 长度按 **12–60 字的带**判，不套「每条 ≥40 字」那条全站下限（G10：实测 156 句里只有
   4 句够 40 字，凑够它的唯一办法是替原句加话，而 spec §7 规则 11 明令禁止加话）。
   带子从 T2 起才有人守：它量的是句子（牌义 156 句、位置/描述 35 句），T1 的 529 条译词
   是 1–9 字的词元，不进这条带，由 `test_keyword_translations_are_chinese_only` 的
   「纯中文、无标点」口径管。
"""

import re
from collections import Counter

from app.content.tarot_deck import DECK
from app.content.tarot_keywords_zh import (
    KEYWORD_ZH,
    SHARED_TRANSLATION,
    TAROT_KEYWORDS_ZH_SOURCE,
)
from tests.plain_wording import FORBIDDEN, advice_hits

#: 禁串与六字表**都从 `tests.plain_wording` 导入**，这里一个都不抄（G8，R26 口径：抄一份
#: 就等于给「两处口径漂移」留出位置）。`SLOT_FORBIDDEN` 在本文件**不适用**：那是「槽位被
#: 嵌进句子中间」的口径（`plain_wording.py:22`），塔罗的 `_zh` 是独立成句/独立成词，
#: 所以「你」「。」这类字在这里合法（156 句牌义全部以「。」收尾）。

CJK = re.compile(r"[一-鿿]")


def _deck_tokens() -> set[str]:
    return {word for card in DECK for word in (*card.upright_keywords, *card.reversed_keywords)}


def test_keyword_table_covers_every_deck_keyword_exactly() -> None:
    """覆盖门 ①：两个方向都等——漏一行就少一个中文词，多一行就是译了牌库里没有的词。

    缺席与冗余项直接印出来：这张表 529 行，只说「不相等」的失败没法修（spec §8 末段
    警告的「恒真断言」另一面是「无信息断言」，都算没测）。
    """
    tokens = _deck_tokens()
    assert set(KEYWORD_ZH) == tokens, (
        f"缺 {sorted(tokens - set(KEYWORD_ZH))} / 多 {sorted(set(KEYWORD_ZH) - tokens)}"
    )
    assert len(KEYWORD_ZH) == 529, "行数动了：牌库或译表被改过，先跑 Step 1 那条计数命令复核"


def test_shared_translations_are_declared_not_accidental() -> None:
    """覆盖门 ③：多词一译必须具名（spec §6.3 的门 ③）。

    实测碰撞是 **0 条**（`unique values: 529 of 529`），所以 `SHARED_TRANSLATION` 今天
    以空表交付。空表不是摆设，它是「例外必须登记」的接口，形状同
    `tests/test_architecture.py::BASELINE`：门永远按「未登记的重复 = 0」判，将来真出现
    一译多词，就得在这里具名并说明凭什么可以共用。登记项还要**逐字对账**，所以登记了
    却过期的条目一样红。
    """
    grouped: dict[str, set[str]] = {}
    for word, zh in KEYWORD_ZH.items():
        grouped.setdefault(zh, set()).add(word)
    duplicated = {zh for zh, words in grouped.items() if len(words) > 1}
    assert duplicated == set(SHARED_TRANSLATION), (
        f"未登记的多词一译 {sorted(duplicated - set(SHARED_TRANSLATION))}；"
        f"登记了但已不重复 {sorted(set(SHARED_TRANSLATION) - duplicated)}"
    )
    for zh, words in SHARED_TRANSLATION.items():
        assert tuple(sorted(grouped[zh])) == words, f"「{zh}」的共用名单与现表不一致"


def test_keyword_translations_are_chinese_only() -> None:
    """每条译词都是中文：不含拉丁字母、含至少一个汉字、不带标点与首尾空白。

    钉「不夹英文」是因为关键词会被 T5 的框架句原样拼进 `synthesis`（`、` 连接前三条），
    一条漏译就变成页面上中英夹杂的词表；钉「无标点」是因为词元不进句子，带「，」的词
    拼起来读起来像半句话。
    """
    for word, zh in KEYWORD_ZH.items():
        assert zh == zh.strip(), f"{word} 的首尾有空白"
        assert CJK.search(zh), f"{word} 的译词里没有汉字：{zh!r}"
        assert not re.search(r"[A-Za-z]", zh), f"{word} 的译词夹了拉丁字母：{zh!r}"
        for punct in ("；", "。", "，", "、", "(", "（"):
            assert punct not in zh, f"{word} 的译词带标点 {punct!r}：{zh!r}"
        for banned in FORBIDDEN:
            assert banned not in zh, f"{word} 的译词带禁串 {banned!r}"


def test_keyword_translations_take_no_verdict_words() -> None:
    """建议词零豁免（G9）：529 条译词命中 `advice_hits()` 的必须是空集。

    实测 0 命中，所以本系统**没有**例外名单、没有具名词形要登记（与紫微四化那种
    「名相必含化忌」的形不同，`non_advice` 在这里用不上）。将来要放宽必须先在这张
    断言里具名并把理由写进 docstring，不许悄悄传 `masks=`。
    """
    offenders = {zh: hits for zh, hits in ((v, advice_hits(v)) for v in KEYWORD_ZH.values()) if hits}
    assert offenders == {}


def test_translation_table_declares_its_own_credential() -> None:
    """译表单独一个出处串（G14）：它的凭据是「本系统自持的译表」，不是公共领域原典。

    混用 `TAROT_SOURCE` 等于让译表冒充原典——卢恩 spec 决策 24 把两张凭据不同的表分开
    署，是同一条理由的反向运用。真正的四行清单在 T6 才组装，这里只钉「串存在且说明了
    自己是谁」。
    """
    assert TAROT_KEYWORDS_ZH_SOURCE
    assert "译" in TAROT_KEYWORDS_ZH_SOURCE, "出处串要能看出这是本系统自持的译表"
