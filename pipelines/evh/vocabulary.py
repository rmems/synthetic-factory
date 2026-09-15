#!/usr/bin/env python3
"""Vocabulary for the ``evh`` mill family (eval-harness lane).

The reviewed mill prefix ``evh`` maps to ``eval-harness-trajectory-factory`` in
``mill_reviewed_vocabulary.REVIEWED_MILL_PREFIX_HOMES``. This package extracts
catalog identity from the nine ``legacy-mill-lane`` scripts without vendoring
``evh-loop*.py``, ``_gen_evh_*.py``, or ``scripts/eval_harness_unique_mill``.
"""

from __future__ import annotations

FAMILY_PREFIX = "evh"
FACTORY = "eval-harness-trajectory-factory"
GENERATOR = "grok-4.6"
RECORD_ID_PREFIX = FAMILY_PREFIX
QUOTA_PER_ROUND = 2
CATALOG_SCHEMA_ID = "evh-catalog-extract/v1"
SLICE_ID = "r801"
DEFAULT_RUN_LABEL = "2026-08-19-agentic"
LEGACY_REF = "origin/legacy-mill-lane"
PRESERVE_COMMIT = "66deb037890ec2b8177c3a07542bf623924037bb"
CATALOG_FILENAME = "CATALOG.json"
MILL_DIR = "scripts/eval_harness_unique_mill"

KIND_PAIRS = "pairs"
KIND_LOOP = "loop"
KIND_GEN = "plant-gen"

SHAPE_ADD_TABLES = "catalog-add-tables"
SHAPE_RAW = "raw-literal"
SHAPE_FSTRING = "catalog-fstring"
SHAPE_PARAM = "catalog-param-fstring"

VENDOR_PREFIXES = (
    "evh-mill-",
    "evh-loop-",
    "_gen_evh_",
    "eval_harness_",
    "mill_plants",
)
FORBIDDEN_MILL_GLOBS = (
    "evh-mill*.py",
    "evh-loop*.py",
    "_gen_evh_*.py",
    "eval_harness_*mill*.py",
    "mill_plants*.py",
)
