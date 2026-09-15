#!/usr/bin/env python3
"""Pinned identity and coded refusals for the leftover leftover leftover wave.

``FAMILY`` is the leftover-wave prefix ``lll``. Record ids still carry the
reviewed LHC mill prefix. Leftover mill scripts stay on
``origin/legacy-mill-lane`` and are never vendored or executed.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path

if __name__.startswith("pipelines."):
    from ..exact_json import ExactJSONFloat, dumps_exact_json
    from ..mill_reviewed_vocabulary import REVIEWED_MILL_PREFIX_HOMES
    from ..oracle_grounded import envelope, refusals
    from ..oracle_grounded.import_twins import bind_import_twin
    from ..raw_tree_guard import is_under_raw
    from ..tag_jsonutil import reject_duplicate_object_keys, reject_json_constant
else:
    from exact_json import ExactJSONFloat, dumps_exact_json
    from mill_reviewed_vocabulary import REVIEWED_MILL_PREFIX_HOMES
    from oracle_grounded import envelope, refusals
    from oracle_grounded.import_twins import bind_import_twin
    from raw_tree_guard import is_under_raw
    from tag_jsonutil import reject_duplicate_object_keys, reject_json_constant

FAMILY = "lll"
FACTORY = "long-horizon-coding-factory"
REVIEWED_PREFIX = "lhc"
RECORD_PREFIX = REVIEWED_PREFIX
GENERATOR = "lll-mill"
MILL_PREFIX = "lll"
CATALOG_FORMAT = "lll-catalog/1"
RUN_FORMAT = "lll-run/1"
RECORD_KIND = "catalog_replay"
QUOTA_PER_ROUND = 2
DEFAULT_CATALOG_ID = "lll-lhc-v1"
LEGACY_REF = "legacy-mill-lane"
LEGACY_COMMIT = "813f93f1969c1c4421e5663492e9663739efa642"
INTENDED_USE = "research_only"
PROJECT_TRAINING_POLICY = "blocked"

CATALOG_FILENAME = "CATALOG.json"
PLANTS_FILENAME = "plants.jsonl"
RECORDS_FILENAME = "records.jsonl"
RUN_FILENAME = "RUN.json"
NOTES_FILENAME = "NOTES.md"

PAIR_KEYS = (
    "title",
    "success_slug",
    "fail_slug",
    "success_plant",
    "fail_plant",
)

VENDOR_NAME_NEEDLES = ("mill", "leftover", "loop")
VENDOR_PREFIXES = (
    "lhc-mill",
    "lll-mill",
    "lll_mill",
    "mill_leftover_leftover_leftover",
)

# First unused leftover leftover leftover slice: LHC lll catalogs whose
# family prefix is not in the miller exclude list.
SOURCE_MILLS = (
    (
        "lhc-mill-lll-lang-r4750",
        "experiments/lhc-mill-lll-lang-r4750.py",
        4750,
        "3ae00f1db72ae6363111aeda2033212287ccfb9f",
    ),
    (
        "lhc-mill-lll-r4654",
        "experiments/lhc-mill-lll-r4654.py",
        4654,
        "87785b3d5d90490f22fca45ca63e49f59d44c0c9",
    ),
    (
        "lhc-mill-lll-r4688",
        "experiments/lhc-mill-lll-r4688.py",
        4688,
        "d4750cd733212bb05136420f1bde7098785cf273",
    ),
)

FINDING_CATALOG_FILE_MISSING = "CATALOG_FILE_MISSING"
FINDING_CATALOG_FIELD_MISSING = "CATALOG_FIELD_MISSING"
FINDING_CATALOG_FIELD_INVALID = "CATALOG_FIELD_INVALID"
FINDING_PLANTS_SHA_MISMATCH = "PLANTS_SHA_MISMATCH"
FINDING_PLANT_FIELD_MISSING = "PLANT_FIELD_MISSING"
FINDING_PLANT_FIELD_INVALID = "PLANT_FIELD_INVALID"
FINDING_PLANT_DUPLICATE = "PLANT_DUPLICATE"
FINDING_PLANT_NOT_FOUND = "PLANT_NOT_FOUND"
FINDING_MILL_NOT_FOUND = "MILL_NOT_FOUND"
FINDING_FACTORY_NOT_REGISTERED = "FACTORY_NOT_REGISTERED"
FINDING_DESTINATION_EXISTS = "DESTINATION_EXISTS"
FINDING_DESTINATION_UNDER_RAW = "DESTINATION_UNDER_RAW"
FINDING_SOURCE_NOT_PARSEABLE = "SOURCE_NOT_PARSEABLE"
FINDING_USAGE = "USAGE"
FINDING_ROUND_INVALID = "ROUND_INVALID"
FINDING_VENDOR_PATH = "VENDOR_PATH"

FINDING_CODES = (
    FINDING_CATALOG_FILE_MISSING,
    FINDING_CATALOG_FIELD_MISSING,
    FINDING_CATALOG_FIELD_INVALID,
    FINDING_PLANTS_SHA_MISMATCH,
    FINDING_PLANT_FIELD_MISSING,
    FINDING_PLANT_FIELD_INVALID,
    FINDING_PLANT_DUPLICATE,
    FINDING_PLANT_NOT_FOUND,
    FINDING_MILL_NOT_FOUND,
    FINDING_FACTORY_NOT_REGISTERED,
    FINDING_DESTINATION_EXISTS,
    FINDING_DESTINATION_UNDER_RAW,
    FINDING_SOURCE_NOT_PARSEABLE,
    FINDING_USAGE,
    FINDING_ROUND_INVALID,
    FINDING_VENDOR_PATH,
)
FINDING_CODE_SET = frozenset(FINDING_CODES)

REVIEWED_HOME = REVIEWED_MILL_PREFIX_HOMES[REVIEWED_PREFIX]
if REVIEWED_HOME != FACTORY:
    raise ImportError(
        f"reviewed prefix home for {REVIEWED_PREFIX!r} is {REVIEWED_HOME!r}, "
        f"not the leftover leftover leftover factory {FACTORY!r}"
    )


class LllRefusal(refusals.CodedRefusal):
    """The family's coded refusal: ``str`` is always ``CODE: prose``."""

    CODES = FINDING_CODE_SET


