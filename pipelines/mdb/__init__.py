#!/usr/bin/env python3
"""Monorepo-dep-bump mill family (``mdb``): AST catalog extract and package skeleton.

PR-a extracted catalog identity from ``origin/legacy-mill-lane`` mill sources
via :mod:`mdb.catalog_extract`. PR-b commits the remaining compact pair
identities in ``pairs.jsonl``. The mill publishers themselves are not
vendored and are never executed.
"""

from . import vocabulary
from .catalog import CATALOG, MdbCatalog, MillCatalog, load_catalog
from .catalog_extract import extract_companion_path, extract_mill_catalog
from .identity import refuse_vendor_paths
from .pairs import PAIRS, DeferredPair, compact_pair_row, load_pairs
from .sources import MILL_SOURCES, MillSource, catalog_sources, loop_sources, source_by_id
from .vocabulary import FACTORY, FAMILY_PREFIX

__all__ = (
    "CATALOG",
    "FACTORY",
    "FAMILY_PREFIX",
    "MILL_SOURCES",
    "MdbCatalog",
    "MillCatalog",
    "MillSource",
    "DeferredPair",
    "PAIRS",
    "catalog_sources",
    "compact_pair_row",
    "extract_companion_path",
    "extract_mill_catalog",
    "load_catalog",
    "load_pairs",
    "loop_sources",
    "refuse_vendor_paths",
    "source_by_id",
    "vocabulary",
)
