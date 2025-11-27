# src/agents/planner.py

from agents.agent_base import AgentBase
from utils.logger import log_agent


class PlannerAgent(AgentBase):
    """
    Planner Agent:
    - Takes the user query
    - Breaks it into tasks
    - Assigns each task to the right agent
    - Sets execution order (priority)
    """

    def run(self, inputs):
        query = inputs.get("query", "")
        log_agent("planner", f"Received query: {query}")

        # If user wants to analyze ROAS specifically
        is_roas_query = "roas" in query.lower()

        # Static but logical task flow
        tasks = []

        # Always load & summarize data first
        tasks.append({
            "task_id": "load_data",
            "agent": "data_agent",
            "priority": 1,
            "params": {}
        })

        # Always generate insights after loading data
        tasks.append({
            "task_id": "generate_insights",
            "agent": "insight_agent",
            "priority": 2,
            "params": {"focus": "roas" if is_roas_query else "general"}
        })

        # Always evaluate hypotheses
        tasks.append({
            "task_id": "evaluate_insights",
            "agent": "evaluator",
            "priority": 3,
            "params": {}
        })

        # Creative suggestions if CTR or creative performance involved
        tasks.append({
            "task_id": "generate_creatives",
            "agent": "creative_generator",
            "priority": 4,
            "params": {"filter": "low_ctr"}
        })

        log_agent("planner", "Plan created successfully")

        return {
            "status": "ok",
            "tasks": tasks,
            "confidence": 0.95
        }
