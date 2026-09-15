#!/usr/bin/env python3
"""Data-pipeline-repair mill family (``dpr``): AST catalog extract.

Archive catalog of ``mill_dpr_leftover_r2631`` and the ``dpr-mill`` /
``dpr_mill`` scripts on ``origin/legacy-mill-lane``. PR-b commits deferred
compact pair identities in ``pairs.jsonl``. Loop scripts and lrd hoppers are
pinned but not extracted. Mill publishers are not vendored and are never
executed.
"""

from .catalog import CATALOG, DprCatalog, MillCatalog, load_catalog
from .catalog_extract import (
    DprExtractError,
    dumps_jsonl,
    extract_call_path_constant,
    extract_catalog_nodes,
    extract_joined_path_constant,
    extract_mill_catalog,
    mill_header,
    pairs_jsonl_path,
    plants_jsonl_path,
    select_representative_pair_rows,
    select_representative_plant_rows,
)
from .pairs import DEFERRED_PAIRS, DeferredPair, load_deferred_pairs
from .sources import (
    MILL_SOURCES,
    MillSource,
    catalog_sources,
    gen_sources,
    hopper_sources,
    loop_sources,
    source_by_id,
)
from .vocabulary import FACTORY, FAMILY_PREFIX

__all__ = (
    "CATALOG",
    "DprCatalog",
    "DEFERRED_PAIRS",
    "DeferredPair",
    "DprExtractError",
    "FACTORY",
    "FAMILY_PREFIX",
    "MILL_SOURCES",
    "MillCatalog",
    "MillSource",
    "catalog_sources",
    "dumps_jsonl",
    "extract_call_path_constant",
    "extract_catalog_nodes",
    "extract_joined_path_constant",
    "extract_mill_catalog",
    "gen_sources",
    "hopper_sources",
    "load_catalog",
    "load_deferred_pairs",
    "loop_sources",
    "mill_header",
    "pairs_jsonl_path",
    "plants_jsonl_path",
    "select_representative_pair_rows",
    "select_representative_plant_rows",
    "source_by_id",
)
