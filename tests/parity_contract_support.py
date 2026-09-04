"""Shared fixtures for the parity contract test modules.

``make_record`` is a valid hardware-parity envelope every sibling suite
mutates; ``make_view`` is the training view the contract builds from it.
"""

import copy
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"
sys.path.insert(0, str(PIPELINES))

from oracle_grounded import parity_contract as contract  # noqa: E402

WHERE = "unit:1"


def make_record(**overrides):
    record = {
        "id": "rec-001",
        "record_kind": contract.KIND_HARDWARE_PARITY,
        "dataset": "hardware-parity-spike-trajectories",
        "schema_version": "1.0.0",
        "generator": {
            "name": "unit-generator",
            "model": "deterministic",
            "role": "proposes scenarios",
            "produced": ["scenario"],
            "may_certify_oracle_result": False,
        },
        "scenario": {"id": "sc-001"},
        "intervention": None,
        "candidate_prediction": {"source": "generator", "authoritative": False},
        "oracle": {"software": {"execution_target": "software_float"}},
        "result": {
            "oracle_backed": True,
            "verdict": contract.VERDICT_MATCH,
            "reason_codes": [],
            "derived_from": ["sha256:aa"],
        },
        "provenance": {"kind": "simulated", "tool": "unit", "tool_version": "1"},
        "validation": {
            "validator": "unit",
            "validator_version": "1",
            "checks": ["envelope_contract"],
        },
        "meta": {"round": 1, "factory": "unit-factory"},
    }
    record.update(copy.deepcopy(overrides))
    return record


def make_view(record, **overrides):
    view = contract.build_training_view(
        record, "prompt", "completion", ["software_float"]
    )
    view.update(overrides)
    return view
