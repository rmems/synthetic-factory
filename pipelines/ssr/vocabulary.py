#!/usr/bin/env python3
"""Vocabulary for the ``ssr`` mill family (secret-scan-remediation lane).

The reviewed mill prefix ``ssr`` maps to ``secret-scan-remediation-factory``
in ``mill_reviewed_vocabulary.REVIEWED_MILL_PREFIX_HOMES``. This first slice
AST-extracts catalog identity from the 77 ``legacy-mill-lane`` mill and loop
scripts without vendoring ``ssr-mill*.py`` and without executing them.
"""

from __future__ import annotations

FAMILY_PREFIX = "ssr"
FACTORY = "secret-scan-remediation-factory"
GENERATOR = "grok-4.6"
RECORD_ID_PREFIX = FAMILY_PREFIX
QUOTA_PER_ROUND = 2
CATALOG_SCHEMA_ID = "ssr-catalog-extract/v1"
SLICE_ID = "r181"
SLICE_MILL_ID = "ssr-mill-r181"
DEFAULT_RUN_LABEL = "2026-08-19-agentic"
LEGACY_REF = "origin/legacy-mill-lane"
PRESERVE_COMMIT = "9178e0bdcc38cef9629c6315d5dd9540492d6a72"
CATALOG_FILENAME = "CATALOG.json"
SOURCE_FILE_COUNT = 77

BANNED = (
    "thought",
    "chain_of_thought",
    "scratch",
    "inner_monologue",
    "spike_events",
)

KIND_PAIRS = "pairs"
KIND_LOOP = "loop"
KIND_FAST = "fast"
VENDOR_PREFIXES = ("ssr-mill-", "ssr-loop-", "ssr_mill_")
FORBIDDEN_MILL_GLOBS = (
    "ssr-mill*.py",
    "ssr-loop*.py",
    "ssr_mill_fast.py",
)
