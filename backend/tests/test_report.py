"""报告产品线（R1/R2/R3）对拍测试：契约形状、确定性、验签、错误信封。

全部直调真实引擎链（TestClient → API → composer → compute_*），不引入任何 mock
（AGENTS.md 第 9 条）。样例与 `test_bazi_hehun.py` 同一批出生数据，保证盘面事实
与既有对拍一致。
"""

from datetime import date, datetime, timedelta, time, timezone

from fastapi.testclient import TestClient

from app.core.report_orders import sign_token, verify_token
from app.main import app
from app.schemas.bazi import BaziNatalRequest
from app.schemas.bazi_hehun import BaziHehunRequest, HehunProfile
from app.schemas.bazi_transit import BaziTransitRequest

client = TestClient(app)


def _hehun_request() -> BaziHehunRequest:
    return BaziHehunRequest(
        male=HehunProfile(birth_date=date(1988, 2, 15), birth_time=time(23, 30), city="成都"),
        female=HehunProfile(birth_date=date(1990, 6, 15), birth_time=time(10, 0), city="北京"),
        reference_date=date(2026, 10, 1),
    )


def _natal_request() -> BaziNatalRequest:
    return BaziNatalRequest(
        birth_date=date(1988, 2, 15),
        birth_time=time(23, 30),
        city="成都",
        gender="male",
        reference_date=date(2026, 10, 1),
    )


def _transit_request() -> BaziTransitRequest:
    return BaziTransitRequest(
        **_natal_request().model_dump(mode="json"),
        start_year=2026,
        end_year=2027,
        focus_year=2026,
    )


def test_r1_preview_and_generate_shape() -> None:
    """R1：预览子集字段齐、完整报告九章序固定、证据卡与边界声明在场。"""
    preview = client.post("/api/v1/report/r1/preview", json=_hehun_request().model_dump(mode="json"))
    assert preview.status_code == 200, preview.text
    p = preview.json()
    assert p["product"] == "r1"
    assert p["section_count"] == 9
    assert len(p["summary"]) >= 4
    assert len(p["key_points"]) >= 2

    doc = client.post("/api/v1/report/r1/generate", json=_hehun_request().model_dump(mode="json"))
    assert doc.status_code == 200, doc.text
    d = doc.json()
    ids = [s["id"] for s in d["sections"]]
    assert ids == [
        "summary", "needs", "complement", "conflict", "scripts",
        "windows", "agreement", "evidence", "boundary",
    ]
    assert d["boundary"] == d["sections"][-1]["body"][0]
    assert d["sections"][0]["evidence_cards"], "摘要章至少一张证据卡"
    assert d["expires_at"] > d["generated_date"]


def test_r2_generate_shape() -> None:
    """R2：十一章序固定，实验章三条可执行条目；新章含格局/六维/大运事实。"""
    doc = client.post("/api/v1/report/r2/generate", json=_natal_request().model_dump(mode="json"))
    assert doc.status_code == 200, doc.text
    d = doc.json()
    ids = [s["id"] for s in d["sections"]]
    assert ids == [
        "summary", "profile", "dimensions", "driver", "stress", "energy",
        "dayun", "relationships", "experiments", "evidence", "boundary",
    ]
    experiments = next(s for s in d["sections"] if s["id"] == "experiments")
    assert len(experiments["bullets"]) == 3
    assert all("30天" in b or "实验" in b for b in experiments["bullets"])
    # 模板占位符 `{area}` 必须由装配器填掉（2026-10-23 走查发现 R2 实验章残留原文）。
    assert all("{" not in b and "}" not in b for b in experiments["bullets"])

    profile = next(s for s in d["sections"] if s["id"] == "profile")
    profile_text = " ".join(profile["body"])
    assert "格局" in profile_text
    assert "喜" in profile_text and "忌" in profile_text

    dimensions = next(s for s in d["sections"] if s["id"] == "dimensions")
    dim_heads = [b for b in dimensions["bullets"] if "（" in b and "分）" in b]
    assert len(dim_heads) == 6, "六维各一条档位/分条"

    dayun = next(s for s in d["sections"] if s["id"] == "dayun")
    assert dayun["body"], "大运章至少有一段（无当前运时给兜底句）"


