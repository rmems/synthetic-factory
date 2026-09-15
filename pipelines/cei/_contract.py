#!/usr/bin/env python3
"""Shared primitives and coded refusals for the ``cei`` mill package.

Both import forms are supported (``cei.x`` with ``pipelines/`` on
``sys.path``, and ``pipelines.cei.x`` from the repository root). Every
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

FACTORY = "csv-excel-ingest-factory"
MILL_PREFIX = "cei"
GENERATOR = "cei-mill"
CATALOG_FORMAT = "cei-catalog/1"
RUN_FORMAT = "cei-run/1"
RECORD_KIND = "episode"
QUOTA_PER_ROUND = 2
DEFAULT_CATALOG_ID = "cei-pairs-v1"
SOURCE_MILL_ID = "cei_r81"
SOURCE_ROUND = 81
SOURCE_REF = "legacy-mill-lane"
SOURCE_PATH = "experiments/cei-mill-r81.py"
SOURCE_COMMIT = "cf63f18e63ca9469246145c1eec9388199d60b47"
NOVEL_COVERAGE_OK = 84
NOVEL_COVERAGE_BAD = 83

CATALOG_FILENAME = "CATALOG.json"
PLANTS_FILENAME = "plants.jsonl"
RECORDS_FILENAME = "records.jsonl"
RUN_FILENAME = "RUN.json"
NOTES_FILENAME = "NOTES.md"

OK_CALL = "_ok"
BAD_CALL = "_bad"
OK_ARG_NAMES = (
    "slug",
    "goal",
    "mod",
    "stack",
    "docs",
    "first_old",
    "first_new",
    "fix_new",
)
BAD_ARG_NAMES = (
    "slug",
    "goal",
    "mod",
    "stack",
    "docs",
    "first_old",
    "first_new",
    "ticket",
)
OK_SIDE_KEYS = (
    "slug",
    "goal",
    "plan",
    "mod",
    "test_fn",
    "src_body",
    "test_body",
    "grep_pat",
    "grep_hit",
    "fail_msg",
    "first_old",
    "first_new",
    "first_obs",
    "still_msg",
    "reread_obs",
    "plan_change",
    "fix_new",
    "fix_obs",
    "docs_url",
    "docs_ok",
    "docs_url2",
    "docs_ok2",
    "outcome",
    "domain",
    "stack",
    "seed",
    "residual",
    "coverage",
)
BAD_SIDE_KEYS = OK_SIDE_KEYS + ("ticket", "ticket_why")

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
BANNED_SLUG_BITS = (
    "leftover leftover leftover",
    "vs-drop",
    "slicercache",
    "prism",
    "ods-content",
)
DECISION_PREFIXES = ("Plan:", "Observation:", "Reflection:", "Tool call:")

FINDING_CATALOG_FILE_MISSING = "cei.catalog_file_missing"
FINDING_CATALOG_FIELD_MISSING = "cei.catalog_field_missing"
FINDING_CATALOG_FIELD_INVALID = "cei.catalog_field_invalid"
FINDING_CATALOG_SHA256_MISMATCH = "cei.catalog_sha256_mismatch"
FINDING_PLANT_FIELD_MISSING = "cei.plant_field_missing"
FINDING_PLANT_FIELD_INVALID = "cei.plant_field_invalid"
FINDING_PLANT_DUPLICATE_ID = "cei.plant_duplicate_id"
FINDING_PLANT_NOT_FOUND = "cei.plant_not_found"
FINDING_MILL_NOT_FOUND = "cei.mill_not_found"
FINDING_FACTORY_NOT_REGISTERED = "cei.factory_not_registered"
FINDING_DESTINATION_EXISTS = "cei.destination_exists"
FINDING_DESTINATION_UNDER_RAW = "cei.destination_under_raw"
FINDING_SOURCE_NOT_PARSEABLE = "cei.source_not_parseable"
FINDING_BANNED_KEY = "cei.banned_key"
FINDING_BANNED_ID = "cei.banned_id"
FINDING_USAGE = "cei.usage"
FINDING_ROUND_INVALID = "cei.round_invalid"
FINDING_GOAL_INVALID = "cei.goal_invalid"

__all__ = [
    "BAD_ARG_NAMES",
    "BAD_CALL",
    "BAD_SIDE_KEYS",
    "BANNED_ID_PREFIXES",
    "BANNED_KEYS",
    "BANNED_SLUG_BITS",
    "CATALOG_FILENAME",
    "CATALOG_FORMAT",
    "DECISION_PREFIXES",
    "DEFAULT_CATALOG_ID",
    "FACTORY",
    "FINDING_BANNED_ID",
    "FINDING_BANNED_KEY",
    "FINDING_CATALOG_FIELD_INVALID",
    "FINDING_CATALOG_FIELD_MISSING",
    "FINDING_CATALOG_FILE_MISSING",
    "FINDING_CATALOG_SHA256_MISMATCH",
    "FINDING_DESTINATION_EXISTS",
    "FINDING_DESTINATION_UNDER_RAW",
    "FINDING_FACTORY_NOT_REGISTERED",
    "FINDING_GOAL_INVALID",
    "FINDING_MILL_NOT_FOUND",
    "FINDING_PLANT_DUPLICATE_ID",
    "FINDING_PLANT_FIELD_INVALID",
    "FINDING_PLANT_FIELD_MISSING",
    "FINDING_PLANT_NOT_FOUND",
    "FINDING_ROUND_INVALID",
    "FINDING_SOURCE_NOT_PARSEABLE",
    "FINDING_USAGE",
    "GENERATOR",
    "MILL_PREFIX",
    "NOTES_FILENAME",
    "NOVEL_COVERAGE_BAD",
    "NOVEL_COVERAGE_OK",
    "OK_ARG_NAMES",
    "OK_CALL",
    "OK_SIDE_KEYS",
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
    "CeiRefusal",
    "bind_import_twin",
    "dumps_exact_json",
    "is_under_raw",
    "load_strict_json",
    "repo_root",
]


class CeiRefusal(Exception):
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
