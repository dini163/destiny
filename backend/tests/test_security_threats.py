"""轴 3（安全与威胁面）的机器侧：简报威胁表逐行落地。

判据来自 `.superpowers/sdd/2026-09-26-fullstack-test/task-12-controller-addendum.md`
第三节（权威现状），每条测的 docstring 引它所钉的**行名**。跑法（2026-09-27 全绿）：
`cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m pytest tests/test_security_threats.py -p no:warnings`

不在此文件立案的三行（诚实处置，见报告）：
- 「部署面暴露」（`/docs` `/openapi.json` 全开）属用户决策 → ledger，不测。
- 「隐私声称与实现不符」（`SiteFooter.tsx` 与 `main.py` docstring 声称本地 E2EE）→ Task 13。
- 「无鉴权响应放大」（错误体逐字回显用户输入，F-A3-1）→ 只进 findings，测层零条：
  把「422 的 input 里含完整请求体」钉成断言会在修法落地（裁掉 input）时转红，故不许钉。
随机源的「抽签引擎只用 `secrets`」半边由 `test_architecture.py::test_draw_engines_use_csprng`
独占（AGENTS 两端不得重复断言），本文件只补分布级「连续抽取不重合」。
"""

import ast
import importlib
import pkgutil
import re
import unicodedata
from pathlib import Path
from typing import Any, get_args, get_origin

import app.schemas as _schemas_pkg
import pytest
from annotated_types import Ge, Le, MaxLen
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.main import create_app
from app.schemas.bazi_hehun import BaziHehunRequest
from app.schemas.bazi_liuri import BaziLiuriResult, TransitDayCell
from app.schemas.bazi_liushi import BaziLiushiResult, TransitHourCell

BACKEND = Path(__file__).resolve().parents[1]
APP = BACKEND / "app"
NGINX_CONF = BACKEND.parent / "frontend" / "nginx.conf"

_JSON = {"Content-Type": "application/json"}
_BASE_NATAL: dict[str, Any] = {
    "birth_date": "1990-01-01",
    "birth_time": "10:00",
    "calendar": "solar",
    "city": "北京",
    "gender": "male",
}


# --------------------------------------------------------------------------- #
# 行 1：无鉴权 + 无限流的计算型 DoS —— 每个会迭代的结构都有硬上限
# --------------------------------------------------------------------------- #
def _ge_le(field: Any) -> tuple[float | None, float | None]:
    md = field.metadata
    ge = next((m.ge for m in md if isinstance(m, Ge)), None)
    le = next((m.le for m in md if isinstance(m, Le)), None)
    return ge, le


def test_compute_dos_iteration_bounds_are_hard_capped() -> None:
    """钉「无鉴权 + 无限流的计算型 DoS」行：所有驱动循环的计数在 schema 层就封顶。

    简报把这一行写成"合婚 21 年轴 ≈3.5 s / 30 年 ≈29 KB"的计时面；addendum 复量推翻——
    30 年反而更快，每请求成本由两张本命盘合成主导，轴长几乎不影响。所以威胁不是"轴长计时"，
    而是"某个可迭代结构无上界"。这一测用 schema 反射证明每一个迭代计数都是编译期硬边界，
    与 `test_bazi_hehun_api` 只发一个越界值看 422 不是同一件事（那条钉行为，这条钉边界存在）。
    """
    # 唯一走 pydantic 的用户可控轴长：合婚 axis_years 1..30。
    assert _ge_le(BaziHehunRequest.model_fields["axis_years"]) == (1, 30)
    # 矩阵规模的上界由响应模型的边界锁死：流日段 ≤ 31 格（公历月最大），流时恒 12 格。
    assert _ge_le(BaziLiuriResult.model_fields["month_index"]) == (0, 11)
    assert _ge_le(BaziLiushiResult.model_fields["month_index"]) == (0, 11)
    assert _ge_le(TransitDayCell.model_fields["weekday"]) == (0, 6)
    assert _ge_le(BaziLiushiResult.model_fields["weekday"]) == (0, 6)
    assert _ge_le(TransitHourCell.model_fields["index"]) == (0, 11)


