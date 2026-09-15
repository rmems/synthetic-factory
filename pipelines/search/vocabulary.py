#!/usr/bin/env python3
"""Vocabulary for the ``search`` mill family (search-index-rebuild lane).

FAMILY=search. The reviewed mill prefix is ``sir`` (see
``mill_reviewed_vocabulary.REVIEWED_MILL_PREFIX_HOMES``). Catalog identity is
AST-extracted from the two leftover leftover leftover mills preserved on
``legacy-mill-lane``. Those leftover3 / leftover-lll publishers hop
destinations and dest-stamp ``meta.factory``; they are not vendored and are
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
CATALOG_FILENAME = "CATALOG.json"

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

VENDOR_PREFIXES = ("search_index_rebuild",)
FORBIDDEN_MILL_GLOBS = (
    "search_index_rebuild*.py",
    "sir-mill-leftover*.py",
    "sir-loop-leftover*.py",
    "sir_r*_leftover*_mill.py",
)
