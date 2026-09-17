#!/usr/bin/env python3
"""Compatibility shim: the confinement itself lives in ``pipelines/operator_paths.py``.

The code-repair scripts imported this module before the pipeline CLIs needed
the same confinement. It moved to ``pipelines/`` so both can reach it; this
spelling keeps resolving to the same functions.
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO = str(Path(__file__).resolve().parents[1])
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

from pipelines.operator_paths import operator_path, operator_roots  # noqa: E402

__all__ = ["operator_path", "operator_roots"]
