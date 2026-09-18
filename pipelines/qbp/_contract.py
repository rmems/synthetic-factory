#!/usr/bin/env python3
"""The one place the qbp family reaches main's shared primitives.

Both import forms are supported (``qbp.x`` with ``pipelines/`` on ``sys.path``,
and ``pipelines.qbp.x`` from the repository root); this shim resolves the
import twin binder, exact JSON, the reviewed mill-identity table, hopper
replay builders, and the raw-tree guard under one name each. Every other
module imports only its siblings and ``_contract``. Every module ends with
``bind_import_twin(__name__)``.
"""

from __future__ import annotations

import json
from pathlib import Path

if __name__.startswith("pipelines."):
    from ..exact_json import ExactJSONFloat, dumps_exact_json
    from ..hopper import episode as hopper_episode
    from ..hopper.notes import notes_md as hopper_notes_md
    from ..mill_family import REVIEWED_MILL_PREFIX_HOMES
    from ..oracle_grounded import envelope, refusals
    from ..oracle_grounded.import_twins import bind_import_twin
    from ..raw_tree_guard import is_under_raw
    from ..tag_jsonutil import reject_duplicate_object_keys, reject_json_constant
else:
    from exact_json import ExactJSONFloat, dumps_exact_json
    from hopper import episode as hopper_episode
    from hopper.notes import notes_md as hopper_notes_md
    from mill_family import REVIEWED_MILL_PREFIX_HOMES
    from oracle_grounded import envelope, refusals
    from oracle_grounded.import_twins import bind_import_twin
    from raw_tree_guard import is_under_raw
    from tag_jsonutil import reject_duplicate_object_keys, reject_json_constant

SCHEMA_ID = "qbp-catalog/v1"
FAMILY_PREFIX = "qbp"
FACTORY = "queue-backpressure-factory"
GENERATOR = "grok-4.6"
N_MILLS = 6
N_PAIRS = 100
QUOTA_PER_ROUND = 2
SUCCESS_STEPS = 16
HANDOFF_STEPS = 17
DEFAULT_CATALOG = Path("config") / "qbp" / "CATALOG.json"
PAIRS_FILENAME = "pairs.jsonl"
LEGACY_LANE = "legacy-mill-lane"
LEGACY_COMMIT = "813f93f1969c1c4421e5663492e9663739efa642"
BAN = frozenset({"disruptor-buffer-vs-timeout", "chronicle-cycle-handoff"})

# mill_id, mill path, mill sha256, plants path, plants sha256, catalog_first, n_pairs
MILL_SOURCES = (
    (
        "qbp-mill-leftover3-r42",
        "experiments/qbp-mill-leftover3-r42.py",
        "d291ce517fb80e855f6be9ba278fd3c04e90b1ec49116c08c1593f1efa6f4f12",
        "experiments/qbp-plants-leftover3.py",
        "9193406db332d2e633f84dde034602885c238d90c04a84b68780e51aaf512779",
        42,
        16,
    ),
    (
        "qbp-mill-leftover3-r58",
        "experiments/qbp-mill-leftover3-r58.py",
        "9f7455a9be3e6840e453edeff7db05bffe5ca9ece343c147be8dab97c419f80c",
        "experiments/qbp-plants-leftover3-r58.py",
        "6aa4a028ef07b2a0f6a25cb6e2235cf41533132e86c574ae8a5179a5a00be4f1",
        58,
        16,
    ),
    (
        "qbp-mill-leftover3-r74",
        "experiments/qbp-mill-leftover3-r74.py",
        "a965e178e9c99c7024aa3e8804e6c3ca438fba7559395984c7a54794bdd7b4c4",
        "experiments/qbp-plants-leftover3-r74.py",
        "6735cd5c79c11d9093a69360f4a8c15c23a2870eae3b6fa2f1924b27f38b90d1",
        74,
        16,
    ),
    (
        "qbp-mill-r74",
        "experiments/qbp-mill-r74.py",
        "274944cf47fdb3088798b5529a242064da5b66ba94c004866fd6ad970bafe8fd",
        "experiments/qbp-plants-r74.py",
        "a4033cff41539162c78b5bd8da4e677cd0e35a5ea4744aa17181ded71da58d8b",
        74,
        20,
    ),
    (
        "qbp-mill-leftover-lll-r77",
        "experiments/qbp-mill-leftover-lll-r77.py",
        "6ea92813e89e552a4623ace3d21fe643f4c2638d9e56ae55faa36a7cc9b4bb45",
        "experiments/qbp-plants-leftover-lll-r77.py",
        "ff312b8b8772b206137f7c9eb18114971e68fda3d456ac5ff3fe07896740d1ef",
        77,
        16,
    ),
    (
        "qbp-mill-r94",
        "experiments/qbp-mill-r94.py",
        "4d98c0a4a67a311e6f2fbf2545a56a4b3277ed2fd7d89518b3245f6c21bd4a5d",
        "experiments/qbp-plants-r94.py",
        "2bd489102d1e4e89d9bae6f7e0bb7f7297e376bd4efb6138f1b0f320db8f7a30",
        94,
        16,
    ),
)
MILL_IDS = tuple(row[0] for row in MILL_SOURCES)
MILL_PATHS = tuple(row[1] for row in MILL_SOURCES)

