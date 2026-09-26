"""吠陀占星端点契约（Task 7）：键集手写、时移口径如实、错误各归其位、DE431 的沉默要说破。

盘的**对错**测在 `tests/golden/test_vedic_golden.py`（岁差三锚 + Vimshottari 手推 + 27 宿
边界），本模块只管 `POST /api/v1/vedic/natal` 这一层有没有把引擎排好的盘如实、按契约
递出去——所以一律断言 JSON，不 import 引擎函数（分派同 `tests/test_qimen_api.py`）。

五道值得单说的门：

* **键集手写、并与前端 `frontend/src/types/vedic.ts` 各抄一份**：从 `VedicChart.model_fields`
  取会让「悄悄多了一个字段」毫无感觉；两个方向都要点名（后端多给前端不读 = 静默丢信息，
  前端多读后端不给 = `undefined`）。
* **`utc_offset_source` 是这条链上唯一会说谎风险的字段**：给了偏移就是 `explicit`，没给
  就是按经度折的 `longitude_approximation`（`round(lon/15)` 小时）。页面据此印徽标，
  两者混用读者无从分辨「命度差 4 分钟经度 1 度」这类误差是谁造成的。
* **错误分工（AGENTS 第 4 条）**：`latitude/longitude/utc_offset_hours` 的 `ge/le` 边界与
  日期解析归 pydantic → 422 `detail`；缺坐标与查无此城是字段之间/前提问题 → 引擎抛
  `InvalidBirthDataError` → 400 信封 `{error:{code,message}}`，不带 `context`。
* **没有任何字段声明实际用了哪一副星历**：`provenance.engine` 只说 `pyswisseph`，而
  PRD §4.1/§6 六处写「瑞士历表 DE431」；golden 侧实测两法角差 0.0 角秒（本仓与镜像里
  都没有 `.se1/.se2/.mos`，`SWEPH_EPHE_PATH` 默认空）。响应里既没有 `ephemeris_mode`
  也没有精度声明，读者只能信引擎名——本轮把它钉成**现状事实 + finding**（同 Task 6
  对时区口径的处理法：条文落地时连同契约一起重定，不是改断言迁就）。
* **数字的位宽是契约**：页面直接把 `longitude`/`years` 印出来，`round` 的位宽一变，
  设计稿里的定宽表格就错位。逐字段钉位宽，不钉值。

复测本文件测数：`cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m pytest
tests/test_vedic_api.py -v` → 31 passed（2026-09-27 实录，含 422 参数化七条）。
"""

import re
from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.content import CONTENT_VERSION

URL = "/api/v1/vedic/natal"

#: 参考请求：J2000 正午格林尼治，与 golden 同一张盘（键集与 golden 的取值互不重复断言）。
PAYLOAD: dict[str, object] = {
    "birth_date": "2000-01-01",
    "birth_time": "12:00",
    "latitude": 51.4769,
    "longitude": -0.0005,
    "utc_offset_hours": 0,
    "target_date": "2026-09-25",
}

KEY_RE = re.compile(r"^[a-z][a-z0-9_]*$")

#: 目标日只挪 `vimshottari.current`；natal 一侧这些键必须逐字节不动。
NATAL_KEYS = ("local_datetime", "utc_datetime", "julian_day", "ayanamsa", "lagna_degree_text")

# ------------------------------------------------------------------ 契约面（手写）

TOP_LEVEL_KEYS = {
    "local_datetime", "utc_datetime", "julian_day", "latitude", "longitude",
    "utc_offset_hours", "utc_offset_source", "zodiac",
    "ayanamsa", "ayanamsa_name",
    "lagna_sign", "lagna_sign_zh", "lagna_sign_glyph", "lagna_index",
    "lagna_degree_text", "lagna_nakshatra", "lagna_nakshatra_zh",
    "moon_sign", "moon_sign_zh", "moon_nakshatra", "moon_nakshatra_zh",
    "moon_nakshatra_lord", "moon_nakshatra_lord_zh", "moon_pada",
    "planets", "rashis", "vimshottari", "provenance", "engine",
}

PLANET_KEYS = {
    "name", "glyph", "name_zh", "name_sa", "longitude", "sign", "sign_zh", "sign_glyph",
    "sign_index", "degree_in_sign", "degree_text", "house", "nakshatra", "nakshatra_zh",
    "nakshatra_devanagari", "nakshatra_lord", "nakshatra_lord_zh", "pada", "retrograde", "speed",
}

