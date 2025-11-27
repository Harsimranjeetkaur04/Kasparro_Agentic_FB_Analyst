# src/utils/logger.py

from loguru import logger
import os

# Ensure logs folder exists
os.makedirs("logs", exist_ok=True)

# Log file rotation: creates new file after 1 MB
logger.add("logs/agent.log", rotation="1 MB", enqueue=True)


def log_agent(agent_name: str, message: str):
    """
    Simple utility for agents to send structured logs.
    """
    logger.info(f"[{agent_name}] {message}")
