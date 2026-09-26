"""Golden tests for the Kabbalah Tree of Life map and the gematria fold.

The Tree is fixed Golden Dawn content: ten Sephiroth (+ the hidden Daath), twenty-two
paths numbered 11-32, three pillars and four worlds. Gematria weighs Latin letters
A=1…Z=26; the arithmetic is independently verifiable (LIGHT = 12+9+7+8+20 = 56,
digital root 2; CHAI = 3+8+1+9 = 21), and the fold maps the ordinal onto a Sephirah
(1-10) and a Path (11-32).
"""

import string

import pytest
from fastapi.testclient import TestClient

from app.core.errors import GematriaInputError
from app.engines.kabbalah import build_tree, compute_gematria


def test_tree_has_the_canonical_structure() -> None:
    tree = build_tree()
    assert tree.sephirah_count == 10
    assert len(tree.sephiroth) == 10
    assert tree.path_count == 22
    assert len(tree.paths) == 22
    assert len(tree.pillars) == 3
    assert len(tree.worlds) == 4


def test_sephiroth_are_numbered_one_to_ten() -> None:
    tree = build_tree()
    assert [s.number for s in tree.sephiroth] == list(range(1, 11))
    assert tree.sephiroth[0].name_zh == "王冠"   # Kether
    assert tree.sephiroth[-1].name_zh == "王国"  # Malkuth
    assert len({s.id for s in tree.sephiroth}) == 10


def test_daath_is_the_hidden_node() -> None:
    tree = build_tree()
    assert tree.daath is not None
    assert tree.daath.number == 0
    assert tree.daath.is_hidden is True


def test_paths_run_eleven_to_thirty_two_and_join_distinct_spheres() -> None:
    tree = build_tree()
    assert sorted(p.number for p in tree.paths) == list(range(11, 33))
    first = next(p for p in tree.paths if p.number == 11)
    assert first.tarot == "The Fool"  # Golden Dawn path 11 = Alef
    for path in tree.paths:
        assert 1 <= path.from_sephirah <= 10
        assert 1 <= path.to_sephirah <= 10
        assert path.from_sephirah != path.to_sephirah
        assert path.letter_value > 0


def test_gematria_ordinal_arithmetic() -> None:
    assert compute_gematria("A").english_ordinal == 1
    assert compute_gematria("AB").english_ordinal == 3  # 1 + 2
    light = compute_gematria("LIGHT")
    assert light.normalized == "LIGHT"
    assert light.english_ordinal == 56    # 12+9+7+8+20
    assert light.english_reduction == 29  # 3+9+7+8+2
    assert light.digital_root == 2        # 5+6=11 → 1+1=2


def test_gematria_ignores_case_and_non_letters() -> None:
    assert compute_gematria("CHAI").english_ordinal == 21  # 3+8+1+9
    assert compute_gematria("chai").english_ordinal == 21
    assert compute_gematria("c h a i").english_ordinal == 21


def test_gematria_folds_onto_the_tree() -> None:
    reading = compute_gematria("LIGHT")
    assert 1 <= reading.sephirah.number <= 10
    assert 11 <= reading.path.number <= 32
    assert reading.synthesis.strip()


def test_tree_endpoint(client: TestClient) -> None:
    response = client.get("/api/v1/kabbalah/tree")
    assert response.status_code == 200
    body = response.json()
    assert body["sephirah_count"] == 10
    assert body["path_count"] == 22
    assert len(body["sephiroth"]) == 10
    assert len(body["paths"]) == 22


def test_gematria_endpoint(client: TestClient) -> None:
    response = client.post("/api/v1/kabbalah/gematria", json={"text": "LIGHT"})
    assert response.status_code == 200
    body = response.json()
    assert body["english_ordinal"] == 56
    assert body["digital_root"] == 2


def test_gematria_rejects_text_without_latin_letters(client: TestClient) -> None:
    response = client.post("/api/v1/kabbalah/gematria", json={"text": "12345"})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "gematria_no_latin_letters"


