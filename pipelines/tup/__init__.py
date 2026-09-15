"""TUP first slice: pinned r1349 inspect-vs-destroy catalog.

``experiments/tup-mill-r1349.py`` on ``legacy-mill-lane`` is parse input
only (``git show`` + ``ast.parse``, never ``exec``). This package loads
the compact catalog and emits designed preference pairs. It does not
vendor mill or loop scripts, does not write ``outputs/raw/``, and does
not stamp ``grok-4.6``.
"""

from ._contract import bind_import_twin

__all__ = ["_contract", "catalog", "cli", "generate"]

bind_import_twin(__name__)
