#!/usr/bin/env python3
"""Sir mill family (``sir``): AST catalog extract, leftover mills off-branch.

FAMILY=sir. Catalog rows are extracted from ``origin/legacy-mill-lane``
pair mills via :mod:`sir.catalog_extract`. The leftover3 / leftover3d
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
