"""Browser-tool-use family (prefix ``brw``).

AST-extracted from ``brw-mill-r193`` on ``origin/legacy-mill-lane``. The family
lives in this package as ``_contract``, ``catalog``, ``generate``, and ``cli``.
Leftover mill scripts are not vendored and are never executed.
"""

from ._contract import (
    BANNED,
    BANNED_CSS,
    BANNED_HOSTS,
    CATALOG_FIRST,
    FACTORY,
    FAMILY_PREFIX,
    GEN,
    GENERATOR,
    MAX_STEPS,
    MIN_STEPS,
    SOURCE_MILL_ID,
    BrwError,
)
from .catalog import PAIRS, pair_at, pair_by_ok_slug, pair_for_round, slugs
from .generate import (
    build_fail,
    build_success,
    generate_window,
    notes_for,
    pair_records,
)

__all__ = (
    "BANNED",
    "BANNED_CSS",
    "BANNED_HOSTS",
    "BrwError",
    "CATALOG_FIRST",
    "FACTORY",
    "FAMILY_PREFIX",
    "GEN",
    "GENERATOR",
    "MAX_STEPS",
    "MIN_STEPS",
    "PAIRS",
    "SOURCE_MILL_ID",
    "build_fail",
    "build_success",
    "generate_window",
    "notes_for",
    "pair_at",
    "pair_by_ok_slug",
    "pair_for_round",
    "pair_records",
    "slugs",
)
