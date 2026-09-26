"""奇门端点契约（Task 6 Step 4）：顶层与逐宫键集**手写**、null 只在中宫、时区口径如实。

安盘的**对错**测在 `tests/golden/test_qimen_golden.py`（四张手推盘 + 环无关关系），
表的**齐不齐**测在 `tests/content/test_qimen_corpus.py`；本模块只管 HTTP 这一层有没有把
引擎排好的盘如实、按契约递出去 —— 故一律断言 JSON，不 import 引擎函数（分派同
`tests/test_ziwei_api.py`）。

四道值得单说的门：

* **键集手写、并与前端 `frontend/src/types/qimen.ts` 各抄一份**：从
  `QimenChart.model_fields` 取会让这条对「悄悄多了一个字段」毫无感觉；两个方向都要点名
  （后端多给前端不读 = 静默丢信息，前端多读后端不给 = `undefined`）。
* **`door`/`god` 的 null 只在洛书五宫**：schema 声明的是 `DoorInfo | None`，前端 `PalaceCell`
  按「中宫无门无神」画空格。若引擎哪天把中宫也填满，JSON 形状照样合规，页面却会多出两格
  没有出处的门神。
* **奇门没有可达的域错误路径**：`app/engines/qimen.py` 唯一的 `raise` 是第 91-92 行那句
  `ValueError("未识别的节气…")`，它不在 `DestinyError` 家族里，真发生就是 500 而非
  `{error:{code,message}}` 信封。它不可达**靠的是局数表覆盖 lunar-python 的 24 节气**，
  那条证明住在语料测里，所以这里钉的是「合法时间戳一律 200，永不出信封」。
* **带时区偏移的时间戳被当墙钟读取**：`2024-05-15T02:30:00Z` 与 `2024-05-15T02:30:00`
  排出同一张盘（丑时），而前者按北京时间是巳时——值符值使随之全变。SCHOOL_NOTE 只声明了
  「未作真太阳时校正」，没声明这一层。本轮把它钉成**现状事实 + finding**（同
  `tests/test_ziwei_api.py` 对 F-A1-3 的处理法：条文落地时连同契约一起重定，不是改断言）。

复测本文件测数：`cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m pytest
tests/test_qimen_api.py -q` → 21 passed（2026-09-26 实录，含「坏时间戳两条 + 日期区间四条」参数化）。
"""

import re

import pytest
from fastapi.testclient import TestClient

from app.content import CONTENT_VERSION

URL = "/api/v1/qimen/chart"

#: 参考时刻：己巳时，阳遁四局（值符天辅落坤二，见 golden 锚 A）。
PAYLOAD: dict[str, object] = {"cast_time": "2024-05-15T10:30:00"}

KEY_RE = re.compile(r"^[a-z][a-z0-9_]*$")

#: 局数的中文数字（引擎印局名用同一套：阳遁四局）。
CN_DIGITS = ["", "一", "二", "三", "四", "五", "六", "七", "八", "九"]

# ------------------------------------------------------------------ 契约面（手写）

TOP_LEVEL_KEYS = {
    "question", "cast_time",
    "year_ganzhi", "month_ganzhi", "day_ganzhi", "time_ganzhi",
    "jieqi", "yuan", "dun", "ju_number", "ju_name",
    "xunshou", "xunshou_yi", "zhifu_star", "zhishi_door",
    "zhifu_palace", "zhishi_palace", "kongwang", "yima",
    "palaces", "engine", "provenance",
}

PALACE_KEYS = {
    "number", "gua", "direction", "element", "zhi", "row", "col", "is_center",
    "dipan_gan", "tianpan_gan", "stars", "door", "god", "kong", "ma",
    "is_zhifu_palace", "is_zhishi_palace",
}

STAR_KEYS = {"name", "element", "luck", "nature", "is_zhifu"}
DOOR_KEYS = {"name", "element", "luck", "nature", "is_zhishi"}
GOD_KEYS = {"name", "luck", "nature"}
PROVENANCE_KEYS = {"engine", "content_version", "source", "school_note"}

# ------------------------------------------------------------------ 前端声明（手抄）
# 照 `frontend/src/types/qimen.ts` 的六个 interface 逐字重抄；不在后端测试里读前端树，
# 两份各抄一次才有门（抄写约定同 `tests/test_ziwei_api.py:60-82`）。

