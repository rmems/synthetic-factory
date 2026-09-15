#!/usr/bin/env python3
"""The one place the ACM family reaches shared import-twin binding.

Both import forms are supported (``acm.x`` with ``pipelines/`` on ``sys.path``,
and ``pipelines.acm.x`` from the repository root). Every sibling ends with
``bind_import_twin(__name__)`` so the two spellings are one object.

Identity is pinned to the reviewed mill-prefix home. The leftover mill scripts
stay on ``legacy-mill-lane``; this package refuses to vendor them.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

if __name__.startswith("pipelines."):
    from ..mill_reviewed_vocabulary import REVIEWED_MILL_PREFIX_HOMES
    from ..oracle_grounded.import_twins import bind_import_twin
else:
    from mill_reviewed_vocabulary import REVIEWED_MILL_PREFIX_HOMES
    from oracle_grounded.import_twins import bind_import_twin

FAMILY = "acm"
FACTORY_NAME = "api-contract-migration-factory"
FACTORY = FACTORY_NAME
GENERATOR = "grok-4.6"
ID_PREFIX = "acm"
QUOTA = 2
STEPS = 16
CATALOG_ID = "api-contract-migration-v1"
CATALOG_FORMAT = "acm-catalog/1"
SOURCE_REF = "legacy-mill-lane"
SOURCE_COMMIT = "6d5ed0c1cac87618a05fab37f2e59bebca0a6031"
VENDOR_PREFIX = "acm-mill-"
# Wrap-mill cartesian leftovers. Historical plant needles stay in the catalog
# bans table but must not convict a later distinct slug that happens to overlap.
WRAP_NEEDLES = ("w131", "422-vs-400", "207-multistatus")
# Full extract on legacy-mill-lane. This PR commits a representative slice.
FULL_ROW_COUNT = 1052
FULL_SOURCE_FILES = 95

REVIEWED_HOME = REVIEWED_MILL_PREFIX_HOMES[FAMILY]
if REVIEWED_HOME != FACTORY_NAME:
    raise ImportError(
        f"reviewed prefix home for {FAMILY!r} is {REVIEWED_HOME!r}, "
        f"not the acm factory {FACTORY_NAME!r}"
    )


def refuse_vendor_paths(paths: Iterable[Path | str]) -> None:
    """Fail closed if any path would vendor an ``acm-mill*.py`` script."""

    for raw in paths:
        name = Path(raw).name
        if name.startswith(VENDOR_PREFIX) and name.endswith(".py"):
            raise SystemExit(f"refusing to vendor {name}")


__all__ = [
    "CATALOG_FORMAT",
    "CATALOG_ID",
    "FACTORY",
    "FACTORY_NAME",
    "FAMILY",
    "FULL_ROW_COUNT",
    "FULL_SOURCE_FILES",
    "GENERATOR",
    "ID_PREFIX",
    "QUOTA",
    "REVIEWED_HOME",
    "SOURCE_COMMIT",
    "SOURCE_REF",
    "STEPS",
    "VENDOR_PREFIX",
    "WRAP_NEEDLES",
    "bind_import_twin",
    "refuse_vendor_paths",
]

bind_import_twin(__name__)
