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

_RUNES_CAST = {"spread_id": "three"}

_TAROT_SPREAD = {"spread_id": "celtic_cross"}

_LENORMAND_TABLEAU = {"spread_id": "grand_tableau"}


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


def test_rune_names_localize_only_when_requested() -> None:
    # p15-g：卢恩符文名（name_zh 叶值）在 en 下换为牌组拉丁名，默认透传。
    # 抽牌随机，故只断言“落盘的符文名均被替换”，不假定具体牌。
    from app.content.rune_futhark import DECK_25

    rune_zh = {r.name_zh for r in DECK_25}
    with TestClient(app) as client:
        d = client.post("/api/v1/runes/cast", json=_RUNES_CAST)
        e = client.post("/api/v1/runes/cast?locale=en", json=_RUNES_CAST)
    assert d.status_code == e.status_code == 200

    dl = _walk_strings(d.json())
    el = _walk_strings(e.json())
    present = [s for s in dl if s in rune_zh]
    assert present, "runes 落宫应至少一个符文名叶值"
    for token in set(present):
        assert token not in el, f"en 未替换符文名 {token}"


def test_name_endpoint_is_exempt_from_localization() -> None:
    # 姓名分析把用户输入的汉字原样回显（NameChar.char）。“金/木”既是五行叶值，
    # 也可能是人名；该路径必须恒透传，不能把人名里的同名汉字翻成五行。
    assert "金" in LABELS["en"] and "木" in LABELS["en"]  # 前提：表里确有这些单字键
    payload = {"surname": "王", "given": "金木"}
    with TestClient(app) as client:
        d = client.post("/api/v1/name/analyze", json=payload)
        e = client.post("/api/v1/name/analyze?locale=en", json=payload)
        h = client.post("/api/v1/name/analyze?locale=zh-Hant", json=payload)
    assert d.status_code == 200
    assert d.content == e.content == h.content, "name 路径应逐字节透传，不参与本地化"
    assert "金" in _walk_strings(d.json())  # 人名字符确实以叶值形式出现


def test_tarot_and_lenormand_card_names_localize() -> None:
    # p15-h：塔罗与雷诺曼牌名（name_zh 叶值）在 en 下换为牌组英文名，默认透传。
    from app.content.lenormand import CARDS as LENO
    from app.content.tarot_deck import DECK as TAROT

    with TestClient(app) as client:
        td = client.post("/api/v1/tarot/spread", json=_TAROT_SPREAD)
        te = client.post("/api/v1/tarot/spread?locale=en", json=_TAROT_SPREAD)
        ld = client.post("/api/v1/lenormand/draw", json=_LENORMAND_TABLEAU)
        le = client.post("/api/v1/lenormand/draw?locale=en", json=_LENORMAND_TABLEAU)
    assert td.status_code == te.status_code == 200
    assert ld.status_code == le.status_code == 200

    tarot_zh = {c.name_zh for c in TAROT}
    leno_zh = {c.name_zh for c in LENO}

    tdl = _walk_strings(td.json())
    tel = _walk_strings(te.json())
    tpresent = {s for s in tdl if s in tarot_zh}
    assert tpresent, "tarot 应至少落一个牌名叶值"
    for token in tpresent:
        assert token not in tel, f"en 未替换塔罗牌名 {token}"

    ldl = _walk_strings(ld.json())
    lel = _walk_strings(le.json())
    lpresent = {s for s in ldl if s in leno_zh}
    assert len(lpresent) >= 30, f"grand_tableau 应落满雷诺曼牌名，实得 {len(lpresent)}"
    for token in lpresent:
        assert token not in lel, f"en 未替换雷诺曼牌名 {token}"


def test_hexagram_names_palace_and_generation_localize() -> None:
    # p15-i：六十四卦全名/短名、八宫宫名、八宫世次叶值在 en 下换为专名英译，默认透传。
    # 用固定手动起卦，卦象/宫/世次叶值稳定落盘（不依赖随机）。
    from app.content.zhouyi_hexagrams import GENERATION_NAMES, HEXAGRAMS, PALACES
    from app.content.zhouyi_trigrams import TRIGRAM_BY_KEY

    full_names = {h.full_name_zh for h in HEXAGRAMS}
    short_names = {h.name_zh for h in HEXAGRAMS}
    palace_names = {f"{TRIGRAM_BY_KEY[pkey].name_zh}宫" for pkey, _ in PALACES}
    generations = set(GENERATION_NAMES)
    atomic = full_names | palace_names | generations

    payload = {
        "method": "manual",
        "manual_coins": [[3, 3, 2], [2, 2, 2], [3, 2, 3], [3, 3, 3], [2, 3, 2], [2, 2, 3]],
        "cast_time": "2024-05-15T10:30:00",
    }
    with TestClient(app) as client:
        d = client.post("/api/v1/zhouyi/cast", json=payload)
        e = client.post("/api/v1/zhouyi/cast?locale=en", json=payload)
    assert d.status_code == e.status_code == 200

    body = d.json()
    dl = _walk_strings(body)
    el = _walk_strings(e.json())
    # 本卦必带全名、宫名、世次三者，逐一断言在 en 下被换掉。
    ben = body["ben"]
    assert ben["full_name_zh"] in full_names
    assert ben["palace_name_zh"] in palace_names
    assert ben["generation"] in generations
    present = [s for s in dl if s in atomic]
    assert present, "zhouyi 应至少落一个卦名/宫名/世次叶值"
    for token in set(present):
        assert token not in el, f"en 未替换卦象专名 {token}"
    # 短名（非八卦卦名的单/双字）也应被换掉；卦名乾坤等已入上表，同词同译。
    non_trigram_shorts = {s for s in dl if s in short_names and s in LABELS["en"]}
    for token in non_trigram_shorts:
        assert token not in el, f"en 未替换卦短名 {token}"


