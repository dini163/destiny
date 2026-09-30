"""梅花端点契约（Task 6 Step 4）：顶层与逐层键集**手写**、报数入参归引擎（400）、出处块五张表齐。

卦象的**对错**测在 `tests/golden/test_meihua_golden.py`（十五张手推锚卦 + 报数护栏），
表的**齐不齐**测在 `tests/content/test_meihua_corpus.py`；本模块只管 HTTP 这一层有没有把
引擎算好的盘如实、按契约递出去 —— 故一律断言 JSON，不 import 引擎函数（分派同
`tests/test_ziwei_api.py` 与 `tests/test_qimen_api.py`）。

值得单说的四道门：

* **状态码是 400，不是 422**：`InvalidCastInputError` 用 `DestinyError` 基类的默认 400
  （`app/core/errors.py:10`），而报数护栏正是它的地盘 —— 「1 至 3 个正整数」坏的是
  `numbers` 与 `method` 之间的**关系**（`method="number"` 时才算必填），每个字段单看都合法，
  故归引擎不归 pydantic（AGENTS 第 4 条）。对照门是 `method="coin"` → 422 `enum`。
* **出处块自 2026-09-30 起在场**（多系统白话计划 Task 7）：`MeihuaCast.provenance` 与
  `plain_summary` 是必填两格，`tables` 逐字来自 `MEIHUA_CONTENT_SOURCES` 的五张表。此前本
  模块把「没有 provenance」钉成顶层键集的一部分并记为出处缺口 finding——缺口已闭合，
  键集钉的是**在场且齐**：少一格、多一格、两份抄本不一致，三条都红。
* **无随机**：AGENTS 第 5 条的 CSPRNG 铁律只管抽签类引擎（tarot/lenormand/runes/zhouyi），
  梅花是确定性算术（报数 ÷8、÷6 与农历数），所以这里钉的是「同入参两次逐字节相同 +
  换报数必换盘」，后者同时排除「端点其实回了一张常量盘」这种假绿。
* **时区偏移按墙钟读取**：与奇门同一条 finding，用单数法演示 —— 下卦与动爻都加时辰序，
  偏移一丢就是整盘换了卦。

复测本文件测数：`cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m pytest
tests/test_meihua_api.py -o addopts=""` → 33 passed（2026-09-30 实录：域错误六条 + pydantic 六条
参数化 + 极值日期四条参数化，其余单条；出处块那条单列，故 32 加一）。
"""

import re

import pytest
from fastapi.testclient import TestClient

URL = "/api/v1/meihua/cast"

#: 参考盘：报数 [7,3] 于 2024-05-15 10:30（巳时）→ 山火贲，动爻四，体离用艮（golden 主锚）。
PAYLOAD: dict[str, object] = {
    "method": "number",
    "numbers": [7, 3],
    "cast_time": "2024-05-15T10:30:00",
}

KEY_RE = re.compile(r"^[a-z][a-z0-9_]*$")

# ------------------------------------------------------------------ 契约面（手写）

TOP_LEVEL_KEYS = {
    "method", "question", "cast_time", "derivation",
    "ben", "hu", "bian", "moving_position",
    "ti", "yong", "tiyong", "wangshuai",
    "hu_analysis", "bian_analysis",
    "score", "score_factors", "verdict", "summary", "engine",
    "plain_summary", "provenance",
}

DERIVATION_KEYS = {"upper_number", "lower_number", "moving_position", "formula", "inputs"}
HEXAGRAM_KEYS = {"number", "name_zh", "full_name_zh", "symbol", "lines", "lower", "upper", "gua_ci"}
TRIGRAM_KEYS = {"key", "name_zh", "symbol", "nature_zh", "element", "position"}
PARTY_KEYS = {"role", "trigram", "leixiang", "wangshuai", "wangshuai_text"}
VERDICT_KEYS = {"relation", "relation_zh", "verdict", "grade", "text"}
WANGSHUAI_KEYS = {"month_zhi", "season_zh", "commanding_element"}
FACTOR_KEYS = {"label", "detail", "delta"}
PROVENANCE_KEYS = {"engine", "method", "tables"}
PROVENANCE_TABLE_KEYS = {"name", "version", "source"}   # 镜像 schemas/common.py:ProvenanceTable

