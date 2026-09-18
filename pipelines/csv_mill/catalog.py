#!/usr/bin/env python3
"""Pinned CSV plant catalog: load, pin, and AST-extract (never exec).

A catalog directory holds ``CATALOG.json`` (identity, factory, mill pins)
and ``plants.jsonl`` (one leftover leftover leftover pair per line). Load
verifies the plants digest and every required field before a plant is
trusted. Historical leftover mill scripts are read only as text through
:func:`plants_from_source`.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from ._contract import (
    CATALOG_FILENAME,
    FINDING_CATALOG_FIELD_INVALID,
    bind_import_twin,
    repo_root,
)
from .catalog_models import Catalog, Mill, Plant
from .catalog_extract import plants_from_source
from .catalog_io import load_catalog as _load_catalog

from .catalog_validation import MILL_ID_RE, SLUG_RE, TICKET_RE

__all__ = [
    "CATALOG_FILENAME",
    "Catalog",
    "Mill",
    "MILL_ID_RE",
    "SLUG_RE",
    "TICKET_RE",
    "Plant",
    "catalog_check",
    "default_catalog_dir",
    "load_catalog",
    "plants_from_source",
    "sha256_bytes",
]


def default_catalog_dir() -> Path:
    return repo_root() / "config" / "csv"


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def load_catalog(directory: Path | None = None) -> Catalog:
    """Load the configured catalog through the strict I/O boundary."""

    return _load_catalog(directory, default_catalog_dir(), sha256_bytes)


def catalog_check(directory: Path | None = None) -> list[dict[str, str]]:
    """Load the catalog. An invalid catalog is a refusal, not a finding list."""

    loaded = load_catalog(directory)
    if loaded.plants:
        return []
    return [{"code": FINDING_CATALOG_FIELD_INVALID, "detail": "empty catalog"}]


bind_import_twin(__name__)
