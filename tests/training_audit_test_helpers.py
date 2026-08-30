"""Shared fixtures for the split training_audit test suite.

pipelines/training_audit.py's regression suite outgrew one file (CodeScene:
low cohesion across ~36 functions, threshold 4) and is now split by
responsibility across test_training_audit_bridge.py,
test_training_audit_readiness.py, test_training_audit_preferences.py,
test_training_audit_agentic.py, and test_training_audit_curated_views.py.
This module holds what two or more of those files need in common.
"""

import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

if str(REPO / "pipelines") not in sys.path:
    sys.path.insert(0, str(REPO / "pipelines"))


def distillation_sidecars(decision="ACCEPT"):
    """Return independent copies of the committed raster and gate fixtures."""
    record = json.loads(
        (REPO / "tests" / "fixtures" / "bridge_gate_snn.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()[0]
    )
    sidecars = {
        "raster": record["raster"],
        "gate_snn": dict(record["gate_snn"]),
    }
    sidecars["gate_snn"]["decision"] = decision
    return sidecars


def thalamic(record_id, provenance="designed", decision="ACCEPT"):
    record = {
        "id": record_id,
        "state": {"sim_or_real": provenance, "domain": "audit-test"},
        "proposed_action": {"action": "noop", "decision_basis": "fixture"},
        "safety_decision": {"decision": decision, "rationale": "bounded fixture"},
        "executed_action": {"action": "noop"},
        "future_outcome": {"success": True},
        "reward_components": {"task_progress": 0.5, "safety": 0.5, "total": 1.0},
        "meta": {"tags": ["audit", "fixture"], "round": 1},
    }
    record.update(distillation_sidecars(decision=decision))
    return record


def gate_snn_bridge(record_id="raster-bridge-1"):
    """Return the committed raster + third-factor + gate-as-SNN record."""
    record = json.loads(
        (REPO / "tests" / "fixtures" / "bridge_gate_snn.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()[0]
    )
    record["id"] = record_id
    return record


def write(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(record) + "\n" for record in records))


def commit_marker_batch(factory: Path, batch: Path):
    """Put ``batch`` behind a valid marker-mode completion point."""
    (factory / ".round-marker-mode.json").write_text(
        '{"version":1,"legacy_baseline":0,"commit_point":"ROUND-rNN.complete.json"}\n'
    )
    notes = factory / "NOTES-r01.md"
    notes.write_text("Novel coverage: fixture\n")
    (factory / "ROUND-r01.complete.json").write_text(
        json.dumps(
            {
                "version": 1,
                "factory": factory.name,
                "round": 1,
                "records": 1,
                "expected_records": 1,
                "commit_point": "ROUND-r01.complete.json",
                "files": [
                    {
                        "name": batch.name,
                        "sha256": hashlib.sha256(batch.read_bytes()).hexdigest(),
                    },
                    {
                        "name": notes.name,
                        "sha256": hashlib.sha256(notes.read_bytes()).hexdigest(),
                    },
                ],
            }
        )
        + "\n"
    )


def episode_preference(record_id, *, pair_goal=None, chosen_goal=None, rejected_goal=None):
    def side(goal):
        record = {
            "steps": [
                {
                    "decision_basis": "fixture observation",
                    "tool_call": {"name": "inspect", "args": {}},
                    "observation": "fixture result",
                }
            ],
            "outcome": "fixture complete",
            "reward": {"success": True},
        }
        if goal is not None:
            record["goal"] = goal
        return record

    record = {
        "id": record_id,
        "chosen": side(chosen_goal),
        "rejected": side(rejected_goal),
        "critique": "chosen path is safer",
        "reward": {"success": True},
    }
    if pair_goal is not None:
        record["goal"] = pair_goal
    return record
