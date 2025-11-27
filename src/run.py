import sys
import os

from utils.io import load_config, write_json
from utils.logger import log_agent

# Import agents
from agents.planner import PlannerAgent
from agents.data_agent import DataAgent
from agents.insight_agent import InsightAgent
from agents.evaluator import EvaluatorAgent
from agents.creative_generator import CreativeGenerator


def run_pipeline(user_query: str) -> None:
    """
    Executes the full multi-agent analysis pipeline.
    """
    config = load_config()
    log_agent("run", f"Starting pipeline for query: '{user_query}'")

    # Initialize agents
    planner = PlannerAgent(config)
    data_agent = DataAgent(config)
    insight_agent = InsightAgent(config)
    evaluator = EvaluatorAgent(config)
    creative_gen = CreativeGenerator(config)

    # -------------------------
    # Step 1: Planner decides workflow
    # -------------------------
    plan_out = planner.run({"query": user_query})
    tasks = plan_out.get("tasks", [])

    if plan_out.get("status") != "ok" or not tasks:
        log_agent("run", "Planner could not generate tasks.")
        sys.exit(1)

    # Data storage for agent outputs
    context = {}

    # -------------------------
    # Step 2: Execute tasks in order
    # -------------------------
    for task in sorted(tasks, key=lambda x: x["priority"]):
        agent_name = task["agent"]
        params = task.get("params", {})

        log_agent("run", f"Executing task: {task['task_id']} with agent {agent_name}")

        if agent_name == "data_agent":
            out = data_agent.run(params)
            context["summary"] = out.get("payload", {})

        elif agent_name == "insight_agent":
            out = insight_agent.run({"summary": context.get("summary", {})})
            context["hypotheses"] = out.get("payload", {}).get("hypotheses", [])

        elif agent_name == "evaluator":
            out = evaluator.run(
                {
                    "hypotheses": context.get("hypotheses", []),
                    "summary": context.get("summary", {}),
                }
            )
            context["evaluations"] = out.get("payload", {}).get("evaluations", [])

        elif agent_name == "creative_generator":
            out = creative_gen.run({"summary": context.get("summary", {})})
            context["creatives"] = out.get("payload", {}).get("creatives", [])

        else:
            log_agent("run", f"Unknown agent: {agent_name}")

    # -------------------------
    # Step 3: Save reports (Hardened merge)
    # -------------------------
    os.makedirs("reports", exist_ok=True)

    validated_insights = []

    hypotheses = context.get("hypotheses", []) or []
    evaluations = context.get("evaluations", []) or []

    # Build an index of evaluations by id if available
    eval_by_id = {}
    for ev in evaluations:
        if isinstance(ev, dict) and ev.get("id"):
            eval_by_id[ev["id"]] = ev

    min_confidence = float(config.get("confidence_min", 0.6))

    for i, hyp in enumerate(hypotheses):
        # try id matching first
        matching_eval = None
        if isinstance(hyp, dict) and hyp.get("id") and hyp["id"] in eval_by_id:
            matching_eval = eval_by_id[hyp["id"]]
        else:
            # fallback to index-based matching
            matching_eval = evaluations[i] if i < len(evaluations) else {}

        # defensive extraction of confidence (support multiple key names)
        confidence_score = 0.0
        if isinstance(matching_eval, dict):
            confidence_score = matching_eval.get(
                "confidence",
                matching_eval.get(
                    "score",
                    matching_eval.get("conf", 0.0),
                ),
            )
            try:
                confidence_score = float(confidence_score)
            except Exception:
                confidence_score = 0.0

        # Accept only items above threshold
        stmt = hyp.get("statement") if isinstance(hyp, dict) else str(hyp)
        if confidence_score >= min_confidence:
            validated_insights.append(
                {
                    "hypothesis": hyp,
                    "evaluation": matching_eval,
                }
            )
        else:
            log_agent(
                "run",
                f"Dropping low-confidence insight: {stmt} ({confidence_score})",
            )

    # Write cleaned insights (include raw for debugging)
    write_json(
        "reports/insights.json",
        {
            "query": user_query,
            "summary": context.get("summary", {}),
            "validated_insights": validated_insights,
            "all_raw_hypotheses": hypotheses,
            "all_raw_evaluations": evaluations,
        },
    )

    write_json(
        "reports/creatives.json",
        {
            "query": user_query,
            "creatives": context.get("creatives", []),
        },
    )

    # Human-readable markdown report (validated only)
    with open("reports/report.md", "w", encoding="utf-8") as f:
        f.write("# Facebook Ads Analysis\n\n")
        f.write(f"### Query: {user_query}\n\n")
        f.write("## Key Insights (Validated)\n\n")
        if not validated_insights:
            f.write("No high-confidence insights found.\n\n")
        for item in validated_insights:
            hyp = item.get("hypothesis", {}) or {}
            ev = item.get("evaluation", {}) or {}
            statement = hyp.get("statement", "<no statement>")
            reasoning = hyp.get(
                "reasoning",
                hyp.get("explanation", "<no reasoning provided>"),
            )
            conf = ev.get("confidence", ev.get("score", "N/A"))
            f.write(f"- **{statement}**\n")
            f.write(f"  - *Reasoning:* {reasoning}\n")
            f.write(
                f"  - *Confidence:* {conf} (Validated by Evaluator)\n\n"
            )

    log_agent("run", "Pipeline completed successfully.")
    print("Analysis complete. Reports generated in /reports.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python src/run.py \"<analysis query>\"")
        sys.exit(1)

    query = " ".join(sys.argv[1:])
    run_pipeline(query)
