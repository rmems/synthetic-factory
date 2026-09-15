#!/usr/bin/env python3
"""Pinned identity and coded refusals for the mac mill family.

Constants are AST-extracted from leftover multi-agent-coordination mills
on ``origin/legacy-mill-lane``. Mill scripts are parse input only and
are never executed.
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

FAMILY_PREFIX = "mac"
FACTORY = "multi-agent-coordination-factory"
GENERATOR = "grok-4.6"
QUOTA_PER_ROUND = 1
RECORD_KIND = "multi_agent"
CATALOG_ID = "mac-leftover-v1"
CATALOG_SCHEMA = "mac-catalog-v1"
CATALOG_FILENAME = "CATALOG.json"
SOURCE_REF = "origin/legacy-mill-lane"
SOURCE_COMMIT = "813f93f1969c1c4421e5663492e9663739efa642"
INTENDED_USE = "research_only"
PROJECT_TRAINING_POLICY = "blocked"

VENDOR_PREFIXES = (
    "mac-mill",
    "mac-hop-loop",
    "_gen_mac",
)
VENDOR_SUFFIXES = ("_mill.py",)

FINDING_AST_NOT_A_PLANT = "CATALOG_AST_NOT_A_PLANT"
FINDING_CATALOG_EMPTY = "CATALOG_EMPTY"
FINDING_CATALOG_FILE_MISSING = "CATALOG_FILE_MISSING"
FINDING_CATALOG_FIELD_INVALID = "CATALOG_FIELD_INVALID"
FINDING_CATALOG_FIELD_MISSING = "CATALOG_FIELD_MISSING"
FINDING_DUPLICATE_FAMILY = "CATALOG_DUPLICATE_FAMILY"
FINDING_FIELD_INVALID = "CATALOG_FIELD_INVALID"
FINDING_FIELD_MISSING = "CATALOG_FIELD_MISSING"
FINDING_SOURCE_NOT_PARSEABLE = "SOURCE_NOT_PARSEABLE"
FINDING_VENDOR_PATH = "VENDOR_PATH_REFUSED"

FINDING_CODES = (
    FINDING_AST_NOT_A_PLANT,
    FINDING_CATALOG_EMPTY,
    FINDING_CATALOG_FILE_MISSING,
    FINDING_CATALOG_FIELD_INVALID,
    FINDING_CATALOG_FIELD_MISSING,
    FINDING_DUPLICATE_FAMILY,
    FINDING_FIELD_INVALID,
    FINDING_FIELD_MISSING,
    FINDING_SOURCE_NOT_PARSEABLE,
    FINDING_VENDOR_PATH,
)
FINDING_CODE_SET = frozenset(FINDING_CODES)


class MacRefusal(refusals.CodedRefusal):
    """The family's coded refusal: ``str`` is always ``CODE: prose``."""

    CODES = FINDING_CODE_SET


refuse, refuse_when, refuse_first = refusals.helpers(MacRefusal)
shown = refusals.shown


def is_vendor_filename(name: str) -> bool:
    """True when ``name`` is a mac mill, hop-loop, or leftover3 publisher."""

    if not name.endswith(".py"):
        return False
    if name.startswith(VENDOR_PREFIXES):
        return True
    return name.startswith("mac_") and name.endswith(VENDOR_SUFFIXES)


def refuse_vendor_paths(paths: Iterable[Path | str]) -> None:
    """Fail closed if any path would vendor a mac mill publisher."""

    for raw in paths:
        name = Path(raw).name
        refuse_when(
            is_vendor_filename(name),
            FINDING_VENDOR_PATH,
            f"refusing to vendor {name}",
        )


def package_dir() -> Path:
    return Path(__file__).resolve().parent


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_strict_json(payload: str | bytes):
    """Keep exact decimal tokens at mac catalog boundaries."""

    return json.loads(
        payload,
        object_pairs_hook=reject_duplicate_object_keys,
        parse_constant=reject_json_constant,
        parse_float=ExactJSONFloat,
    )


__all__ = [
    "CATALOG_FILENAME",
    "CATALOG_ID",
    "CATALOG_SCHEMA",
    "FACTORY",
    "FAMILY_PREFIX",
    "FINDING_AST_NOT_A_PLANT",
    "FINDING_CATALOG_EMPTY",
    "FINDING_CATALOG_FIELD_INVALID",
    "FINDING_CATALOG_FIELD_MISSING",
    "FINDING_CATALOG_FILE_MISSING",
    "FINDING_CODES",
    "FINDING_CODE_SET",
    "FINDING_DUPLICATE_FAMILY",
    "FINDING_FIELD_INVALID",
    "FINDING_FIELD_MISSING",
    "FINDING_SOURCE_NOT_PARSEABLE",
    "FINDING_VENDOR_PATH",
    "GENERATOR",
    "INTENDED_USE",
    "PROJECT_TRAINING_POLICY",
    "QUOTA_PER_ROUND",
    "RECORD_KIND",
    "SOURCE_COMMIT",
    "SOURCE_REF",
    "VENDOR_PREFIXES",
    "MacRefusal",
    "bind_import_twin",
    "dumps_exact_json",
    "envelope",
    "is_under_raw",
    "is_vendor_filename",
    "load_strict_json",
    "package_dir",
    "refuse",
    "refuse_first",
    "refuse_vendor_paths",
    "refuse_when",
    "refusals",
    "repo_root",
    "shown",
]


bind_import_twin(__name__)
