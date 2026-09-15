"""Payment-idempotency (pay) lane: cleaned r330 episode data and builders.

Mill burst FAMILY=pay. The composer is cancelled; this package owns the pay
lane. It is the cleaned, AST-extracted form of the legacy staging script
``experiments/mill_leftover_leftover_leftover_pay_r330.py`` from
``origin/legacy-mill-lane``: the 16 payment-provider pairs and the pure
``success_ep`` / ``fail_ep`` / ``notes`` builders live here as an importable
package. The staging/execution machinery that drove ``round_txn.py`` via
subprocess is intentionally not vendored — this package performs no I/O and
is never executed on this branch.

Distinct from r324-r329; no ``sir-``/``dbc-`` ids.
"""

from __future__ import annotations

from .episodes import db, fail_ep, success_ep
from .notes import notes
from .pairs import FAC, GEN, PAIRS, PREFIX

__all__ = [
    "FAC",
    "GEN",
    "PAIRS",
    "PREFIX",
    "db",
    "fail_ep",
    "notes",
    "success_ep",
]
