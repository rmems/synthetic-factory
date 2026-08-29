#!/usr/bin/env python3
"""Shared fixtures and helpers for the preference-arm gate test modules.

Split out of ``test_preference_arms`` so each test module can state one
responsibility. Not named ``test_*`` so it is not itself collected.
"""

import contextlib
import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

import preference_arms  # noqa: E402

ARM_FIXTURES = REPO / "tests" / "fixtures" / "preference-arms"
TWO_SESSION_ROUND = ARM_FIXTURES / "batch-r11.jsonl"
NEAR_VERBATIM = ARM_FIXTURES / "near-verbatim-r11.jsonl"
GATE_LABEL_ONLY = ARM_FIXTURES / "gate-label-only-r11.jsonl"
SINGLE_SESSION = ARM_FIXTURES / "single-session-r11.jsonl"


def load(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def first(path):
    return load(path)[0]


def run_cli(argv):
    """Return (exit_code, stdout) for a CLI invocation."""
    out = io.StringIO()
    err = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = preference_arms.main(argv)
    return code, out.getvalue(), err.getvalue()


def check(record, **kwargs):
    return preference_arms.check_pair(record, source_path="memory.jsonl", source_line=1, **kwargs)


def diagnosis_document(index, *, root_cause=None, context=None):
    if context is None:
        context = {
            "state": {"sim_or_real": "designed", "case": index},
            "proposed_action": {"action": "hold", "case": index},
        }
    target = {"per_component": {"safety": 0.5, "task_progress": 0.25}, "total": 0.75}
    return (
        "# Diagnosis\n\n"
        "## Shared context\n\n"
        "```json\n"
        f"{json.dumps(context, sort_keys=True)}\n"
        "```\n\n"
        "## Root cause\n\n"
        f"{root_cause or f'The gate skipped the required check for case {index}.'}\n\n"
        "## Cascade effects\n\n"
        "The gate error propagated through execution, outcome, and reward.\n\n"
        "## Supervisor catch\n\n"
        "Require the missing evidence before allowing execution.\n\n"
        "## Repair sketch\n\n"
        "Add the bounded check and use the safe fallback on failure.\n\n"
        "## Target reward delta\n\n"
        "```json\n"
        f"{json.dumps(target, sort_keys=True)}\n"
        "```\n"
    )


def assert_blocked_copy(test, record, *reasons, distance=0.0):
    """A cosmetically edited arm still reads as a copy, and for these reasons.

    Returns the decision so a caller can add its own assertions.
    """
    decision = check(record)
    test.assertEqual(decision.arm_distance, distance)
    for reason in reasons:
        test.assertIn(reason, decision.reason_codes)
    return decision
