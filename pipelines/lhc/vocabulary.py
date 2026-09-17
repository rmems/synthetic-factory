#!/usr/bin/env python3
"""Vocabulary for the ``lhc`` mill family (long-horizon-coding lane).

The reviewed mill prefix ``lhc`` maps to ``long-horizon-coding-factory`` in
``mill_reviewed_vocabulary.REVIEWED_MILL_PREFIX_HOMES``. PR-a extracts catalog identity from the 134 ``legacy-mill-lane`` scripts
without vendoring ``lhc-mill*.py``. PR-b lands the deferred compact pair
identities as ``pairs.jsonl`` (``lhc-mill-w4cl-r4605`` stays in
``pipelines/lhc_w4cl`` only).
"""

from __future__ import annotations

FAMILY_PREFIX = "lhc"
FACTORY = "long-horizon-coding-factory"
GENERATOR = "grok-4.6"
RECORD_ID_PREFIX = FAMILY_PREFIX
QUOTA_PER_ROUND = 2
CATALOG_SCHEMA_ID = "lhc-catalog-extract/v1"
SLICE_ID = "w4x-r4358"
SLICE_MILL_ID = "lhc-mill-w4x-r4358"
DEFAULT_RUN_LABEL = "2026-08-19-agentic"
LEGACY_REF = "origin/legacy-mill-lane"
PRESERVE_COMMIT = "813f93f1969c1c4421e5663492e9663739efa642"
CATALOG_FILENAME = "CATALOG.json"
PAIRS_FILENAME = "pairs.jsonl"
SOURCE_COUNT = 134
DEFERRED_PAIR_ROWS = 1287
EXCLUDED_DEFERRED_MILL_ID = "lhc-mill-w4cl-r4605"

PAIR_IDENTITY_KEYS = (
    "fail_key",
    "fail_plant",
    "fail_slug",
    "success_key",
    "success_plant",
    "success_slug",
    "title",
)
PAIR_ROW_KEYS = (*PAIR_IDENTITY_KEYS, "i", "mill_id", "path")

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
        "USED_FROM",
        "LHC_PAIRS",
        "PAIRS",
        "PLANTS",
    }
)
PAIR_CTOR_NAMES = frozenset({"fn", "fn_pair", "P", "mk", "expand", "plant_from"})
KIND_PAIRS = "pairs"
VENDOR_PREFIXES = ("lhc-mill-",)
FORBIDDEN_MILL_GLOBS = (
    "lhc-mill*.py",
    "lhc_*_mill.py",
    "lhc-loop*.py",
)
