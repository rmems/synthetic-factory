#!/usr/bin/env python3
"""Shared fixtures and CLI helper for the hardware-parity test modules.

`tests/test_hardware_parity*.py` were one 1836-line module; they now split by
responsibility (generation, validation gates, captured-evidence provenance)
and share the committed parity-run fixture and the CLI shim from here.
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
    / "hardware-parity-spike-trajectories"
    / "batch-r01.jsonl"
)
sys.path.insert(0, str(PIPELINES))

WHERE = "unit:1"


def fixture_records():
    return [
        json.loads(line)
        # Only LF frames a record, matching hp.read_jsonl: str.splitlines()
        # would also split on U+2028/U+2029.
        for line in FIXTURE.read_text(encoding="utf-8").split("\n")
        if line.strip()
    ]


def cli(args):
    return subprocess.run(
        [sys.executable, str(PIPELINES / "hardware_parity.py"), *args],
        capture_output=True,
        text=True,
    )
