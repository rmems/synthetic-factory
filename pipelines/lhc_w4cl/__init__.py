#!/usr/bin/env python3
"""LHC w4cl mill slice (``lhc``): AST catalog extract, mill publisher off-branch.

FAMILY=lhc. Catalog rows are extracted from ``origin/legacy-mill-lane``
``lhc-mill-w4cl-r4605.py`` via :mod:`lhc_w4cl.catalog_extract`. The mill
publisher is not vendored and is never executed.
"""

from . import vocabulary
from .catalog import CATALOG, LhcW4clCatalog, MillCatalog, load_catalog
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
    "LhcW4clCatalog",
    "MillCatalog",
    "MillSource",
    "catalog_sources",
    "extract_mill_catalog",
    "load_catalog",
    "refuse_vendor_paths",
    "source_by_id",
    "vocabulary",
)