def test_kabbalah_pillars_and_daath_localize() -> None:
    # p15-h：卡巴拉三柱与隐藏原质 Daath 专名叶值只在请求时替换，默认透传。
    # 十原质 name_zh（美/智慧…）与字母音译（辛）因与常用词/天干共形，不入全局表，本测不假定。
    from app.content.kabbalah import DAATH, PILLARS

    keys = {p.name_zh for p in PILLARS.values()} | {DAATH.name_zh}
    assert PILLARS["mercy"].name_zh == "慈悲之柱"
    with TestClient(app) as client:
        d = client.get("/api/v1/kabbalah/tree")
        e = client.get("/api/v1/kabbalah/tree?locale=en")
        h = client.get("/api/v1/kabbalah/tree?locale=zh-Hant")
    assert d.status_code == e.status_code == h.status_code == 200

    dl = _walk_strings(d.json())
    el = _walk_strings(e.json())
    present = {s for s in dl if s in keys}
    assert present == keys, f"tree 应落盘三柱与 Daath 专名，实得 {present}"
    for token in present:
        assert token not in el, f"en 未替换卡巴拉专名 {token}"
    # 字形有差的专名（严厉之柱/知识（隐藏））在 zh-Hant 下也要被换掉。
    hl = _walk_strings(h.json())
    for token in [s for s in present if s in LABELS["zh-Hant"]]:
        assert token not in hl, f"zh-Hant 未替换卡巴拉专名 {token}"


def test_card_and_hexagram_traditional_forms_localize() -> None:
    # p15：塔罗/雷诺曼牌名与六十四卦名的繁体叶子（zh-Hant）——繁简有差者被传统化。
    # 音译专名（卢恩符文）无权威繁体，回落源简体（同 en-only 裁定）。
    from app.core.locale_i18n import localize_str

    hant = {
        "魔术师": "魔術師", "战车": "戰車", "正义": "正義", "宝剑国王": "寶劍国王",
        "星币侍从": "星幣侍從", "骑士": "騎士", "云": "雲",
        "乾为天": "乾為天", "山地剥": "山地剝", "火水未济": "火水未濟", "本宫": "本宮",
    }
    for source, trad in hant.items():
        assert LABELS["zh-Hant"][source] == trad, f"zh-Hant 表里 {source} 应为 {trad}"
        assert localize_str(source, "zh-Hant") == trad
    # 音译符文名不入繁体表——回落源简体，不被机械传统化。
    for rune in ("费胡", "阿尔吉兹", "空白符"):
        assert rune not in LABELS["zh-Hant"], f"卢恩音译名不应入繁体表：{rune}"
        assert localize_str(rune, "zh-Hant") == rune


def test_nakshatras_and_outer_planets_localize() -> None:
    # p15：吠陀二十七星宿名与三颗外行星中文名在 en 下换为拉丁/英文，默认透传。
    from app.content.vedic import NAKSHATRAS

    nak_zh = {n.name_zh for n in NAKSHATRAS}
    planets = {"天王星", "海王星", "冥王星"}
    with TestClient(app) as client:
        v_def = client.post("/api/v1/vedic/natal", json=_VEDIC_NATAL)
        v_en = client.post("/api/v1/vedic/natal?locale=en", json=_VEDIC_NATAL)
        w_def = client.post("/api/v1/western/natal", json=_WESTERN_NATAL)
        w_en = client.post("/api/v1/western/natal?locale=en", json=_WESTERN_NATAL)
    assert v_def.status_code == v_en.status_code == 200
    assert w_def.status_code == w_en.status_code == 200

    vd = _walk_strings(v_def.json())
    ve = _walk_strings(v_en.json())
    present_nak = {s for s in vd if s in nak_zh}
    assert present_nak, "vedic 本命盘应至少落一个星宿名叶值"
    for token in present_nak:
        assert token not in ve, f"en 未替换星宿名 {token}"

    wd = _walk_strings(w_def.json())
    we = _walk_strings(w_en.json())
    present_planets = {s for s in wd if s in planets}
    assert present_planets == planets, f"western 应落三颗外行星，实得 {present_planets}"
    for token in present_planets:
        assert token not in we, f"en 未替换行星名 {token}"


def test_ziwei_star_names_localize() -> None:
    # p15：紫微星名（主/乙级）与四化在 en・zh-Hant 下替换，默认透传。
    from app.content.ziwei import MAJOR_STARS, MINOR_STARS, SIHUA_LABELS
    from app.core.locale_i18n import localize_str

    star_names = set(MAJOR_STARS) | set(MINOR_STARS) | set(SIHUA_LABELS)
    with TestClient(app) as client:
        d = client.post("/api/v1/ziwei/chart", json=_ZIWEI)
        e = client.post("/api/v1/ziwei/chart?locale=en", json=_ZIWEI)
    assert d.status_code == e.status_code == 200
    dl = _walk_strings(d.json())
    el = _walk_strings(e.json())
    present = {s for s in dl if s in star_names}
    assert present, "ziwei 应至少落一个星名/四化叶值"
    for token in present:
        assert token not in el, f"en 未替换星名/四化 {token}"
    # 繁体字形有差的星名在 zh-Hant 下也要被换掉。
    assert localize_str("巨门", "zh-Hant") == "巨門"
    assert localize_str("化禄", "zh-Hant") == "化祿"


_BAZI_NATAL = {
    "birth_date": "1990-06-15",
    "birth_time": "08:30:00",
    "city": "成都",
    "gender": "male",
    "calendar": "solar",
    "apply_true_solar_time": True,
}


