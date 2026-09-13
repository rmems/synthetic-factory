#!/usr/bin/env python3
"""Shared fixtures for the trajectory-pair preference gate test modules.

Split out of ``test_curate_trajectory_preferences`` so each test module can
state one responsibility. Not named ``test_*`` so it is not itself collected.
"""

import copy
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"
if str(PIPELINES) not in sys.path:
    sys.path.insert(0, str(PIPELINES))

FIXTURE_DIR = REPO / "tests" / "fixtures" / "grok-trajectory-preferences"
PURITY_FIXTURES = REPO / "tests" / "fixtures" / "preference-purity"


def step(n: int, basis: str, command: str = "ls -la", observation: str = "designed: ok"):
    return {
        "n": n,
        "decision_basis": basis,
        "tool_call": {"name": "bash", "args": {"command": command}},
        "observation": observation,
    }


def trajectory_pair(record_id: str = "tpf-1") -> dict:
    """A record shaped exactly like a published Grok preference pair."""

    shared = [step(1, "Observation: the operator asked for a crash-safe publish.")]
    return {
        "id": record_id,
        "goal": "Publish manifest.json so readers never observe a partial object.",
        "outcome": "Chosen renamed a temp file; rejected truncated in place.",
        "reward": {
            "success": True,
            "preference_margin": 0.7,
            "same_goal": 1.0,
        },
        "meta": {"round": 1},
        "chosen": {
            "steps": copy.deepcopy(shared) + [step(2, "Plan: fsync a temp file, then rename.")],
            "outcome": "Readers only ever see a complete object.",
            "reward": {"success": True, "process_quality": 0.9},
        },
        "rejected": {
            "steps": copy.deepcopy(shared) + [step(2, "Plan: truncate the destination in place.")],
            "outcome": "A half-written destination broke the harvest parser.",
            "reward": {"success": False, "process_quality": 0.2},
        },
        "critique": "One goal, one shared prefix, one fork.",
    }


def same_state_pair(record_id: str = "ffpc-1") -> dict:
    """A Fable FFPC pair, which this lane must defer rather than judge."""

    state = {"episode": "e1", "environment": {"queue_depth": 3}}
    proposal = {"action": "flush", "parameters": {"batch": 8}}
    return {
        "id": record_id,
        "chosen": {
            "state": copy.deepcopy(state),
            "proposed_action": copy.deepcopy(proposal),
            "future_outcome": {"ok": True},
        },
        "rejected": {
            "state": copy.deepcopy(state),
            "proposed_action": copy.deepcopy(proposal),
            "future_outcome": {"ok": False},
        },
        "reward_delta": {"total": 0.4},
    }
