#!/usr/bin/env python3
"""Shared fixtures and writers for spike-probe tests."""

import json
from pathlib import Path

FIXTURES = Path(__file__).resolve().parent / "fixtures"
GATE_SNN_FIXTURE = FIXTURES / "bridge_gate_snn.jsonl"


def gate_snn_record():
    return json.loads(GATE_SNN_FIXTURE.read_text(encoding="utf-8").splitlines()[0])


def write(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(record) + "\n" for record in records))
