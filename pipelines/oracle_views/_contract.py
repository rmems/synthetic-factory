"""The one place the oracle text views reach main's shared primitives.

Both import forms are supported (``oracle_views.x`` with ``pipelines/`` on
``sys.path``, and ``pipelines.oracle_views.x`` from the repository root); this
shim resolves the canonical-JSON digest, the envelope, the family constants,
the coded refusal base, exact-JSON serialization, the hidden-reasoning key
check, the raw-tree guard, the operator path confinement and the shared oracle
run validator under one name each, so every other module in the package imports
only its siblings and ``_contract``.
"""

from __future__ import annotations

if __name__.startswith("pipelines."):
    from .. import oracle_validate as validator
    from ..curate_coding import contains_hidden_reasoning_key
    from ..exact_json import dumps_exact_json
    from ..operator_paths import confine
    from ..oracle_grounded import canon, envelope, families, record, refusals, sim
    from ..oracle_grounded.import_twins import bind_import_twin
    from ..raw_tree_guard import is_under_raw
else:
    import oracle_validate as validator
    from curate_coding import contains_hidden_reasoning_key
    from exact_json import dumps_exact_json
    from operator_paths import confine
    from oracle_grounded import canon, envelope, families, record, refusals, sim
    from oracle_grounded.import_twins import bind_import_twin
    from raw_tree_guard import is_under_raw

__all__ = [
    "bind_import_twin",
    "canon",
    "confine",
    "contains_hidden_reasoning_key",
    "dumps_exact_json",
    "envelope",
    "families",
    "is_under_raw",
    "record",
    "refusals",
    "sim",
    "validator",
]

bind_import_twin(__name__)
