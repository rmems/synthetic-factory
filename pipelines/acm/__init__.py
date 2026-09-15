"""API contract-migration family (prefix ``acm``).

AST-extracts leftover OpenAPI-drift pairs from ``legacy-mill-lane``. The
family lives in this package as ``_contract``, ``catalog``, ``generate``,
and ``cli``. Leftover mill scripts are not vendored.
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
    STEPS,
    bind_import_twin,
    refuse_vendor_paths,
)
from .catalog import check_catalog, load_catalog
from .generate import extract_tree

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
    "STEPS",
    "bind_import_twin",
    "check_catalog",
    "extract_tree",
    "load_catalog",
    "refuse_vendor_paths",
)

bind_import_twin(__name__)
