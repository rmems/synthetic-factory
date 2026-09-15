"""Email-webhook-retry leftover-event family (``FAMILY=ewr``).

The catalog is AST-extracted from the leftover plants on ``legacy-mill-lane``.
``ewr_*mill.py`` is not vendored. Generate writes a brand-new destination and
refuses ``outputs/raw/``.
"""

from ._contract import (
    FACTORY,
    FAMILY_PREFIX,
    GENERATOR,
    bind_import_twin,
)
from .catalog import Catalog, Pair, ast_extract_catalog, catalog_check, load_catalog
from . import generate
from .generate import BuiltPair, build_pair

__all__ = [
    "BuiltPair",
    "Catalog",
    "FACTORY",
    "FAMILY_PREFIX",
    "GENERATOR",
    "Pair",
    "ast_extract_catalog",
    "bind_import_twin",
    "build_pair",
    "catalog_check",
    "generate",
    "load_catalog",
]

bind_import_twin(__name__)
