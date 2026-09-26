"""轴 2 的机器侧：分层 import 方向、每系统后端四件、抽签引擎随机源、golden 覆盖齐备。

判据文字见仓库根 `AGENTS.md`（第 1/2/5 条）；本模块只用 stdlib（ast + pathlib）读
`app/**.py` 的源码文本，不 import 被测代码，故任何引擎崩了都影响不到这里。

棘轮而非硬门：现状里已裁定的例外写进 BASELINE / 例外集合（附裁定理由与 ledger 行号），
断言只保证「不再变差」；已实测为零的反向依赖对就是硬门（BASELINE 缺省 0）。
复测口径（2026-09-26 全绿）：
`cd backend && .venv/Scripts/python.exe -m pytest tests/test_architecture.py -p no:warnings`
"""

import ast
from pathlib import Path

import pytest

APP = Path(__file__).resolve().parents[1] / "app"
TESTS = Path(__file__).resolve().parent

#: 分层的内→外序号（数字越大越靠外）。被禁的跨界方向逐条列在 FORBIDDEN，
#: 序号本身不参与断言，它解释的是那张清单为什么长这样：content 是底座，
#: api 是外壳，中间层不得回头依赖更外层的推导/HTTP 装配。
LAYER = {"content": 0, "core": 1, "schemas": 1, "solar": 1, "engines": 2, "api": 3}

#: (引用方, 被引方) 的禁止对：左侧层不得 `import app.<右侧>`
FORBIDDEN: list[tuple[str, str]] = [
    ("content", "engines"),
    ("content", "api"),
    ("content", "schemas"),
    ("schemas", "engines"),
    ("schemas", "api"),
    ("engines", "api"),
]

#: 现测（2026-09-26）仍存在的违规数；未登记的 kind 基线为 0（硬门）。
#: 唯一非零项 `content->schemas`：`app/content/__init__.py`、
#: `app/content/bazi_hehun_rules.py`、`app/content/synastry.py` 三处从
#: `app.schemas.scoring` 只引出处措辞常量 MODEL_PARAM_SOURCE，属常量住所不佳
#: 而非契约依赖 —— 裁定见 AGENTS.md 第 1 条例外段与 ledger F-A2-1。
BASELINE: dict[str, int] = {"content->schemas": 3}


def assert_no_new_violations(kind: str, count: int, offenders: list[str]) -> None:
    """棘轮断言：`count <= BASELINE.get(kind, 0)`，并把新 offenders 报出来。

    修掉一处违规后把基线调低一格是义务；调高需要先在 findings ledger 立一条
    新发现并给出裁定，不得为了让测试变绿而上调。
    """
    limit = BASELINE.get(kind, 0)
    assert count <= limit, (
        f"{kind} 违规 {count} 处，超出基线 {limit}；新增: {offenders[limit:] or offenders}"
    )


def _imports_of(path: Path) -> set[str]:
    """该文件 import 到的 `app.<layer>` 层名集合（全仓无相对 import，只看绝对路径）。"""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("app."):
            found.add(node.module.split(".")[1])
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("app."):
                    found.add(alias.name.split(".")[1])
    return found


@pytest.mark.parametrize(("src", "dst"), FORBIDDEN)
def test_layer_direction(src: str, dst: str) -> None:
    """AGENTS.md 第 1 条：六条反向 import 方向不得越过各自的基线。"""
    offenders = [
        p.relative_to(APP.parent).as_posix()
        for p in sorted((APP / src).rglob("*.py"))
        if dst in _imports_of(p)
    ]
    assert_no_new_violations(f"{src}->{dst}", len(offenders), offenders)


#: 抽牌/起卦类引擎（AGENTS.md 第 5 条 / PRD §4.1）：抽签随机只能来自 CSPRNG。
#: `random` 是 Mersenne Twister，可被观测若干次输出后预测下一次的牌。
DRAW_ENGINES = ("tarot", "lenormand", "runes", "zhouyi")


@pytest.mark.parametrize("engine", DRAW_ENGINES)
def test_draw_engines_use_csprng(engine: str) -> None:
    source = (APP / "engines" / f"{engine}.py").read_text(encoding="utf-8")
    assert "import secrets" in source, f"{engine}.py 必须用 secrets（PRD §4.1 抽签公平性）"
    assert "import random" not in source, f"{engine}.py 不得退回可预测的 random 模块"


#: `meta` 是平台级路由（health、城市检索），不是测算系统，不入七件套清单。
NON_SYSTEM_ROUTERS = {"__init__", "router", "meta"}

#: 语料文件用单数词干的已登记别名（`content/rune_futhark.py`、`content/rune_spreads.py`）。
CONTENT_STEM_ALIAS: dict[str, str] = {"runes": "rune"}

#: 无 `content/` 语料的已裁定例外（ledger F-A2-2）：占星族的"表"是与 pyswisseph
#: 计算绑定的常量（星座/行星/相位定义），住在引擎里而非语料层；transit 的表刻意
#: 复用 `app.engines.western` 而不双份维护（`app/engines/transit.py:16` 头注）。
CONTENT_LESS_SYSTEMS = {"western", "transit"}


def _system_names() -> list[str]:
    """系统清单以已挂载的路由为准：新系统一旦出端点文件，缺件即红。"""
    return sorted(
        p.stem for p in (APP / "api" / "v1").glob("*.py") if p.stem not in NON_SYSTEM_ROUTERS
    )


@pytest.mark.parametrize("system", _system_names())
def test_every_system_has_backend_pieces(system: str) -> None:
    """AGENTS.md 第 2 条：后端四件（content 语料、引擎、契约、路由）逐系统齐备。

    前端五件由 `frontend/tests/architecture/conventions.test.ts` 负责，
    两边不得重复断言同一件事（分工条文见 AGENTS.md 第 2 条）。
    """
    stem = CONTENT_STEM_ALIAS.get(system, system)
    missing = []
    if system not in CONTENT_LESS_SYSTEMS and not list(APP.glob(f"content/{stem}*.py")):
        missing.append(f"content/{stem}*.py")
    if not list(APP.glob(f"engines/{system}.py")) + list(APP.glob(f"engines/{system}_*.py")):
        missing.append(f"engines/{system}.py")
    if not list(APP.glob(f"schemas/{system}*.py")):
        missing.append(f"schemas/{system}.py")
    assert (APP / "api" / "v1" / f"{system}.py").exists()
    assert not missing, f"{system} 缺后端件: {missing}"


@pytest.mark.parametrize("system", _system_names())
def test_every_router_has_golden_tests(system: str) -> None:
    """有路由就必须有对拍：`tests/golden/` 或顶层 `tests/` 任一处命中即通过。

    合婚、流日、流时的对拍住在 `tests/test_bazi_{hehun,liuri,liushi}.py` 而非
    `golden/`，那是既有的分层选择，不算缺口，本测试不为统一目录去搬既有文件。
    这条防的是「新系统只加端点不加对拍」。
    """
    hits = (
        sorted((TESTS / "golden").glob(f"test_{system}*.py"))
        + sorted(TESTS.glob(f"test_{system}*.py"))
    )
    assert hits, f"{system} 有 api/v1 路由却没有任何对拍测试（golden/ 与顶层均无 test_{system}*.py）"
