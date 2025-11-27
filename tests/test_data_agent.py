# tests/test_data_agent.py
import json
from agents.data_agent import DataAgent

def test_data_agent_runs_and_has_payload():
    cfg = {"data_csv": "data/sample_fb_ads.csv"}
    agent = DataAgent(cfg)
    out = agent.run({})
    assert out["status"] == "ok"
    payload = out["payload"]
    # basic keys
    assert "global" in payload
    assert "trend" in payload
    assert "campaign_summaries" in payload
    assert "low_ctr_campaigns" in payload
    # low_ctr should be a list
    assert isinstance(payload["low_ctr_campaigns"], list)
