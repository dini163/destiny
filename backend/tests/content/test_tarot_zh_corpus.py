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


#: 整句类 `_zh` 的长度带（G10）。下限 12 挡「只有一个词」的敷衍，上限 60 挡「把两句
#: 拼成一段」的越界。156 句牌义实测 21–42 字、均值 30.5，复测：`cd backend &&
#: PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "from app.content.tarot_deck import
#: DECK; t=[len(c.meaning_zh(o)) for c in DECK for o in ('upright','reversed')];
#: print(len(t), min(t), max(t), round(sum(t)/len(t),1))"` → `156 21 42 30.5`。
#: T3 那 35 句位置/描述今天还不在这棵树里，所以这里不替它预填数字：它落地时要用同一条
#: 命令量自己的表，把实测值写在下面而不是援引计划里的草稿值（AGENTS.md §8）。
SENTENCE_BAND = (12, 60)


def _sentence(label: str, text: str) -> str:
    """通用的一句检查：禁串、建议词、长度带，一次把三项判完。"""
    for banned in FORBIDDEN:
        assert banned not in text, f"{label} 带禁串 {banned!r}：{text!r}"
    hits = advice_hits(text)
    assert hits == [], f"{label} 命中建议词 {hits}：{text!r}"
    low, high = SENTENCE_BAND
    assert low <= len(text) <= high, f"{label} 长度 {len(text)} 出带：{text!r}"
    return text


def test_every_card_carries_chinese_meanings_for_both_orientations() -> None:
    """78 张牌 × 2 向 = 156 句中文牌义，必填、与英文不同句、在长度带内（G10、G11）。

    「非空」与「不等于英文」这两件只有真表量得到：字段若默认成英文串，页面看起来有中文、
    其实一行都没译，而响应仍然 200。
    """
    for card in DECK:
        for orientation in ("upright", "reversed"):
            zh = card.meaning_zh(orientation)
            en = card.meaning(orientation)
            assert zh and zh != en, f"{card.id}/{orientation} 的中文牌义缺席或等于英文"
            _sentence(f"{card.id}/{orientation}", zh)


def test_reversed_meanings_open_with_the_reversal_marker() -> None:
    """结构忠实门（G11 唯一能机检的那一半）：逆位中文句一律以「逆位时，」开头。

    英文原句 78 条逆位全都以 `Reversed, ` 起头（复测：`cd backend &&
    PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "from app.content.tarot_deck import
    DECK; print(sum(1 for c in DECK if c.reversed_meaning.startswith('Reversed, ')))"` → `78`），
    所以中文侧同位开头是「没换句式、没自己起话」的可见凭据。钉不住语义，就钉句式；
    语义那一半由 T8 的人工走查承担，且必须逐条贴「原句 / 译文」成对样本进 ledger。
    """
    for card in DECK:
        assert card.reversed_meaning.startswith("Reversed, "), card.id
        assert card.meaning_zh("reversed").startswith("逆位时，"), card.id
        assert not card.meaning_zh("upright").startswith("逆位时，"), card.id


def test_chinese_keyword_tuples_are_assembled_from_the_english_ones() -> None:
    """装配等式门 ②（spec §6.3）：`*_keywords_zh` 必须逐位等于 `KEYWORD_ZH[*_keywords]`。

    这条测的是**装配发生了**且**方向没接错**：等式若用同一份 `KEYWORD_ZH` 手算，它能抓住
    「正位的中文表其实是逆位英文表算出来的」这类接反，也能抓住把中文表按英文顺序抄歪一格
    （off-by-one）——那正是手抄 78 处会出、结构上一处不会出的错。
    """
    for card in DECK:
        assert card.upright_keywords_zh == tuple(KEYWORD_ZH[w] for w in card.upright_keywords)
        assert card.reversed_keywords_zh == tuple(KEYWORD_ZH[w] for w in card.reversed_keywords)
        assert len(card.keywords_zh("upright")) == len(card.keywords("upright")), card.id
        assert len(card.keywords_zh("reversed")) == len(card.keywords("reversed")), card.id


def test_assembled_keyword_texts_pass_the_wording_gates() -> None:
    """651 个装配出来的中文词（78 张牌 × 两个方向的每一个槽位）不带禁串、不带建议词。

    译表自己过过一遍（T1）还不够：进响应的是**按牌装配后**的这些串，同一条门要在装配结果
    上再走一次，才证明「装配」没有把某个词换成别的写法。651 的复测：`cd backend &&
    PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "from app.content.tarot_deck import
    DECK; print(sum(len(c.upright_keywords) + len(c.reversed_keywords) for c in DECK))"` →
    `651`（529 个 token 里有跨牌复用的，所以槽位数大于 token 数）。
    """
    for card in DECK:
        for orientation in ("upright", "reversed"):
            for zh in card.keywords_zh(orientation):
                for banned in FORBIDDEN:
                    assert banned not in zh, f"{card.id}/{orientation}：{zh!r}"
                assert advice_hits(zh) == [], f"{card.id}/{orientation}：{zh!r}"


def test_all_156_chinese_meanings_are_distinct() -> None:
    """156 句两两不同：牌义抄重了不会被任何响应形状发现，只有这一条会。"""
    texts = [card.meaning_zh(o) for card in DECK for o in ("upright", "reversed")]
    assert len(texts) == 156
    duplicated = {t for t, n in Counter(texts).items() if n > 1}
    assert duplicated == set()
