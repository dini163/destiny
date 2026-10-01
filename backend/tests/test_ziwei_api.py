"""紫微端点契约（Task 5 Step 4）：顶层键集**手写**、`gender` 缺失归 pydantic、
响应里不许有前端从未声明的字段。

安星的**对错**测在 `tests/golden/test_ziwei_golden.py`（手推锚）与
`tests/content/test_ziwei_corpus.py`（表不变量）；本模块只管 HTTP 这一层有没有把
引擎排好的盘如实、按契约递出去 —— 故一律断言 JSON，不 import 引擎函数。

四道门值得单说：

* **顶层键集手写**（不从 `ZiweiChart.model_fields` 取）：从模型取会让这条对
  「悄悄多了一个字段」毫无感觉，而锁死契约面正是它的用途 —— 加字段应当是一次显式改动
  （同 `tests/test_runes_api.py:31-33` 的裁定）。
* **`gender` 缺失 → 422 且走 FastAPI 的 `detail`**：字段自身过不了类型/必填校验归 pydantic，
  字段之间归引擎（AGENTS.md 第 4 条）。对照门是「校正开启却没有地点」→ **400
  `invalid_birth_data`**，那两样东西每个字段单看都合法，坏的是它们之间的关系。
* **逐层键集等于 `frontend/src/types/ziwei.ts` 手抄来的那份**：后端多一个字段而前端
  没声明，页面不会报错，只会静默不显示；前端多一个字段而后端不给，拿到的是 `undefined`。
  两个方向都是「形对而实不全」（PRD §9），所以两边都要点名，而不是只扫一侧。
* **无 `score`、无百分号**：这一页印的每一个数都该能追到一条安星诀或一次历法换算，
  任何可信度/概率类的数都是编的（PRD §4.1），故递归扫整棵响应树。
"""

import pytest
from fastapi.testclient import TestClient

URL = "/api/v1/ziwei/chart"

#: 只给最少的必填项 + 显式经度，真太阳时关掉，好让历法事实与参考盘逐字对齐。
PAYLOAD: dict[str, object] = {
    "birth_date": "2000-08-16",
    "birth_time": "12:00",
    "calendar": "solar",
    "longitude": 116.4074,
    "gender": "male",
    "apply_true_solar_time": False,
}

# ------------------------------------------------------------------ 契约面（手写）

#: 手写而不从 `ZiweiChart.model_fields` 取，理由见模块头注。
TOP_LEVEL_KEYS = {
    "name", "gender", "calendar", "standard_datetime", "true_solar_time", "tst_applied",
    "tst_offset_minutes", "longitude", "lunar_date", "lunar_year_ganzhi", "lunar_month",
    "lunar_day", "lunar_leap", "time_zhi", "ming_gong_zhi", "ming_gong_ganzhi",
    "ming_gong_nayin", "shen_gong_zhi", "shen_gong_name", "wuxing_ju", "wuxing_ju_number",
    "ming_zhu", "shen_zhu", "ziwei_zhi", "tianfu_zhi", "palaces", "sihua",
    "dayun_direction", "dayun_start_age", "engine", "provenance",
}

PALACE_KEYS = {
    "index", "zhi", "gan", "ganzhi", "name", "is_ming", "is_shen", "dayun", "stars", "plain",
}

STAR_KEYS = {"name", "kind", "element", "yin_yang", "group", "nature", "sihua"}

SIHUA_KEYS = {"year_gan", "lu", "quan", "ke", "ji"}

PROVENANCE_KEYS = {"engine", "content_version", "source", "school_note", "tables"}

# ------------------------------------------------------------------ 前端声明（手抄）
# 下面五份是照 `frontend/src/types/ziwei.ts` 的五个 interface **逐字重抄**的字段名，
# 故意不在测试里读那个文件：后端测试不该依赖前端树的路径，而两份各抄一次才有门
# （抄写约定同 `tests/content/test_rune_corpora.py`）。