refuse, refuse_when, refuse_first = refusals.helpers(LllRefusal)
shown = refusals.shown

__all__ = [
    "CATALOG_FILENAME",
    "CATALOG_FORMAT",
    "DEFAULT_CATALOG_ID",
    "FACTORY",
    "FAMILY",
    "FINDING_CODE_SET",
    "FINDING_CODES",
    "GENERATOR",
    "INTENDED_USE",
    "LEGACY_COMMIT",
    "LEGACY_REF",
    "LllRefusal",
    "MILL_PREFIX",
    "NOTES_FILENAME",
    "PAIR_KEYS",
    "PLANTS_FILENAME",
    "PROJECT_TRAINING_POLICY",
    "QUOTA_PER_ROUND",
    "RECORD_KIND",
    "RECORD_PREFIX",
    "RECORDS_FILENAME",
    "REVIEWED_HOME",
    "REVIEWED_PREFIX",
    "RUN_FILENAME",
    "RUN_FORMAT",
    "SOURCE_MILLS",
    "VENDOR_NAME_NEEDLES",
    "VENDOR_PREFIXES",
    "bind_import_twin",
    "dumps_exact_json",
    "envelope",
    "is_under_raw",
    "load_strict_json",
    "refuse",
    "refuse_first",
    "refuse_vendor_paths",
    "refuse_when",
    "refusals",
    "repo_root",
    "require_round",
    "shown",
]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_strict_json(payload: str | bytes):
    """Keep exact decimal tokens at leftover leftover leftover catalog boundaries."""

    return json.loads(
        payload,
        object_pairs_hook=reject_duplicate_object_keys,
        parse_constant=reject_json_constant,
        parse_float=ExactJSONFloat,
    )


def require_round(rnd: int) -> int:
    refuse_when(
        type(rnd) is not int or rnd < 1,
        FINDING_ROUND_INVALID,
        f"round must be a positive int, got {shown(rnd)}",
    )
    return rnd


def refuse_vendor_paths(paths: Iterable[Path | str]) -> None:
    """Fail closed if any path would vendor a leftover mill or hop loop."""

    for raw in paths:
        name = Path(raw).name.lower()
        refuse_when(
            name.endswith(".py") and any(needle in name for needle in VENDOR_NAME_NEEDLES),
            FINDING_VENDOR_PATH,
            f"refusing to vendor {Path(raw).name}",
        )
        refuse_when(
            name.endswith(".py") and name.startswith(VENDOR_PREFIXES),
            FINDING_VENDOR_PATH,
            f"refusing to vendor {Path(raw).name}",
        )


bind_import_twin(__name__)
