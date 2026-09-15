"""MCP tool-schema leftover mill: pinned catalog, generate, CLI.

The leftover mill scripts on ``legacy-mill-lane`` are not vendored. Their
``PAIRS`` literals were AST-extracted (``git show`` + ``ast.parse``, never
``exec``) into ``config/msd/``. This package loads that catalog and emits
success/handoff episode pairs. It does not hop factories, does not write
``outputs/raw/``, and does not stamp ``grok-4.6``. The leftover-loop
publisher is dropped.
"""

from ._contract import bind_import_twin

__all__ = ["_contract", "catalog", "cli", "generate"]

bind_import_twin(__name__)
