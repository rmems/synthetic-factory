#!/usr/bin/env python3
"""Pinned identity for the API contract-migration mill family (``acm``)."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from . import _contract

FAMILY = "acm"
FACTORY_NAME = "api-contract-migration-factory"
GENERATOR = "grok-4.6"
ID_PREFIX = "acm"
QUOTA = 2
STEPS = 16
CATALOG_ID = "api-contract-migration-v1"
CATALOG_FORMAT = "acm-catalog/1"
# Preservation commit on ``legacy-mill-lane``; the mill scripts stay there.
SOURCE_REF = "legacy-mill-lane"
SOURCE_COMMIT = "6d5ed0c1cac87618a05fab37f2e59bebca0a6031"
VENDOR_PREFIX = "acm-mill-"


def refuse_vendor_paths(paths: Iterable[Path | str]) -> None:
    """Fail closed if any path would vendor an ``acm-mill*.py`` script."""

    for raw in paths:
        name = Path(raw).name
        if name.startswith(VENDOR_PREFIX) and name.endswith(".py"):
            raise SystemExit(f"refusing to vendor {name}")


__all__ = [
    "CATALOG_FORMAT",
    "CATALOG_ID",
    "FACTORY_NAME",
    "FAMILY",
    "GENERATOR",
    "ID_PREFIX",
    "QUOTA",
    "SOURCE_COMMIT",
    "SOURCE_REF",
    "STEPS",
    "VENDOR_PREFIX",
    "refuse_vendor_paths",
]

_contract.bind_import_twin(__name__)
