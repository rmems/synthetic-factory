#!/usr/bin/env python3
"""Secret-scan-remediation mill family (``ssr``): AST catalog extract skeleton.

Second slice. Catalog identity stays in ``CATALOG.json``; deferred pair bodies
live in ``pairs.jsonl``. Legacy mill publishers are not vendored and are never
executed.
"""

from . import vocabulary
from .catalog import CATALOG, MillCatalog, SsrCatalog, load_catalog
from .catalog_extract import (
    deferred_pair_rows,
    dumps_pairs_jsonl,
    extract_companion_path,
    extract_mill_catalog,
    pairs_jsonl_path,
    write_pairs_jsonl,
)
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
    "deferred_pair_rows",
    "dumps_pairs_jsonl",
    "extract_companion_path",
    "extract_mill_catalog",
    "fast_sources",
    "load_catalog",
    "loop_sources",
    "pairs_jsonl_path",
    "refuse_vendor_paths",
    "source_by_id",
    "vocabulary",
    "write_pairs_jsonl",
)
