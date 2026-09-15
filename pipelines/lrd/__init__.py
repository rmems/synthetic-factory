"""Log-redaction leftover mill (prefix ``lrd``).

Family home for the first leftover leftover leftover mill preserved on
``legacy-mill-lane`` as
``experiments/lrd_r157_leftover_leftover_leftover_mill.py``. Target factory:
``log-redaction-factory`` (reviewed prefix home ``lrd``).

This is the *cleaned* first slice. The preserve commit also carried leftover3
mills, ``lrd-loop-*`` drivers, and ``dpr-lrd-hopper*`` scripts. Only the r157
``PAIRS`` literals are AST-extracted (``git show`` + ``ast.parse``, never
``exec`` / ``import``). Hoppers stay with ``dpr``; this package refuses hopper
exec. Loops and leftover3 mills are a later slice. The exec path (``txn`` /
``main`` / ``subprocess``) is not reproduced and nothing writes
``outputs/raw/``.
"""

from ._contract import bind_import_twin

__all__ = ["_contract", "catalog", "cli", "generate"]

bind_import_twin(__name__)
