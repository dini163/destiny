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
   是 1–9 字的词元，不进这条带。口径各是一条判据，不互相援引：译词侧是
   `test_keyword_translations_are_chinese_only` 的**整串纯汉字** fullmatch（⇒ 自动无标点、
   无拉丁字母、无首尾空白），句子侧是 `_sentence` 的**含汉字 + 不含拉丁字母**两判
   （前者挡中英对调，后者挡半译）。
"""

import re
from collections import Counter

from app.content.tarot_deck import DECK, SPREADS, TAROT_SOURCE
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


#: 译词的「纯中文」口径：整串只由中日韩汉字区段（U+4E00–U+9FFF）组成。
#: 与 `CJK` 同一个字符范围，但 `CJK` 没有量词（它是给 `search` 用的「含汉字」判据），
#: 所以这里另写一条带 `+` 的：`CJK.fullmatch(zh)` 会把两字以上的词元判成不合法（实跑即是）。
PURE_CJK = re.compile(r"[\u4e00-\u9fff]+")


def test_keyword_translations_are_chinese_only() -> None:
    """每条译词都是中文：整串只由汉字组成，因而自动不含拉丁字母、不含标点、无首尾空白。

    钉「不夹英文」是因为关键词会被 T5 的框架句原样拼进 `synthesis`（`、` 连接前三条），
    一条漏译就变成页面上中英夹杂的词表；钉「无标点」是因为词元不进句子，带「，」的词
    拼起来读起来像半句话。

    这两件原来写作三条（含汉字 / 拉丁禁串 / 六个标点枚举），现在一条 `PURE_CJK.fullmatch`
    全包（`[\u4e00-\u9fff]+` 就是原来那个 `[一-鿿]` 范围加量词），三份口径并成一份是刻意的
    ——同一个事实多处钉就是漂移的起点（AGENTS.md §2 的精神）。实测 529 条值 0 条不满足，
    所以这条加强是免费的（复测：`cd backend && PYTHONIOENCODING=utf-8
    .venv/Scripts/python.exe -c "import re; from app.content.tarot_keywords_zh import
    KEYWORD_ZH; print(len(KEYWORD_ZH), sum(1 for v in KEYWORD_ZH.values() if not
    re.fullmatch(r'[\\u4e00-\\u9fff]+', v)))"` → `529 0`；把判据分别换成
    `re.search(r'[A-Za-z]', v)` 与「含那六个枚举标点之一」，非零计数也都是 0，
    所以旧三条各自抓到的东西，新一条一样都不放过）。
    `zh == zh.strip()` 仍单列：它给的是「首尾有空白」这个具体诊断，fullmatch 只会说
    「不是纯汉字」，报错信息更差。
    """
    for word, zh in KEYWORD_ZH.items():
        assert zh == zh.strip(), f"{word} 的首尾有空白"
        assert PURE_CJK.fullmatch(zh), f"{word} 的译词不是纯汉字：{zh!r}"
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


def test_deck_source_string_keeps_the_two_claims_it_carries() -> None:
    """`TAROT_SOURCE` 的承重声明用**子串**钉，不钉全串（形状照 `test_rune_corpora.py` 的
    `test_wyrd_does_not_borrow_the_kylver_or_unicode_credentials`）。

    为什么是子串：这串是印进响应给读者看的出处文案（现值 = `Rider-Waite-Smith 塔罗通行牌义 ·
    78 张大小阿卡纳与六种 Waite 系布阵位次（PRD 6.7）`，定义在 `app/content/tarot_deck.py:19`），
    它的**说法**（牌义与布局同据 Rider-Waite-Smith 一系、清单在 PRD 6.7 有规范落点）必须留住，
    **措辞**要能自由改好——钉全串就是把一句注释锁进测里（R28 反对的那一类）。
    为什么这条不是偏差表第 20 行那个盲区：那行的「手抄 `source=`」抓不到，是因为等式两侧同读
    一个常量（改定义谁都不红）；这里量的正是那个常量自己承载的两条声明，被删掉才红。
    """
    assert "Rider-Waite" in TAROT_SOURCE, "牌义凭据被摘掉：出处串不再说明这套牌义据哪个体系"
    assert "PRD" in TAROT_SOURCE, "布局凭据被摘掉：六种位次布局的出处（PRD 6.7）没了着落"


#: 整句类 `_zh` 的长度带（G10）。下限 12 挡「只有一个词」的敷衍，上限 60 挡「把两句
#: 拼成一段」的越界。156 句牌义实测 21–42 字、均值 30.5，复测：`cd backend &&
#: PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "from app.content.tarot_deck import
#: DECK; t=[len(c.meaning_zh(o)) for c in DECK for o in ('upright','reversed')];
#: print(len(t), min(t), max(t), round(sum(t)/len(t),1))"` → `156 21 42 30.5`。
#: T3 那 35 句落地后按同一条命令量自己的表，实测值写在下面（不援引计划里的草稿值，
#: AGENTS.md §8）：整族 17–31 字、均值 23.2，其中宫位释义 17–31 字、均值 23.0，牌阵描述
#: 17–29 字、均值 24.2，复测：`cd backend && PYTHONIOENCODING=utf-8
#: .venv/Scripts/python.exe -c "from app.content.tarot_deck import SPREADS;
#: pos=[len(p.meaning_zh) for s in SPREADS.values() for p in s.positions];
#: des=[len(s.description_zh) for s in SPREADS.values()];
#: f=lambda t: (len(t), min(t), max(t), round(sum(t)/len(t),1)); print('all', f(pos+des));
#: print('pos', f(pos)); print('desc', f(des))"` → `all (35, 17, 31, 23.2)` /
#: `pos (29, 17, 31, 23.0)` / `desc (6, 17, 29, 24.2)`：距下限最少 5 字（最短句 17 字），
#: 距上限最少 29 字（最长句 31 字）。
SENTENCE_BAND = (12, 60)


def _sentence(label: str, text: str) -> str:
    """通用的一句检查：语言方向、半译、禁串、建议词、长度带，一次把五项判完。

    方向那一项（必须有汉字）挡的是**中英互换**：`_spread()` 那格是五个一串的位置元组，
    第 4/5 格一旦对调，落到 `meaning_zh` 上的英文句照样非空、照样在 12–60 带内、照样与
    现在变成中文的 `meaning` 不相等、在 35 句里也照样唯一 —— 其余各项一个都不会红
    （T3 评审量出来的这条，卡片侧同理）。它证不了「译得准」（G11 把那一半交给人工走查），
    但它是「配对没接反」最便宜的机检，所以住在公共检查里而不是任何一家的门里。

    「不含拉丁字母」把方向门从「整句是英文」扩到「半句没译」：`「开端、start」` 这类值
    原来五项全过（含汉字、非禁串、无建议词、在带内、与英文不等）。实测 191 句（156 牌义
    + 29 位次释义 + 6 阵描述）命中 0 条，所以这条也是免费的加强（复测：`cd backend &&
    PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "import re; from
    app.content.tarot_deck import DECK, SPREADS; t=[c.meaning_zh(o) for c in DECK for o in
    ('upright','reversed')] + [p.meaning_zh for s in SPREADS.values() for p in s.positions] +
    [s.description_zh for s in SPREADS.values()]; print(len(t), sum(1 for x in t if
    re.search(r'[A-Za-z]', x)))"` → `191 0`）。

    **本文件的限度（登记，不装钉过；形状同偏差表第 20 行）**：上面两判都只管**中英对调**
    这一个方向。中文↔中文的跨牌错行——把两张牌的 `upright_meaning_zh` 字面量互换——在本
    文件任何一条门下都不红：换过去的句子照样含汉字、无拉丁、非空、在 12–60 带内、156 句里
    唯一、无禁词。本轮加了两判之后仍**实测**复现这条限度（`tarot_major.py` 的 1 号牌与 2 号牌
    的 `upright_meaning_zh` 互换 → 本文件与 `tests/golden/test_tarot_golden.py` 共 **43 条全绿
    / 0 红**，还原后同）。G11 早就把语义那一半判给人工走查，所以这条错行的唯一防线是 T8
    那次成对走查（逐条「原句 / 译文」贴对，记录在 `progress.md`），不是这里。
    """
    assert CJK.search(text), f"{label} 不含汉字，疑似中英互换：{text!r}"
    assert not re.search(r"[A-Za-z]", text), f"{label} 含拉丁字母，疑似半译：{text!r}"
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


def test_every_spread_position_carries_a_chinese_gloss() -> None:
    """29 个宫位各有中文释义：非空、不等于英文、在长度带内。

    位次的中文**标签**早就成对（`label_zh`，`tests/golden/test_tarot_golden.py` 的
    `test_spread_positions_have_unique_keys_and_bilingual_labels` 已钉；此处刻意不写行号——
    那条测原来在 `:96-103`，T4 在同文件追加两条测后漂到了 `:98-105`，见计划偏离表第 14 行），
    缺的是释义那半边——这正是 spec §3.2 实测出的形状：塔罗不是「全英文」，是「名字有中文、
    句子只有英文」。本条只钉这一件，标签那件不在这里重复（同一件事两份口径就是漂移的起点）。
    """
    total = 0
    for spread in SPREADS.values():
        for position in spread.positions:
            total += 1
            assert position.meaning_zh, f"{spread.id}/{position.key} 缺中文释义"
            _sentence(f"{spread.id}/{position.key}", position.meaning_zh)
            assert position.meaning_zh != position.meaning, f"{spread.id}/{position.key}"
    assert total == 29, "宫位数动了：阵或位次被增删，先复核张数 1/3/10/5/5/5"


def test_every_spread_carries_a_chinese_description() -> None:
    """六个阵各有中文描述，且 `description_zh` 与 `description` 同在不互为副本。"""
    assert len(SPREADS) == 6
    for spread in SPREADS.values():
        assert spread.description_zh, spread.id
        _sentence(f"{spread.id}/description", spread.description_zh)
        assert spread.description_zh != spread.description


def test_spread_chinese_texts_are_all_distinct() -> None:
    """35 句（29 释义 + 6 描述）两两不同。

    这条不是洁癖：三个阵同名不同位（`celtic_cross.present` 与 `three_card.present`、
    三个阵各有一个 `outcome`、两个阵各有一个 `guidance`/`challenge`），抄串了读起来完全
    通顺，只有对账能发现（复测：`cd backend && PYTHONIOENCODING=utf-8
    .venv/Scripts/python.exe -c "from app.content.tarot_deck import SPREADS;
    print([ (s,p.key) for s in SPREADS for p in SPREADS[s].positions if p.key in
    ('present','outcome','guidance','challenge') ])"` → 实测 9 条重名位次（4 个键名分别被
    2、3、2、2 个阵复用；计划草稿的 8 与本命令输出不符，以输出为准，AGENTS.md §8）。
    """
    texts = [p.meaning_zh for s in SPREADS.values() for p in s.positions]
    texts += [s.description_zh for s in SPREADS.values()]
    assert len(texts) == 35
    assert len(set(texts)) == 35, {t for t, n in Counter(texts).items() if n > 1}


def test_spread_texts_take_no_verdict_words() -> None:
    """35 句宫位/描述过建议词门（G9 的 0 命中实测覆盖这一族）。"""
    for spread in SPREADS.values():
        assert advice_hits(spread.description_zh) == [], spread.id
        for position in spread.positions:
            assert advice_hits(position.meaning_zh) == [], f"{spread.id}/{position.key}"