# --------------------------------------------------------------------------- #
# 行 2：日期/时间极值
# --------------------------------------------------------------------------- #
def test_extreme_and_edge_dates_never_leak_internals(client: TestClient) -> None:
    """钉「日期/时间极值」行：`date.min`/`date.max`、闰年 2-29、`time` 到微秒都被干净处理。

    addendum 未覆盖此行，照简报原样测。实测（2026-09-27）：合法极端日 0001-01-01 / 9999-12-31
    返回 200；23:59:59 与带微秒的时刻返回 200（分钟精度，秒/微秒被吸收）；非法日历日 2023-02-29
    被 pydantic 挡成 422。任何一条都不得泄 traceback 或崩到 500。
    """
    for iso in ("0001-01-01", "1900-01-01", "9999-12-31"):
        r = client.post(
            "/api/v1/bazi/natal",
            json={**_BASE_NATAL, "birth_date": iso, "birth_time": "23:59:59"},
        )
        assert r.status_code == 200, (iso, r.text[:120])
        assert r.json()["four_pillars"]

    # 闰日（闰年 2-29）正常排盘；秒/微秒精度不致崩。
    leap = client.post(
        "/api/v1/bazi/natal",
        json={**_BASE_NATAL, "birth_date": "2000-02-29", "birth_time": "23:59:59.123456"},
    )
    assert leap.status_code == 200, leap.text[:120]

    # 平年 2-29 是非法日历日 → pydantic 422，不是域错误、更不是 500。
    bad = client.post(
        "/api/v1/bazi/natal",
        json={**_BASE_NATAL, "birth_date": "2023-02-29"},
    )
    assert bad.status_code == 422
    assert "error" not in bad.json()


# --------------------------------------------------------------------------- #
# 行 3：非法经纬度（含 NaN / Infinity）
# --------------------------------------------------------------------------- #
def test_coordinate_bounds_reject_out_of_range(client: TestClient) -> None:
    """钉「非法经纬度」行的有限越界半边：`common.py` 的 `ge/le` 把 lat/lon 挡在 422。

    `latitude ∈ [-90, 90]`、`longitude ∈ [-180, 180]`（`app/schemas/common.py:30-31`）。
    边界值放行、越界一格即 422，且报错定位精确指向越界的那一个字段（另一个留在合法域内），
    不被其它字段吸走。
    """
    for field, edge, over, under, bound_over, bound_under in (
        ("latitude", 90.0, 90.0001, -90.0001, "less_than_equal", "greater_than_equal"),
        ("longitude", 180.0, 180.0001, -180.0001, "less_than_equal", "greater_than_equal"),
    ):
        other = 0.0
        ok = client.post(
            "/api/v1/bazi/natal",
            json={
                **_BASE_NATAL,
                "city": None,
                "latitude": edge if field == "latitude" else other,
                "longitude": edge if field == "longitude" else other,
            },
        )
        assert ok.status_code == 200, (field, ok.text[:120])
        for bad_value, expect_type in ((over, bound_over), (under, bound_under)):
            r = client.post(
                "/api/v1/bazi/natal",
                json={
                    **_BASE_NATAL,
                    "city": None,
                    "latitude": bad_value if field == "latitude" else other,
                    "longitude": bad_value if field == "longitude" else other,
                },
            )
            assert r.status_code == 422, (field, bad_value, r.text[:120])
            items = r.json()["detail"]
            assert {item["loc"][-1] for item in items} == {field}
            assert {item["type"] for item in items} == {expect_type}