# ============================================================================ #
# 外部锚点（Task 9A ①-⑥）
# ============================================================================ #
#
# 上面几条属于「调一次引擎、断它返回的东西非空 / 数量对」这一族：值从被测对象读回来，
# 断言也从同一处读回来，引擎自错即测自错。下面按判据 ①-⑥ 追加八条测（⑥ 拆成
# 「跳字可见」「字母刻度本身」「无字母即抛错」三条），把锚换成两类表外可推导的东西：
#
# * **公版结构事实** —— 22 个希伯来字母的表序与 1/10/20…400 百位制 gematria、塔罗大
#   阿卡纳 0…I…XXI 各一枚、图论握手引理 Σdeg = 2|E|、三柱与左右坐标 / 四界与上下坐标
#   的对应、A=1…Z=26 的字母表总和 351 = 26×27/2。
# * **「响应自己印的声称 ⊆ 响应自己给的数据」**（AGENTS §7 的反向一面：出处可以不是
#   仓内表，但印给用户的话必须在同一份响应里兑）。
#
# 卡巴拉在 PRD 与 design/ 里查无此系统（复测：`grep -rln "卡巴拉\|Kabbal" prd/*.md` 与
# `ls design/ | grep -i kabbal`，两条在 2026-09-27 均无输出），因此仓内没有可比对的权威
# 名录：外部锚只走到公版可自查的结构与数值为止，不引入任何凭记忆抄来的命名表。

#: 手写外部表：Golden Dawn 路径号 11-32 → 字母转写名 → 该字母的希伯来 gematria 值。
#: 表序 Aleph…Tav 与数值 1…9、10、20…100（十位）、200/300/400（百位）是公版事实，
#: 与 ``content/kabbalah.py`` 无关，所以这条真能判语料的对错。
#: 复测：`pytest tests/golden/test_kabbalah_golden.py -k hebrew`（下表与引擎输出逐字
#: 相等才绿；跑不动时用它所在的那条测本身当测法）。把逐条值的第三列换成 `p.letter`
#: 即得下面那串字形。
HANDBOOK_LETTERS: tuple[tuple[int, str, int], ...] = (
    (11, "Aleph", 1),
    (12, "Beth", 2),
    (13, "Gimel", 3),
    (14, "Daleth", 4),
    (15, "Heh", 5),
    (16, "Vav", 6),
    (17, "Zayin", 7),
    (18, "Cheth", 8),
    (19, "Teth", 9),
    (20, "Yod", 10),
    (21, "Kaph", 20),
    (22, "Lamed", 30),
    (23, "Mem", 40),
    (24, "Nun", 50),
    (25, "Samekh", 60),
    (26, "Ayin", 70),
    (27, "Peh", 80),
    (28, "Tzaddi", 90),
    (29, "Qoph", 100),
    (30, "Resh", 200),
    (31, "Shin", 300),
    (32, "Tav", 400),
)

#: 22 个希伯来字母的基本形式（U+05D0–U+05EA，不含 ך ם ן ף ץ 五个词尾形）。
#: 复测同 ``HANDBOOK_LETTERS`` 那条，只是把逐条打出来的第三列换成 ``p.letter``。
HANDBOOK_GLYPHS = "אבגדהוזחטיכלמנסעפצקרשת"

#: 大阿卡纳的 22 个序号，愚者 0 起、世界 XXI 止（公版）。
HANDBOOK_NUMERALS: tuple[str, ...] = (
    "0", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI",
    "XII", "XIII", "XIV", "XV", "XVI", "XVII", "XVIII", "XIX", "XX", "XXI",
)


def test_hebrew_letters_match_the_public_alphabet_and_gematria_scale() -> None:
    """判据 ①：字母三列（路径号 / 转写名 / gematria 值）逐条对拍表外标准。

    今天这一族只有一句 ``path.letter_value > 0``（在
    ``test_paths_run_eleven_to_thirty_two_and_join_distinct_spheres`` 里，Task 9A 前的既有条目），
    它判不出「Kaph 被写成 11」—— 11 也 > 0。数值表是百位制（1-10 单位、20-100 十位、
    200/300/400 百位），抄错一处就会同时破坏字形序与数值序，故两条一起钉。
    """
    tree = build_tree()
    assert [(p.number, p.letter_name, p.letter_value) for p in tree.paths] == list(
        HANDBOOK_LETTERS
    )
    assert "".join(p.letter for p in tree.paths) == HANDBOOK_GLYPHS
    assert len({p.letter for p in tree.paths}) == 22
    # 数值列单独再走一遍公版刻度：单位数 1…10、十位 20…100、百位 200/300/400。
    assert [p.letter_value for p in tree.paths] == (
        list(range(1, 11)) + list(range(20, 101, 10)) + [200, 300, 400]
    )


