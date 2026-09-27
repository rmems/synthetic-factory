#!/usr/bin/env python3
"""Additional sir leftover catalogs: AST extraction, publishers off-branch.

FAMILY=sir. This package owns only leftover3-r72 and r108-leftover3d;
the ``search`` package owns the r31/r52/r72 home mills and their pair rows.
The two leftover catalogs are extracted from ``origin/legacy-mill-lane``
via :mod:`sir.catalog_extract`. The leftover3 / leftover3d
publishers and leftover3 loop are not vendored and are never executed.
"""

from . import vocabulary
from .catalog import CATALOG, MillCatalog, SirCatalog, load_catalog
from .catalog_extract import extract_mill_catalog
from .identity import refuse_vendor_paths
from .sources import MILL_SOURCES, MillSource, catalog_sources, source_by_id
from .vocabulary import FACTORY, FAMILY, FAMILY_PREFIX

__all__ = (
    "CATALOG",
    "FACTORY",
    "FAMILY",
    "FAMILY_PREFIX",
    "MILL_SOURCES",
    "MillCatalog",
    "MillSource",
    "SirCatalog",
    "catalog_sources",
    "extract_mill_catalog",
    "load_catalog",
    "refuse_vendor_paths",
    "source_by_id",
    "vocabulary",
)