def test_nonfinite_coordinates_never_yield_a_chart() -> None:
    """钉「非法经纬度」行的 NaN/Infinity 半边：非有限浮点绝不得产出一张盘。

    addendum 明写"NaN/Infinity 行为未测，留给执行者实测"。实测（2026-09-27）：
    `NaN`/`Infinity` 是 python-json 解码器接受但**非严格 JSON** 的字面量（TestClient 的
    `json=` 通道因 `allow_nan=False` 直接拒发，只能走 raw body）；服务端收下后 `ge/le` 判
    NaN 失败进入 422 序列化，而 Starlette 的 JSON 响应同样 `allow_nan=False`，回抛
    `ValueError: Out of range float values...` → 最终 **500**（错误序列化自崩，是一个已立案
    健壮性面，见报告）。此断言只钉安全底线：**永不 2xx**，因此将来把它修成干净的 422 也仍绿。
    """
    quiet = TestClient(create_app(), raise_server_exceptions=False)
    for literal in ("NaN", "Infinity"):
        body = (
            '{"birth_date":"1990-01-01","birth_time":"10:00","calendar":"solar",'
            f'"gender":"male","city":null,"latitude":{literal},"longitude":0.0}}'
        )
        r = quiet.post("/api/v1/bazi/natal", content=body.encode("utf-8"), headers=_JSON)
        assert r.status_code >= 400, (literal, r.status_code, r.text[:120])


# --------------------------------------------------------------------------- #
# 行 4：超长/异形字符串 —— 钉有界的那一半，无界的 24 个只进 ledger（见报告）
# --------------------------------------------------------------------------- #
def _strip_optional(ann: Any) -> Any:
    args = get_args(ann)
    if args:
        keep = tuple(a for a in args if a is not type(None))
        if len(keep) == 1:
            return keep[0]
    return ann


def _bounded_string_leaves() -> dict[str, int]:
    """反射全部 `*Request` 模型（含嵌套子模型），返回 {限定路径: max_length} 的有界 str 叶。"""
    requests: dict[str, type[BaseModel]] = {}
    for m in pkgutil.iter_modules(_schemas_pkg.__path__):
        mod = importlib.import_module(f"app.schemas.{m.name}")
        for name in dir(mod):
            obj = getattr(mod, name)
            if isinstance(obj, type) and issubclass(obj, BaseModel) and name.endswith("Request"):
                requests.setdefault(name, obj)
    assert len(requests) == 19, sorted(requests)

    out: dict[str, int] = {}

    def walk(model: type[BaseModel], prefix: str) -> None:
        for fname, f in model.model_fields.items():
            path = f"{prefix}.{fname}"
            ann = _strip_optional(f.annotation)
            ml = next((x.max_length for x in f.metadata if isinstance(x, MaxLen)), None)
            if ann is str:
                if ml is not None:
                    out[path] = ml
            elif get_origin(ann) is dict and get_args(ann)[1] is str:
                if ml is not None:
                    out[path + "[]"] = ml
            elif isinstance(ann, type) and issubclass(ann, BaseModel):
                walk(ann, path)

    for name in sorted(requests):
        walk(requests[name], name)
    return out


# addendum 第三节行 4 的有界清单（41 个自由文本 str 叶里的 17 个有界者）。
# 复测：本文件的 `_bounded_string_leaves()`（走完嵌套，含 Hehun/Synastry 的子模型）。
_EXPECTED_BOUNDED: dict[str, int] = {
    "BaziHehunRequest.female.name": 40,
    "BaziHehunRequest.male.name": 40,
    "BaziLiuriRequest.name": 40,
    "BaziLiushiRequest.name": 40,
    "BaziNatalRequest.name": 40,
    "BaziTransitRequest.name": 40,
    "GematriaRequest.text": 64,
    "LenormandRequest.question": 120,
    "NameAnalyzeRequest.given": 3,
    "NameAnalyzeRequest.surname": 2,
    "NumerologyChartRequest.full_name": 80,
    "NumerologyChartRequest.name_zh": 20,
    "QimenRequest.question": 120,
    "RuneCastRequest.question": 120,
    "SynastryRequest.person_a.name": 40,
    "SynastryRequest.person_b.name": 40,
    "ZiweiRequest.name": 40,
}