RASHI_KEYS = {"sign_index", "sign", "sign_zh", "sign_glyph", "house", "is_lagna", "planet_names"}

VIMSHOTTARI_KEYS = {
    "total_years", "balance_at_birth_years", "moon_elapsed_fraction", "birth_nakshatra",
    "birth_nakshatra_zh", "birth_lord", "birth_lord_zh", "mahadashas", "current",
}

MAHADASHA_KEYS = {
    "lord", "lord_zh", "glyph", "start_date", "end_date", "years", "is_current", "antardashas",
}

ANTARDASHA_KEYS = {"lord", "lord_zh", "glyph", "start_date", "end_date", "years", "is_current"}
CURRENT_KEYS = {
    "target_date", "mahadasha_lord", "mahadasha_lord_zh", "antardasha_lord", "antardasha_lord_zh",
}
PROVENANCE_KEYS = {"engine", "ayanamsa_name", "content_version", "source", "note"}
REQUEST_KEYS = {
    "birth_date", "birth_time", "city", "latitude", "longitude", "utc_offset_hours", "target_date",
}

KEY_SIZES = {
    "TOP_LEVEL_KEYS": (TOP_LEVEL_KEYS, 29),
    "PLANET_KEYS": (PLANET_KEYS, 20),
    "RASHI_KEYS": (RASHI_KEYS, 7),
    "VIMSHOTTARI_KEYS": (VIMSHOTTARI_KEYS, 9),
    "MAHADASHA_KEYS": (MAHADASHA_KEYS, 8),
    "ANTARDASHA_KEYS": (ANTARDASHA_KEYS, 7),
    "CURRENT_KEYS": (CURRENT_KEYS, 5),
    "PROVENANCE_KEYS": (PROVENANCE_KEYS, 5),
}

# ------------------------------------------------------------------ 前端声明（手抄）
# 照 `frontend/src/types/vedic.ts` 的 interface 逐字重抄；不在后端测试里读前端树，
# 两份各抄一次才有门（抄写约定同 `tests/test_qimen_api.py:72-90`）。

FRONTEND_CHART_KEYS = {
    "local_datetime", "utc_datetime", "julian_day", "latitude", "longitude",
    "utc_offset_hours", "utc_offset_source", "zodiac",
    "ayanamsa", "ayanamsa_name",
    "lagna_sign", "lagna_sign_zh", "lagna_sign_glyph", "lagna_index",
    "lagna_degree_text", "lagna_nakshatra", "lagna_nakshatra_zh",
    "moon_sign", "moon_sign_zh", "moon_nakshatra", "moon_nakshatra_zh",
    "moon_nakshatra_lord", "moon_nakshatra_lord_zh", "moon_pada",
    "planets", "rashis", "vimshottari", "provenance", "engine",
}

FRONTEND_PLANET_KEYS = {
    "name", "glyph", "name_zh", "name_sa", "longitude", "sign", "sign_zh", "sign_glyph",
    "sign_index", "degree_in_sign", "degree_text", "house", "nakshatra", "nakshatra_zh",
    "nakshatra_devanagari", "nakshatra_lord", "nakshatra_lord_zh", "pada", "retrograde", "speed",
}

FRONTEND_RASHI_KEYS = {
    "sign_index", "sign", "sign_zh", "sign_glyph", "house", "is_lagna", "planet_names",
}

FRONTEND_VIMSHOTTARI_KEYS = {
    "total_years", "balance_at_birth_years", "moon_elapsed_fraction", "birth_nakshatra",
    "birth_nakshatra_zh", "birth_lord", "birth_lord_zh", "mahadashas", "current",
}

FRONTEND_MAHADASHA_KEYS = {
    "lord", "lord_zh", "glyph", "start_date", "end_date", "years", "is_current", "antardashas",
}

FRONTEND_ANTARDASHA_KEYS = {
    "lord", "lord_zh", "glyph", "start_date", "end_date", "years", "is_current",
}

FRONTEND_CURRENT_KEYS = {
    "target_date", "mahadasha_lord", "mahadasha_lord_zh", "antardasha_lord", "antardasha_lord_zh",
}

FRONTEND_PROVENANCE_KEYS = {"engine", "ayanamsa_name", "content_version", "source", "note"}

FRONTEND_REQUEST_KEYS = {
    "birth_date", "birth_time", "city", "latitude", "longitude", "utc_offset_hours", "target_date",
}

#: 前端把 `UtcOffsetSource` 声明成字面量联合，后端声明的是裸 `str`——所以联合名单只能在这里钉。
FRONTEND_OFFSET_SOURCES = {"explicit", "longitude_approximation"}

