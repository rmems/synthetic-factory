#!/usr/bin/env python3
"""Pinned identity and coded refusals for the TTF trajectory family.

Constants are AST-extracted from the first recovered ``ttf*`` slice on
``origin/codex/recover-grok-01a06111``. This module is the only place the
family names the factory, generator, quota, and vendor ban. Recovered mill
scripts are parse input only and are never executed.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

if __name__.startswith("pipelines."):
    from ..exact_json import dumps_exact_json
    from ..oracle_grounded import envelope, refusals
    from ..oracle_grounded.import_twins import bind_import_twin
    from ..raw_tree_guard import is_under_raw
else:
    from exact_json import dumps_exact_json
    from oracle_grounded import envelope, refusals
    from oracle_grounded.import_twins import bind_import_twin
    from raw_tree_guard import is_under_raw

FAMILY_PREFIX = "ttf"
FACTORY = "thalamic-trajectory-factory"
GENERATOR = "grok-4.6"
RUN_LABEL = "2026-09-02-final-heavy"
LINEAR_ISSUE = "RM-793"
QUOTA_PER_ROUND = 5
RECORD_KIND = "thalamic"
CATALOG_ID = "ttf-r02c-v1"
SLICE_ID = "r02c"
SOURCE_REF = "origin/codex/recover-grok-01a06111"
SOURCE_COMMIT = "e5206e72fa829931162944648e1e180949baaf0b"
SOURCE_TREE = (
    "recovery/grok-session-01a06111-1b84-7250-aec4-9d120db6c1a4/"
    "recovered_sources/by-original-path"
)
SOURCE_FILE = "ttf_r02c_gen.py"
SOURCE_RELPATH = (
    "tmp-root--215e7a505f5c/versions/v0008/ttf_r02c_gen.py"
)
SOURCE_SHA256 = (
    "8930294b4643f01b346d0a285f76068e7cf379fd0dac6c944e39a7e08c431fdc"
)
ORIGINAL_PATH = "/tmp/ttf_r02c_gen.py"
INTENDED_USE = "research_only"
PROJECT_TRAINING_POLICY = "blocked"
VENDOR_NAME_NEEDLES = (
    "mill",
    "leftover",
    "loop",
)
VENDOR_PREFIXES = (
    "ttf-mill",
    "ttf_mill",
    "ttf-loop",
    "ttf_loop",
)

FINDING_AST_NOT_A_PLANT = "CATALOG_AST_NOT_A_PLANT"
FINDING_CATALOG_EMPTY = "CATALOG_EMPTY"
FINDING_CATALOG_SLICE_STRIDE = "CATALOG_SLICE_STRIDE"
FINDING_DESTINATION_EXISTS = "DESTINATION_EXISTS"
FINDING_DESTINATION_UNDER_RAW = "DESTINATION_UNDER_RAW"
FINDING_DUPLICATE_ID = "CATALOG_DUPLICATE_ID"
FINDING_FIELD_INVALID = "CATALOG_FIELD_INVALID"
FINDING_FIELD_MISSING = "CATALOG_FIELD_MISSING"
FINDING_ROUND_OUT_OF_DOMAIN = "ROUND_OUT_OF_DOMAIN"
FINDING_SLICE_OUT_OF_DOMAIN = "SLICE_OUT_OF_DOMAIN"
FINDING_VENDOR_PATH = "VENDOR_PATH_REFUSED"

FINDING_CODES = (
    FINDING_AST_NOT_A_PLANT,
    FINDING_CATALOG_EMPTY,
    FINDING_CATALOG_SLICE_STRIDE,
    FINDING_DESTINATION_EXISTS,
    FINDING_DESTINATION_UNDER_RAW,
    FINDING_DUPLICATE_ID,
    FINDING_FIELD_INVALID,
    FINDING_FIELD_MISSING,
    FINDING_ROUND_OUT_OF_DOMAIN,
    FINDING_SLICE_OUT_OF_DOMAIN,
    FINDING_VENDOR_PATH,
)
FINDING_CODE_SET = frozenset(FINDING_CODES)


class TtfRefusal(refusals.CodedRefusal):
    """The family's coded refusal: ``str`` is always ``CODE: prose``."""

    CODES = FINDING_CODE_SET


refuse, refuse_when, refuse_first = refusals.helpers(TtfRefusal)
shown = refusals.shown


def require_round(rnd: int) -> int:
    """Accept a positive integer round token. Booleans are not rounds."""

    refuse_when(
        type(rnd) is not int or rnd < 1,
        FINDING_ROUND_OUT_OF_DOMAIN,
        f"round must be a positive int, got {shown(rnd)}",
    )
    return rnd


def refuse_vendor_paths(paths: Iterable[Path | str]) -> None:
    """Fail closed if any path would vendor a recovered mill or loop script."""

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
    "FINDING_CATALOG_SLICE_STRIDE",
    "FINDING_CODES",
    "FINDING_CODE_SET",
    "FINDING_DESTINATION_EXISTS",
    "FINDING_DESTINATION_UNDER_RAW",
    "FINDING_DUPLICATE_ID",
    "FINDING_FIELD_INVALID",
    "FINDING_FIELD_MISSING",
    "FINDING_ROUND_OUT_OF_DOMAIN",
    "FINDING_SLICE_OUT_OF_DOMAIN",
    "FINDING_VENDOR_PATH",
    "GENERATOR",
    "INTENDED_USE",
    "LINEAR_ISSUE",
    "ORIGINAL_PATH",
    "PROJECT_TRAINING_POLICY",
    "QUOTA_PER_ROUND",
    "RECORD_KIND",
    "RUN_LABEL",
    "SLICE_ID",
    "SOURCE_COMMIT",
    "SOURCE_FILE",
    "SOURCE_RELPATH",
    "SOURCE_REF",
    "SOURCE_SHA256",
    "SOURCE_TREE",
    "VENDOR_NAME_NEEDLES",
    "VENDOR_PREFIXES",
    "TtfRefusal",
    "bind_import_twin",
    "dumps_exact_json",
    "envelope",
    "is_under_raw",
    "refuse",
    "refuse_first",
    "refuse_vendor_paths",
    "refuse_when",
    "refusals",
    "require_round",
    "shown",
]


bind_import_twin(__name__)
