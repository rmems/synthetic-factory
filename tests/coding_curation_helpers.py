"""Shared builders for coding-curation unit tests."""

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PIPELINES = ROOT / "pipelines"
if str(PIPELINES) not in sys.path:
    sys.path.insert(0, str(PIPELINES))

from curate_coding import curate_jsonl  # noqa: E402


def visible_step(**overrides):
    step = {
        "n": 1,
        "thought": "private scratch text that must never affect output",
        "tool_call": {"name": "bash", "args": {"command": "pytest -q"}},
        "observation": "Two tests failed with a timezone mismatch.",
        "reflection": "The failure is deterministic outside UTC. Inspect both clocks next.",
    }
    step.update(overrides)
    return step


def episode(steps):
    return {
        "goal": "Diagnose the failing build.",
        "steps": steps,
        "outcome": "The visible evidence isolated the defect.",
        "reward": {"success": True},
        "meta": {"factory": "agentic-coding-trajectory-factory"},
    }


def wrap_record(steps):
    """A Thalamic gate record whose executed_action embeds a coding episode."""
    return {
        "state": {"episode_id": "actf-r02-004", "sim_or_real": "designed"},
        "proposed_action": {
            "action_type": "delegate_to_coding_agent",
            "policy_confidence": 0.71,
            "internal_reasoning": "private gate rationale that must not publish",
            "internal_reasoning_verbatim": "verbatim private gate rationale",
        },
        "safety_decision": {"decision": "ACCEPT", "rationale": "bounded fixture"},
        "executed_action": {
            "goal": "Diagnose the failing build.",
            "steps": steps,
            "outcome": "The visible evidence isolated the defect.",
            "reward": {"success": True},
        },
        "future_outcome": {"success": True},
        "reward_components": {"task_progress": 0.5, "safety": 0.5, "total": 1.0},
        "meta": {"factory": "agentic-coding-trajectory-factory", "round": 2},
    }


def curated_result(steps_per_record):
    """Curate temporary JSONL episodes and return the full curate_jsonl result."""
    with tempfile.TemporaryDirectory() as temporary:
        source = Path(temporary) / "episodes.jsonl"
        with source.open("w", encoding="utf-8") as handle:
            for steps in steps_per_record:
                handle.write(json.dumps(episode(steps), ensure_ascii=False) + "\n")
        return curate_jsonl(source)
