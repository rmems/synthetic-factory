#!/usr/bin/env python3
"""Shared primitives and coded refusals for the ``obs`` mill package.

Both import forms are supported (``obs.x`` with ``pipelines/`` on
``sys.path``, and ``pipelines.obs.x`` from the repository root). Every
module ends with ``bind_import_twin(__name__)`` so the two spellings are
one object.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

if __name__.startswith("pipelines."):
    from ..exact_json import ExactJSONFloat, dumps_exact_json
    from ..oracle_grounded.import_twins import bind_import_twin
    from ..raw_tree_guard import is_under_raw
    from ..tag_jsonutil import reject_duplicate_object_keys, reject_json_constant
else:
    from exact_json import ExactJSONFloat, dumps_exact_json
    from oracle_grounded.import_twins import bind_import_twin
    from raw_tree_guard import is_under_raw
    from tag_jsonutil import reject_duplicate_object_keys, reject_json_constant

FACTORY = "observability-debug-factory"
MILL_PREFIX = "obs"
GENERATOR = "obs-mill"
CATALOG_FORMAT = "obs-catalog/1"
RUN_FORMAT = "obs-run/1"
RECORD_KIND = "episode"
QUOTA_PER_ROUND = 2
DEFAULT_CATALOG_ID = "obs-plants-v1"
SHAPE_HOP = "hop"
SHAPE_LEFTOVER3 = "leftover3"
SHAPE_LEFTOVER_SPEC = "leftover_spec"

SOURCE_REF = "legacy-mill-lane"
SOURCE_COMMIT = "4efb4b3db81efec46c341723087d801683f2051b"
SOURCE_METHOD = "git-show+ast.parse"

CATALOG_FILENAME = "CATALOG.json"
HOP_FILENAME = "hop-plants.jsonl"
LEFTOVER3_FILENAME = "leftover3-pairs.jsonl"
LEFTOVER_SPECS_FILENAME = "leftover-specs.jsonl"
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
    r"^(obs-mill.*\.py|obs-loop.*\.py|_gen_obs_leftover.*\.py|"
    r"obs_r385_leftover3_mill\.py|mill_plants_a[b-i]\.py)$"
)

FINDING_CATALOG_FILE_MISSING = "obs.catalog_file_missing"
FINDING_CATALOG_FIELD_MISSING = "obs.catalog_field_missing"
FINDING_CATALOG_FIELD_INVALID = "obs.catalog_field_invalid"
FINDING_CATALOG_SHA256_MISMATCH = "obs.catalog_sha256_mismatch"
FINDING_PLANT_FIELD_MISSING = "obs.plant_field_missing"
FINDING_PLANT_FIELD_INVALID = "obs.plant_field_invalid"
FINDING_PLANT_DUPLICATE_ID = "obs.plant_duplicate_id"
FINDING_PLANT_NOT_FOUND = "obs.plant_not_found"
FINDING_MILL_NOT_FOUND = "obs.mill_not_found"
FINDING_FACTORY_NOT_REGISTERED = "obs.factory_not_registered"
FINDING_DESTINATION_EXISTS = "obs.destination_exists"
FINDING_DESTINATION_UNDER_RAW = "obs.destination_under_raw"
FINDING_DESTINATION_VENDOR = "obs.destination_vendor"
FINDING_SOURCE_NOT_PARSEABLE = "obs.source_not_parseable"
FINDING_BANNED_KEY = "obs.banned_key"
FINDING_USAGE = "obs.usage"
FINDING_ROUND_INVALID = "obs.round_invalid"
FINDING_SHAPE_UNSUPPORTED = "obs.shape_unsupported"

__all__ = [
    "BANNED_KEYS",
    "CATALOG_FILENAME",
    "CATALOG_FORMAT",
    "DEFAULT_CATALOG_ID",
    "FACTORY",
    "FINDING_BANNED_KEY",
    "FINDING_CATALOG_FIELD_INVALID",
    "FINDING_CATALOG_FIELD_MISSING",
    "FINDING_CATALOG_FILE_MISSING",
    "FINDING_CATALOG_SHA256_MISMATCH",
    "FINDING_DESTINATION_EXISTS",
    "FINDING_DESTINATION_UNDER_RAW",
    "FINDING_DESTINATION_VENDOR",
    "FINDING_FACTORY_NOT_REGISTERED",
    "FINDING_MILL_NOT_FOUND",
    "FINDING_PLANT_DUPLICATE_ID",
    "FINDING_PLANT_FIELD_INVALID",
    "FINDING_PLANT_FIELD_MISSING",
    "FINDING_PLANT_NOT_FOUND",
    "FINDING_ROUND_INVALID",
    "FINDING_SHAPE_UNSUPPORTED",
    "FINDING_SOURCE_NOT_PARSEABLE",
    "FINDING_USAGE",
    "GENERATOR",
    "HOP_FILENAME",
    "LEFTOVER3_FILENAME",
    "LEFTOVER_SPECS_FILENAME",
    "MILL_PREFIX",
    "NOTES_FILENAME",
    "ObsRefusal",
    "QUOTA_PER_ROUND",
    "RECORD_KIND",
    "RECORDS_FILENAME",
    "RUN_FILENAME",
    "RUN_FORMAT",
    "SHAPE_HOP",
    "SHAPE_LEFTOVER3",
    "SHAPE_LEFTOVER_SPEC",
    "SOURCE_COMMIT",
    "SOURCE_METHOD",
    "SOURCE_REF",
    "VENDOR_NAME_RE",
    "bind_import_twin",
    "dumps_exact_json",
    "is_under_raw",
    "load_strict_json",
    "refuse_vendor_path",
    "repo_root",
]


class ObsRefusal(Exception):
    """A coded, fail-closed refusal. ``str`` is ``CODE: prose``."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_strict_json(payload: str | bytes):
    """Keep exact decimal tokens at catalog and record boundaries."""

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
        if VENDOR_NAME_RE.fullmatch(part):
            raise ObsRefusal(
                FINDING_DESTINATION_VENDOR,
                f"destination {resolved} names vendored mill script {part!r}",
            )
    if resolved.exists() and resolved.is_dir():
        for child in resolved.rglob("*"):
            if VENDOR_NAME_RE.fullmatch(child.name):
                raise ObsRefusal(
                    FINDING_DESTINATION_VENDOR,
                    f"destination {resolved} contains vendored mill script {child.name!r}",
                )


bind_import_twin(__name__)
