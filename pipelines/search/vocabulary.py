#!/usr/bin/env python3
"""Vocabulary for the ``search`` mill family (search-index-rebuild lane).

FAMILY=search. The reviewed mill prefix is ``sir`` (see
``mill_reviewed_vocabulary.REVIEWED_MILL_PREFIX_HOMES``). Slice leftover-mills
is the #266 leftover3 / leftover-lll catalog.
Slices sir-mill-r31, sir-mill-r52, and sir-mill-r72 are home mills AST-extracted
from ``experiments/sir-mill-r31.py``, ``sir-mill-r52.py``, and ``sir-mill-r72.py``.
Leftover3 / leftover-lll
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
DEFAULT_RUN_LABEL = "2026-08-19-agentic"
LEGACY_REF = "origin/legacy-mill-lane"
PRESERVE_COMMIT = "e39b5453220fed034c7e112421953e0bf9a18e3d"
HOME_PRESERVE_COMMIT = "854c59b31eb9bde983f79c8a1adf3b40d04100a9"
R72_PRESERVE_COMMIT = HOME_PRESERVE_COMMIT
CATALOG_FILENAME = "CATALOG.json"
R31_SLICE_ID = "sir-mill-r31"
R31_JSONL_FILENAME = "r31.jsonl"
R31_HEADER_FILENAME = "R31.json"
R31_HEADER_SCHEMA_ID = "search-r31-catalog/v1"
R31_JSONL_SHA256 = "00a7773c539b9090f4b60e6b201539df14a49d1944fd468032f3040f5a49a61a"
R31_MILL_ID = "sir-mill-r31"
R31_PATH = "experiments/sir-mill-r31.py"
R31_CATALOG_FIRST = 31
R31_N_ROWS = 16
R31_FIRST_SLUG = "sqlite-vec-rebuild"
R31_LAST_SLUG = "lancedb-ivf-rebuild"
R31_BLOB_SHA = "229a91d892fe12d19e21f0e25d5031bca348f51e"
R31_SHA256 = "b0332396e1c20c8640a4c0cf04e91ec135e983407b91a3cc76e24154debe72ae"
R52_SLICE_ID = "sir-mill-r52"
R52_JSONL_FILENAME = "r52.jsonl"
R52_HEADER_FILENAME = "R52.json"
R52_HEADER_SCHEMA_ID = "search-r52-catalog/v1"
R52_JSONL_SHA256 = "a2385814f9f686d360c12246d454e537a9411d408e80db960da8f8c6410d3f73"
R52_MILL_ID = "sir-mill-r52"
R52_PATH = "experiments/sir-mill-r52.py"
R52_CATALOG_FIRST = 52
R52_N_ROWS = 20
R52_FIRST_SLUG = "pinecone-ns-rebuild"
R52_LAST_SLUG = "pgvector-sparsevec-rebuild"
R52_BLOB_SHA = "3dc95d6019dd2e193a431c6f60198d3875abbfd1"
R52_SHA256 = "2f9ee3e5a294dbe79dafa4c1683a548b2d01bcea0f5ad4311594028216d8ff39"
R72_SLICE_ID = "sir-mill-r72"
R72_JSONL_FILENAME = "r72.jsonl"
R72_HEADER_FILENAME = "R72.json"
R72_HEADER_SCHEMA_ID = "search-r72-catalog/v1"
R72_JSONL_SHA256 = "575b63b03efbb08419260cd29a97b2175f59cdb04591a41f9f95327d377c0c78"
R72_MILL_ID = "sir-mill-r72"
R72_PATH = "experiments/sir-mill-r72.py"
R72_CATALOG_FIRST = 72
R72_N_ROWS = 20
R72_FIRST_SLUG = "orama-rebuild"
R72_LAST_SLUG = "bleve-scorch-rebuild"
R72_BLOB_SHA = "860ef89f276787201cc7ef76221bb41c339bcc76"
R72_SHA256 = "5b5be41f09925373302324e5260913acd59e625b3570abc932a069b0d7a52fcd"
HOME_MILL_IDS = (R31_MILL_ID, R52_MILL_ID, R72_MILL_ID)

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
