#!/usr/bin/env python3
"""The one place the dlk mill reaches main's shared primitives.

Both import forms are supported (``dlk.x`` with ``pipelines/`` on ``sys.path``,
and ``pipelines.dlk.x`` from the repository root); this shim resolves the
import twin binder, the exact-JSON serializer and the reviewed mill-identity
table under one name each, so every other module in the package imports only
its siblings and ``_contract``. Every module ends with
``bind_import_twin(__name__)`` so the two spellings are one object (the
``oracle_grounded`` convention).

The reviewed prefix home is the identity authority for this lane: the
``dlk`` prefix is pinned to ``distributed-lock-factory`` in
``mill_reviewed_vocabulary.REVIEWED_MILL_PREFIX_HOMES``, and this contract
refuses to load if that pin ever drifts.
"""

from __future__ import annotations

from typing import Any

if __name__.startswith("pipelines."):
    from ..exact_json import dumps_exact_json
    from ..mill_family import MILL_ID_RE, REVIEWED_MILL_PREFIX_HOMES, mill_prefix
    from ..oracle_grounded.import_twins import bind_import_twin
else:
    from exact_json import dumps_exact_json
    from mill_family import MILL_ID_RE, REVIEWED_MILL_PREFIX_HOMES, mill_prefix
    from oracle_grounded.import_twins import bind_import_twin

__all__ = [
    "EXPECTED",
    "FACTORY",
    "GEN",
    "MILL_ID_RE",
    "N_ROUNDS",
    "PREFIX",
    "PRESERVED_ROUNDS",
    "REVIEWED_HOME",
    "bind_import_twin",
    "dumps_exact_json",
    "mill_prefix",
]

# Identity pinned from the reviewed mill-identity table. The legacy scripts
# hard-coded ``distributed-lock-factory`` and ``grok-4.6``; the cleaned package
# re-derives the factory from the reviewed prefix home so a drift in the table
# is caught at import rather than silently authorizing a foreign lane.
PREFIX = "dlk"
FACTORY = "distributed-lock-factory"
GEN = "grok-4.6"
N_ROUNDS = 16
EXPECTED = 2
PRESERVED_ROUNDS = (1214, 1280)

REVIEWED_HOME = REVIEWED_MILL_PREFIX_HOMES[PREFIX]
if REVIEWED_HOME != FACTORY:  # pragma: no cover - the table pin is the authority
    raise ImportError(
        f"reviewed prefix home for {PREFIX!r} is {REVIEWED_HOME!r}, "
        f"not the dlk factory {FACTORY!r}"
    )


def canonical_json(value: Any) -> str:
    """Stable canonical JSON for catalog digests (sorted keys, exact decimals)."""
    return dumps_exact_json(value, ensure_ascii=True, sort_keys=True)


bind_import_twin(__name__)
