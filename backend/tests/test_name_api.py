"""端点契约（spec §9.4）：422 机器码、缺值不给占位、简繁入口等价。"""

from fastapi.testclient import TestClient

from app.content.kangxi_strokes import traditional_candidates

#: 扩展 B 的字：确为汉字，但按 spec §5.1 不在本语料范围内 ⇒ 200 + warning，不是 422。
_OUTSIDE_CORPUS = "𠀀"


def _post(
    client: TestClient, surname: str, given: str, variants: dict[str, str] | None = None
):
    return client.post(
        "/api/v1/name/analyze",
        json={"surname": surname, "given": given, "variants": variants},
    )


def test_common_name_returns_the_five_grids_in_order(client: TestClient) -> None:
    body = _post(client, "陸", "青玄").json()
    assert [grid["key"] for grid in body["grids"]] == ["tian", "ren", "di", "wai", "zong"]
    assert [grid["value"] for grid in body["grids"]] == [17, 24, 13, 6, 29]
    assert body["input"]["modality"] == "单姓复名"
    assert body["provenance"]["corpus"]["size"] > 30_000
    assert [table["name"] for table in body["provenance"]["tables"]] == [
        "kangxi_strokes",
        "name_numerology",
        "name_sancai",
        "name_plain",
    ]


def test_non_han_input_is_rejected_with_a_machine_code(client: TestClient) -> None:
    response = _post(client, "L", "青玄")
    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "not_han"
    assert error["message"]
    assert error["context"] == {"field": "surname", "chars": ["L"]}


def test_ambiguous_simplified_lists_every_candidate(client: TestClient) -> None:
    """决策六：一简对多繁不猜正体，把候选一次报全给用户点选。"""
    response = _post(client, "王", "发财")
    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "ambiguous_traditional"
    assert error["context"] == {
        "field": "given",
        "choices": [{"char": "发", "candidates": traditional_candidates("发")}],
    }


def test_variant_must_be_one_of_the_candidates(client: TestClient) -> None:
    response = _post(client, "王", "发财", {"发": "青"})
    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "variant_required"
    assert error["context"] == {
        "field": "given",
        "char": "发",
        "given": "青",
        "candidates": traditional_candidates("发"),
    }


def test_variants_resolve_an_ambiguous_name(client: TestClient) -> None:
    """简体 + variants 与直接写正体必须逐字段同解；展示字形仍留用户输入的那个。"""
    with_variants = _post(client, "王", "发财", {"发": "發"}).json()
    without = _post(client, "王", "發财").json()
    assert with_variants["grids"] == without["grids"]
    assert with_variants["input"]["resolved_traditional"] == "王發財"
    assert without["input"]["resolved_traditional"] == "王發財"
    assert [item["char"] for item in with_variants["chars"]] == ["王", "发", "财"]
    assert [item["resolved"] for item in with_variants["chars"]] == ["王", "發", "財"]


def test_char_outside_the_corpus_keeps_the_unaffected_grids(client: TestClient) -> None:
    """未收录字只污染它参与的那些格：天格仍算得出，三才与 score 整块不出。"""
    response = _post(client, "王", _OUTSIDE_CORPUS)
    assert response.status_code == 200
    body = response.json()
    assert body["warnings"] == [f"stroke_unresolved:{_OUTSIDE_CORPUS}"]
    grids = {grid["key"]: grid for grid in body["grids"]}
    assert [grids[key]["value"] for key in ("tian", "ren", "di", "wai", "zong")] == [
        6,
        None,
        None,
        None,
        None,
    ]
    assert grids["tian"]["formula"] == "5+1"
    assert grids["ren"]["formula"] == "5+?"
    assert grids["wai"]["formula"] == "总格−人格+1"
    assert body["sancai"] is None and body["score"] is None
    text = response.text
    assert '"value":0' not in text and '"number":0' not in text


def test_length_bounds_are_pydantic_validation(client: TestClient) -> None:
    """超长是请求格式错误（FastAPI 的 detail 形状），不是领域错误。"""
    response = _post(client, "王", "青青青青")
    assert response.status_code == 422
    assert "detail" in response.json()