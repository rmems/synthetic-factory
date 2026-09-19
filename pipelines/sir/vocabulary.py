#!/usr/bin/env python3
"""Vocabulary for the additional ``sir`` leftover catalogs in the search lane.

FAMILY=sir. The reviewed mill prefix is ``sir`` (see
``mill_reviewed_vocabulary.REVIEWED_MILL_PREFIX_HOMES``). Catalog identity is
AST-extracted from two leftover mills preserved on ``legacy-mill-lane``.
The ``search`` package owns the r31/r52/r72 home-mill catalogs.
The leftover3 / leftover3d publishers and the leftover3 loop stay off this
branch and are never executed.
"""

from __future__ import annotations

if __name__.startswith("pipelines."):
    from ..oracle_grounded.import_twins import bind_import_twin
else:
    from oracle_grounded.import_twins import bind_import_twin

FAMILY = "sir"
FAMILY_PREFIX = "sir"
FACTORY = "search-index-rebuild-factory"
GENERATOR = "grok-4.6"
RECORD_ID_PREFIX = FAMILY_PREFIX
QUOTA_PER_ROUND = 2
CATALOG_SCHEMA_ID = "sir-catalog-extract/v1"
SLICE_ID = "leftover-mills"
DEFAULT_RUN_LABEL = "2026-08-19-agentic"
LEGACY_REF = "origin/legacy-mill-lane"
PRESERVE_COMMIT = "854c59b31eb9bde983f79c8a1adf3b40d04100a9"
CATALOG_FILENAME = "CATALOG.json"
PAIRS_FILENAME = "pairs.jsonl"
EXTRACTION = "AST literals only; leftover mill / loop publishers were never imported or executed"

KIND_LEFTOVER_PAIRS = "leftover-pairs"
SHAPE_PAIR_6TUPLES = "pair-6tuples"

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

VENDOR_PREFIXES = (
    "sir-mill",
    "sir-loop",
    "sir_r",
    "search_index_rebuild",
)
FORBIDDEN_MILL_GLOBS = (
    "sir-mill*.py",
    "sir-loop*.py",
    "sir_*_mill.py",
    "search_index_rebuild*.py",
)

PAIR_FIELD_ORDER = (
    "mill_id",
    "success_slug",
    "fail_slug",
    "success_engine",
    "fail_engine",
    "success_wrong",
    "fail_wrong",
    "success_fix",
    "fail_leftover",
    "success_ticket",
    "fail_ticket",
    "success_url",
    "fail_url",
    "fail_handoff",
)

bind_import_twin(__name__)
