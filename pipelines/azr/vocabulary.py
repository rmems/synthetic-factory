#!/usr/bin/env python3
"""Vocabulary for the ``azr`` mill family (authz-regression lane).

The reviewed mill prefix ``azr`` maps to ``authz-regression-factory`` in
``mill_reviewed_vocabulary.REVIEWED_MILL_PREFIX_HOMES``. PR-a extracts
catalog identity from the 76 ``legacy-mill-lane`` scripts without
vendoring ``azr-mill*.py``.
"""

from __future__ import annotations

FAMILY_PREFIX = "azr"
FACTORY = "authz-regression-factory"
GENERATOR = "grok-4.6"
RECORD_ID_PREFIX = FAMILY_PREFIX
QUOTA_PER_ROUND = 2
CATALOG_SCHEMA_ID = "azr-catalog-extract/v1"
SLICE_ID = "r1181"
DEFAULT_RUN_LABEL = "2026-08-19-agentic"
LEGACY_REF = "origin/legacy-mill-lane"
PRESERVE_COMMIT = "9e7fe52231c94b8a9fd3e5b28995505651dbb37e"
CATALOG_FILENAME = "CATALOG.json"
N_SOURCES = 76
N_MILLS = 22
N_LOOPS = 22
N_PLANTS = 20
N_GENS = 12

BANNED = (
    "thought",
    "chain_of_thought",
    "scratch",
    "inner_monologue",
    "spike_events",
)

KIND_PAIRS = "pairs"
KIND_PLANTS = "plants"
KIND_LOOP = "loop"
KIND_GEN = "plant-gen"

SHAPE_LITERAL = "pairs-literal"
SHAPE_NEW_PLUS_KEEP = "pairs-new-plus-keep"
SHAPE_IDOR_BFLA = "idor-bfla-rows"
SHAPE_IDOR_BFLA_COMPOSE = "idor-bfla-compose"
SHAPE_SLICE = "pairs-slice"
SHAPE_PLANTS_ZIP = "plants-zip"

VENDOR_PREFIXES = ("azr-mill-", "azr-loop-", "azr-plants-", "_gen_azr_")
FORBIDDEN_MILL_GLOBS = (
    "azr-mill*.py",
    "azr-loop*.py",
    "azr-plants*.py",
    "_gen_azr_*.py",
    "azr_*_mill.py",
)
