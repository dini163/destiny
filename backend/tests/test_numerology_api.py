"""端点契约（spec §9.4）：200 形状、无 `score`、四张表、域错误 422、长度归 pydantic。

算术的性质测在 `tests/test_numerology.py`，外部锚点在 `tests/golden/`；本模块只管
「HTTP 这一层有没有把引擎算出的东西如实递出去」。故这里全部断言 JSON，不 import 引擎的
任何函数 —— 只 import 语料的表名清单，因为「响应声称引了哪几张表」正是契约的一部分。

两条守卫值得单说：

* **无 `score`**（决策 14）与**无百分比**（决策 13）：设计稿印了「综合指数 82%」，而
  毕达哥拉斯数理没有权威的吉凶总分传统，硬凑一个加权分等于让系统声称有人替它赋过分。
  这类字段日后极可能被「顺手加回来」，所以这里递归扫整个响应，而不是只看顶层。
* **`provenance.tables` 正好四张**：多列一张等于让本端点声称引了它没读的书。
"""

from datetime import date

from fastapi.testclient import TestClient

from app.content import CONTENT_VERSION, NUMEROLOGY_CONTENT_SOURCES

URL = "/api/v1/numerology/chart"

#: 主角案例（spec §2.4）。设计稿印的六个核心数里有三个与它自己印的算式互相矛盾，
#: 故本模块一律只认算式能推出来的东西。`reference_date` 显式给出，免得随今天漂移。
PAYLOAD: dict[str, object] = {
    "full_name": "LU QINGXUAN",
    "name_zh": "陆青玄",
    "birth_date": "1994-05-14",
    "reference_date": "2026-09-24",
}

CORE_ORDER = ["life_path", "expression", "soul_urge", "personality", "birthday", "maturity"]
PINNACLE_ORDER = ["first", "second", "third", "fourth"]
CHALLENGE_ORDER = ["first", "second", "main", "fourth"]
CYCLE_ORDER = ["previous_year", "year", "next_year", "month", "day"]


def _post(client: TestClient, **overrides: object):
    return client.post(URL, json={**PAYLOAD, **overrides})


def _walk_keys(node: object) -> set[str]:
    """递归收集响应里出现过的全部字典键，用来扫「不许出现的字段名」。"""
    if isinstance(node, dict):
        return set(node) | {key for value in node.values() for key in _walk_keys(value)}
    if isinstance(node, list):
        return {key for value in node for key in _walk_keys(value)}
    return set()


# ------------------------------------------------------------------ 200 形状


def test_the_chart_comes_back_whole_and_in_the_documented_order(
    client: TestClient,
) -> None:
    response = _post(client)
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {
        "input",
        "letters",
        "letter_map",
        "core",
        "karmic_debts",
        "pinnacles",
        "challenges",
        "personal_cycles",
        "name_grid",
        "loshu_grid",
        "provenance",
    }
    assert [item["key"] for item in body["core"]] == CORE_ORDER
    assert [item["key"] for item in body["pinnacles"]] == PINNACLE_ORDER
    assert [item["key"] for item in body["challenges"]] == CHALLENGE_ORDER
    assert list(body["personal_cycles"]) == CYCLE_ORDER
    # 前端直接渲染后端的账本、不重算任何算术（决策 5），故每一步都得递到浏览器。
    for card in body["core"]:
        assert card["label"] and card["source"]
        if card["value"] is not None:
            assert card["steps"]
            for step in card["steps"]:
                assert set(step) == {"label", "expression", "total", "reduced", "karmic_debt"}


def test_the_input_block_reports_what_was_actually_computed(client: TestClient) -> None:
    """回显块是决策 8 的落点：跳过了什么、算了几个字母，都如实报，不偷偷当 0。"""
    body = _post(client).json()
    echoed = body["input"]
    assert echoed["full_name"] == "LU QINGXUAN"
    assert echoed["name_zh"] == "陆青玄"
    assert echoed["birth_date"] == "1994-05-14"
    assert echoed["reference_date"] == "2026-09-24"
    assert echoed["y_as_vowel"] is False
    assert echoed["age_at_reference"] == 32
    assert (echoed["letter_count"], echoed["skipped_count"]) == (10, 1)
    assert echoed["skipped_chars"] == [" "]
    assert echoed["vowel_total"] + echoed["consonant_total"] == echoed["letter_total"] == 50
    assert len(body["letters"]) == 10
    assert sum(item["value"] for item in body["letters"]) == echoed["letter_total"]


def test_the_reference_date_defaults_to_today(client: TestClient) -> None:
    """缺省取今天（决策 11，与八字诸页同一个习惯）；golden 测试靠显式传参固定。"""
    echoed = _post(client, reference_date=None).json()["input"]
    assert echoed["reference_date"] == date.today().isoformat()


