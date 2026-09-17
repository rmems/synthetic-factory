"""Sparse-reward long-task family (prefix ``srl``).

AST-extracted from ``srl_r6110`` on ``origin/legacy-mill-lane``. The family
lives in this package as ``_contract``, ``catalog``, ``generate``, and ``cli``.
Leftover mill scripts are not vendored.
"""

from ._contract import (
    BANNED,
    FACTORY,
    FAMILY_PREFIX,
    GEN,
    GENERATOR,
    N_STEPS,
    SOURCE_MILL_ID,
    SrlError,
)
from .catalog import PLANTS, plant_at, plant_by_slug, slugs
from .generate import episode, hid, notes, record_id

__all__ = (
    "BANNED",
    "FACTORY",
    "FAMILY_PREFIX",
    "GEN",
    "GENERATOR",
    "N_STEPS",
    "PLANTS",
    "SOURCE_MILL_ID",
    "SrlError",
    "episode",
    "hid",
    "notes",
    "plant_at",
    "plant_by_slug",
    "record_id",
    "slugs",
)
