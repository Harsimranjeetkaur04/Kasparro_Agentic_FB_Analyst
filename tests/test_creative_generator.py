# tests/test_creative_generator.py
from agents.creative_generator import CreativeGenerator

def test_creative_generator_structure():
    cfg = {"data_csv": "data/sample_fb_ads.csv"}
    agent = CreativeGenerator(cfg)
    # summary only needs low_ctr_campaigns list; empty list falls back to global
    out = agent.run({"summary": {"low_ctr_campaigns": []}})
    assert out["status"] == "ok"
    payload = out["payload"]
    assert "creatives" in payload
    creatives = payload["creatives"]
    assert isinstance(creatives, list)
    # each creative entry must have campaign and generated list
    assert len(creatives) > 0
    first = creatives[0]
    assert "campaign" in first
    assert "generated" in first
    assert isinstance(first["generated"], list)
    assert len(first["generated"]) > 0
    g = first["generated"][0]
    assert "headline" in g and "message" in g and "cta" in g
