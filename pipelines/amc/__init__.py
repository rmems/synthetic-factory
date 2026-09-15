#!/usr/bin/env python3
"""Agent-memory-compaction mill family (``amc``): AST catalog extract.

PR-a. Catalog rows are extracted from ``origin/legacy-mill-lane`` mill sources
via :mod:`amc.catalog_extract`. The mill publishers themselves are not
vendored and are never executed.
"""

from . import vocabulary
from .catalog import CATALOG, AmcCatalog, MillCatalog, load_catalog
from .catalog_extract import (
    compose_family,
    extract_companion_path,
    extract_mill_catalog,
    zip_table_pairs,
)
from .identity import refuse_vendor_paths
from .sources import MILL_SOURCES, MillSource, catalog_sources, loop_sources, source_by_id
from .vocabulary import FACTORY, FAMILY_PREFIX

__all__ = (
    "CATALOG",
    "AmcCatalog",
    "FACTORY",
    "FAMILY_PREFIX",
    "MILL_SOURCES",
    "MillCatalog",
    "MillSource",
    "catalog_sources",
    "compose_family",
    "extract_companion_path",
    "extract_mill_catalog",
    "load_catalog",
    "loop_sources",
    "refuse_vendor_paths",
    "source_by_id",
    "vocabulary",
    "zip_table_pairs",
)
