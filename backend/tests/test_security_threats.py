"""轴 3（安全与威胁面）的机器侧：简报威胁表逐行落地。

判据来自 `.superpowers/sdd/2026-09-26-fullstack-test/task-12-controller-addendum.md`
第三节（权威现状）与同目录 `task-12-fix1-brief.md`（评审 6 条的落地口径），每条测的 docstring
引它所钉的**行名**。跑法（2026-09-27 全绿）：
`cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m pytest tests/test_security_threats.py -p no:warnings`

不在此文件立案的三行（诚实处置，见报告）：
- 「部署面暴露」（`/docs` `/openapi.json` 全开）属用户决策 → ledger，不测。
- 「隐私声称与实现不符」（`SiteFooter.tsx` 与 `main.py` docstring 声称本地 E2EE）→ Task 13。
- 「无鉴权响应放大」（错误体逐字回显用户输入，F-A3-1）→ 只进 findings，测层零条：
  把「422 的 input 里含完整请求体」钉成断言会在修法落地（裁掉 input）时转红，故不许钉。
随机源的「抽签引擎只用 `secrets`」半边由 `test_architecture.py::test_draw_engines_use_csprng`
独占（AGENTS 两端不得重复断言同一件事），本文件只补分布级「连续抽取不重合」。
两处形状裁定（修复轮 1）：行 3 的 NaN/Infinity 与行 6 的未捕获异常是**同一个真实 500**，
合并为一处取证，每种 raw body 只发一次；行 5 的路径遍历静态半边从"数据流启发式"换成
"读盘站点登记"，范围是 `app/**/*.py` 全量。
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
# 行 1：无鉴权 + 无限流的计算型 DoS —— 已登记的边界；未封顶的计数只记述
# --------------------------------------------------------------------------- #
def _ge_le(field: Any) -> tuple[float | None, float | None]:
    md = field.metadata
    ge = next((m.ge for m in md if isinstance(m, Ge)), None)
    le = next((m.le for m in md if isinstance(m, Le)), None)
    return ge, le


def test_compute_dos_iteration_bounds_registry() -> None:
    """钉「无鉴权 + 无限流的计算型 DoS」行里**确实存在**的六条边界，并把没封顶的写清楚。

    这一测钉的三件事（旧 docstring 声称"每一个迭代计数都是编译期硬边界"，那句证不到自己的
    结论，已作废——反例：引擎改成产 366 个日格，本测照样全绿）：

    ① `BaziHehunRequest.axis_years` 的 `(1, 30)`：全仓**唯一**一个"用户可控、且由 pydantic
       封顶"的迭代计数（`app/schemas/bazi_hehun.py:60`，`:51` 注写明它是唯一走 pydantic 的轴
       字段；复测：反射全部 `*Request` 模型的 list 型字段，只有 `MeihuaCastRequest.numbers` 与
       `ZhouyiCastRequest.manual_coins` 两个，`metadata` 都是 `[]`，见 ③）。
    ② 响应模型的五条 `ge/le`（`month_index`/`weekday`/`index`）钉的是**格子里那个数的取值域**，
       不是**格子有几格**：`month_index ∈ 0..11` 说月份号，对 `days` 的长度没有任何约束力。
       测留着的理由是它们确实是存在的边界，只是不承担"封顶迭代次数"这个论证。
    ③ 未被封顶的迭代计数——**只记述、不立断言**（立了就是把现状当契约、违「不立永久红灯」）：
       - `BaziLiuriResult.days`、`BaziLiushiResult.hours` 的 `metadata == []`，即两个响应列表
         零长度界。实际上界由结构给而不由 schema 给：日格来自节气月段的逐日枚举
         （`app/engines/bazi_liuri.py:177-188` 的 `_enumerate_days`），实测 2016–2036 共 252 段
         落在 **29..32 天**（29×34、30×97、31×98、32×23），最大 32 天，例如 2024-07-06→2024-08-06；
         时格恒 12。addendum 写的"流日 ≤ 31 格"因此被实测推翻（它只扫了 2024/2025 的部分月）。
         复测：`jieqi_boundaries(y)` 取 `(end-start).days+1` 逐年统计；
         或 `POST /api/v1/bazi/liuri/matrix` 以 `reference_date=2024-07-15` → `len(days)==32`、
         `POST /api/v1/bazi/liushi/day` → `len(hours)==12`。
       - `ZhouyiCastRequest.manual_coins: list[list[int]] | None` 的 `metadata == []`：校验住在
         引擎 `app/engines/zhouyi.py:60-71`，发生在**分配之后**——实测 100 000 掷的 payload 会
         被完整构造出来，再由引擎拒成 400 `invalid_cast_input`
         （"manual_coins must contain exactly 6 throws, got 100000." / 107 bytes）。
       - 本轮新发现的第四条（简报未列）：`MeihuaCastRequest.numbers: list[int]` 同样
         `metadata == []`，1..3 个的上界住在引擎 `app/engines/meihua.py:91-92`，也是分配之后。
       这四条是「已接受面」，进 findings/ledger。
    """
    assert _ge_le(BaziHehunRequest.model_fields["axis_years"]) == (1, 30)
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


def _nonfinite_body(literal: str) -> bytes:
    return (
        '{"birth_date":"1990-01-01","birth_time":"10:00","calendar":"solar",'
        f'"gender":"male","city":null,"latitude":{literal},"longitude":0.0}}'
    ).encode("utf-8")


def test_nonfinite_coordinates_never_yield_a_chart_and_never_leak_a_stack() -> None:
    """钉「非法经纬度」的 NaN/Infinity 半边 **+**「错误体泄露」的未捕获异常半边（一处取证）。

    非严格 JSON 的 `NaN`/`Infinity`/`-Infinity` 被 python-json 解码器接受，而 TestClient 的
    `json=` 通道因 `allow_nan=False` 拒发，只能走 raw body。服务端收下后 `ge/le` 判 NaN 失败
    进入 422 序列化，Starlette 的 JSON 响应同样 `allow_nan=False`，回抛
    `ValueError: Out of range float values are not JSON compliant`。实测（2026-09-27，
    本函数即复测命令）：三条字面量都是 **500 / 21 bytes** 纯文本 "Internal Server Error"。
    `errors.py` 全文只有 `register_error_handlers` 那**一个** handler（无 catch-all
    `exception_handler`），未处理异常一律走 Starlette 默认 500 —— 这就是同一个请求能同时
    代表「未捕获异常」这一族泄露面的理由，两种旧写法（各发一次同一个 raw body）已合并。

    钉 `>= 400` 而不是 `== 500` 是**刻意的**：500 是当前的错误序列化缺陷（已立案的健壮性面），
    不是期望值。把它钉成 `== 500` 等于给"修成干净 422"设罚，正是本文件 nginx 那条
    "只钉已在的三条、绝不钉缺失"的同一个理由。修法无论往哪边走都必须成立的两件事，就钉这两件：
    ① 永不产盘、永不 2xx；② 崩了也不把栈吐给客户端（响应体不含 `Traceback`、不含 `File "`）。
    """
    quiet = TestClient(create_app(), raise_server_exceptions=False)
    for literal in ("NaN", "Infinity", "-Infinity"):
        r = quiet.post("/api/v1/bazi/natal", content=_nonfinite_body(literal), headers=_JSON)
        assert r.status_code >= 400, (literal, r.status_code, r.text[:120])
        assert "four_pillars" not in r.text, (literal, r.text[:120])
        assert "Traceback" not in r.text and 'File "' not in r.text, (literal, r.text[:120])


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


def _discover_request_models() -> dict[str, type[BaseModel]]:
    """按 `*Request` 后缀收集 schemas 包里的请求模型（含嵌套子模型由 walker 负责）。

    "以 `*Request` 结尾"是命名耦合（新增系统若换个后缀就静默不入反射），属 ledger 记账项，
    本轮不动它的选取口径；件数断言（含 report.py 的 ReportTimeRequest / ReportRelationshipRequest）写在用它的那个测的函数体里，不写在 helper 里。
    """
    requests: dict[str, type[BaseModel]] = {}
    for m in pkgutil.iter_modules(_schemas_pkg.__path__):
        mod = importlib.import_module(f"app.schemas.{m.name}")
        for name in dir(mod):
            obj = getattr(mod, name)
            if isinstance(obj, type) and issubclass(obj, BaseModel) and name.endswith("Request"):
                requests.setdefault(name, obj)
    return requests


def _bounded_leaves(requests: dict[str, type[BaseModel]]) -> tuple[dict[str, int], dict[str, int]]:
    """反射两个**语义不同**的上限集合：`str` 叶的值长上限，与 `dict` 字段的**条目数**上限。

    返回 `(string_caps, dict_entry_caps)`。后者用 `{}.` 式后缀（`<字段路径>{}`）标记，因为
    pydantic 的 `max_length` 挂在 `dict[str, str]` 上管的是"这个 dict 有几条"，**不是** value
    的长度——实测（2026-09-27，复测：`class M(BaseModel): d: dict[str, str] = Field(max_length=5)`）
    `M(d={'a': 'x'*5000})` 通过、`M(d=<6 条>)` 被拒。旧写法把条目数界登记进字符串上限表，
    是方向性误判：哪天有人给 `NameAnalyzeRequest.variants` 加 `max_length=5`，表里会记成
    "该 str 叶已限定"而长绿，而 100 KB 的 value 回显（F-A3-1 的第三条通道）照样存在。
    """
    string_caps: dict[str, int] = {}
    dict_entry_caps: dict[str, int] = {}

    def walk(model: type[BaseModel], prefix: str) -> None:
        for fname, f in model.model_fields.items():
            path = f"{prefix}.{fname}"
            ann = _strip_optional(f.annotation)
            ml = next((x.max_length for x in f.metadata if isinstance(x, MaxLen)), None)
            if ann is str:
                if ml is not None:
                    string_caps[path] = ml
            elif get_origin(ann) is dict and len(get_args(ann)) == 2 and get_args(ann)[1] is str:
                if ml is not None:
                    dict_entry_caps[f"{path}{{}}"] = ml
            elif isinstance(ann, type) and issubclass(ann, BaseModel):
                walk(ann, path)

    for name in sorted(requests):
        walk(requests[name], name)
    return string_caps, dict_entry_caps


# addendum 第三节行 4 的有界清单（40 个 `str` 叶 + 1 个 `dict[str,str]` 的 value 位 = 41 个
# 自由文本叶里的 17 个有界者）。复测：本文件的 `_bounded_leaves()`（走完嵌套，含
# `BaziHehunRequest.male/female` 与 `SynastryRequest.person_a/person_b` 两个子模型）。
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

# 字典字段的**条目数**上限登记表。今天为空：实测全仓 19 个 `*Request` 里只有一个 dict 字段
# （`NameAnalyzeRequest.variants: dict[str, str] | None`），它的 `metadata == []`。
# 将来若有人给它加 `max_length`，它会出现在 `_bounded_leaves()` 的第二个返回值里，
# 名字带 `{}` 后缀——那是一道"条目数界"，不是"值长界"，两者不能被当成同一件事。
_EXPECTED_DICT_ENTRY_CAPS: dict[str, int] = {}


def test_string_input_caps_present_in_registry_survive() -> None:
    """钉「超长/异形字符串」行的可钉半边：登记的 17 个上限，其**存在与取值**一个都不能丢/不能放。

    逐路径核对（评审 4 条把这里的形状改了）：对 `_EXPECTED_BOUNDED` 的每个键断言反射值**相等**
    ——被删掉 → `missing` 非空红；被放宽 → 取值不等红。反射表里**多出来**的键**不红**，那是
    新增上限（收紧），是改进。旧写法 `_bounded_leaves() == _EXPECTED_BOUNDED` 恰好相反：
    实测给 `ZiweiRequest.city` 追加一个 `MaxLen(40)` 会反射出 18 键、整表不等 → 直接红，
    于是"只减不加"那句是假的、登记表惩罚改进。现在的语义与 nginx 那条一致：
    退化必报警，改进不误伤。

    无上限的 24 个自由文本叶（`city` ×12、`house_system` ×3、`spread_id` ×3、`question` ×3、
    `focus_hour_zhi` 1、`significator` 1、`variants` 的 value 位 1）是「已接受面」，整张进
    ledger/报告，不在此断言——简报"逐个请求模型断言**每个** str 入参都有上限"今天为假，
    照写即永久红灯。`question` 的分裂（塔罗/梅花/周易无界 vs 雷诺曼/奇门/卢恩 120）是这一行
    真正的发现。`variants` 那条走的是 `_EXPECTED_DICT_ENTRY_CAPS`（条目数，不是值长），
    两个集合的语义差别见 `_bounded_leaves()` 的 docstring。
    """
    requests = _discover_request_models()
    assert len(requests) == 21, sorted(requests)
    string_caps, dict_entry_caps = _bounded_leaves(requests)

    missing = sorted(set(_EXPECTED_BOUNDED) - set(string_caps))
    assert not missing, f"登记在案的字符串上限消失了: {missing}"
    for path, cap in _EXPECTED_BOUNDED.items():
        assert string_caps[path] == cap, f"{path} 的 max_length 被放宽: {string_caps[path]} ≠ {cap}"

    missing_caps = sorted(set(_EXPECTED_DICT_ENTRY_CAPS) - set(dict_entry_caps))
    assert not missing_caps, f"登记在案的条目数上限消失了: {missing_caps}"
    for path, cap in _EXPECTED_DICT_ENTRY_CAPS.items():
        assert dict_entry_caps[path] == cap, (
            f"{path} 的条目数上限被放宽: 现状 {dict_entry_caps[path]} ≠ 登记 {cap}"
        )


# --------------------------------------------------------------------------- #
# 行 5：Unicode 规范化 / 路径遍历（证否）
# --------------------------------------------------------------------------- #
_READ_METHODS = frozenset({"open", "read_text", "read_bytes"})
_PATH_CONSTRUCTORS = frozenset({"Path", "PurePath", "PosixPath", "WindowsPath"})

#: 全后端读盘站点的登记表：`(相对 backend/ 的文件, 路径实参归约到的终点名)`。
#: 实测 2026-09-27 恰 3 处（`grep -rn "\.open(\|open(\|read_text(\|read_bytes(" app` 同结论）。
#: 新增第 4 处必须来这里登记并接受复审——这就是"新增加一个读盘点 → 红"的机制。
_REGISTERED_FILE_READ_SITES: frozenset[tuple[str, str]] = frozenset(
    {
        ("app/content/kangxi_strokes.py", "_STROKES_PATH"),
        ("app/content/kangxi_strokes.py", "_RADICALS_PATH"),
        ("app/solar/geo.py", "_CITIES_PATH"),
    }
)


def _top_level_constants(tree: ast.Module) -> set[str]:
    """模块级（顶层）赋值的名字里那些全大写者：本仓约定的常量（`_UPPER_SNAKE` 也算）。"""
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Assign):
            targets = node.targets
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target]
        else:
            continue
        for target in targets:
            if isinstance(target, ast.Name) and target.id.isupper():
                names.add(target.id)
    return names


def _assignments(tree: ast.Module) -> dict[str, list[ast.expr]]:
    """每个简单名字在这个模块里的全部赋值右值（多于一条即视为运行时可变，不敢当路径来源）。"""
    values: dict[str, list[ast.expr]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            pairs = [(t, node.value) for t in node.targets]
        elif isinstance(node, ast.AnnAssign):
            pairs = [(node.target, node.value)]
        else:
            continue
        for target, value in pairs:
            if isinstance(target, ast.Name) and value is not None:
                values.setdefault(target.id, []).append(value)
    return values


def _runtime_bound_names(tree: ast.Module) -> set[str]:
    """任何在运行时才被绑定的名字：函数形参、`for`/推导/`with as`/`except as`/海象的目标。

    保守起见一律禁作路径来源——旧启发式只看"所在函数的形参"，于是模块级 `open()`、嵌套函数
    形参、一跳赋值全都从指缝里漏掉。
    """
    names: set[str] = set()
    for node in ast.walk(tree):
        target: ast.expr | str | None = None
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            a = node.args
            optionals = [arg for arg in (a.vararg, a.kwarg) if arg is not None]
            for arg in (*a.posonlyargs, *a.args, *a.kwonlyargs, *optionals):
                names.add(arg.arg)
            continue
        if isinstance(node, (ast.For, ast.AsyncFor, ast.comprehension, ast.NamedExpr)):
            target = node.target
        elif isinstance(node, ast.withitem):
            target = node.optional_vars
        elif isinstance(node, ast.ExceptHandler):
            target = node.name
        if target is None:
            continue
        if isinstance(target, str):  # `except X as name` 的 name 是裸字符串
            names.add(target)
            continue
        for sub in ast.walk(target):
            if isinstance(sub, ast.Name):
                names.add(sub.id)
    return names


def _resolve_path_source(
    expr: ast.expr,
    constants: set[str],
    values: dict[str, list[ast.expr]],
    bound: set[str],
    depth: int = 0,
) -> tuple[str, str]:
    """把"路径实参"归约成可登记的终点：`("const"|"literal"|"combined", 终点)` 或 `("dynamic", …)`。

    `("const", name)`：终点是模块级常量名；`("literal", "'x.json'")`：字符串字面量；
    `("combined", "a|b")`：拼装（`BinOp`/f-string），要求**每一段**都归约到常量或字面量；
    `("dynamic", …)`：归约到运行时绑定的名字、来源不明、或重赋值多次——一律判红。
    一跳赋值（`p = _CITIES_PATH; open(p)`）绕不过这里：跟着赋值链走到底，终点仍是那个常量。
    """
    if depth > 4:
        return "dynamic", f"归约深度>4: {ast.unparse(expr)}"
    if isinstance(expr, ast.Constant) and isinstance(expr.value, str):
        return "literal", repr(expr.value)
    if isinstance(expr, ast.Name):
        if expr.id in bound:
            return "dynamic", f"运行时绑定名 {expr.id}"
        if expr.id in constants:
            return "const", expr.id
        assigned = values.get(expr.id, [])
        if len(assigned) == 1:
            return _resolve_path_source(assigned[0], constants, values, bound, depth + 1)
        if not assigned:
            return "dynamic", f"未在本模块赋值的名 {expr.id}"
        return "dynamic", f"{expr.id} 有 {len(assigned)} 处赋值"
    if isinstance(expr, ast.BinOp):
        parts = [
            _resolve_path_source(part, constants, values, bound, depth + 1)
            for part in (expr.left, expr.right)
        ]
        if any(kind == "dynamic" for kind, _ in parts):
            return "dynamic", ast.unparse(expr)
        return "combined", "|".join(token for _, token in parts)
    if isinstance(expr, ast.JoinedStr):
        parts = [
            _resolve_path_source(value, constants, values, bound, depth + 1)
            for value in expr.values
            if isinstance(value, (ast.Constant, ast.FormattedValue))
        ]
        formatted = [v for v in expr.values if isinstance(v, ast.FormattedValue)]
        for v in formatted:
            parts.append(_resolve_path_source(v.value, constants, values, bound, depth + 1))
        if any(kind == "dynamic" for kind, _ in parts):
            return "dynamic", ast.unparse(expr)
        return "combined", "|".join(token for _, token in parts)
    if isinstance(expr, ast.Call):
        if isinstance(expr.func, ast.Name) and expr.func.id in _PATH_CONSTRUCTORS and expr.args:
            return _resolve_path_source(expr.args[0], constants, values, bound, depth + 1)
        return "dynamic", ast.unparse(expr)
    return "dynamic", ast.unparse(expr)


def _read_sites_in_module(source: str, rel: str) -> tuple[set[tuple[str, str]], list[str]]:
    """一个模块里的读盘调用点：`open(...)` / `X.open()` / `X.read_text()` / `X.read_bytes()`。

    覆盖**所有作用域**（含模块级与嵌套函数），返回 `(站点集合, 路径来源可疑清单)`。
    """
    tree = ast.parse(source)
    constants = _top_level_constants(tree)
    values = _assignments(tree)
    bound = _runtime_bound_names(tree)
    sites: set[tuple[str, str]] = set()
    suspicious: list[str] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        path_arg: ast.expr | None
        if isinstance(func, ast.Name) and func.id == "open":
            path_arg = node.args[0] if node.args else next(
                (kw.value for kw in node.keywords if kw.arg == "file"), None
            )
        elif isinstance(func, ast.Attribute) and func.attr in _READ_METHODS:
            path_arg = func.value
        else:
            continue
        if path_arg is None:
            continue
        kind, token = _resolve_path_source(path_arg, constants, values, bound)
        if kind == "dynamic":
            suspicious.append(f"{rel}:{node.lineno}: {token} ({ast.unparse(node)[:80]})")
        else:
            sites.add((rel, token))
    return sites, suspicious


def test_file_read_sites_are_the_registered_module_constants() -> None:
    """钉「路径遍历」这半边的静态形状：全后端读盘站点清单 + 每处路径实参只取模块级常量。

    范围（评审 5 条换掉的形状）：`app/**/*.py` **全量**。旧写法只看 `app/content/**` 与
    `app/engines/**`，实测只覆盖到 2 个调用点（`engines/` 一个都没有），还漏了
    `app/solar/geo.py:25` —— 正是"Unknown city"这条域错误走的那段代码；`app/api/**`、
    `app/core/**` 也 entirely 不在旧范围里。启发式（"open 的实参里出现所在函数的形参名"）
    换成登记制，因为数据流分析在这里既不可信也难维护。断言两件事：

    ① 站点集合**恰等于** `_REGISTERED_FILE_READ_SITES` 那 3 处：少一处说明那行被改形状
      （改名/搬走，同样要人来对账），多一处即新增加一个读盘点 → 红，逼人来复审。
    ② 每处路径实参归约到的终点必须是**模块级常量名**（本仓写法 `_STROKES_PATH` 这类
      `_UPPER_SNAKE`）或字符串字面量；拼装表达式要求每一段都归约到常量/字面量。任何归约到
      运行时绑定的名字（形参、`for`/推导/`with as`/`except as`/海象目标）、未赋值的名、
      或模块内被赋值两次以上的名，都进 `suspicious` 并判红。一跳赋值（`p = user; open(p)`）
      绕不过 ②，因为跟着赋值链走到底，终点仍是那个可疑名。非 `Path(...)` 族的构造函数调用
      （例如 `os.path.join(_DIR, "cities.json")`）即使各段都是常量也照样判可疑并红——那是刻意
      保守：新的拼装方式必须人来复审并登记，不由静态检查替它背书。

    实测（2026-09-27）：站点恰 3 处，全部是 `X.open(encoding=...)` 形状，路径实参分别是
    `_STROKES_PATH`、`_RADICALS_PATH`（`app/content/kangxi_strokes.py:79/:81`）与
    `_CITIES_PATH`（`app/solar/geo.py:25`），三个名字都是模块级常量。
    复测：`grep -rn "\\.open(\\|open(\\|read_text(\\|read_bytes(" backend/app --include=*.py`。

    诚实的限制：这是**静态形状检查**，不证明运行时值不可控——模块级常量的值如果被别处改写，
    本测看不见；读的清单只覆盖 `open`/`.open()`/`.read_text()`/`.read_bytes()` 四种形状，
    `glob`/`os.scandir`/`shutil` 等非本族入口不在内。用户输入是否可能被当路径用，运行时那半
    边由 `test_unicode_and_traversal_literals_are_handled_cleanly` 的 `../..` 探针钉。
    """
    sites: set[tuple[str, str]] = set()
    suspicious: list[str] = []
    for path in sorted(APP.rglob("*.py")):
        found, hops = _read_sites_in_module(
            path.read_text(encoding="utf-8"), path.relative_to(BACKEND).as_posix()
        )
        sites |= found
        suspicious.extend(hops)

    assert not suspicious, "读盘路径实参归约到可疑来源: " + "; ".join(suspicious)
    assert sites == _REGISTERED_FILE_READ_SITES, (
        "读盘站点与登记表不一致——新增读盘点必须来复审并登记: "
        f"新出现 {sorted(sites - _REGISTERED_FILE_READ_SITES)}，"
        f"消失 {sorted(_REGISTERED_FILE_READ_SITES - sites)}"
    )


def test_unicode_and_traversal_literals_are_handled_cleanly(client: TestClient) -> None:
    """钉「Unicode 规范化」行的运行时半边：异形码位/零宽/`..` 字面既不越权读盘也不 500。

    非单汉字一律被引擎挡成干净 422 `not_han`（长度归 pydantic、字符集归引擎，AGENTS §4）；
    `../..` 当城市名走的是"查不到城市"的域错误（`invalid_birth_data`），绝不落到文件系统。
    规范化的**机理**那半边不住在这里：本文件下一条测
    `test_odd_han_forms_are_resolved_or_flagged_never_silent` 才测 NFKC（这条过去的 docstring
    声称测了 NFKC，实际只断了一条永真式 `normalize("NFC", "伟") == "伟"`——"伟"无分解，
    那个断言不存在失败的可能，已删）。
    """
    ok = client.post("/api/v1/name/analyze", json={"surname": "伟", "given": "明"})
    assert ok.status_code == 200, ok.text[:120]

    # 异形码位一律写转义，不写裸字形：这些字符在编辑器里肉眼难以区分，U+200B 更是完全
    # 不可见（AGENTS §8 / `kangxi_strokes.py:28-29` 的同款理由）。
    # U+FB4F 希伯来连字、U+2160 罗马数字、U+3220 CJK 兼容括符、U+FB01 拉丁连字 ﬁ、U+200B 零宽空格。
    for weird in ("\uFB4F", "\u2160", "\u3220", "\uFB01"):
        r = client.post("/api/v1/name/analyze", json={"surname": weird, "given": "明"})
        assert r.status_code == 422, (hex(ord(weird)), r.text[:120])
        assert r.json()["error"]["code"] == "not_han"

    # 零宽空格混进名（姓氏位与名首位都试）：被字符集校验挡成 not_han，而不是静默当作一个
    # 可见汉字计数。
    zw_surname = client.post("/api/v1/name/analyze", json={"surname": "\u200B", "given": "明"})
    assert zw_surname.status_code == 422 and zw_surname.json()["error"]["code"] == "not_han"
    zw_given = client.post("/api/v1/name/analyze", json={"surname": "王", "given": "\u200B明"})
    assert zw_given.status_code == 422 and zw_given.json()["error"]["code"] == "not_han"

    traversal = client.post(
        "/api/v1/ziwei/chart", json={**_BASE_NATAL, "city": "../../etc/passwd"}
    )
    assert traversal.status_code == 400  # InvalidBirthDataError，不是文件读取
    assert traversal.json()["error"]["code"] == "invalid_birth_data"


#: `(探针标签, 异形码位, NFKC 规范形码位)`：成对的都是**同形字**，归一化能把左列换成右列。
_NFKC_PROBES: tuple[tuple[str, str, str], ...] = (
    ("CJK 兼容表意 U+F909（契）", "\uF909", "\u5951"),
    ("CJK 兼容表意 U+F929（朗）", "\uF929", "\u6717"),
    ("CJK 兼容表意 U+F973（拾）", "\uF973", "\u62FE"),
    ("康熙部首 U+2F45（方）", "\u2F45", "\u65B9"),
)


def test_odd_han_forms_are_resolved_or_flagged_never_silent(client: TestClient) -> None:
    """钉「Unicode 规范化」行真正的那条形：解析不出的字形必须**出声**，静默降级判红。

    stdlib 前提（探针表右列，逐条断言；Unicode 15.1.0）：`normalize("NFKC", "\\u2F45") == "\\u65B9"`
    ——部首形与正字是同形字，归一化本可以把部首还原成正字。**引擎没有做这一步**：`_HAN`
    把 U+2E80..U+2FDF 整段当汉字放行（`app/engines/name_numerology.py:45-48`），笔画却按码位
    查 `backend/data/kangxi_strokes.json`。于是同一族异形码位今天分两种命运（实测 2026-09-27）：
      - U+F909/U+F929/U+F973：Unihan 为每个兼容码位单独给了 kRSUnicode 行，所以**它们自己就在
        语料里**，200 且康熙笔画与各自规范形逐字相同（9/11/10 画），五格与总分也一致
        （17.5 下 / 57.5 中 / 73.5 中上）。它们过是因为语料恰好收录，不是因为引擎归了一。
      - U+2F45：语料**没有**这个码位（正字 U+65B9 有，4 画），200 但 `kangxi_strokes=null`、
        人/地/外/总四格 value 全 None、`score=null`，靠 `warnings: ["stroke_unresolved:⽅"]` 出声；
        规范形 方 → 200、4 画、无警告、score 20.0。
    所以**不许**钉"异形码位与规范形结果相同"——那句对部首形是假的，钉了就是永久红灯。
    钉的是这条不静默不变式：`POST /name/analyze` 带异形码位时只能是
      ① 200 且"未解析出笔画的字的集合" == "带 `stroke_unresolved:<该字>` 警告的字的集合"
        （缺了就是"看着正常、五格其实少一块"），并且未解析时 `score` 必须为 None、
        算式里带 `?` 的那几格 `value` 必须为 None；或
      ② 422 且 `error.code == "not_han"` 干净拒收。
    两者之外的任何形状（500、未解析又不出声、出了声却仍给出分数）都红。①写成条件式而不是
    死钉"必须出声"，是给"将来补上 NFKC 归一"留门：那才是正解，把它判红就是反安全激励
    （与本文件 NaN 那条钉 `>= 400` 而非 `== 500` 同一个理由）。
    另记两条不立断言的事实：带圈二 U+3221 不在 `_HAN` 覆盖段 → 422 `not_han`，但它的 NFKC 形
    `(二)` 含 ASCII 括号，会是另一种形状（pydantic `string_too_long` 的 `detail`，无 `error` 键），
    故不作本测探针；兼容表意三兄弟的 `readings` 是**空数组**（Unihan 没给它们拼音），今天无人出声，
    这条是本测看不见的静默降级，只进 findings。
    """
    for label, odd, canonical in _NFKC_PROBES:
        assert unicodedata.normalize("NFKC", odd) == canonical, label

        r = client.post("/api/v1/name/analyze", json={"surname": "王", "given": odd + "明"})
        assert r.status_code in (200, 422), (label, r.status_code, r.text[:160])
        if r.status_code == 422:
            assert r.json()["error"]["code"] == "not_han", (label, r.text[:160])
            continue

        payload = r.json()
        unresolved = sorted(c["char"] for c in payload["chars"] if c["kangxi_strokes"] is None)
        flagged = sorted(
            w.split(":", 1)[1]
            for w in payload["warnings"]
            if w.startswith("stroke_unresolved:")
        )
        assert unresolved == flagged, (label, "未解析的字与出声的字不是一批", unresolved, flagged)
        if unresolved:
            assert payload["score"] is None, (label, "缺笔画却给出了分数", payload["score"])
            assert all(
                g["value"] is None for g in payload["grids"] if "?" in g["formula"]
            ), (label, payload["grids"])


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
    契约一坏（非 200）必须显式判红：先 `assert status_code == 200` 再取 `.json()[key]`，
    否则退化成一个信息量为零的 KeyError。
    """
    draws: set[tuple[Any, ...]] = set()
    for _ in range(3):
        r = client.post(endpoint, json=payload)
        assert r.status_code == 200, (endpoint, r.text[:120])
        draws.add(tuple(r.json()[key]))
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

    范围声明：本测核的是 conf **文本**，不核 nginx 的 `add_header` **继承规则**——`location
    /assets/` 与 `= /index.html` 各自带 `add_header`，按 nginx 语义 server 级那三条对这两类
    响应不生效，所以"本测绿"不等于"每一条响应都带这三个头"。该事实由控制器写进 findings。
    """
    conf = NGINX_CONF.read_text(encoding="utf-8")
    assert 'add_header X-Content-Type-Options "nosniff" always' in conf
    assert 'add_header Referrer-Policy "strict-origin-when-cross-origin" always' in conf
    assert 'add_header X-Frame-Options "DENY" always' in conf
