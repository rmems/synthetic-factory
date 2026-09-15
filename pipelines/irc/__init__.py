"""Incident-response leftover3 family (prefix ``irc``).

AST-extracted first slice from ``irc_r3366_leftover3_mill`` on
``origin/legacy-mill-lane``. The family lives here as ``_contract``,
``catalog``, ``generate``, and ``cli``. Leftover mill scripts are not
vendored and are never executed.
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
