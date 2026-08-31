"""Shared fixtures and CLI helpers for the split validate_run test suite.

pipelines/validate_run.py's regression suite outgrew one file (CodeScene:
low cohesion across ~70 functions, 723+ lines) and is now split by
responsibility across test_validate_run_cli.py, test_validate_run_invariants.py,
test_validate_run_spikes.py, and test_validate_run_contracts.py. This module
holds only what two or more of those files need in common.
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"
VALIDATE = PIPELINES / "validate_run.py"

if str(PIPELINES) not in sys.path:
    sys.path.insert(0, str(PIPELINES))

# Minimal record that passes the thalamic shape check (required keys + decision).
# Includes strict fields: meta.round and valid provenance/state.
TINY_THALAMIC = {
    "state": {"episode_id": "tiny-001", "sim_or_real": "designed"},
    "proposed_action": {"action_type": "noop"},
    "safety_decision": {"decision": "ACCEPT", "rationale": "test fixture"},
    "executed_action": {"action_type": "noop"},
    "future_outcome": {"success": "full"},
    "reward_components": {"total": 0.0},
    "meta": {"round": 1},
    "provenance": {"kind": "designed", "claimed": "designed"},
}

EXPECTED_TOTALS = {
    "files": 1,
    "records": 1,
    "by_kind": {"thalamic": 1},
    "error_count": 0,
}


def _tiny_run_dir(tmp: Path) -> Path:
    run_dir = tmp / "run"
    run_dir.mkdir()
    (run_dir / "tiny.jsonl").write_text(json.dumps(TINY_THALAMIC) + "\n")
    return run_dir


def _invoke(*args):
    return subprocess.run(
        [sys.executable, str(VALIDATE), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def _run_with_record(record):
    """Helper: write single record to temp dir and invoke validator."""
    with tempfile.TemporaryDirectory() as raw:
        run_dir = Path(raw) / "run"
        run_dir.mkdir()
        (run_dir / "case.jsonl").write_text(json.dumps(record) + "\n")
        result = _invoke(str(run_dir))
        return result
