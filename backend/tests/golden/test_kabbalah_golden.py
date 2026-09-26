"""Golden tests for the Kabbalah Tree of Life map and the gematria fold.

The Tree is fixed Golden Dawn content: ten Sephiroth (+ the hidden Daath), twenty-two
paths numbered 11-32, three pillars and four worlds. Gematria weighs Latin letters
A=1…Z=26; the arithmetic is independently verifiable (LIGHT = 12+9+7+8+20 = 56,
digital root 2; CHAI = 3+8+1+9 = 21), and the fold maps the ordinal onto a Sephirah
(1-10) and a Path (11-32).
"""

from fastapi.testclient import TestClient

from app.engines.kabbalah import build_tree, compute_gematria


def test_tree_has_the_canonical_structure() -> None:
    tree = build_tree()
    assert tree.sephirah_count == 10
    assert len(tree.sephiroth) == 10
    assert tree.path_count == 22
    assert len(tree.paths) == 22
    assert len(tree.pillars) == 3
    assert len(tree.worlds) == 4


def test_sephiroth_are_numbered_one_to_ten() -> None:
    tree = build_tree()
    assert [s.number for s in tree.sephiroth] == list(range(1, 11))
    assert tree.sephiroth[0].name_zh == "王冠"   # Kether
    assert tree.sephiroth[-1].name_zh == "王国"  # Malkuth
    assert len({s.id for s in tree.sephiroth}) == 10


def test_daath_is_the_hidden_node() -> None:
    tree = build_tree()
    assert tree.daath is not None
    assert tree.daath.number == 0
    assert tree.daath.is_hidden is True


def test_paths_run_eleven_to_thirty_two_and_join_distinct_spheres() -> None:
    tree = build_tree()
    assert sorted(p.number for p in tree.paths) == list(range(11, 33))
    first = next(p for p in tree.paths if p.number == 11)
    assert first.tarot == "The Fool"  # Golden Dawn path 11 = Alef
    for path in tree.paths:
        assert 1 <= path.from_sephirah <= 10
        assert 1 <= path.to_sephirah <= 10
        assert path.from_sephirah != path.to_sephirah
        assert path.letter_value > 0


def test_gematria_ordinal_arithmetic() -> None:
    assert compute_gematria("A").english_ordinal == 1
    assert compute_gematria("AB").english_ordinal == 3  # 1 + 2
    light = compute_gematria("LIGHT")
    assert light.normalized == "LIGHT"
    assert light.english_ordinal == 56    # 12+9+7+8+20
    assert light.english_reduction == 29  # 3+9+7+8+2
    assert light.digital_root == 2        # 5+6=11 → 1+1=2


def test_gematria_ignores_case_and_non_letters() -> None:
    assert compute_gematria("CHAI").english_ordinal == 21  # 3+8+1+9
    assert compute_gematria("chai").english_ordinal == 21
    assert compute_gematria("c h a i").english_ordinal == 21


def test_gematria_folds_onto_the_tree() -> None:
    reading = compute_gematria("LIGHT")
    assert 1 <= reading.sephirah.number <= 10
    assert 11 <= reading.path.number <= 32
    assert reading.synthesis.strip()


def test_tree_endpoint(client: TestClient) -> None:
    response = client.get("/api/v1/kabbalah/tree")
    assert response.status_code == 200
    body = response.json()
    assert body["sephirah_count"] == 10
    assert body["path_count"] == 22
    assert len(body["sephiroth"]) == 10
    assert len(body["paths"]) == 22


def test_gematria_endpoint(client: TestClient) -> None:
    response = client.post("/api/v1/kabbalah/gematria", json={"text": "LIGHT"})
    assert response.status_code == 200
    body = response.json()
    assert body["english_ordinal"] == 56
    assert body["digital_root"] == 2


def test_gematria_rejects_text_without_latin_letters(client: TestClient) -> None:
    response = client.post("/api/v1/kabbalah/gematria", json={"text": "12345"})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "gematria_no_latin_letters"
