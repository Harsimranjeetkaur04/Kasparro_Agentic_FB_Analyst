# tests/test_report_merge.py
import os
import json
from types import SimpleNamespace
import builtins

# We'll import the function indirectly by simulating the context used in run.py.
# Since run.py is script-like, testing the exact run requires some wiring.
# Instead, we'll test the merging logic directly by replicating the core merge snippet.

from agents.data_agent import DataAgent  # use to get a config path if needed

def merge_hypotheses_and_evals(hypotheses, evaluations, min_confidence=0.6):
    # replicate logic from run.py snippet
    validated = []
    eval_by_id = {ev["id"]: ev for ev in evaluations if isinstance(ev, dict) and ev.get("id")}
    for i, hyp in enumerate(hypotheses):
        matching_eval = None
        if isinstance(hyp, dict) and hyp.get("id") and hyp["id"] in eval_by_id:
            matching_eval = eval_by_id[hyp["id"]]
        else:
            matching_eval = evaluations[i] if i < len(evaluations) else {}

        conf = 0.0
        if isinstance(matching_eval, dict):
            conf = matching_eval.get("confidence",
                   matching_eval.get("score",
                   matching_eval.get("conf", 0.0)))
            try:
                conf = float(conf)
            except:
                conf = 0.0

        if conf >= min_confidence:
            validated.append({"hypothesis": hyp, "evaluation": matching_eval})
    return validated

def test_merge_by_id_and_index_and_threshold():
    hypotheses = [
        {"id": "H1", "statement": "A"},
        {"id": "H2", "statement": "B"},
        {"id": "H3", "statement": "C"}
    ]
    # evaluation order swapped: H2 is first, but includes id mapping;
    evaluations = [
        {"id": "H2", "confidence": 0.7},
        {"id": "H1", "confidence": 0.3},  # below threshold
        {"confidence": 0.8}  # no id, should match index 2 -> H3
    ]

    validated = merge_hypotheses_and_evals(hypotheses, evaluations, min_confidence=0.6)
    # expected: H2 matched by id (0.7 >= 0.6) and H3 matched by index (0.8 >= 0.6) -> 2 validated
    ids = [v["hypothesis"]["id"] for v in validated]
    assert set(ids) == {"H2", "H3"}
