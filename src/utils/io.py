# src/utils/io.py

import yaml
import pandas as pd
import json
import os


def load_config(path: str = "config/config.yaml"):
    """
    Loads YAML config file.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config file not found: {path}")

    with open(path, "r") as f:
        return yaml.safe_load(f)


def load_csv(path: str):
    """
    Loads a CSV and returns a pandas DataFrame.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"CSV file not found: {path}")

    return pd.read_csv(path)


def write_json(path: str, data):
    """
    Writes data as JSON to a given path.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, "w") as f:
        json.dump(data, f, indent=2)