def test_bazi_ten_god_names_localize() -> None:
    # p15：八字十神（shishen_gan/ten_god 叶值）在 en・zh-Hant 下替换，默认透传。
    from app.content.bazi_shishen import TEN_GOD_MEANING

    gods = set(TEN_GOD_MEANING) | {"日主"}
    with TestClient(app) as client:
        d = client.post("/api/v1/bazi/natal", json=_BAZI_NATAL)
        e = client.post("/api/v1/bazi/natal?locale=en", json=_BAZI_NATAL)
        h = client.post("/api/v1/bazi/natal?locale=zh-Hant", json=_BAZI_NATAL)
    assert d.status_code == e.status_code == h.status_code == 200
    dl = _walk_strings(d.json())
    el = _walk_strings(e.json())
    hl = _walk_strings(h.json())
    present = {s for s in dl if s in gods}
    assert present, "bazi 命局应至少落一个十神叶值"
    for token in present:
        assert token not in el, f"en 未替换十神 {token}"
    for token in [s for s in present if s in LABELS["zh-Hant"]]:
        assert token not in hl, f"zh-Hant 未替换十神 {token}"


def test_bazi_auxiliary_display_names_localize() -> None:
    # p15：八字辅助专名（维度/柱位/藏干层/旺衰带/十二长生/格局）在 en 下替换，默认透传。
    from app.content.bazi_changsheng import CHANG_SHENG_ORDER
    from app.content.bazi_dimensions import DIMENSION_ORDER
    from app.content.bazi_geju import GEJU_RULES

    tokens = (
        set(DIMENSION_ORDER)
        | {"年柱", "月柱", "日柱", "时柱", "本气", "中气", "余气", "身强", "中和", "身弱"}
        | set(CHANG_SHENG_ORDER)
        | set(GEJU_RULES)
    )
    with TestClient(app) as client:
        d = client.post("/api/v1/bazi/natal", json=_BAZI_NATAL)
        e = client.post("/api/v1/bazi/natal?locale=en", json=_BAZI_NATAL)
    assert d.status_code == e.status_code == 200
    dl = _walk_strings(d.json())
    el = _walk_strings(e.json())
    present = {s for s in dl if s in tokens}
    assert present, "bazi 命局应至少落一个辅助专名叶值"
    for token in present:
        assert token not in el, f"en 未替换辅助专名 {token}"
    # 直接单测：十二长生与格局根干取到预期译文。
    assert localize("长生", "en") == "Growth"
    assert localize("七杀格", "en") == "Qisha Structure"
    assert localize("事业", "zh-Hant") == "事業"
    assert localize("建禄格", "zh-Hant") == "建祿格"


def test_bazi_nayin_and_shensha_localize() -> None:
    # p15：六十甲子纳音与神煞在 en 下替换（真端点取到哪个换哪个），默认透传。
    from app.content.bazi_nayin import NAYIN_MEANING
    from app.content.bazi_shensha import SHENSHA_RULES

    tokens = {c.nayin for c in NAYIN_MEANING.values()} | (
        set(SHENSHA_RULES) - {"十二长生"}
    )
    with TestClient(app) as client:
        d = client.post("/api/v1/bazi/natal", json=_BAZI_NATAL)
        e = client.post("/api/v1/bazi/natal?locale=en", json=_BAZI_NATAL)
    assert d.status_code == e.status_code == 200
    dl = _walk_strings(d.json())
    el = _walk_strings(e.json())
    present = {s for s in dl if s in tokens}
    assert present, "bazi 命局应至少落一个纳音/神煞叶值"
    for token in present:
        assert token not in el, f"en 未替换纳音/神煞 {token}"
    # 直接单测：钗钏金（易错字）的 en 与繁体、神煞的 en 与繁体均取到预期译文。
    assert localize("钗钏金", "en") == "Hairpin Metal"
    assert localize("钗钏金", "zh-Hant") == "釵釧金"
    assert localize("天乙贵人", "en") == "Celestial Noble"
    assert localize("天乙贵人", "zh-Hant") == "天乙貴人"
    assert localize("空亡", "en") == "Void"


def test_ganzhi_pillars_localize() -> None:
    # p15：六十甲子干支柱在 en 下替换（拼音），皆繁简同形故 zh-Hant 逐字节透传。
    stems = "甲乙丙丁戊己庚辛壬癸"
    branches = "子丑寅卯辰巳午未申酉戌亥"
    gz60 = {stems[i % 10] + branches[i % 12] for i in range(60)}
    with TestClient(app) as client:
        d = client.post("/api/v1/bazi/natal", json=_BAZI_NATAL)
        e = client.post("/api/v1/bazi/natal?locale=en", json=_BAZI_NATAL)
        h = client.post("/api/v1/bazi/natal?locale=zh-Hant", json=_BAZI_NATAL)
    assert d.status_code == e.status_code == h.status_code == 200
    dl = _walk_strings(d.json())
    el = _walk_strings(e.json())
    hl = _walk_strings(h.json())
    present = {s for s in dl if s in gz60}
    assert present, "bazi 命局应至少落一个干支柱叶值"
    for token in present:
        assert token not in el, f"en 未替换干支柱 {token}"
        # 繁简同形：zh-Hant 应保留原串（仍作为叶值出现）。
        assert token in hl, f"zh-Hant 不应改动干支柱 {token}"
    assert localize("甲子", "en") == "Jia Zi"
    assert localize("癸亥", "en") == "Gui Hai"
    assert localize("甲子", "zh-Hant") == "甲子"


