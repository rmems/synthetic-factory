#!/usr/bin/env python3
"""The one place the lrd mill reaches main's shared primitives.

Both import forms are supported (``lrd.x`` with ``pipelines/`` on ``sys.path``,
and ``pipelines.lrd.x`` from the repository root). Every other module in the
package imports only its siblings and ``_contract``. Each module ends with
``bind_import_twin(__name__)`` so the two spellings are one object (the
hopper / code_repair convention).
"""

from __future__ import annotations

import json
from pathlib import Path

if __name__.startswith("pipelines."):
    from ..exact_json import ExactJSONFloat, dumps_exact_json
    from ..mill_family import REVIEWED_MILL_PREFIX_HOMES
    from ..oracle_grounded import envelope, refusals
    from ..oracle_grounded.import_twins import bind_import_twin
    from ..raw_tree_guard import is_under_raw
    from ..tag_jsonutil import reject_duplicate_object_keys, reject_json_constant
else:
    from exact_json import ExactJSONFloat, dumps_exact_json
    from mill_family import REVIEWED_MILL_PREFIX_HOMES
    from oracle_grounded import envelope, refusals
    from oracle_grounded.import_twins import bind_import_twin
    from raw_tree_guard import is_under_raw
    from tag_jsonutil import reject_duplicate_object_keys, reject_json_constant

FAMILY = "lrd"
FACTORY = "log-redaction-factory"
PREFIX = "lrd"
GENERATOR = "grok-4.6"
CATALOG_FORMAT = "lrd-mill-catalog/1"
CATALOG_ID = "lrd-r157-v1"
RUN_FORMAT = "lrd-run/1"
RECORD_KIND = "episode"
QUOTA_PER_ROUND = 2
DEFAULT_CATALOG_REL = ("config", "lrd")
SOURCE_MILL_ID = "lrd_r157"
SOURCE_ROUND = 157
SOURCE_REF = "legacy-mill-lane"
SOURCE_PATH = "experiments/lrd_r157_leftover_leftover_leftover_mill.py"
SOURCE_COMMIT = "a9e6602a7bd43b314f9691984ae5f48d40c762b2"
NOVEL_COVERAGE = "84%"

CATALOG_FILENAME = "CATALOG.json"
PLANTS_FILENAME = "plants.jsonl"
RECORDS_FILENAME = "records.jsonl"
RUN_FILENAME = "RUN.json"
NOTES_FILENAME = "NOTES.md"

# dpr-lrd-hopper* stay with dpr. Name stems the extractor refuses.
HOPPER_NAME_MARKERS = ("hopper", "dpr-lrd-hopper")
LOOP_NAME_MARKERS = ("-loop-", "lrd-loop")
HOPPER_DEF_NAMES = frozenset({"mill_and_publish"})

BANNED_KEYS = frozenset(
    {
        "thought",
        "chain_of_thought",
        "scratch",
        "inner_monologue",
        "spike_events",
    }
)
BANNED_ID_PREFIXES = ("sir-", "dbc-", "saf-")

PAIR_KEYS = (
    "mod",
    "drop",
    "stack",
    "field",
    "naive",
    "conf",
    "conf2",
    "oldc",
    "newc",
    "old2",
    "new2",
    "test",
    "ticket",
    "slug",
    "fail",
    "domain",
)

FINDING_CATALOG_FILE_MISSING = "CATALOG_FILE_MISSING"
FINDING_CATALOG_FIELD_MISSING = "CATALOG_FIELD_MISSING"
FINDING_CATALOG_FIELD_INVALID = "CATALOG_FIELD_INVALID"
FINDING_CATALOG_SHA256_MISMATCH = "CATALOG_SHA256_MISMATCH"
FINDING_PLANT_FIELD_MISSING = "PLANT_FIELD_MISSING"
FINDING_PLANT_FIELD_INVALID = "PLANT_FIELD_INVALID"
FINDING_PLANT_DUPLICATE_ID = "PLANT_DUPLICATE_ID"
FINDING_PLANT_NOT_FOUND = "PLANT_NOT_FOUND"
FINDING_MILL_NOT_FOUND = "MILL_NOT_FOUND"
FINDING_FACTORY_NOT_REGISTERED = "FACTORY_NOT_REGISTERED"
FINDING_DESTINATION_EXISTS = "DESTINATION_EXISTS"
FINDING_DESTINATION_UNDER_RAW = "DESTINATION_UNDER_RAW"
FINDING_SOURCE_NOT_PARSEABLE = "SOURCE_NOT_PARSEABLE"
FINDING_HOPPER_REFUSED = "HOPPER_REFUSED"
FINDING_LOOP_REFUSED = "LOOP_REFUSED"
FINDING_BANNED_KEY = "BANNED_KEY"
FINDING_BANNED_ID = "BANNED_ID"
FINDING_USAGE = "USAGE"
FINDING_ROUND_INVALID = "ROUND_INVALID"
FINDING_PACKAGE_EXEC = "PACKAGE_EXEC"