def test_string_input_caps_present_in_registry_survive() -> None:
    """钉「超长/异形字符串」行的可钉半边：17 个已声明上限的自由文本字段一个都不能丢/不能放。

    简报"逐个请求模型断言**每个** str 入参都有上限"今天为假（addendum 复量：41 叶里 24 个
    无上限，其中 `city` ×12、`house_system`/`spread_id`/`question` 各 3 等），照写即永久红灯，
    违"不立永久红灯"裁定——那 24 个作为「已接受面」整张进 ledger/报告，不在此断言。
    这里只锁**有界的这一半**：若哪天有人删掉或放宽其中一个 `max_length`，反射出的表就会与
    登记清单不符而转红（收紧别处不会红，因它只增不减）。`question` 的分裂（塔罗/梅花/周易
    无界 vs 雷诺曼/奇门/卢恩 120）是这一行真正的发现，记于报告。
    """
    assert _bounded_string_leaves() == _EXPECTED_BOUNDED


# --------------------------------------------------------------------------- #
# 行 5：Unicode 规范化 / 路径遍历（证否）
# --------------------------------------------------------------------------- #
def _open_calls_reaching_parameters(source: str) -> list[str]:
    """该模块里把"函数形参"当作 `open(...)` / `path.open(...)` 路径实参的调用（AST 级）。"""
    tree = ast.parse(source)
    offenders: list[str] = []

    def is_open(node: ast.AST) -> bool:
        if isinstance(node, ast.Call):
            f = node.func
            if isinstance(f, ast.Name) and f.id == "open":
                return True
            if isinstance(f, ast.Attribute) and f.attr == "open":
                return True
        return False

    for fn in [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]:
        params = {a.arg for a in (*fn.args.posonlyargs, *fn.args.args, *fn.args.kwonlyargs)}
        for call in (c for c in ast.walk(fn) if is_open(c)):
            used = {n.id for n in ast.walk(call) if isinstance(n, ast.Name)}
            if used & params:
                offenders.append(f"{fn.name}:open<-{sorted(used & params)}")
    return offenders


def test_user_input_never_reaches_file_paths() -> None:
    """钉「Unicode 规范化」行的路径遍历半边（证否成立）：语料/引擎里没有任何 open() 用形参当路径。

    addendum 实测：`app/content/kangxi_strokes.py` 全文只有两处 open，路径都是模块级常量
    （`_STROKES_PATH`/`_RADICALS_PATH`），无用户输入进路径。此测把它推广为一条静态不变式：
    `app/content/**` 与 `app/engines/**` 里凡打开文件，路径实参都不得是所在函数的形参——
    即用户可控的姓名/城市/文本永远参与不了文件路径构造，`..` 类字面也就无从被当路径。
    """
    offenders: list[str] = []
    for sub in ("content", "engines"):
        for path in sorted((APP / sub).rglob("*.py")):
            hits = _open_calls_reaching_parameters(path.read_text(encoding="utf-8"))
            offenders.extend(f"{path.relative_to(APP).as_posix()}:{h}" for h in hits)
    assert not offenders, "用户输入进了文件路径: " + ", ".join(offenders)