FRONTEND_CHART_KEYS = {
    "name", "gender", "calendar", "standard_datetime", "true_solar_time", "tst_applied",
    "tst_offset_minutes", "longitude", "lunar_date", "lunar_year_ganzhi", "lunar_month",
    "lunar_day", "lunar_leap", "time_zhi", "ming_gong_zhi", "ming_gong_ganzhi",
    "ming_gong_nayin", "shen_gong_zhi", "shen_gong_name", "wuxing_ju", "wuxing_ju_number",
    "ming_zhu", "shen_zhu", "ziwei_zhi", "tianfu_zhi", "palaces", "sihua",
    "dayun_direction", "dayun_start_age", "engine", "provenance",
}

FRONTEND_PALACE_KEYS = {
    "index", "zhi", "gan", "ganzhi", "name", "is_ming", "is_shen", "dayun", "stars", "plain",
}

FRONTEND_STAR_KEYS = {"name", "kind", "element", "yin_yang", "group", "nature", "sihua"}

FRONTEND_SIHUA_KEYS = {"year_gan", "lu", "quan", "ke", "ji"}

FRONTEND_PROVENANCE_KEYS = {"engine", "content_version", "source", "school_note", "tables"}

#: 三层键集的对照表，一次扫完（少一个字段/多一个字段都会被点名）。
KEY_LAYERS: list[tuple[str, set[str], set[str]]] = [
    ("palaces[]", PALACE_KEYS, FRONTEND_PALACE_KEYS),
    ("palaces[].stars[]", STAR_KEYS, FRONTEND_STAR_KEYS),
    ("sihua", SIHUA_KEYS, FRONTEND_SIHUA_KEYS),
    ("provenance", PROVENANCE_KEYS, FRONTEND_PROVENANCE_KEYS),
]


def _post(client: TestClient, **overrides: object):
    return client.post(URL, json={**PAYLOAD, **overrides})


def _walk_keys(node: object) -> set[str]:
    """递归收集响应里出现过的全部字典键。"""
    if isinstance(node, dict):
        return set(node) | {key for value in node.values() for key in _walk_keys(value)}
    if isinstance(node, list):
        return {key for value in node for key in _walk_keys(value)}
    return set()


# ------------------------------------------------------------------ 200 形状


def test_the_chart_comes_back_with_exactly_the_hand_written_contract(client: TestClient) -> None:
    response = _post(client)
    assert response.status_code == 200
    body = response.json()
    assert set(body) == TOP_LEVEL_KEYS
    assert len(TOP_LEVEL_KEYS) == 31  # 抄漏一格会让上面的相等变成自证
    assert body["name"] is None
    assert body["gender"] == "male"
    assert body["calendar"] == "solar"
    assert body["standard_datetime"] == "2000-08-16 12:00"
    assert body["engine"] == "ziwei-deterministic"
    assert body["provenance"]["engine"] == body["engine"]  # 两处引擎名不能各说各话


def test_nested_objects_carry_exactly_their_declared_keys(client: TestClient) -> None:
    """十二宫、宫里的星、四化、出处四件 nested 对象的键集同样钉死。"""
    body = _post(client).json()
    assert len(body["palaces"]) == 12
    for palace in body["palaces"]:
        assert set(palace) == PALACE_KEYS, palace["zhi"]
        for star in palace["stars"]:
            assert set(star) == STAR_KEYS, star["name"]
    assert set(body["sihua"]) == SIHUA_KEYS
    assert set(body["provenance"]) == PROVENANCE_KEYS