def test_the_letter_map_is_the_same_table_the_name_letters_were_read_from(
    client: TestClient,
) -> None:
    """映射表九列下发（spec §5.1），且与同一份响应里的逐字值**对得上**。

    这一条是前端不另抄一份 A–Z 的前提：表只在后端有一份，页面才能把它与逐字透视条
    摆在一屏而不担心两处自相矛盾。故这里不只数九列，还拿姓名里每个字母反查它所在列的
    数字 —— 两份数据在同一份 JSON 里互证，漂移了就同时炸。

    不断言具体哪几个字母归哪列：那是语料测（`LETTER_VALUES` ↔ `VALUE_GROUPS` 双向锁）
    的活，在此重列一遍只会多一份可漂移的副本。只锁形状：26 个字母一个不多一个不少，
    九列值为 1..9，以及 26 = 9 + 9 + 8 带来的那一列只有两个字母。
    """
    body = _post(client).json()
    columns = body["letter_map"]
    assert [column["value"] for column in columns] == list(range(1, 10))
    spelled = [char for column in columns for char in column["letters"]]
    assert sorted(spelled) == [chr(code) for code in range(ord("A"), ord("Z") + 1)]
    assert len(columns[-1]["letters"]) == 2
    value_of = {char: column["value"] for column in columns for char in column["letters"]}
    assert [value_of[item["char"]] for item in body["letters"]] == [
        item["value"] for item in body["letters"]
    ]


def test_both_grids_come_back_separately_with_their_own_missing_lists(
    client: TestClient,
) -> None:
    """决策 9：两张九宫各读各的输入、各带各的缺数释义，绝不合成一张表。"""
    body = _post(client).json()
    name_grid, loshu = body["name_grid"], body["loshu_grid"]
    assert [cell["digit"] for cell in name_grid["cells"]] == list(range(1, 10))
    assert [cell["digit"] for cell in loshu["cells"]] == list(range(1, 10))
    assert name_grid["layout"] == loshu["layout"] == [[4, 9, 2], [3, 5, 7], [8, 1, 6]]
    assert name_grid["total"] == 10
    assert [item["digit"] for item in name_grid["karmic_lessons"]] == [2, 4]
    assert (loshu["total"], loshu["zero_count"]) == (7, 1)
    assert loshu["digits"] == [1, 9, 9, 4, 0, 5, 1, 4]
    assert [item["digit"] for item in loshu["missing"]] == [2, 3, 6, 7, 8]
    assert len(loshu["planes"]) == 8 and loshu["line_sums"] == [15] * 8
    assert [plane["key"] for plane in loshu["planes"] if plane["complete"]] == ["will"]


def test_y_as_vowel_moves_y_between_the_two_columns(client: TestClient) -> None:
    """决策 7：Y 默认按辅音；打开开关后 `Lynn` 的灵魂冲动数才算得出来。

    这一对请求把决策 17 的留空理由与它给的建议一起验了：默认那一份不仅 `value` 为
    null，还在 `unavailable_reason` 里告诉用户可以打开这个开关。
    """
    default = _post(client, full_name="Lynn", name_zh=None)
    assert default.status_code == 200
    card = {item["key"]: item for item in default.json()["core"]}["soul_urge"]
    assert card["value"] is None and card["root"] is None and card["meaning"] is None
    assert not card["steps"] and not card["keywords"] and card["master_title"] is None
    assert card["is_master"] is False
    assert "Y" in card["unavailable_reason"]
    flipped = _post(client, full_name="Lynn", name_zh=None, y_as_vowel=True)
    assert flipped.json()["input"]["y_as_vowel"] is True
    assert {item["key"]: item for item in flipped.json()["core"]}["soul_urge"]["value"] == 7


def test_a_missing_core_number_never_turns_into_a_zero(client: TestClient) -> None:
    """决策 17 在 HTTP 层的形状：算不出就是 `null`，不是 `0`。

    只扫 `core` 那一段：挑战数与九宫计数里的 0 是值域的真实成员（`|5−5| = 0`、
    「这个数一次都没出现」），扫全盘会把它们一起判负。而核心数的值域是
    `{1..9, 11, 22, 33}`，0 永远不是它的合法成员。
    """
    core = _post(client, full_name="Lynn", name_zh=None).json()["core"]
    assert all(card["value"] != 0 for card in core)
    assert any(card["value"] is None for card in core)


