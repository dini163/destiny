"""端点契约（Task 9B 判据 ⑫⑬）：大桌走 HTTP 时网格字段不丢、`question` 的长度归 pydantic、
非法 `significator` 今天静默降级。

几何与组合算术在 ``tests/golden/test_lenormand_golden.py``（判据 ⑧-⑪ 在那里锚表侧列、席位
表与邻位算术）；本模块只管「HTTP 这一层有没有把引擎装配好的东西原样递到浏览器」，因此不
import 引擎函数 —— 只 import 一个正则与 ``TestClient``。与 ``test_runes_api.py`` 同一取舍：
字段清单手写而不从 ``LenormandReading.model_fields`` 取，因为「从模型取」对「悄悄少了一个
字段」毫无感觉，而锁死契约面正是它的用途。

三条值得单说：

* **`row`/`col`/`position_key` 必须原样到浏览器**：前端大桌按 ``(row, col)`` 落格、React key
  用 ``position_index``，两件事在同一行 —— ``LenormandBoard.tsx:51`` 的
  ``<div key={card.position_index} style={gridCell(card.row, card.col)} …>``（`gridCell` 自己是
  ``:66-67``）；``position_key`` 今天在前端只出现在类型声明
  （``types/lenormand.ts:52``）—— 于是下面那条 SEAT_KEY 格式断言钉的是**契约面**（键名在
  传输中丢失或改名即坏），不是「页面的 key」。席位表本身的形状归 golden 判据 ⑨，这里只验
  「传输层没把它弄丢或改名」—— 于是断言的是键存在、类型是 ``int``、36 席的 key 互不相同。
* **两种 422 不是一种**：``question`` 的 ``max_length=120``（``schemas/lenormand.py:23``）
  坏在字段自身，走 FastAPI 默认 ``detail`` 形状；``spread_id`` 未知坏在引擎前提，走
  ``{error: {code}}`` 信封（后者已由既有 ``test_lenormand_endpoint_rejects_unknown_spread``
  钉住，本模块不重念）。AGENTS §4 的分工。
* **判据 ⑬ 钉的是缺陷的现状，不是缺陷的正确形态**：见该测 docstring。
"""

import re

from fastapi.testclient import TestClient

URL = "/api/v1/lenormand/draw"

#: 手写而不从 `LenormandReading.model_fields` 取：加/删顶层字段应当是一次显式改动。
TOP_LEVEL_KEYS = {
    "spread_id", "spread_name_zh", "spread_name_en", "layout", "description", "question",
    "cards", "drawn_ids", "combinations", "significator", "synthesis",
    "positive_count", "neutral_count", "negative_count", "plain_summary",
    "rng", "engine", "provenance",
}

#: 一席的全部字段。`row`/`col`/`position_key` 是前端网格的输入（AGENTS §3：snake_case 端到端，
#: 前端不重命名），`essence`/`as_modifier` 是组合直读的两端原料。
CARD_KEYS = {
    "position_index", "position_key", "position_label_zh", "position_meaning", "row", "col",
    "card_id", "number", "name", "name_zh", "polarity", "polarity_label", "keywords",
    "essence", "meaning", "as_modifier", "is_significator",
}

PROVENANCE_KEYS = {"engine", "content_version", "source", "note", "tables"}

#: 全仓约定的反面对手：任何 camelCase / PascalCase 键都意味着有人在前端做了重命名。
SNAKE_CASE = re.compile(r"^[a-z0-9]+(_[a-z0-9]+)*$")
SEAT_KEY = re.compile(r"^seat-\d{2}$")


def _seat_cell(seat: int) -> tuple[int, int]:
    """第 `seat` 席（1 起）该落在哪一格：前 32 席铺 4 行 8 列，末 4 席排第 4 行的 0..3。

    独立手写的算术，不读 `content.lenormand`，这样「交付面 vs 语料表」才是两件事。
    """
    if seat <= 32:
        return (seat - 1) // 8, (seat - 1) % 8
    return 4, seat - 33


def _walk_keys(node: object) -> set[str]:
    """递归收集响应树里出现过的全部键名（字典键、列表元素继续下钻）。"""
    found: set[str] = set()
    if isinstance(node, dict):
        for key, value in node.items():
            found.add(str(key))
            found |= _walk_keys(value)
    elif isinstance(node, list):
        for item in node:
            found |= _walk_keys(item)
    return found


