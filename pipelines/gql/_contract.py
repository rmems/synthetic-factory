#!/usr/bin/env python3
"""Shared primitives and coded refusals for the ``gql`` mill package.

Both import forms are supported (``gql.x`` with ``pipelines/`` on
``sys.path``, and ``pipelines.gql.x`` from the repository root). Every
module ends with ``bind_import_twin(__name__)`` so the two spellings are
one object.
"""

from __future__ import annotations

import json
from pathlib import Path

if __name__.startswith("pipelines."):
    from ..exact_json import ExactJSONFloat, dumps_exact_json
    from ..oracle_grounded.import_twins import bind_import_twin
    from ..raw_tree_guard import is_under_raw
    from ..tag_jsonutil import reject_duplicate_object_keys, reject_json_constant
else:
    from exact_json import ExactJSONFloat, dumps_exact_json
    from oracle_grounded.import_twins import bind_import_twin
    from raw_tree_guard import is_under_raw
    from tag_jsonutil import reject_duplicate_object_keys, reject_json_constant

FACTORY = "graphql-nplusone-factory"
MILL_PREFIX = "gql"
GENERATOR = "gql-mill"
CATALOG_FORMAT = "gql-catalog/1"
RUN_FORMAT = "gql-run/1"
RECORD_KIND = "episode"
QUOTA_PER_ROUND = 2
DEFAULT_CATALOG_ID = "gql-plants-v1"
SHAPE_PAIR = "pair"
SHAPE_SURFACE = "surface"

CATALOG_FILENAME = "CATALOG.json"
PLANTS_FILENAME = "plants.jsonl"
RECORDS_FILENAME = "records.jsonl"
RUN_FILENAME = "RUN.json"
NOTES_FILENAME = "NOTES.md"

BANNED_KEYS = frozenset(
    {
        "thought",
        "chain_of_thought",
        "scratch",
        "inner_monologue",
        "spike_events",
    }
)

# Union of leftover-clone tokens the r211/r216 mills refused in slugs.
BANNED_SLUG_TOKENS = frozenset(
    {
        "httpget",
        "specifiedby",
        "deprecated-reason",
        "collectfields",
        "parseliteral",
        "getargumentvalues",
        "getfielddef",
        "completelistvalue",
        "typeinfo-leftover",
        "shouldinclude",
        "getvariablevalues",
        "valuefromast",
        "getoperationast",
        "buildexecutioncontext",
        "executefieldsserially",
        "completevalue",
        "getdirectivevalues",
        "memoize3",
        "astfromvalue",
        "rename-object-fields",
        "mesh-leftover-prefix",
        "mesh-leftover",
        "wrap-fields",
        "mesh-leftover-mock",
        "mesh-leftover-federation",
        "oneof-input",
        "hasnext",
        "dataloader-prime",
        "dataloader-cache-key",
        "apq-persisted",
        "stream-initialcount",
        "federation-entities",
        "defer-label",
        "strawberry-context-loader",
        "mercurius-preeexec",
    }
)

FINDING_CATALOG_FILE_MISSING = "gql.catalog_file_missing"
FINDING_CATALOG_FIELD_MISSING = "gql.catalog_field_missing"
FINDING_CATALOG_FIELD_INVALID = "gql.catalog_field_invalid"
FINDING_CATALOG_SHA256_MISMATCH = "gql.catalog_sha256_mismatch"
FINDING_PLANT_FIELD_MISSING = "gql.plant_field_missing"
FINDING_PLANT_FIELD_INVALID = "gql.plant_field_invalid"
FINDING_PLANT_DUPLICATE_ID = "gql.plant_duplicate_id"
FINDING_PLANT_NOT_FOUND = "gql.plant_not_found"
FINDING_MILL_NOT_FOUND = "gql.mill_not_found"
FINDING_FACTORY_NOT_REGISTERED = "gql.factory_not_registered"
FINDING_DESTINATION_EXISTS = "gql.destination_exists"
FINDING_DESTINATION_UNDER_RAW = "gql.destination_under_raw"
FINDING_SOURCE_NOT_PARSEABLE = "gql.source_not_parseable"
FINDING_BANNED_KEY = "gql.banned_key"
FINDING_USAGE = "gql.usage"
FINDING_ROUND_INVALID = "gql.round_invalid"

__all__ = [
    "BANNED_KEYS",
    "BANNED_SLUG_TOKENS",
    "CATALOG_FILENAME",
    "CATALOG_FORMAT",
    "DEFAULT_CATALOG_ID",
    "FACTORY",
    "GENERATOR",
    "GqlRefusal",
    "MILL_PREFIX",
    "NOTES_FILENAME",
    "PLANTS_FILENAME",
    "QUOTA_PER_ROUND",
    "RECORD_KIND",
    "RECORDS_FILENAME",
    "RUN_FILENAME",
    "RUN_FORMAT",
    "SHAPE_PAIR",
    "SHAPE_SURFACE",
    "bind_import_twin",
    "dumps_exact_json",
    "is_under_raw",
    "load_strict_json",
    "repo_root",
]


class GqlRefusal(Exception):
    """A coded, fail-closed refusal. ``str`` is ``CODE: prose``."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_strict_json(payload: str | bytes):
    """Keep exact decimal tokens at catalog and record boundaries."""

    return json.loads(
        payload,
        object_pairs_hook=reject_duplicate_object_keys,
        parse_constant=reject_json_constant,
        parse_float=ExactJSONFloat,
    )


bind_import_twin(__name__)