def test_bazi_relation_enum_localize() -> None:
    # p15：干支关系枚举名（合冲刑害会·伏反吟）在 en 下替换，繁体字形有差者同步。
    from app.content.bazi_relations import RELATION_TABLES

    names = set(RELATION_TABLES.keys())
    with TestClient(app) as client:
        d = client.post("/api/v1/bazi/natal", json=_BAZI_NATAL)
        e = client.post("/api/v1/bazi/natal?locale=en", json=_BAZI_NATAL)
    assert d.status_code == e.status_code == 200
    dl = _walk_strings(d.json())
    el = _walk_strings(e.json())
    present = {s for s in dl if s in names}
    assert present, "bazi 命局应至少落一个干支关系枚举叶值"
    for token in present:
        assert token not in el, f"en 未替换关系枚举 {token}"
    # 直接单测：全族枚举在两种语种都取到预期译文（不依赖本盘是否出现）。
    assert localize("地支六冲", "en") == "Six Branch Clashes"
    assert localize("伏吟", "en") == "Fu Yin Repetition"
    assert localize("自刑", "en") == "Self Punishment"
    assert localize("地支六冲", "zh-Hant") == "地支六沖"
    assert localize("无恩之刑", "zh-Hant") == "無恩之刑"
    # 繁简同形的枚举回落源文。
    assert localize("三合", "zh-Hant") == "三合"


def test_bazi_structured_labels_localize() -> None:
    # p15：用神三法/柱距档/岁运档/基准行等结构化标签在 en・zh-Hant 下替换。
    from app.engines.bazi_rules import FARTHEST, STRENGTH_BY_DISTANCE

    tokens = (
        {"扶抑", "通关", "调候", "顺", "滞", "基准分"}
        | set(STRENGTH_BY_DISTANCE.values())
        | {FARTHEST}
    )
    with TestClient(app) as client:
        d = client.post("/api/v1/bazi/natal", json=_BAZI_NATAL)
        e = client.post("/api/v1/bazi/natal?locale=en", json=_BAZI_NATAL)
    assert d.status_code == e.status_code == 200
    dl = _walk_strings(d.json())
    el = _walk_strings(e.json())
    present = {s for s in dl if s in tokens}
    assert present, "bazi 命局应至少落一个结构化标签叶值"
    for token in present:
        assert token not in el, f"en 未替换结构化标签 {token}"
    # 直接单测：三法与档位、繁体转形取到预期译文。
    assert localize("通关", "en") == "Mediation"
    assert localize("紧临", "en") == "Adjacent"
    assert localize("顺", "en") == "Favorable"
    assert localize("通关", "zh-Hant") == "通關"
    assert localize("滞", "zh-Hant") == "滯"
    assert localize("基准分", "zh-Hant") == "基準分"


def test_zhouyi_yao_position_names_localize() -> None:
    # p15：六爻爻题（初九/六二…上六）在 en 下替换；皆繁简同形，zh-Hant 逐字节透传。
    from app.content.zhouyi_text import line_name

    yao = {line_name(pos, yang) for pos in range(1, 7) for yang in (True, False)}
    assert len(yao) == 12
    with TestClient(app) as client:
        d = client.post("/api/v1/zhouyi/cast", json=_ZHOUYI_CAST)
        e = client.post("/api/v1/zhouyi/cast?locale=en", json=_ZHOUYI_CAST)
        h = client.post("/api/v1/zhouyi/cast?locale=zh-Hant", json=_ZHOUYI_CAST)
    assert d.status_code == e.status_code == h.status_code == 200
    dl = _walk_strings(d.json())
    el = _walk_strings(e.json())
    hl = _walk_strings(h.json())
    present = {s for s in dl if s in yao}
    assert present, "zhouyi 投盘应至少落一个爻题叶值"
    for token in present:
        assert token not in el, f"en 未替换爻题 {token}"
        assert token in hl, f"zh-Hant 不应改动爻题 {token}"
    assert localize("初六", "en") == "First Line (Yin)"
    assert localize("九五", "en") == "Fifth Line (Yang)"
    assert localize("上九", "en") == "Top Line (Yang)"
    assert localize("九二", "zh-Hant") == "九二"


def test_solar_terms_localize() -> None:
    # p15：二十四节气叶值在 en 下替换；字形有差者（惊/蛰/种/满/处）zh-Hant 转形，余透传。
    import app.content.qimen as Q

    terms = set(Q.YANG_JU) | set(Q.YIN_JU)
    assert len(terms) == 24
    with TestClient(app) as client:
        d = client.post("/api/v1/qimen/chart", json=_QIMEN_CAST)
        e = client.post("/api/v1/qimen/chart?locale=en", json=_QIMEN_CAST)
        h = client.post("/api/v1/qimen/chart?locale=zh-Hant", json=_QIMEN_CAST)
    assert d.status_code == e.status_code == h.status_code == 200
    dl = _walk_strings(d.json())
    el = _walk_strings(e.json())
    hl = _walk_strings(h.json())
    present = {s for s in dl if s in terms}
    assert present, "qimen 应至少落一个节气叶值"
    for token in present:
        assert token not in el, f"en 未替换节气 {token}"
    # 直接单测：全族取到预期英译；繁简同形者 zh-Hant 透传，字形有差者转形。
    assert localize("立春", "en") == "Start of Spring"
    assert localize("惊蛰", "en") == "Awakening of Insects"
    assert localize("大寒", "en") == "Major Cold"
    assert localize("立春", "zh-Hant") == "立春"
    assert localize("惊蛰", "zh-Hant") == "驚蟄"
    assert localize("芒种", "zh-Hant") == "芒種"
    assert localize("处暑", "zh-Hant") == "處暑"


