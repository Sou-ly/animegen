import os
from pathlib import Path

import yaml


def _load_dotenv(path: str = ".env") -> None:
    env_path = Path(path)
    if not env_path.exists():
        return
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key not in os.environ:
                os.environ[key] = value


def load_config(path: str = "config.yaml") -> dict:
    _load_dotenv()

    with open(path) as f:
        cfg = yaml.safe_load(f)

    cfg["anthropic_api_key"] = os.environ.get("ANTHROPIC_API_KEY", "")
    cfg["fal_api_key"] = os.environ.get("FAL_KEY", "")

    return cfg
