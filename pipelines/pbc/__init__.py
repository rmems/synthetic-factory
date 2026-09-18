"""PBC mill family (prefix ``pbc`` / proto-breaking-change).

The family lives here as ``_contract``, ``catalog``, ``generate``, and
``cli``. Leftover mill scripts are not vendored.
"""

from ._contract import (
    CATALOG_FORMAT,
    CATALOG_ID,
    FACTORY,
    FACTORY_NAME,
    FAMILY,
    GENERATOR,
    ID_PREFIX,
    QUOTA,
    SOURCE_COMMIT,
    SOURCE_REF,
    bind_import_twin,
    refuse_vendor_paths,
)
from .catalog import load_catalog, load_mill_usage_burst_plan
from .generate import handoff_episode, notes_for, success_episode

__all__ = (
    "CATALOG_FORMAT",
    "CATALOG_ID",
    "FACTORY",
    "FACTORY_NAME",
    "FAMILY",
    "GENERATOR",
    "ID_PREFIX",
    "QUOTA",
    "SOURCE_COMMIT",
    "SOURCE_REF",
    "bind_import_twin",
    "handoff_episode",
    "load_catalog",
    "load_mill_usage_burst_plan",
    "notes_for",
    "refuse_vendor_paths",
    "success_episode",
)

bind_import_twin(__name__)
