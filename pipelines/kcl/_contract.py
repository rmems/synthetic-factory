#!/usr/bin/env python3
"""Shared primitives and coded refusals for the ``kcl`` mill package.

Both import forms are supported (``kcl.x`` with ``pipelines/`` on
``sys.path``, and ``pipelines.kcl.x`` from the repository root). Every
module ends with ``bind_import_twin(__name__)`` so the two spellings are
one object.
"""

from __future__ import annotations

import json
from pathlib import Path

if __name__.startswith("pipelines."):
    from ..exact_json import ExactJSONFloat, dumps_exact_json
    from ..oracle_grounded import refusals
    from ..oracle_grounded.import_twins import bind_import_twin
    from ..raw_tree_guard import is_under_raw
    from ..tag_jsonutil import reject_duplicate_object_keys, reject_json_constant
else:
    from exact_json import ExactJSONFloat, dumps_exact_json
    from oracle_grounded import refusals
    from oracle_grounded.import_twins import bind_import_twin
    from raw_tree_guard import is_under_raw
    from tag_jsonutil import reject_duplicate_object_keys, reject_json_constant

FACTORY = "k8s-crashloop-factory"
FAMILY_PREFIX = "kcl"
GENERATOR = "kcl-mill"
HOPPER_WAVE = "g46c"
CATALOG_FORMAT = "kcl-catalog/1"
DEFAULT_CATALOG_ID = "kcl-plants-v1"
CATALOG_SLICE = "identities"
ROW_KIND_REPRESENTATIVE = "representative"
ROW_KIND_IDENTITY = "identity"
REPRESENTATIVE_BODY_COUNT = 12
FULL_PLANT_COUNT = 705
FULL_PAIR_COUNT = 478
FULL_ROW_COUNT = 227
RECORD_KIND = "episode"
QUOTA_PER_ROUND = 2
SUCCESS_STEPS = 16
HANDOFF_STEPS = 18
SHAPE_PAIR = "pair"
SHAPE_ROW = "row"

CATALOG_FILENAME = "CATALOG.json"
PLANTS_FILENAME = "plants.jsonl"
DEFAULT_CATALOG = Path("config") / "kcl"
LEGACY_REF = "legacy-mill-lane"
LEGACY_COMMIT = "813f93f1969c1c4421e5663492e9663739efa642"
EXTRACT_METHOD = "git-show+ast.parse"

PAIR_KEYS = (
    "plant",
    "app",
    "chart",
    "slug",
    "field",
    "fail_val",
    "fix_val",
    "hide_path",
    "hide_old",
    "hide_new",
    "values_fail",
    "values_fix",
    "tpl",
    "log",
    "live_ok",
    "hide_name",
    "new_vs",
    "seed",
    "n2",
    "ci",
    "handoff",
    "pytest_ok",
    "pytest_fail",
    "tmpl_test",
    "rs",
)
ROW_KEYS = (
    "idx",
    "plant",
    "slug",
    "field",
    "fail",
    "fix",
    "hide_key",
    "hide_old",
    "hide_new",
    "crash",
    "new_vs",
)

BANNED_KEYS = frozenset(
    {
        "thought",
        "chain_of_thought",
        "scratch",
        "inner_monologue",
        "spike_events",
    }
)
BANNED_PLANTS = frozenset(
    {
        "bay-prod",
        "cwm-prod",
        "llyn-prod",
        "atoll-prod",
        "kyle-prod",
        "voe-prod",
        "tarn-prod",
        "lough-prod",
        "weald-prod",
        "fen-prod",
    }
)
BANNED_NEEDLES = (
    "unconfined",
    "webhook",
    "ipfamilies",
    "internaltrafficpolicy",
    "externaltrafficpolicy",
    "allocateloadbalancernodeports",
    "bitbucket_home",
    "keycloak_home",
    "bay-prod",
    "apparmor",
)
BANNED_ID_TOKENS = ("-w3-empty", "sx-handoff")
VENDOR_GLOBS = ("kcl-mill*.py", "kcl-loop*.py", "kcl-hop-mill*.py", "hopper_mill_g46c.py")

# mill_id, base_round, source path, extract shape
# pair() kwargs *or* module-level PAIRS: list[dict] = [{...}, ...] literals.
# kcl-loop / kcl-hop-mill / kcl-mill-r1443.py / kcl-mill-r1644.py are
# drivers (they exec plants or hopper_mill_*); hop replay uses hopper g46c.
SOURCE_MILLS = (
    ("kcl_r1007", 1007, "experiments/kcl-mill-r1007.py", SHAPE_PAIR),
    ("kcl_pref", 1076, "experiments/kcl-mill-pref.py", SHAPE_PAIR),
    ("kcl_u1092", 1092, "experiments/kcl-mill-unique-r1092.py", SHAPE_PAIR),
    ("kcl_r1092", 1092, "experiments/kcl-mill-r1092.py", SHAPE_PAIR),
    ("kcl_r1152", 1152, "experiments/kcl-mill-r1152.py", SHAPE_PAIR),
    ("kcl_r1216", 1216, "experiments/kcl-mill-r1216.py", SHAPE_PAIR),
    ("kcl_r1236", 1236, "experiments/kcl-mill-r1236.py", SHAPE_PAIR),
    ("kcl_r1266", 1266, "experiments/kcl-mill-r1266.py", SHAPE_PAIR),
    ("kcl_r1379", 1379, "experiments/kcl-mill-lll-r1379.py", SHAPE_PAIR),
    ("kcl_r1443", 1443, "experiments/kcl-plants-r1443.py", SHAPE_ROW),
    ("kcl_r1644", 1644, "experiments/kcl-plants-r1644.py", SHAPE_ROW),
)
# Full leftover extract sizes. The committed plants.jsonl is a representative
# slice; bulky dumps are kcl-mill-r1007.py (141) and kcl-plants-r1443.py (195).
FULL_MILL_COUNTS = (
    ("kcl_r1007", 141),
    ("kcl_pref", 16),
    ("kcl_u1092", 12),
    ("kcl_r1092", 32),
    ("kcl_r1152", 64),
    ("kcl_r1216", 20),
    ("kcl_r1236", 160),
    ("kcl_r1266", 16),
    ("kcl_r1379", 17),
    ("kcl_r1443", 195),
    ("kcl_r1644", 32),
)

