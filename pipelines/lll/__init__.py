#!/usr/bin/env python3
"""Leftover leftover leftover (``lll``) mill family.

AST-extracts the first unused leftover leftover leftover slice from
``origin/legacy-mill-lane`` (the three LHC ``lhc-mill-lll*`` catalogs).
Leftover mill scripts stay on that archive and are never vendored or executed.
"""

from __future__ import annotations

from ._contract import (
    FACTORY,
    FAMILY,
    GENERATOR,
    LllRefusal,
    bind_import_twin,
    refuse_vendor_paths,
)
from . import catalog, cli, generate

__all__ = [
    "FACTORY",
    "FAMILY",
    "GENERATOR",
    "LllRefusal",
    "bind_import_twin",
    "catalog",
    "cli",
    "generate",
    "refuse_vendor_paths",
]


bind_import_twin(__name__)
