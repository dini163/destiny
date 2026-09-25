"""端点契约（spec §9.4）：200 形状、`deck_size` 随开关、无 `score` 与无百分号、
域错误 422、长度归 pydantic。

抽牌的性质测在 `tests/test_runes.py`，语料不变量在 `tests/content/`，外部锚点在
`tests/golden/`；本模块只管「HTTP 这一层有没有把引擎抽出的东西如实递出去」。故这里
一律断言 JSON，不 import 引擎函数 —— 只 import 语料的表名与牌阵，因为「响应声称引了
哪几张表」「这一阵该落几枚」正是契约的一部分。

三条守卫值得单说：

* **无 `score`、无百分号**（决策 6/7）：设计稿在这一页印了五个百分比。卢恩铸石不吃
  出生时间与地点，没有任何输入可以推出那类数字。这类字段日后极可能被顺手加回来，
  所以这里递归扫整棵响应树，键名与字符串值都扫，而不是只看顶层。
* **`provenance.tables` 正好两张**：多列一张等于让本端点声称引了它没读的书。
* **字形逐枚对回 Unicode**：出处卡印「码位锚点」供读者自查。若传输弄坏了一个字符，
  页面上就是一枚错符文，而这正是设计稿在本页犯过四次的错。
"""

import unicodedata

import pytest
from fastapi.testclient import TestClient

from app.content import CONTENT_VERSION, RUNE_CONTENT_SOURCES
from app.content.rune_spreads import SPREAD_IDS, SPREADS

URL = "/api/v1/runes/cast"

#: 只给牌阵，其余走 spec 的缺省（关空白符、允许逆位、无所问）。
PAYLOAD: dict[str, object] = {"spread_id": "three"}

#: 手写而不从 `RuneCastResponse.model_fields` 取：从模型取会让这条对「悄悄多了一个
#: 字段」毫无感觉，而锁死契约面正是它的用途 —— 加字段应当是一次显式改动。
TOP_LEVEL_KEYS = {
    "spread_id", "spread_name", "spread_name_zh", "spread_description", "question",
    "stones", "drawn_keys", "allow_reversed", "include_wyrd", "aett_balance",
    "synthesis", "shadow_counsel", "reversible_note", "codex", "provenance",
}

STONE_KEYS = {
    "position_index", "position_key", "position_label", "position_label_zh",
    "position_meaning", "order", "key", "glyph", "name", "name_zh", "transliteration",
    "name_meaning", "name_meaning_uncertain", "aett", "aett_zh", "reversible",
    "is_wyrd", "orientation", "keywords", "meaning", "source",
}


def _post(client: TestClient, **overrides: object):
    return client.post(URL, json={**PAYLOAD, **overrides})


def _walk_keys(node: object) -> set[str]:
    """递归收集响应里出现过的全部字典键，用来扫「不许出现的字段名」。"""
    if isinstance(node, dict):
        return set(node) | {key for value in node.values() for key in _walk_keys(value)}
    if isinstance(node, list):
        return {key for value in node for key in _walk_keys(value)}
    return set()


def _walk_strings(node: object) -> list[str]:
    """递归收集全部字符串值：百分号与假技术名词可能藏在文案里，不只在键名上。"""
    if isinstance(node, str):
        return [node]
    if isinstance(node, dict):
        return [text for value in node.values() for text in _walk_strings(value)]
    if isinstance(node, list):
        return [text for value in node for text in _walk_strings(value)]
    return []


# ------------------------------------------------------------------ 200 形状


@pytest.mark.parametrize("spread_id", SPREAD_IDS)
def test_the_cast_comes_back_whole_for_every_spread(
    client: TestClient, spread_id: str
) -> None:
    response = _post(client, spread_id=spread_id)
    assert response.status_code == 200
    body = response.json()
    assert set(body) == TOP_LEVEL_KEYS
    assert body["spread_id"] == spread_id
    assert body["question"] is None
    size = SPREADS[spread_id].size
    assert len(body["stones"]) == size
    assert body["drawn_keys"] == [stone["key"] for stone in body["stones"]]
    assert len(set(body["drawn_keys"])) == size  # sample() 不放回


def test_each_stone_carries_both_its_position_and_its_rune(client: TestClient) -> None:
    """前端不重算任何东西，故位次四件套与符文身份都得整份递到浏览器。"""
    stone = _post(client).json()["stones"][0]
    assert set(stone) == STONE_KEYS
    assert stone["orientation"] in {"upright", "reversed"}
    assert stone["keywords"] and stone["meaning"] and stone["source"]
    assert stone["position_label"] and stone["position_label_zh"]
    assert stone["position_meaning"]


def test_symmetric_stones_never_come_back_reversed_over_http(client: TestClient) -> None:
    """引擎那条结构守卫在 HTTP 层复查一次：对称符不可能带着逆位徽标出现在页面上。"""
    for _ in range(30):
        for stone in _post(client, spread_id="five").json()["stones"]:
            if not stone["reversible"]:
                assert stone["orientation"] == "upright", stone["name"]


# ------------------------------------------------------------------ 空白符开关


@pytest.mark.parametrize("include_wyrd,expected", [(False, 24), (True, 25)])
def test_deck_size_follows_the_wyrd_toggle(
    client: TestClient, include_wyrd: bool, expected: int
) -> None:
    body = _post(client, spread_id="five", include_wyrd=include_wyrd).json()
    assert body["provenance"]["deck_size"] == expected
    assert body["include_wyrd"] is include_wyrd
    if not include_wyrd:
        assert "wyrd" not in body["drawn_keys"]


