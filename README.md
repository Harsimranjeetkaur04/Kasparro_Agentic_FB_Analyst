# Agentic Facebook Ads Performance Analyst

**Goal:** Build a multi-agent system that diagnoses Facebook Ads performance (ROAS/CTR), explains drivers for performance changes, and generates creative suggestions grounded in the provided dataset.

This repo contains a placement-ready implementation with data cleaning, fuzzy canonicalization of campaign names, hypothesis generation, quantitative evaluation, and creative generation.

---

## Quick status

- Multi-agent pipeline: Planner → DataAgent → InsightAgent → Evaluator → CreativeGenerator  
- Data canonicalization & fuzzy merging of campaign names  
- Data-grounded creative generation (templated; optional LLM rewrite available)  
- JSON reports in `reports/` and human-friendly `reports/report.md`  
- Unit tests (`pytest`) and CI (`GitHub Actions`) configured

---

## Quick start (local)

1. Create & activate virtual environment:

```bash
python -m venv .venv
# macOS / Linux
source .venv/bin/activate
# Windows (Git Bash)
.venv/Scripts/activate
```

2. Install dependencies:
```bash
  pip install -r requirements.txt
```

3. Run the pipeline:
```bash
  python src/run.py "Analyze ROAS drop in last 7 days"
```

4. Run demo script:
```bash
  chmod +x demo.sh
  ./demo.sh "Analyze ROAS drop in last 7 days"
```

6. Run tests:
```bash
  pytest -q
```