def test_wangshuai_grades_and_sanyuan_localize() -> None:
    # p15：月令旺相休囚死（梅花落叶）与奇门三元在 en 下替换；均繁简同形，zh-Hant 透传。
    import app.content.qimen as Q
    from app.content.bazi_wangshuai import WANG_SHUAI_VALUE

    meihua_cast = {
        "method": "time",
        "birth_date": "1990-06-15",
        "birth_time": "08:30:00",
    }
    ws = set(WANG_SHUAI_VALUE)
    yuan = set(Q.YUAN_NAMES)
    assert ws == {"旺", "相", "休", "囚", "死"}
    with TestClient(app) as client:
        md = client.post("/api/v1/meihua/cast", json=meihua_cast)
        me = client.post("/api/v1/meihua/cast?locale=en", json=meihua_cast)
        mh = client.post("/api/v1/meihua/cast?locale=zh-Hant", json=meihua_cast)
        qd = client.post("/api/v1/qimen/chart", json=_QIMEN_CAST)
        qe = client.post("/api/v1/qimen/chart?locale=en", json=_QIMEN_CAST)
    assert md.status_code == me.status_code == mh.status_code == 200
    assert qd.status_code == qe.status_code == 200
    mdl = _walk_strings(md.json())
    mel = _walk_strings(me.json())
    mhl = _walk_strings(mh.json())
    present = {s for s in mdl if s in ws}
    assert present, "meihua 应至少落一个旺相休囚死叶值"
    for token in present:
        assert token not in mel, f"en 未替换旺衰 {token}"
        assert token in mhl, f"zh-Hant 不应改动旺衰 {token}"
    qdl = _walk_strings(qd.json())
    qel = _walk_strings(qe.json())
    qpresent = {s for s in qdl if s in yuan}
    assert qpresent, "qimen 应至少落一个三元叶值"
    for token in qpresent:
        assert token not in qel, f"en 未替换三元 {token}"
    # 直接单测：全族取到预期英译；死复用十二长生 Death；繁简同形透传。
    assert localize("旺", "en") == "Prosperous"
    assert localize("囚", "en") == "Imprisoned"
    assert localize("死", "en") == "Death"
    assert localize("上元", "en") == "Upper Yuan"
    assert localize("下元", "en") == "Lower Yuan"
    assert localize("旺", "zh-Hant") == "旺"
    assert localize("中元", "zh-Hant") == "中元"


def test_numerology_display_names_localize() -> None:
    # p15：数理显示名（核心/顶峰/挑战/周期标签、洛书八平面、核心数关键词）在 en 下替换。
    import app.engines.numerology as N
    import app.content.numerology_loshu as L
    from app.content.numerology_meanings import CORE_MEANINGS

    payload = {"birth_date": "1990-06-15", "full_name": "John Smith"}
    kw = {k for cm in CORE_MEANINGS.values() for k in cm.keywords}
    planes = {p.name_zh for p in L.PLANES}
    labels = (
        set(N.CORE_LABELS.values())
        | set(N.PINNACLE_LABELS.values())
        | set(N.CHALLENGE_LABELS.values())
        | set(N.CYCLE_LABELS.values())
    )
    tokens = kw | planes | labels
    with TestClient(app) as client:
        d = client.post("/api/v1/numerology/chart", json=payload)
        e = client.post("/api/v1/numerology/chart?locale=en", json=payload)
    assert d.status_code == e.status_code == 200
    dl = _walk_strings(d.json())
    el = _walk_strings(e.json())
    present = {s for s in dl if s in tokens}
    assert present, "numerology 应至少落一个显示名叶值"
    for token in present:
        assert token not in el, f"en 未替换数理显示名 {token}"
    # 直接单测：双语卡标签取英文尾；平面取权威 name_en；关键词取英译。
    assert localize("生命灵数 Life Path", "en") == "Life Path"
    assert localize("主挑战 Main Challenge", "en") == "Main Challenge"
    assert localize("心智平面", "en") == "Mental Plane"
    assert localize("银弓（财富之箭）", "en") == "Silver Yog"
    assert localize("乐观", "en") == "Optimistic"
    # zh-Hant：权威全串转形；繁简同形透传；含一对多歧义字者（实干）透传。
    assert localize("灵魂冲动数 Soul Urge", "zh-Hant") == "靈魂衝動數 Soul Urge"
    assert localize("实务平面", "zh-Hant") == "實務平面"
    assert localize("乐观", "zh-Hant") == "樂觀"
    assert localize("心智平面", "zh-Hant") == "心智平面"
    assert localize("实干", "zh-Hant") == "实干"


def test_bazi_transit_rule_labels_localize() -> None:
    # p15：岁运账本规则短名与粒度名在 en 下替换；干留天干之干，冲取六冲之沖。
    from app.content.bazi_transit_rules import TRANSIT_RULES

    payload = {
        "birth_date": "1990-06-15", "birth_time": "08:30:00", "city": "成都",
        "gender": "male", "calendar": "solar", "apply_true_solar_time": True, "target_year": 2026,
    }
    labels = {r.label for r in TRANSIT_RULES.values()}
    with TestClient(app) as client:
        d = client.post("/api/v1/bazi/liuyue", json=payload)
        e = client.post("/api/v1/bazi/liuyue?locale=en", json=payload)
    assert d.status_code == e.status_code == 200
    dl = _walk_strings(d.json())
    el = _walk_strings(e.json())
    present = {s for s in dl if s in labels}
    assert present, "bazi 岁运应至少落一个规则短名叶值"
    for token in present:
        assert token not in el, f"en 未替换岁运规则短名 {token}"
    # 直接单测：全族取到预期英译；繁体对干/冲/岁取正确字形，无差者透传。
    assert localize("值太岁", "en") == "Encountering Tai Sui"
    assert localize("日主临衰病死墓绝", "en") == "Day Master at Decline, Illness, Death, Tomb, Extinction"
    assert localize("流年", "en") == "Flowing Year"
    assert localize("大运", "en") == "Major Luck Cycle"
    assert localize("运干入喜用", "zh-Hant") == "運干入喜用"
    assert localize("冲太岁", "zh-Hant") == "沖太歲"
    assert localize("半合忌", "zh-Hant") == "半合忌"
    assert localize("三会忌", "zh-Hant") == "三會忌"
    assert localize("大运", "zh-Hant") == "大運"