def test_unicode_and_traversal_literals_are_handled_cleanly(client: TestClient) -> None:
    """钉「Unicode 规范化」行的运行时半边：异形码位/零宽/`..` 字面既不越权读盘也不 500。

    NFC/NFKC 同形汉字（`伟`）正常排笔画；阿拉伯字形 ligature、罗马数字、CJK 兼容括符、
    连字 `ﬁ` 这类非单汉字一律被引擎挡成干净 422 `not_han`（长度归 pydantic、字符集归引擎，
    AGENTS §4）；`../..` 当城市名走的是"查不到城市"的域错误，绝不落到文件系统。
    """
    assert unicodedata.normalize("NFC", "伟") == "伟"
    ok = client.post("/api/v1/name/analyze", json={"surname": "伟", "given": "明"})
    assert ok.status_code == 200, ok.text[:120]

    # 非单汉字码位：希伯来连字 U+FB4F、罗马数字 U+2160、CJK 兼容括符 U+3220、拉丁连字 ﬁ U+FB01。
    # 写成转义而非裸字符：这些字形在编辑器里难以肉眼区分（AGENTS §8 / kangxi_strokes 头注同理）。
    for weird in ("ﭏ", "Ⅰ", "㈠", "ﬁ"):
        r = client.post("/api/v1/name/analyze", json={"surname": weird, "given": "明"})
        assert r.status_code == 422, (weird, r.text[:120])
        assert r.json()["error"]["code"] == "not_han"

    # 零宽空格混进名：被字符集校验挡成 not_han，而不是静默当作一个可见汉字计数。
    zw = client.post("/api/v1/name/analyze", json={"surname": "王", "given": "​明"})
    assert zw.status_code == 422 and zw.json()["error"]["code"] == "not_han"

    traversal = client.post(
        "/api/v1/ziwei/chart", json={**_BASE_NATAL, "city": "../../etc/passwd"}
    )
    assert traversal.status_code == 400  # InvalidBirthDataError，不是文件读取
    assert traversal.json()["error"]["code"] == "invalid_birth_data"


# --------------------------------------------------------------------------- #
# 行 6：错误体泄露
# --------------------------------------------------------------------------- #
def test_domain_error_envelope_leaks_no_internals() -> None:
    """钉「错误体泄露」行：域错误信封只 {code,message,context}，无 traceback/绝对路径。

    `register_error_handlers`（`app/core/errors.py:113`，addendum 订正简报的 :112 偏 1）把
    DestinyError 映射成统一信封。本测用真实域错误（认不出的城市）核信封键集与"不含栈/盘符"，
    与第 13 面（message 内插用户原文）不同族，不在这里立案。
    """
    client = TestClient(create_app())
    r = client.post("/api/v1/ziwei/chart", json={**_BASE_NATAL, "city": "不存在的城市"})
    assert r.status_code == 400
    body = r.text
    assert set(r.json()["error"]) <= {"code", "message", "context"}
    assert "Traceback" not in body
    assert not re.search(r"[A-Za-z]:\\", body)  # Windows 盘符绝对路径
    assert "/app/" not in body and ".py" not in body  # 容器/源码路径


def test_uncaught_exception_returns_bare_500(client: TestClient) -> None:
    """钉「错误体泄露」行的未捕获异常半边：崩了也不把栈吐给客户端。

    `errors.py` 全文件只有那**一个** `exception_handler`（addendum 行 6 实测），故未处理异常走
    Starlette 默认 500。上面 NaN 那条已在真实运行里触发过一次 500——其响应体是纯文本
    "Internal Server Error"，不含 Traceback。这里以同一 NaN raw body 复现并核泄漏。
    """
    quiet = TestClient(create_app(), raise_server_exceptions=False)
    body = (
        '{"birth_date":"1990-01-01","birth_time":"10:00","calendar":"solar",'
        '"gender":"male","city":null,"latitude":NaN,"longitude":0.0}'
    )
    r = quiet.post("/api/v1/bazi/natal", content=body.encode("utf-8"), headers=_JSON)
    assert r.status_code == 500
    assert "Traceback" not in r.text and 'File "' not in r.text


