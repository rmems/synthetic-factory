"""RAG leftover-filter mill: pinned catalog, generate, CLI.

The leftover mill and loop driver on ``legacy-mill-lane`` are not vendored.
``PAIRS`` was AST-extracted (``git show`` + ``ast.parse``, never ``exec``)
into ``config/rag/``. This package loads that catalog and emits
success/handoff episode pairs. It does not hop factories, does not write
``outputs/raw/``, and does not stamp ``grok-4.6``.
"""

from ._contract import bind_import_twin

__all__ = ["_contract", "catalog", "cli", "generate"]

bind_import_twin(__name__)
