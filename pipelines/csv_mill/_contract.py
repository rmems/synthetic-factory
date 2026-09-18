#!/usr/bin/env python3
"""Shared primitives for the csv leftover-mill family (code_repair _contract).

Both import forms are supported (``csv_mill.x`` with ``pipelines/`` on ``sys.path``,
and ``pipelines.csv_mill.x`` from the repository root). Every module ends with
``bind_import_twin(__name__)`` so the two spellings are one object.

The reviewed mill-prefix home is ``cei`` → ``csv-excel-ingest-factory``.
``FAMILY`` is the package slice name; leftover mill scripts stay on
``legacy-mill-lane`` and are never vendored or executed.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass, fields
from pathlib import Path

if __name__.startswith("pipelines."):
    from ..exact_json import ExactJSONFloat
    from .. import exact_json as _exact_json
    from ..mill_reviewed_vocabulary import REVIEWED_MILL_PREFIX_HOMES
    from .. import oracle_grounded as _oracle_grounded
    from ..oracle_grounded import refusals
    from ..oracle_grounded.import_twins import bind_import_twin
    from .. import raw_tree_guard as _raw_tree_guard
    from ..tag_jsonutil import reject_duplicate_object_keys, reject_json_constant
else:
    from exact_json import ExactJSONFloat
    import exact_json as _exact_json
    from mill_reviewed_vocabulary import REVIEWED_MILL_PREFIX_HOMES
    import oracle_grounded as _oracle_grounded
    from oracle_grounded import refusals
    from oracle_grounded.import_twins import bind_import_twin
    import raw_tree_guard as _raw_tree_guard
    from tag_jsonutil import reject_duplicate_object_keys, reject_json_constant

dumps_exact_json = _exact_json.dumps_exact_json
envelope = _oracle_grounded.envelope
is_under_raw = _raw_tree_guard.is_under_raw

FAMILY = "csv"
FACTORY = "csv-excel-ingest-factory"
REVIEWED_PREFIX = "cei"
RECORD_PREFIX = REVIEWED_PREFIX
GENERATOR = "csv-mill"
MILL_PREFIX = "csv"
CATALOG_FORMAT = "csv-catalog/1"
RUN_FORMAT = "csv-run/1"
RECORD_KIND = "episode"
QUOTA_PER_ROUND = 2
DEFAULT_CATALOG_ID = "csv-lll-v1"
SOURCE_ROUND = 114
LEGACY_REF = "legacy-mill-lane"
LEGACY_COMMIT = "813f93f1969c1c4421e5663492e9663739efa642"
LEGACY_SOURCE = "experiments/mill_leftover_leftover_leftover_csv_r114.py"
DECISION_BASIS_LIMIT = 240
DECISION_BASIS_PREFIXES = frozenset({"Plan", "Observation", "Reflection", "Tool call"})

CATALOG_FILENAME = "CATALOG.json"
PLANTS_FILENAME = "plants.jsonl"
RECORDS_FILENAME = "records.jsonl"
RUN_FILENAME = "RUN.json"
NOTES_FILENAME = "NOTES.md"


@dataclass(frozen=True)
class PairFields:
    """One authoritative schema for the recovered success/handoff pair fields."""

    slug: str
    fail: str
    mod: str
    drop: str
    keep: str
    naive: str
    stack: str
    drop_stack: str
    doc: str
    doc2: str
    domain: str
    ticket: str
    test_ok: str
    test_fail: str
    short: str
    dshort: str
    first_wrong: str


PAIR_KEYS = tuple(field.name for field in fields(PairFields))

BANNED_KEYS = frozenset(
    {
        "thought",
        "chain_of_thought",
        "scratch",
        "inner_monologue",
        "spike_events",
    }
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
FINDING_DESTINATION_INVALID = "DESTINATION_INVALID"
FINDING_DESTINATION_UNDER_RAW = "DESTINATION_UNDER_RAW"
FINDING_SOURCE_NOT_PARSEABLE = "SOURCE_NOT_PARSEABLE"
FINDING_BANNED_KEY = "BANNED_KEY"
FINDING_USAGE = "USAGE"
FINDING_ROUND_INVALID = "ROUND_INVALID"
FINDING_DECISION_BASIS = "DECISION_BASIS"
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
    FINDING_DESTINATION_INVALID,
    FINDING_DESTINATION_UNDER_RAW,
    FINDING_SOURCE_NOT_PARSEABLE,
    FINDING_BANNED_KEY,
    FINDING_USAGE,
    FINDING_ROUND_INVALID,
    FINDING_DECISION_BASIS,
    FINDING_VENDOR_PATH,
)
FINDING_CODE_SET = frozenset(FINDING_CODES)

REVIEWED_HOME = REVIEWED_MILL_PREFIX_HOMES[REVIEWED_PREFIX]
if REVIEWED_HOME != FACTORY:
    raise ImportError(
        f"reviewed prefix home for {REVIEWED_PREFIX!r} is {REVIEWED_HOME!r}, "
        f"not the csv factory {FACTORY!r}"
    )


class CsvRefusal(refusals.CodedRefusal):
    """The family's coded refusal: ``str`` is always ``CODE: prose``."""

    CODES = FINDING_CODE_SET


refuse, refuse_when, refuse_first = refusals.helpers(CsvRefusal)
shown = refusals.shown

# The vocabulary exports every coded finding along with the pinned constants.
# Explicit helper exports keep implementation imports out of the public surface.
__all__ = [name for name in globals() if name.isupper()] + [
    "CsvRefusal",
    "PairFields",
    "bind_import_twin",
    "dumps_exact_json",
    "envelope",
    "is_under_raw",
    "is_integer",
    "load_strict_json",
    "refuse",
    "refuse_first",
    "refuse_vendor_paths",
    "refuse_when",
    "refusals",
    "repo_root",
    "shown",
]


def is_integer(value: object) -> bool:
    """JSON integer domain, excluding booleans."""
    return isinstance(value, int) and not isinstance(value, bool)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_strict_json(payload: str | bytes):
    """Keep exact decimal tokens at csv catalog and record boundaries."""

    return json.loads(
        payload,
        object_pairs_hook=reject_duplicate_object_keys,
        parse_constant=reject_json_constant,
        parse_float=ExactJSONFloat,
    )


def refuse_vendor_paths(paths: Iterable[Path | str]) -> None:
    """Fail closed if any path would vendor a leftover mill or hop loop."""

    for raw in paths:
        name = Path(raw).name
        lowered = name.lower()
        if "mill" in lowered and lowered.endswith(".py"):
            raise CsvRefusal(FINDING_VENDOR_PATH, f"refusing to vendor {name}")
        if "-loop-" in lowered and lowered.endswith(".py"):
            raise CsvRefusal(FINDING_VENDOR_PATH, f"refusing to vendor {name}")


bind_import_twin(__name__)
