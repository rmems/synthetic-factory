#!/usr/bin/env python3
"""Secret-scan-remediation mill family (``ssr``): AST catalog extract skeleton.

PR-a. Catalog rows are extracted from ``origin/legacy-mill-lane`` mill sources
via :mod:`ssr.catalog_extract`. The mill publishers themselves are not
vendored and are never executed.
"""

from . import vocabulary
from .catalog import CATALOG, MillCatalog, SsrCatalog, load_catalog
from .catalog_extract import extract_companion_path, extract_mill_catalog
from .identity import refuse_vendor_paths
from .sources import (
    MILL_SOURCES,
    MillSource,
    catalog_sources,
    fast_sources,
    loop_sources,
    source_by_id,
)
from .vocabulary import FACTORY, FAMILY_PREFIX

__all__ = (
    "CATALOG",
    "FACTORY",
    "FAMILY_PREFIX",
    "MILL_SOURCES",
    "MillCatalog",
    "MillSource",
    "SsrCatalog",
    "catalog_sources",
    "extract_companion_path",
    "extract_mill_catalog",
    "fast_sources",
    "load_catalog",
    "loop_sources",
    "refuse_vendor_paths",
    "source_by_id",
    "vocabulary",
)