def test_no_unfilled_template_placeholders() -> None:
    """防回归：三份报告的正文/要点/证据卡都不许残留 `{...}` 占位符。"""
    cases = [
        ("r1", _hehun_request().model_dump(mode="json")),
        ("r2", _natal_request().model_dump(mode="json")),
        ("r3", _transit_request().model_dump(mode="json")),
    ]
    for product, payload in cases:
        d = client.post(f"/api/v1/report/{product}/generate", json=payload)
        assert d.status_code == 200, d.text
        for section in d.json()["sections"]:
            joined = " ".join(section["body"]) + " ".join(section["bullets"])
            for card in section["evidence_cards"]:
                joined += card["claim"] + card["chart_fact"] + card["falsifier"]
            assert "{" not in joined and "}" not in joined, (
                f"{product}/{section['id']} 残留模板占位符"
            )


def test_r3_generate_shape() -> None:
    """R3：七章序固定，聚焦年十二节气流月齐，行动清单每窗口一条。"""
    doc = client.post("/api/v1/report/r3/generate", json=_transit_request().model_dump(mode="json"))
    assert doc.status_code == 200, doc.text
    d = doc.json()
    ids = [s["id"] for s in d["sections"]]
    assert ids == ["summary", "months", "windows", "actions", "review", "evidence", "boundary"]
    months = next(s for s in d["sections"] if s["id"] == "months")
    assert len(months["bullets"]) == 12
    actions = next(s for s in d["sections"] if s["id"] == "actions")
    assert 1 <= len(actions["bullets"]) <= 12


def test_same_input_yields_same_order_id_and_sections() -> None:
    """确定性：同一输入两次生成，订单号/版本/章节逐字一致（AGENTS.md 第 9 条）。"""
    payload = _hehun_request().model_dump(mode="json")
    r1 = client.post("/api/v1/report/r1/generate", json=payload).json()
    r2 = client.post("/api/v1/report/r1/generate", json=payload).json()
    assert r1["order_id"] == r2["order_id"]
    assert r1["version"] == r2["version"]
    assert r1["sections"] == r2["sections"]


def test_preview_is_subset_of_full_summary() -> None:
    """预览的关键结论就是完整报告摘要条的头部子集，不另造口径。"""
    payload = _natal_request().model_dump(mode="json")
    p = client.post("/api/v1/report/r2/preview", json=payload).json()
    d = client.post("/api/v1/report/r2/generate", json=payload).json()
    summary = next(s for s in d["sections"] if s["id"] == "summary")
    assert p["key_points"] == summary["bullets"][: len(p["key_points"])]


def test_fetch_roundtrip_and_signature_checks() -> None:
    """签名链接：验签 + 输入匹配后重算一致；错令牌/错订单 404。"""
    payload = _hehun_request().model_dump(mode="json")
    d = client.post("/api/v1/report/r1/generate", json=payload).json()
    order_id, token = d["order_id"], d["token"]

    fetched = client.post(f"/api/v1/report/r1/{order_id}?token={token}", json=payload)
    assert fetched.status_code == 200, fetched.text
    assert fetched.json()["order_id"] == order_id
    assert fetched.json()["sections"] == d["sections"]

    bad_token = client.post(f"/api/v1/report/r1/{order_id}?token=forged", json=payload)
    assert bad_token.status_code == 404

    bad_order = client.post(f"/api/v1/report/r1/0000000000000000?token={token}", json=payload)
    assert bad_order.status_code == 404


def test_verify_token_rejects_forged_and_expired() -> None:
    """core 层：伪造令牌与过期令牌都必须验签失败（恒定时间比较，防时序侧信道）。"""
    secret, order = "test-secret", "0123456789abcdef"
    created = datetime.now(timezone.utc) - timedelta(hours=1)
    good = sign_token(secret, "r1", order, created)
    assert verify_token(secret, "r1", order, good, ttl_hours=24)

    forged = good[:-1] + ("0" if good[-1] != "0" else "1")
    assert not verify_token(secret, "r1", order, forged, ttl_hours=24)
    assert not verify_token("other-secret", "r1", order, good, ttl_hours=24)

    expired = sign_token(secret, "r1", order, datetime.now(timezone.utc) - timedelta(days=2))
    assert not verify_token(secret, "r1", order, expired, ttl_hours=24)


def test_r3_out_of_range_returns_domain_error_envelope() -> None:
    """区间早于命盘大运：走引擎的 `TransitRangeError`，机器码信封（422，非 pydantic 400）。"""
    req = _transit_request().model_dump(mode="json")
    req["start_year"], req["end_year"], req["focus_year"] = 1900, 1901, 1900
    resp = client.post("/api/v1/report/r3/generate", json=req)
    assert resp.status_code == 422
    assert resp.json()["error"]["code"].startswith("transit_range")
