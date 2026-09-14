#!/usr/bin/env python3
"""Canonical JSON and the digest every oracle record is hashed with.

A leaf: the one definition of "the same value" that the simulators, the capture
replayer and both parity families all resolve to.
"""

from __future__ import annotations

from pathlib import Path
import hashlib
import json
import sys

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))



def canonical_json(obj):
    """Stable JSON text used for every digest in the parity families."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(obj):
    """sha256 of the canonical JSON encoding, prefixed with the algorithm."""
    return "sha256:" + hashlib.sha256(canonical_json(obj).encode("utf-8")).hexdigest()