def test_the_twelve_palaces_arrive_in_earthly_branch_order(client: TestClient) -> None:
    """宫序是前端画盘的坐标：十二宫按地支 index 0-11 递增给出，一宫不多一宫不少。"""
    palaces = _post(client).json()["palaces"]
    assert [palace["index"] for palace in palaces] == list(range(12))
    assert [palace["zhi"] for palace in palaces] == list("子丑寅卯辰巳午未申酉戌亥")
    assert sum(palace["is_ming"] for palace in palaces) == 1
    assert sum(palace["is_shen"] for palace in palaces) == 1
    for palace in palaces:
        assert palace["ganzhi"] == palace["gan"] + palace["zhi"]
        assert palace["name"] and palace["dayun"]
    # 28 颗星一颗不落在盘外：十四主星 + 六吉 + 六煞 + 禄马。
    stars = [star for palace in palaces for star in palace["stars"]]
    assert len(stars) == 28
    assert {star["kind"] for star in stars} == {"主星", "吉", "煞", "禄马"}


def test_major_stars_arrive_with_their_nature_and_yi_stars_without(
    client: TestClient,
) -> None:
    """星格样式按「是否主星」分叉：主星必带 阴阳/星系/星情，乙级三样都必须缺席。

    前端 `StarCell` 用这三个字段决定展开与否；引擎若把乙级也填上，页面会多出十四格
    无出处的星情文案，而 JSON 形状完全合规。
    """
    palaces = _post(client).json()["palaces"]
    majors = [s for p in palaces for s in p["stars"] if s["kind"] == "主星"]
    minors = [s for p in palaces for s in p["stars"] if s["kind"] != "主星"]
    assert len(majors) == 14 and len(minors) == 14
    for star in majors:
        assert star["yin_yang"] in {"阴", "阳"}
        assert star["group"] in {"紫微系", "天府系"}
        assert star["nature"]
    for star in minors:
        assert star["yin_yang"] is None and star["group"] is None and star["nature"] is None


# ------------------------------------------------------------------ 前后端契约对拍


def test_the_response_contains_no_field_the_frontend_never_declared(client: TestClient) -> None:
    """后端多出的字段在页面上是隐形的（前端 interface 里没有它），故必须点名。"""
    body = _post(client).json()
    extra = set(body) - FRONTEND_CHART_KEYS
    assert not extra, f"响应里有前端未声明的顶层字段: {sorted(extra)}"
    for palace in body["palaces"]:
        assert not set(palace) - FRONTEND_PALACE_KEYS, palace["zhi"]
        for star in palace["stars"]:
            assert not set(star) - FRONTEND_STAR_KEYS, star["name"]
    assert not set(body["sihua"]) - FRONTEND_SIHUA_KEYS
    assert not set(body["provenance"]) - FRONTEND_PROVENANCE_KEYS


def test_the_frontend_declares_no_field_the_response_never_sends(client: TestClient) -> None:
    """反方向同样要命：前端照着声明读一个后端不给的字段，页面上就是 `undefined`。"""
    body = _post(client).json()
    assert not FRONTEND_CHART_KEYS - set(body), sorted(FRONTEND_CHART_KEYS - set(body))
    samples: dict[str, dict[str, object]] = {
        "palaces[]": body["palaces"][0],
        "palaces[].stars[]": body["palaces"][0]["stars"][0],
        "sihua": body["sihua"],
        "provenance": body["provenance"],
    }
    for path, _, frontend in KEY_LAYERS:
        node = samples[path]
        assert not frontend - set(node), f"{path} 前端声明了响应里没有的字段: {sorted(frontend - set(node))}"
    # 本模块两份抄写不得自相矛盾（否则上面两条门都在偷工）。
    for path, declared, frontend in KEY_LAYERS:
        assert declared == frontend, f"{path} 的手写契约与前端抄本不同"
    assert TOP_LEVEL_KEYS == FRONTEND_CHART_KEYS


def test_the_openapi_contract_advertises_the_same_key_sets(client: TestClient) -> None:
    """前端类型是照 schema 手写的，schema 与手写契约不一致时以「三方同字」为准。"""
    spec = client.get("/openapi.json").json()
    assert URL in spec["paths"]
    schemas = spec["components"]["schemas"]
    assert set(schemas["ZiweiChart"]["properties"]) == TOP_LEVEL_KEYS
    assert set(schemas["Palace"]["properties"]) == PALACE_KEYS
    assert set(schemas["StarPlacement"]["properties"]) == STAR_KEYS
    assert set(schemas["SiHuaInfo"]["properties"]) == SIHUA_KEYS
    assert set(schemas["ZiweiProvenance"]["properties"]) == PROVENANCE_KEYS
    assert set(schemas["ZiweiRequest"]["required"]) == {"birth_date", "birth_time", "gender"}


