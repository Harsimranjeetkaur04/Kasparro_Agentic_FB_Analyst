# 🚀 Agentic Facebook Ads Performance Analyst

A Multi-Agent Autonomous System for Diagnosing ROAS/CTR Trends and Generating Creative Improvements

## 📌 Overview

This project implements a multi-agent autonomous analysis system that diagnoses Facebook Ads performance, explains why ROAS fluctuated, and generates new creative ideas for under-performing campaigns.

It was built as a placement-ready submission for the Kasparro Applied AI Engineer – Agentic Marketing Analyst assignment.

The system is fully modular, fully local (LLMs optional), and provides end-to-end analytics:

- Clean & canonicalize noisy Facebook Ads campaign data
- Aggregate and interpret ROAS/CTR trends
- Generate hypotheses about performance shifts
- Validate them using quantitative metrics
- Suggest new creatives grounded in existing messaging

## 🎯 Problem Statement

📌 "Build a multi-agent system that diagnoses Facebook Ads performance, explains reasons behind ROAS changes, identifies performance drivers such as audience fatigue or creative underperformance, and recommends new creative directions grounded in the dataset’s messaging."

The system must include 5 agents:

- **Planner Agent** – decomposes user query
- **Data Agent** – loads and summarizes data
- **Insight Agent** – generates hypotheses
- **Evaluator Agent** – tests hypotheses
- **Creative Generator** – proposes new creative direction

All prompts must:
- Follow layered prompting (Think → Analyze → Conclude)
- Enforce JSON schemas
- Use reflection / retry logic
- Operate without passing the full CSV (summaries only)

## 🧠 Architecture Diagram (Agentic Flow)

```text
           ┌────────────────┐
           │  User Query    │
           └───────┬────────┘
                   │
                   ▼
           ┌────────────────┐
           │  PlannerAgent  │
           │ (task builder) │
           └───────┬────────┘
  ┌─────────────────┼───────────────────┐
  ▼                 ▼                   ▼
┌─────────┐   ┌────────────┐     ┌──────────────┐
│DataAgent│→→→│InsightAgent│→→→→│EvaluatorAgent│
└────┬────┘   └────┬───────┘     └──────┬───────┘
     │             │                    │
     ▼             ▼                    ▼
                 ┌───────────────────────────────┐
                 │   CreativeGenerator (CTR Fix) │
                 └──────────────┬────────────────┘
                                ▼
                         Final Reports
```
## 🧩 Agents & Responsibilities

| Agent | Purpose | Input | Output |
| :--- | :--- | :--- | :--- |
| **PlannerAgent** | Decompose query → task list | user query | ordered tasks |
| **DataAgent** | Load CSV, clean, aggregate metrics, canonicalize campaigns | dataset | summary object |
| **InsightAgent** | Generate hypotheses | summary | hypotheses list |
| **EvaluatorAgent** | Validate hypotheses | hypotheses + summary | evaluations |
| **CreativeGenerator** | Generate creatives for low-CTR campaigns | summary | creatives list |

Each agent has its own prompt file inside `src/prompts/*.md`.

## 📂 Dataset Description

The dataset contains synthetic Facebook Ads data with the following fields:

* `campaign_name`, `adset_name`, `date`
* `spend`, `impressions`, `clicks`, `ctr`
* `purchases`, `revenue`, `roas`
* `creative_type`, `creative_message`
* `audience_type`, `platform`, `country`

The **DataAgent** performs:
* Missing-value handling
* Lowercasing and standardization
* Fuzzy canonicalization of campaign names
### 📦 Features Implemented
✔ Multi-agent pipeline with JSON schemas
✔ Layered prompt design (Think → Analyze → Conclude)
✔ Reflection & retry logic in prompts
✔ Fuzzy campaign name normalization
✔ Low-CTR campaign identification
✔ Fully grounded creative generation (no hallucination)
✔ Quantitative ROAS/CTR evaluation
✔ Complete report generation
✔ Test suite (pytest)
✔ CI automation via GitHub Actions
✔ Makefile for easy CLI usage
✔ demo.sh script for quick runs

**Summary computation includes:**
* Global metrics
* Daily trends
* Canonical campaign aggregates
* Low-CTR detection
* Creative message clustering

## ⚙️ Configuration

Configuration is handled in `config/config.yaml`.