KEY_LAYERS: list[tuple[str, set[str], set[str], str]] = [
    ("planets[]", PLANET_KEYS, FRONTEND_PLANET_KEYS, "VedicPlanet"),
    ("rashis[]", RASHI_KEYS, FRONTEND_RASHI_KEYS, "RashiCell"),
    ("vimshottari", VIMSHOTTARI_KEYS, FRONTEND_VIMSHOTTARI_KEYS, "Vimshottari"),
    ("vimshottari.mahadashas[]", MAHADASHA_KEYS, FRONTEND_MAHADASHA_KEYS, "Mahadasha"),
    ("...mahadashas[].antardashas[]", ANTARDASHA_KEYS, FRONTEND_ANTARDASHA_KEYS, "Antardasha"),
    ("vimshottari.current", CURRENT_KEYS, FRONTEND_CURRENT_KEYS, "CurrentDasha"),
    ("provenance", PROVENANCE_KEYS, FRONTEND_PROVENANCE_KEYS, "VedicProvenance"),
]

# ------------------------------------------------------------------ 词表（手抄，不引语料）

SIDEREAL_SIGNS_EN = (
    "Mesha", "Vrishabha", "Mithuna", "Karka", "Simha", "Kanya",
    "Tula", "Vrischika", "Dhanu", "Makara", "Kumbha", "Meena",
)
SIDEREAL_SIGNS_ZH = ("白羊", "金牛", "双子", "巨蟹", "狮子", "处女",
                     "天秤", "天蝎", "射手", "摩羯", "水瓶", "双鱼")
NAVAGRAHA_EN = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")
NAVAGRAHA_ZH = ("太阳", "太阴", "火星", "水星", "木星", "金星", "土星", "罗睺", "计都")
NAVAGRAHA_SA = ("Surya", "Chandra", "Mangala", "Budha", "Guru", "Shukra", "Shani", "Rahu", "Ketu")


def _post(client: TestClient, **overrides: object):
    return client.post(URL, json={**PAYLOAD, **overrides})


def _body(client: TestClient, **overrides: object) -> dict[str, object]:
    response = _post(client, **overrides)
    assert response.status_code == 200, response.text
    return response.json()


def _walk_keys(node: object) -> set[str]:
    if isinstance(node, dict):
        return set(node) | {key for value in node.values() for key in _walk_keys(value)}
    if isinstance(node, list):
        return {key for item in node for key in _walk_keys(item)}
    return set()


def _decimal_places(value: float) -> int:
    """小数位宽，按十进制展开数（不用 repr：1e-05 那类会带上科学计数法）。"""
    text = format(float(value), ".10f").rstrip("0")
    if "." not in text:
        return 0
    return len(text.split(".")[1])


# ------------------------------------------------------------------ 200 形状


def test_the_chart_comes_back_with_exactly_the_hand_written_contract(client: TestClient) -> None:
    response = _post(client)
    assert response.status_code == 200
    body = response.json()
    assert set(body) == TOP_LEVEL_KEYS
    assert len(TOP_LEVEL_KEYS) == 29  # 尺寸哨兵：抄漏一格上面那条相等就直接红，这条管的是两侧同时缩水
    assert body["engine"] == "pyswisseph"  # 引擎名在两处出现，见出处那一条测
    assert body["zodiac"] == "sidereal"
    assert body["ayanamsa_name"] == "Lahiri (Chitrapaksha)"
    assert body["local_datetime"] == "2000-01-01 12:00"
    assert body["utc_datetime"] == "2000-01-01 12:00"  # 偏移 0：本地即 UT
    assert body["latitude"] == 51.4769 and body["longitude"] == -0.0005
    assert body["moon_pada"] == 4


def test_the_declared_key_sets_keep_their_declared_sizes() -> None:
    """八层键集的尺寸哨兵单独一条：某层被同时抄短，上面那些相等断言会一起哑掉。"""
    for name, (keys, size) in KEY_SIZES.items():
        assert len(keys) == size, name


