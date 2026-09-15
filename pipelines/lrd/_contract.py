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
CATALOG_ID = "lrd-plants-v1"
RUN_FORMAT = "lrd-run/1"
RECORD_KIND = "episode"
QUOTA_PER_ROUND = 2
DEFAULT_CATALOG_REL = ("config", "lrd")
CATALOG_SLICE = "full"
SOURCE_MILL_ID = "lrd_r157"
SOURCE_ROUND = 157
SOURCE_REF = "legacy-mill-lane"
SOURCE_PATH = "experiments/lrd_r157_leftover_leftover_leftover_mill.py"
SOURCE_COMMIT = "813f93f1969c1c4421e5663492e9663739efa642"
EXTRACT_METHOD = "git-show+ast.parse"
NOVEL_COVERAGE = "84%"

SHAPE_LEGACY = "legacy"
SHAPE_LEFTOVER3 = "leftover3"
SHAPE_P_IDTOKEN = "p_idtoken"
SHAPE_P_COOKIE = "p_cookie"
SHAPE_LLL = "lll"
LEFTOVER3_CALLS = frozenset({"OK", "FAIL"})
P_IDTOKEN_ARG_COUNT = 17
P_COOKIE_ARG_COUNT = 17
LLL_PAIR_KEYS = (
    "slug",
    "domain",
    "stack",
    "seed",
    "root",
    "f1",
    "f2",
    "token",
    "wrong",
    "right",
    "ticket",
)

# mill_id, base_round, legacy-mill-lane path, extract shape
SOURCE_MILLS = (
    ("lrd_r157", 157, "experiments/lrd_r157_leftover_leftover_leftover_mill.py", SHAPE_LEGACY),
    ("lrd_r67", 67, "experiments/lrd-mill-leftover3-r67.py", SHAPE_LEFTOVER3),
    ("lrd_r75", 75, "experiments/lrd-mill-leftover3b-r75.py", SHAPE_LEFTOVER3),
    ("lrd_r81", 81, "experiments/lrd-mill-leftover3c-r81.py", SHAPE_LEFTOVER3),
    ("lrd_r100", 100, "experiments/lrd-mill-leftover3d-r100.py", SHAPE_LEFTOVER3),
    ("lrd_r123", 123, "experiments/lrd-mill-leftover3-idtoken.py", SHAPE_P_IDTOKEN),
    ("lrd_r97", 97, "experiments/lrd-mill-lll-r97.py", SHAPE_LLL),
    ("lrd_r116", 116, "experiments/lrd-mill-r116.py", SHAPE_P_COOKIE),
)

FULL_MILL_COUNTS = (
    ("lrd_r157", 16),
    ("lrd_r67", 8),
    ("lrd_r75", 6),
    ("lrd_r81", 16),
    ("lrd_r100", 16),
    ("lrd_r123", 16),
    ("lrd_r97", 16),
    ("lrd_r116", 24),
)
FULL_PLANT_COUNT = sum(count for _, count in FULL_MILL_COUNTS)

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
    "CATALOG_SLICE",
    "DEFAULT_CATALOG_REL",
    "EXTRACT_METHOD",
    "FULL_MILL_COUNTS",
    "FULL_PLANT_COUNT",
    "LEFTOVER3_CALLS",
    "LLL_PAIR_KEYS",
    "P_COOKIE_ARG_COUNT",
    "P_IDTOKEN_ARG_COUNT",
    "SHAPE_LEGACY",
    "SHAPE_LEFTOVER3",
    "SHAPE_LLL",
    "SHAPE_P_COOKIE",
    "SHAPE_P_IDTOKEN",
    "SOURCE_MILLS",
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
