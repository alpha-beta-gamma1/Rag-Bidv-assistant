import os
from pathlib import Path

def ensure_directories(config: dict):
    """Create necessary directories if they don't exist."""
    for path in [config["data"]["raw"], config["data"]["processed"],
                 config["data"]["embeddings"], config["data"]["chunks"]]:
        Path(path).mkdir(parents=True, exist_ok=True)