# ------------------------------------------------------------------ 422 / 400 分工


def test_gender_is_required_and_its_absence_is_pydantic_validation(client: TestClient) -> None:
    """缺 `gender`：字段自身过不了必填校验 → FastAPI 的 `detail`，不是域错误形状。"""
    payload = {key: value for key, value in PAYLOAD.items() if key != "gender"}
    response = client.post(URL, json=payload)
    assert response.status_code == 422
    body = response.json()
    assert "error" not in body
    assert [list(issue["loc"]) for issue in body["detail"]] == [["body", "gender"]]
    assert body["detail"][0]["type"] == "missing"


@pytest.mark.parametrize("value", ["other", "MALE", "", "男"])
def test_an_unsupported_gender_value_is_rejected_before_the_engine(
    client: TestClient, value: str
) -> None:
    """大限方向只认两个值；引擎没有任何「猜一个方向」的退路（PRD 禁 mock）。"""
    response = _post(client, gender=value)
    assert response.status_code == 422
    body = response.json()
    assert "detail" in body and "error" not in body
    assert body["detail"][0]["type"] == "enum"


@pytest.mark.parametrize("name", ["名" * 41, "x" * 200])
def test_name_length_is_pydantic_validation(client: TestClient, name: str) -> None:
    """长度归 pydantic（40 字上限，`ZiweiRequest.name`），文案回显原样。"""
    response = _post(client, name=name)
    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "string_too_long"
    assert _post(client, name="示例甲").json()["name"] == "示例甲"


@pytest.mark.parametrize(
    "overrides",
    [
        {"longitude": None},  # 无经度无城市
        {"longitude": None, "city": "Nowhereville"},  # 城市查不到
    ],
    ids=["no-location", "unknown-city"],
)
def test_true_solar_time_without_a_usable_location_is_a_domain_error(
    client: TestClient, overrides: dict[str, object]
) -> None:
    """字段之间的关系坏 → 引擎抛 `InvalidBirthDataError` → 400 统一形状（AGENTS.md 第 4 条）。

    这些入参每个字段单看都合法，故绝不能落进 pydantic 的 `detail`；而「地点不明就干脆
    不校正、悄悄按北京时间排盘」是更糟的退路 —— 那会把生时算错一个时辰、整盘星位全换。
    """
    response = _post(client, apply_true_solar_time=True, **overrides)
    assert response.status_code == 400
    body = response.json()
    assert "detail" not in body
    assert body["error"]["code"] == "invalid_birth_data"
    assert body["error"]["message"]


def test_an_out_of_range_coordinate_is_rejected_by_pydantic(client: TestClient) -> None:
    """经度的定义域写在契约里（`ge=-180, le=180`），越界是字段自身的事 → 422。"""
    response = _post(client, longitude=200.0)
    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "less_than_equal"


def test_birth_time_is_mandatory_down_to_the_minute(client: TestClient) -> None:
    """斗数离不开生时（命宫 = 生月 ± 生时），缺生时不能退成「正午」。

    这条与 PRD §3.2/§9 的「未知出生时间按 12:00 起盘 + 时柱待验徽标」互斥，是
    findings F-A1-3 记下的功能缺口：条文落地时本条须连同契约一起重定，不是改断言。
    """
    response = client.post(URL, json={k: v for k, v in PAYLOAD.items() if k != "birth_time"})
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "birth_time"]


# ------------------------------------------------------------------ 历法与地点如实递到浏览器


