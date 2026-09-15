#!/usr/bin/env python3
"""Docker-build-cache mill family (``dbc``): AST catalog extract and package skeleton.

PR-a. Catalog rows are extracted from ``origin/legacy-mill-lane`` mill sources
via :mod:`dbc.catalog_extract`. The mill publishers themselves are not
vendored and are never executed. ``dbc_r597`` / ``dbc_r600`` hop launderers
are excluded from the catalog.
"""

from . import vocabulary
from .catalog import CATALOG, DbcCatalog, MillCatalog, load_catalog
from .catalog_extract import compose_family_records, extract_companion_path, extract_mill_catalog
from .identity import is_excluded_launderer_path, refuse_vendor_paths
from .sources import (
    EXCLUDED_LAUNDERERS,
    MILL_SOURCES,
    MillSource,
    catalog_sources,
    gen_sources,
    hop_sources,
    loop_sources,
    source_by_id,
)
from .vocabulary import FACTORY, FAMILY_PREFIX

__all__ = (
    "CATALOG",
    "EXCLUDED_LAUNDERERS",
    "FACTORY",
    "FAMILY_PREFIX",
    "DbcCatalog",
    "MILL_SOURCES",
    "MillCatalog",
    "MillSource",
    "catalog_sources",
    "compose_family_records",
    "extract_companion_path",
    "extract_mill_catalog",
    "gen_sources",
    "hop_sources",
    "is_excluded_launderer_path",
    "load_catalog",
    "loop_sources",
    "refuse_vendor_paths",
    "source_by_id",
    "vocabulary",
)