def test_tarot_trumps_are_the_major_arcana_exactly_once_each() -> None:
    """判据 ②：22 枚塔罗序号与 0…I…XXI 成双射，并兑响应自己印的取向。

    界线要说清：黄金黎明制把力量排 VIII、正义排 XI，马赛第制正好相反（正义 VIII ·
    力量 XI）—— **换制不是 bug 是取向，本测不裁决哪一制才对**。它测的是出处诚实性：
    ``provenance.source`` 与 ``provenance.note`` 把这一取向印给了用户（AGENTS §7），
    那么同一份响应里的数据必须兑；哪天有人改了取向却忘了改文案，这条才红。
    """
    tree = build_tree()
    numerals = [p.tarot_numeral for p in tree.paths]
    assert len(numerals) == len(set(numerals)) == 22
    assert set(numerals) == set(HANDBOOK_NUMERALS)
    # 路径 11 = 愚者 0 起，逐号 +1：序号在表里的位置 == 路径号 − 11。
    assert numerals == list(HANDBOOK_NUMERALS)
    for path in tree.paths:
        assert HANDBOOK_NUMERALS.index(path.tarot_numeral) == path.number - 11
    assert len({p.tarot for p in tree.paths}) == 22

    by_number = {p.number: p for p in tree.paths}
    assert (by_number[19].tarot, by_number[19].tarot_zh, by_number[19].tarot_numeral) == (
        "Strength",
        "力量",
        "VIII",
    )
    assert (by_number[22].tarot, by_number[22].tarot_zh, by_number[22].tarot_numeral) == (
        "Justice",
        "正义",
        "XI",
    )
    assert "力量 VIII" in tree.provenance.source and "正义 XI" in tree.provenance.source
    assert "力量为 VIII" in tree.provenance.note and "正义为 XI" in tree.provenance.note


def test_the_path_graph_is_a_simple_connected_graph_on_ten_spheres() -> None:
    """判据 ③：22 条路径构成十顶点上的简单连通图。

    分两层，别混着读：

    * **必真**（与语料内容无关的数学/定义）：无自环 ⇒ 去重后边数仍是 22 ⇒ Σdeg = 2|E|
      = 44（握手引理）⇒ BFS 从 Kether 可达全部十球。任何一条被破坏都说明这张图画不出来。
    * **现状围栏**：逐点度的多重集 ``[3,3,4,4,4,4,4,5,5,8]``。Tiphareth(6) 度为 8 是
      公版事实（它是十字汇聚点），其余九个度数按交付现状钉；改一条边的端点会同时动到
      两个度数，这条就是提醒那是显式改动。复测：
      ``pytest tests/golden/test_kabbalah_golden.py -k simple_connected``（多重集写在本
      函数的断言里，逐点度由 `edges` 现算，不从任何表读）。
    """
    tree = build_tree()
    edges = [(p.from_sephirah, p.to_sephirah) for p in tree.paths]
    assert len(edges) == tree.path_count == 22
    assert all(a != b for a, b in edges), "路径不许连接同一原质（自环）"
    assert len({frozenset(edge) for edge in edges}) == 22, "同一无向边不许出现两次"

    degrees = {number: 0 for number in range(1, 11)}
    adjacency = {number: set() for number in range(1, 11)}
    for a, b in edges:
        degrees[a] += 1
        degrees[b] += 1
        adjacency[a].add(b)
        adjacency[b].add(a)
    assert sum(degrees.values()) == 2 * len(edges) == 44
    assert all(degree >= 1 for degree in degrees.values()), "十原质不许有孤点"
    assert sorted(degrees.values()) == [3, 3, 4, 4, 4, 4, 4, 5, 5, 8]
    assert degrees[6] == max(degrees.values()) == 8, "Tiphareth 是最大度节点"

    seen = {1}
    stack = [1]
    while stack:
        for nxt in adjacency[stack.pop()]:
            if nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    assert seen == set(range(1, 11)), "路径图必须连通"


