#!/usr/bin/env python3
"""Shared primitives for the hopper family (code_repair _contract pattern).

Both import forms are supported (``hopper.x`` with ``pipelines/`` on
``sys.path``, and ``pipelines.hopper.x`` from the repository root). Every
module ends with ``bind_import_twin(__name__)`` so the two spellings are one
object.
"""

from __future__ import annotations

import json

if __name__.startswith("pipelines."):
    from ..oracle_grounded import envelope, refusals
    from ..oracle_grounded.import_twins import bind_import_twin
    from ..raw_tree_guard import is_under_raw
    from ..tag_jsonutil import reject_duplicate_object_keys, reject_json_constant
    from ..exact_json import ExactJSONFloat
else:
    from oracle_grounded import envelope, refusals
    from oracle_grounded.import_twins import bind_import_twin
    from raw_tree_guard import is_under_raw
    from tag_jsonutil import reject_duplicate_object_keys, reject_json_constant
    from exact_json import ExactJSONFloat

FINDING_CATALOG_FILE_MISSING = "CATALOG_FILE_MISSING"
FINDING_CATALOG_FIELD_MISSING = "CATALOG_FIELD_MISSING"
FINDING_CATALOG_FIELD_INVALID = "CATALOG_FIELD_INVALID"
FINDING_PLANTS_SHA_MISMATCH = "PLANTS_SHA_MISMATCH"
FINDING_PLANT_FIELD_MISSING = "PLANT_FIELD_MISSING"
FINDING_PLANT_FIELD_INVALID = "PLANT_FIELD_INVALID"
FINDING_PLANT_DUPLICATE = "PLANT_DUPLICATE"
FINDING_DESTINATION_EXISTS = "DESTINATION_EXISTS"
FINDING_DESTINATION_UNDER_RAW = "DESTINATION_UNDER_RAW"
FINDING_UNKNOWN_WAVE = "UNKNOWN_WAVE"
FINDING_UNKNOWN_FACTORY = "UNKNOWN_FACTORY"
FINDING_UNKNOWN_SLUG = "UNKNOWN_SLUG"
FINDING_RAW_ROOT_REQUIRED = "RAW_ROOT_REQUIRED"
FINDING_PUBLISH_FAILED = "PUBLISH_FAILED"
FINDING_PAIR_INVALID = "PAIR_INVALID"

FINDING_CODES = (
    FINDING_CATALOG_FILE_MISSING,
    FINDING_CATALOG_FIELD_MISSING,
    FINDING_CATALOG_FIELD_INVALID,
    FINDING_PLANTS_SHA_MISMATCH,
    FINDING_PLANT_FIELD_MISSING,
    FINDING_PLANT_FIELD_INVALID,
    FINDING_PLANT_DUPLICATE,
    FINDING_DESTINATION_EXISTS,
    FINDING_DESTINATION_UNDER_RAW,
    FINDING_UNKNOWN_WAVE,
    FINDING_UNKNOWN_FACTORY,
    FINDING_UNKNOWN_SLUG,
    FINDING_RAW_ROOT_REQUIRED,
    FINDING_PUBLISH_FAILED,
    FINDING_PAIR_INVALID,
)
FINDING_CODE_SET = frozenset(FINDING_CODES)


class HopperRefusal(refusals.CodedRefusal):
    """The family's coded refusal: ``str`` is always ``CODE: prose``."""

    CODES = FINDING_CODE_SET


refuse, refuse_when, refuse_first = refusals.helpers(HopperRefusal)
shown = refusals.shown

__all__ = [
    "FINDING_CODE_SET",
    "FINDING_CODES",
    "HopperRefusal",
    "bind_import_twin",
    "envelope",
    "is_under_raw",
    "load_strict_json",
    "refuse",
    "refuse_first",
    "refuse_when",
    "refusals",
    "shown",
]


def load_strict_json(payload: str | bytes):
    """Keep exact decimal tokens at hopper catalog boundaries."""
    return json.loads(
        payload,
        object_pairs_hook=reject_duplicate_object_keys,
        parse_constant=reject_json_constant,
        parse_float=ExactJSONFloat,
    )


bind_import_twin(__name__)
