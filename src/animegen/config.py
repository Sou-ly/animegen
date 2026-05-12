import os
from pathlib import Path

import yaml


def load_config(path: str = "config.yaml") -> dict:
    with open(path) as f:
        cfg = yaml.safe_load(f)

    cfg["anthropic_api_key"] = os.environ.get("ANTHROPIC_API_KEY", "")
    cfg["fal_api_key"] = os.environ.get("FAL_KEY", "")

    return cfg
