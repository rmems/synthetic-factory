#!/usr/bin/env python3
"""Pinned identity and coded refusals for the TTF trajectory family.

Constants are AST-extracted from recovered ``ttf*`` generators on
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
    from ..tag_jsonutil import load_strict_json
else:
    from exact_json import dumps_exact_json
    from oracle_grounded import envelope, refusals
    from oracle_grounded.import_twins import bind_import_twin
    from raw_tree_guard import is_under_raw
    from tag_jsonutil import load_strict_json

FAMILY_PREFIX = "ttf"
FACTORY = "thalamic-trajectory-factory"
GENERATOR = "grok-4.6"
RUN_LABEL = "2026-09-02-final-heavy"
LINEAR_ISSUE = "RM-793"
QUOTA_PER_ROUND = 5
RECORD_KIND = "thalamic"
CATALOG_ID = "ttf-recover-v1"
CATALOG_SCHEMA = "ttf-plants-v1"
CATALOG_FILENAME = "CATALOG.json"
PLANTS_FILENAME = "plants.jsonl"
SOURCE_REF = "origin/codex/recover-grok-01a06111"
SOURCE_COMMIT = "e5206e72fa829931162944648e1e180949baaf0b"
SOURCE_TREE = (
    "recovery/grok-session-01a06111-1b84-7250-aec4-9d120db6c1a4/"
    "recovered_sources/by-original-path"
)
LEGACY_REF = "origin/legacy-mill-lane"
LEGACY_COMMIT = "813f93f1969c1c4421e5663492e9663739efa642"
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

# Recover-grok mill catalogs with a five-record REC_/rec_ extract (git show + ast.parse).
SOURCE_CATALOGS = (
    (
        "r02",
        "gen_ttf_r02.py",
        "tmp-root--c8ae2b925cad/versions/v0001/gen_ttf_r02.py",
        "abf5e140da613b77899983fd07e684395a8a9e0e97a756097e0a4d619cfd070e",
        "/tmp/gen_ttf_r02.py",
    ),
    (
        "r02c",
        "ttf_r02c_gen.py",
        "tmp-root--215e7a505f5c/versions/v0008/ttf_r02c_gen.py",
        "8930294b4643f01b346d0a285f76068e7cf379fd0dac6c944e39a7e08c431fdc",
        "/tmp/ttf_r02c_gen.py",
    ),
    (
        "r03",
        "gen_ttf_r03_tail.py",
        "tmp-root--95746ac5c89e/versions/v0001/gen_ttf_r03_tail.py",
        "5f8e0d3254495f1e30fbcfb8bc32ef9ffd71f9a8999c5be1d2c58a301b848376",
        "/tmp/gen_ttf_r03_tail.py",
    ),
    (
        "r04",
        "builders_r04.py",
        "ttf-r04--24386877af80/versions/v0001/builders_r04.py",
        "07044fe2a253697ac0b61fb2441fcb41685e5e511f08c95aeb723bdf61fa5bcb",
        "/tmp/builders_r04.py",
    ),
    (
        "r12",
        "ttf_r12_gen.py",
        "tmp-root--b4b9fdb4a3dc/versions/v0004/ttf_r12_gen.py",
        "422440684f042945fd93431e496824294ec05fb3ec7b750df60640a3ad90e7dc",
        "/tmp/ttf_r12_gen.py",
    ),
    (
        "r24",
        "tail_r24.py",
        "ttf-r24-live--1b54e5bfc24d/versions/v0001/tail_r24.py",
        "6b449f3ea0c09158b98efe8bae2f9c2cd45d7d65d7b7ab9f223a57a81abc2fa9",
        "/tmp/tail_r24.py",
    ),
    (
        "r72",
        "gen_r72.py",
        "ttf-r72-live--d95f8fb37739/versions/v0001/gen_r72.py",
        "36cf5ca30686624bc445067f891042a7686537748a98518f749819050592642a",
        "/tmp/gen_r72.py",
    ),
)
SLICE_IDS = tuple(item[0] for item in SOURCE_CATALOGS)
FULL_PLANT_COUNT = len(SOURCE_CATALOGS) * QUOTA_PER_ROUND

FINDING_AST_NOT_A_PLANT = "CATALOG_AST_NOT_A_PLANT"
FINDING_CATALOG_EMPTY = "CATALOG_EMPTY"
FINDING_CATALOG_FILE_MISSING = "CATALOG_FILE_MISSING"
FINDING_CATALOG_SLICE_STRIDE = "CATALOG_SLICE_STRIDE"
FINDING_DESTINATION_EXISTS = "DESTINATION_EXISTS"
FINDING_DESTINATION_UNDER_RAW = "DESTINATION_UNDER_RAW"
FINDING_DUPLICATE_ID = "CATALOG_DUPLICATE_ID"
FINDING_FIELD_INVALID = "CATALOG_FIELD_INVALID"
FINDING_FIELD_MISSING = "CATALOG_FIELD_MISSING"
FINDING_PLANTS_SHA_MISMATCH = "PLANTS_SHA_MISMATCH"
FINDING_ROUND_OUT_OF_DOMAIN = "ROUND_OUT_OF_DOMAIN"
FINDING_SLICE_OUT_OF_DOMAIN = "SLICE_OUT_OF_DOMAIN"
FINDING_VENDOR_PATH = "VENDOR_PATH_REFUSED"

FINDING_CODES = (
    FINDING_AST_NOT_A_PLANT,
    FINDING_CATALOG_EMPTY,
    FINDING_CATALOG_FILE_MISSING,
    FINDING_CATALOG_SLICE_STRIDE,
    FINDING_DESTINATION_EXISTS,
    FINDING_DESTINATION_UNDER_RAW,
    FINDING_DUPLICATE_ID,
    FINDING_FIELD_INVALID,
    FINDING_FIELD_MISSING,
    FINDING_PLANTS_SHA_MISMATCH,
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


def default_catalog_dir() -> Path:
    return Path(__file__).resolve().parent


__all__ = [
    "CATALOG_FILENAME",
    "CATALOG_ID",
    "CATALOG_SCHEMA",
    "FACTORY",
    "FAMILY_PREFIX",
    "FINDING_AST_NOT_A_PLANT",
    "FINDING_CATALOG_EMPTY",
    "FINDING_CATALOG_FILE_MISSING",
    "FINDING_CATALOG_SLICE_STRIDE",
    "FINDING_CODES",
    "FINDING_CODE_SET",
    "FINDING_DESTINATION_EXISTS",
    "FINDING_DESTINATION_UNDER_RAW",
    "FINDING_DUPLICATE_ID",
    "FINDING_FIELD_INVALID",
    "FINDING_FIELD_MISSING",
    "FINDING_PLANTS_SHA_MISMATCH",
    "FINDING_ROUND_OUT_OF_DOMAIN",
    "FINDING_SLICE_OUT_OF_DOMAIN",
    "FINDING_VENDOR_PATH",
    "FULL_PLANT_COUNT",
    "GENERATOR",
    "INTENDED_USE",
    "LEGACY_COMMIT",
    "LEGACY_REF",
    "LINEAR_ISSUE",
    "PLANTS_FILENAME",
    "PROJECT_TRAINING_POLICY",
    "QUOTA_PER_ROUND",
    "RECORD_KIND",
    "RUN_LABEL",
    "SLICE_IDS",
    "SOURCE_CATALOGS",
    "SOURCE_COMMIT",
    "SOURCE_REF",
    "SOURCE_TREE",
    "VENDOR_NAME_NEEDLES",
    "VENDOR_PREFIXES",
    "TtfRefusal",
    "bind_import_twin",
    "default_catalog_dir",
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
