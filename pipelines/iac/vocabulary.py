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
SLICE_ID = "mill_plants"
DEFAULT_RUN_LABEL = "2026-08-19-agentic"
LEGACY_REF = "origin/legacy-mill-lane"
PRESERVE_COMMIT = "51bc810cd2cdd753e97b1ae737d5fa5b00b92478"
ARCHIVE_B_REF = "origin/legacy-mill-lane"
ARCHIVE_B_COMMIT = "813f93f1969c1c4421e5663492e9663739efa642"
PLANTS_SOURCE_PATH = "scripts/infra_as_code_mill/mill_plants.py"
PLANTS_BLOB_SHA = "af10345ae8103af86c05e58355559c5bcd795a8b"
PLANTS_SOURCE_SHA256 = "d2d60f15dafbb666299f1be1f2df7bcdc60aafd9dfc2fda17310f97273f0c585"
PLANTS_B_SOURCE_PATH = "scripts/infra_as_code_mill/mill_plants_b.py"
PLANTS_B_BLOB_SHA = "f28b122cac1956113df18c04ea7eb545d884e590"
PLANTS_B_SOURCE_SHA256 = "e6827da1d0ea4808e535c0cf4a9107f240d4da717790d82f001aeba029c0b558"
CATALOG_FILENAME = "CATALOG.json"
PLANTS_FILENAME = "plants.jsonl"
PLANTS_B_FILENAME = "plants_b.jsonl"
PLANTS_COMPACT_KEYS = (
    "index",
    "success_slug",
    "fail_slug",
    "success_seed",
    "fail_seed",
    "scenario",
    "ticket",
    "test",
    "fail_handoff",
)

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
    "mill_plants*.py",
    "infra_as_code_mill/*.py",
)