def test_ziwei_qimen_meihua_aux_labels_localize() -> None:
    # p15：紫微 kind/阴阳/顺逆行、奇门阳遁阴遁、梅花体用小节标签/体用关系/月令季节/旺衰档位。
    from app.content.meihua import SEASON_BY_MONTH_ZHI, TIYONG_RELATIONS

    ziwei_payload = {
        "birth_date": "2000-08-16", "birth_time": "12:00", "calendar": "solar",
        "longitude": 116.4074, "gender": "male", "apply_true_solar_time": False,
    }
    meihua_payload = {"method": "time", "birth_date": "1990-06-15", "birth_time": "08:30:00"}

    ziwei_aux = {"主星", "煞", "禄马", "顺行", "逆行", "阳", "阴"}
    qimen_dun = {"阳遁", "阴遁"}
    relations = {r.name_zh for r in TIYONG_RELATIONS.values()}
    seasons = set(SEASON_BY_MONTH_ZHI.values())
    assert len(relations) == 5 and len(seasons) == 12

    with TestClient(app) as client:
        zd = client.post("/api/v1/ziwei/chart", json=ziwei_payload)
        ze = client.post("/api/v1/ziwei/chart?locale=en", json=ziwei_payload)
        qd = client.post("/api/v1/qimen/chart", json=_QIMEN_CAST)
        qe = client.post("/api/v1/qimen/chart?locale=en", json=_QIMEN_CAST)
        md = client.post("/api/v1/meihua/cast", json=meihua_payload)
        me = client.post("/api/v1/meihua/cast?locale=en", json=meihua_payload)
        mh = client.post("/api/v1/meihua/cast?locale=zh-Hant", json=meihua_payload)
    assert all(r.status_code == 200 for r in (zd, ze, qd, qe, md, me, mh))

    zpresent = {s for s in _walk_strings(zd.json()) if s in ziwei_aux}
    assert zpresent, "ziwei 应至少落一个辅助显示名叶值"
    zel = _walk_strings(ze.json())
    for token in zpresent:
        assert token not in zel, f"en 未替换紫微辅助名 {token}"

    qpresent = {s for s in _walk_strings(qd.json()) if s in qimen_dun}
    assert qpresent, "qimen 应至少落一个遁局叶值"
    qel = _walk_strings(qe.json())
    for token in qpresent:
        assert token not in qel, f"en 未替换奇门遁局 {token}"

    me_family = relations | seasons | {
        "体用生克", "卦气旺衰", "互卦(过程)", "变卦(结局)", "上吉", "小吉", "中平", "大凶",
    }
    mpresent = {s for s in _walk_strings(md.json()) if s in me_family}
    assert mpresent, "meihua 应至少落一个体用小节/关系/季节叶值"
    mel = _walk_strings(me.json())
    for token in mpresent:
        assert token not in mel, f"en 未替换梅花标签 {token}"

    # 直接单测：全族取到预期英译；字形有差者（体→體/气→氣/过→過/变→變/马→馬/阳→陽）zh-Hant 转形，同形者透传。
    assert localize("主星", "en") == "Major Star"
    assert localize("禄马", "en") == "Prosperity & Horse"
    assert localize("阳遁", "en") == "Yang Dun"
    assert localize("体用比和", "en") == "Ti & Yong Harmonious"
    assert localize("季秋", "en") == "Late Autumn"
    assert localize("互卦(过程)", "en") == "Nuclear Hexagram (Process)"
    assert localize("禄马", "zh-Hant") == "祿馬"
    assert localize("阳", "zh-Hant") == "陽"
    assert localize("体用生克", "zh-Hant") == "體用生克"
    assert localize("变卦(结局)", "zh-Hant") == "變卦(結局)"
    assert localize("主星", "zh-Hant") == "主星"
    assert localize("季秋", "zh-Hant") == "季秋"
    assert localize("逆行", "zh-Hant") == "逆行"


def test_qimen_ju_name_and_branch_pairs_localize() -> None:
    # p15：奇门局名（阳遁/阴遁 × 一..九局）与宫位/旬空地支二支对在 en 下替换；局名 zh-Hant 仅阳/阴转形，地支对同形透传。
    import app.content.qimen as C
    import app.engines.qimen as Q

    ju = {f"{dun}{Q._cn_number(n)}局" for dun in ("阳遁", "阴遁") for n in range(1, 10)}
    pairs = {p.zhi for p in C.LUOSHU.values() if len(p.zhi) == 2} | {
        v for v in C.XUNKONG_BY_XUNSHOU.values() if len(v) == 2
    }
    assert len(ju) == 18
    family = ju | pairs
    with TestClient(app) as client:
        d = client.post("/api/v1/qimen/chart", json=_QIMEN_CAST)
        e = client.post("/api/v1/qimen/chart?locale=en", json=_QIMEN_CAST)
        h = client.post("/api/v1/qimen/chart?locale=zh-Hant", json=_QIMEN_CAST)
    assert d.status_code == e.status_code == h.status_code == 200
    dl = _walk_strings(d.json())
    el = _walk_strings(e.json())
    hl = _walk_strings(h.json())
    present = {s for s in dl if s in family}
    assert present, "qimen 应至少落一个局名或地支对叶值"
    for token in present:
        assert token not in el, f"en 未替换奇门局名/地支对 {token}"
    # 地支二支对繁简同形：zh-Hant 逐字节透传（局名转形不在此断言，取固定单测）。
    for token in present & pairs:
        assert token in hl, f"zh-Hant 不应改动地支对 {token}"
    # 局名 zh-Hant 仅阳/阴转形（遁/局/数字同形）；地支对繁简同形透传。
    assert localize("阳遁四局", "zh-Hant") == "陽遁四局"
    assert localize("阴遁一局", "zh-Hant") == "陰遁一局"
    assert localize("戌亥", "zh-Hant") == "戌亥"
    # 直接单测：全族取到预期英译（局名 Yang/Yin Dun Ju N；地支对沿用单支 pinyin）。
    assert localize("阳遁一局", "en") == "Yang Dun Ju 1"
    assert localize("阴遁九局", "en") == "Yin Dun Ju 9"
    assert localize("丑寅", "en") == "Chou & Yin"
    assert localize("戌亥", "en") == "Xu & Hai"