def test_the_codex_is_25_entries_whichever_way_the_toggle_sits(client: TestClient) -> None:
    """决策 25：开关管的是抽不抽得着空白符，不是它在不在典里。"""
    for include_wyrd in (False, True):
        codex = _post(client, include_wyrd=include_wyrd).json()["codex"]
        assert codex["total"] == 25
        assert [len(group["runes"]) for group in codex["aettir"]] == [8, 8, 8]
        assert codex["wyrd"]["is_wyrd"] is True
        assert codex["wyrd"]["glyph"] == ""


def test_glyphs_survive_the_round_trip_and_still_match_their_codepoints(
    client: TestClient,
) -> None:
    """把 §8 的码位锚点从语料一路验到浏览器收到的那份 JSON。

    设计稿在本页印错过四枚字形，而肉眼在页面上看不出来 —— 只有拿码位与 Unicode
    官方名互证才算数。空白符没有字形，故它的这两个字段必须是 `null` 而不是编一个。
    """
    codex = _post(client, include_wyrd=True).json()["codex"]
    entries = [rune for group in codex["aettir"] for rune in group["runes"]]
    entries.append(codex["wyrd"])
    assert len(entries) == 25

    real = [rune for rune in entries if not rune["is_wyrd"]]
    assert len(real) == 24
    for rune in real:
        assert rune["glyph"] == chr(rune["codepoint"]), rune["key"]
        assert rune["unicode_name"] == unicodedata.name(rune["glyph"]), rune["key"]

    wyrd = codex["wyrd"]
    assert wyrd["codepoint"] is None and wyrd["unicode_name"] is None


# ------------------------------------------------------------------ 决策 6 / 7 守卫


def test_there_is_no_score_and_no_percentage_anywhere_in_the_response(
    client: TestClient,
) -> None:
    response = _post(client, spread_id="five", include_wyrd=True)
    body = response.json()
    keys = _walk_keys(body)
    assert not (keys & {"score", "total_score", "percentage", "percent", "rating", "ratio"})
    # 比只查键名更强的一层：文案里也不许留下百分号（半角与全角都算）。
    assert "%" not in response.text and "％" not in response.text
    assert not [text for text in _walk_strings(body) if text.rstrip().endswith(("%", "％"))]


def test_the_openapi_schema_does_not_advertise_a_score(client: TestClient) -> None:
    """从 `/openapi.json` 那一侧再守一次：前端照 schema 生成类型，schema 里有就会长出来。"""
    spec = client.get("/openapi.json").json()
    assert URL in spec["paths"]
    schema = spec["components"]["schemas"]["RuneCastResponse"]
    assert "score" not in schema["properties"]
    assert set(schema["properties"]) == TOP_LEVEL_KEYS


# ------------------------------------------------------------------ 溯源


def test_provenance_lists_exactly_the_tables_this_endpoint_reads(client: TestClient) -> None:
    provenance = _post(client).json()["provenance"]
    assert [table["name"] for table in provenance["tables"]] == [
        module for module, _ in RUNE_CONTENT_SOURCES
    ]
    for table, (_, source) in zip(provenance["tables"], RUNE_CONTENT_SOURCES, strict=True):
        assert table["source"] == source
        # 本端点无历法库、无星历表，故版本取本仓语料的滚动版本。
        assert table["version"] == CONTENT_VERSION
    assert provenance["rng"] == "secrets"
    assert provenance["badge"] == "#RUNES-FUTHARK"
    assert provenance["method"] and provenance["naming_note"] and provenance["wyrd_note"]


def test_provenance_never_repeats_the_mockups_invented_claims(client: TestClient) -> None:
    """决策 18/19：徽标只印方法标识，熵源如实说 `secrets`。

    设计稿写「量子混沌伪随机熵源」与档案号 `-2026-N09`：前者是假技术，后者每人不同
    又无推导依据，只能靠编。故这两样在整份响应里连一个字都不许留下。
    """
    text = "".join(_walk_strings(_post(client).json()))
    for banned in ("量子", "quantum", "2026-N09"):
        assert banned not in text, banned


# ------------------------------------------------------------------ 422


@pytest.mark.parametrize("bad_id", ["celtic_cross", "yggdrasil", "", "THREE"])
def test_an_unknown_spread_id_returns_the_shared_error_shape(
    client: TestClient, bad_id: str
) -> None:
    """域错误走统一形状（与塔罗同一条路径），不是 FastAPI 的 `detail`。"""
    response = _post(client, spread_id=bad_id)
    assert response.status_code == 422
    body = response.json()
    assert "detail" not in body
    assert body["error"]["code"] == "unsupported_method"
    assert body["error"]["message"]


def test_question_length_is_pydantic_validation_not_a_domain_error(
    client: TestClient,
) -> None:
    """长度归 pydantic（回 FastAPI 的 `detail` 形状），分工同 `numerology.py`。"""
    response = _post(client, question="问" * 121)
    assert response.status_code == 422
    body = response.json()
    assert "detail" in body and "error" not in body


def test_a_question_at_the_limit_is_accepted_and_echoed(client: TestClient) -> None:
    """边界那一侧也要验：120 字正好过，且原样回显、并领起直读那句。"""
    question = "问" * 120
    body = _post(client, question=question).json()
    assert body["question"] == question
    assert question in body["synthesis"]