def test_grand_tableau_over_http_delivers_every_grid_field_the_page_needs(client: TestClient) -> None:
    """判据 ⑫：大桌 200、36 席、每席带 `row`/`col`/`position_key`、`rng == "secrets"`、
    出处卡印的「36」与本次发牌张数兑现。

    分工要说清：席位表**该**长什么样（4×8+4，不是 8×8）归 golden 判据 ⑨，那里读语料表；
    本测读的是交付面 —— 每席的 `(row, col)` 必须与它自己的 `position_key` 编号互算得出
    （`_seat_cell` 是手写的算术，不 import 语料），于是「路由器少递一个字段、把行列抹平或
    整体错位、把 snake_case 改成 camelCase」这类只在 HTTP 边界上发生的损坏会在这里红。
    复测：``pytest tests/test_lenormand_api.py -k grid_field``。
    """
    response = client.post(URL, json={"spread_id": "grand_tableau", "question": "今年的合作能否落地"})
    assert response.status_code == 200
    body = response.json()
    assert set(body) == TOP_LEVEL_KEYS
    assert body["layout"] == "tableau"
    assert body["question"] == "今年的合作能否落地"

    cards = body["cards"]
    assert len(cards) == 36
    for card in cards:
        assert set(card) == CARD_KEYS, card["position_key"]
        assert isinstance(card["row"], int) and isinstance(card["col"], int)
        assert SEAT_KEY.match(str(card["position_key"])), card["position_key"]
        assert card["position_label_zh"] and card["position_meaning"]
        assert card["essence"] and card["as_modifier"], "组合直读的两端原料不得为空"
    assert len({card["position_key"] for card in cards}) == 36, "36 席的 key 必须互不相同"
    # 同一份响应内部的跨字段一致性：席位号自己就得算出行列（4×8+4，不是 8×8），
    # 于是「row/col 被抹平或整体错位」这类只在传输层发生的损坏会在这里红，而不必回到
    # golden 去读语料表 —— 判据 ⑨ 钉表的形状，这一行钉交付的形状。
    assert [(card["row"], card["col"]) for card in cards] == [_seat_cell(n) for n in range(1, 37)]
    assert len(set(body["drawn_ids"])) == 36
    assert [card["position_index"] for card in cards] == list(range(36))

    # 抽签类引擎的随机源声明（AGENTS §5 / PRD 铁律）在响应里必须看得见。
    assert body["rng"] == "secrets"
    assert body["engine"] == "lenormand-combination"
    assert set(body["provenance"]) == PROVENANCE_KEYS
    # 出处诚实性（AGENTS §7）：source 印「36 张」，本次张数已在上面钉死为 36，两侧互证。
    assert "36" in body["provenance"]["source"]

    # snake_case 端到端：整棵树里不许出现一个 camelCase 键。
    keys = _walk_keys(body)
    assert keys, "响应树不能是空的"
    assert [key for key in keys if not SNAKE_CASE.match(key)] == []


def test_question_is_a_pydantic_length_bound_not_a_domain_error(client: TestClient) -> None:
    """判据 ⑫ 的边界半边：121 字 → 422 且响应体是 ``detail`` 形状，不是 ``{error}`` 信封。

    AGENTS §4 的分工写在这里最典型：``LenormandRequest.question`` 的
    ``max_length=120``（``schemas/lenormand.py:23``）是字段自身的约束，FastAPI 的默认校验
    就够，引擎根本不会被调用；「这个问句与本局无关」那种前提性错误才归引擎抛 ``DestinyError``
    子类并带机器码。前端读的是 ``error.code``，把这一类也塞进信封就等于发一个不存在的码。
    实测（2026-09-27）：121 字 → ``{"detail": [{"type": "string_too_long", ...}]}``，
    ``detail`` 一项，键为 ``string_too_long``；120 字正常 200 并原样回显。
    """
    too_long = client.post(URL, json={"spread_id": "three_card", "question": "问" * 121})
    assert too_long.status_code == 422
    body = too_long.json()
    assert set(body) == {"detail"}
    assert [item["type"] for item in body["detail"]] == ["string_too_long"]
    assert "error" not in body

    at_the_limit = client.post(URL, json={"spread_id": "three_card", "question": "问" * 120})
    assert at_the_limit.status_code == 200
    assert at_the_limit.json()["question"] == "问" * 120
    assert len(at_the_limit.json()["question"]) == 120


