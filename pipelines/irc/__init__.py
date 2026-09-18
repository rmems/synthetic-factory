"""Incident-response on-call family (prefix ``irc``).

AST-extracted slices from ``origin/legacy-mill-lane``: leftover3 pair plants
in ``catalog``, pipe-row literals in ``pipe_catalog`` + ``specs.jsonl``.
Mill scripts are not vendored and are never executed.
"""

from ._contract import (
    CATALOG_FIRST,
    FACTORY,
    FAMILY_PREFIX,
    GENERATOR,
    SOURCE_MILL_ID,
    IrcRefusal,
    bind_import_twin,
)
from .catalog import PAIRS, pair_at, pair_by_ok_slug, pair_for_round, slugs
from .generate import build_episode, notes_for, pair_records

__all__ = (
    "CATALOG_FIRST",
    "FACTORY",
    "FAMILY_PREFIX",
    "GENERATOR",
    "IrcRefusal",
    "PAIRS",
    "SOURCE_MILL_ID",
    "build_episode",
    "notes_for",
    "pair_at",
    "pair_by_ok_slug",
    "pair_for_round",
    "pair_records",
    "slugs",
)

bind_import_twin(__name__)
