#!/usr/bin/env python3
"""The vocabulary every `hardware_parity*` sibling shares.

Constants only, and no import from the family: this is what the catalog, the
metrics, the record builder, the validators and the CLI all agree on, so it
has to be the one module none of them can create a cycle through.
"""

from __future__ import annotations

import sys
from pathlib import Path

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from oracle_grounded import parity_contract as contract  # noqa: E402
from neuro_oracle import Q88_STEP  # noqa: E402

SCHEMA_VERSION = "1.0.0"
VALIDATOR = "pipelines/hardware_parity.py"
FACTORY_SLUG = "hardware-parity-spike-trajectories"
RECORD_KIND = contract.KIND_HARDWARE_PARITY

# A membrane difference larger than four Q8.8 least-significant bits is worth a
# reason code even when the spike trains agree: it says the two datapaths are
# drifting and the agreement may not survive a longer window.
MEMBRANE_TOLERANCE = 4 * Q88_STEP
# Float comparison tolerance when re-deriving recorded metrics.
METRIC_TOL = 1e-9
VALIDATION_DATA_ERRORS = (
    TypeError,
    ValueError,
    OverflowError,
    RecursionError,
    UnicodeError,
    KeyError,
    IndexError,
    AttributeError,
)

# The one pairing this family measures. Free text here would let a record
# advertise an execution (e.g. a live FPGA) that its adapter legs do not
# substantiate, so validation pins it to this canonical value.
ORACLE_PAIRING = "software_simulator <-> deployment_target"

GENERATOR_BLOCK = {
    "name": "synthetic-factory.hardware_parity.scenario_catalog",
    "model": "deterministic-stdlib-catalog",
    "role": "proposes test configurations and perturbations",
    "produced": ["scenario", "intervention", "candidate_prediction"],
    "may_certify_oracle_result": False,
    "note": (
        "Scenarios in this fixture are authored by a deterministic in-repo catalog, "
        "not by a language model. Whoever authors them, the generator block never "
        "supplies result fields."
    ),
}


# Frontier-session catalogs inherit research-only disposition (#173). Stamps are
# required on every record so training-view consumers cannot strip the signal.
CATALOG_AUTHORSHIP = {
    "mode": "frontier_session",
    "intended_use": "research_only",
    "project_training_policy": "blocked",
    "attestation": (
        "Hardware-parity scenario catalogs were authored in a frontier-model "
        "session; every resulting record is research-only."
    ),
}
