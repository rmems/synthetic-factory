#!/usr/bin/env python3
"""Vocabulary for the ``cst`` mill family (cache-stampede lane).

The reviewed mill prefix ``cst`` maps to ``cache-stampede-factory`` in
``mill_reviewed_vocabulary.REVIEWED_MILL_PREFIX_HOMES``. PR-a extracts
``PAIRS`` / ``PLANTS`` catalogs from the 21 ``legacy-mill-lane`` scripts
without vendoring ``cst-mill*.py``.
"""

from __future__ import annotations

FAMILY_PREFIX = "cst"
FACTORY = "cache-stampede-factory"
GENERATOR = "grok-4.6"
RECORD_ID_PREFIX = FAMILY_PREFIX
QUOTA_PER_ROUND = 2
CATALOG_SCHEMA_ID = "cst-catalog-extract/v1"
DEFAULT_RUN_LABEL = "2026-08-19-agentic"
LEGACY_REF = "origin/legacy-mill-lane"
PRESERVE_COMMIT = "224c61bb55bf230189fc44b7845c7649fb903517"
CATALOG_FILENAME = "CATALOG.json"

# product, slug_ok, slug_part, plant, src, test, api, naive, fix, workers,
# residual, sibling, sib_file, sib_test, miss_metric
PAIR_FIELDS_15 = (
    "product",
    "slug_ok",
    "slug_part",
    "plant",
    "src",
    "test",
    "api",
    "naive",
    "fix",
    "workers",
    "residual",
    "sibling",
    "sib_file",
    "sib_test",
    "miss_metric",
)

# r2430 adds trigger / cache_key / origin (commented as metric, trigger, cache_key, origin).
PAIR_FIELDS_18 = PAIR_FIELDS_15[:-1] + (
    "metric",
    "trigger",
    "cache_key",
    "origin",
)

PLANT_ROW_KEYS = ("slug_ok", "slug_bad", "ok", "bad")
CATALOG_ASSIGNMENT_NAMES = frozenset(
    {"PAIRS", "PLANTS", "CATALOG_FIRST", "GEN", "FAC", "MAX_ROUNDS"}
)
CATALOG_CONSTRUCTOR_NAMES = frozenset({"plant", "ok", "bad"})
FORBIDDEN_MILL_GLOBS = (
    "cst-mill*.py",
    "cst_*_mill.py",
    "cst_r*_mill.py",
    "cst-loop*.py",
)
