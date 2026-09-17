"""Feature-flag-debug mill family: AST-extracted leftover-execution catalog.

``synthetic-factory -> feature-flag-debug-factory``. Catalog rows are lifted
from the three ``ffd-mill*.py`` leftover mills on ``origin/legacy-mill-lane``
by :mod:`ast` (constructors only). Those mill scripts are never vendored.
"""

__all__ = "_contract catalog generate cli".split()

from ._contract import bind_import_twin

bind_import_twin(__name__)
