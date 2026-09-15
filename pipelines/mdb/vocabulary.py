#!/usr/bin/env python3
"""Vocabulary for the ``mdb`` mill family (monorepo-dep-bump lane).

The reviewed mill prefix ``mdb`` maps to ``monorepo-dep-bump-factory`` in
``mill_reviewed_vocabulary.REVIEWED_MILL_PREFIX_HOMES``. PR-a extracts
catalog identity from the 41 ``legacy-mill-lane`` scripts without
vendoring ``mdb-mill*.py``.
"""

from __future__ import annotations

FAMILY_PREFIX = "mdb"
FACTORY = "monorepo-dep-bump-factory"
GENERATOR = "grok-4.6"
RECORD_ID_PREFIX = FAMILY_PREFIX
QUOTA_PER_ROUND = 2
CATALOG_SCHEMA_ID = "mdb-catalog-extract/v1"
SLICE_ID = "r709"
DEFAULT_RUN_LABEL = "2026-08-19-agentic"
LEGACY_REF = "origin/legacy-mill-lane"
PRESERVE_COMMIT = "f769a8c09e45960ca7a3b7d600cbb2a481a67516"
CATALOG_FILENAME = "CATALOG.json"
SLICE_MILL_ID = "mdb-mill-r709"

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
        "CATALOG_FIRST",
        "BANNED_SLUG_NEEDLES",
        "PAIRS",
        "PLANTS",
        "STEMS",
        "TOOLS",
        "RAW",
        "SLUGS",
        "FREE_PLANTS",
    }
)
PAIR_CTOR_NAMES = frozenset({"P", "make", "R", "expand", "row_from_slug"})
KIND_PAIRS = "pairs"
KIND_LOOP = "loop"
KIND_GEN = "plant-gen"
VENDOR_PREFIXES = ("mdb-mill-", "mdb-loop-", "_gen_mdb_", "mdb-hop-")
FORBIDDEN_MILL_GLOBS = (
    "mdb-mill*.py",
    "mdb-loop*.py",
    "_gen_mdb_*.py",
    "mdb-hop-loop.py",
    "mdb_*_mill.py",
)