def test_nested_objects_carry_exactly_their_declared_keys(client: TestClient) -> None:
    """九曜、十二宫、大运、小运、当前段、出处六件 nested 对象的键集同样钉死。"""
    body = _body(client)
    assert len(body["planets"]) == 9 and len(body["rashis"]) == 12
    for planet in body["planets"]:
        assert set(planet) == PLANET_KEYS, planet["name"]
    for cell in body["rashis"]:
        assert set(cell) == RASHI_KEYS, cell["sign_index"]
    vs = body["vimshottari"]
    assert set(vs) == VIMSHOTTARI_KEYS
    for md in vs["mahadashas"]:
        assert set(md) == MAHADASHA_KEYS, md["lord"]
        for ad in md["antardashas"]:
            assert set(ad) == ANTARDASHA_KEYS, (md["lord"], ad["lord"])
    # 默认 PAYLOAD 的目标日（2026-09-25）在出生之后，`current` 必不为 null；真成了 null
    # 就该红，而不是静默跳过这一层。「出生前的目标日 → current 为 null」那一形状另有其主：
    # `test_a_target_date_before_birth_leaves_no_current_period`。
    assert vs["current"] is not None
    assert set(vs["current"]) == CURRENT_KEYS
    assert set(body["provenance"]) == PROVENANCE_KEYS


def test_the_response_is_snake_case_end_to_end(client: TestClient) -> None:
    """AGENTS 第 3 条：后端 JSON 全 snake_case，前端不重命名——一个驼峰键就是 undefined。"""
    keys = _walk_keys(_body(client))
    assert keys, "响应树里一个键都没有，说明抄错了 URL"
    assert [key for key in keys if not KEY_RE.match(key)] == []


def test_the_json_numbers_respect_the_declared_rounding(client: TestClient) -> None:
    """位宽是契约：页面按定宽印度数与值年，round 的位数一变表格就错位。

    引擎侧的 round 位宽（`app/engines/vedic.py`）：黄经与 ayanamsa 4 位、儒略日 5 位、
    速度 6 位、值年与宿内比例分别 4 位与 6 位；星座内度数走
    `app/engines/western.py:80-81` 的 `_degree_in_sign`，也是 4 位。
    """
    body = _body(client)
    assert _decimal_places(body["julian_day"]) <= 5
    assert _decimal_places(body["ayanamsa"]) <= 4
    for planet in body["planets"]:
        assert _decimal_places(planet["longitude"]) <= 4, planet["name"]
        assert _decimal_places(planet["speed"]) <= 6, planet["name"]
        # 上限 4 的出处是 `western._degree_in_sign` 的 `round(..., 4)`；原来给 6 宽了两档，
        # 八曜实测最多 4 位小数（2026-09-27）。
        assert _decimal_places(planet["degree_in_sign"]) <= 4, planet["name"]
    vs = body["vimshottari"]
    assert _decimal_places(vs["balance_at_birth_years"]) <= 4
    assert _decimal_places(vs["moon_elapsed_fraction"]) <= 6
    for md in vs["mahadashas"]:
        assert _decimal_places(md["years"]) <= 4, md["lord"]
        for ad in md["antardashas"]:
            assert _decimal_places(ad["years"]) <= 4, (md["lord"], ad["lord"])


# ------------------------------------------------------------------ 词表与取值范围


def test_the_graha_and_rashi_vocabularies_are_the_published_ones(client: TestClient) -> None:
    """九曜三名（英/中/梵）与十二宿曜名（梵/中）逐位对齐，序列本身独立手抄。

    这是键集之外的另一头：键对了但词表串行（例如把「计都」排到 Rahu 上），页面照样印错。
    """
    body = _body(client)
    assert [p["name"] for p in body["planets"]] == list(NAVAGRAHA_EN)
    assert [p["name_zh"] for p in body["planets"]] == list(NAVAGRAHA_ZH)
    assert [p["name_sa"] for p in body["planets"]] == list(NAVAGRAHA_SA)
    assert [r["sign"] for r in body["rashis"]] == list(SIDEREAL_SIGNS_EN)
    assert [r["sign_zh"] for r in body["rashis"]] == list(SIDEREAL_SIGNS_ZH)
    lagna_index = body["lagna_index"]
    for cell in body["rashis"]:
        assert cell["sign_glyph"]
        # 整宫制：宫号 = 星座序相对命度所在星座的顺数偏移，与命度落在哪一宫无关。
        assert cell["house"] == ((cell["sign_index"] - lagna_index) % 12) + 1
        assert cell["is_lagna"] == (cell["sign_index"] == lagna_index)
    assert sum(1 for r in body["rashis"] if r["is_lagna"]) == 1
    assert next(r for r in body["rashis"] if r["is_lagna"])["house"] == 1
    assert sum(len(r["planet_names"]) for r in body["rashis"]) == 9


