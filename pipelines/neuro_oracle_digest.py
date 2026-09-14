#!/usr/bin/env python3
"""Canonical JSON and the digest every oracle record is hashed with.

A leaf: the one definition of "the same value" that the simulators, the capture
replayer and both parity families all resolve to.
"""

from __future__ import annotations

import hashlib
import json
import sys

if __package__:
    # Import-twin helpers join the package import lock; import-order tests cover this edge.
    from . import _assert_direct_sibling, _expose_package_sibling  # pylint: disable=cyclic-import

    _assert_direct_sibling("neuro_oracle_digest")
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "neuro_oracle_digest"
    )

def canonical_json(obj):
    """Stable JSON text used for every digest in the parity families."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(obj):
    """sha256 of the canonical JSON encoding, prefixed with the algorithm."""
    return "sha256:" + hashlib.sha256(canonical_json(obj).encode("utf-8")).hexdigest()


if __package__:
    _expose_package_sibling(__name__)
