#!/usr/bin/env python3
"""Authz-regression mill family (``azr``): AST catalog extract and package skeleton.

PR-a. Catalog rows are extracted from ``origin/legacy-mill-lane`` mill sources
via :mod:`azr.catalog_extract`. The mill publishers themselves are not
vendored and are never executed.
"""

from . import vocabulary
from .catalog import CATALOG, AzrCatalog, MillCatalog, load_catalog
from .catalog_extract import extract_companion_path, extract_mill_catalog, extract_plant_catalog
from .identity import refuse_vendor_paths
from .sources import (
    MILL_SOURCES,
    MillSource,
    catalog_sources,
    gen_sources,
    loop_sources,
    plant_sources,
    source_by_id,
)
from .vocabulary import FACTORY, FAMILY_PREFIX

__all__ = (
    "CATALOG",
    "FACTORY",
    "FAMILY_PREFIX",
    "AzrCatalog",
    "MILL_SOURCES",
    "MillCatalog",
    "MillSource",
    "catalog_sources",
    "extract_companion_path",
    "extract_mill_catalog",
    "extract_plant_catalog",
    "gen_sources",
    "load_catalog",
    "loop_sources",
    "plant_sources",
    "refuse_vendor_paths",
    "source_by_id",
    "vocabulary",
)
