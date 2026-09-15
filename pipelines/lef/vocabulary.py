#!/usr/bin/env python3
"""Vocabulary for the ``lef`` mill family (llm-eval-flakiness lane).

The reviewed mill prefix ``lef`` maps to ``llm-eval-flakiness-factory`` in
``mill_reviewed_vocabulary.REVIEWED_MILL_PREFIX_HOMES``. PR-a extracts the
six flake-class catalogs from the 7 ``legacy-mill-lane`` scripts without
vendoring ``lef-mill*.py`` and without executing a publisher.
"""

from __future__ import annotations

FAMILY_PREFIX = "lef"
FACTORY = "llm-eval-flakiness-factory"
GENERATOR = "grok-4.6"
RECORD_ID_PREFIX = FAMILY_PREFIX
QUOTA_PER_ROUND = 2
CATALOG_SCHEMA_ID = "lef-catalog-extract/v1"
SLICE_ID = "r629"
DEFAULT_RUN_LABEL = "2026-08-19-agentic"
LEGACY_REF = "origin/legacy-mill-lane"
PRESERVE_COMMIT = "02d05373e4144ab609ec141b28fd4c52a4174f21"
CATALOG_FILENAME = "CATALOG.json"
ROWS_FILENAME = "rows.jsonl"
SLICE_MILL_ID = "lef-mill-r629"
PAIR_BUCKETS = 3

KIND_TABLES = "tables"
KIND_STEMS = "stems"
KIND_LOOP = "loop"
KIND_SLUGS = "slugs"

SHAPE_TABLES = "six-tables"
SHAPE_STEMS = "stems"

TABLE_NAMES = (
    "CACHE_OK",
    "LAST_BAD",
    "SEED_OK",
    "TEMP0_BAD",
    "ALIAS_OK",
    "TRUNC_BAD",
)
TRUNC_MORE_NAME = "_TRUNC_MORE"

TABLE_FIELDS = {
    "CACHE_OK": (
        "slug",
        "field",
        "hi",
        "lo",
        "mid",
        "old_val",
        "new_val",
        "avoided",
        "ticket",
    ),
    "LAST_BAD": (
        "slug",
        "window",
        "last_hi",
        "early_lo",
        "mid",
        "unit_last",
        "unit_early",
        "avoided",
        "ticket",
    ),
    "SEED_OK": ("slug", "leak", "item", "hi", "lo", "mid", "avoided", "ticket"),
    "TEMP0_BAD": (
        "slug",
        "sampler",
        "avoided",
        "ticket",
        "vary_lo",
        "pub_hi",
        "mid",
    ),
    "ALIAS_OK": (
        "slug",
        "alias_from",
        "alias_to",
        "canonical",
        "hi",
        "lo",
        "mid",
        "avoided",
        "ticket",
    ),
    "TRUNC_BAD": (
        "slug",
        "limit_now",
        "limit_wrong",
        "avoided",
        "ticket",
        "pub_hi",
        "true_lo",
        "mid",
    ),
}

FLAKE_CLASSES = (
    "cache-key omitted field",
    "judge last-pair-only",
    "seed leak",
    "temperature=0 still samples",
    "rubric aliasing",
    "tool-output truncation",
)

BANNED_KEYS = ("thought", "chain_of_thought", "scratch", "inner_monologue")

NUMS_FORMULA = {
    "hi": {"base": 0.86, "mod": 8, "step": 0.01, "ndigits": 2},
    "lo": {"base": 0.14, "mod": 9, "step": 0.01, "ndigits": 2},
    "mid": {"base": 0.70, "mod": 7, "step": 0.01, "ndigits": 2},
}

VENDOR_PREFIXES = ("lef-mill-", "lef-loop-")
FORBIDDEN_MILL_GLOBS = (
    "lef-mill*.py",
    "lef-loop*.py",
)
SLUGS_FILENAME = ".lef-used-slugs.txt"
CATALOG_ASSIGNMENT_NAMES = frozenset(
    {
        "FACTORY",
        "GEN",
        "CATALOG_FIRST",
        "BANNED_SNIPPETS",
        "BANNED_KEYS",
        "BANNED_SLUGS",
        "STEMS",
        "FROMS",
        "CANONS",
        "LIMS",
        TRUNC_MORE_NAME,
        *TABLE_NAMES,
    }
)