def test_star_door_god_nature_localize() -> None:
    # p15：紫微十四主星 + 奇门九星/八门/八神 类象 nature 在 en 下全替换；繁简同形者 zh-Hant 透传。
    import app.content.ziwei as Z
    import app.content.qimen as Q

    natures = (
        {s.nature for s in Z.MAJOR_STARS.values()}
        | {s.nature for s in Q.NINE_STARS}
        | {d.nature for d in Q.EIGHT_DOORS}
        | set(Q.GOD_NATURE.values())
    )
    assert len(natures) == 39
    ziwei_payload = {
        "birth_date": "2000-08-16", "birth_time": "12:00", "calendar": "solar",
        "longitude": 116.4074, "gender": "male", "apply_true_solar_time": False,
    }
    with TestClient(app) as client:
        zd = client.post("/api/v1/ziwei/chart", json=ziwei_payload)
        ze = client.post("/api/v1/ziwei/chart?locale=en", json=ziwei_payload)
        qd = client.post("/api/v1/qimen/chart", json=_QIMEN_CAST)
        qe = client.post("/api/v1/qimen/chart?locale=en", json=_QIMEN_CAST)
    assert zd.status_code == ze.status_code == qd.status_code == qe.status_code == 200
    for d, el in ((zd, _walk_strings(ze.json())), (qd, _walk_strings(qe.json()))):
        present = {s for s in _walk_strings(d.json()) if s in natures}
        assert present, "排盘应至少落一个类象 nature 叶值"
        for token in present:
            assert token not in el, f"en 未替换 nature {token}"
    # 直接单测：全族取到英译；字形有差者 zh-Hant 转形（冲->衝/发->發/贵->貴），同形者透传。
    assert localize("帝座·尊贵领导", "en") == "Imperial Seat · Noble Leadership"
    assert localize("左辅·诚信敦厚", "en") == "Left Assistant · Sincere Generosity"
    assert localize("贵人首领·百恶不侵", "en") == "Noble Chief · Impervious to Evil"
    assert localize("将星·冲劲肃杀", "zh-Hant") == "將星·衝勁肅殺"
    assert localize("开通发达·求财赴任", "zh-Hant") == "開通發達·求財赴任"
    assert localize("财库·稳重保守", "zh-Hant") == "財庫·穩重保守"
    assert localize("福禄·温和享受", "zh-Hant") == "福禄·温和享受"
    assert localize("和合婚姻·交易中介", "zh-Hant") == "和合婚姻·交易中介"


def test_zodiac_animals_localize() -> None:
    # p15：十二生肖（.zodiac，lunar-python 立春生肖）en 全替换；仅龙/马/鸡/猪
    # 字形有差者 zh-Hant 转形，其余繁简同形透传。蛇/狗 复用卡牌既有英译。
    zodiac = {"鼠", "牛", "虎", "兔", "龙", "蛇", "马", "羊", "猴", "鸡", "狗", "猪"}
    payload = {
        "birth_date": "1990-06-15", "birth_time": "08:30:00", "city": "成都",
        "gender": "male", "calendar": "solar", "apply_true_solar_time": True,
    }
    with TestClient(app) as client:
        zd = client.post("/api/v1/bazi/natal", json=payload)
        ze = client.post("/api/v1/bazi/natal?locale=en", json=payload)
        zh = client.post("/api/v1/bazi/natal?locale=zh-Hant", json=payload)
    assert zd.status_code == ze.status_code == zh.status_code == 200
    present = {s for s in _walk_strings(zd.json()) if s in zodiac}
    assert present, "八字本命盘应落一个生肖叶值"
    en_leaves = _walk_strings(ze.json())
    for token in present:
        assert token not in en_leaves, f"en 未替换生肖 {token}"
    zh_leaves = _walk_strings(zh.json())
    for token in present:
        expected = localize(token, "zh-Hant")
        assert expected in zh_leaves, f"zh-Hant 未落地 {token}->{expected}"
    # 直接单测：全族英译；字形有差者转形，同形者透传。
    assert localize("马", "en") == "Horse"
    assert localize("龙", "en") == "Dragon"
    assert localize("鼠", "en") == "Rat"
    assert localize("猪", "en") == "Pig"
    assert localize("马", "zh-Hant") == "馬"
    assert localize("龙", "zh-Hant") == "龍"
    assert localize("鸡", "zh-Hant") == "雞"
    assert localize("猪", "zh-Hant") == "豬"
    assert localize("鼠", "zh-Hant") == "鼠"
    assert localize("牛", "zh-Hant") == "牛"
    assert localize("蛇", "en") == "Snake"
    assert localize("狗", "en") == "Dog"


