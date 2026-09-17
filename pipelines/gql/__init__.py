"""GraphQL leftover-execution mill: pinned catalog, generate, CLI.

The seven ``gql-mill-r*.py`` scripts on ``legacy-mill-lane`` are not
vendored. Their ``PAIRS`` / ``EXTRA`` / ``CATALOG`` literals were
AST-extracted (``git show`` + ``ast.parse``, never ``exec``) into
``config/gql/``. Loop mills (``gql-loop-*.py``, published-slug scans,
modulo catalog wrap) are dropped. This package loads the catalog and
emits success/handoff episode pairs. It does not hop factories, does not
write ``outputs/raw/``, and does not stamp ``grok-4.6``.
"""

from ._contract import bind_import_twin

__all__ = ["_contract", "catalog", "cli", "generate"]

bind_import_twin(__name__)
