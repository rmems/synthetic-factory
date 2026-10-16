"""Shared record builders for the promote test modules."""

import sys
from pathlib import Path

PIPELINES = Path(__file__).resolve().parents[1] / "pipelines"
if str(PIPELINES) not in sys.path:
    sys.path.insert(0, str(PIPELINES))

import promote

__all__ = ["CLAIMED_LIVE", "_thalamic", "promote"]

CLAIMED_LIVE = "real (production \u2026 actions live)"


def _thalamic(sim_or_real=CLAIMED_LIVE, **overrides):
    rec = {
        "state": {"sim_or_real": sim_or_real, "domain": "test"},
        "proposed_action": {"action_type": "noop"},
        "safety_decision": {"decision": "ACCEPT", "rationale": "ok"},
        "executed_action": {"action_type": "noop"},
        "future_outcome": {"success": "full"},
        "reward_components": {"task_progress": 0.4, "safety": 0.6, "total": 1.0},
        "meta": {"id": "t-001"},
    }
    rec.update(overrides)
    return rec