def test_the_master_card_arrives_with_its_title(client: TestClient) -> None:
    """主角盘上唯一那张主数卡，两个字段必须成对到浏览器。

    为什么是「成对」而不是「有值」：`CoreNumberHero.tsx:30-32` 与
    `CoreNumberCard.tsx:65-67` 的渲染条件是 `card.is_master && card.master_title`，
    没有 else 分支 —— `is_master` 为真而 `master_title` 为空时，页面上那一行「主数 ·」
    角标**静默消失**，卡上仍印着 11/2，读者无从知道少了一样东西。

    引擎层那一环已有 `(item.master_title is not None) == item.is_master`
    （`tests/test_numerology.py:305`）与 golden 的 `[False]*5 + [True]`
    （`tests/golden/test_numerology_golden.py:140-142`），称号文本本身住在
    `tests/content/test_numerology_corpora.py`。本条只管序列化：字段在 response model
    里被改名、或被哪一层 `exclude_none` 抹掉，上面三条都还是绿的，而页面已经印不出来了。
    """
    core = _post(client).json()["core"]
    assert [card["key"] for card in core] == CORE_ORDER
    assert [card["is_master"] for card in core] == [False] * 5 + [True]
    assert [card["master_title"] is not None for card in core] == [False] * 5 + [True]
    assert core[5]["key"] == "maturity" and core[5]["value"] == 11
    assert core[5]["master_title"] == "MASTER INTUITION · 灵性直觉者"
    assert [card["master_title"] for card in core[:5]] == [None] * 5


# ------------------------------------------------------------------ 决策 13 / 14 守卫


def test_there_is_no_score_and_no_percentage_anywhere_in_the_response(
    client: TestClient,
) -> None:
    text = _post(client).text
    keys = _walk_keys(_post(client).json())
    assert not (keys & {"score", "total_score", "balance", "percentage", "percent", "rating"})
    # 设计稿那个「综合指数 82%」在响应里连一个百分号都不许留下（决策 13）。
    assert "%" not in text and "％" not in text


def test_the_openapi_schema_does_not_advertise_a_score(client: TestClient) -> None:
    """从 `/openapi.json` 那一侧再守一次：前端照 schema 生成类型，schema 里有就会长出来。"""
    spec = client.get("/openapi.json").json()
    assert URL in spec["paths"]
    schema = spec["components"]["schemas"]["NumerologyChart"]
    assert "score" not in schema["properties"]
    assert set(schema["required"]) == set(schema["properties"])


# ------------------------------------------------------------------ 溯源


def test_provenance_lists_exactly_the_tables_this_endpoint_reads(client: TestClient) -> None:
    provenance = _post(client).json()["provenance"]
    assert [table["name"] for table in provenance["tables"]] == [
        module for module, _ in NUMEROLOGY_CONTENT_SOURCES
    ]
    for table, (_, source) in zip(provenance["tables"], NUMEROLOGY_CONTENT_SOURCES, strict=True):
        assert table["source"] == source
        # 本端点无历法库，故版本取本仓语料的滚动版本，而不是某个外部库的版本号。
        assert table["version"] == CONTENT_VERSION
    assert provenance["reference_date"] == "2026-09-24"
    # 决策 16：档案号只印方法标识。设计稿那个 `-9405` 流水号每人不同又无推导依据，
    # 只能靠编，编了就是 mock 数据。故它不随人变：换个名字与生日，它一个字也不动。
    assert provenance["badge"] == "#NUMERO-PYTHAG"
    assert provenance["engine"] and provenance["method"]
    other = _post(client, full_name="Anna", birth_date="1990-01-01").json()["provenance"]
    assert other["badge"] == provenance["badge"]


# ------------------------------------------------------------------ 422


def test_a_name_without_latin_letters_is_rejected_with_a_machine_code(
    client: TestClient,
) -> None:
    """纯中文名过得了 pydantic 的长度校验，坏的是只有引擎知道的那条映射前提（spec §7）。"""
    response = _post(client, full_name="陆青玄")
    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "numerology_no_latin_letters"
    assert error["message"]
    # `context` 是给机器的：前端据它提示「请改用拼音」，而不是去解析人读的文案。
    assert error["context"] == {"field": "full_name", "chars": ["陆", "青", "玄"]}


def test_length_bounds_are_pydantic_validation_not_domain_errors(
    client: TestClient,
) -> None:
    """长度归 pydantic（回 FastAPI 的 `detail` 形状），分工同 `name.py`。"""
    for overrides in (
        {"full_name": ""},
        {"full_name": "A" * 81},
        {"name_zh": "陆" * 21},
    ):
        response = _post(client, **overrides)
        assert response.status_code == 422, overrides
        body = response.json()
        assert "detail" in body and "error" not in body