def test_every_graha_stays_inside_the_declared_ranges(client: TestClient) -> None:
    """0–360 黄经、0–11 星座序、1–12 宫、1–4 足、0–30 宿内度、逆行与速度同号：六个取值域各钉一次。"""
    for planet in _body(client)["planets"]:
        assert 0.0 <= planet["longitude"] < 360.0, planet["name"]
        assert 0 <= planet["sign_index"] <= 11
        assert 1 <= planet["house"] <= 12
        assert 1 <= planet["pada"] <= 4
        assert planet["retrograde"] == (planet["speed"] < 0), planet["name"]
        assert planet["nakshatra"] and planet["nakshatra_zh"] and planet["nakshatra_devanagari"]
        assert planet["nakshatra_lord"] in NAVAGRAHA_EN
        # 半开区间而不是 `<= 30`：`degree_in_sign` 是 `_normalize_longitude(lon) % 30` 再 round
        # 的余数（`app/engines/western.py:80-81`），30 这一端结构上取不到；写成闭区间就是允许
        # 一个引擎永远给不出的值，也就不再是「域」的契约而是废话的契约。
        assert 0.0 <= planet["degree_in_sign"] < 30.0, planet["name"]
        assert re.fullmatch(r"\d{1,2}°\d{2}'", planet["degree_text"]), planet["degree_text"]


def test_the_dasha_lords_are_navagraha_and_the_windows_are_iso_dates(client: TestClient) -> None:
    """大运主必须仍是九曜之一，日期一律 `YYYY-MM-DD`——页面直接排时间轴。"""
    vs = _body(client)["vimshottari"]
    assert vs["total_years"] == 120
    assert vs["birth_lord"] in NAVAGRAHA_EN
    assert vs["birth_lord_zh"] in NAVAGRAHA_ZH
    for md in vs["mahadashas"]:
        assert md["lord"] in NAVAGRAHA_EN and md["lord_zh"] in NAVAGRAHA_ZH
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", md["start_date"])
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", md["end_date"])
        assert md["glyph"]
        for ad in md["antardashas"]:
            assert ad["lord"] in NAVAGRAHA_EN and ad["lord_zh"] in NAVAGRAHA_ZH
            assert ad["start_date"] <= ad["end_date"]


# ------------------------------------------------------------------ 时移来源分支


def test_an_explicit_utc_offset_is_echoed_verbatim(client: TestClient) -> None:
    """给了偏移就是 `explicit`，且 UTC 时刻 = 本地钟点 − 偏移（含半小时区）。"""
    body = _body(client, utc_offset_hours=5.5)
    assert body["utc_offset_source"] == "explicit"
    assert body["utc_offset_hours"] == 5.5
    assert body["local_datetime"] == "2000-01-01 12:00"
    assert body["utc_datetime"] == "2000-01-01 06:30"


def test_an_omitted_utc_offset_is_replaced_by_the_longitude_zone(client: TestClient) -> None:
    """不给偏移时按经度折时区，并如实标 `longitude_approximation`。

    东经 116.4074 → round(116.4074/15) = 8 小时；西经 52.0 → round(−3.4667) = −3 小时。
    第二支取的是赤道上的西经 52°（北大西洋东侧），只是一个经度样本点、不对应任何城市，
    变量名照此自陈；原来叫 `denver` 是误称——丹佛在西经 105° 一带，折出来是 −7 小时。
    这条分支是真值差：折出来的区时与实测时区可差数小时，命度随之漂移。
    """
    beijing = _body(client, longitude=116.4074, latitude=39.9042, utc_offset_hours=None)
    assert beijing["utc_offset_source"] == "longitude_approximation"
    assert beijing["utc_offset_hours"] == 8.0
    assert beijing["utc_datetime"] == "2000-01-01 04:00"
    west_atlantic = _body(client, longitude=-52.0, latitude=0.0, utc_offset_hours=None)
    assert west_atlantic["utc_offset_source"] == "longitude_approximation"
    assert west_atlantic["utc_offset_hours"] == -3.0
    # 前端把该字段声明成两个字面量的联合，后端类型是裸 str：名单在此钉死。
    assert {west_atlantic["utc_offset_source"], "explicit"} == FRONTEND_OFFSET_SOURCES


