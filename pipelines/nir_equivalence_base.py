#!/usr/bin/env python3
"""Strict JSON comparison and digesting, shared by the catalog, the validator
and the views.

Small on purpose: these two decide whether two recorded values are the same
value, and that question must have exactly one answer across the family.
"""

from __future__ import annotations

import sys

if __package__:
    # Import-twin helpers join the package import lock; import-order tests cover this edge.
    from . import _assert_direct_sibling, _expose_package_sibling  # pylint: disable=cyclic-import

    _assert_direct_sibling("nir_equivalence_base")
    from .neuro_oracle import digest  # noqa: E402
    from .nir_equivalence_terms import (  # noqa: E402
        CANONICAL_DATA_ERRORS,
        contract,
    )
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "nir_equivalence_base"
    )
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


if __package__:
    _expose_package_sibling(__name__)