def test_prose_fixed_lines_localize() -> None:
    # p16：合成段落（compose 以 \n 连接开篇句/条目/收尾句）在 en 下按**整行精确匹配**本地化，
    # 命中的固定行被换、未登记的逐条判语原样保留；默认 zh-Hans 路径逐字节透传不动。
    import app.content.bazi_plain as B

    openers = set(B.DIMENSION_OPENERS.values())
    closers = set(B.TIER_CLOSERS.values())
    payload = {
        "birth_date": "1990-06-15", "birth_time": "08:30:00", "city": "成都",
        "gender": "male", "calendar": "solar", "apply_true_solar_time": True,
    }
    with TestClient(app) as client:
        d = client.post("/api/v1/bazi/natal", json=payload)
        e = client.post("/api/v1/bazi/natal?locale=en", json=payload)
    assert d.status_code == e.status_code == 200
    # 直接单测：合成串里命中的固定行被换，其余行原样；未含换行的长句不误伤。
    opener = next(iter(openers))
    composed = f"{opener}\n你命里的某条判语。"
    localized = localize(composed, "en")
    assert localized != composed, "en 应换掉合成段落里的开篇句那一行"
    assert localized.endswith("\n你命里的某条判语。"), "未登记的条目行必须逐字节保留"
    assert localize(opener, "zh-Hans") == opener, "默认 locale 不得动合成段落"
    # 端到端：某维 plain 的首行（开篇句）在 en 下变英、默认路径不变。
    dleaf = d.json()["interpretation"]["six_dimensions"][0]["plain"]
    eleaf = e.json()["interpretation"]["six_dimensions"][0]["plain"]
    assert dleaf.split("\n")[0] in (openers | closers), "首行应是已登记的固定开篇句"
    assert eleaf.split("\n")[0] != dleaf.split("\n")[0], "en 未本地化开篇句行"
    assert eleaf.split("\n")[0].isascii(), f"en 开篇句行仍含非 ASCII：{eleaf.split(chr(10))[0]!r}"


def test_prose_fixed_lines_localize_zh_hant() -> None:
    # p16：有界固定行（开篇句 / 档位收尾句）的繁体转换——合成段落里命中的固定行被转成
    # 繁体，未登记的逐条判语原样逐字节保留；默认 zh-Hans 路径透传不动。逐行经 OpenCC
    # s2tw 短语级转换后校对；本语料内地支「丑」与吉凶档「凶」各自只有一义，已把
    # s2tw 的 醜 / 兇 误转回 丑 / 凶。
    import app.content.bazi_plain as B
    from app.core.locale_i18n import LABELS

    openers = set(B.DIMENSION_OPENERS.values()) | set(B.TIER_CLOSERS.values())
    ht = LABELS["zh-Hant"]
    assert all(k in ht for k in openers), "87 固定行的繁体须全登记"
    joined = "".join(ht.values())
    assert "醜" not in joined and "兇" not in joined, "地支丑/吉凶档 被误转为 醜/兇"

    payload = {
        "birth_date": "1990-06-15", "birth_time": "08:30:00", "city": "成都",
        "gender": "male", "calendar": "solar", "apply_true_solar_time": True,
    }
    with TestClient(app) as client:
        d = client.post("/api/v1/bazi/natal", json=payload)
        h = client.post("/api/v1/bazi/natal?locale=zh-Hant", json=payload)
    assert d.status_code == h.status_code == 200

    opener = next(iter(set(B.DIMENSION_OPENERS.values())))
    composed = f"{opener}\n你命里的某条判语。"
    localized = localize(composed, "zh-Hant")
    assert localized != composed, "zh-Hant 应换掉合成段落里的开篇句那一行"
    assert localized.endswith("\n你命里的某条判语。"), "未登记的条目行必须逐字节保留"
    assert localize(opener, "zh-Hans") == opener, "默认 locale 不得动合成段落"

    dleaf = d.json()["interpretation"]["six_dimensions"][0]["plain"]
    hleaf = h.json()["interpretation"]["six_dimensions"][0]["plain"]
    assert dleaf.split("\n")[0] != hleaf.split("\n")[0], "zh-Hant 未本地化开篇句行"
    assert dleaf.split("\n")[1] != hleaf.split("\n")[1], "逐条判语行在 zh-Hant 下已本地化"


def test_judgment_prose_localize_zh_hant() -> None:
    # p16：逐条判语（compose 逐字搬运的各系统条目白话）的繁体登记——判语行在 zh-Hant
    # 下被整行精确换为繁体，未含换行的单条判语走整串精确匹配；含 {} 槽位的模板帧不登记
    # （合成后不等于任何整行）；默认 zh-Hans 逐字节透传。转换经 OpenCC s2tw 后按本语料
    # 术语校正（地支丑/吉凶档/咸卦/面(皮)/回(音)/合(眼缘) 不被误转）。
    import app.engines.plain_corpora as PC
    from app.core.locale_i18n import LABELS

    ht = LABELS["zh-Hant"]
    corpora = [x for x in vars(PC).values() if type(x).__name__ == "PlainCorpus"]
    registered = 0
    for c in corpora:
        for v in c.entries.values():
            if "{" in v or "}" in v:
                continue
            assert v in ht, f"{c.system} 逐条判语未登记繁体：{v[:16]}"
            assert localize(v, "zh-Hant") != v, f"{c.system} 判语繁体应与原文不同：{v[:16]}"
            assert localize(v, "zh-Hans") == v
            registered += 1
    assert registered > 2000, registered
    # 术语回退在整表层面无残留
    joined = "".join(ht.values())
    for bad in ("醜", "兇", "鹹", "麵", "閤", "迴"):
        assert bad not in joined, f"术语误转残留：{bad}"
    assert "紫微在丑" in joined and "咸卦的卦辭" in joined


def test_template_frames_excluded_from_line_keys() -> None:
    # p16：含 {} 槽位的模板帧不作整行键（合成后 filled 值不等于任何整行，行级匹配跳过）。
    import app.engines.plain_corpora as PC
    from app.core.locale_i18n import LABELS

    ht = LABELS["zh-Hant"]
    corpora = [x for x in vars(PC).values() if type(x).__name__ == "PlainCorpus"]
    templates = [v for c in corpora for v in c.entries.values() if "{" in v or "}" in v]
    assert templates, "expected template-brace frames to exist"
    for v in templates:
        assert v not in ht, f"模板帧不应作整行键：{v[:16]}"
