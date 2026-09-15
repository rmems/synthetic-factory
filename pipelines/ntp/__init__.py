#!/usr/bin/env python3
"""Notebook-to-pipeline mill family (``ntp``): AST catalog extract and package skeleton.

PR-a landed leftover-slice identities. PR-b binds compact r1326 theme rows
from ``themes.jsonl``. Catalog rows are extracted from
``origin/legacy-mill-lane`` mill sources via :mod:`ntp.catalog_extract`.
The mill publishers themselves are not vendored and are never executed.
"""

from . import vocabulary
from .catalog import CATALOG, MillCatalog, NtpCatalog, load_catalog
from .catalog_extract import extract_companion_path, extract_mill_catalog
from .identity import refuse_vendor_paths
from .sources import (
    MILL_SOURCES,
    MillSource,
    catalog_sources,
    chain_sources,
    gen_sources,
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
    "NtpCatalog",
    "catalog_sources",
    "chain_sources",
    "extract_companion_path",
    "extract_mill_catalog",
    "gen_sources",
    "load_catalog",
    "loop_sources",
    "refuse_vendor_paths",
    "source_by_id",
    "vocabulary",
)
