#!/usr/bin/env python3
"""Vocabulary for the ``gor`` mill family (git-ops-recovery lane).

The reviewed mill prefix ``gor`` maps to ``git-ops-recovery-factory`` in
``mill_reviewed_vocabulary.REVIEWED_MILL_PREFIX_HOMES``. PR-a extracts
catalog identity from the 33 ``legacy-mill-lane`` scripts without
vendoring ``gor-mill*.py``. PR-b lands the 961 deferred pair identities
(r973–r1460) as compact ``pairs.jsonl``.
"""

from __future__ import annotations

FAMILY_PREFIX = "gor"
FACTORY = "git-ops-recovery-factory"
GENERATOR = "grok-4.6"
RECORD_ID_PREFIX = FAMILY_PREFIX
QUOTA_PER_ROUND = 2
CATALOG_SCHEMA_ID = "gor-catalog-extract/v1"
SLICE_ID = "r946"
SLICE_MILL_ID = "gor-mill-r946"
DEFAULT_RUN_LABEL = "2026-08-19-agentic"
LEGACY_REF = "origin/legacy-mill-lane"
PRESERVE_COMMIT = "a2000438238dd1ac2b68b232430e6fb8f334b58f"
CATALOG_FILENAME = "CATALOG.json"
PAIRS_FILENAME = "pairs.jsonl"
DEFERRED_PAIR_ROWS = 961
BULKY_MILL_ID = "gor-mill-r1460"
BULKY_N_ROWS = 528
PAIR_IDENTITY_KEYS = (
    "fail_handoff",
    "fail_marker",
    "fail_slug",
    "fail_stem",
    "success_marker",
    "success_slug",
    "success_stem",
)
PAIR_ROW_KEYS = (
    "fail_handoff",
    "fail_marker",
    "fail_slug",
    "fail_stem",
    "i",
    "mill_id",
    "path",
    "success_marker",
    "success_slug",
    "success_stem",
)

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

SHAPE_LITERAL = "pairs-literal"
SHAPE_S_H = "pairs-s-h"
SHAPE_PLANT = "pairs-plant"
SHAPE_LEFTOVER_PLANT = "pairs-leftover-plant"
SHAPE_GITCFG = "pairs-gitcfg"
SHAPE_ADD = "pairs-add"

PAIR_CTOR_NAMES = frozenset(
    {"_S", "_H", "plant", "leftover_plant", "gitcfg", "cmdplant", "_cfg", "_cmd", "_pair"}
)
VENDOR_PREFIXES = ("gor-mill-", "gor-loop-", "_gen_gor_")
FORBIDDEN_MILL_GLOBS = (
    "gor-mill*.py",
    "gor-loop*.py",
    "_gen_gor_*.py",
    "gor_*_mill.py",
)

# Positional catalogs in r1460. Keyword-only constructors omit this map.
CTOR_POSARGS: dict[str, tuple[str, ...]] = {
    "_cfg": (
        "slug",
        "stem",
        "key",
        "bad",
        "good",
        "effect",
        "probe",
        "bad_obs",
        "good_obs",
        "wrong",
        "wrong_obs",
    ),
    "_cmd": (
        "slug",
        "stem",
        "knob",
        "effect",
        "map_cmd",
        "map_obs",
        "wrong",
        "wrong_obs",
        "rec_cmd",
        "rec_obs",
        "left_cmd",
        "left_obs",
    ),
}