RELATION_KEYS = {"yong_sheng_ti", "bi_he", "ti_ke_yong", "ti_sheng_yong", "yong_ke_ti"}
WANGSHUAI_STATES = {"旺", "相", "休", "囚", "死"}
BANDS = {"上吉", "吉", "小吉", "中平", "小凶", "凶"}

# ------------------------------------------------------------------ 前端声明（手抄）
# 照 `frontend/src/types/meihua.ts` 的响应侧 interface 逐字重抄；不在后端测试里读前端树，
# 两份各抄一次才有门（抄写约定同 `tests/test_ziwei_api.py:60-82`）。出处块那两层的本子照
# 本模块 `MeihuaProvenance` 与 `schemas/common.py:ProvenanceTable` 的形状抄，前端落地时同名。

FRONTEND_CAST_KEYS = {
    "method", "question", "cast_time", "derivation",
    "ben", "hu", "bian", "moving_position",
    "ti", "yong", "tiyong", "wangshuai",
    "hu_analysis", "bian_analysis",
    "score", "score_factors", "verdict", "summary", "engine",
    "plain_summary", "provenance",
}

FRONTEND_DERIVATION_KEYS = {"upper_number", "lower_number", "moving_position", "formula", "inputs"}
FRONTEND_HEXAGRAM_KEYS = {
    "number", "name_zh", "full_name_zh", "symbol", "lines", "lower", "upper", "gua_ci",
}
FRONTEND_TRIGRAM_KEYS = {"key", "name_zh", "symbol", "nature_zh", "element", "position"}
FRONTEND_PARTY_KEYS = {"role", "trigram", "leixiang", "wangshuai", "wangshuai_text"}
FRONTEND_VERDICT_KEYS = {"relation", "relation_zh", "verdict", "grade", "text"}
FRONTEND_WANGSHUAI_KEYS = {"month_zhi", "season_zh", "commanding_element"}
FRONTEND_FACTOR_KEYS = {"label", "detail", "delta"}
FRONTEND_PROVENANCE_KEYS = {"engine", "method", "tables"}
FRONTEND_PROVENANCE_TABLE_KEYS = {"name", "version", "source"}

KEY_LAYERS: list[tuple[str, set[str], set[str]]] = [
    ("derivation", DERIVATION_KEYS, FRONTEND_DERIVATION_KEYS),
    ("ben|hu|bian", HEXAGRAM_KEYS, FRONTEND_HEXAGRAM_KEYS),
    ("ben.lower|upper", TRIGRAM_KEYS, FRONTEND_TRIGRAM_KEYS),
    ("ti|yong", PARTY_KEYS, FRONTEND_PARTY_KEYS),
    ("tiyong", VERDICT_KEYS, FRONTEND_VERDICT_KEYS),
    ("wangshuai", WANGSHUAI_KEYS, FRONTEND_WANGSHUAI_KEYS),
    ("score_factors[]", FACTOR_KEYS, FRONTEND_FACTOR_KEYS),
    ("provenance", PROVENANCE_KEYS, FRONTEND_PROVENANCE_KEYS),
]


def _post(client: TestClient, **overrides: object):
    return client.post(URL, json={**PAYLOAD, **overrides})


def _walk_keys(node: object) -> set[str]:
    if isinstance(node, dict):
        return set(node) | {key for value in node.values() for key in _walk_keys(value)}
    if isinstance(node, list):
        return {key for item in node for key in _walk_keys(item)}
    return set()


# ------------------------------------------------------------------ 200 形状


