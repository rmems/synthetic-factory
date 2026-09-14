#!/usr/bin/env python3
"""The vocabulary every `nir_equivalence*` sibling shares.

Constants only, importing nothing from the family, so no sibling can create a
cycle through it.
"""

from __future__ import annotations

import sys
from pathlib import Path

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from oracle_grounded import parity_contract as contract  # noqa: E402



SCHEMA_VERSION = "1.0.0"
VALIDATOR = "pipelines/nir_equivalence.py"
FACTORY_SLUG = "nir-cross-runtime-equivalence"
RECORD_KIND = contract.KIND_NIR_EQUIVALENCE

NUMERIC_TOL = 1e-9

STATUS_EXECUTED = "executed"
STATUS_UNSUPPORTED = "unsupported"
STATUS_UNAVAILABLE = "unavailable"
RUNTIME_STATUSES = (STATUS_EXECUTED, STATUS_UNSUPPORTED, STATUS_UNAVAILABLE)
UNAVAILABLE_REASON_CODES = frozenset(
    {"RUNTIME_NOT_INSTALLED", "RUNTIME_ADAPTER_NOT_IMPLEMENTED"}
)
CANONICAL_DATA_ERRORS = (
    TypeError,
    ValueError,
    OverflowError,
    RecursionError,
    UnicodeEncodeError,
)
VALIDATION_DATA_ERRORS = CANONICAL_DATA_ERRORS + (KeyError, IndexError, AttributeError)
# `in_repo_reference` results are re-executed during validation.
# `upstream_runtime` results cannot be, which is why only the former may ever
# be marked executed here.
RUNTIME_CLASSES = ("in_repo_reference", "upstream_runtime")

# The one pairing this family measures. Free text here would let a record
# advertise an execution its runtime entries do not substantiate, so
# validation pins it to this canonical value.
ORACLE_PAIRING = "cross-runtime NIR execution"

STATEFUL_TYPES = frozenset({"LIF", "IF", "LI", "Delay"})
ALL_KNOWN_TYPES = frozenset(
    {"Input", "Output", "Affine", "Linear", "LIF", "IF", "LI", "Delay", "Threshold"}
)


GENERATOR_BLOCK = {
    "name": "synthetic-factory.nir_equivalence.graph_catalog",
    "model": "deterministic-stdlib-catalog",
    "role": "proposes graphs, boundary values, and unsupported constructs",
    "produced": ["scenario", "intervention", "candidate_prediction"],
    "may_certify_oracle_result": False,
    "note": (
        "The catalog authors graphs. It never authors outputs: every event trace on "
        "a record comes from an interpreter and is re-executed during validation."
    ),
}


CATALOG_AUTHORSHIP = {
    "mode": "frontier_session",
    "intended_use": "research_only",
    "project_training_policy": "blocked",
    "attestation": (
        "NIR cross-runtime graph catalogs were authored in a frontier-model "
        "session; every resulting record is research-only."
    ),
}
