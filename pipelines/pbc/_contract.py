#!/usr/bin/env python3
"""PBC family identity. Leftover mill scripts stay on legacy-mill-lane."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

if __name__.startswith("pipelines."):
    from ..mill_reviewed_vocabulary import REVIEWED_MILL_PREFIX_HOMES
    from ..oracle_grounded.import_twins import bind_import_twin
else:
    from mill_reviewed_vocabulary import REVIEWED_MILL_PREFIX_HOMES
    from oracle_grounded.import_twins import bind_import_twin

FAMILY = "pbc"
FACTORY_NAME = "proto-breaking-change-factory"
FACTORY = FACTORY_NAME
GENERATOR = "grok-4.6"
ID_PREFIX = "pbc"
QUOTA = 2
CATALOG_ID = "proto-breaking-change-v1"
CATALOG_FORMAT = "pbc-catalog/1"
PLAN_SCHEMA_ID = "mill-usage-burst-plan/v1"
PLAN_SLICE = "A"
SOURCE_REF = "legacy-mill-lane"
SOURCE_COMMIT = "813f93f1969c1c4421e5663492e9663739efa642"
VENDOR_PREFIX = "pbc-mill-"
DEFAULT_PLAN_PATH = "config/mill-usage-burst-plan.pbc-a.json"
DEFAULT_RUN_LABEL = "2026-08-19-agentic"
# Full extract on legacy-mill-lane. This PR commits a first-slice catalog.
FULL_MILL_COUNT = 8
FULL_PAIR_COUNT = 708
FULL_EPISODE_COUNT = 1416
LEFTOVER_MILL_ID = "pbc_r1335"
LEFTOVER_FIRST_SLUG = "date-to-int32-poured"
SLICE_PAIR_COUNT = 8

REVIEWED_HOME = REVIEWED_MILL_PREFIX_HOMES[FAMILY]
if REVIEWED_HOME != FACTORY_NAME:
    raise ImportError(
        f"reviewed prefix home for {FAMILY!r} is {REVIEWED_HOME!r}, "
        f"not the pbc factory {FACTORY_NAME!r}"
    )


def refuse_vendor_paths(paths: Iterable[Path | str]) -> None:
    """Fail closed if any path would vendor a ``pbc-mill*.py`` script."""

    for raw in paths:
        name = Path(raw).name
        if name.startswith(VENDOR_PREFIX) and name.endswith(".py"):
            raise SystemExit(f"refusing to vendor {name}")


__all__ = [
    "CATALOG_FORMAT",
    "CATALOG_ID",
    "DEFAULT_PLAN_PATH",
    "DEFAULT_RUN_LABEL",
    "FACTORY",
    "FACTORY_NAME",
    "FAMILY",
    "FULL_EPISODE_COUNT",
    "FULL_MILL_COUNT",
    "FULL_PAIR_COUNT",
    "GENERATOR",
    "ID_PREFIX",
    "LEFTOVER_FIRST_SLUG",
    "LEFTOVER_MILL_ID",
    "PLAN_SCHEMA_ID",
    "PLAN_SLICE",
    "QUOTA",
    "REVIEWED_HOME",
    "SLICE_PAIR_COUNT",
    "SOURCE_COMMIT",
    "SOURCE_REF",
    "VENDOR_PREFIX",
    "bind_import_twin",
    "refuse_vendor_paths",
]

bind_import_twin(__name__)