FRONTEND_CHART_KEYS = {
    "question", "cast_time",
    "year_ganzhi", "month_ganzhi", "day_ganzhi", "time_ganzhi",
    "jieqi", "yuan", "dun", "ju_number", "ju_name",
    "xunshou", "xunshou_yi", "zhifu_star", "zhishi_door",
    "zhifu_palace", "zhishi_palace", "kongwang", "yima",
    "palaces", "engine", "provenance",
}

FRONTEND_PALACE_KEYS = {
    "number", "gua", "direction", "element", "zhi", "row", "col", "is_center",
    "dipan_gan", "tianpan_gan", "stars", "door", "god", "kong", "ma",
    "is_zhifu_palace", "is_zhishi_palace",
}

FRONTEND_STAR_KEYS = {"name", "element", "luck", "nature", "is_zhifu"}
FRONTEND_DOOR_KEYS = {"name", "element", "luck", "nature", "is_zhishi"}
FRONTEND_GOD_KEYS = {"name", "luck", "nature"}
FRONTEND_PROVENANCE_KEYS = {"engine", "content_version", "source", "school_note"}

KEY_LAYERS: list[tuple[str, set[str], set[str]]] = [
    ("palaces[]", PALACE_KEYS, FRONTEND_PALACE_KEYS),
    ("palaces[].stars[]", STAR_KEYS, FRONTEND_STAR_KEYS),
    ("palaces[].door", DOOR_KEYS, FRONTEND_DOOR_KEYS),
    ("palaces[].god", GOD_KEYS, FRONTEND_GOD_KEYS),
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


def test_the_board_comes_back_with_exactly_the_hand_written_contract(client: TestClient) -> None:
    response = _post(client)
    assert response.status_code == 200
    body = response.json()
    assert set(body) == TOP_LEVEL_KEYS
    assert len(TOP_LEVEL_KEYS) == 22  # 尺寸哨兵：抄漏一格上面那条相等就直接红，这条管的是两侧同时缩水
    assert body["engine"] == "qimen-luoshu-rotating"
    assert body["provenance"]["engine"] == body["engine"]  # 两处引擎名不能各说各话
    assert body["cast_time"] == "2024-05-15 10:30"
    assert body["question"] is None


def test_nested_objects_carry_exactly_their_declared_keys(client: TestClient) -> None:
    """九宫、宫里星、门、神、出处四件 nested 对象的键集同样钉死。"""
    body = _post(client).json()
    assert len(body["palaces"]) == 9
    for palace in body["palaces"]:
        assert set(palace) == PALACE_KEYS, palace["number"]
        for star in palace["stars"]:
            assert set(star) == STAR_KEYS, star["name"]
        if palace["door"] is not None:
            assert set(palace["door"]) == DOOR_KEYS, palace["number"]
        if palace["god"] is not None:
            assert set(palace["god"]) == GOD_KEYS, palace["number"]
    assert set(body["provenance"]) == PROVENANCE_KEYS


def test_the_nine_palaces_arrive_in_loshu_order_and_fill_the_grid(client: TestClient) -> None:
    """宫序 1→9 是前端画盘的坐标；九宫的 (row, col) 恰是 3×3 九格（南上北下）。"""
    palaces = _post(client).json()["palaces"]
    assert [p["number"] for p in palaces] == list(range(1, 10))
    assert {(p["row"], p["col"]) for p in palaces} == {(r, c) for r in range(3) for c in range(3)}
    assert [p["gua"] for p in palaces] == ["坎", "坤", "震", "巽", "中", "乾", "兑", "艮", "离"]
    for palace in palaces:
        assert palace["is_center"] == (palace["number"] == 5)
        assert palace["dipan_gan"] and len(palace["dipan_gan"]) == 1
        assert palace["zhi"] == "" if palace["is_center"] else palace["zhi"]


def test_door_and_god_are_null_only_in_the_center_palace(client: TestClient) -> None:
    """中五宫无门无神、天盘亦空；其余八宫恰一门一神至少一星——页面按此分叉渲染。"""
    palaces = _post(client).json()["palaces"]
    center = next(p for p in palaces if p["is_center"])
    assert (center["door"], center["god"], center["stars"], center["tianpan_gan"]) == \
        (None, None, [], [])
    assert center["zhi"] == "" and not center["kong"] and not center["ma"]
    others = [p for p in palaces if not p["is_center"]]
    assert len(others) == 8
    for palace in others:
        assert palace["door"] is not None and palace["god"] is not None
        assert len(palace["stars"]) >= 1
        assert len(palace["stars"]) == len(palace["tianpan_gan"])


def test_the_placement_vocabularies_stay_inside_their_declared_ranges(client: TestClient) -> None:
    """吉凶/五行两个词表是页面直接印出的字符串，越界即「形对而实不全」。"""
    body = _post(client).json()
    elements = {"金", "木", "水", "火", "土"}
    luck3 = {"吉", "凶", "中平"}
    placements: list[tuple[str, dict]] = []
    for palace in body["palaces"]:
        for star in palace["stars"]:
            placements.append(("star", star))
        if palace["door"]:
            placements.append(("door", palace["door"]))
        if palace["god"]:
            placements.append(("god", palace["god"]))
    assert len(placements) == 9 + 8 + 8  # 九星（含寄宫的第二枚）+ 八门 + 八神
    for kind, item in placements:
        assert item["name"] and item["nature"], (kind, item)
        assert item["luck"] in ({"吉", "凶"} if kind == "god" else luck3), (kind, item["name"])
        if kind != "god":
            assert item["element"] in elements, (kind, item["name"])
    assert {p["dipan_gan"] for p in body["palaces"]} - set("甲乙丙丁戊己庚辛壬癸") == set()


def test_the_top_level_fields_and_flags_describe_the_same_board(client: TestClient) -> None:
    """顶层声明与逐宫旗标必须同实：值符星就在 `zhifu_palace`、值使门就在 `zhishi_palace`，
    两个「落宫」标记各只亮一格，且值使永不落中五（中五无门）。"""
    body = _post(client).json()
    assert sum(1 for p in body["palaces"] if p["is_zhifu_palace"]) == 1
    assert sum(1 for p in body["palaces"] if p["is_zhishi_palace"]) == 1
    fu = next(p for p in body["palaces"] if p["number"] == body["zhifu_palace"])
    zhi = next(p for p in body["palaces"] if p["number"] == body["zhishi_palace"])
    assert body["zhifu_star"] in [s["name"] for s in fu["stars"]]
    assert any(s["is_zhifu"] for s in fu["stars"])
    assert fu["god"]["name"] == "值符" and fu["is_zhifu_palace"]
    assert zhi["door"]["name"] == body["zhishi_door"] and zhi["door"]["is_zhishi"]
    assert body["zhishi_palace"] != 5 and zhi["is_zhishi_palace"]
    assert body["dun"] in {"阳遁", "阴遁"} and body["ju_number"] in range(1, 10)
    assert body["ju_name"] == body["dun"] + CN_DIGITS[body["ju_number"]] + "局"
    assert body["yuan"] in {"上元", "中元", "下元"}
    assert body["xunshou"][0] == "甲" and body["xunshou_yi"] in "戊己庚辛壬癸"
    assert len(body["kongwang"]) == 2 and body["yima"] in "子丑寅卯辰巳午未申酉戌亥"


def test_the_response_is_snake_case_end_to_end(client: TestClient) -> None:
    """AGENTS 第 3 条：后端 JSON 全 snake_case，前端不重命名——一个驼峰键就会让页面拿到 undefined。"""
    keys = _walk_keys(_post(client).json())
    assert keys, "响应树里一个键都没有，说明抄错了 URL"
    assert [key for key in keys if not KEY_RE.match(key)] == []


# ------------------------------------------------------------------ 422 归 pydantic


def test_question_length_is_pydantic_validation(client: TestClient) -> None:
    """`QimenRequest.question` 的 120 字上限是字段自身的事 → FastAPI 的 `detail`，不是信封。"""
    response = _post(client, question="问" * 121)
    assert response.status_code == 422
    body = response.json()
    assert "error" not in body
    assert body["detail"][0]["type"] == "string_too_long"
    assert body["detail"][0]["loc"] == ["body", "question"]
    assert _post(client, question="问" * 120).status_code == 200


@pytest.mark.parametrize(
    "value",
    ["2024-13-45T99:99:99", "not-a-time"],
    ids=["越界月份", "非时间串"],
)
def test_a_malformed_timestamp_is_pydantic_validation(client: TestClient, value: str) -> None:
    response = _post(client, cast_time=value)
    assert response.status_code == 422
    body = response.json()
    assert "error" not in body
    assert body["detail"][0]["loc"] == ["body", "cast_time"]
    assert body["detail"][0]["type"] == "datetime_from_date_parsing"


# ------------------------------------------------------------------ 无域错误路径（现状钉死）


@pytest.mark.parametrize(
    "cast_time",
    ["1900-01-01T10:30:00", "2100-12-31T10:30:00", "1800-01-01T10:30:00", "2200-01-01T10:30:00"],
    ids=["区间起点", "区间终点", "区间前", "区间后"],
)
def test_every_parsable_datetime_returns_a_full_board_never_an_envelope(
    client: TestClient, cast_time: str
) -> None:
    """奇门没有 `DestinyError` 可达路径：任何能解析的时间都给出整盘，绝不出信封。

    PRD §4.1 的支持区间是 1900-2100（端点两条），区间外的两条同样按盘给出——lunar-python
    的历法在这个区间仍然算得出干支与节气，所以「越界」在这里不是错误而是如实计算。
    真会失败的那条路（`engines/qimen.py:91` 的 `ValueError`）要的是「局数表缺一个节气」，
    而那由 `tests/content/test_qimen_corpus.py::test_the_two_dun_together_cover_all_twenty_four_jieqi`
    堵住；它一旦被触发就是 500，不是 `{error:{code}}` 信封——这是本端点契约的已知边界。
    """
    response = _post(client, cast_time=cast_time)
    assert response.status_code == 200
    body = response.json()
    assert "error" not in body and "detail" not in body
    assert len(body["palaces"]) == 9
    assert body["ju_name"] and body["zhifu_star"] and body["zhishi_door"]
    assert 1 <= body["ju_number"] <= 9


def test_the_endpoint_is_a_pure_function_of_the_cast_time(client: TestClient) -> None:
    """排盘无随机（AGENTS 第 5 条只管抽签类引擎，奇门不在其列）：同请求两次逐字节相同。"""
    first = _post(client)
    second = _post(client)
    assert first.status_code == 200
    assert first.json() == second.json()
    assert first.text == second.text


def test_omitting_cast_time_casts_the_present_moment(client: TestClient) -> None:
    """缺省取服务器当前时刻：局名与四柱必须自洽，而不是回显一个空串。"""
    response = client.post(URL, json={})
    assert response.status_code == 200
    body = response.json()
    assert len(body["palaces"]) == 9
    assert body["question"] is None
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}", body["cast_time"])
    assert body["dun"] in {"阳遁", "阴遁"} and body["ju_name"].startswith(body["dun"])


