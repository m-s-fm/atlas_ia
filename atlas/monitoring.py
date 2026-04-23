"""Traces JSONL. Une fonction, un fichier."""
import json
from datetime import datetime, timezone
from pathlib import Path


def log_trace(log_path: str = "./logs/traces.jsonl", **fields) -> None:
    """Écrit une trace JSON dans un fichier."""
    Path(log_path).parent.mkdir(parents=True, exist_ok=True)
    record = {"timestamp": datetime.now(timezone.utc).isoformat(), **fields}
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")