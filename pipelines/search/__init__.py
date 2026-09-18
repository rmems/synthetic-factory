#!/usr/bin/env python3
"""Search mill family (``search``): AST catalog extract, leftover mills off-branch.

FAMILY=search. Leftover3 / leftover-lll pair rows live in ``CATALOG.json``
(#266). Home slices sir-mill-r31, sir-mill-r52, and sir-mill-r72 are compact
JSONL extracts of the matching ``experiments/sir-mill-r*.py`` scripts. Leftover
publishers
are not vendored, not re-extracted, and never executed.
"""

from . import vocabulary
from .catalog import (
    CATALOG,
    R31,
    R52,
    R72,
    HomeMillCatalog,
    MillCatalog,
    SearchCatalog,
    load_catalog,
    load_home_mill,
    load_r72,
)
from .catalog_extract import extract_home_mill_catalog, extract_mill_catalog
from .identity import refuse_cataloged_leftover_mill, refuse_vendor_paths
from .sources import (
    HOME_MILL_SOURCES,
    MILL_SOURCES,
    R31_SOURCE,
    R52_SOURCE,
    R72_SOURCE,
    MillSource,
    catalog_sources,
    home_mill_sources,
    source_by_id,
)
from .vocabulary import FACTORY, FAMILY, FAMILY_PREFIX

__all__ = (
    "CATALOG",
    "FACTORY",
    "FAMILY",
    "FAMILY_PREFIX",
    "HOME_MILL_SOURCES",
    "MILL_SOURCES",
    "R31",
    "R31_SOURCE",
    "R52",
    "R52_SOURCE",
    "R72",
    "R72_SOURCE",
    "HomeMillCatalog",
    "MillCatalog",
    "MillSource",
    "SearchCatalog",
    "catalog_sources",
    "extract_home_mill_catalog",
    "extract_mill_catalog",
    "home_mill_sources",
    "load_catalog",
    "load_home_mill",
    "load_r72",
    "refuse_cataloged_leftover_mill",
    "refuse_vendor_paths",
    "source_by_id",
    "vocabulary",
)