FINDING_CATALOG_FILE_MISSING = "kcl.catalog_file_missing"
FINDING_CATALOG_FIELD_MISSING = "kcl.catalog_field_missing"
FINDING_CATALOG_FIELD_INVALID = "kcl.catalog_field_invalid"
FINDING_CATALOG_SHA256_MISMATCH = "kcl.catalog_sha256_mismatch"
FINDING_PLANT_FIELD_MISSING = "kcl.plant_field_missing"
FINDING_PLANT_FIELD_INVALID = "kcl.plant_field_invalid"
FINDING_PLANT_DUPLICATE = "kcl.plant_duplicate"
FINDING_PLANT_NOT_FOUND = "kcl.plant_not_found"
FINDING_PLANT_IDENTITY_ONLY = "kcl.plant_identity_only"
FINDING_MILL_NOT_FOUND = "kcl.mill_not_found"
FINDING_FACTORY_NOT_REGISTERED = "kcl.factory_not_registered"
FINDING_DESTINATION_EXISTS = "kcl.destination_exists"
FINDING_DESTINATION_UNDER_RAW = "kcl.destination_under_raw"
FINDING_SOURCE_NOT_PARSEABLE = "kcl.source_not_parseable"
FINDING_BANNED = "kcl.banned"
FINDING_USAGE = "kcl.usage"
FINDING_ROUND_INVALID = "kcl.round_invalid"
FINDING_VENDOR_PATH = "kcl.vendor_path"
FINDING_UNKNOWN_WAVE = "kcl.unknown_wave"

FINDING_CODES = frozenset(
    {
        FINDING_CATALOG_FILE_MISSING,
        FINDING_CATALOG_FIELD_MISSING,
        FINDING_CATALOG_FIELD_INVALID,
        FINDING_CATALOG_SHA256_MISMATCH,
        FINDING_PLANT_FIELD_MISSING,
        FINDING_PLANT_FIELD_INVALID,
        FINDING_PLANT_DUPLICATE,
        FINDING_PLANT_NOT_FOUND,
        FINDING_PLANT_IDENTITY_ONLY,
        FINDING_MILL_NOT_FOUND,
        FINDING_FACTORY_NOT_REGISTERED,
        FINDING_DESTINATION_EXISTS,
        FINDING_DESTINATION_UNDER_RAW,
        FINDING_SOURCE_NOT_PARSEABLE,
        FINDING_BANNED,
        FINDING_USAGE,
        FINDING_ROUND_INVALID,
        FINDING_VENDOR_PATH,
        FINDING_UNKNOWN_WAVE,
    }
)


class KclRefusal(refusals.CodedRefusal):
    """A coded refusal from the kcl catalog, generator, or hop replay."""

    CODES = FINDING_CODES


refuse, refuse_when, refuse_first = refusals.helpers(KclRefusal)


def load_strict_json(payload: str | bytes):
    """Keep exact decimal tokens at kcl catalog and episode boundaries."""

    return json.loads(
        payload,
        object_pairs_hook=reject_duplicate_object_keys,
        parse_constant=reject_json_constant,
        parse_float=ExactJSONFloat,
    )


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def default_catalog_dir(root: Path | None = None) -> Path:
    return (root or repo_root()) / DEFAULT_CATALOG


__all__ = [
    "BANNED_ID_TOKENS",
    "BANNED_KEYS",
    "BANNED_NEEDLES",
    "BANNED_PLANTS",
    "CATALOG_FILENAME",
    "CATALOG_FORMAT",
    "CATALOG_SLICE",
    "REPRESENTATIVE_BODY_COUNT",
    "ROW_KIND_IDENTITY",
    "ROW_KIND_REPRESENTATIVE",
    "DEFAULT_CATALOG",
    "DEFAULT_CATALOG_ID",
    "EXTRACT_METHOD",
    "FACTORY",
    "FAMILY_PREFIX",
    "FINDING_CODES",
    "FULL_MILL_COUNTS",
    "FULL_PAIR_COUNT",
    "FULL_PLANT_COUNT",
    "FULL_ROW_COUNT",
    "GENERATOR",
    "HANDOFF_STEPS",
    "HOPPER_WAVE",
    "KclRefusal",
    "LEGACY_COMMIT",
    "LEGACY_REF",
    "PAIR_KEYS",
    "PLANTS_FILENAME",
    "QUOTA_PER_ROUND",
    "RECORD_KIND",
    "ROW_KEYS",
    "SHAPE_PAIR",
    "SHAPE_ROW",
    "SOURCE_MILLS",
    "SUCCESS_STEPS",
    "VENDOR_GLOBS",
    "bind_import_twin",
    "default_catalog_dir",
    "dumps_exact_json",
    "is_under_raw",
    "load_strict_json",
    "refuse",
    "refuse_first",
    "refuse_when",
    "repo_root",
]


bind_import_twin(__name__)