FINDING_CODES = (
    FINDING_CATALOG_FILE_MISSING,
    FINDING_CATALOG_FIELD_MISSING,
    FINDING_CATALOG_FIELD_INVALID,
    FINDING_CATALOG_SHA256_MISMATCH,
    FINDING_PLANT_FIELD_MISSING,
    FINDING_PLANT_FIELD_INVALID,
    FINDING_PLANT_DUPLICATE_ID,
    FINDING_PLANT_NOT_FOUND,
    FINDING_MILL_NOT_FOUND,
    FINDING_FACTORY_NOT_REGISTERED,
    FINDING_DESTINATION_EXISTS,
    FINDING_DESTINATION_UNDER_RAW,
    FINDING_SOURCE_NOT_PARSEABLE,
    FINDING_HOPPER_REFUSED,
    FINDING_LOOP_REFUSED,
    FINDING_BANNED_KEY,
    FINDING_BANNED_ID,
    FINDING_USAGE,
    FINDING_ROUND_INVALID,
    FINDING_PACKAGE_EXEC,
)
FINDING_CODE_SET = frozenset(FINDING_CODES)

REVIEWED_HOME = REVIEWED_MILL_PREFIX_HOMES[PREFIX]
if REVIEWED_HOME != FACTORY:  # pragma: no cover - the table pin is the authority
    raise ImportError(
        f"reviewed prefix home for {PREFIX!r} is {REVIEWED_HOME!r}, "
        f"not the lrd factory {FACTORY!r}"
    )


class LrdRefusal(refusals.CodedRefusal):
    """The family's coded refusal: ``str`` is always ``CODE: prose``."""

    CODES = FINDING_CODE_SET


refuse, refuse_when, refuse_first = refusals.helpers(LrdRefusal)
shown = refusals.shown


def load_strict_json(payload: str | bytes):
    """Keep exact decimal tokens at catalog and record boundaries."""

    return json.loads(
        payload,
        object_pairs_hook=reject_duplicate_object_keys,
        parse_constant=reject_json_constant,
        parse_float=ExactJSONFloat,
    )


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def default_catalog_dir() -> Path:
    return repo_root().joinpath(*DEFAULT_CATALOG_REL)


__all__ = [
    "BANNED_ID_PREFIXES",
    "BANNED_KEYS",
    "CATALOG_FILENAME",
    "CATALOG_FORMAT",
    "CATALOG_ID",
    "DEFAULT_CATALOG_REL",
    "FACTORY",
    "FAMILY",
    "FINDING_CODE_SET",
    "FINDING_CODES",
    "GENERATOR",
    "HOPPER_DEF_NAMES",
    "HOPPER_NAME_MARKERS",
    "LOOP_NAME_MARKERS",
    "LrdRefusal",
    "NOTES_FILENAME",
    "NOVEL_COVERAGE",
    "PAIR_KEYS",
    "PLANTS_FILENAME",
    "PREFIX",
    "QUOTA_PER_ROUND",
    "RECORD_KIND",
    "RECORDS_FILENAME",
    "REVIEWED_HOME",
    "RUN_FILENAME",
    "RUN_FORMAT",
    "SOURCE_COMMIT",
    "SOURCE_MILL_ID",
    "SOURCE_PATH",
    "SOURCE_REF",
    "SOURCE_ROUND",
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
    "repo_root",
    "shown",
]

bind_import_twin(__name__)
