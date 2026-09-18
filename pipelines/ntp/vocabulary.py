#!/usr/bin/env python3
"""Vocabulary for the ``ntp`` mill family (notebook-to-pipeline lane).

The reviewed mill prefix ``ntp`` maps to ``notebook-to-pipeline-factory`` in
``mill_reviewed_vocabulary.REVIEWED_MILL_PREFIX_HOMES``. PR-a extracts
catalog identity from the 84 ``legacy-mill-lane`` scripts without
vendoring ``ntp-mill*.py``. PR-b lands compact r1326 theme identities in
``themes.jsonl``. PR-c lands orch / unique-lll / unique-llll identities in
``pairs.jsonl``.
"""

from __future__ import annotations

FAMILY_PREFIX = "ntp"
FACTORY = "notebook-to-pipeline-factory"
GENERATOR = "grok-4.6"
RECORD_ID_PREFIX = FAMILY_PREFIX
QUOTA_PER_ROUND = 2
CATALOG_SCHEMA_ID = "ntp-catalog-extract/v1"
SLICE_ID = "leftover"
SLICE_MILL_ID = "ntp-mill-unique-leftover"
DEFAULT_RUN_LABEL = "2026-08-19-agentic"
LEGACY_REF = "origin/legacy-mill-lane"
PRESERVE_COMMIT = "813f93f1969c1c4421e5663492e9663739efa642"
CATALOG_FILENAME = "CATALOG.json"
MILLS_FILENAME = "mills.jsonl"
LEFTOVER_FILENAME = "leftover.jsonl"
THEMES_FILENAME = "themes.jsonl"
PAIRS_FILENAME = "pairs.jsonl"
THEME_MILL_ID = "ntp-mill-r1326"
THEME_MILL_IDS = frozenset({THEME_MILL_ID})
CATALOG_EXTRACTION_NOTE = (
    "AST literals only; orch/unique-lll/unique-llll pair identities in pairs.jsonl; "
    "unique-db/dbm mills stay unmilled."
)
PAIR_MILL_IDS = frozenset(
    {
        "ntp-mill-orch-leftover3",
        "ntp-mill-unique-lll",
        "ntp-mill-unique-llll",
        *(f"ntp-mill-unique-llll{n}" for n in range(2, 35)),
    }
)
PLANT_PREFIX = "folio-"

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
        "START",
        "SUCCESS",
        "LEFTOVER",
        "SUCCESS_SPEC",
        "LEFTOVER_SPEC",
    }
)
PAIR_CTOR_NAMES = frozenset({"s_from", "l_from", "S", "L"})
KIND_PAIRS = "pairs"
KIND_LOOP = "loop"
KIND_GEN = "plant-gen"
KIND_CHAIN = "chain"
VENDOR_PREFIXES = (
    "ntp-mill-",
    "ntp-loop-",
    "ntp-chain-",
    "ntp-extend-",
    "_gen_ntp_",
)
FORBIDDEN_MILL_GLOBS = (
    "ntp-mill*.py",
    "ntp-loop*.py",
    "ntp-chain*.py",
    "ntp-extend*.py",
    "_gen_ntp_*.py",
    "ntp_*_mill.py",
)
