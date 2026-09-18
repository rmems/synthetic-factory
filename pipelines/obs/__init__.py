"""Observability leftover mill: pinned catalog, generate, CLI.

The fifteen ``obs-*`` scripts on ``legacy-mill-lane`` @ ``4efb4b3`` are
not vendored. Their ``PAIRS`` / ``P()`` / ``_P()`` / ``SPECS`` / ``L14``
/ ``L15`` / ``L16`` literals were AST-extracted (``git show`` +
``ast.parse``, never ``exec``) into ``config/obs/``. Loop mills
(``obs-loop-*.py``) are dropped. This package loads the catalog and
emits success/handoff episode pairs. It does not hop factories, does
not write ``outputs/raw/``, and does not stamp ``grok-4.6``.
"""

from ._contract import bind_import_twin

__all__ = ["_contract", "catalog", "cli", "generate"]

bind_import_twin(__name__)
