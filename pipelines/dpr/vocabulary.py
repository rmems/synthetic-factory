#!/usr/bin/env python3
"""Vocabulary for the ``dpr`` mill family (data-pipeline-repair lane).

The reviewed mill prefix ``dpr`` maps to ``data-pipeline-repair-factory`` in
``mill_reviewed_vocabulary.REVIEWED_MILL_PREFIX_HOMES``. This package archives
``CATALOG`` / ``PAIRS`` literals AST-extracted from
``origin/legacy-mill-lane`` mill sources. Loop scripts and lrd hoppers are
pinned so later PRs can bind them; they are not catalog rows. Mill publishers
are not vendored and are never executed.
"""

from __future__ import annotations

FAMILY_PREFIX = "dpr"
FACTORY = "data-pipeline-repair-factory"
GENERATOR = "grok-4.6"
RECORD_ID_PREFIX = FAMILY_PREFIX
QUOTA_PER_ROUND = 2
CATALOG_SCHEMA_ID = "dpr-catalog-extract/v1"
CATALOG_SLICE = "representative"
DEFAULT_RUN_LABEL = "2026-08-19-agentic"
LEGACY_REF = "origin/legacy-mill-lane"
PRESERVE_COMMIT = "6fe337661de77b0dcc71e686578ddb0fa01e5863"
CATALOG_FILENAME = "CATALOG.json"
PLANTS_FILENAME = "plants.jsonl"
PAIRS_FILENAME = "pairs.jsonl"
# "all" keeps every extracted pair; "ends" keeps first and last only.
REPRESENTATIVE_PAIR_POLICY = {
    "dpr-mill-leftover3-r2475": "all",
    "dpr-mill-r2631": "ends",
}

KIND_PAIRS = "pairs"
KIND_PLANTS = "plants"
KIND_LOOP = "loop"
KIND_HOPPER = "hopper"
KIND_GEN = "gen"

CATALOG_ASSIGNMENT_NAMES = frozenset(
    {
        "CATALOG",
        "PAIRS",
        "NEW_PAIRS",
        "MORE",
        "START",
        "MAX_ROUNDS",
        "GENERATOR",
        "GEN",
        "FACTORY",
        "BANNED_NEEDLES",
        "BANNED_SUBSTR",
    }
)
PAIR_CTOR_NAMES = frozenset({"OK", "FAIL", "okp", "failp"})
LEFTOVER_PLANT_KEYS = (
    "mod",
    "slug",
    "fail",
    "stack",
    "token",
    "wrong",
    "wrong_key",
    "test_ok",
    "test_fail",
    "docs",
    "doc2",
    "handoff",
    "domain_ok",
    "domain_fail",
    "first_patch",
    "fix_patch",
    "src_obs",
    "plan_ok",
    "plan_fail",
    "ban",
)
FORBIDDEN_MILL_GLOBS = (
    "dpr-mill*.py",
    "dpr_mill*.py",
    "mill_dpr*.py",
    "dpr-loop*.py",
    "dpr_loop*.py",
    "dpr-lrd-hopper*.py",
    "_gen_dpr*.py",
)
HOPPER_NAME_NEEDLES = ("hopper", "lrd-hopper", "dpr-lrd")
