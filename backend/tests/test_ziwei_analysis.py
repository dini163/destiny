from fastapi.testclient import TestClient
from app.main import app
from app.content.bazi_zangfu import get_bazi_zangfu_guidance
from app.content.zhouyi_yangzhai import get_yangzhai_hexagram_meaning

client = TestClient(app)

def test_ziwei_analysis_api_all_topics():
    payload = {
        "birth_date": "1984-01-01",
        "birth_time": "00:00",
        "calendar": "solar",
        "longitude": 120.0,
        "gender": "male",
        "apply_true_solar_time": False,
    }
    res = client.post("/api/v1/ziwei/analysis", json=payload)
    assert res.status_code == 200, res.text
    data = res.json()
    assert "chart" in data
    assert "analysis" in data
    analysis = data["analysis"]
    assert len(analysis) == 13
    for topic in (
        "mingGong", "personality", "fuQi", "guanLu", "caiBo", "jiE",
        "xiongDi", "ziNv", "qianYi", "jiaoYou", "tianZhai", "fuDe", "fuMu"
    ):
        assert topic in analysis
        assert len(analysis[topic]) > 200
        # Check standard sections
        assert "【一句话定调】" in analysis[topic]
        assert "【核心论断】" in analysis[topic]
        assert "【命盘依据】" in analysis[topic]
        assert "【经典出处】" in analysis[topic]


def test_ziwei_analysis_api_single_topic():
    payload = {
        "birth_date": "1984-01-01",
        "birth_time": "00:00",
        "calendar": "solar",
        "longitude": 120.0,
        "gender": "male",
        "apply_true_solar_time": False,
        "topic": "fuQi",
    }
    res = client.post("/api/v1/ziwei/analysis", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert len(data["analysis"]) == 1
    assert "fuQi" in data["analysis"]


def test_bazi_zangfu_guidance():
    # Test clash e.g. 子 and 午
    res = get_bazi_zangfu_guidance(["子", "午", "寅", "卯"])
    assert len(res) >= 1
    clash_item = next(r for r in res if r["type"] == "clash")
    assert "子午冲" in clash_item["label"]
    assert "胆" in clash_item["organs"]
    assert "心" in clash_item["organs"]
    assert "足少阳胆经" in clash_item["meridians"]

    # Test excess
    res2 = get_bazi_zangfu_guidance(["酉", "酉", "丑", "亥"])
    excess_item = next(r for r in res2 if r["type"] == "excess")
    assert "酉" in excess_item["label"]
    assert "肾" in excess_item["organs"]


def test_zhouyi_yangzhai_meaning():
    # Check 乾为天
    q = get_yangzhai_hexagram_meaning("乾为天")
    assert q is not None
    assert q["is_name_position_equal"] is True
    assert "西北方" in q["position_direction"]
    assert "父" in q["person_role"]

    # Check 雷天大壮 (长男居西北)
    dz = get_yangzhai_hexagram_meaning("雷天大壮")
    assert dz is not None
    assert dz["is_name_position_equal"] is False
    assert "长男" in dz["person_role"]
    assert "西北方" in dz["position_direction"]


def test_bazi_zangfu_api():
    res = client.post("/api/v1/bazi/zangfu", json={"branches": ["子", "午", "寅", "卯"]})
    assert res.status_code == 200, res.text
    data = res.json()
    assert "items" in data
    assert any("子午冲" in it["label"] for it in data["items"])


def test_zhouyi_yangzhai_api():
    res = client.post("/api/v1/zhouyi/yangzhai", json={"hexagram_name": "地天泰"})
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["hexagram_name"] == "地天泰"
    assert data["meaning"] is not None
    assert "母" in data["meaning"]["person_role"]
    assert "西北方" in data["meaning"]["position_direction"]