**Example:**
```yaml
data_csv: "data/synthetic_fb_ads_undergarments.csv"
use_llm: false
similarity_threshold: 0.78
confidence_min: 0.6
```
* **`use_llm`**: Enable/disable LLM rewriting of creatives.
* **`similarity_threshold`**: Fuzzy grouping threshold for campaign canonicalization.
* **`confidence_min`**: Minimum confidence score required for validated hypotheses.
## 🏁 Quick Start (Local)
Create & activate virtual environment:
```bash
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows (Git Bash)
.venv/Scripts/activate
```
### Install dependencies:
```bash
pip install -r requirements.txt
```
### Run the analysis pipeline:
```bash
python src/run.py "Analyze ROAS drop in last 7 days"
```
### Using Makefile:
```bash
make run QUERY="Analyze ROAS drop in last 7 days"
```
### Using demo script:
```bash
chmod +x demo.sh
./demo.sh "Analyze ROAS drop in last 7 days"
```
### Check the outputs:
| File | Description |
| :--- | :--- |
| `reports/insights.json` | Validated hypotheses + summary |
| `reports/creatives.json` | Creative recommendations |
| `reports/report.md` | Clean human-readable report |

### 📑 Prompt Design Philosophy
All prompt files follow the required layered format:
1. Think
Explain reasoning steps internally.
2. Analyze
Transform reasoning into structured actions.
3. Conclude
Output strict JSON according to a schema.
4. Retry Logic
If low-confidence or missing data:
 - refine hypothesis
 - lower similarity threshold
 - default to last 7 days
 - fallback to templates (in creative generator)
 - abort safely if needed

### 🧪Testing
Run unit tests:

```bash
pytest -q
```
## Current test coverage includes:
* DataAgent functionality
* CreativeGenerator output format
* Hypothesis–evaluation merging logic

### 🤖 CI/CD (GitHub Actions)
A full CI pipeline runs automatically on each push/pull request to main.
## Workflow file: .github/workflows/ci.yml
It performs:
* Python setup
* Dependency installation
* pytest -q
* Uploads reports/ as artifacts

### 🧪 Example Output
## Example validated insight:

```JSON

{
  "statement": "ROAS decreased due to CTR drop in the last 7 days.",
  "confidence": 0.82,
  "reasoning": "CTR consistently trended downward while spend remained stable."
}
```
## Example creative recommendation:

```JSON
{
  "headline": "Experience Invisible Comfort",
  "message": "Smooth, breathable fabric for all-day support.",
  "cta": "Shop Now"
}
```

### 🏗 Project Folder Structure
```text
.
Kasparro_Agentic_FB_Analyst/
│
├── src/
│   ├── agents/
│   │   ├── planner.py
│   │   ├── data_agent.py
│   │   ├── insight_agent.py
│   │   ├── evaluator.py
│   │   └── creative_generator.py
│   │
│   ├── prompts/
│   │   ├── planner.md
│   │   ├── data_agent.md
│   │   ├── insight_agent.md
│   │   ├── evaluator.md
│   │   └── creative_generator.md
│   │
│   ├── run.py
│   └── utils/
│       ├── io.py
│       ├── logger.py
│       └── metrics.py
│
├── data/
│   └── synthetic_fb_ads_undergarments.csv
│
├── reports/          # auto-generated
├── logs/             # auto-generated
├── tests/
├── .github/workflows/ci.yml
├── demo.sh
├── Makefile
└── README.md
```
### Developer Utilities
#### Run with Makefile:
```bash
make setup
make run QUERY="Analyze ROAS change"
make test
make clean
```

## 📝 Submission Notes (for Recruiters)

This repository includes every deliverable required by the assignment:

* ✔ Multi-agent architecture
* ✔ Prompt files (layered, structured, JSON schemas)
* ✔ Hypothesis generation + quantitative evaluation
* ✔ Creative generation grounded in dataset messaging
* ✔ CI/CD automation
* ✔ Reproducibility (Makefile, config, seeds)
* ✔ Tests for core components
* ✔ Reports + logs

### 🚀 Future Improvements

* Add LLM-based rewrite stage with JSON validation

* Add time-series anomaly detection

* Add creative clustering using embeddings

* Build UI dashboard

* Add per-campaign uplift simulation

## 🙋 Contact

**Harsimranjeet Kaur**

* **GitHub:** [https://github.com/Harsimranjeetkaur04](https://github.com/Harsimranjeetkaur04)
* **Email:** [ssimrankaur515@gmail.com]

---

**🎉 Final Note**
This project was built with production-style structure, modularity, and clean engineering practices to match the expectations of the Kasparro Applied AI Engineering assignment.


