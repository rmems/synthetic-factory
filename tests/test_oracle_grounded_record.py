#!/usr/bin/env python3
"""Tests for the record envelope, the generator/oracle split, and the boundary.

The point of these is adversarial: it should not be possible to make a record
that looks authoritative without an oracle having produced it. Each test below
mutates one thing and asserts the validator notices.
"""

import copy
import json
import math
import shutil
import subprocess  # nosec B404 -- the protocol test executes a fixed local fixture
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

from oracle_grounded import (  # noqa: E402
    canon,
    families,
    generators,
    oracles,
    record,
    schema_validation,
    sim,
)

DOUBLE = REPO / "tests" / "fixtures" / "oracle-grounded" / "protocol_double.py"
PINNED_COMMIT = oracles.resolve_commit(REPO)[0]

__all__ = (
    "DOUBLE", "PINNED_COMMIT", "Path", "REPO", "accepted_reference", "build", "canon",
    "copy", "double_env", "families", "forge_consistent_eligibility", "generators", "json",
    "math", "mock", "oracles", "proposal_findings", "record", "relabel_as_named_runtime",
    "relabel_plasticity_stage_as_named", "result_findings", "schema_validation", "shutil",
    "sim", "subprocess", "sys", "tempfile", "threading", "time", "unittest",
)


def build(family, index=0, **kwargs):
    kwargs.setdefault("commit", PINNED_COMMIT)
    kwargs.setdefault("dirty", False)
    kwargs.setdefault("environ", {})
    return record.build_record(
        family, index, seed=12345, run=record.RecordRunContext(**kwargs)
    )


def double_env(mode="ok", runtimes=("axon-encoder",)):
    command = f"{sys.executable} {DOUBLE} {mode}"
    return {oracles.env_key(runtime): command for runtime in runtimes}


def result_findings(item):
    item["result_hash"] = canon.digest(item["result"])
    return record.validate_record(item, check_declared_status=False)


def proposal_findings(item):
    item["proposal_hash"] = canon.digest(record.proposal_of(item))
    return record.validate_record(item, check_declared_status=False)


def relabel_plasticity_stage_as_named(item):
    """A structurally valid mixed chain: reference critic, named plasticity."""
    item = copy.deepcopy(item)
    oracle = item["oracle"]
    oracle["implementation"] = "mixed"
    oracle["authority"] = "mixed-reference-and-runtime"
    item["provenance"]["claimed"] = "mixed-reference-and-runtime"
    item["meta"]["tags"][-1] = "mixed"
    stage = oracle["stages"][1]
    runtime = oracle["requested_runtime"][1]
    stage["implementation"] = "named-runtime"
    stage["oracle_id"] = runtime
    stage["version"] = "0.0.0-double"
    stage["runtime_commit"] = "a" * 40
    stage["executable"] = runtime
    stage.pop("module_digest", None)
    oracle["availability"]["runtimes"][1]["bound"] = True
    oracle["availability"]["all_bound"] = False
    oracle["availability"]["unbound"] = [oracle["requested_runtime"][0]]
    oracle["runtime_bound"] = False
    oracle["id"] = "+".join(entry["oracle_id"] for entry in oracle["stages"])
    item["result"]["produced_by"] = oracle["id"]
    item["result_hash"] = canon.digest(item["result"])
    item["validation"] = record.assess(item)
    return item


def forge_consistent_eligibility(item, offset=0.05):
    """Shift eligibility[0] and recompute the retained update from the rule."""
    plasticity = item["result"]["measured"]["plasticity"]
    critic = item["result"]["measured"]["critic"]
    config = item["oracle"]["configuration"]["plasticity"]
    plasticity["eligibility"][0] = round(plasticity["eligibility"][0] + offset, 6)
    raw_delta = (
        config["learning_rate"]
        * plasticity["eligibility"][0]
        * critic["dopamine_phasic"]
        * plasticity["modulatory_gain"]
    )
    updated = sim.clamp(
        plasticity["weights_before"][0] + raw_delta, config["w_min"], config["w_max"]
    )
    plasticity["weight_deltas"][0] = updated - plasticity["weights_before"][0]
    plasticity["weights_after"][0] = updated
    plasticity["update_applied"] = any(
        abs(delta) > sim.WEIGHT_UPDATE_EPS for delta in plasticity["weight_deltas"]
    )
    return item


def relabel_as_named_runtime(item):
    """Create a structurally valid synthetic named-runtime record for gate tests."""
    item = copy.deepcopy(item)
    oracle = item["oracle"]
    oracle["implementation"] = "named-runtime"
    oracle["authority"] = "measured-runtime"
    item["provenance"]["claimed"] = "measured-runtime"
    item["meta"]["tags"][-1] = "named-runtime"
    oracle["runtime_bound"] = True
    oracle["availability"]["all_bound"] = True
    oracle["availability"]["unbound"] = []
    for probe in oracle["availability"]["runtimes"]:
        probe["bound"] = True
    stage_ids = []
    for stage, runtime in zip(oracle["stages"], oracle["requested_runtime"], strict=True):
        stage["implementation"] = "named-runtime"
        stage["oracle_id"] = runtime
        stage["version"] = "0.0.0-double"
        stage["runtime_commit"] = "a" * 40
        stage["executable"] = runtime
        stage.pop("module_digest", None)
        stage_ids.append(runtime)
    oracle["id"] = "+".join(stage_ids)
    item["result"]["produced_by"] = oracle["id"]
    item["result_hash"] = canon.digest(item["result"])
    item["validation"] = record.assess(item)
    return item


def accepted_reference(family, limit=24):
    """Return the first accepted reference record for the shared test seed."""
    return next(
        item
        for item in (build(family, index) for index in range(limit))
        if item["validation"]["status"] == "accepted"
    )