def test_the_cast_comes_back_with_exactly_the_hand_written_contract(client: TestClient) -> None:
    response = _post(client)
    assert response.status_code == 200
    body = response.json()
    assert set(body) == TOP_LEVEL_KEYS
    assert len(TOP_LEVEL_KEYS) == 21  # 尺寸哨兵：抄漏一格上面那条相等就直接红，这条管的是两侧同时缩水
    assert body["engine"] == "meihua-tiyong"
    assert body["method"] == "number"
    assert body["question"] is None
    assert body["cast_time"] == "2024-05-15 10:30"
    # 参考盘的三卦与动爻（本卦#22、互#40、变#30、动爻四）——HTTP 层递出的就是锚点。
    assert [body[key]["number"] for key in ("ben", "hu", "bian")] == [22, 40, 30]
    assert body["moving_position"] == 4


def test_nested_objects_carry_exactly_their_declared_keys(client: TestClient) -> None:
    """算式、三卦、两体用、卦气、账本行七层对象的键集同样钉死。"""
    body = _post(client).json()
    assert set(body["derivation"]) == DERIVATION_KEYS
    for key in ("ben", "hu", "bian"):
        assert set(body[key]) == HEXAGRAM_KEYS, key
        assert set(body[key]["lower"]) == TRIGRAM_KEYS, key
        assert set(body[key]["upper"]) == TRIGRAM_KEYS, key
    for party in (body["ti"], body["yong"]):
        assert set(party) == PARTY_KEYS
        assert set(party["trigram"]) == TRIGRAM_KEYS
    assert set(body["tiyong"]) == VERDICT_KEYS
    assert set(body["wangshuai"]) == WANGSHUAI_KEYS
    for factor in body["score_factors"]:
        assert set(factor) == FACTOR_KEYS


def test_the_provenance_block_and_each_table_row_carry_exactly_the_declared_keys(
    client: TestClient
) -> None:
    """出处块三格与逐表三格的形状钉死；五张表的**名单**测在 golden，这里只管每格有什么。"""
    body = _post(client).json()
    assert set(body["provenance"]) == PROVENANCE_KEYS
    assert body["provenance"]["engine"] == "lunar-python"
    assert body["provenance"]["method"]
    for table in body["provenance"]["tables"]:
        assert set(table) == PROVENANCE_TABLE_KEYS


def test_the_three_hexagrams_share_one_shape_and_a_six_line_alphabet(client: TestClient) -> None:
    """本/互/变三卦同形：六爻自下而上、只有 0/1、文王序 1-64、卦符按序、卦辞非空。"""
    body = _post(client).json()
    for key in ("ben", "hu", "bian"):
        hexagram = body[key]
        assert len(hexagram["lines"]) == 6 and set(hexagram["lines"]) <= {0, 1}, key
        assert 1 <= hexagram["number"] <= 64, key
        assert hexagram["symbol"] == chr(0x4DC0 + hexagram["number"] - 1), key
        assert hexagram["name_zh"] and hexagram["full_name_zh"] and hexagram["gua_ci"], key
        assert hexagram["lower"]["position"] == "lower", key
        assert hexagram["upper"]["position"] == "upper", key
    moving = body["moving_position"] - 1
    ben_lines, bian_lines = body["ben"]["lines"], body["bian"]["lines"]
    assert ben_lines[moving] ^ 1 == bian_lines[moving]
    index = [i for i in range(6) if i != moving]
    assert [ben_lines[i] for i in index] == [bian_lines[i] for i in index]


def test_the_printed_arithmetic_uses_the_same_numbers_as_the_board(client: TestClient) -> None:
    """「透明算式」不许只印个样子：式子里的余数必须就是响应实际用的卦数与动爻。"""
    body = _post(client).json()
    derivation = body["derivation"]
    assert derivation["upper_number"] in range(1, 9)
    assert derivation["lower_number"] in range(1, 9)
    assert derivation["moving_position"] == body["moving_position"] in range(1, 7)
    assert f"余{derivation['upper_number']}为上卦" in derivation["formula"]
    assert f"余{derivation['lower_number']}为下卦" in derivation["formula"]
    assert f"余{derivation['moving_position']}为动爻" in derivation["formula"]
    assert "报数" in derivation["inputs"]


