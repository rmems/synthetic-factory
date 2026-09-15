#!/usr/bin/env python3
"""Search mill family (``search``): AST catalog extract, leftover mills off-branch.

FAMILY=search. Leftover3 / leftover-lll pair rows live in ``CATALOG.json``
(#266). Slice sir-mill-r72 is the compact JSONL extract of
``experiments/sir-mill-r72.py`` (20 home-factory pairs). Leftover publishers
are not vendored, not re-extracted, and never executed.
"""

from . import vocabulary
from .catalog import (
    CATALOG,
    R72,
    HomeMillCatalog,
    MillCatalog,
    SearchCatalog,
    load_catalog,
    load_r72,
)
from .catalog_extract import extract_home_mill_catalog, extract_mill_catalog
from .identity import refuse_cataloged_leftover_mill, refuse_vendor_paths
from .sources import MILL_SOURCES, R72_SOURCE, MillSource, catalog_sources, source_by_id
from .vocabulary import FACTORY, FAMILY, FAMILY_PREFIX

__all__ = (
    "CATALOG",
    "FACTORY",
    "FAMILY",
    "FAMILY_PREFIX",
    "MILL_SOURCES",
    "R72",
    "R72_SOURCE",
    "HomeMillCatalog",
    "MillCatalog",
    "MillSource",
    "SearchCatalog",
    "catalog_sources",
    "extract_home_mill_catalog",
    "extract_mill_catalog",
    "load_catalog",
    "load_r72",
    "refuse_cataloged_leftover_mill",
    "refuse_vendor_paths",
    "source_by_id",
    "vocabulary",
)
