"""Distributed-lock mill (prefix ``dlk``).

Family home for the generator preserved on ``legacy-mill-lane`` as
``experiments/dlk_r1214_leftover3_mill.py`` and
``experiments/dlk_r1280_leftover3_mill.py``. Target factory:
``distributed-lock-factory`` (reviewed prefix home ``dlk`` in
``mill_reviewed_vocabulary.REVIEWED_MILL_PREFIX_HOMES``).

This is the *cleaned* package. The legacy scripts each carried a plant catalog
plus pure episode builders (``step``/``success_ep``/``fail_ep``/``notes``) and
an exec path (``txn``/``main``) that published raw rounds by shelling out to
``round_txn.py``. Only the data and the pure builders are carried over: the
plant catalog lives under ``config/dlk/`` and the builders live in
:mod:`.generate`. The exec path is deliberately not reproduced -- this package
never executes the generator and never writes a raw round.
"""

__all__ = ("_contract catalog generate cli").split()

from . import _contract  # noqa: F401  -- binds the import twin for the package
