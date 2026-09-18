#!/usr/bin/env python3
"""Vocabulary for the LHC w4cl-r4605 mill slice (long-horizon-coding lane).

FAMILY=lhc, slot 6 by leftover mill-count. The reviewed prefix ``lhc`` maps
to ``long-horizon-coding-factory``. This slice AST-extracts one unused
plants-mk-fn mill from ``legacy-mill-lane``. The publisher is not vendored
and is never executed.
"""

from __future__ import annotations

FAMILY = "lhc"
FAMILY_PREFIX = "lhc"
FACTORY = "long-horizon-coding-factory"
GENERATOR = "grok-4.6"
RECORD_ID_PREFIX = FAMILY_PREFIX
QUOTA_PER_ROUND = 2
CATALOG_SCHEMA_ID = "lhc-w4cl-catalog-extract/v1"
SLICE_ID = "w4cl-r4605"
SLICE_MILL_ID = "lhc-mill-w4cl-r4605"
DEFAULT_RUN_LABEL = "2026-08-19-agentic"
LEGACY_REF = "origin/legacy-mill-lane"
PRESERVE_COMMIT = "813f93f1969c1c4421e5663492e9663739efa642"
CATALOG_FILENAME = "CATALOG.json"
SOURCE_COUNT = 1

KIND_PAIRS = "pairs"
SHAPE_PLANTS_MK_FN = "plants-mk-fn"

BANNED = (
    "thought",
    "chain_of_thought",
    "scratch",
    "inner_monologue",
    "spike_events",
)

VENDOR_PREFIXES = ("lhc-mill-", "lhc-loop-")
FORBIDDEN_MILL_GLOBS = (
    "lhc-mill*.py",
    "lhc-loop*.py",
    "lhc_*_mill.py",
)
