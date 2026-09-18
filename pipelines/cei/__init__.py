"""CSV/Excel ingest mill: pinned catalog, generate, CLI.

Hop-mill ``experiments/cei-mill-r81.py`` (39 ``_ok``/``_bad`` pairs) and
leftover leftover leftover ``experiments/cei_r48_mill.py`` (16 ``S()``
pairs) were AST-extracted (``git show`` + ``ast.parse``, never ``exec``)
into ``config/cei/``. Mills, hop-loop, and leftover leftover leftover
leftover3 importers stay on ``legacy-mill-lane``. This package does not
hop factories, does not write ``outputs/raw/``, and does not stamp
``grok-4.6``.
"""

from ._contract import bind_import_twin

__all__ = ["_contract", "catalog", "cli", "generate"]

bind_import_twin(__name__)
