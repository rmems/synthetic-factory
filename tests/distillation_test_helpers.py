"""Shared committed raster and gate fixtures for cross-suite test helpers."""

import json
from pathlib import Path


BRIDGE_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "bridge_gate_snn.jsonl"


def load_bridge_fixture():
    """Load a fresh copy of the committed Bridge fixture."""

    return json.loads(BRIDGE_FIXTURE.read_text(encoding="utf-8").splitlines()[0])


def distillation_sidecars(decision="ACCEPT"):
    """Return independent raster and gate sidecars for one decision."""

    record = load_bridge_fixture()
    sidecars = {
        "raster": record["raster"],
        "gate_snn": dict(record["gate_snn"]),
    }
    sidecars["gate_snn"]["decision"] = decision
    return sidecars
