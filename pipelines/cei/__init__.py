"""CSV/Excel ingest mill: pinned catalog, generate, CLI.

The hop mill on ``legacy-mill-lane`` (``experiments/cei-mill-r81.py``) is
not vendored. Its ``_ok`` / ``_bad`` ``PAIRS`` were AST-extracted
(``git show`` + ``ast.parse``, never ``exec``) into ``config/cei/``. This
package loads that catalog and emits designed episode pairs. It does not
hop factories, does not write ``outputs/raw/``, and does not stamp
``grok-4.6``.
"""

from ._contract import bind_import_twin

__all__ = ["_contract", "catalog", "cli", "generate"]

bind_import_twin(__name__)
