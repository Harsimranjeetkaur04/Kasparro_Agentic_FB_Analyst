from typing import Any, Dict

class AgentBase:
    def __init__(self, config: Dict):
        self.config = config

    def run(self, inputs: Dict) -> Dict:
        """
        Run agent task. Returns structured dict output.
        """
        raise NotImplementedError
