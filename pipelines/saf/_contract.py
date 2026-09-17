#!/usr/bin/env python3
"""Shared primitives and coded refusals for the ``saf`` mill package.

Both import forms are supported (``saf.x`` with ``pipelines/`` on
``sys.path``, and ``pipelines.saf.x`` from the repository root). Every
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

FACTORY = "safety-calibration-factory"
MILL_PREFIX = "saf"
GENERATOR = "saf-mill"
CATALOG_FORMAT = "saf-catalog/1"
RUN_FORMAT = "saf-run/1"
RECORD_KIND = "safety_case"
QUOTA_PER_ROUND = 2
DEFAULT_CATALOG_ID = "saf-pairs-v1"
SOURCE_MILL_ID = "saf_r5045"
SOURCE_ROUND = 5045
SOURCE_REF = "legacy-mill-lane"
SOURCE_PATH = "experiments/saf_r5045_leftover_leftover_leftover_mill.py"
SOURCE_COMMIT = "6fe337661de77b0dcc71e686578ddb0fa01e5863"
NOVEL_COVERAGE = "86%"

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

BANNED_ID_PREFIXES = ("sir-", "dbc-")

FLAVORS = (
    "tool-output",
    "README",
    "over-refusal",
    "clarify",
    "escalate",
)

PAIR_KEYS = (
    "flavor",
    "slug",
    "twin",
    "plant",
    "mutate",
    "flag",
    "readonly",
    "runbook",
    "policy",
    "owner",
    "safe",
    "trigger",
    "ticket",
    "dest",
    "extra",
)

FINDING_CATALOG_FILE_MISSING = "saf.catalog_file_missing"
FINDING_CATALOG_FIELD_MISSING = "saf.catalog_field_missing"
FINDING_CATALOG_FIELD_INVALID = "saf.catalog_field_invalid"
FINDING_CATALOG_SHA256_MISMATCH = "saf.catalog_sha256_mismatch"
FINDING_PLANT_FIELD_MISSING = "saf.plant_field_missing"
FINDING_PLANT_FIELD_INVALID = "saf.plant_field_invalid"
FINDING_PLANT_DUPLICATE_ID = "saf.plant_duplicate_id"
FINDING_PLANT_NOT_FOUND = "saf.plant_not_found"
FINDING_MILL_NOT_FOUND = "saf.mill_not_found"
FINDING_FACTORY_NOT_REGISTERED = "saf.factory_not_registered"
FINDING_DESTINATION_EXISTS = "saf.destination_exists"
FINDING_DESTINATION_UNDER_RAW = "saf.destination_under_raw"
FINDING_SOURCE_NOT_PARSEABLE = "saf.source_not_parseable"
FINDING_BANNED_KEY = "saf.banned_key"
FINDING_BANNED_ID = "saf.banned_id"
FINDING_USAGE = "saf.usage"
FINDING_ROUND_INVALID = "saf.round_invalid"

__all__ = [
    "BANNED_ID_PREFIXES",
    "BANNED_KEYS",
    "CATALOG_FILENAME",
    "CATALOG_FORMAT",
    "DEFAULT_CATALOG_ID",
    "FACTORY",
    "FLAVORS",
    "GENERATOR",
    "MILL_PREFIX",
    "NOTES_FILENAME",
    "NOVEL_COVERAGE",
    "PAIR_KEYS",
    "PLANTS_FILENAME",
    "QUOTA_PER_ROUND",
    "RECORD_KIND",
    "RECORDS_FILENAME",
    "RUN_FILENAME",
    "RUN_FORMAT",
    "SOURCE_COMMIT",
    "SOURCE_MILL_ID",
    "SOURCE_PATH",
    "SOURCE_REF",
    "SOURCE_ROUND",
    "SafRefusal",
    "bind_import_twin",
    "dumps_exact_json",
    "is_under_raw",
    "load_strict_json",
    "repo_root",
]


class SafRefusal(Exception):
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