def test_pillar_and_world_labels_agree_with_the_rendered_geometry() -> None:
    """判据 ④：柱名/界名（标签）与 x/y（渲染坐标）是两个独立字段，必须互证。

    今天的测一次都没看过 ``x``/``y``，而前端整棵树的 SVG 布局就靠它们：标签写「慈悲之柱」
    却把节点画到左边，页面与出处卡当场自相矛盾，测却全绿。
    实测样本（复测：``pytest tests/golden/test_kabbalah_golden.py -k pillar_and_world``；
    2026-09-27）：mercy 三点的 ``x`` 全为 0.84、severity 全为 0.16、equilibrium 全为 0.5。
    """
    tree = build_tree()
    nodes = tree.sephiroth
    by_pillar: dict[str, set[int]] = {}
    for node in nodes:
        by_pillar.setdefault(node.pillar, set()).add(node.number)
    assert by_pillar == {"equilibrium": {1, 6, 9, 10}, "mercy": {2, 4, 7}, "severity": {3, 5, 8}}
    assert all(node.x > 0.5 for node in nodes if node.pillar == "mercy")
    assert all(node.x < 0.5 for node in nodes if node.pillar == "severity")
    assert all(node.x == 0.5 for node in nodes if node.pillar == "equilibrium")
    # 标签也必须在同一份响应里对得上：`pillar_name_zh` 是 `pillars` 表按 id 查出来的那一个。
    printed_pillars = {pillar.id: pillar.name_zh for pillar in tree.pillars}
    assert all(node.pillar_name_zh == printed_pillars[node.pillar] for node in nodes)

    # 四界按 y 单调降落：从上到下读必须是 atziluth×3 → bria×3 → yetzirah×3 → assiah×1，
    # 一次都不许交错；`world_name_zh` 在 `worlds` 清单里的位次也得等于该界的界次。
    ordered = sorted(nodes, key=lambda node: (node.y, node.number))
    assert [node.world for node in ordered] == (
        ["atziluth"] * 3 + ["bria"] * 3 + ["yetzirah"] * 3 + ["assiah"]
    )
    assert [node.y for node in ordered] == sorted(node.y for node in nodes)
    assert len(tree.worlds) == 4
    assert [node.world_name_zh for node in ordered] == [
        tree.worlds[rank] for rank in [0, 0, 0, 1, 1, 1, 2, 2, 2, 3]
    ]


def test_daath_is_the_only_veiled_node_and_carries_no_path() -> None:
    """判据 ⑤：Daath 有其位而无其数，且 22 条路径的端点里没有它（度为 0）。

    既有的 ``test_daath_is_the_hidden_node`` 只看了 ``number``/``is_hidden`` 两个标量。
    「零路径」是深渊节点的定义性事实（它有位置、无质），也是将来真给 Daath 连边时必须
    显式来改测的地方 —— 今天连一条边都装配不出来：``_path_node`` 反查
    ``get_sephirah(0)`` 直接 ``KeyError``（变异探针实测，2026-09-27），所以那是一次连
    引擎一起动的契约改动，不是补一行语料。
    """
    tree = build_tree()
    daath = tree.daath
    assert daath is not None
    assert daath.number == 0 and daath.is_hidden is True
    assert tree.sephirah_count == len(tree.sephiroth) == 10, "隐节点不占十原质之数"
    assert daath.id not in {node.id for node in tree.sephiroth}

    endpoints = {p.from_sephirah for p in tree.paths} | {p.to_sephirah for p in tree.paths}
    assert endpoints == set(range(1, 11)), "0（Daath）不许出现在任何路径端点上"
    assert not [node for node in tree.sephiroth if node.is_hidden], "隐节点只有 Daath 一个"

    # 位置：落在中柱上，且悬在 Kether 与 Tiphareth 之间的深渊里。
    kether, tiphareth = tree.sephiroth[0], tree.sephiroth[5]
    assert daath.pillar == "equilibrium" and daath.x == 0.5
    assert kether.y < daath.y < tiphareth.y
    assert daath.pillar_name_zh == {p.id: p.name_zh for p in tree.pillars}[daath.pillar]