def test_an_unlisted_significator_downgrades_silently_to_seven_pairs(client: TestClient) -> None:
    """判据 ⑬：**钉现状** —— 非法 `significator` 不报错，静默降级为首行线读（7 条组合）。

    今天的行为链是：``schemas/lenormand.py:24`` 把 ``significator`` 声明成自由 ``str | None``
    （无枚举校验），``engines/lenormand.py:64`` 再 ``SIGNIFICATOR_BY_GENDER.get(significator
    or "")`` —— 未命中得 ``None``，于是 ``_tableau_combinations`` 走无指示牌分支，
    ``significator`` 字段为 ``null``，``combinations`` 退回首行 8 席的 7 对。

    AGENTS §4 说「枚举归 pydantic」，按这条该 422；但把 ``significator`` 收成枚举是一次
    **契约动作**（前端 ``LenormandPage`` 送什么值、旧链接带什么参数都要一并核），归另立的
    计划，本轮不动 ``app/**``。**这条测的是今天的行为**：将来加了枚举校验，此测按新行为重写，
    不要留着一个红灯当纪念碑。

    为什么现在必须钉住：不钉的话，「用户要女人牌、拿到一份无指示牌读法」这件事无人知晓。
    定级要说实话：今天的 UI 送不出 ``"MAN"``/``"男"`` —— 前端 ``lib/lenormand.ts:46-50`` 的
    ``SIGNIFICATOR_OPTIONS`` 只有 ``none|male|female``，``:53-54`` 把它们映射成
    ``'male'|'female'|null``，``LenormandPage.tsx:23`` 的 state 就是那个联合，页面也不从 URL
    读该参数。这条钉住的是**直接打 API 的消费者**这条坏路径；一旦有第二个客户端可达
    （分享链接带参 / 移动端 / 开放 API），它就从「小」升「中」—— 后果不是文案难看，而是
    **换了一份读法**：2/3/4 条四正邻位读 → 7 条首行线读，``significator`` 整块不渲染。
    实测（2026-09-27，本函数即复测命令：
    ``pytest tests/test_lenormand_api.py -k unlisted_significator``）：两个值都 200、
    ``significator`` 为 ``null``、``combinations`` 恰 7 条、无一席带 ``is_significator``。
    """
    for value in ("MAN", "男"):
        response = client.post(URL, json={"spread_id": "grand_tableau", "significator": value})
        assert response.status_code == 200, value
        body = response.json()
        assert "error" not in body, value
        assert body["significator"] is None, value
        assert sum(1 for card in body["cards"] if card["is_significator"]) == 0, value
        assert len(body["combinations"]) == 7, value
        assert [combo["context"] for combo in body["combinations"]] == [
            f"第{i}位 → 第{i + 1}位" for i in range(1, 8)
        ], value

    # 对照组：表里认得的值走的是另一条路 —— 真的指示牌对象会出现在响应里，且组合不是那 7 条。
    known = client.post(URL, json={"spread_id": "grand_tableau", "significator": "female"})
    assert known.status_code == 200
    sig = known.json()["significator"]
    assert sig is not None and (sig["number"], sig["name_zh"]) == (29, "女人")
    flagged = [card for card in known.json()["cards"] if card["is_significator"]]
    assert len(flagged) == 1 and (flagged[0]["row"], flagged[0]["col"]) == (sig["row"], sig["col"])
    assert len(known.json()["combinations"]) in {2, 3, 4}, "四正邻位按落席贴边程度取值，永不是 7"


def test_the_reading_lists_both_lenormand_tables_in_provenance(client: TestClient) -> None:
    """读了就列（AGENTS §7 / G19）：白话表进响应清单。

    名单逐字写死而不从 `LENORMAND_CONTENT_SOURCES` 取：`tables` 整表由那份登记常量生成
    （`engines/lenormand.py` 的 `_tables()`），常量少一行、多一行或改了表名都会让这一条
    红；反过来照常量自抄一份，等于让断言跟着被测物一起改（取舍同 `test_qimen_api.py`
    的 `test_the_board_lists_both_qimen_tables_in_provenance`）。
    """
    response = client.post(URL, json={"spread_id": "three_card", "question": "这一季的安排怎么走"})
    body = response.json()
    assert {row["name"] for row in body["provenance"]["tables"]} == {"lenormand", "lenormand_plain"}
    assert all(row["version"] for row in body["provenance"]["tables"])
    assert all(row["source"] for row in body["provenance"]["tables"])


def test_plain_summary_is_a_non_empty_paragraph_distinct_from_synthesis(client: TestClient) -> None:
    """交付面只钉「必填非空 + 首行成句 + 不与 `synthesis` 同文 + 行数 = 席位 + 1」；逐行对账归 golden。"""
    response = client.post(URL, json={"spread_id": "nine_card"})
    body = response.json()
    plain = body["plain_summary"]
    assert plain
    assert plain.split("\n")[0].endswith("。")
    assert plain != body["synthesis"]
    assert len(plain.split("\n")) == len(body["cards"]) + 1