def test_turning_tst_off_falls_back_to_the_standard_meridian(client: TestClient) -> None:
    """不开校正时不必给地点：经度回落到东经 120° 标准经线，且两个 TST 字段留空。"""
    body = _post(client, longitude=None).json()
    assert body["longitude"] == 120.0
    assert body["tst_applied"] is False
    assert body["true_solar_time"] is None
    assert body["tst_offset_minutes"] is None
    assert body["lunar_date"] == "庚辰年七月十七"


def test_true_solar_time_moves_the_hour_and_therefore_the_whole_board(client: TestClient) -> None:
    """成都（东经 104.07°）校正后 12:00 → 10:51 = 巳时，命宫随之一宫一宫地搬。

    这一条守的是「时辰是诚实的」（PRD §7）：如果后端收下城市却不真校正，
    `true_solar_time` 会与标准时间相同、命宫也纹丝不动，而形状依旧合规。
    """
    body = _post(client, longitude=None, city="成都", apply_true_solar_time=True).json()
    assert body["tst_applied"] is True
    assert body["true_solar_time"] == "2000-08-16 10:51"
    assert body["tst_offset_minutes"] == pytest.approx(-68.6, abs=1.0)
    assert body["time_zhi"] == "巳"
    assert body["ming_gong_zhi"] == "卯"
    # 同一生日在北京经度不校正时是命宫寅 —— 差一宫，全盘星位都不同。
    plain = _post(client).json()
    assert plain["time_zhi"] == "午" and plain["ming_gong_zhi"] == "寅"
    assert [p["stars"] for p in body["palaces"]] != [p["stars"] for p in plain["palaces"]]


def test_a_lunar_input_reproduces_the_same_board_as_its_solar_equivalent(client: TestClient) -> None:
    """农历直入（2000 年七月十七，非闰月）应与公历 2000-08-16 排出同一张盘。"""
    lunar = _post(client, birth_date="2000-07-17", calendar="lunar").json()
    solar = _post(client).json()
    assert lunar["lunar_date"] == solar["lunar_date"] == "庚辰年七月十七"
    assert lunar["lunar_leap"] is False
    for field in ("ming_gong_zhi", "ming_gong_ganzhi", "wuxing_ju", "ziwei_zhi", "tianfu_zhi"):
        assert lunar[field] == solar[field], field
    assert lunar["palaces"] == solar["palaces"]
    assert lunar["sihua"] == solar["sihua"]


#: PRD §4.1 承诺的支持区间两端点（1900–2100）。两张盘都按 `PAYLOAD` 的午时、不开校正，
#: 好让回显的农历串就是断言对象；日期本身另在
#: `tests/golden/test_ziwei_golden.py::SWEPT_BIRTHS` 有引擎层的扫盘锚。
#: 农历串取权威库复核（AGENTS.md 第 6 条：不自算历法）—— 年取 `getYearInGanZhi()`、
#: 月日取 `getMonthInChinese()/getDayInChinese()`，与本断言同形。复测（2026-09-30 实录 → 己亥年腊月初一；把日期换成 2100,12,31 → 庚申年腊月初一）：`cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "from lunar_python import Solar;l=Solar.fromYmdHms(1900,1,1,12,0,0).getLunar();print(l.getYearInGanZhi()+'年'+l.getMonthInChinese()+'月'+l.getDayInChinese())"`
DATE_ENDPOINTS: list[tuple[str, str, str, str, str]] = [
    ("1900-01-01", "己亥年腊月初一", "土五局", "逆行", "未"),
    ("2100-12-31", "庚申年腊月初一", "木三局", "顺行", "未"),
]