def test_the_two_offset_routes_disagree_about_the_same_clock_reading(client: TestClient) -> None:
    """同一串钟点，`explicit=0` 与「按经度折 8 小时」给出两张不同的盘：徽标不能省。"""
    explicit = _body(client, latitude=39.9042, longitude=116.4074, utc_offset_hours=0)
    folded = _body(client, latitude=39.9042, longitude=116.4074, utc_offset_hours=None)
    assert explicit["utc_datetime"] == "2000-01-01 12:00"
    assert folded["utc_datetime"] == "2000-01-01 04:00"
    assert explicit["julian_day"] != folded["julian_day"]
    explicit_longitudes = [p["longitude"] for p in explicit["planets"]]
    folded_longitudes = [p["longitude"] for p in folded["planets"]]
    assert explicit_longitudes != folded_longitudes
    assert explicit["lagna_degree_text"] != folded["lagna_degree_text"]


def test_the_city_branch_fills_coordinates_and_explicit_ones_win(client: TestClient) -> None:
    """城市名解析出的坐标照原样回显；同时给坐标时坐标优先（`app/solar/geo.py` 的口径）。"""
    from_city = _body(client, city="北京", latitude=None, longitude=None)
    assert from_city["latitude"] == 39.905 and from_city["longitude"] == 116.4053
    both = _body(client, city="北京")
    assert (both["latitude"], both["longitude"]) == (51.4769, -0.0005)


# ------------------------------------------------------------------ 目标日只管大运


def test_only_the_dasha_marker_moves_when_the_target_date_moves(client: TestClient) -> None:
    """`target_date` 是「今天走到哪一大运」的读数点，不许挪动本命盘分毫。"""
    early = _body(client, target_date="2001-06-01")
    late = _body(client, target_date="2050-01-01")
    for key in NATAL_KEYS:
        assert early[key] == late[key], key
    assert early["planets"] == late["planets"] and early["rashis"] == late["rashis"]
    assert early["vimshottari"]["mahadashas"][:1] == late["vimshottari"]["mahadashas"][:1]
    assert early["vimshottari"]["current"]["target_date"] == "2001-06-01"
    assert late["vimshottari"]["current"]["target_date"] == "2050-01-01"
    assert early["vimshottari"]["current"] != late["vimshottari"]["current"]


def test_a_target_date_before_birth_leaves_no_current_period(client: TestClient) -> None:
    """区间外的目标日不是错误：轴从出生起算，早于出生就只有「无当前段」这一种形状。

    `VedicNatalRequest.target_date` 没有 `ge` 约束，引擎按 `start <= t < end` 判定，
    出生前的日期落在所有窗口之外——`current` 为 null，且没有任何 `is_current` 为真。
    前端 `Vimshottari.current` 声明成可空，正是为这一状态留的。
    """
    body = _body(client, target_date="1999-12-31")
    assert body["vimshottari"]["current"] is None
    assert sum(1 for md in body["vimshottari"]["mahadashas"] if md["is_current"]) == 0
    assert sum(1 for md in body["vimshottari"]["mahadashas"]
               for ad in md["antardashas"] if ad["is_current"]) == 0


def test_the_missing_target_date_defaults_to_the_servers_today(client: TestClient) -> None:
    """缺省 `target_date` 时取**服务器自己那天**（`app/api/v1/vedic.py:31` 的
    `request.target_date or date.today()`），钉的就是这条契约。

    本测拿客户端的 `date.today()` 去比响应：两端读的是同一台机器的同一个钟，所以今天绿、
    明天仍然绿。但这份耦合是实打实的**跨日竞态**——服务端与测试进程一旦分属两台机器或两个
    时区（UTC 与本地日界不同步）、或 CI 时钟偏移，它和
    `test_a_target_date_before_birth_leaves_no_current_period`（那条靠固定日期才稳）就会红。
    不冻结日期是刻意的：冻结得往生产代码里加时钟注入点，本轮一行 `app/**` 都不动。
    这条不适用于给了 `target_date` 的载荷：其余各测各自指定日期，出生前那条尤其要断的正是
    「无当前段」，与默认值无关。
    """
    body = _body(client, target_date=None)
    today = date.today().isoformat()
    assert body["vimshottari"]["current"] is not None
    assert body["vimshottari"]["current"]["target_date"] == today
    assert sum(1 for md in body["vimshottari"]["mahadashas"] if md["is_current"]) == 1


def test_the_endpoint_is_a_pure_function_of_the_payload(client: TestClient) -> None:
    """排盘无随机（AGENTS 第 5 条只约束抽签类引擎）：同请求两次逐字节相同。"""
    first = _post(client)
    second = _post(client)
    assert first.status_code == 200
    assert first.json() == second.json()
    assert first.text == second.text


# ------------------------------------------------------------------ 错误分工


