#!/usr/bin/env python3
"""Tiny ACM loop binding used only as AST-extract input."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Legacy mill filename on legacy-mill-lane; this fixture does not vendor it.
LEGACY_MILL = "acm-mill-r1.py"
MILL = ROOT / "experiments" / "acm-pairs-r1.py"
