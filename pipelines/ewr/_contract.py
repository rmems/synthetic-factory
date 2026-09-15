#!/usr/bin/env python3
"""The one place the ewr family reaches main's shared primitives.

Both import forms are supported (``ewr.x`` with ``pipelines/`` on
``sys.path``, and ``pipelines.ewr.x`` from the repository root). Every other
module in this package imports only its siblings and ``_contract``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
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

SCHEMA_ID = "ewr-catalog/v2"
FAMILY_PREFIX = "ewr"
FACTORY = "email-webhook-retry-factory"
GENERATOR = "grok-4.6"
START_ROUND = 40
N_PLANT_PAIRS = 16
N_MAPPING_PAIRS = 16
N_MILLS = 2
N_PAIRS = N_PLANT_PAIRS + N_MAPPING_PAIRS
QUOTA_PER_ROUND = 2
SUCCESS_STEPS = 16
HANDOFF_STEPS = 17
DEFAULT_CATALOG = Path("config") / "ewr" / "CATALOG.json"
PAIRS_FILENAME = "pairs.jsonl"
LEGACY_LANE = "legacy-mill-lane"
LEGACY_COMMIT = "813f93f1969c1c4421e5663492e9663739efa642"
PLANTS_MILL_ID = "ewr-leftover3-r40"
MAPPING_MILL_ID = "ewr-lll-r56"
LEGACY_PLANTS = "experiments/ewr_leftover3_plants.py"
LEGACY_MILL = "experiments/ewr_leftover3_mill.py"
LEGACY_MAPPING_MILL = "experiments/mill_leftover_leftover_leftover_r56.py"
LEGACY_PLANTS_SHA256 = "cfe8e4334c7ae6f0d592e262fafa34bd7da590b2a1f24d59100f82284ffcbd2a"
LEGACY_MILL_SHA256 = "607ea5ed58611c410f8b7d5d5746c9d745588226e62646d77aa3b34676abfdbf"
LEGACY_MAPPING_MILL_SHA256 = "38a1304441ecb930579fe3e3fc065e704c3f18db746170c103c3965769f84fb5"
PAIRS_SHA256 = "851928c4c83b87f04beaa676e5d176704c59f31e6593ccb57cf38d5eaa3f3c2c"

MAPPING_FIELDS = frozenset(
    {
        "slug",
        "fail",
        "mod",
        "drop",
        "esp",
        "idf",
        "evf",
        "naive",
        "doc",
        "doc2",
        "domain",
        "stack",
        "ticket",
        "test_ok",
        "test_fail",
        "short",
        "dshort",
    }
)

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
FINDING_CATALOG_MILL = "ewr.catalog.mill"
FINDING_PAIRS_SHA_MISMATCH = "ewr.catalog.pairs_sha"
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
        FINDING_CATALOG_MILL,
        FINDING_PAIRS_SHA_MISMATCH,
        FINDING_GENERATE_RAW_TREE,
        FINDING_GENERATE_DEST_EXISTS,
        FINDING_GENERATE_GOAL,
        FINDING_GENERATE_SHAPE,
        FINDING_GENERATE_HIDDEN,
        FINDING_GENERATE_ROUND,
        FINDING_USAGE,
    }
)


@dataclass(frozen=True)
class MillPin:
    mill_id: str
    source_format: str
    mill_path: str
    mill_sha256: str
    plants_path: str | None
    plants_sha256: str | None
    catalog_first: int
    n_pairs: int


MILL_SOURCES: tuple[MillPin, ...] = (
    MillPin(
        PLANTS_MILL_ID,
        "plants-v1",
        LEGACY_MILL,
        LEGACY_MILL_SHA256,
        LEGACY_PLANTS,
        LEGACY_PLANTS_SHA256,
        START_ROUND,
        N_PLANT_PAIRS,
    ),
    MillPin(
        MAPPING_MILL_ID,
        "mapping-v1",
        LEGACY_MAPPING_MILL,
        LEGACY_MAPPING_MILL_SHA256,
        None,
        None,
        56,
        N_MAPPING_PAIRS,
    ),
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


def load_pair_json(payload: str | bytes):
    """Load compact pair rows; plant coverage integers stay plain Python ints."""

    return json.loads(
        payload,
        object_pairs_hook=reject_duplicate_object_keys,
        parse_constant=reject_json_constant,
    )


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def default_catalog_path(root: Path | None = None) -> Path:
    return (root or repo_root()) / DEFAULT_CATALOG


def default_pairs_path(catalog_path: Path) -> Path:
    return catalog_path.parent / PAIRS_FILENAME


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
    "LEGACY_LANE",
    "LEGACY_MAPPING_MILL",
    "LEGACY_MAPPING_MILL_SHA256",
    "LEGACY_MILL",
    "LEGACY_MILL_SHA256",
    "LEGACY_PLANTS",
    "LEGACY_PLANTS_SHA256",
    "MAPPING_FIELDS",
    "MAPPING_MILL_ID",
    "MAX_DECISION_BASIS",
    "MILL_SOURCES",
    "MillPin",
    "N_MAPPING_PAIRS",
    "N_MILLS",
    "N_PAIRS",
    "N_PLANT_PAIRS",
    "PAIRS_FILENAME",
    "PAIRS_SHA256",
    "PLANTS_MILL_ID",
    "QUOTA_PER_ROUND",
    "SCHEMA_ID",
    "START_ROUND",
    "SUCCESS_STEPS",
    "bind_import_twin",
    "contains_hidden_reasoning_key",
    "default_catalog_path",
    "default_pairs_path",
    "dumps_exact_json",
    "is_under_raw",
    "load_pair_json",
    "load_strict_json",
    "refuse",
    "refuse_first",
    "refuse_when",
    "repo_root",
]


bind_import_twin(__name__)
