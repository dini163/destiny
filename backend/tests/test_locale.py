"""后端响应本地化：默认 zh-Hans 逐字节透传，显式 locale 才换结构化标签。

用真实端点（紫微排盘）取带 `PlainSection.title` 与 `verdict.grade` 的响应，不造任何
mock 载荷（AGENTS §9）。默认路径与 `?locale=en` / `?locale=zh-Hant` 各打一次，比对
形状不变、目标串被换、非标签文本原样。
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.locale_i18n import LABELS, localize, resolve_locale
from app.main import app

_ZIWEI = {
    "birth_date": "1988-02-15",
    "birth_time": "23:30:00",
    "calendar": "lunar",
    "city": "成都",
    "gender": "male",
    "apply_true_solar_time": True,
}


def _walk_strings(value: object) -> list[str]:
    out: list[str] = []
    if isinstance(value, str):
        out.append(value)
    elif isinstance(value, dict):
        for v in value.values():
            out.extend(_walk_strings(v))
    elif isinstance(value, list):
        for v in value:
            out.extend(_walk_strings(v))
    return out


def test_resolve_locale_normalizes() -> None:
    assert resolve_locale(None) == "zh-Hans"
    assert resolve_locale("zh-Hans") == "zh-Hans"
    assert resolve_locale("fr") == "zh-Hans"
    assert resolve_locale("en") == "en"
    assert resolve_locale("zh-Hant") == "zh-Hant"


def test_localize_is_exact_match_only() -> None:
    # 整串命中才换；作为长句一部分的同款字不被动。
    assert localize("全盘气象", "en") == LABELS["en"]["全盘气象"]
    sentence = "全盘气象在这一盘里偏燥。"
    assert localize(sentence, "en") == sentence
    assert localize({"a": ["吉", "其他"]}, "en") == {"a": [LABELS["en"]["吉"], "其他"]}


def test_default_path_is_byte_identical_and_active_locales_swap_labels() -> None:
    with TestClient(app) as client:
        default = client.post("/api/v1/ziwei/chart", json=_ZIWEI)
        en = client.post("/api/v1/ziwei/chart?locale=en", json=_ZIWEI)
        hant = client.post("/api/v1/ziwei/chart?locale=zh-Hant", json=_ZIWEI)

    assert default.status_code == en.status_code == hant.status_code == 200
    d = default.json()
    de = en.json()
    dh = hant.json()

    # 形状（键、层级、数组长度、非标签文本）在三种 locale 下一致。
    assert list(d.keys()) == list(de.keys()) == list(dh.keys())

    # 至少有一个小节标题落在表里，且在 en/zh-Hant 下被换掉。
    titles = [s for s in _walk_strings(d) if s in LABELS["en"]]
    assert titles, "ziwei 响应应携带至少一个可本地化的结构化标签"
    for title in titles:
        assert title not in _walk_strings(de), f"en 未替换 {title}"
        assert title in _walk_strings(d), f"默认路径不该出现替换（应保留源文）"

    # 默认 zh-Hans 与「未知 locale」完全同字节：未知值不进本地化路径。
    with TestClient(app) as client:
        unknown = client.post("/api/v1/ziwei/chart?locale=fr", json=_ZIWEI)
    assert unknown.content == default.content
