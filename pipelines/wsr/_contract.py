#!/usr/bin/env python3
"""Pinned identity for the websocket-reconnect leftover3 family (prefix ``wsr``).

Constants are AST-extracted from ``wsr-mill-leftover3-r41`` on
``origin/legacy-mill-lane``. Plants live in that mill; there is no separate
``wsr_*plants.py``. This module is the only place the family names the
factory, generator, banned slugs, and source pin.
"""

from __future__ import annotations

import json
from pathlib import Path

if __name__.startswith("pipelines."):
    from ..curate_coding import contains_hidden_reasoning_key
    from ..exact_json import ExactJSONFloat, dumps_exact_json
    from ..oracle_grounded import refusals
    from ..oracle_grounded.import_twins import bind_import_twin
    from ..raw_tree_guard import is_under_raw
    from ..tag_jsonutil import reject_duplicate_object_keys, reject_json_constant
else:
    from curate_coding import contains_hidden_reasoning_key
    from exact_json import ExactJSONFloat, dumps_exact_json
    from oracle_grounded import refusals
    from oracle_grounded.import_twins import bind_import_twin
    from raw_tree_guard import is_under_raw
    from tag_jsonutil import reject_duplicate_object_keys, reject_json_constant

SCHEMA_ID = "wsr-catalog/v1"
FAMILY_PREFIX = "wsr"
FACTORY = "websocket-reconnect-factory"
GENERATOR = "grok-4.6"
START_ROUND = 41
N_ROUNDS = 16
QUOTA_PER_ROUND = 2
SUCCESS_STEPS = 16
HANDOFF_STEPS = 17
DEFAULT_CATALOG = Path("config") / "wsr" / "catalog.json"
LEGACY_PLANTS = "experiments/wsr-mill-leftover3-r41.py"
LEGACY_MILL = LEGACY_PLANTS
LEGACY_COMMIT = "fec0f5f398a4cf22a5f6c2b2ef4cdc89b6d00202"
LEGACY_PLANTS_SHA256 = "7a01aeebabccee9ac1ce38216463012321367483578af6f52cc09e704c4b4b82"
LEGACY_MILL_SHA256 = LEGACY_PLANTS_SHA256

BANNED_SLUGS = frozenset(
    {
        "anycable-restore-session",
        "reverb-activity-timeout-handoff",
        "cookie-replay",
    }
)
BANNED_SLUG_TOKENS = ("anycable", "reverb", "cookie-replay")
BANNED_RECORD_KEYS = ("thought", "chain_of_thought", "scratch", "inner_monologue")
DECISION_PREFIXES = ("Plan:", "Observation:", "Reflection:", "Tool call:")
MAX_DECISION_BASIS = 240
PLACEHOLDER_GOALS = frozenset({"x", "placeholder", "todo", "tbd", "fix it"})

FINDING_CATALOG_NOT_AN_OBJECT = "wsr.catalog.not_an_object"
FINDING_CATALOG_SCHEMA = "wsr.catalog.schema"
FINDING_CATALOG_FIELD_MISSING = "wsr.catalog.field_missing"
FINDING_CATALOG_FIELD_INVALID = "wsr.catalog.field_invalid"
FINDING_CATALOG_PAIR_COUNT = "wsr.catalog.pair_count"
FINDING_CATALOG_DUPLICATE = "wsr.catalog.duplicate"
FINDING_CATALOG_BANNED = "wsr.catalog.banned"
FINDING_CATALOG_PLANT = "wsr.catalog.plant"
FINDING_GENERATE_RAW_TREE = "wsr.generate.raw_tree"
FINDING_GENERATE_DEST_EXISTS = "wsr.generate.dest_exists"
FINDING_GENERATE_GOAL = "wsr.generate.goal"
FINDING_GENERATE_SHAPE = "wsr.generate.shape"
FINDING_GENERATE_HIDDEN = "wsr.generate.hidden_reasoning"
FINDING_GENERATE_ROUND = "wsr.generate.round"
FINDING_USAGE = "wsr.usage"

FINDING_CODES = frozenset(
    {
        FINDING_CATALOG_NOT_AN_OBJECT,
        FINDING_CATALOG_SCHEMA,
        FINDING_CATALOG_FIELD_MISSING,
        FINDING_CATALOG_FIELD_INVALID,
        FINDING_CATALOG_PAIR_COUNT,
        FINDING_CATALOG_DUPLICATE,
        FINDING_CATALOG_BANNED,
        FINDING_CATALOG_PLANT,
        FINDING_GENERATE_RAW_TREE,
        FINDING_GENERATE_DEST_EXISTS,
        FINDING_GENERATE_GOAL,
        FINDING_GENERATE_SHAPE,
        FINDING_GENERATE_HIDDEN,
        FINDING_GENERATE_ROUND,
        FINDING_USAGE,
    }
)


class WsrRefusal(refusals.CodedRefusal):
    """A coded refusal from the wsr catalog or generator."""

    CODES = FINDING_CODES


refuse, refuse_when, refuse_first = refusals.helpers(WsrRefusal)


def load_strict_json(payload: str | bytes):
    """Keep exact decimal tokens at wsr catalog and episode boundaries."""

    return json.loads(
        payload,
        object_pairs_hook=reject_duplicate_object_keys,
        parse_constant=reject_json_constant,
        parse_float=ExactJSONFloat,
    )


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def default_catalog_path(root: Path | None = None) -> Path:
    return (root or repo_root()) / DEFAULT_CATALOG


__all__ = [
    "BANNED_RECORD_KEYS",
    "BANNED_SLUGS",
    "BANNED_SLUG_TOKENS",
    "DECISION_PREFIXES",
    "DEFAULT_CATALOG",
    "FACTORY",
    "FAMILY_PREFIX",
    "FINDING_CODES",
    "GENERATOR",
    "HANDOFF_STEPS",
    "LEGACY_COMMIT",
    "LEGACY_MILL",
    "LEGACY_MILL_SHA256",
    "LEGACY_PLANTS",
    "LEGACY_PLANTS_SHA256",
    "MAX_DECISION_BASIS",
    "N_ROUNDS",
    "PLACEHOLDER_GOALS",
    "QUOTA_PER_ROUND",
    "SCHEMA_ID",
    "START_ROUND",
    "SUCCESS_STEPS",
    "WsrRefusal",
    "bind_import_twin",
    "contains_hidden_reasoning_key",
    "default_catalog_path",
    "dumps_exact_json",
    "is_under_raw",
    "load_strict_json",
    "refuse",
    "refuse_first",
    "refuse_when",
    "repo_root",
]


bind_import_twin(__name__)
