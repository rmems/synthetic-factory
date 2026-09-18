"""Log-redaction leftover mill (prefix ``lrd``).

Family home for the first leftover leftover leftover mill preserved on
``legacy-mill-lane`` as
``experiments/lrd_r157_leftover_leftover_leftover_mill.py``. Target factory:
``log-redaction-factory`` (reviewed prefix home ``lrd``).

The committed catalog is a *representative* slice (see ``config/lrd``): all
eight leftover mills on ``legacy-mill-lane`` @ ``813f93f`` are AST-extracted
(``git show`` + ``ast.parse``, never ``exec`` / ``import``), with full mill
inventory pinned in ``CATALOG.json``. ``generate`` replays only legacy r157
plants today; leftover3 / ``P()`` / ``lll`` rows are catalog-pinned for later
replay. Hoppers stay with ``dpr``; loops are excluded. Nothing writes
``outputs/raw/``.
"""

from ._contract import bind_import_twin

__all__ = ["_contract", "catalog", "cli", "generate"]

bind_import_twin(__name__)