def test_the_ti_yong_parties_are_the_two_trigrams_of_the_primary_board(client: TestClient) -> None:
    """体与用必须是本卦的上下两画卦（各占一段）、角色成对，且旺衰与关系都在声明词表内。"""
    body = _post(client).json()
    assert (body["ti"]["role"], body["yong"]["role"]) == ("ti", "yong")
    positions = {body["ti"]["trigram"]["position"], body["yong"]["trigram"]["position"]}
    assert positions == {"lower", "upper"}
    ben = body["ben"]
    for party in (body["ti"], body["yong"]):
        trigram = party["trigram"]
        assert trigram in (ben["lower"], ben["upper"]), trigram["name_zh"]
        assert trigram["element"] in {"金", "木", "水", "火", "土"}
        assert party["wangshuai"] in WANGSHUAI_STATES, trigram["name_zh"]
        assert party["wangshuai_text"] and party["leixiang"].startswith(
            f"{trigram['name_zh']}为{trigram['nature_zh']}："
        )
    assert body["tiyong"]["relation"] in RELATION_KEYS
    assert body["tiyong"]["grade"] in {-2, -1, 1, 2}
    assert body["tiyong"]["text"]
    assert body["wangshuai"]["month_zhi"] in "子丑寅卯辰巳午未申酉戌亥"
    assert body["wangshuai"]["commanding_element"] in {"金", "木", "水", "火", "土"}
    assert body["hu_analysis"] and body["bian_analysis"] and body["summary"]


def test_the_ledger_is_four_lines_and_is_the_score(client: TestClient) -> None:
    """吉凶指数没有暗账：四本账按固定名目给出，`score` 恰为 50 加其和，档位只认六个名字。"""
    body = _post(client).json()
    factors = body["score_factors"]
    assert [f["label"] for f in factors] == ["体用生克", "卦气旺衰", "互卦(过程)", "变卦(结局)"]
    assert all(f["detail"] for f in factors)
    assert body["score"] == 50 + sum(f["delta"] for f in factors)
    assert 0 <= body["score"] <= 100
    assert body["verdict"] in BANDS


def test_the_response_is_snake_case_end_to_end(client: TestClient) -> None:
    """AGENTS 第 3 条：后端 JSON 全 snake_case，前端不重命名——一个驼峰键就是页面上的 undefined。"""
    keys = _walk_keys(_post(client).json())
    assert keys
    assert [key for key in keys if not KEY_RE.match(key)] == []


# ------------------------------------------------------------------ 400 归引擎 · 422 归 pydantic


@pytest.mark.parametrize(
    ("method", "numbers"),
    [
        ("number", None),          # 缺 numbers：字段单看合法，坏的是它与 method 的关系
        ("number", []),            # 空表
        ("number", [0]),           # 零不是正整数
        ("number", [7, 0]),        # 混在合法值里的零
        ("number", [-3]),          # 负数
        ("number", [1, 2, 3, 4]),  # 超出 1-3 个
    ],
    ids=["缺数", "空表", "单零", "双含零", "单负", "四数"],
)
def test_a_number_cast_the_engine_cannot_compute_is_a_400_domain_error(
    client: TestClient, method: str, numbers: list[int] | None
) -> None:
    """`InvalidCastInputError` 走基类默认 **400**（AGENTS 第 4 条：状态码按子类分，不是一律 422）。

    复测：`grep -n "class " app/core/errors.py` 与 `grep -n "status_code" app/core/errors.py`
    （2026-09-26 实录 8 个子类、5×422 / 2×400 / 1×500，本类在 400 那一侧）。信封形状是
    `{error:{code,message}}`，没有 `context` 就不许多一个键；`detail` 不得出现（那是 pydantic 的形状）。
    """
    response = _post(client, method=method, numbers=numbers)
    assert response.status_code == 400
    body = response.json()
    assert "detail" not in body
    assert set(body) == {"error"}
    assert set(body["error"]) == {"code", "message"}
    assert body["error"]["code"] == "invalid_cast_input"
    assert "正整数" in body["error"]["message"]


