# src/agents/agent_base.py

from typing import Dict, Any

class AgentBase:
    """
    Base class for all agents.
    Ensures every agent has a consistent interface.
    """

    def __init__(self, config: Dict):
        self.config = config

    def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Must be implemented by each agent.

        Expected return format:
        {
            "status": "ok" / "error",
            "payload": ...,
            "confidence": float,
            "error": optional
        }
        """
        raise NotImplementedError("Each agent must implement run().")
