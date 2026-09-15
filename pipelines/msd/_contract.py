#!/usr/bin/env python3
"""Shared primitives and coded refusals for the ``msd`` mill package.

Both import forms are supported (``msd.x`` with ``pipelines/`` on
``sys.path``, and ``pipelines.msd.x`` from the repository root). Every
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

FACTORY = "mcp-tool-schema-drift-factory"
MILL_PREFIX = "msd"
GENERATOR = "msd-mill"
CATALOG_FORMAT = "msd-catalog/1"
RUN_FORMAT = "msd-run/1"
RECORD_KIND = "episode"
QUOTA_PER_ROUND = 2
DEFAULT_CATALOG_ID = "msd-plants-v1"
NOVEL_COVERAGE = "82%"
DECISION_PREFIXES = ("Plan:", "Observation:", "Reflection:", "Tool call:")

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

FINDING_CATALOG_FILE_MISSING = "msd.catalog_file_missing"
FINDING_CATALOG_FIELD_MISSING = "msd.catalog_field_missing"
FINDING_CATALOG_FIELD_INVALID = "msd.catalog_field_invalid"
FINDING_CATALOG_SHA256_MISMATCH = "msd.catalog_sha256_mismatch"
FINDING_PLANT_FIELD_MISSING = "msd.plant_field_missing"
FINDING_PLANT_FIELD_INVALID = "msd.plant_field_invalid"
FINDING_PLANT_DUPLICATE_ID = "msd.plant_duplicate_id"
FINDING_PLANT_NOT_FOUND = "msd.plant_not_found"
FINDING_MILL_NOT_FOUND = "msd.mill_not_found"
FINDING_FACTORY_NOT_REGISTERED = "msd.factory_not_registered"
FINDING_DESTINATION_EXISTS = "msd.destination_exists"
FINDING_DESTINATION_UNDER_RAW = "msd.destination_under_raw"
FINDING_SOURCE_NOT_PARSEABLE = "msd.source_not_parseable"
FINDING_BANNED_KEY = "msd.banned_key"
FINDING_USAGE = "msd.usage"
FINDING_ROUND_INVALID = "msd.round_invalid"

__all__ = [
    "BANNED_KEYS",
    "CATALOG_FILENAME",
    "CATALOG_FORMAT",
    "DECISION_PREFIXES",
    "DEFAULT_CATALOG_ID",
    "FACTORY",
    "GENERATOR",
    "MILL_PREFIX",
    "MsdRefusal",
    "NOTES_FILENAME",
    "NOVEL_COVERAGE",
    "PLANTS_FILENAME",
    "QUOTA_PER_ROUND",
    "RECORD_KIND",
    "RECORDS_FILENAME",
    "RUN_FILENAME",
    "RUN_FORMAT",
    "bind_import_twin",
    "dumps_exact_json",
    "is_under_raw",
    "load_strict_json",
    "repo_root",
]


class MsdRefusal(Exception):
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