def test_a_utc_offset_is_read_as_wall_clock_and_is_not_converted(client: TestClient) -> None:
    """带偏移的 ISO 串按「字面钟点」起局，不做任何时区换算 —— 本轮 finding，非契约承诺。

    `2024-05-15T02:30:00Z` 这一瞬间在北京时间已是 10:30（巳时），而引擎把 02:30 当 02:30，
    排出的是丑时盘：`time_ganzhi` 由己巳变乙丑，值符值使与逐宫星门神全变。
    SCHOOL_NOTE 只声明「时辰径取输入钟点，未作真太阳时校正」，没有声明偏移量被丢弃；
    响应回显的 `cast_time` 也不带偏移，读者无从分辨。页面侧目前只发 `datetime-local` 的
    无偏移串（`frontend/src/pages/QimenPage.tsx` 的 `normalizeCastTime`），所以这条在 App 内
    不可达，只有直连 API 的调用方会踩到。修法（二选一，须由控制器裁定）：
    按 `app/solar` 换算到北京时间，或在 schema 层拒收带偏移的串——两者都会让本测红，
    届时连同这条 docstring 一起重定，不是把断言改成迁就。
    """
    naive = _post(client, cast_time="2024-05-15T02:30:00").json()
    zulu = _post(client, cast_time="2024-05-15T02:30:00Z").json()
    beijing = _post(client, cast_time="2024-05-15T10:30:00").json()
    assert naive == zulu                                   # 偏移被静默丢弃
    assert zulu["cast_time"] == "2024-05-15 02:30"
    assert zulu["time_ganzhi"] == naive["time_ganzhi"] != beijing["time_ganzhi"]
    assert zulu["palaces"] != beijing["palaces"]           # 同瞬间两派盘，值符值使全不同


