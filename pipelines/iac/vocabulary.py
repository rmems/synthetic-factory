#!/usr/bin/env python3
"""Vocabulary for the ``iac`` mill family (infra-as-code lane).

The reviewed mill prefix ``iac`` maps to ``infra-as-code-factory`` in
``mill_reviewed_vocabulary.REVIEWED_MILL_PREFIX_HOMES``. PR-a extracts
catalog identity from the 15 ``legacy-mill-lane`` scripts without
vendoring ``iac-mill*.py``.
"""

from __future__ import annotations

FAMILY_PREFIX = "iac"
FACTORY = "infra-as-code-factory"
GENERATOR = "grok-4.6"
RECORD_ID_PREFIX = FAMILY_PREFIX
QUOTA_PER_ROUND = 2
CATALOG_SCHEMA_ID = "iac-catalog-extract/v1"
SLICE_ID = "r609"
DEFAULT_RUN_LABEL = "2026-08-19-agentic"
LEGACY_REF = "origin/legacy-mill-lane"
PRESERVE_COMMIT = "51bc810cd2cdd753e97b1ae737d5fa5b00b92478"
CATALOG_FILENAME = "CATALOG.json"

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
        "BANNED",
        "PAIRS",
        "KEEP",
        "K8S",
        "CLI",
        "CLI_SPEC",
        "_DROP_SUCCESS",
        "_EXTRA",
        "_EXTRA2",
        "_EXTRA3",
        "_EXTRA4",
        "_EXTRA5",
    }
)
PAIR_CTOR_NAMES = frozenset({"_suc", "_fail", "leftover_pair", "file_pair", "tool_pair"})
KIND_PAIRS = "pairs"
KIND_LOOP = "loop"
KIND_GEN = "plant-gen"
VENDOR_PREFIXES = ("iac-mill-", "iac-loop-", "_gen_iac_")
FORBIDDEN_MILL_GLOBS = (
    "iac-mill*.py",
    "iac-loop*.py",
    "_gen_iac_*.py",
    "iac_*_mill.py",
)