@pytest.mark.parametrize(("birth", "lunar", "ju", "direction", "ming_zhi"), DATE_ENDPOINTS)
def test_the_two_prd_date_endpoints_come_back_as_full_boards(
    client: TestClient, birth: str, lunar: str, ju: str, direction: str, ming_zhi: str
) -> None:
    """区间端点必须**整盘**回来，不是「不报错就行」。

    控制台把年份下拉的上限卡在**当前年**，2100 在页面上根本选不到（走查项 5 记此不可达），
    所以这一层只能在这里验：端点若被历法库悄悄裁掉，页面拿到的会是一张缺星缺宫的盘，
    而不是一个错误。
    """
    body = _post(client, birth_date=birth).json()
    assert body["lunar_date"] == lunar
    assert body["wuxing_ju"] == ju and body["dayun_direction"] == direction
    assert body["ming_gong_zhi"] == ming_zhi
    assert len(body["palaces"]) == 12
    ming = [palace for palace in body["palaces"] if palace["is_ming"]]
    assert [(palace["name"], palace["zhi"]) for palace in ming] == [("命宫", ming_zhi)]
    assert [palace["name"] for palace in body["palaces"]].count("命宫") == 1
    # 十四主星之外，乙级星（禄存、擎羊、陀罗、火铃、地空地劫、天马、六吉）也要在场：
    kinds = {star["kind"] for palace in body["palaces"] for star in palace["stars"]}
    assert kinds == {"主星", "吉", "煞", "禄马"}, f"端点盘的星类不齐: {sorted(kinds)}"



# ------------------------------------------------------------------ 确定性与「不许编数」


def test_the_same_request_twice_returns_the_identical_board(client: TestClient) -> None:
    """紫微盘没有任何随机成分：同请求两次必须逐字节相等（PRD §4.1 可复核）。"""
    first = _post(client)
    second = _post(client)
    assert first.status_code == 200
    assert first.json() == second.json()
    assert first.text == second.text


def test_there_is_no_score_or_probability_anywhere_in_the_response(client: TestClient) -> None:
    """这一页每个数都要有诀可追：可信度、概率、百分比一类一个都不许出现。"""
    body = _post(client, city="成都", longitude=None, apply_true_solar_time=True).json()
    keys = _walk_keys(body)
    banned = {
        "score", "confidence", "probability", "percentage", "percent",
        "certainty", "luck_index", "compatibility", "rating",
    }
    assert not (keys & banned), f"响应里出现了编出来的量化字段: {sorted(keys & banned)}"
    assert "%" not in _post(client).text and "％" not in _post(client).text


def test_provenance_names_the_book_and_discloses_the_two_divergences(client: TestClient) -> None:
    """出处与口径必须自己讲清楚：书级出处 + 四化派别 + 闰月口径（+ 大限方向规则）。

    这三处都是「同一生日两派排出来不一样」的地方；不写进响应，读者无从复核，
    而 `tests/content/test_ziwei_corpus.py` 钉的是表体，钉不住派别声明。
    """
    provenance = _post(client).json()["provenance"]
    assert "紫微斗数全书" in provenance["source"]
    assert provenance["content_version"]
    note = provenance["school_note"]
    assert "四化" in note and "全书" in note
    assert "闰月" in note
    assert "阳男阴女顺行" in note and "阴男阳女逆行" in note


def test_the_chart_lists_both_ziwei_tables_in_provenance(client: TestClient) -> None:
    """读了就列（AGENTS §7 / G19）：白话表进响应清单，且清单就是登记常量本身。"""
    body = _post(client).json()
    assert {row["name"] for row in body["provenance"]["tables"]} == {"ziwei", "ziwei_plain"}
    assert all(row["version"] for row in body["provenance"]["tables"])
    assert all(row["source"] for row in body["provenance"]["tables"])


def test_every_palace_carries_a_non_empty_plain_paragraph(client: TestClient) -> None:
    """交付面只钉「必填非空 + 末句成句」：`Palace.plain` 是 `str` 无默认，缺一次就 500。

    逐字对账归 golden（Step 1 已钉 `lines[0] == ZIWEI.openers[palace.name]`），两边不重复
    断言同一件事（AGENTS §2 的同一口径）。
    """
    body = _post(client).json()
    for palace in body["palaces"]:
        assert palace["plain"], palace["name"]
        assert palace["plain"].split("\n")[-1].endswith("。")
