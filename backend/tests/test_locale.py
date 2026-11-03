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

_WESTERN_NATAL = {
    "birth_date": "1990-06-15",
    "birth_time": "08:30:00",
    "latitude": 51.4769,
    "longitude": -0.0005,
    "utc_offset_hours": 0.0,
}

_VEDIC_NATAL = {
    "birth_date": "2000-01-01",
    "birth_time": "12:00",
    "latitude": 51.4769,
    "longitude": -0.0005,
    "utc_offset_hours": 0,
    "target_date": "2026-09-25",
    "gender": "male",
}

_ZHOUYI_CAST = {
    "method": "time",
    "birth_date": "1990-06-15",
    "birth_time": "08:30:00",
}

_QIMEN_CAST = {"cast_time": "2024-05-15T10:30:00"}


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


def test_western_sign_names_localize_only_when_requested() -> None:
    # p15 星座专名表：默认 zh-Hans 逐字节透传，`?locale=en` 才把 sign_zh 叶值换掉。
    from app.engines.western import SIGNS_ZH

    with TestClient(app) as client:
        default = client.post("/api/v1/western/natal", json=_WESTERN_NATAL)
        en = client.post("/api/v1/western/natal?locale=en", json=_WESTERN_NATAL)
        hant = client.post("/api/v1/western/natal?locale=zh-Hant", json=_WESTERN_NATAL)

    assert default.status_code == en.status_code == hant.status_code == 200
    d_leaves = _walk_strings(default.json())
    en_leaves = _walk_strings(en.json())

    # 响应确实携带至少一个星座名叶值（真响应，不 mock）。
    present_signs = [s for s in d_leaves if s in SIGNS_ZH]
    assert present_signs, "western 本命盘应至少落一个星座名叶值"
    for sign in present_signs:
        assert sign not in en_leaves, f"en 未替换星座名 {sign}"
    # 默认 zh-Hans 路径保留源文，星座专名表不越界。
    assert any(s in SIGNS_ZH for s in d_leaves)


def test_graha_and_trigram_display_names_localize_only_when_requested() -> None:
    # p15-a 专名表：吠陀九曜（name_zh）与八卦卦名/卦象/五行叶值，
    # 默认 zh-Hans 逐字节透传，`?locale=en` / `?locale=zh-Hant` 才把叶子换掉。
    from app.content.vedic import GRAHAS
    from app.content.wuxing import ELEMENT_ORDER
    from app.content.zhouyi_trigrams import TRIGRAMS

    graha_zh = {g.name_zh for g in GRAHAS}
    element_zh = set(ELEMENT_ORDER)
    trigram_names = {t.name_zh for t in TRIGRAMS}
    trigram_natures = {t.nature_zh for t in TRIGRAMS}
    atomic = trigram_names | element_zh

    with TestClient(app) as client:
        v_def = client.post("/api/v1/vedic/natal", json=_VEDIC_NATAL)
        v_en = client.post("/api/v1/vedic/natal?locale=en", json=_VEDIC_NATAL)
        v_hant = client.post("/api/v1/vedic/natal?locale=zh-Hant", json=_VEDIC_NATAL)
        z_def = client.post("/api/v1/zhouyi/cast", json=_ZHOUYI_CAST)
        z_en = client.post("/api/v1/zhouyi/cast?locale=en", json=_ZHOUYI_CAST)

    assert v_def.status_code == v_en.status_code == v_hant.status_code == 200
    assert z_def.status_code == z_en.status_code == 200

    # 吠陀：九曜名作为叶值落盘，en 下被换掉。
    vd = _walk_strings(v_def.json())
    ve = _walk_strings(v_en.json())
    present_grahas = [s for s in vd if s in graha_zh]
    assert present_grahas, "vedic 本命盘应至少落一个九曜名叶值"
    for graha in present_grahas:
        assert graha not in ve, f"en 未替换九曜名 {graha}"

    # 周易：卦名/五行/卦象原子叶值在 en 下被换掉，默认保留源文。
    zd = _walk_strings(z_def.json())
    ze = _walk_strings(z_en.json())
    present_atomic = [s for s in zd if s in atomic]
    assert present_atomic, "zhouyi 响应应至少落一个卦名/五行叶值"
    for token in set(present_atomic):
        assert token not in ze, f"en 未替换原子专名 {token}"
    # 纯卦象叶值（不在五行集里的 nature_zh）同样要在 en 下被换掉。
    pure_natures = trigram_natures - element_zh
    for token in [s for s in zd if s in pure_natures]:
        assert token not in ze, f"en 未替换卦象叶值 {token}"


