"""Shared fixtures for the split training_audit test suite.

pipelines/training_audit.py's regression suite outgrew one file (CodeScene:
low cohesion across ~36 functions, threshold 4) and is now split by
responsibility across test_training_audit_bridge.py,
test_training_audit_readiness.py, test_training_audit_preferences.py,
test_training_audit_agentic.py, and test_training_audit_curated_views.py.
This module holds what two or more of those files need in common.
"""

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

if str(REPO / "pipelines") not in sys.path:
    sys.path.insert(0, str(REPO / "pipelines"))


def thalamic(record_id, provenance="designed", decision="ACCEPT"):
    return {
        "id": record_id,
        "state": {"sim_or_real": provenance, "domain": "audit-test"},
        "proposed_action": {"action": "noop", "decision_basis": "fixture"},
        "safety_decision": {"decision": decision, "rationale": "bounded fixture"},
        "executed_action": {"action": "noop"},
        "future_outcome": {"success": True},
        "reward_components": {"task_progress": 0.5, "safety": 0.5, "total": 1.0},
        "meta": {"tags": ["audit", "fixture"], "round": 1},
    }


def write(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(record) + "\n" for record in records))


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
