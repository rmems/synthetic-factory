#!/usr/bin/env python3
"""The one place the ewr family reaches main's shared primitives.

Both import forms are supported (``ewr.x`` with ``pipelines/`` on
``sys.path``, and ``pipelines.ewr.x`` from the repository root). Every other
module in this package imports only its siblings and ``_contract``.
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

SCHEMA_ID = "ewr-catalog/v1"
FAMILY_PREFIX = "ewr"
FACTORY = "email-webhook-retry-factory"
GENERATOR = "grok-4.6"
START_ROUND = 40
N_ROUNDS = 16
QUOTA_PER_ROUND = 2
SUCCESS_STEPS = 16
HANDOFF_STEPS = 17
DEFAULT_CATALOG = Path("config") / "ewr" / "catalog.json"
LEGACY_PLANTS = "experiments/ewr_leftover3_plants.py"
LEGACY_MILL = "experiments/ewr_leftover3_mill.py"
LEGACY_COMMIT = "e1e3a79c2109d545f35d9cb9a3d7e021779522f4"
LEGACY_PLANTS_SHA256 = "cfe8e4334c7ae6f0d592e262fafa34bd7da590b2a1f24d59100f82284ffcbd2a"
LEGACY_MILL_SHA256 = "607ea5ed58611c410f8b7d5d5746c9d745588226e62646d77aa3b34676abfdbf"

BANNED_SLUG_TOKENS = ("beehiiv", "constant-contact", "invoice-row-dup")
BANNED_RECORD_KEYS = ("thought", "chain_of_thought", "scratch", "inner_monologue")
DECISION_PREFIXES = ("Plan:", "Observation:", "Reflection:", "Tool call:")
MAX_DECISION_BASIS = 240

FINDING_CATALOG_NOT_AN_OBJECT = "ewr.catalog.not_an_object"
FINDING_CATALOG_SCHEMA = "ewr.catalog.schema"
FINDING_CATALOG_FIELD_MISSING = "ewr.catalog.field_missing"
FINDING_CATALOG_FIELD_INVALID = "ewr.catalog.field_invalid"
FINDING_CATALOG_PAIR_COUNT = "ewr.catalog.pair_count"
FINDING_CATALOG_DUPLICATE = "ewr.catalog.duplicate"
FINDING_CATALOG_BANNED = "ewr.catalog.banned"
FINDING_CATALOG_PLANT = "ewr.catalog.plant"
FINDING_GENERATE_RAW_TREE = "ewr.generate.raw_tree"
FINDING_GENERATE_DEST_EXISTS = "ewr.generate.dest_exists"
FINDING_GENERATE_GOAL = "ewr.generate.goal"
FINDING_GENERATE_SHAPE = "ewr.generate.shape"
FINDING_GENERATE_HIDDEN = "ewr.generate.hidden_reasoning"
FINDING_GENERATE_ROUND = "ewr.generate.round"
FINDING_USAGE = "ewr.usage"

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


class EwrRefusal(refusals.CodedRefusal):
    """A coded refusal from the ewr catalog or generator."""

    CODES = FINDING_CODES


refuse, refuse_when, refuse_first = refusals.helpers(EwrRefusal)


def load_strict_json(payload: str | bytes):
    """Keep exact decimal tokens at ewr catalog and episode boundaries."""

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
    "BANNED_SLUG_TOKENS",
    "DECISION_PREFIXES",
    "DEFAULT_CATALOG",
    "EwrRefusal",
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
    "QUOTA_PER_ROUND",
    "SCHEMA_ID",
    "START_ROUND",
    "SUCCESS_STEPS",
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
