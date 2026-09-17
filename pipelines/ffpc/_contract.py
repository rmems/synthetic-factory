#!/usr/bin/env python3
"""Pinned identity and coded refusals for the FFPC preference family.

Constants are AST-extracted from recovered Session-A builders on
``origin/codex/recover-grok-01a06111``. This module is the only place the
family names the factory, generator, quota, isolation, and vendor ban.
Recovered mill scripts are parse input only and are never executed.
"""

from __future__ import annotations

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

FAMILY_PREFIX = "ffpc"
FACTORY = "failure-as-fuel-preference-cascade"
GENERATOR = "grok-4.6"
GEN = GENERATOR
ISOLATION = "two-session"
LINEAR_ISSUE = "RM-793"
RUN_LABEL = "2026-09-02-final-heavy"
QUOTA_PER_ROUND = 3
RECORD_KIND = "preference"
CATALOG_ID = "ffpc-recover-v1"
SOURCE_REF = "origin/codex/recover-grok-01a06111"
SOURCE_COMMIT = "e5206e72fa829931162944648e1e180949baaf0b"
SOURCE_TREE = (
    "recovery/grok-session-01a06111-1b84-7250-aec4-9d120db6c1a4/"
    "recovered_sources/by-original-path"
)
INTENDED_USE = "research_only"
PROJECT_TRAINING_POLICY = "blocked"
VENDOR_NAME_NEEDLES = (
    "mill",
    "leftover",
)
VENDOR_PREFIXES = (
    "ffpc-mill",
    "ffpc_mill",
)

FINDING_AST_NOT_A_PLANT = "CATALOG_AST_NOT_A_PLANT"
FINDING_CATALOG_EMPTY = "CATALOG_EMPTY"
FINDING_CATALOG_FILE_MISSING = "CATALOG_FILE_MISSING"
FINDING_CATALOG_TRIPLE_STRIDE = "CATALOG_TRIPLE_STRIDE"
FINDING_PLANTS_SHA_MISMATCH = "PLANTS_SHA_MISMATCH"
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
    FINDING_CATALOG_TRIPLE_STRIDE,
    FINDING_PLANTS_SHA_MISMATCH,
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


class FfpcRefusal(refusals.CodedRefusal):
    """The family's coded refusal: ``str`` is always ``CODE: prose``."""

    CODES = FINDING_CODE_SET


refuse, refuse_when, refuse_first = refusals.helpers(FfpcRefusal)
shown = refusals.shown


def load_strict_json(payload: str | bytes):
    """Keep exact decimal tokens at FFPC catalog boundaries."""

    return json.loads(
        payload,
        object_pairs_hook=reject_duplicate_object_keys,
        parse_constant=reject_json_constant,
        parse_float=ExactJSONFloat,
    )


def require_round(rnd: int) -> int:
    """Accept a positive integer round token. Booleans are not rounds."""

    refuse_when(
        type(rnd) is not int or rnd < 1,
        FINDING_ROUND_OUT_OF_DOMAIN,
        f"round must be a positive int, got {shown(rnd)}",
    )
    return rnd


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
    "CATALOG_ID",
    "FACTORY",
    "FAMILY_PREFIX",
    "FINDING_AST_NOT_A_PLANT",
    "FINDING_CATALOG_EMPTY",
    "FINDING_CATALOG_FILE_MISSING",
    "FINDING_CATALOG_TRIPLE_STRIDE",
    "FINDING_PLANTS_SHA_MISMATCH",
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
    "ISOLATION",
    "LINEAR_ISSUE",
    "PROJECT_TRAINING_POLICY",
    "QUOTA_PER_ROUND",
    "RECORD_KIND",
    "RUN_LABEL",
    "SOURCE_COMMIT",
    "SOURCE_REF",
    "SOURCE_TREE",
    "VENDOR_NAME_NEEDLES",
    "VENDOR_PREFIXES",
    "FfpcRefusal",
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
    "require_round",
    "shown",
]


bind_import_twin(__name__)