@pytest.mark.parametrize(
    ("overrides", "issue_type"),
    [
        ({"method": "coin"}, "enum"),
        ({"method": "TIME"}, "enum"),
        ({"numbers": ["七", "三"]}, "int_parsing"),
        ({"numbers": [7.5, 3]}, "int_from_float"),
        ({"numbers": "73"}, "list_type"),
        ({"cast_time": "2024-05-15T10:30:99"}, "datetime_from_date_parsing"),
    ],
    ids=["乱方法", "大写方法", "汉字数", "小数", "字符串当列表", "坏时刻"],
)
def test_a_field_that_cannot_pass_its_own_declaration_is_pydantic_validation(
    client: TestClient, overrides: dict[str, object], issue_type: str
) -> None:
    """字段自身的类型/枚举/长度问题一律 422 `detail`，绝不出信封（分工同 AGENTS 第 4 条）。"""
    response = _post(client, **overrides)
    assert response.status_code == 422
    body = response.json()
    assert "error" not in body
    assert body["detail"][0]["type"] == issue_type


def test_the_time_method_needs_no_numbers_at_all(client: TestClient) -> None:
    """`method="time"` 时 `numbers` 缺席是合法的：护栏只在 number 法上生效（关系的另一面）。"""
    body = _post(client, method="time", numbers=None).json()
    assert body["method"] == "time"
    assert "农历" in body["derivation"]["inputs"]
    assert body["derivation"]["upper_number"] in range(1, 9)


# ------------------------------------------------------------------ 极值日期（PRD §4.1 区间）


@pytest.mark.parametrize(
    "cast_time",
    ["1900-01-01T10:30:00", "2100-12-31T10:30:00", "1800-01-01T10:30:00", "2200-01-01T10:30:00"],
    ids=["区间起点", "区间终点", "区间前", "区间后"],
)
def test_every_parsable_datetime_returns_a_full_cast_never_an_envelope(
    client: TestClient, cast_time: str
) -> None:
    """梅花的时间法没有 `DestinyError` 可达路径：任何能解析的时刻都给整盘，绝不出信封。

    PRD §4.1 的支持区间是 1900-2100（端点两条），区间外的两条同样按盘给出 —— `lunar-python`
    在这个区间仍算得出农历四数，「越界」在这里不是错误而是如实计算。页面上的年份下拉只到
    1900..当前年（走查实录 128 项 = `----` + 2026..1900），故 2100 一条在 App 内不可达，
    只能在端点层钉（同 `tests/test_qimen_api.py::test_every_parsable_datetime_returns_a_full_board_never_an_envelope`）。
    """
    response = _post(client, method="time", numbers=None, cast_time=cast_time)
    assert response.status_code == 200
    body = response.json()
    assert "error" not in body and "detail" not in body
    assert body["cast_time"] == cast_time[:10] + " " + cast_time[11:16]
    assert all(1 <= body[key]["number"] <= 64 for key in ("ben", "hu", "bian"))
    assert body["moving_position"] in range(1, 7)
    assert body["derivation"]["upper_number"] in range(1, 9)
    assert body["derivation"]["lower_number"] in range(1, 9)
    assert len(body["score_factors"]) == 4
    assert body["score"] == 50 + sum(f["delta"] for f in body["score_factors"])


# ------------------------------------------------------------------ 确定性（无随机源）