def test_gematria_skips_non_latin_characters_visibly_and_adds_nothing() -> None:
    """判据 ⑥：跳字必须可见（可复原），且跳过与否不得改变称量结果。

    计划原文要的是「静默跳过不行，跳过不得与『值为 0』同形」。可及手段是把 ``text``
    （原样回显的入参）与 ``normalized``/``breakdown`` 相减：负空间就是被跳过的那些字符，
    它们一个都不许出现在被称量的字母里。三型输入的 ordinal 全部手算：
    ``LIGHT`` = 12+9+7+8+20 = 56、``L!I@G#H%T`` 同 56、``Li Wei 2024 · 张伟``
    只剩 LIWEI = 12+9+23+5+9 = 58。
    ``digital_root`` 折的是 **ordinal**（1+((n−1) mod 9)，与「十进制各位递归求和到一位」
    同值），``english_reduction`` 是逐字母数字根之和 —— 它是另一个量，不是数根的中间步骤。
    """
    cases = {
        "LIGHT": ("LIGHT", 12 + 9 + 7 + 8 + 20, 3 + 9 + 7 + 8 + 2, 2),
        "L!I@G#H%T": ("LIGHT", 12 + 9 + 7 + 8 + 20, 3 + 9 + 7 + 8 + 2, 2),
        "Li Wei 2024 · 张伟": ("LIWEI", 12 + 9 + 23 + 5 + 9, 3 + 9 + 5 + 5 + 9, 4),
    }
    for text, (normalized, spelled_out, folded, root) in cases.items():
        reading = compute_gematria(text)
        assert reading.text == text, "入参原样回显：跳过了什么，diff 一下就知道"
        assert reading.normalized == normalized
        assert [item.letter for item in reading.breakdown] == list(normalized)
        assert reading.english_ordinal == spelled_out
        assert reading.english_ordinal == sum(item.ordinal for item in reading.breakdown)
        assert reading.english_reduction == folded
        assert reading.english_reduction == sum(item.reduction for item in reading.breakdown)
        assert reading.digital_root == root == 1 + ((reading.english_ordinal - 1) % 9)
        skipped = [ch for ch in text if not (ch.isascii() and ch.isalpha())]
        # 每一个字符要么被称量、要么被跳过：不增不减，才谈得上「跳过是可见的」。
        assert len(skipped) == len(text) - len(normalized)
        for ch in skipped:
            assert ch not in reading.normalized
            assert ch not in "".join(item.letter for item in reading.breakdown)
        assert reading.sephirah.number == ((reading.english_ordinal - 1) % 10) + 1
        assert reading.path.number == ((reading.english_ordinal - 1) % 22) + 11

    # 三型里的两型确实带被跳过的字符（否则上面那句 diff 就是测空气）：复测
    # `python -c "print(len('Li Wei 2024 · 张伟'), len('L!I@G#H%T'), len('LIGHT'))"` → `16 9 5`。
    assert len("Li Wei 2024 · 张伟") == 16
    assert len("L!I@G#H%T") == 9
    assert len(compute_gematria("Li Wei 2024 · 张伟").normalized) == 5
    assert len(compute_gematria("L!I@G#H%T").normalized) == 5
    assert len("LIGHT") == len(compute_gematria("LIGHT").normalized) == 5

    # 装饰与否同值：punct/CJK 加进来只是被跳过，一个数也不改变。
    bare, decorated = compute_gematria("LIWEI"), compute_gematria("Li Wei 2024 · 张伟")
    assert (bare.english_ordinal, bare.english_reduction, bare.digital_root) == (
        decorated.english_ordinal,
        decorated.english_reduction,
        decorated.digital_root,
    )
    # 折算法在响应文案里印着（`GEMATRIA_NOTE` → provenance.note），数据必须兑。
    assert "mod 10" in decorated.provenance.note and "mod 22" in decorated.provenance.note


def test_the_english_ordinal_scale_runs_from_a_equals_1_to_z_equals_26() -> None:
    """判据 ⑥ 的算术底：A=1…Z=26 ⇒ 整副字母表 351 = 26×27/2，逐位数字根 126。

    351 与 126 都不从仓内任何表读：前者是等差数列求和，后者是
    (1+…+9)×2 + (1+…+8) = 45+45+36。这是本包除图论那条之外唯一纯算术的外部锚，
    它判的是 ``LetterValue.ordinal``/``reduction`` 两列的定义本身。
    """
    reading = compute_gematria(string.ascii_lowercase)
    assert reading.normalized == string.ascii_uppercase
    assert [(item.letter, item.ordinal) for item in reading.breakdown] == [
        (char, index) for index, char in enumerate(string.ascii_uppercase, start=1)
    ]
    assert reading.english_ordinal == 26 * 27 // 2 == 351
    assert [item.reduction for item in reading.breakdown] == [
        1 + ((ordinal - 1) % 9) for ordinal in range(1, 27)
    ]
    assert reading.english_reduction == 45 + 45 + 36 == 126
    assert reading.digital_root == 9


def test_a_word_without_latin_letters_raises_instead_of_weighing_zero() -> None:
    """判据 ⑥ 的另一半：纯 CJK 在引擎侧就是抛错，不是一份零值命盘（AGENTS §4 字符集归引擎）。

    既有 ``test_gematria_rejects_text_without_latin_letters`` 从端点打的是 ``"12345"``
    （纯数字）；汉字这条是不同的输入形状 —— 它过得了 pydantic 的长度校验，只有引擎知道
    「A=1…Z=26 定义在拉丁字母表上」。端点侧的同一形状测在 ``tests/test_kabbalah_api.py``。
    """
    with pytest.raises(GematriaInputError) as excinfo:
        compute_gematria("张伟")
    assert excinfo.value.code == "gematria_no_latin_letters"
    assert excinfo.value.status_code == 422
    assert excinfo.value.message