# ------------------------------------------------------------------ 出处诚实性


def test_provenance_names_the_book_and_the_four_school_choices(client: TestClient) -> None:
    """出处与口径必须自己讲清楚：书级出处 + 拆补/转盘/寄宫/八神四处派别（AGENTS 第 7 条）。"""
    provenance = _post(client).json()["provenance"]
    assert provenance["source"] and "烟波钓叟歌" in provenance["source"]
    assert provenance["content_version"] == CONTENT_VERSION
    note = provenance["school_note"]
    for declared in ("拆补法", "转盘法", "寄坤二宫", "八神", "未作真太阳时校正"):
        assert declared in note, declared


def test_the_openapi_contract_advertises_the_same_key_sets(client: TestClient) -> None:
    """前端类型是照 schema 手写的，schema 与手写契约不一致时以「三方同字」为准。"""
    spec = client.get("/openapi.json").json()
    assert URL in spec["paths"]
    schemas = spec["components"]["schemas"]
    assert set(schemas["QimenChart"]["properties"]) == TOP_LEVEL_KEYS
    assert set(schemas["QimenPalace"]["properties"]) == PALACE_KEYS
    assert set(schemas["StarInfo"]["properties"]) == STAR_KEYS
    assert set(schemas["DoorInfo"]["properties"]) == DOOR_KEYS
    assert set(schemas["GodInfo"]["properties"]) == GOD_KEYS
    assert set(schemas["QimenProvenance"]["properties"]) == PROVENANCE_KEYS
    # 两个入参都有默认值：奇门是用事之时的盘，「现在」就是它缺省的定义域。
    assert "required" not in schemas["QimenRequest"]
    assert set(schemas["QimenRequest"]["properties"]) == {"cast_time", "question"}


