"""Database-migration leftover family (``FAMILY=dbm``).

The leftover3 catalog and sequential leftover-mill identities are AST-extracted
from ``origin/legacy-mill-lane``. ``*mill*.py`` is not vendored. Generate writes
a brand-new destination and refuses ``outputs/raw/``.
"""

from ._contract import (
    FACTORY,
    FAMILY_PREFIX,
    GENERATOR,
    bind_import_twin,
)
from .catalog import Catalog, Leftover3, Pair, catalog_check, load_leftover3, load_mills
from . import generate
from .generate import BuiltPair, build_pair

__all__ = [
    "BuiltPair",
    "Catalog",
    "FACTORY",
    "FAMILY_PREFIX",
    "GENERATOR",
    "Leftover3",
    "Pair",
    "bind_import_twin",
    "build_pair",
    "catalog_check",
    "generate",
    "load_leftover3",
    "load_mills",
]

bind_import_twin(__name__)
