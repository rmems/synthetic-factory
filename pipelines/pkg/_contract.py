#!/usr/bin/env python3
"""Pinned identity and coded refusals for the PKG release-attestation family.

Constants are AST-extracted from ``experiments/pkg-mill-r163.py`` on
``origin/legacy-mill-lane``. This module is the only place the family names
the factory, generator, quota, source pin, and vendor ban. Mill scripts
are parse input only and are never executed.
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

FAMILY_PREFIX = "pkg"
FACTORY = "package-release-factory"
GENERATOR = "grok-4.6"
GEN = GENERATOR
QUOTA_PER_ROUND = 2
RECORD_KIND = "episode"
CATALOG_ID = "pkg-r163-v1"
SOURCE_REF = "origin/legacy-mill-lane"
SOURCE_COMMIT = "813f93f1969c1c4421e5663492e9663739efa642"
SOURCE_PATH = "experiments/pkg-mill-r163.py"
INTENDED_USE = "research_only"
PROJECT_TRAINING_POLICY = "blocked"
VENDOR_NAME_NEEDLES = (
    "mill",
    "leftover",
    "loop",
)
VENDOR_PREFIXES = (
    "pkg-mill",
    "pkg-loop",
    "pkg_mill",
    "pkgs-",
    "pkgs_",
)

FINDING_AST_NOT_A_PLANT = "CATALOG_AST_NOT_A_PLANT"
FINDING_CATALOG_EMPTY = "CATALOG_EMPTY"
FINDING_CATALOG_PAIR_STRIDE = "CATALOG_PAIR_STRIDE"
FINDING_DESTINATION_EXISTS = "DESTINATION_EXISTS"
FINDING_DESTINATION_UNDER_RAW = "DESTINATION_UNDER_RAW"
FINDING_DUPLICATE_ID = "CATALOG_DUPLICATE_ID"
FINDING_FIELD_INVALID = "CATALOG_FIELD_INVALID"
FINDING_FIELD_MISSING = "CATALOG_FIELD_MISSING"
FINDING_PAIR_INVALID = "PAIR_INVALID"
FINDING_PAIR_OUT_OF_DOMAIN = "PAIR_OUT_OF_DOMAIN"
FINDING_ROUND_OUT_OF_DOMAIN = "ROUND_OUT_OF_DOMAIN"
FINDING_VENDOR_PATH = "VENDOR_PATH_REFUSED"

FINDING_CODES = (
    FINDING_AST_NOT_A_PLANT,
    FINDING_CATALOG_EMPTY,
    FINDING_CATALOG_PAIR_STRIDE,
    FINDING_DESTINATION_EXISTS,
    FINDING_DESTINATION_UNDER_RAW,
    FINDING_DUPLICATE_ID,
    FINDING_FIELD_INVALID,
    FINDING_FIELD_MISSING,
    FINDING_PAIR_INVALID,
    FINDING_PAIR_OUT_OF_DOMAIN,
    FINDING_ROUND_OUT_OF_DOMAIN,
    FINDING_VENDOR_PATH,
)
FINDING_CODE_SET = frozenset(FINDING_CODES)


class PkgRefusal(refusals.CodedRefusal):
    """The family's coded refusal: ``str`` is always ``CODE: prose``."""

    CODES = FINDING_CODE_SET


refuse, refuse_when, refuse_first = refusals.helpers(PkgRefusal)
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
    """Fail closed if any path would vendor a mill, loop, or demoted pkgs script."""

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
    "FINDING_CATALOG_PAIR_STRIDE",
    "FINDING_CODES",
    "FINDING_CODE_SET",
    "FINDING_DESTINATION_EXISTS",
    "FINDING_DESTINATION_UNDER_RAW",
    "FINDING_DUPLICATE_ID",
    "FINDING_FIELD_INVALID",
    "FINDING_FIELD_MISSING",
    "FINDING_PAIR_INVALID",
    "FINDING_PAIR_OUT_OF_DOMAIN",
    "FINDING_ROUND_OUT_OF_DOMAIN",
    "FINDING_VENDOR_PATH",
    "GEN",
    "GENERATOR",
    "INTENDED_USE",
    "PROJECT_TRAINING_POLICY",
    "QUOTA_PER_ROUND",
    "RECORD_KIND",
    "SOURCE_COMMIT",
    "SOURCE_PATH",
    "SOURCE_REF",
    "VENDOR_NAME_NEEDLES",
    "VENDOR_PREFIXES",
    "PkgRefusal",
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
