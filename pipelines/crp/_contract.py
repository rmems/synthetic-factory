#!/usr/bin/env python3
"""The one place the CRP family reaches main's shared primitives.

Both import forms are supported (``crp.x`` with ``pipelines/`` on
``sys.path``, and ``pipelines.crp.x`` from the repository root). Every
module ends with ``bind_import_twin(__name__)`` so the two spellings are
one object.
"""

from __future__ import annotations

import json
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

FINDING_NOUN_MISSING = "CATALOG_NOUN_MISSING"
FINDING_FIELD_MISSING = "CATALOG_FIELD_MISSING"
FINDING_FIELD_INVALID = "CATALOG_FIELD_INVALID"
FINDING_DUPLICATE_SLUG = "CATALOG_DUPLICATE_SLUG"
FINDING_DUPLICATE_FAMILY = "CATALOG_DUPLICATE_FAMILY"
FINDING_AST_NOT_A_PLANT = "CATALOG_AST_NOT_A_PLANT"
FINDING_CATALOG_EMPTY = "CATALOG_EMPTY"
FINDING_CATALOG_FILE_MISSING = "CATALOG_FILE_MISSING"
FINDING_CATALOG_TRIPLE_STRIDE = "CATALOG_TRIPLE_STRIDE"
FINDING_PLANTS_SHA_MISMATCH = "PLANTS_SHA_MISMATCH"
FINDING_ROUND_OUT_OF_DOMAIN = "ROUND_OUT_OF_DOMAIN"
FINDING_TRIPLE_OUT_OF_DOMAIN = "TRIPLE_OUT_OF_DOMAIN"
FINDING_DESTINATION_EXISTS = "DESTINATION_EXISTS"
FINDING_DESTINATION_UNDER_RAW = "DESTINATION_UNDER_RAW"
FINDING_CRITIQUE_TOO_SHORT = "CRITIQUE_TOO_SHORT"

FINDING_CODES = (
    FINDING_NOUN_MISSING,
    FINDING_FIELD_MISSING,
    FINDING_FIELD_INVALID,
    FINDING_DUPLICATE_SLUG,
    FINDING_DUPLICATE_FAMILY,
    FINDING_AST_NOT_A_PLANT,
    FINDING_CATALOG_EMPTY,
    FINDING_CATALOG_FILE_MISSING,
    FINDING_CATALOG_TRIPLE_STRIDE,
    FINDING_PLANTS_SHA_MISMATCH,
    FINDING_ROUND_OUT_OF_DOMAIN,
    FINDING_TRIPLE_OUT_OF_DOMAIN,
    FINDING_DESTINATION_EXISTS,
    FINDING_DESTINATION_UNDER_RAW,
    FINDING_CRITIQUE_TOO_SHORT,
)
FINDING_CODE_SET = frozenset(FINDING_CODES)


class CrpRefusal(refusals.CodedRefusal):
    """The family's coded refusal: ``str`` is always ``CODE: prose``."""

    CODES = FINDING_CODE_SET


refuse, refuse_when, refuse_first = refusals.helpers(CrpRefusal)
shown = refusals.shown

__all__ = [
    "CrpRefusal",
    "FINDING_AST_NOT_A_PLANT",
    "FINDING_CATALOG_EMPTY",
    "FINDING_CATALOG_FILE_MISSING",
    "FINDING_CATALOG_TRIPLE_STRIDE",
    "FINDING_CODES",
    "FINDING_CODE_SET",
    "FINDING_CRITIQUE_TOO_SHORT",
    "FINDING_DESTINATION_EXISTS",
    "FINDING_DESTINATION_UNDER_RAW",
    "FINDING_DUPLICATE_FAMILY",
    "FINDING_DUPLICATE_SLUG",
    "FINDING_FIELD_INVALID",
    "FINDING_FIELD_MISSING",
    "FINDING_NOUN_MISSING",
    "FINDING_PLANTS_SHA_MISMATCH",
    "FINDING_ROUND_OUT_OF_DOMAIN",
    "FINDING_TRIPLE_OUT_OF_DOMAIN",
    "bind_import_twin",
    "dumps_exact_json",
    "envelope",
    "is_under_raw",
    "load_strict_json",
    "refuse",
    "refuse_first",
    "refuse_when",
    "refusals",
    "repo_root",
    "shown",
]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_strict_json(payload: str | bytes):
    """Keep exact decimal tokens at CRP catalog and record boundaries."""

    return json.loads(
        payload,
        object_pairs_hook=reject_duplicate_object_keys,
        parse_constant=reject_json_constant,
        parse_float=ExactJSONFloat,
    )


bind_import_twin(__name__)
