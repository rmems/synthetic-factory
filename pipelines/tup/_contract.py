#!/usr/bin/env python3
"""Shared primitives for the tup family (hopper / code_repair _contract).

Both import forms are supported (``tup.x`` with ``pipelines/`` on
``sys.path``, and ``pipelines.tup.x`` from the repository root). Every
module ends with ``bind_import_twin(__name__)`` so the two spellings are
one object.
"""

from __future__ import annotations

import json
import re
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

FACTORY = "tool-use-preference-factory"
MILL_PREFIX = "tup"
GENERATOR = "tup-mill"
CATALOG_FORMAT = "tup-catalog/1"
RUN_FORMAT = "tup-run/1"
DEFAULT_CATALOG_ID = "tup-v2"
SLICE = "tup-mill-r1349"
SOURCE_REF = "legacy-mill-lane"
SOURCE_COMMIT = "dba9f9a1d0e984e58fc14c992228f09534c26d57"
SOURCE_PATH = "experiments/tup-mill-r1349.py"
SOURCE_METHOD = "git-show+ast.parse"
SOURCE_SHA256 = "c6dbebe3787759023d8a249791419a6add90f3a2fa6c0904159b051f265d85ab"
SOURCE_BLOB_SHA1 = "b0e965da738d49af64219403398203f48d91ab8e"
QUOTA_PER_ROUND = 3
BANNED_GOAL = "Check designed checkout"

CATALOG_FILENAME = "CATALOG.json"
FAMILIES_FILENAME = "families.jsonl"
PLANTS_EXTRA_FILENAME = "plants-extra.jsonl"
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

VENDOR_NAME_RE = re.compile(
    r"^(tup-mill.*\.py|tup-loop.*\.py|tup_.*mill.*\.py|tup_compact\.py|"
    r"tup_themes\.py|tup_mill.*\.py|tup_unique_leftover_mill\.py|"
    r"_gen_tup.*\.py)$"
)

FINDING_CATALOG_FILE_MISSING = "CATALOG_FILE_MISSING"
FINDING_CATALOG_FIELD_MISSING = "CATALOG_FIELD_MISSING"
FINDING_CATALOG_FIELD_INVALID = "CATALOG_FIELD_INVALID"
FINDING_PLANTS_SHA_MISMATCH = "PLANTS_SHA_MISMATCH"
FINDING_PLANT_FIELD_MISSING = "PLANT_FIELD_MISSING"
FINDING_PLANT_FIELD_INVALID = "PLANT_FIELD_INVALID"
FINDING_PLANT_DUPLICATE = "PLANT_DUPLICATE"
FINDING_PLANT_NOT_FOUND = "PLANT_NOT_FOUND"
FINDING_DESTINATION_EXISTS = "DESTINATION_EXISTS"
FINDING_DESTINATION_UNDER_RAW = "DESTINATION_UNDER_RAW"
FINDING_DESTINATION_VENDOR = "DESTINATION_VENDOR"
FINDING_SOURCE_NOT_PARSEABLE = "SOURCE_NOT_PARSEABLE"
FINDING_BANNED_KEY = "BANNED_KEY"
FINDING_USAGE = "USAGE"
FINDING_ROUND_INVALID = "ROUND_INVALID"

FINDING_CODES = (
    FINDING_CATALOG_FILE_MISSING,
    FINDING_CATALOG_FIELD_MISSING,
    FINDING_CATALOG_FIELD_INVALID,
    FINDING_PLANTS_SHA_MISMATCH,
    FINDING_PLANT_FIELD_MISSING,
    FINDING_PLANT_FIELD_INVALID,
    FINDING_PLANT_DUPLICATE,
    FINDING_PLANT_NOT_FOUND,
    FINDING_DESTINATION_EXISTS,
    FINDING_DESTINATION_UNDER_RAW,
    FINDING_DESTINATION_VENDOR,
    FINDING_SOURCE_NOT_PARSEABLE,
    FINDING_BANNED_KEY,
    FINDING_USAGE,
    FINDING_ROUND_INVALID,
)
FINDING_CODE_SET = frozenset(FINDING_CODES)


class TupRefusal(refusals.CodedRefusal):
    """The family's coded refusal: ``str`` is always ``CODE: prose``."""

    CODES = FINDING_CODE_SET


refuse, refuse_when, refuse_first = refusals.helpers(TupRefusal)
shown = refusals.shown

__all__ = [
    "BANNED_GOAL",
    "BANNED_KEYS",
    "CATALOG_FILENAME",
    "CATALOG_FORMAT",
    "DEFAULT_CATALOG_ID",
    "FACTORY",
    "FAMILIES_FILENAME",
    "PLANTS_EXTRA_FILENAME",
    "FINDING_CODES",
    "FINDING_CODE_SET",
    "GENERATOR",
    "MILL_PREFIX",
    "NOTES_FILENAME",
    "QUOTA_PER_ROUND",
    "RECORDS_FILENAME",
    "RUN_FILENAME",
    "RUN_FORMAT",
    "SLICE",
    "SOURCE_BLOB_SHA1",
    "SOURCE_COMMIT",
    "SOURCE_METHOD",
    "SOURCE_PATH",
    "SOURCE_REF",
    "SOURCE_SHA256",
    "TupRefusal",
    "VENDOR_NAME_RE",
    "bind_import_twin",
    "dumps_exact_json",
    "envelope",
    "is_under_raw",
    "load_strict_json",
    "refuse",
    "refuse_first",
    "refuse_vendor_path",
    "refuse_when",
    "repo_root",
    "shown",
]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_strict_json(payload: str | bytes):
    """Keep exact decimal tokens at tup catalog and record boundaries."""

    return json.loads(
        payload,
        object_pairs_hook=reject_duplicate_object_keys,
        parse_constant=reject_json_constant,
        parse_float=ExactJSONFloat,
    )


def refuse_vendor_path(path: Path) -> None:
    """Refuse a destination that names or contains a vendored mill script."""

    resolved = Path(path)
    for part in resolved.parts:
        refuse_when(
            bool(VENDOR_NAME_RE.fullmatch(part)),
            FINDING_DESTINATION_VENDOR,
            f"destination {resolved} names vendored mill script {part!r}",
        )
    if resolved.exists() and resolved.is_dir():
        for child in resolved.rglob("*"):
            refuse_when(
                bool(VENDOR_NAME_RE.fullmatch(child.name)),
                FINDING_DESTINATION_VENDOR,
                f"destination {resolved} contains vendored mill script "
                f"{child.name!r}",
            )


bind_import_twin(__name__)
