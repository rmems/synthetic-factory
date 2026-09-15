#!/usr/bin/env python3
"""Pinned identity and coded refusals for pay Archive B (mill_plants).

Archive A (r330 leftover-leftover-leftover) lives in :mod:`pipelines.pay.pairs`.
Archive B is AST-extracted from ``scripts/payment_idempotency_mill/mill_plants.py``
(bytes on ``origin/legacy-mill-lane``; Grok recovery session
``origin/codex/recover-grok-01a06111`` @ ``e5206e72``). Mill scripts are parse
input only and are never executed.
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

FAMILY_PREFIX = "pay"
FACTORY = "payment-idempotency-factory"
GENERATOR = "grok-4.6"
ARCHIVE = "B"
CATALOG_ID = "pay-archive-b-v1"
CATALOG_SCHEMA = "pay-archive-b-catalog-v1"
CATALOG_FILENAME = "CATALOG.json"
PAIRS_FILENAME = "archive_b.jsonl"
SOURCE_SESSION_REF = "origin/codex/recover-grok-01a06111"
SOURCE_SESSION_COMMIT = "e5206e72fa829931162944648e1e180949baaf0b"
SOURCE_BYTES_REF = "origin/legacy-mill-lane"
SOURCE_BYTES_COMMIT = "813f93f1969c1c4421e5663492e9663739efa642"
SOURCE_PATH = "scripts/payment_idempotency_mill/mill_plants.py"
START_ROUND = 98
INTENDED_USE = "research_only"
PROJECT_TRAINING_POLICY = "blocked"

VENDOR_PREFIXES = (
    "payment_idempotency_mill",
    "mill_plants",
)
VENDOR_SUFFIXES = ("_mill.py",)

FINDING_AST_NOT_A_PAIR = "CATALOG_AST_NOT_A_PAIR"
FINDING_CATALOG_FIELD_INVALID = "CATALOG_FIELD_INVALID"
FINDING_CATALOG_FIELD_MISSING = "CATALOG_FIELD_MISSING"
FINDING_CATALOG_FILE_MISSING = "CATALOG_FILE_MISSING"
FINDING_CATALOG_SHA256_MISMATCH = "CATALOG_SHA256_MISMATCH"
FINDING_DUPLICATE_SLUG = "CATALOG_DUPLICATE_SLUG"
FINDING_PAIR_FIELD_MISSING = "PAIR_FIELD_MISSING"
FINDING_SLICE_A_OVERLAP = "ARCHIVE_B_OVERLAPS_SLICE_A"
FINDING_SOURCE_NOT_PARSEABLE = "SOURCE_NOT_PARSEABLE"
FINDING_VENDOR_PATH = "VENDOR_PATH_REFUSED"

FINDING_CODES = (
    FINDING_AST_NOT_A_PAIR,
    FINDING_CATALOG_FIELD_INVALID,
    FINDING_CATALOG_FIELD_MISSING,
    FINDING_CATALOG_FILE_MISSING,
    FINDING_CATALOG_SHA256_MISMATCH,
    FINDING_DUPLICATE_SLUG,
    FINDING_PAIR_FIELD_MISSING,
    FINDING_SLICE_A_OVERLAP,
    FINDING_SOURCE_NOT_PARSEABLE,
    FINDING_VENDOR_PATH,
)
FINDING_CODE_SET = frozenset(FINDING_CODES)


class PayRefusal(refusals.CodedRefusal):
    """Coded refusal for the pay Archive B catalog."""

    CODES = FINDING_CODE_SET


refuse, refuse_when, refuse_first = refusals.helpers(PayRefusal)
shown = refusals.shown


def package_dir() -> Path:
    return Path(__file__).resolve().parent


def repo_root() -> Path:
    return package_dir().parents[1]


def is_vendor_filename(name: str) -> bool:
    lowered = name.lower()
    if any(lowered.startswith(prefix) for prefix in VENDOR_PREFIXES):
        return True
    return any(lowered.endswith(suffix) for suffix in VENDOR_SUFFIXES)


def refuse_vendor_paths(directory: Path) -> None:
    for path in directory.iterdir():
        if path.is_file() and is_vendor_filename(path.name):
            refuse(FINDING_VENDOR_PATH, f"vendor mill path {path.name} is not allowed in the package")


def load_strict_json(path: Path) -> dict:
    raw = path.read_text(encoding="utf-8")
    payload = json.loads(
        raw,
        object_pairs_hook=reject_duplicate_object_keys,
        parse_constant=reject_json_constant,
        parse_float=ExactJSONFloat,
    )
    refuse_when(not isinstance(payload, dict), FINDING_CATALOG_FIELD_INVALID, f"{path} root must be object")
    return payload


bind_import_twin(__name__)
