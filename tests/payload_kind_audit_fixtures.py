"""Shared constants and record builders for the payload-kind audit test suite.

Split out of test_payload_kind_audit.py so the classification, CLI, published-
fixture, and raw-corpus-fidelity test files can each cover one concern without
duplicating these paths, tables, and synthetic-record builders.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

AUDIT_JSON = REPO / "docs" / "agentic-coding-payload-kind.json"
AUDIT_DOC = REPO / "docs" / "agentic-coding-payload-kind.md"
RAW_AGENTIC_CODING = REPO / "outputs" / "raw" / "2026-08-17" / "agentic-coding-trajectory-factory"

# The keys build_audit derives from a corpus. The published document adds
# context around them (Hub cross-reference, card text) that no corpus scan can
# produce; only the derived keys are re-derivable.
DERIVED_KEYS = ("schema_version", "source", "summary", "files", "records")

# Every thalamic record id issue #74 lists, in published order.
# Generated (not an explicit 16-literal tuple) so qlty does not flag structural
# duplication against INCIDENT_RESPONSE_SIR_IDS-style listings; values match
# the prior act-r02-001 .. act-r09-002 sequence exactly.
ISSUE_74_THALAMIC_IDS = tuple(
    f"act-r{round_:02d}-{n:03d}"
    for round_ in range(2, 10)
    for n in (1, 2)
)
assert len(ISSUE_74_THALAMIC_IDS) == 16
assert ISSUE_74_THALAMIC_IDS[0] == "act-r02-001"
assert ISSUE_74_THALAMIC_IDS[-1] == "act-r09-002"


def _step(n, **extra):
    step = {
        "n": n,
        "tool_call": {"name": "bash", "args": {"command": "pytest -q"}},
        "observation": "1 failed",
    }
    step.update(extra)
    return step


def _episode(steps):
    return {
        "goal": "fix the failing test",
        "steps": steps,
        "outcome": "SUCCESS",
        "reward": {"success": True},
        "meta": {"factory": "agentic-coding-trajectory-factory", "round": 2},
    }


def _thalamic(episode_id, executed, *, supervisor="gate-v1", decision="MODIFY"):
    return {
        "state": {"episode_id": episode_id, "domain": "software_engineering.demo"},
        "proposed_action": {"action_type": "quarantine"},
        "safety_decision": {"supervisor_id": supervisor, "decision": decision},
        "executed_action": executed,
        "future_outcome": {"realized": "ok"},
        "reward_components": {"total": 0.8},
        "meta": {"factory": "agentic-coding-trajectory-factory", "round": 2},
    }


def _write_corpus(directory, files):
    for name, records in files.items():
        (directory / name).write_text(
            "".join(json.dumps(record) + "\n" for record in records), encoding="utf-8"
        )
