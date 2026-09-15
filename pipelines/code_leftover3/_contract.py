#!/usr/bin/env python3
"""The one place the code family reaches main's shared primitives.

Both import forms are supported (``code_leftover3.x`` with
``pipelines/`` on ``sys.path``, and ``pipelines.code_leftover3.x`` from
the repository root). Every module ends with
``bind_import_twin(__name__)`` so the two spellings are one object. The
package is not named ``code`` so leftover_mill's ``sys.path`` insert
cannot shadow the stdlib interactive module.
"""

from __future__ import annotations

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

FINDING_NOUN_MISSING = "CATALOG_NOUN_MISSING"
FINDING_FIELD_MISSING = "CATALOG_FIELD_MISSING"
FINDING_FIELD_INVALID = "CATALOG_FIELD_INVALID"
FINDING_DUPLICATE_SLUG = "CATALOG_DUPLICATE_SLUG"
FINDING_DUPLICATE_FAMILY = "CATALOG_DUPLICATE_FAMILY"
FINDING_AST_NOT_A_PLANT = "CATALOG_AST_NOT_A_PLANT"
FINDING_CATALOG_EMPTY = "CATALOG_EMPTY"
FINDING_CATALOG_TRIPLE_STRIDE = "CATALOG_TRIPLE_STRIDE"
FINDING_NOTFAM_DRIFT = "CATALOG_NOTFAM_DRIFT"
FINDING_COVERED_SLUG = "CATALOG_COVERED_SLUG"
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
    FINDING_CATALOG_TRIPLE_STRIDE,
    FINDING_NOTFAM_DRIFT,
    FINDING_COVERED_SLUG,
    FINDING_ROUND_OUT_OF_DOMAIN,
    FINDING_TRIPLE_OUT_OF_DOMAIN,
    FINDING_DESTINATION_EXISTS,
    FINDING_DESTINATION_UNDER_RAW,
    FINDING_CRITIQUE_TOO_SHORT,
)
FINDING_CODE_SET = frozenset(FINDING_CODES)


class CodeRefusal(refusals.CodedRefusal):
    """The family's coded refusal: ``str`` is always ``CODE: prose``."""

    CODES = FINDING_CODE_SET


refuse, refuse_when, refuse_first = refusals.helpers(CodeRefusal)
shown = refusals.shown

__all__ = [
    "CodeRefusal",
    "FINDING_AST_NOT_A_PLANT",
    "FINDING_CATALOG_EMPTY",
    "FINDING_CATALOG_TRIPLE_STRIDE",
    "FINDING_CODES",
    "FINDING_CODE_SET",
    "FINDING_COVERED_SLUG",
    "FINDING_CRITIQUE_TOO_SHORT",
    "FINDING_DESTINATION_EXISTS",
    "FINDING_DESTINATION_UNDER_RAW",
    "FINDING_DUPLICATE_FAMILY",
    "FINDING_DUPLICATE_SLUG",
    "FINDING_FIELD_INVALID",
    "FINDING_FIELD_MISSING",
    "FINDING_NOTFAM_DRIFT",
    "FINDING_NOUN_MISSING",
    "FINDING_ROUND_OUT_OF_DOMAIN",
    "FINDING_TRIPLE_OUT_OF_DOMAIN",
    "bind_import_twin",
    "dumps_exact_json",
    "envelope",
    "is_under_raw",
    "refuse",
    "refuse_first",
    "refuse_when",
    "refusals",
    "shown",
]


bind_import_twin(__name__)
