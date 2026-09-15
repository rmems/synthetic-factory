#!/usr/bin/env python3
"""Vocabulary for the ``lef`` mill family (llm-eval-flakiness lane).

The reviewed mill prefix ``lef`` maps to ``llm-eval-flakiness-factory`` in
``mill_reviewed_vocabulary.REVIEWED_MILL_PREFIX_HOMES``. PR-a extracted the
six flake-class catalogs from the 7 ``legacy-mill-lane`` scripts without
vendoring ``lef-mill*.py`` and without executing a publisher. The second
slice commits the deferred r728 and r968 table rows into ``rows.jsonl``.
The third slice AST-extracts Archive B ``mill_plants.py`` (r613–r620) into
``plants.jsonl`` without vendoring ``scripts/llm_eval_flakiness_mill/*``.
"""

from __future__ import annotations

FAMILY_PREFIX = "lef"
FACTORY = "llm-eval-flakiness-factory"
GENERATOR = "grok-4.6"
RECORD_ID_PREFIX = FAMILY_PREFIX
QUOTA_PER_ROUND = 2
CATALOG_SCHEMA_ID = "lef-catalog-extract/v1"
SLICE_ID = "full"
DEFAULT_RUN_LABEL = "2026-08-19-agentic"
LEGACY_REF = "origin/legacy-mill-lane"
PRESERVE_COMMIT = "02d05373e4144ab609ec141b28fd4c52a4174f21"
CATALOG_FILENAME = "CATALOG.json"
ROWS_FILENAME = "rows.jsonl"
SLICE_MILL_ID = "lef-mill-r629"
COMMITTED_MILL_IDS = ("lef-mill-r629", "lef-mill-r728", "lef-mill-r968")
COMMITTED_ROW_COUNT = 682
PAIR_BUCKETS = 3

ARCHIVE_B_COMMIT = "813f93f1969c1c4421e5663492e9663739efa642"
PLANTS_SOURCE_PATH = "scripts/llm_eval_flakiness_mill/mill_plants.py"
PLANTS_MILL_ID = "lef-mill-plants-a"
PLANTS_CATALOG_FIRST = 613
PLANTS_PAIR_COUNT = 8
PLANTS_FILENAME = "plants.jsonl"
PLANTS_BLOB_SHA = "98bf17417e6d5e25651c48febf09248b1ecabd34"
OK_CALL = "_ok"
BAD_CALL = "_bad"

KIND_TABLES = "tables"
KIND_STEMS = "stems"
KIND_LOOP = "loop"
KIND_SLUGS = "slugs"
KIND_PLANTS = "plants"

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
    "mill_plants.py",
    "mill_plants_*.py",
    "mill_gen.py",
    "mill.py",
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
