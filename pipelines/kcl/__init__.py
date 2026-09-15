"""Kubernetes CrashLoop leftover mill (``FAMILY=kcl``).

The leftover ``kcl-mill*.py`` / ``kcl-loop*.py`` scripts on
``legacy-mill-lane`` are not vendored and are never executed. Their
``pair()`` / ``PAIRS`` / ``mk()`` catalogs are AST-extracted
(``git show`` + ``ast.parse``) into ``config/kcl/``. The committed
``plants.jsonl`` pins every extracted plant identity; twelve rows keep
full pair/plant bodies and the rest are compact identity lines. Hop replay uses
hopper on main (the **g46c** API: ``start_by_factory`` /
``pairs_by_factory`` / ``emit_stage``) instead of a leftover hopper mill.
"""

from ._contract import (
    FACTORY,
    FAMILY_PREFIX,
    GENERATOR,
    bind_import_twin,
)
from .catalog import Catalog, Plant, ast_extract_plants, catalog_check, load_catalog
from . import generate
from .generate import BuiltPair, build_pair

__all__ = [
    "BuiltPair",
    "Catalog",
    "FACTORY",
    "FAMILY_PREFIX",
    "GENERATOR",
    "Plant",
    "ast_extract_plants",
    "bind_import_twin",
    "build_pair",
    "catalog_check",
    "generate",
    "load_catalog",
]

bind_import_twin(__name__)