def test_the_same_request_twice_returns_the_identical_cast(client: TestClient) -> None:
    """梅花起卦是算术不是抽签：同请求两次必须逐字节相等（PRD §4.1 可复核）。"""
    first = _post(client)
    second = _post(client)
    assert first.status_code == 200
    assert first.json() == second.json()
    assert first.text == second.text


def test_different_numbers_give_a_different_board(client: TestClient) -> None:
    """换报数必换盘：排除「端点其实回了一张常量盘」这种全绿的假象。"""
    seven_three = _post(client, numbers=[7, 3]).json()
    three_seven = _post(client, numbers=[3, 7]).json()
    assert seven_three["ben"]["number"] != three_seven["ben"]["number"]
    assert seven_three["summary"] != three_seven["summary"]


def test_omitting_everything_casts_the_present_moment_by_time(client: TestClient) -> None:
    """全缺省：方法是 `time`，时刻取现在，算式里印出农历四数——回显必须像个时刻。"""
    response = client.post(URL, json={})
    assert response.status_code == 200
    body = response.json()
    assert body["method"] == "time"
    assert body["question"] is None
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}", body["cast_time"])
    assert len(body["score_factors"]) == 4
    assert body["score"] == 50 + sum(f["delta"] for f in body["score_factors"])


def test_question_has_no_length_cap_and_is_echoed_verbatim(client: TestClient) -> None:
    """`MeihuaCastRequest.question` 没有 `max_length`（对照奇门的 120）——本轮的口径不一致 finding。

    两页的问事栏在前端都没有长度限制，后端一边设卡一边不设卡：同一段长文在 `/qimen/chart`
    拿 422、在 `/meihua/cast` 拿 200。这不是「梅花更宽松」的裁定，而是没人管过这一格
    （记入 Task 6 报告）。本测钉现状并留下对照，真要统一时连同它一起重定。
    """
    long_text = "问" * 500
    echoed = _post(client, question=long_text)
    assert echoed.status_code == 200
    assert echoed.json()["question"] == long_text


def test_a_utc_offset_is_read_as_wall_clock_and_moves_the_board(client: TestClient) -> None:
    """与奇门同一条时区 finding，用单数法演示：下卦与动爻都加时辰序，偏移一丢整盘换卦。

    `2024-05-15T02:30:00Z` 这一瞬间按北京时间是 10:30（巳时，时辰序 6），引擎却按 02:30
    （丑时，序 2）起卦：单数法 [8] 的下卦由 (8+6)÷8 余 6 变 (8+2)÷8 余 2，本卦由地水师
    （#7）变成泽地萃一类——不是差一个标注，是差一整张盘。页面只发无偏移串
    （`frontend/src/pages/PlumBlossomPage.tsx` 的 `normalizeCastTime`），故 App 内不可达。
    """
    naive = _post(client, numbers=[8], cast_time="2024-05-15T02:30:00").json()
    zulu = _post(client, numbers=[8], cast_time="2024-05-15T02:30:00Z").json()
    beijing = _post(client, numbers=[8], cast_time="2024-05-15T10:30:00").json()
    assert naive == zulu
    assert zulu["cast_time"] == "2024-05-15 02:30"
    assert zulu["ben"]["number"] != beijing["ben"]["number"]
    assert beijing["ben"]["number"] == 7          # golden 主锚之一：巳时单数法 [8] → 地水师


# ------------------------------------------------------------------ OpenAPI 三方同字


