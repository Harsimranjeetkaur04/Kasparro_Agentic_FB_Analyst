# SELF REVIEW — Kasparro Agentic FB Analyst

**Author:** Harsimranjeet Kaur  
**Repo:** kasparro-agentic-fb-analyst-harsimranjeet-kaur  
**Version:** v1.0

---

## 1) What the assignment asked
Build a multi-agent (Planner, Data, Insight, Evaluator, Creative) system that:
- Diagnoses why ROAS changed over time.
- Identifies drivers (audience fatigue, creative underperformance, spend shifts).
- Suggests new creative directions grounded in the dataset’s creative messages.
- Uses layered prompts (Think → Analyze → Conclude), JSON schemas, and retry/reflection logic.

---

## 2) What I built (summary)
- A modular pipeline: Planner → DataAgent → InsightAgent → Evaluator → CreativeGenerator.
- Data canonicalization (fuzzy merge) for noisy campaign names.
- DataAgent summarization: global metrics, daily trend, per-campaign aggregated summaries, low-CTR detection.
- InsightAgent: generates up to 6 data-grounded hypotheses with evidence requirements.
- EvaluatorAgent: computes numeric evidence (roas_change_pct, ctr_change_pct, etc.), returns validation & confidence.
- CreativeGenerator: produces 3–6 candidates per low-CTR campaign grounded in existing creative messages; optional LLM rewrite (disabled by default).
- Reports: `reports/insights.json`, `reports/creatives.json`, `reports/report.md`.
- CI: GitHub Actions runs tests; `Makefile` and `demo.sh` for easy reproducibility.
- Tests: unit tests for core components; `pytest` passes.

---

## 3) Key design choices & rationale
- **Agent decomposition** — keeps reasoning local to each agent; easier to test and to extend.
- **Summaries (not raw CSV)** — prevents LLMs (if enabled) from being overwhelmed and avoids leaking unnecessary data.
- **Fuzzy canonicalization** — addresses real-world noisy naming in ad accounts and reduces duplication across campaigns.
- **Schema-first prompts** — strict schemas make validation and automated testing straightforward.
- **Config-driven thresholds** — `config/config.yaml` controls similarity threshold and confidence thresholds for easy tuning.
- **Optional LLM** — LLM rewrite is optional and fails safely (fallback to templates).

---

## 4) Limitations & trade-offs
- Evaluator uses heuristic thresholds (10–20% rules) rather than full statistical testing — chosen for simplicity and interpretability.
- Creative generation is template + anchor-driven; an LLM could improve stylistic variety but increases external dependency and safety complexity.
- The current dataset is synthetic and small — results may differ on large, production datasets.

---

## 5) How to validate / what to look for
1. Run the pipeline:
   ```bash
   python src/run.py "Analyze ROAS drop in last 7 days"
  ```
2. Check reports/insights.json:

 * validated_insights contain hypothesis + evaluator confidence.

3. Check reports/creatives.json:

* Each low-CTR campaign has generated candidates rooted in anchor_examples.

4. Tests:
```bash
pytest -q
```
## 6) Reproducibility & command used for outputs

* config/config.yaml controls thresholds, seed, fuzzy matching, etc.

* The exact command used to generate all final reports:
```bash
  python src/run.py "Analyze ROAS drop in last 7 days"
```
* Commit hash for the outputs:
  - Replace this in your repo after running:
  ```bash
  git rev-parse --short HEAD
  ```
* Insert here:
<INSERT_COMMIT_HASH_HERE>

## 7) Evidence files required by the assignment

✔ reports/report.md
✔ reports/insights.json
✔ reports/creatives.json
✔ logs/agent.log
✔ src/prompts/*.md
✔ Unit tests (tests/)
✔ CI workflow (.github/workflows/ci.yml)

## 8) Possible future improvements
* Add LLM rewrite with strict JSON validator
* Add audience-level analysis & frequency capping detection
* Add causal uplift estimation
* Add Streamlit UI for interactive diagnosis
* Add campaign clustering via embeddings
  
### Thank you for reviewing this submission.