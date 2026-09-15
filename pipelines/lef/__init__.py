#!/usr/bin/env python3
"""llm-eval-flakiness mill family (``lef``): AST catalog extract and package skeleton.

Catalog rows are extracted from ``origin/legacy-mill-lane`` mill sources via
:mod:`lef.catalog_extract`. The mill publishers themselves are not vendored
and are never executed. ``rows.jsonl`` holds the r629 + r728 + r968 tables.
``plants.jsonl`` holds Archive B ``mill_plants.py`` pairs (r613–r620).
"""

from . import vocabulary
from .catalog import CATALOG, LefCatalog, MillCatalog, SlugListing, load_catalog
from .catalog_extract import extract_companion_path, extract_mill_catalog
from .identity import refuse_vendor_paths
from .plants_extract import dumps_plants_jsonl, extract_plant_pairs
from .sources import (
    MILL_SOURCES,
    PLANT_SOURCE,
    MillSource,
    catalog_sources,
    loop_sources,
    plant_sources,
    source_by_id,
)
from .vocabulary import FACTORY, FAMILY_PREFIX

__all__ = (
    "CATALOG",
    "FACTORY",
    "FAMILY_PREFIX",
    "LefCatalog",
    "MILL_SOURCES",
    "MillCatalog",
    "MillSource",
    "PLANT_SOURCE",
    "SlugListing",
    "catalog_sources",
    "dumps_plants_jsonl",
    "extract_companion_path",
    "extract_mill_catalog",
    "extract_plant_pairs",
    "load_catalog",
    "loop_sources",
    "plant_sources",
    "refuse_vendor_paths",
    "source_by_id",
    "vocabulary",
)