def test_the_openapi_contract_advertises_the_same_key_sets(client: TestClient) -> None:
    """前端类型是照 schema 手写的，schema 与手写契约不一致时以「三方同字」为准。"""
    spec = client.get("/openapi.json").json()
    assert URL in spec["paths"]
    schemas = spec["components"]["schemas"]
    assert set(schemas["MeihuaCast"]["properties"]) == TOP_LEVEL_KEYS
    assert set(schemas["MeihuaDerivation"]["properties"]) == DERIVATION_KEYS
    assert set(schemas["MeihuaHexagram"]["properties"]) == HEXAGRAM_KEYS
    assert set(schemas["MeihuaTrigram"]["properties"]) == TRIGRAM_KEYS
    assert set(schemas["TiYongParty"]["properties"]) == PARTY_KEYS
    assert set(schemas["TiYongVerdict"]["properties"]) == VERDICT_KEYS
    assert set(schemas["WangshuaiInfo"]["properties"]) == WANGSHUAI_KEYS
    assert set(schemas["app__schemas__meihua__ScoreFactor"]["properties"]) == FACTOR_KEYS
    assert set(schemas["MeihuaProvenance"]["properties"]) == PROVENANCE_KEYS
    # 四个入参都有默认值：缺省即「此刻以年月日时起一卦」。
    assert "required" not in schemas["MeihuaCastRequest"]
    assert set(schemas["MeihuaCastRequest"]["properties"]) == {
        "method", "numbers", "question", "cast_time",
    }
    assert set(schemas["MeihuaMethod"]["enum"]) == {"time", "number"}


def test_the_response_contains_no_field_the_frontend_never_declared(client: TestClient) -> None:
    """后端多出的字段在页面上是隐形的（前端 interface 里没有它），故必须点名。"""
    body = _post(client, method="time").json()
    assert not set(body) - FRONTEND_CAST_KEYS, sorted(set(body) - FRONTEND_CAST_KEYS)
    for key in ("derivation", "tiyong", "wangshuai"):
        assert not set(body[key]) - {
            "derivation": FRONTEND_DERIVATION_KEYS,
            "tiyong": FRONTEND_VERDICT_KEYS,
            "wangshuai": FRONTEND_WANGSHUAI_KEYS,
        }[key], key
    for hexagram_key in ("ben", "hu", "bian"):
        hexagram = body[hexagram_key]
        assert not set(hexagram) - FRONTEND_HEXAGRAM_KEYS, hexagram_key
        for side in ("lower", "upper"):
            assert not set(hexagram[side]) - FRONTEND_TRIGRAM_KEYS, (hexagram_key, side)
    for party in (body["ti"], body["yong"]):
        assert not set(party) - FRONTEND_PARTY_KEYS, party["role"]
        assert not set(party["trigram"]) - FRONTEND_TRIGRAM_KEYS
    for factor in body["score_factors"]:
        assert not set(factor) - FRONTEND_FACTOR_KEYS
    assert not set(body["provenance"]) - FRONTEND_PROVENANCE_KEYS, "provenance"
    for table in body["provenance"]["tables"]:
        assert not set(table) - FRONTEND_PROVENANCE_TABLE_KEYS


def test_the_frontend_declares_no_field_the_response_never_sends(client: TestClient) -> None:
    """反方向同样要命：前端照着声明读一个后端不给的字段，页面上就是 `undefined`。"""
    body = _post(client).json()
    assert not FRONTEND_CAST_KEYS - set(body), sorted(FRONTEND_CAST_KEYS - set(body))
    samples: dict[str, dict[str, object]] = {
        "derivation": body["derivation"],
        "ben|hu|bian": body["ben"],
        "ben.lower|upper": body["ben"]["lower"],
        "ti|yong": body["ti"],
        "tiyong": body["tiyong"],
        "wangshuai": body["wangshuai"],
        "score_factors[]": body["score_factors"][0],
        "provenance": body["provenance"],
    }
    for path, _, frontend in KEY_LAYERS:
        node = samples[path]
        assert not frontend - set(node), f"{path} 前端声明了响应里没有的字段: {sorted(frontend - set(node))}"
    # 本模块两份抄写不得自相矛盾（否则上面两条门都在偷工）。
    for path, declared, frontend in KEY_LAYERS:
        assert declared == frontend, f"{path} 的手写契约与前端抄本不同"
    assert TOP_LEVEL_KEYS == FRONTEND_CAST_KEYS