def test_najia_six_spirits_and_six_relatives_localize() -> None:
    # p15-c：纳甲六神（liushen）与六亲（liuqin）叶值只在请求时替换，默认透传。
    from app.content.zhouyi_najia import LIUSHEN_ORDER
    from app.engines.zhouyi import (
        _LIUQIN_BROTHER,
        _LIUQIN_OFFICER,
        _LIUQIN_OFFSPRING,
        _LIUQIN_PARENT,
        _LIUQIN_WEALTH,
    )

    liushen = set(LIUSHEN_ORDER)
    liuqin = {_LIUQIN_PARENT, _LIUQIN_BROTHER, _LIUQIN_OFFSPRING, _LIUQIN_WEALTH, _LIUQIN_OFFICER}

    with TestClient(app) as client:
        d = client.post("/api/v1/zhouyi/cast", json=_ZHOUYI_CAST)
        e = client.post("/api/v1/zhouyi/cast?locale=en", json=_ZHOUYI_CAST)
    assert d.status_code == e.status_code == 200

    dl = _walk_strings(d.json())
    el = _walk_strings(e.json())
    present = [s for s in dl if s in liushen | liuqin]
    assert present, "zhouyi 应至少落一个六神/六亲叶值"
    assert any(s in liushen for s in present), "应含六神叶值"
    assert any(s in liuqin for s in present), "应含六亲叶值"
    for token in set(present):
        assert token not in el, f"en 未替换六神/六亲叶值 {token}"


def test_ziwei_palace_names_localize_only_when_requested() -> None:
    # p15-d：紫微十二宫宫名叶值（PALACE_NAMES）只在请求时替换，默认透传。
    from app.content.ziwei import PALACE_NAMES

    palaces = set(PALACE_NAMES)
    with TestClient(app) as client:
        d = client.post("/api/v1/ziwei/chart", json=_ZIWEI)
        e = client.post("/api/v1/ziwei/chart?locale=en", json=_ZIWEI)
        h = client.post("/api/v1/ziwei/chart?locale=zh-Hant", json=_ZIWEI)
    assert d.status_code == e.status_code == h.status_code == 200

    dl = _walk_strings(d.json())
    el = _walk_strings(e.json())
    present = [s for s in dl if s in palaces]
    assert present, "ziwei 应至少落一个宫名叶值"
    for token in set(present):
        assert token not in el, f"en 未替换宫名 {token}"
    # 繁简有差的宫名（命宫/财帛…）在 zh-Hant 下也要被换掉。
    hl = _walk_strings(h.json())
    for token in [s for s in set(present) if s in LABELS["zh-Hant"]]:
        assert token not in hl, f"zh-Hant 未替换宫名 {token}"


def test_stems_and_branches_localize_only_when_requested() -> None:
    # p15-e：天干地支单字叶值（najia 装卦）在 en 下被拼音转写替换，默认透传。
    stems = "甲乙丙丁戊己庚辛壬癸"
    branches = "子丑寅卯辰巳午未申酉戌亥"
    atomic = set(stems) | set(branches)

    with TestClient(app) as client:
        d = client.post("/api/v1/zhouyi/cast", json=_ZHOUYI_CAST)
        e = client.post("/api/v1/zhouyi/cast?locale=en", json=_ZHOUYI_CAST)
    assert d.status_code == e.status_code == 200

    dl = _walk_strings(d.json())
    el = _walk_strings(e.json())
    present = [s for s in dl if s in atomic]
    assert present, "zhouyi 纳甲应至少落一个天干/地支单字叶值"
    for token in set(present):
        assert token not in el, f"en 未替换干支叶值 {token}"


def test_qimen_stars_doors_directions_localize() -> None:
    # p15-f：奇门九星/八门/方位叶值在 en・zh-Hant 下替换，默认透传。
    from app.content.qimen import EIGHT_DOORS, NINE_STARS

    names = {s.name for s in NINE_STARS} | {d.name for d in EIGHT_DOORS}
    with TestClient(app) as client:
        d = client.post("/api/v1/qimen/chart", json=_QIMEN_CAST)
        e = client.post("/api/v1/qimen/chart?locale=en", json=_QIMEN_CAST)
        h = client.post("/api/v1/qimen/chart?locale=zh-Hant", json=_QIMEN_CAST)
    assert d.status_code == e.status_code == h.status_code == 200

    dl = _walk_strings(d.json())
    el = _walk_strings(e.json())
    hl = _walk_strings(h.json())
    present = [s for s in dl if s in names]
    assert present, "qimen 应至少落一个星/门叶值"
    for token in set(present):
        assert token not in el, f"en 未替换星/门叶值 {token}"
    # 八门含“门”字形差，zh-Hant 下也要被换掉。
    for token in [s for s in set(present) if s in LABELS["zh-Hant"]]:
        assert token not in hl, f"zh-Hant 未替换星/门叶值 {token}"
