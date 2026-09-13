"""Shared builders for same-context preference-pair unit tests.

The curation tests and the leftover-mill quarantine tests both need to build
preference pairs whose two branches share a canonical context, and to write
them as JSONL. Those builders live here so the two suites cannot drift apart
about what a same-context pair looks like.
"""

import copy
import json

__all__ = ["pair", "trajectory", "write_jsonl"]


def trajectory(record_id, state=None, proposal=None, decision="ACCEPT"):
    return {
        "id": record_id,
        "state": state
        or {"sim_or_real": "designed", "domain": "preference-curation-test"},
        "proposed_action": proposal
        or {"action": "bounded-noop", "decision_basis": "fixture"},
        "safety_decision": {"decision": decision, "rationale": "fixture rationale"},
        "executed_action": {"action": "bounded-noop"},
        "future_outcome": {"success": decision != "REJECT"},
        "reward_components": {"task_progress": 0.5, "safety": 0.5, "total": 1.0},
        "meta": {"tags": ["preference", "fixture"]},
    }


def pair(record_id="pair-1", chosen_state=None, rejected_state=None, proposal=None):
    shared_state = {"sim_or_real": "designed", "domain": "same-problem"}
    shared_proposal = proposal or {"action": "inspect", "decision_basis": "fixture"}
    return {
        "id": record_id,
        "chosen": trajectory(
            f"{record_id}-chosen",
            state=copy.deepcopy(chosen_state or shared_state),
            proposal=copy.deepcopy(shared_proposal),
            decision="MODIFY",
        ),
        "rejected": trajectory(
            f"{record_id}-rejected",
            state=copy.deepcopy(rejected_state or shared_state),
            proposal=copy.deepcopy(shared_proposal),
            decision="ACCEPT",
        ),
        "critique": "fixture preference",
        "reward_delta": {"task_progress": 0.0, "safety": 0.0, "total": 0.0},
    }


def write_jsonl(path, records):
    path.write_text("".join(json.dumps(record) + "\n" for record in records))
