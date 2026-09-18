#!/usr/bin/env python3
"""Infra-as-code mill family (``iac``): AST catalog extract and package skeleton.

PR-a/PR-b. Mill catalog rows are extracted from ``origin/legacy-mill-lane`` via
:mod:`iac.catalog_extract`. Archive B plant identities come from
``scripts/infra_as_code_mill/mill_plants.py`` via :mod:`iac.plants_extract`.
Publishers are not vendored and are never executed.
"""

from . import vocabulary
from .catalog import CATALOG, IacCatalog, MillCatalog, load_catalog
from .catalog_extract import extract_companion_path, extract_mill_catalog
from .plants_extract import extract_archive_b_more_plants, extract_archive_b_plants
from .identity import refuse_vendor_paths
from .sources import MILL_SOURCES, MillSource, catalog_sources, loop_sources, source_by_id
from .vocabulary import FACTORY, FAMILY_PREFIX

__all__ = (
    "CATALOG",
    "FACTORY",
    "FAMILY_PREFIX",
    "IacCatalog",
    "MILL_SOURCES",
    "MillCatalog",
    "MillSource",
    "catalog_sources",
    "extract_companion_path",
    "extract_archive_b_more_plants",
    "extract_archive_b_plants",
    "extract_mill_catalog",
    "load_catalog",
    "loop_sources",
    "refuse_vendor_paths",
    "source_by_id",
    "vocabulary",
)
