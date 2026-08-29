#!/usr/bin/env python3
"""Shared fixtures and graph builders for the NIR-equivalence test modules.

`tests/test_nir_equivalence*.py` were one 1414-line module; they now split by
responsibility and share the committed parity-run fixture, the CLI shim, and
the small graph/stimulus builders from here.
"""

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"
FIXTURE = (
    REPO
    / "tests"
    / "fixtures"
    / "parity-run"
    / "nir-cross-runtime-equivalence"
    / "batch-r01.jsonl"
)
sys.path.insert(0, str(PIPELINES))

import nir_equivalence as nir  # noqa: E402

WHERE = "unit:1"


def fixture_records():
    return [
        json.loads(line)
        for line in FIXTURE.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def cli(args):
    return subprocess.run(
        [sys.executable, str(PIPELINES / "nir_equivalence.py"), *args],
        capture_output=True,
        text=True,
    )


def refresh_result(record):
    comparison = nir.compare_runtimes(
        record["scenario"], record["oracle"]["runtimes"]
    )
    verdict, reason_codes = nir.verdict_for(comparison)
    record["result"]["comparison"] = comparison
    record["result"]["verdict"] = verdict
    record["result"]["reason_codes"] = reason_codes
    record["result"]["derived_from"] = nir._evidence_lineage(
        record["oracle"]["runtimes"]
    )
    record["result"]["summary"] = nir._summarize(
        record["scenario"], comparison, verdict
    )


def rebuild_scenario(scenario, round_number=1):
    entries = [
        nir.execute_runtime(runtime, scenario)
        for runtime in (*nir.IN_REPO_RUNTIMES, *nir.UPSTREAM_RUNTIMES)
    ]
    return nir.build_record(scenario, entries, round_number)


def linear_graph():
    return {
        "name": "unit",
        "dt_s": 0.001,
        "nodes": {
            "in": {"type": "Input", "shape": [2], "size": 2},
            "thr": {"type": "Threshold", "size": 2, "threshold": 0.5},
            "out": {"type": "Output", "size": 2},
        },
        "edges": [["in", "thr"], ["thr", "out"]],
    }


def stimulus(steps=4):
    return {"name": "unit", "steps": steps, "channels": 2,
            "events": [[1.0, 0.0] for _ in range(steps)]}
