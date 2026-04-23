"""Tests unitaires du monitoring JSONL (Sprint 3)."""
import json
from pathlib import Path

from atlas.monitoring import log_trace


def test_log_trace_ecrit_json_valide(tmp_path):
    log_file = tmp_path / "traces.jsonl"
    log_trace(str(log_file), session_id="test", model="test-model", latency_ms=123)

    content = log_file.read_text(encoding="utf-8").strip()
    record = json.loads(content)

    assert "timestamp" in record
    assert record["session_id"] == "test"
    assert record["model"] == "test-model"
    assert record["latency_ms"] == 123


def test_log_trace_append_plusieurs_lignes(tmp_path):
    log_file = tmp_path / "traces.jsonl"
    log_trace(str(log_file), event="first")
    log_trace(str(log_file), event="second")

    lines = log_file.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 2
    assert json.loads(lines[0])["event"] == "first"
    assert json.loads(lines[1])["event"] == "second"