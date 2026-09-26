"""端点契约（Task 9A 判据 ⑦）：`GET /tree` 零加工、契约面不缺块、文案含其所算之数、
两类 422 各回各的形状。

结构与算术的性质测在 ``tests/golden/test_kabbalah_golden.py``（那里锚的是公版表与
图论/数论事实）；本模块只管「HTTP 这一层有没有把引擎装配好的东西原样递到浏览器」。
与 ``test_runes_api.py``/``test_numerology_api.py`` 不同的是，这里**刻意 import 引擎**：
``GET /tree`` 没有输入，唯一可测的就是「交付面 == 装配面」，比对 ``build_tree()`` 才是
这条判据的本体；字段清单（``TOP_LEVEL_KEYS``）仍然手写而不从 ``model_fields`` 取，
理由同那两个文件 —— 从模型取就对「悄悄少了一个字段」毫无感觉。

三条值得单说：

* **逐字相等**：``GET /tree`` 是这棵树唯一的交付面，今天的端点测只数了四个顶层数字
  （``sephirah_count``/``path_count`` 与两个长度）。路由器哪天漏装一块 —— ``worlds``、
  ``daath``、节点上的 ``color`` —— 页面就少画一片，而那条测照样绿。
* **`synthesis` 含三个数字字面量**：「响应自己印的字面 ⊆ 响应自己给的数据」那一族在
  HTTP 层的落点，防 ``engines/kabbalah.py`` 里那串 f-string 与字段脱钩。
* **两种 422 不是一种**：``GematriaRequest.text`` 的 `min_length=1, max_length=64`
  （``schemas/kabbalah.py``）坏在字段自身，走 FastAPI 默认 ``detail`` 形状；一个拉丁
  字母也没有坏在引擎前提，走 ``{error: {code, message}}`` 信封（AGENTS §4 的分工）。
  前端一律读 ``error.code``，把二者混成一份 ``detail`` 就等于让页面失去可分支的码。
"""

import re

from fastapi.testclient import TestClient

from app.engines.kabbalah import build_tree

TREE_URL = "/api/v1/kabbalah/tree"
GEMATRIA_URL = "/api/v1/kabbalah/gematria"

#: 手写而不从 `KabbalahTree.model_fields` 取：加/删顶层字段应当是一次显式改动。
#: 复测：`pytest tests/test_kabbalah_api.py -k byte_for_byte` —— 这个集合与
#: `build_tree().model_dump()` 的键集在同一条断言里比，两边一漂移就红。
TOP_LEVEL_KEYS = {
    "pillars",
    "worlds",
    "sephiroth",
    "daath",
    "paths",
    "sephirah_count",
    "path_count",
    "provenance",
}

#: 金版（King-Scale）色在暗底上以 6 位十六进制交付，前端直接填进 SVG，不做二次解析。
HEX_COLOUR = re.compile(r"#[0-9a-fA-F]{6}")


def test_get_tree_hands_the_assembled_map_over_byte_for_byte(client: TestClient) -> None:
    """判据 ⑦：路由是薄装配，交付的 JSON 必须逐字等于引擎的 `model_dump()`。

    射程要说清：这条只测「HTTP 层 vs 装配层」的分歧 —— 引擎自己改了内容，两边一起动，
    它不会红（那是 golden 那六条判据的活）。它红的是路由器另拼一份模型、漏装一块、
    或日后加一层缓存把交付面与装配面脱钩。变异探针实测：让 `GET /tree` 少返回
    `worlds`，这条立刻红（2026-09-27）。
    """
    response = client.get(TREE_URL)
    assert response.status_code == 200
    body = response.json()
    assert set(body) == TOP_LEVEL_KEYS
    assert body == build_tree().model_dump()
    # 顶层计数与数组长度在同一份 JSON 里自证（前端按 count 铺网格，按数组取节点）。
    assert body["sephirah_count"] == len(body["sephiroth"]) == 10
    assert body["path_count"] == len(body["paths"]) == 22
    assert len(body["worlds"]) == 4 and all(isinstance(word, str) for word in body["worlds"])
    assert body["daath"]["number"] == 0 and body["daath"]["is_hidden"] is True


def test_the_three_pillars_are_printed_with_their_sides(client: TestClient) -> None:
    """`pillars` 是页面图例的来源：三条的 id / 中文名 / 英文名 / `side` 逐条整体对拍。

    右 = 慈悲（Jachin）、左 = 严厉（Boaz）、中 = 平衡（Middle），照的是
    ``content/kabbalah.py`` 的 `PILLARS` 表；顺序本身也是交付现状（图例按
    中柱 → 右柱 → 左柱 印）。`virtue` 是一句人读的品德描述文案，改动它不该红契约，
    故只断非空，不逐字钉。
    """
    pillars = client.get(TREE_URL).json()["pillars"]
    rows = [(p["id"], p["name_zh"], p["name_en"], p["side"]) for p in pillars]
    assert rows == [
        ("equilibrium", "中柱·平衡", "Middle", "middle"),
        ("mercy", "慈悲之柱", "Jachin", "right"),
        ("severity", "严厉之柱", "Boaz", "left"),
    ]
    assert all(pillar["virtue"] for pillar in pillars)


