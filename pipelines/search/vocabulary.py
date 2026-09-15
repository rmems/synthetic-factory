#!/usr/bin/env python3
"""Vocabulary for the ``search`` mill family (search-index-rebuild lane).

FAMILY=search. The reviewed mill prefix is ``sir`` (see
``mill_reviewed_vocabulary.REVIEWED_MILL_PREFIX_HOMES``). Slice leftover-mills
is the #266 leftover3 / leftover-lll catalog.
Slice sir-mill-r72 is the second-slice home mill (20 unique-engine pairs)
AST-extracted from ``experiments/sir-mill-r72.py``. Leftover3 / leftover-lll
publishers hop destinations and dest-stamp ``meta.factory``; they stay in
the leftover catalog, are not re-extracted here, are not vendored, and are
never executed.
"""

from __future__ import annotations

FAMILY = "search"
FAMILY_PREFIX = "sir"
FACTORY = "search-index-rebuild-factory"
GENERATOR = "grok-4.6"
RECORD_ID_PREFIX = FAMILY_PREFIX
QUOTA_PER_ROUND = 2
CATALOG_SCHEMA_ID = "search-catalog-extract/v1"
SLICE_ID = "leftover-mills"
R72_SLICE_ID = "sir-mill-r72"
DEFAULT_RUN_LABEL = "2026-08-19-agentic"
LEGACY_REF = "origin/legacy-mill-lane"
PRESERVE_COMMIT = "e39b5453220fed034c7e112421953e0bf9a18e3d"
R72_PRESERVE_COMMIT = "854c59b31eb9bde983f79c8a1adf3b40d04100a9"
CATALOG_FILENAME = "CATALOG.json"
R72_JSONL_FILENAME = "r72.jsonl"
R72_MILL_ID = "sir-mill-r72"
R72_PATH = "experiments/sir-mill-r72.py"
R72_CATALOG_FIRST = 72
R72_N_ROWS = 20
R72_FIRST_SLUG = "orama-rebuild"
R72_LAST_SLUG = "bleve-scorch-rebuild"
R72_BLOB_SHA = "860ef89f276787201cc7ef76221bb41c339bcc76"
R72_SHA256 = "5b5be41f09925373302324e5260913acd59e625b3570abc932a069b0d7a52fcd"

KIND_LEFTOVER_PAIRS = "leftover-pairs"
KIND_HOME_PAIRS = "home-pairs"
SHAPE_PAIR_6TUPLES = "pair-6tuples"
LEFTOVER_MARKERS = ("leftover3", "leftover-lll", "leftover_lll")

BANNED = (
    "thought",
    "chain_of_thought",
    "scratch",
    "inner_monologue",
    "spike_events",
)

CATALOG_ASSIGNMENT_NAMES = frozenset(
    {
        "FACTORY",
        "GEN",
        "N_ROUNDS",
        "CATALOG_FIRST",
        "HOP",
        "PAIRS",
    }
)

VENDOR_PREFIXES = ("search_index_rebuild",)
FORBIDDEN_MILL_GLOBS = (
    "search_index_rebuild*.py",
    "sir-mill-leftover*.py",
    "sir-loop-leftover*.py",
    "sir_r*_leftover*_mill.py",
)
CATALOGED_LEFTOVER_STEMS = frozenset(
    {
        "search_index_rebuild_leftover3_mill",
        "search_index_rebuild_leftover_lll_mill",
        "sir-mill-leftover3-r72",
        "sir-loop-leftover3-r72",
        "sir_r108_leftover3d_mill",
    }
)
