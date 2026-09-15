#!/usr/bin/env python3
"""The one place the ffd family reaches main's shared primitives.

Both import forms are supported (``ffd.x`` with ``pipelines/`` on
``sys.path``, and ``pipelines.ffd.x`` from the repository root). Every other
module in the package imports only its siblings and ``_contract``. Each module
ends with ``bind_import_twin(__name__)`` so the two spellings are one object.
"""

from __future__ import annotations

import json
from pathlib import Path

if __name__.startswith("pipelines."):
    from ..exact_json import ExactJSONFloat, dumps_exact_json
    from ..oracle_grounded import envelope, refusals
    from ..oracle_grounded.import_twins import bind_import_twin
    from ..raw_tree_guard import is_under_raw
    from ..tag_jsonutil import reject_duplicate_object_keys, reject_json_constant
else:
    from exact_json import ExactJSONFloat, dumps_exact_json
    from oracle_grounded import envelope, refusals
    from oracle_grounded.import_twins import bind_import_twin
    from raw_tree_guard import is_under_raw
    from tag_jsonutil import reject_duplicate_object_keys, reject_json_constant

FAMILY = "ffd"
FACTORY = "feature-flag-debug-factory"
PREFIX = "ffd"
GENERATOR = "grok-4.6"
CATALOG_FORMAT = "ffd-mill-catalog/1"
CATALOG_ID = "ffd-v1"
DEFAULT_CATALOG_REL = ("config", "ffd")
SOURCES = ("leftover3", "lll", "hop")
DECISION_BASIS_PREFIXES = ("Plan:", "Observation:", "Reflection:", "Tool call:")
BANNED_KEYS = ("thought", "chain_of_thought", "scratch", "inner_monologue")
MAX_DECISION_BASIS = 240
MAX_ROUND = 10_000

FINDING_CATALOG_FILE_MISSING = "CATALOG_FILE_MISSING"
FINDING_CATALOG_FIELD_MISSING = "CATALOG_FIELD_MISSING"
FINDING_CATALOG_FIELD_INVALID = "CATALOG_FIELD_INVALID"
FINDING_CATALOG_SHA256_MISMATCH = "CATALOG_SHA256_MISMATCH"
FINDING_SOURCE_UNKNOWN = "SOURCE_UNKNOWN"
FINDING_ROUND_OUT_OF_DOMAIN = "ROUND_OUT_OF_DOMAIN"
FINDING_PAIR_OUT_OF_DOMAIN = "PAIR_OUT_OF_DOMAIN"
FINDING_DESTINATION_EXISTS = "DESTINATION_EXISTS"
FINDING_DESTINATION_UNDER_RAW = "DESTINATION_UNDER_RAW"
FINDING_BANNED_KEY = "BANNED_KEY"
FINDING_DECISION_BASIS_INVALID = "DECISION_BASIS_INVALID"
FINDING_PLACEHOLDER_GOAL = "PLACEHOLDER_GOAL"
FINDING_PAIR_SHAPE = "PAIR_SHAPE"
FINDING_SLUG_COLLISION = "SLUG_COLLISION"
FINDING_SOURCE_UNPARSEABLE = "SOURCE_UNPARSEABLE"
FINDING_INPUT_NOT_AN_OBJECT = "INPUT_NOT_AN_OBJECT"

FINDING_CODES = (
    FINDING_CATALOG_FILE_MISSING,
    FINDING_CATALOG_FIELD_MISSING,
    FINDING_CATALOG_FIELD_INVALID,
    FINDING_CATALOG_SHA256_MISMATCH,
    FINDING_SOURCE_UNKNOWN,
    FINDING_ROUND_OUT_OF_DOMAIN,
    FINDING_PAIR_OUT_OF_DOMAIN,
    FINDING_DESTINATION_EXISTS,
    FINDING_DESTINATION_UNDER_RAW,
    FINDING_BANNED_KEY,
    FINDING_DECISION_BASIS_INVALID,
    FINDING_PLACEHOLDER_GOAL,
    FINDING_PAIR_SHAPE,
    FINDING_SLUG_COLLISION,
    FINDING_SOURCE_UNPARSEABLE,
    FINDING_INPUT_NOT_AN_OBJECT,
)
FINDING_CODE_SET = frozenset(FINDING_CODES)


class FfdRefusal(refusals.CodedRefusal):
    """The family's coded refusal: a ``ContractError`` whose ``str`` is ``CODE: prose``."""

    CODES = FINDING_CODE_SET


refuse, refuse_when, refuse_first = refusals.helpers(FfdRefusal)
shown = refusals.shown


def load_strict_json(payload: str | bytes):
    """Keep exact decimal tokens at catalog and record boundaries."""

    return json.loads(
        payload,
        object_pairs_hook=reject_duplicate_object_keys,
        parse_constant=reject_json_constant,
        parse_float=ExactJSONFloat,
    )


def default_catalog_dir() -> Path:
    return Path(__file__).resolve().parents[2].joinpath(*DEFAULT_CATALOG_REL)


__all__ = [
    "BANNED_KEYS",
    "CATALOG_FORMAT",
    "CATALOG_ID",
    "DECISION_BASIS_PREFIXES",
    "FACTORY",
    "FAMILY",
    "FINDING_CODE_SET",
    "FINDING_CODES",
    "FfdRefusal",
    "GENERATOR",
    "MAX_DECISION_BASIS",
    "MAX_ROUND",
    "PREFIX",
    "SOURCES",
    "bind_import_twin",
    "default_catalog_dir",
    "dumps_exact_json",
    "envelope",
    "is_under_raw",
    "load_strict_json",
    "refuse",
    "refuse_first",
    "refuse_when",
    "refusals",
    "shown",
]

bind_import_twin(__name__)
