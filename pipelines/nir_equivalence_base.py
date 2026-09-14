#!/usr/bin/env python3
"""Strict JSON comparison and digesting, shared by the catalog, the validator
and the views.

Small on purpose: these two decide whether two recorded values are the same
value, and that question must have exactly one answer across the family.
"""

from __future__ import annotations

import sys
from pathlib import Path

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from neuro_oracle import digest  # noqa: E402
from nir_equivalence_terms import (  # noqa: E402
    CANONICAL_DATA_ERRORS,
    contract,
)


def _strict_json_equal(recorded, expected):
    try:
        return contract.strict_json_equal(recorded, expected)
    except RecursionError:
        return False


def _safe_digest(value):
    try:
        return digest(value)
    except CANONICAL_DATA_ERRORS:
        return None