def test_every_sphere_including_daath_arrives_with_a_hex_colour(client: TestClient) -> None:
    """11 个节点（十原质 + 隐的 Daath）的 `color` 都得是 6 位十六进制。

    原子的失败形状是「字段在，值不是 CSS 认的颜色」—— 页面会画出一块无色节点而不报错，
    故这里扫全部 11 个，而不是抽样。实测样本：`#3FBF6F`（Netzach）、`#4B5BD6`（Chesed）、
    `#5B3A6E`（Binah）、`#C9C3A0`（Daath）。
    最后那句「11 枚颜色互不相同」是**现状围栏，不是契约**（同 golden 判据 ③ 的度数多重集）：
    合法换配色、或让两个原质复用同一色号，都会红在一个端点契约测里 —— 改色号的人请连同那一
    行一起改，别把它当引擎缺陷修。复测：``pytest tests/test_kabbalah_api.py -k hex_colour``
    绿 = 11 点仍是 11 色（2026-09-27 实测；上面四枚样本就是这 11 个值里的四枚）。
    """
    body = client.get(TREE_URL).json()
    nodes = body["sephiroth"] + [body["daath"]]
    assert len(nodes) == 11
    for node in nodes:
        assert HEX_COLOUR.fullmatch(node["color"]), node["id"]
    assert len({node["color"] for node in nodes}) == 11, "十一个球的颜色互不相同"


def test_gematria_synthesis_prints_the_numbers_it_computed(client: TestClient) -> None:
    """`synthesis` 里的字面必须与同一份响应里的字段值同形（LIGHT = 56 / 29 / 2）。"""
    response = client.post(GEMATRIA_URL, json={"text": "LIGHT"})
    assert response.status_code == 200
    body = response.json()
    assert (body["normalized"], body["english_ordinal"], body["english_reduction"],
            body["digital_root"]) == ("LIGHT", 56, 29, 2)
    synthesis = body["synthesis"]
    assert body["normalized"] in synthesis
    for value in (body["english_ordinal"], body["english_reduction"], body["digital_root"]):
        assert str(value) in synthesis
    # 折算法则印在出处卡上，落点就得是它算出来的那两个号：56 → 原质 6 / 路径 22。
    assert body["sephirah"]["number"] == ((body["english_ordinal"] - 1) % 10) + 1 == 6
    assert body["path"]["number"] == ((body["english_ordinal"] - 1) % 22) + 11 == 22
    assert body["path"]["tarot_numeral"] == "XI", "LIGHT 折到正义，正是出处卡印的那一制"


def test_a_word_without_latin_letters_is_an_engine_error_envelope(client: TestClient) -> None:
    """汉字与纯符号过得了 pydantic 的长度校验，坏的是只有引擎知道的那条字母表前提。

    ``"12345"`` 由既有 golden 覆盖；``"张伟"`` 与「符号 + 空格」是端点侧的新形状：后者
    连 ``min_length=1`` 都骗不过它没有字母这一事实，却仍然是一个非空字符串。
    """
    for text in ("张伟", "· 12 ·"):
        response = client.post(GEMATRIA_URL, json={"text": text})
        assert response.status_code == 422, text
        body = response.json()
        assert "detail" not in body, text
        assert body["error"]["code"] == "gematria_no_latin_letters", text
        assert body["error"]["message"], text


def test_text_length_bounds_are_pydantic_validation_not_domain_errors(client: TestClient) -> None:
    """`text` 的 1..64 是字段自身的约束 → FastAPI 默认 `detail`，不是 `{error}` 信封。

    约束住在 ``schemas/kabbalah.py`` 的 ``GematriaRequest.text``（``min_length=1``、
    ``max_length=64``，2026-09-27 复核）：复测就是本函数 ——
    ``pytest tests/test_kabbalah_api.py -k text_length_bounds``。65 字与空串各回一份只有
    ``detail`` 的 422（``type`` 分别是 ``string_too_long`` / ``string_too_short``），
    64 字正常 200。与雷诺曼 ``question``（120 字）是同一条分工：长度归 pydantic，
    字符集归引擎（AGENTS §4）。
    """
    for text, expected_type in ((("A" * 65), "string_too_long"), ("", "string_too_short")):
        response = client.post(GEMATRIA_URL, json={"text": text})
        assert response.status_code == 422, len(text)
        body = response.json()
        assert "error" not in body, text
        assert [item["type"] for item in body["detail"]] == [expected_type], text
    at_the_limit = client.post(GEMATRIA_URL, json={"text": "A" * 64})
    assert at_the_limit.status_code == 200
    assert at_the_limit.json()["normalized"] == "A" * 64
