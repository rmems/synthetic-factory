#!/usr/bin/env python3
"""Shared fixtures and helpers for the round-transaction preference tests.

Split out of ``test_round_txn`` so each test module states one
responsibility. Not named ``test_*`` so it is not itself collected.
"""

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

import round_txn  # noqa: E402

PREFERENCE_FIXTURES = REPO / "tests" / "fixtures" / "preference-arms"


def write_records(path, records):
    path.write_text("".join(json.dumps(record) + "\n" for record in records))


def thalamic_factory(root):
    """The unrelated (non-preference) factory directory, for negative cases."""
    path = Path(root) / "outputs" / "raw" / "2099-01-01" / "thalamic-trajectory-factory"
    path.mkdir(parents=True)
    return path


def _fixture_records(fixture):
    return [
        json.loads(line)
        for line in (PREFERENCE_FIXTURES / fixture).read_text().splitlines()
        if line.strip()
    ]


def _drop_null_absence_markers(outcome):
    # "No incident" is an absent key, not a null one: the execution gate
    # reads a present ``incident``/``hazard_avoided`` as a claimed
    # observable event and refuses a null payload for it.
    for field in ("incident", "hazard_avoided"):
        if outcome.get(field, "") is None:
            del outcome[field]


def _declare_canonical_observables(outcome, arm_name):
    # main's publish gate runs verify_execution in strict mode and wants the
    # canonical observable trio. The committed arms carry domain observables
    # (compressor_read, doses_transferred) but not that shape, so declare it
    # here rather than editing the fixture's recorded evidence.
    outcome.setdefault("timeline", [{"t_ms": 0, "event": f"{arm_name} arm executed"}])
    outcome.setdefault("observed_effects", [f"{arm_name} arm outcome recorded"])
    outcome.setdefault(
        "new_state",
        {"sim_or_real": "designed", "domain": "transaction-test"},
    )


def _normalize_arm(record, arm_name, round_number):
    arm = record[arm_name]
    arm["id"] = arm["id"].replace("r11", f"r{round_number:02d}")
    outcome = arm.get("future_outcome")
    if isinstance(outcome, dict):
        _drop_null_absence_markers(outcome)
        _declare_canonical_observables(outcome, arm_name)


def ffpc_record(fixture="batch-r11.jsonl", round_number=1, index=0):
    record = _fixture_records(fixture)[index]
    record["id"] = record["id"].replace("r11", f"r{round_number:02d}")
    record["goal"] = "repair one failed action without changing its context"
    for holder in (record, record["chosen"], record["rejected"]):
        holder["meta"]["round"] = round_number
        holder["meta"]["factory"] = round_txn.PREFERENCE_ISOLATION_FACTORY
        holder["meta"]["isolation"] = round_txn.PREFERENCE_TWO_SESSION
    for arm_name in ("chosen", "rejected"):
        _normalize_arm(record, arm_name, round_number)
    return record


def diagnosis_document(index, *, root_cause=None):
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
