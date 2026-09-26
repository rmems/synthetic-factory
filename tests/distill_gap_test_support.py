#!/usr/bin/env python3
"""Shared helpers for the ``test_distill_*_gaps`` regression suites."""

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

import moe_router as mr  # noqa: E402
from oracle_grounded import distill_contract as oc  # noqa: E402


def teacher_recording(texts):
    """A replay recording of routing the reference oracle really computed."""

    reference = mr.ReferenceMoERouter()
    return {
        "run_id": "gap-r1",
        "recorded_at": "2026-08-23T00:00:00Z",
        "teacher": {
            "is_llm_teacher": True,
            "model": "unit-test/not-a-real-moe-checkpoint",
            "revision_or_checkpoint": "1234567890abcdef1234567890abcdef12345678",
            "configuration_sha256": reference.fingerprint()["configuration_sha256"],
            "num_local_experts": reference.num_experts,
            "num_experts_per_tok": reference.top_k,
            "num_layers": reference.num_layers,
        },
        "observations": {
            mr.RecordedTeacherRouter.key_for(text): reference.route(text).as_dict()
            for text in texts
        },
    }


def rehash(record: dict) -> dict:
    """Re-stamp the content digest so only the family check can object."""

    record["provenance"]["record_sha256"] = oc.record_digest(record)
    return record


def clone(record: dict) -> dict:
    return json.loads(json.dumps(record))


def measurements_for(record: dict, candidate_id: str, quantity: str):
    """Yield the oracle measurements for one (candidate, quantity) pair."""

    for item in record["result"]["measurements"]:
        detail = item.get("detail")
        if not isinstance(detail, dict):
            continue
        if detail.get("candidate") != candidate_id:
            continue
        if item.get("quantity") == quantity:
            yield item


def set_cost_measurement(record: dict, candidate_id: str, quantity: str, value) -> None:
    """Restate one candidate's measured value in the record's measurements."""

    for item in measurements_for(record, candidate_id, quantity):
        item["value"] = value
