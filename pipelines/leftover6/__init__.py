"""Leftover6 leftover-prefix catalog: AST extract only, leftover6 mills off-branch.

FAMILY=leftover6 is the leftover-variant prefix (mill-count rank 5 among
unused leftover prefixes). Source mills dest-stamp gql / sbox / ssl, which
already have reviewed homes. leftover6 itself is not added to
``REVIEWED_MILL_PREFIX_HOMES``. Leftover6 publishers are not vendored and
are never executed.
"""

from ._contract import bind_import_twin
from .catalog import (
    CATALOG,
    CATALOG_DIR,
    CATALOG_PATH,
    FAMILY,
    GENERATOR,
    Catalog,
    CatalogError,
    MillSource,
    is_vendor_filename,
    load_catalog,
    refuse_vendor_paths,
)
from .catalog_extract import extract_source

__all__ = [
    "CATALOG",
    "CATALOG_DIR",
    "CATALOG_PATH",
    "FAMILY",
    "GENERATOR",
    "Catalog",
    "CatalogError",
    "MillSource",
    "extract_source",
    "is_vendor_filename",
    "load_catalog",
    "refuse_vendor_paths",
]


bind_import_twin(__name__)
