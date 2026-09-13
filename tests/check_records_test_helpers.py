"""Shared fixtures and CLI helpers for the split check_records test suite.

pipelines/check_records.py's regression suite outgrew one file (CodeScene:
low cohesion across ~40 functions, threshold 4) and is now split by
responsibility across test_check_records_rewards.py,
test_check_records_identity.py, test_check_records_cli.py, and
test_check_records_spikes.py. This module holds what two or more of those
files need in common.
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
CHECKER = PIPELINES / "check_records.py"

if str(PIPELINES) not in sys.path:
    sys.path.insert(0, str(PIPELINES))


def _thalamic(**overrides):
    rec = {
        "id": "t-001",
        "state": {"sim_or_real": "designed", "domain": "test"},
        "proposed_action": {"action_type": "noop"},
        "safety_decision": {"decision": "ACCEPT", "rationale": "ok"},
        "executed_action": {"action_type": "noop"},
        "future_outcome": {"success": "full"},
        "reward_components": {
            "task_progress": 0.4,
            "safety": 0.6,
            "total": 1.0,
        },
        "meta": {"id": "t-001", "round": 1},
    }
    rec.update(overrides)
    if "id" not in overrides and isinstance(overrides.get("meta"), dict):
        candidate = overrides["meta"].get("id")
        if isinstance(candidate, str):
            rec["id"] = candidate
    # meta.round is required at the shape layer; meta overrides here only
    # target identity, so backfill round unless a test sets it explicitly.
    if isinstance(rec.get("meta"), dict):
        rec["meta"].setdefault("round", 1)
    return rec


def _write_jsonl(path, records):
    path.write_text("".join(json.dumps(r) + "\n" for r in records))


def _run_dir(records, name="batch.jsonl"):
    tmp = tempfile.TemporaryDirectory()
    path = Path(tmp.name) / name
    _write_jsonl(path, records)
    return tmp, Path(tmp.name)


def _cli(args, cwd=None):
    return subprocess.run(
        [sys.executable, str(CHECKER), *args],
        cwd=str(cwd or REPO),
        capture_output=True,
        text=True,
    )
