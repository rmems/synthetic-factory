"""Flaky-test leftover-cause mill: pinned catalog, generate, CLI.

The five leftover mill scripts on ``legacy-mill-lane`` are not vendored.
Their ``PLANTS`` literals were AST-extracted (``git show`` + ``ast.parse``,
never ``exec``) into ``config/flk/``. This package loads that catalog and
emits success/handoff episode pairs. It does not hop factories, does not
write ``outputs/raw/``, and does not stamp ``grok-4.6``.
"""

from ._contract import bind_import_twin

__all__ = ["_contract", "catalog", "cli", "generate"]

bind_import_twin(__name__)
