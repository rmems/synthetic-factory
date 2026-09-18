#!/usr/bin/env python3
"""Authz-regression mill family (``azr``): AST catalog extract and package skeleton.

PR-a extracts catalog identity from ``origin/legacy-mill-lane``. PR-b lands
the 1320 deferred pair identities as compact ``pairs.jsonl``. The mill
publishers themselves are not vendored and are never executed.
"""

from . import vocabulary
from .catalog import CATALOG, AzrCatalog, MillCatalog, load_catalog
from .catalog_extract import (
    dumps_pairs_jsonl,
    extract_companion_path,
    extract_mill_catalog,
    extract_plant_catalog,
    load_pair_rows,
    pairs_jsonl_path,
)
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
    "dumps_pairs_jsonl",
    "extract_companion_path",
    "extract_mill_catalog",
    "extract_plant_catalog",
    "gen_sources",
    "load_catalog",
    "load_pair_rows",
    "pairs_jsonl_path",
    "loop_sources",
    "plant_sources",
    "refuse_vendor_paths",
    "source_by_id",
    "vocabulary",
)
