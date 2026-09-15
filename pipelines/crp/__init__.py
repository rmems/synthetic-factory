"""Code-review preference mill (prefix ``crp``).

AST-extracted leftover leftover leftover plants and the r432 compact
JSONL slice for ``code-review-preference-factory``. Catalog rows carry
``noun``. Mill scripts named ``crp-mill*.py`` are not vendored;
``catalog.plants_from_source`` is the extract seam.
"""

__all__ = ("_contract catalog generate cli r432").split()

from ._contract import bind_import_twin

bind_import_twin(__name__)