@pytest.mark.parametrize(
    "field, value, code",
    [
        ("latitude", 91, "less_than_equal"),
        ("latitude", -91, "greater_than_equal"),
        ("longitude", 181, "less_than_equal"),
        ("longitude", -181, "greater_than_equal"),
        ("utc_offset_hours", 15, "less_than_equal"),
        ("utc_offset_hours", -15, "greater_than_equal"),
        ("target_date", "nope", "date_from_datetime_parsing"),
    ],
    ids=["纬度上限", "纬度下限", "经度上限", "经度下限", "偏移上限", "偏移下限", "目标日解析"],
)
def test_field_level_bounds_are_pydantic_validation(client: TestClient, field: str, value: object,
                                                    code: str) -> None:
    """每个字段单独看就不合法 → 422 `detail`，不是信封（AGENTS 第 4 条）。"""
    response = _post(client, **{field: value})
    assert response.status_code == 422
    body = response.json()
    assert "error" not in body
    assert body["detail"][0]["loc"] == ["body", field]
    assert body["detail"][0]["type"] == code


@pytest.mark.parametrize(
    "overrides",
    [
        {"latitude": None, "longitude": None},
        {"city": "不存在市", "latitude": None, "longitude": None},
    ],
    ids=["裸请求缺坐标", "查无此城"],
)
def test_a_missing_or_unresolvable_location_is_an_envelope(client: TestClient,
                                                           overrides: dict[str, object]) -> None:
    """字段之间的问题（每个字段单独看都合法/缺的是前提）归引擎 → 400 机器码信封。

    `InvalidBirthDataError` 走基类默认 400（`app/core/errors.py:10`），不是 422；
    两条路径都不带 `context`——那是给需要按钮的候选列表用的（姓名学简繁那类）。
    """
    response = _post(client, **overrides)
    assert response.status_code == 400
    body = response.json()
    assert "detail" not in body
    assert set(body["error"]) == {"code", "message"}
    assert body["error"]["code"] == "invalid_birth_data"
    assert body["error"]["message"]


def test_the_birth_data_fields_are_the_only_required_ones(client: TestClient) -> None:
    """缺 birth_date / birth_time 各自 422 `missing`，其余五项都可省（城市或坐标至少给一处）。"""
    for field in ("birth_date", "birth_time"):
        payload = dict(PAYLOAD)
        payload.pop(field)
        response = client.post(URL, json=payload)
        assert response.status_code == 422, field
        assert response.json()["detail"][0]["type"] == "missing"
        assert response.json()["detail"][0]["loc"] == ["body", field]


# ------------------------------------------------------------------ 出处诚实性


def test_provenance_names_the_frame_the_spans_and_the_no_fortune_clause(client: TestClient) -> None:
    """出处四件套自证口径：岁差名、13°20′ 宿宽、120 年九曜值年、不虚构吉凶（AGENTS 第 7 条）。"""
    provenance = _body(client)["provenance"]
    assert provenance["content_version"] == CONTENT_VERSION
    assert provenance["ayanamsa_name"] == "Lahiri (Chitrapaksha)"
    source = provenance["source"]
    for declared in ("Lahiri", "Chitrapaksha", "13°20'", "120 年", "Navagraha"):
        assert declared in source, declared
    note = provenance["note"]
    for declared in ("恒星黄道", "整宫制", "不含天王、海王、冥王三王星",
                     "计都·金星·太阳·太阴·火星·罗睺·木星·土星·水星", "未作任何主观吉凶"):
        assert declared in note, declared


def test_no_field_of_the_response_claims_which_ephemeris_actually_ran(client: TestClient) -> None:
    """现状事实 + finding：响应只报 `pyswisseph`，不报它到底读了 DE 文件还是走了 Moshier。

    golden 那侧实测（2026-09-27）：本仓与镜像里没有 `.se1/.se2/.mos`，
    `SWEPH_EPHE_PATH` 默认空 → 计算走 `FLG_MOSEPH`，而同一瞬时按 `FLG_SWIEPH` 请求得到的
    八曜黄经逐位相同（最大角差 0.0 角秒，swe 回报的 retflags 里带的是 MOSEPH 位），
    不抛错也不降级报警。于是 PRD §4.1/§6 的「瑞士历表 DE431」在运行时没有任何兜着的东西。
    已上线前端全文没有「DE431」字样（只有「瑞士星历 pyswisseph」），那句话两种模式下都
    为真，所以缺口在 PRD 与运行时之间，不在文案与运行时之间：AGENTS 第 7 条也已裁定
    design/*/code.html 不是契约。修法二选一（(a) 把 DE 文件配进镜像 / (b) 把声称下调为
    「pyswisseph（默认 Moshier 解析历）」），由控制器裁定；无论走哪条，本测与 golden 的
    星历模式那两条一起重定，而不是删断言。
    """
    body = _body(client)
    assert body["engine"] == "pyswisseph"
    assert body["provenance"]["engine"] == body["engine"]  # 两处引擎名不得各说各话
    offenders = {key for key in _walk_keys(body)
                 if re.search(r"mode|ephe|de43|precis|accura", key, re.IGNORECASE)}
    assert offenders == set(), offenders
    text = _post(client).text
    assert "DE431" not in text and "Moshier" not in text


