#!/usr/bin/env python3
"""Vocabulary for the ``dbc`` mill family (docker-build-cache lane).

The reviewed mill prefix ``dbc`` maps to ``docker-build-cache-factory``
in ``mill_reviewed_vocabulary.REVIEWED_MILL_PREFIX_HOMES``. PR-a extracts
catalog identity from the 69 ``legacy-mill-lane`` scripts without
vendoring ``dbc-mill*.py`` and without the r597/r600 hop launderers.
The second slice commits the remaining 1212 pair identities as compact
JSONL; r193 stays in ``CATALOG.json``.
"""

from __future__ import annotations

FAMILY_PREFIX = "dbc"
FACTORY = "docker-build-cache-factory"
GENERATOR = "grok-4.6"
RECORD_ID_PREFIX = FAMILY_PREFIX
QUOTA_PER_ROUND = 2
CATALOG_SCHEMA_ID = "dbc-catalog-extract/v1"
SLICE_ID = "r193"
DEFAULT_RUN_LABEL = "2026-08-19-agentic"
LEGACY_REF = "origin/legacy-mill-lane"
PRESERVE_COMMIT = "b183a48c94892a71d543321acc808129dc399e50"
CATALOG_FILENAME = "CATALOG.json"
PAIRS_FILENAME = "pairs.jsonl"
SLICE_MILL_ID = "dbc-mill-r193"
SLICE_PAIR_ROWS = 40
N_PAIR_ROWS = 1252
DEFERRED_PAIR_ROWS = 1212
PAIRS_SHA256 = "57b39bcacd486e447953cd7a1d733acd503914917f57b73a774ef30a8a909e48"
PAIR_JSONL_KEYS = (
    "fail_handoff",
    "fail_plant",
    "fail_slug",
    "mill_id",
    "source_path",
    "success_plant",
    "success_slug",
)
R248_MILL_ID = "dbc-mill-r248"
R248_COMPANION_ID = "dbc-mill-r233"
R647_MILL_ID = "dbc-mill-r647"
R647_COMPANION_ID = "dbc-mill-r598"
R647_INHERIT_FROM = 36

BANNED = (
    "thought",
    "chain_of_thought",
    "scratch",
    "inner_monologue",
    "spike_events",
)

KIND_PAIRS = "pairs"
KIND_LOOP = "loop"
KIND_GEN = "plant-gen"
KIND_HOP = "hop"
KIND_SLUGS = "slug-list"
KIND_LAUNDERER = "launderer"

VENDOR_PREFIXES = ("dbc-mill-", "dbc-loop-", "dbc-hop-", "dbc-chain-")
FORBIDDEN_MILL_GLOBS = (
    "dbc-mill*.py",
    "dbc-loop*.py",
    "dbc-hop*.py",
    "dbc-chain*.py",
    "dbc_*_mill.py",
    "dbc_leftover_lang_mill.py",
)

EXCLUDED_LAUNDERER_PATHS = (
    "experiments/dbc_r597_leftover3_mill.py",
    "experiments/dbc_r600_leftover3_cacheprod_mill.py",
)
