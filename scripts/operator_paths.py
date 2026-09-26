#!/usr/bin/env python3
"""Compatibility shim: the confinement itself lives in ``pipelines/operator_paths.py``.

The module aliases itself to the pipelines module so both spellings are one
object.
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO = str(Path(__file__).resolve().parents[1])
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

from pipelines import operator_paths as _operator_paths

sys.modules[__name__] = _operator_paths