def test_the_response_contains_no_field_the_frontend_never_declared(client: TestClient) -> None:
    """后端多出的字段在页面上是隐形的（前端 interface 里没有它），故必须点名。"""
    body = _post(client).json()
    assert not set(body) - FRONTEND_CHART_KEYS, sorted(set(body) - FRONTEND_CHART_KEYS)
    for palace in body["palaces"]:
        assert not set(palace) - FRONTEND_PALACE_KEYS, palace["number"]
        for star in palace["stars"]:
            assert not set(star) - FRONTEND_STAR_KEYS, star["name"]
        for node, frontend in (
            (palace["door"], FRONTEND_DOOR_KEYS),
            (palace["god"], FRONTEND_GOD_KEYS),
        ):
            if node is not None:
                assert not set(node) - frontend, palace["number"]
    assert not set(body["provenance"]) - FRONTEND_PROVENANCE_KEYS


def test_the_frontend_declares_no_field_the_response_never_sends(client: TestClient) -> None:
    """反方向同样要命：前端照着声明读一个后端不给的字段，页面上就是 `undefined`。"""
    body = _post(client).json()
    assert not FRONTEND_CHART_KEYS - set(body), sorted(FRONTEND_CHART_KEYS - set(body))
    samples: dict[str, dict[str, object]] = {
        "palaces[]": body["palaces"][0],
        "palaces[].stars[]": next(s for p in body["palaces"] for s in p["stars"]),
        "palaces[].door": next(p["door"] for p in body["palaces"] if p["door"]),
        "palaces[].god": next(p["god"] for p in body["palaces"] if p["god"]),
        "provenance": body["provenance"],
    }
    for path, _, frontend in KEY_LAYERS:
        node = samples[path]
        assert not frontend - set(node), f"{path} 前端声明了响应里没有的字段: {sorted(frontend - set(node))}"
    # 本模块两份抄写不得自相矛盾（否则上面两条门都在偷工）。
    for path, declared, frontend in KEY_LAYERS:
        assert declared == frontend, f"{path} 的手写契约与前端抄本不同"
    assert TOP_LEVEL_KEYS == FRONTEND_CHART_KEYS