# --------------------------------------------------------------------------- #
# 行 7：随机源可预测性（只补分布级；`secrets` 半边归 test_architecture）
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    ("endpoint", "payload", "key"),
    [
        ("/api/v1/tarot/spread", {"spread_id": "celtic_cross"}, "drawn_ids"),
        ("/api/v1/lenormand/draw", {"spread_id": "grand_tableau"}, "drawn_ids"),
        ("/api/v1/runes/cast", {"spread_id": "five"}, "drawn_keys"),
    ],
)
def test_consecutive_draws_are_not_predictable(
    client: TestClient, endpoint: str, payload: dict[str, Any], key: str
) -> None:
    """钉「随机源可预测性」行的分布级半边：连续多次抽取不总是同一副。

    "抽签引擎只用 `secrets`"这条源码不变式已由 `test_architecture.py::test_draw_engines_use_csprng`
    独占，AGENTS 禁止两处重复断言同一件事，故此处只补统计事实：同一牌阵连抽 3 次不得三次全等
    （Mersenne 若被误用会退化，全等虽概率极低也非零；此处规模 grand_tableau=36、celtic_cross=10、
    five=5，三次全等概率趋零，故不断言具体牌、只断言"存在差异"，非 flaky）。
    """
    draws = {tuple(client.post(endpoint, json=payload).json()[key]) for _ in range(3)}
    assert len(draws) >= 2, f"{endpoint} 三次抽取完全相同，随机源可疑"


# --------------------------------------------------------------------------- #
# 行 8：CORS —— 钉现状（默认 origins + 通配 method/header + 凭证），是登记不是修复
# --------------------------------------------------------------------------- #
def test_cors_surface_matches_registered_defaults() -> None:
    """钉「CORS」行：默认白名单只有 localhost:5173，且 `allow_credentials=True` + 两串 `*`。

    `main.py:33-39` 实测：`allow_origins=settings.cors_origin_list`、`allow_credentials=True`、
    `allow_methods=["*"]`、`allow_headers=["*"]`；`config.py:19` 默认 `cors_origins` 只有
    `http://localhost:5173`（本机 dev 前端跑在 5174，跨源调用靠 nginx 同源代理，属配置项不是缺陷）。
    这一面是**已接受/待议**（纯计算无 cookie，`allow_credentials` 整条或可去掉；两串 `*` 宜收窄），
    本测钉的是"别在无人察觉时漂移"，不是宣称它安全。
    """
    app = create_app()
    cors = next(mw for mw in app.user_middleware if mw.cls is CORSMiddleware)
    opts = cors.kwargs
    assert opts["allow_origins"] == ["http://localhost:5173"]
    assert opts["allow_credentials"] is True
    assert opts["allow_methods"] == ["*"]
    assert opts["allow_headers"] == ["*"]


# --------------------------------------------------------------------------- #
# 行 10：nginx 安全头 —— 只钉已在的三条；缺的 CSP/Permissions/HSTS/body 上限记 ledger
# --------------------------------------------------------------------------- #
def test_nginx_emits_the_three_registered_security_headers() -> None:
    """钉「nginx 头」行的已在半边：`nginx.conf` 确实 add_header 那三条。

    addendum 实测恰三条（`:18-20`）：`nosniff` / `Referrer-Policy: strict-origin-when-cross-origin`
    / `X-Frame-Options: DENY`。缺 `Content-Security-Policy`、`Permissions-Policy`、
    `Strict-Transport-Security`、`client_max_body_size`（走 nginx 时吃默认 1 MB，直连 :8000 则无上限，
    与第 13 面同源）——那四条是 ledger，不在此断"缺失"（否则将来加一条反而红）。
    "实响应头"那半句需 `docker compose up` 部署环境，本轮测层不依赖容器，记为不测。
    """
    conf = NGINX_CONF.read_text(encoding="utf-8")
    assert 'add_header X-Content-Type-Options "nosniff" always' in conf
    assert 'add_header Referrer-Policy "strict-origin-when-cross-origin" always' in conf
    assert 'add_header X-Frame-Options "DENY" always' in conf