def test_the_openapi_contract_advertises_the_same_key_sets(client: TestClient) -> None:
    """前端类型照 schema 手写，所以「手写契约 == schema == 响应」三方必须同字。"""
    spec = client.get("/openapi.json").json()
    assert URL in spec["paths"]
    schemas = spec["components"]["schemas"]
    assert set(schemas["VedicChart"]["properties"]) == TOP_LEVEL_KEYS
    for path, declared, _, model in KEY_LAYERS:
        assert set(schemas[model]["properties"]) == declared, path
    assert set(schemas["VedicNatalRequest"]["properties"]) == REQUEST_KEYS
    assert schemas["VedicNatalRequest"]["required"] == ["birth_date", "birth_time"]


def test_the_response_contains_no_field_the_frontend_never_declared(client: TestClient) -> None:
    """后端多出的字段在页面上是隐形的（前端 interface 里没有它），故必须点名。"""
    body = _body(client)
    assert not set(body) - FRONTEND_CHART_KEYS, sorted(set(body) - FRONTEND_CHART_KEYS)
    for planet in body["planets"]:
        assert not set(planet) - FRONTEND_PLANET_KEYS, planet["name"]
    for cell in body["rashis"]:
        assert not set(cell) - FRONTEND_RASHI_KEYS, cell["sign_index"]
    vs = body["vimshottari"]
    assert not set(vs) - FRONTEND_VIMSHOTTARI_KEYS
    for md in vs["mahadashas"]:
        assert not set(md) - FRONTEND_MAHADASHA_KEYS, md["lord"]
        for ad in md["antardashas"]:
            assert not set(ad) - FRONTEND_ANTARDASHA_KEYS, (md["lord"], ad["lord"])
    # 默认 PAYLOAD 的目标日在出生之后 → current 恒不为 null（null 那一形状由
    # `test_a_target_date_before_birth_leaves_no_current_period` 用另一份载荷钉）。
    assert vs["current"] is not None
    assert not set(vs["current"]) - FRONTEND_CURRENT_KEYS
    assert not set(body["provenance"]) - FRONTEND_PROVENANCE_KEYS


def test_the_frontend_declares_no_field_the_response_never_sends(client: TestClient) -> None:
    """反方向同样要命：前端读一个后端不给的字段，页面上就是 `undefined`。"""
    body = _body(client)
    assert not FRONTEND_CHART_KEYS - set(body), sorted(FRONTEND_CHART_KEYS - set(body))
    vs = body["vimshottari"]
    samples: dict[str, dict[str, object]] = {
        "planets[]": body["planets"][0],
        "rashis[]": body["rashis"][0],
        "vimshottari": vs,
        "vimshottari.mahadashas[]": vs["mahadashas"][0],
        "...mahadashas[].antardashas[]": next(
            ad for md in vs["mahadashas"] for ad in md["antardashas"]
        ),
        "vimshottari.current": vs["current"],
        "provenance": body["provenance"],
    }
    # 默认 PAYLOAD 下 current 必不为 null（同 `test_nested_objects_carry_exactly_their_declared_keys`
    # 的口径），所以原来那句「可能为 null」和 `or {}` 的死分支一并去掉：真为 null 就是要红，
    # 而不是这一层 quietly 不测。「出生前的目标日」那种载荷归
    # `test_a_target_date_before_birth_leaves_no_current_period` 管。
    assert vs["current"] is not None
    for path, declared, frontend, _ in KEY_LAYERS:
        node = samples[path]
        assert not frontend - set(node), f"{path} 前端声明了响应里没有的字段: {sorted(frontend - set(node))}"
        assert declared == frontend, f"{path} 的手写契约与前端抄本不同"
    assert TOP_LEVEL_KEYS == FRONTEND_CHART_KEYS
    assert REQUEST_KEYS == FRONTEND_REQUEST_KEYS
