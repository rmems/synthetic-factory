"""Queue-backpressure leftover family (``FAMILY=qbp``).

The catalog is AST-extracted from ``qbp-mill*.py`` on ``legacy-mill-lane``
(via each mill's plants pointer). Those mill scripts are not vendored and are
never executed. Replay uses hopper's public episode builders. Generate writes
a brand-new destination and refuses ``outputs/raw/``.
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
