#!/usr/bin/env python3
"""Pinned identity and coded refusals for the NELB bridge family.

Constants are AST-extracted from the recovered r01 builder on
``origin/codex/recover-grok-01a06111``. This module is the only place the
family names the factory, generator, quota, isolation, and vendor ban.
Recovered mill scripts are parse input only and are never executed.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
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

FAMILY_PREFIX = "nelb"
FACTORY = "neuromorphic-event-language-bridge"
GENERATOR = "grok-4.6"
GEN = GENERATOR
ISOLATION = "single-session"
LINEAR_ISSUE = "RM-793"
RUN_LABEL = "2026-09-02-final-heavy"
QUOTA_PER_ROUND = 3
RECORD_KIND = "bridge_pair"
CATALOG_ID = "nelb-plants-v2"
CATALOG_FORMAT = "nelb-catalog/2"
CATALOG_FILENAME = "CATALOG.json"
PLANTS_FILENAME = "plants.jsonl"
LEGACY_REF = "origin/legacy-mill-lane"
LEGACY_COMMIT = "813f93f1969c1c4421e5663492e9663739efa642"
SOURCE_REF = "origin/codex/recover-grok-01a06111"
SOURCE_COMMIT = "e5206e72fa829931162944648e1e180949baaf0b"
SOURCE_TREE = (
    "recovery/grok-session-01a06111-1b84-7250-aec4-9d120db6c1a4/"
    "recovered_sources/by-original-path"
)
SOURCE_SLICE = "nelb-r01-live--a4378171ce87/versions/v0001/gen_r01.py"
INTENDED_USE = "research_only"
PROJECT_TRAINING_POLICY = "blocked"
SNN_TAGS = ("race", "refractory", "adaptation")
VENDOR_NAME_NEEDLES = (
    "mill",
    "leftover",
)
VENDOR_PREFIXES = (
    "nelb-mill",
    "nelb_mill",
    "gen_r",
)

FINDING_AST_NOT_A_PLANT = "CATALOG_AST_NOT_A_PLANT"
FINDING_CATALOG_EMPTY = "CATALOG_EMPTY"
FINDING_CATALOG_FILE_MISSING = "CATALOG_FILE_MISSING"
FINDING_CATALOG_SHA256_MISMATCH = "CATALOG_SHA256_MISMATCH"
FINDING_CATALOG_TRIPLE_STRIDE = "CATALOG_TRIPLE_STRIDE"
FINDING_DESTINATION_EXISTS = "DESTINATION_EXISTS"
FINDING_DESTINATION_UNDER_RAW = "DESTINATION_UNDER_RAW"
FINDING_DUPLICATE_ID = "CATALOG_DUPLICATE_ID"
FINDING_FIELD_INVALID = "CATALOG_FIELD_INVALID"
FINDING_FIELD_MISSING = "CATALOG_FIELD_MISSING"
FINDING_ROUND_OUT_OF_DOMAIN = "ROUND_OUT_OF_DOMAIN"
FINDING_TRIPLE_OUT_OF_DOMAIN = "TRIPLE_OUT_OF_DOMAIN"
FINDING_VENDOR_PATH = "VENDOR_PATH_REFUSED"

FINDING_CODES = (
    FINDING_AST_NOT_A_PLANT,
    FINDING_CATALOG_EMPTY,
    FINDING_CATALOG_FILE_MISSING,
    FINDING_CATALOG_SHA256_MISMATCH,
    FINDING_CATALOG_TRIPLE_STRIDE,
    FINDING_DESTINATION_EXISTS,
    FINDING_DESTINATION_UNDER_RAW,
    FINDING_DUPLICATE_ID,
    FINDING_FIELD_INVALID,
    FINDING_FIELD_MISSING,
    FINDING_ROUND_OUT_OF_DOMAIN,
    FINDING_TRIPLE_OUT_OF_DOMAIN,
    FINDING_VENDOR_PATH,
)
FINDING_CODE_SET = frozenset(FINDING_CODES)


class NelbRefusal(refusals.CodedRefusal):
    """The family's coded refusal: ``str`` is always ``CODE: prose``."""

    CODES = FINDING_CODE_SET


refuse, refuse_when, refuse_first = refusals.helpers(NelbRefusal)
shown = refusals.shown


def require_round(rnd: int) -> int:
    """Accept a positive integer round token. Booleans are not rounds."""

    refuse_when(
        type(rnd) is not int or rnd < 1,
        FINDING_ROUND_OUT_OF_DOMAIN,
        f"round must be a positive int, got {shown(rnd)}",
    )
    return rnd


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def default_catalog_dir() -> Path:
    return Path(__file__).resolve().parent


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def load_strict_json(payload: str | bytes):
    """Keep exact decimal tokens at catalog and record boundaries."""

    return json.loads(
        payload,
        object_pairs_hook=reject_duplicate_object_keys,
        parse_constant=reject_json_constant,
        parse_float=ExactJSONFloat,
    )


def refuse_vendor_paths(paths: Iterable[Path | str]) -> None:
    """Fail closed if any path would vendor a recovered mill script."""

    for raw in paths:
        path = Path(raw)
        name = path.name.lower()
        refuse_when(
            name.endswith(".py") and any(needle in name for needle in VENDOR_NAME_NEEDLES),
            FINDING_VENDOR_PATH,
            f"refusing to vendor {path.name}",
        )
        refuse_when(
            name.endswith(".py") and name.startswith(VENDOR_PREFIXES),
            FINDING_VENDOR_PATH,
            f"refusing to vendor {path.name}",
        )


__all__ = [
    "CATALOG_FILENAME",
    "CATALOG_FORMAT",
    "CATALOG_ID",
    "FACTORY",
    "FAMILY_PREFIX",
    "FINDING_AST_NOT_A_PLANT",
    "FINDING_CATALOG_EMPTY",
    "FINDING_CATALOG_FILE_MISSING",
    "FINDING_CATALOG_SHA256_MISMATCH",
    "FINDING_CATALOG_TRIPLE_STRIDE",
    "FINDING_CODES",
    "FINDING_CODE_SET",
    "FINDING_DESTINATION_EXISTS",
    "FINDING_DESTINATION_UNDER_RAW",
    "FINDING_DUPLICATE_ID",
    "FINDING_FIELD_INVALID",
    "FINDING_FIELD_MISSING",
    "FINDING_ROUND_OUT_OF_DOMAIN",
    "FINDING_TRIPLE_OUT_OF_DOMAIN",
    "FINDING_VENDOR_PATH",
    "GEN",
    "GENERATOR",
    "INTENDED_USE",
    "LEGACY_COMMIT",
    "LEGACY_REF",
    "ISOLATION",
    "LINEAR_ISSUE",
    "PLANTS_FILENAME",
    "PROJECT_TRAINING_POLICY",
    "QUOTA_PER_ROUND",
    "RECORD_KIND",
    "RUN_LABEL",
    "SNN_TAGS",
    "SOURCE_COMMIT",
    "SOURCE_REF",
    "SOURCE_SLICE",
    "SOURCE_TREE",
    "VENDOR_NAME_NEEDLES",
    "VENDOR_PREFIXES",
    "NelbRefusal",
    "bind_import_twin",
    "default_catalog_dir",
    "dumps_exact_json",
    "envelope",
    "is_under_raw",
    "load_strict_json",
    "refuse",
    "repo_root",
    "sha256_bytes",
    "refuse_first",
    "refuse_vendor_paths",
    "refuse_when",
    "refusals",
    "require_round",
    "shown",
]


bind_import_twin(__name__)
