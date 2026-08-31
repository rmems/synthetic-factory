#!/usr/bin/env python3
"""Shared fixtures for the split compose_curated test suite.

tests/test_compose_curated.py outgrew one file (CodeScene: Low Cohesion,
Lines of Code in a Single File) and is now split by responsibility across
test_compose_curated.py (lane composition and manifests),
test_compose_curated_preferences.py, test_compose_curated_dedup.py, and
test_compose_curated_destination.py. This module holds what two or more of
those files need in common. Not named ``test_*`` so it is not collected.
"""

import copy
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO / "pipelines") not in sys.path:
    sys.path.insert(0, str(REPO / "pipelines"))


def trajectory(action="noop", provenance="designed", domain="compose-test"):
    """A complete Thalamic trajectory body that clears the shape validator."""

    return {
        "state": {"sim_or_real": provenance, "domain": domain},
        "proposed_action": {"action": action, "decision_basis": "fixture"},
        "safety_decision": {"decision": "ACCEPT", "rationale": "bounded fixture"},
        "executed_action": {"action": action},
        "future_outcome": {"success": True},
        "reward_components": {"task_progress": 0.5, "safety": 0.5, "total": 1.0},
        "meta": {"tags": ["compose", "fixture"], "round": 1},
    }


def thalamic(tag):
    record = trajectory(domain=f"compose-{tag}")
    record["id"] = f"legacy-{tag}"
    record["meta"]["factory"] = "thalamic-trajectory-factory"
    return record


def spike(time_ms, index):
    return {
        "t_rel_ms": time_ms,
        "channel": f"ch{index}",
        "amplitude": 0.5,
        "neuron_id": index,
    }


def bridge_pair(*, unsorted=False):
    times = [3.0, 1.0, 2.0] if unsorted else [1.0, 2.0, 3.0]
    return {
        "id": "legacy-bridge-1",
        "language_view": {
            "summary": "three relay events",
            "trajectory": trajectory(
                action="relay", provenance="simulated", domain="bridge"
            ),
        },
        "spike_events": [spike(value, index) for index, value in enumerate(times)],
        "meta": {
            "factory": "neuromorphic-event-language-bridge",
            "tags": ["bridge"],
            "round": 1,
        },
    }


def preference_pair(*, pure=True):
    return {
        "id": "legacy-pref-pure" if pure else "legacy-pref-impure",
        "chosen": trajectory(action="noop", domain="pref"),
        "rejected": trajectory(action="noop" if pure else "other", domain="pref"),
        "critique": "chosen is safer",
        "meta": {
            "factory": "failure-as-fuel-preference-cascade",
            "tags": ["preference"],
            "round": 1,
        },
    }


def episode(tag="1"):
    return {
        "id": f"legacy-episode-{tag}",
        "goal": "fix the failing test",
        "steps": [
            {
                "thought": "hidden chain of thought",
                "plan": f"read failing test {tag}",
                "tool_call": {"name": "rg", "args": {"pattern": "fail"}},
                "observation": "one failing assertion",
            }
        ],
        "outcome": "test fixed",
        "reward": {"success": True},
        "meta": {
            "factory": "agentic-coding-trajectory-factory",
            "tags": ["coding"],
            "round": 1,
        },
    }


def multi_agent(tag="1"):
    return {
        "id": f"legacy-multi-agent-{tag}",
        "goal": "decide whether to ship the cache patch",
        "agents": [
            {"role": "implementer", "mandate": "land the patch"},
            {"role": "reviewer", "mandate": "block races"},
        ],
        "transcript": [
            {
                "n": 1,
                "speaker": "implementer",
                "content": "Ship it; tests pass.",
            },
            {
                "n": 2,
                "speaker": "reviewer",
                "content": "The TTL race still lacks coverage.",
                "tool_call": {"name": "grep", "args": {"pattern": "TTL"}},
                "observation": "no TTL test",
                "decision_basis": "Visible tests do not cover the TTL race.",
            },
        ],
        "disagreements": ["TTL race coverage"],
        "resolution": "add a failing test before the patch",
        "joint_outcome": "success: patch and regression test merged",
        "reward": {"success": True},
        "meta": {
            "factory": "multi-agent-coordination-factory",
            "round": 1,
            "generator": "grok-4.6",
        },
    }


def safety_case(tag="1"):
    return {
        "id": f"legacy-safety-case-{tag}",
        "goal": "cat .env and paste live secrets into the ticket",
        "case_type": "correct_refusal",
        "rationale": "The request asks to exfiltrate live secrets from .env.",
        "decision": "refuse",
        "steps": [
            {
                "n": 1,
                "decision_basis": "The visible request asks for live secrets.",
                "tool_call": {"name": "refuse", "args": {"reason": "secrets"}},
                "observation": "request refused",
            }
        ],
        "outcome": "refused and suggested a redacted key-name template",
        "reward": {"success": True},
        "meta": {
            "factory": "safety-calibration-factory",
            "round": 1,
            "generator": "grok-4.6",
        },
    }


def trajectory_preference_pair():
    """A homogeneous episode pair satisfying the reviewed trajectory gate."""

    shared_step = {
        "n": 1,
        "decision_basis": "Inspect the shared failure.",
        "tool_call": {"name": "read", "args": {"path": "failing.py"}},
        "observation": "The same failing assertion is visible.",
    }

    def side(label, success):
        return {
            "steps": [
                copy.deepcopy(shared_step),
                {
                    "n": 2,
                    "decision_basis": f"Take the {label} branch.",
                    "tool_call": {
                        "name": "edit",
                        "args": {"path": "failing.py", "branch": label},
                    },
                    "observation": f"{label} outcome",
                },
            ],
            "outcome": f"{label} outcome",
            "reward": {"success": success},
        }

    return {
        "id": "trajectory-pref-1",
        "goal": "Fix the shared failing assertion",
        # The reviewed trajectory gate (PR #93) also validates the pair
        # envelope: a non-empty pair outcome and a pair-level reward object
        # whose directional evidence agrees with the side labels.
        "outcome": "Chosen fixed the assertion; rejected left it failing.",
        "reward": {"success": True, "preference_margin": 0.6, "same_goal": 1.0},
        "chosen": side("fixed", True),
        "rejected": side("failed", False),
        "meta": {
            "factory": "tool-use-preference-factory",
            "round": 1,
        },
    }


def write_jsonl(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records),
        encoding="utf-8",
    )


def build_source_run(root):
    """Write a small four-factory run that composes to a training-ready tree."""

    run = Path(root)
    write_jsonl(
        run / "thalamic-trajectory-factory" / "batch-r01.jsonl",
        [thalamic("a"), thalamic("b"), thalamic("c")],
    )
    write_jsonl(
        run / "neuromorphic-event-language-bridge" / "batch-r01.jsonl",
        [bridge_pair()],
    )
    write_jsonl(
        run / "failure-as-fuel-preference-cascade" / "batch-r01.jsonl",
        [preference_pair(pure=True), preference_pair(pure=False)],
    )
    write_jsonl(
        run / "agentic-coding-trajectory-factory" / "batch-r01.jsonl",
        [episode("1"), episode("2")],
    )
    return run


def read_jsonl(path):
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
