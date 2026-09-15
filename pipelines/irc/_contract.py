#!/usr/bin/env python3
"""The one place the IRC family reaches main's shared primitives.

Both import forms are supported (``irc.x`` with ``pipelines/`` on ``sys.path``,
and ``pipelines.irc.x`` from the repository root). Every sibling ends with
``bind_import_twin(__name__)`` so the two spellings are one object.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path

if __name__.startswith("pipelines."):
    from ..exact_json import ExactJSONFloat, dumps_exact_json
    from ..mill_reviewed_vocabulary import REVIEWED_MILL_PREFIX_HOMES
    from ..oracle_grounded import envelope, refusals
    from ..oracle_grounded.import_twins import bind_import_twin
    from ..raw_tree_guard import is_under_raw
    from ..tag_jsonutil import reject_duplicate_object_keys, reject_json_constant
else:
    from exact_json import ExactJSONFloat, dumps_exact_json
    from mill_reviewed_vocabulary import REVIEWED_MILL_PREFIX_HOMES
    from oracle_grounded import envelope, refusals
    from oracle_grounded.import_twins import bind_import_twin
    from raw_tree_guard import is_under_raw
    from tag_jsonutil import reject_duplicate_object_keys, reject_json_constant

FAMILY_PREFIX = "irc"
FACTORY = "incident-response-oncall-factory"
GENERATOR = "irc-mill"
SOURCE_GENERATOR = "grok-4.6"
CATALOG_FIRST = 3366
CATALOG_LAST = 3381
N_PAIRS = 16
QUOTA_PER_ROUND = 2
STEPS = 17
NOVEL_COVERAGE = 97
SOURCE_MILL_ID = "irc_r3366_leftover3_mill"
SOURCE_REF = "origin/legacy-mill-lane"
SOURCE_COMMIT = "070f1697804fc5c719da58683a485f045b568ede"
SOURCE_PATH = "experiments/irc_r3366_leftover3_mill.py"
SOURCE_BLOB = "222a25cf0c89c92c2f63af14eab19ef728bb7fb4"
SOURCE_SHA256 = "99608f5b89c4140b9ebc2e8d0e7f469151409fc6c26f067a635edb151b337e51"
FAMILY_LANE_COMMIT = "813f93f1969c1c4421e5663492e9663739efa642"
FAMILY_SOURCE_FILES = 141
DEFERRED_MILLS = 60
FULL_MILL_CATALOGS = 60
COMMITTED_MILL_CATALOGS = 34
FULL_SPEC_ROW_COUNT = 2900
COMMITTED_SPEC_ROW_COUNT = 1848
CATALOG_ID = "irc-family-v1"
CATALOG_SCHEMA = "irc-catalog-v1"
CATALOG_FILENAME = "CATALOG.json"
SPECS_FILENAME = "specs.jsonl"
PIPE_FIELD_NAMES = ("SPECS", "ROWS")
TICKET_BASE = 11265
RUN_FORMAT = "irc-run/1"
RECORDS_FILENAME = "records.jsonl"
RUN_FILENAME = "RUN.json"
NOTES_FILENAME = "NOTES.md"

REVIEWED_HOME = REVIEWED_MILL_PREFIX_HOMES[FAMILY_PREFIX]
if REVIEWED_HOME != FACTORY:
    raise ImportError(
        f"reviewed prefix home for {FAMILY_PREFIX!r} is {REVIEWED_HOME!r}, "
        f"not {FACTORY!r}"
    )

BANNED_KEYS = frozenset(
    {"thought", "chain_of_thought", "scratch", "inner_monologue", "spike_events"}
)
VENDOR_PREFIXES = ("irc-mill-", "irc-loop-", "irc-chain-", "irc-pub-", "irc_r")
VENDOR_SUFFIXES = ("_mill.py", "-mill.py", "-loop.py", "-chain.py")

FINDING_PAIR_NOT_FOUND = "irc.pair_not_found"
FINDING_ROUND_INVALID = "irc.round_invalid"
FINDING_SOURCE_NOT_PARSEABLE = "irc.source_not_parseable"
FINDING_DESTINATION_EXISTS = "irc.destination_exists"
FINDING_DESTINATION_UNDER_RAW = "irc.destination_under_raw"
FINDING_VENDOR_PATH = "irc.vendor_path"
FINDING_BANNED_KEY = "irc.banned_key"
FINDING_USAGE = "irc.usage"
FINDING_CATALOG_FILE_MISSING = "irc.catalog_file_missing"
FINDING_CATALOG_FIELD_MISSING = "irc.catalog_field_missing"
FINDING_CATALOG_FIELD_INVALID = "irc.catalog_field_invalid"
FINDING_CATALOG_SHA256_MISMATCH = "irc.catalog_sha256_mismatch"
FINDING_CODES = (
    FINDING_PAIR_NOT_FOUND,
    FINDING_ROUND_INVALID,
    FINDING_SOURCE_NOT_PARSEABLE,
    FINDING_DESTINATION_EXISTS,
    FINDING_DESTINATION_UNDER_RAW,
    FINDING_VENDOR_PATH,
    FINDING_BANNED_KEY,
    FINDING_USAGE,
    FINDING_CATALOG_FILE_MISSING,
    FINDING_CATALOG_FIELD_MISSING,
    FINDING_CATALOG_FIELD_INVALID,
    FINDING_CATALOG_SHA256_MISMATCH,
)
FINDING_CODE_SET = frozenset(FINDING_CODES)


class IrcRefusal(refusals.CodedRefusal):
    """Fail-closed IRC refusal. ``str`` is always ``CODE: prose``."""

    CODES = FINDING_CODE_SET


refuse, refuse_when, refuse_first = refusals.helpers(IrcRefusal)
shown = refusals.shown


def refuse_vendor_paths(paths: Iterable[Path | str]) -> None:
    """Fail closed if any path would vendor an IRC mill / loop / chain script."""

    for raw in paths:
        name = Path(raw).name
        if name.startswith(VENDOR_PREFIXES) or name.endswith(VENDOR_SUFFIXES):
            refuse(FINDING_VENDOR_PATH, f"refusing to vendor {name}")


def require_round(rnd: object) -> int:
    refuse_when(type(rnd) is not int or rnd < 1, FINDING_ROUND_INVALID, shown(rnd))
    return rnd  # type: ignore[return-value]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def package_dir() -> Path:
    return Path(__file__).resolve().parent


def load_strict_json(payload: str | bytes):
    """Keep exact decimal tokens at catalog and record boundaries."""

    return json.loads(
        payload,
        object_pairs_hook=reject_duplicate_object_keys,
        parse_constant=reject_json_constant,
        parse_float=ExactJSONFloat,
    )


__all__ = [
    "BANNED_KEYS",
    "CATALOG_FILENAME",
    "CATALOG_FIRST",
    "CATALOG_ID",
    "CATALOG_LAST",
    "CATALOG_SCHEMA",
    "COMMITTED_MILL_CATALOGS",
    "COMMITTED_SPEC_ROW_COUNT",
    "DEFERRED_MILLS",
    "FACTORY",
    "FAMILY_LANE_COMMIT",
    "FAMILY_PREFIX",
    "FAMILY_SOURCE_FILES",
    "FULL_MILL_CATALOGS",
    "FULL_SPEC_ROW_COUNT",
    "FINDING_BANNED_KEY",
    "FINDING_CATALOG_FIELD_INVALID",
    "FINDING_CATALOG_FIELD_MISSING",
    "FINDING_CATALOG_FILE_MISSING",
    "FINDING_CATALOG_SHA256_MISMATCH",
    "FINDING_CODE_SET",
    "FINDING_CODES",
    "FINDING_DESTINATION_EXISTS",
    "FINDING_DESTINATION_UNDER_RAW",
    "FINDING_PAIR_NOT_FOUND",
    "FINDING_ROUND_INVALID",
    "FINDING_SOURCE_NOT_PARSEABLE",
    "FINDING_USAGE",
    "FINDING_VENDOR_PATH",
    "GENERATOR",
    "IrcRefusal",
    "NOTES_FILENAME",
    "NOVEL_COVERAGE",
    "N_PAIRS",
    "PIPE_FIELD_NAMES",
    "QUOTA_PER_ROUND",
    "RECORDS_FILENAME",
    "REVIEWED_HOME",
    "RUN_FILENAME",
    "RUN_FORMAT",
    "SOURCE_BLOB",
    "SOURCE_COMMIT",
    "SOURCE_GENERATOR",
    "SOURCE_MILL_ID",
    "SOURCE_PATH",
    "SOURCE_REF",
    "SOURCE_SHA256",
    "SPECS_FILENAME",
    "STEPS",
    "TICKET_BASE",
    "VENDOR_PREFIXES",
    "bind_import_twin",
    "dumps_exact_json",
    "envelope",
    "is_under_raw",
    "load_strict_json",
    "package_dir",
    "refuse",
    "repo_root",
    "refuse_first",
    "refuse_vendor_paths",
    "refuse_when",
    "require_round",
    "shown",
]

bind_import_twin(__name__)
