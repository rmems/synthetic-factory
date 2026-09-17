"""Safety-calibration leftover-cause mill: pinned catalog, generate, CLI.

The leftover mill on ``legacy-mill-lane`` is not vendored. Its ``PAIRS``
literals were AST-extracted (``git show`` + ``ast.parse``, never ``exec``)
into ``config/saf/``. This package loads that catalog and emits designed
safety-case pairs. It does not hop factories, does not write
``outputs/raw/``, and does not stamp ``grok-4.6``.
"""

from ._contract import bind_import_twin

__all__ = ["_contract", "catalog", "cli", "generate"]

bind_import_twin(__name__)
