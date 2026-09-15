#!/usr/bin/env python3
"""The one place the dbm family reaches main's shared primitives.

Both import forms are supported (``dbm.x`` with ``pipelines/`` on
``sys.path``, and ``pipelines.dbm.x`` from the repository root). Every other
module in this package imports only its siblings and ``_contract``.
"""

from __future__ import annotations

import json
from pathlib import Path

if __name__.startswith("pipelines."):
    from ..curate_coding import contains_hidden_reasoning_key
    from ..exact_json import ExactJSONFloat, dumps_exact_json
    from ..mill_family import REVIEWED_MILL_PREFIX_HOMES
    from ..oracle_grounded import refusals
    from ..oracle_grounded.import_twins import bind_import_twin
    from ..raw_tree_guard import is_under_raw
    from ..tag_jsonutil import reject_duplicate_object_keys, reject_json_constant
else:
    from curate_coding import contains_hidden_reasoning_key
    from exact_json import ExactJSONFloat, dumps_exact_json
    from mill_family import REVIEWED_MILL_PREFIX_HOMES
    from oracle_grounded import refusals
    from oracle_grounded.import_twins import bind_import_twin
    from raw_tree_guard import is_under_raw
    from tag_jsonutil import reject_duplicate_object_keys, reject_json_constant

SCHEMA_LEFTOVER3 = "dbm-leftover3/v1"
SCHEMA_MILLS = "dbm-mills/v1"
FAMILY_PREFIX = "dbm"
FACTORY = "db-migration-repair-factory"
GENERATOR = "grok-4.6"
START_ROUND = 1260
N_PAIRS = 17
QUOTA_PER_ROUND = 2
SUCCESS_STEPS = 16
COVERAGE_FLOOR = 52
MILL_COUNT = 9
MILL_PAIRS = 601
MILL_PLANTS = 1202
DEFAULT_LEFTOVER3 = Path("config") / "dbm" / "leftover3.json"
DEFAULT_MILLS = Path("config") / "dbm" / "mills.json"
LEGACY_LANE = "legacy-mill-lane"
LEGACY_COMMIT = "813f93f1969c1c4421e5663492e9663739efa642"
LEGACY_LEFTOVER3 = "experiments/unique_dbm_leftover3_mill.py"
LEGACY_LEFTOVER3_SHA256 = "a435d7c9d5340ad1065b9821476736e04238e6aa4b29e720a64b6dc57a607631"
LEGACY_PLANTS_GEN = "experiments/_gen_dbm_plants_r1340.py"
LEGACY_PLANTS_GEN_SHA256 = "7f92115d076506a130efdfaca422242ca246b1cf0c75e327878c4e6970e0d704"
BANNED_KEYS = ("thought", "chain_of_thought", "scratch", "inner_monologue")
ENGINES = (
    "alembic",
    "atlas",
    "dbmate",
    "django",
    "expand-contract",
    "flyway",
    "gh-ost",
    "golang-migrate",
    "goose",
    "liquibase",
    "pgroll",
    "prisma",
    "pt-osc",
    "skeema",
    "sqitch",
    "vitess",
)
PLANT_KEYS = (
    "engine",
    "slug",
    "plant",
    "surface",
    "table",
    "col",
    "col_v2",
    "leftover",
    "leftover2",
    "seed",
    "fail",
    "inspect",
    "catalog",
    "abort",
    "col_type",
    "lock_fail",
)
CONSTRUCTORS = frozenset({"P", "Q", "R", "pl"})
REVIEWED_HOME = REVIEWED_MILL_PREFIX_HOMES[FAMILY_PREFIX]
if REVIEWED_HOME != FACTORY:  # pragma: no cover - the table pin is the authority
    raise ImportError(
        f"reviewed prefix home for {FAMILY_PREFIX!r} is {REVIEWED_HOME!r}, "
        f"not the dbm factory {FACTORY!r}"
    )

