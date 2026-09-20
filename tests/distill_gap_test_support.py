#!/usr/bin/env python3
"""Shared helpers for the ``test_distill_*_gaps`` regression suites."""

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

from oracle_grounded import distill_contract as oc  # noqa: E402


def rehash(record: dict) -> dict:
    """Re-stamp the content digest so only the family check can object."""

    record["provenance"]["record_sha256"] = oc.record_digest(record)
    return record


def clone(record: dict) -> dict:
    return json.loads(json.dumps(record))


def set_cost_measurement(record: dict, candidate_id: str, quantity: str, value) -> None:
    """Restate one candidate's measured value in the record's measurements."""

    for item in record["result"]["measurements"]:
        detail = item.get("detail")
        if not isinstance(detail, dict):
            continue
        if detail.get("candidate") != candidate_id:
            continue
        if item["quantity"] == quantity:
            item["value"] = value