REVIEWED_HOME = REVIEWED_MILL_PREFIX_HOMES[FAMILY_PREFIX]
if REVIEWED_HOME != FACTORY:  # pragma: no cover - the table pin is the authority
    raise ImportError(
        f"reviewed prefix home for {FAMILY_PREFIX!r} is {REVIEWED_HOME!r}, "
        f"not the qbp factory {FACTORY!r}"
    )

FINDING_CATALOG_NOT_AN_OBJECT = "qbp.catalog.not_an_object"
FINDING_CATALOG_SCHEMA = "qbp.catalog.schema"
FINDING_CATALOG_FIELD_MISSING = "qbp.catalog.field_missing"
FINDING_CATALOG_FIELD_INVALID = "qbp.catalog.field_invalid"
FINDING_CATALOG_PAIR_COUNT = "qbp.catalog.pair_count"
FINDING_CATALOG_DUPLICATE = "qbp.catalog.duplicate"
FINDING_CATALOG_BANNED = "qbp.catalog.banned"
FINDING_CATALOG_PLANT = "qbp.catalog.plant"
FINDING_CATALOG_MILL = "qbp.catalog.mill"
FINDING_PAIRS_SHA_MISMATCH = "qbp.catalog.pairs_sha"
FINDING_GENERATE_RAW_TREE = "qbp.generate.raw_tree"
FINDING_GENERATE_DEST_EXISTS = "qbp.generate.dest_exists"
FINDING_GENERATE_ROUND = "qbp.generate.round"
FINDING_GENERATE_MILL = "qbp.generate.mill"
FINDING_GENERATE_SHAPE = "qbp.generate.shape"
FINDING_USAGE = "qbp.usage"

FINDING_CODES = frozenset(
    {
        FINDING_CATALOG_NOT_AN_OBJECT,
        FINDING_CATALOG_SCHEMA,
        FINDING_CATALOG_FIELD_MISSING,
        FINDING_CATALOG_FIELD_INVALID,
        FINDING_CATALOG_PAIR_COUNT,
        FINDING_CATALOG_DUPLICATE,
        FINDING_CATALOG_BANNED,
        FINDING_CATALOG_PLANT,
        FINDING_CATALOG_MILL,
        FINDING_PAIRS_SHA_MISMATCH,
        FINDING_GENERATE_RAW_TREE,
        FINDING_GENERATE_DEST_EXISTS,
        FINDING_GENERATE_ROUND,
        FINDING_GENERATE_MILL,
        FINDING_GENERATE_SHAPE,
        FINDING_USAGE,
    }
)


class QbpRefusal(refusals.CodedRefusal):
    """A coded refusal from the qbp catalog or generator."""

    CODES = FINDING_CODES


refuse, refuse_when, refuse_first = refusals.helpers(QbpRefusal)


def load_strict_json(payload: str | bytes):
    """Keep exact decimal tokens at qbp catalog boundaries."""

    return json.loads(
        payload,
        object_pairs_hook=reject_duplicate_object_keys,
        parse_constant=reject_json_constant,
        parse_float=ExactJSONFloat,
    )


def load_pair_json(payload: str | bytes):
    """Load compact constructor-arg rows; plant numbers stay plain Python floats."""

    return json.loads(
        payload,
        object_pairs_hook=reject_duplicate_object_keys,
        parse_constant=reject_json_constant,
    )


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def default_catalog_path(root: Path | None = None) -> Path:
    return (root or repo_root()) / DEFAULT_CATALOG


def default_pairs_path(catalog_path: Path) -> Path:
    return catalog_path.parent / PAIRS_FILENAME


__all__ = [
    "BAN",
    "DEFAULT_CATALOG",
    "FACTORY",
    "FAMILY_PREFIX",
    "FINDING_CODES",
    "GENERATOR",
    "HANDOFF_STEPS",
    "LEGACY_COMMIT",
    "LEGACY_LANE",
    "MILL_IDS",
    "MILL_PATHS",
    "MILL_SOURCES",
    "N_MILLS",
    "N_PAIRS",
    "PAIRS_FILENAME",
    "QUOTA_PER_ROUND",
    "QbpRefusal",
    "SCHEMA_ID",
    "SUCCESS_STEPS",
    "bind_import_twin",
    "default_catalog_path",
    "default_pairs_path",
    "dumps_exact_json",
    "envelope",
    "hopper_episode",
    "hopper_notes_md",
    "is_under_raw",
    "load_pair_json",
    "load_strict_json",
    "refuse",
    "refuse_first",
    "refuse_when",
    "repo_root",
]


bind_import_twin(__name__)