FINDING_CATALOG_NOT_AN_OBJECT = "dbm.catalog.not_an_object"
FINDING_CATALOG_SCHEMA = "dbm.catalog.schema"
FINDING_CATALOG_FIELD_MISSING = "dbm.catalog.field_missing"
FINDING_CATALOG_FIELD_INVALID = "dbm.catalog.field_invalid"
FINDING_CATALOG_PAIR_COUNT = "dbm.catalog.pair_count"
FINDING_CATALOG_DUPLICATE = "dbm.catalog.duplicate"
FINDING_CATALOG_PLANT = "dbm.catalog.plant"
FINDING_CATALOG_ENGINE = "dbm.catalog.engine"
FINDING_GENERATE_RAW_TREE = "dbm.generate.raw_tree"
FINDING_GENERATE_DEST_EXISTS = "dbm.generate.dest_exists"
FINDING_GENERATE_GOAL = "dbm.generate.goal"
FINDING_GENERATE_SHAPE = "dbm.generate.shape"
FINDING_GENERATE_HIDDEN = "dbm.generate.hidden_reasoning"
FINDING_GENERATE_ROUND = "dbm.generate.round"
FINDING_USAGE = "dbm.usage"

FINDING_CODES = frozenset(
    {
        FINDING_CATALOG_NOT_AN_OBJECT,
        FINDING_CATALOG_SCHEMA,
        FINDING_CATALOG_FIELD_MISSING,
        FINDING_CATALOG_FIELD_INVALID,
        FINDING_CATALOG_PAIR_COUNT,
        FINDING_CATALOG_DUPLICATE,
        FINDING_CATALOG_PLANT,
        FINDING_CATALOG_ENGINE,
        FINDING_GENERATE_RAW_TREE,
        FINDING_GENERATE_DEST_EXISTS,
        FINDING_GENERATE_GOAL,
        FINDING_GENERATE_SHAPE,
        FINDING_GENERATE_HIDDEN,
        FINDING_GENERATE_ROUND,
        FINDING_USAGE,
    }
)


class DbmRefusal(refusals.CodedRefusal):
    """A coded refusal from the dbm catalog or generator."""

    CODES = FINDING_CODES


refuse, refuse_when, refuse_first = refusals.helpers(DbmRefusal)


def load_strict_json(payload: str | bytes):
    """Keep exact decimal tokens at dbm catalog and episode boundaries."""

    return json.loads(
        payload,
        object_pairs_hook=reject_duplicate_object_keys,
        parse_constant=reject_json_constant,
        parse_float=ExactJSONFloat,
    )


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def leftover3_path(root: Path | None = None) -> Path:
    return (root or repo_root()) / DEFAULT_LEFTOVER3


def mills_path(root: Path | None = None) -> Path:
    return (root or repo_root()) / DEFAULT_MILLS


__all__ = [
    "BANNED_KEYS",
    "CONSTRUCTORS",
    "COVERAGE_FLOOR",
    "DEFAULT_LEFTOVER3",
    "DEFAULT_MILLS",
    "DbmRefusal",
    "ENGINES",
    "FACTORY",
    "FAMILY_PREFIX",
    "FINDING_CODES",
    "GENERATOR",
    "LEGACY_COMMIT",
    "LEGACY_LANE",
    "LEGACY_LEFTOVER3",
    "LEGACY_LEFTOVER3_SHA256",
    "LEGACY_PLANTS_GEN",
    "LEGACY_PLANTS_GEN_SHA256",
    "MILL_COUNT",
    "MILL_PAIRS",
    "MILL_PLANTS",
    "N_PAIRS",
    "PLANT_KEYS",
    "QUOTA_PER_ROUND",
    "REVIEWED_HOME",
    "SCHEMA_LEFTOVER3",
    "SCHEMA_MILLS",
    "START_ROUND",
    "SUCCESS_STEPS",
    "bind_import_twin",
    "contains_hidden_reasoning_key",
    "dumps_exact_json",
    "is_under_raw",
    "leftover3_path",
    "load_strict_json",
    "mills_path",
    "refuse",
    "refuse_first",
    "refuse_when",
    "repo_root",
]


bind_import_twin(__name__)
