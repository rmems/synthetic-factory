#!/usr/bin/env python3
"""Vocabulary for the ``amc`` mill family (agent-memory-compaction lane).

The reviewed mill prefix ``amc`` maps to ``agent-memory-compaction-factory``
in ``mill_reviewed_vocabulary.REVIEWED_MILL_PREFIX_HOMES``. PR-a extracts
catalog identity from the 23 ``legacy-mill-lane`` scripts without vendoring
``amc-mill*.py``.
"""

from __future__ import annotations

FAMILY_PREFIX = "amc"
FACTORY = "agent-memory-compaction-factory"
GENERATOR = "grok-4.6"
RECORD_ID_PREFIX = FAMILY_PREFIX
QUOTA_PER_ROUND = 2
SUCCESS_STEPS = 16
HOST = "mneme-agent"
CATALOG_SCHEMA_ID = "amc-catalog-extract/v1"
DEFAULT_RUN_LABEL = "2026-08-19-agentic"
LEGACY_REF = "origin/legacy-mill-lane"
PRESERVE_COMMIT = "bb0775859c86d4692112c4845790fa1623ab8abb"
CATALOG_FILENAME = "CATALOG.json"

KIND_PAIRS = "pairs"
KIND_LOOP = "loop"
KIND_LEFTOVER = "leftover"

SHAPE_FS = "pairs-fs"
SHAPE_FAIL_SUCC = "pairs-fail-succ"
SHAPE_L = "pairs-l"
SHAPE_P = "pairs-p"
SHAPE_PREFIX_NEW = "pairs-prefix-new"
SHAPE_TABLE_ZIP = "pairs-table-zip"
SHAPE_LEFTOVER = "leftover-dict"

PREFIX_MILL_ID = "amc-mill-r229"
PREFIX_SLICE = 16

FS_CTORS = frozenset({"F", "S"})
FAIL_SUCC_CTORS = frozenset({"fail", "succ"})
L_CTOR = "L"
P_CTOR = "P"
PAIR_CTOR_NAMES = FS_CTORS | FAIL_SUCC_CTORS | {L_CTOR, P_CTOR}

BANNED_SLUG_NEEDLES = (
    "loftus",
    "verb-rewrite",
    "verb_swap",
    "verb-swap",
    "checksum",
    "pincksum",
    "hierarchical-summary",
    "fifo-evict",
    "fifo-drop",
    "salient-fact",
    "comment-slice",
    "skip-verb-swap",
    "require-crc",
)

VENDOR_PREFIXES = ("amc-mill-", "amc-loop-", "mill_amc_")
FORBIDDEN_MILL_GLOBS = (
    "amc-mill*.py",
    "amc-loop*.py",
    "mill_amc*.py",
)
