#!/usr/bin/env python3
"""The one place the mill family reaches main's shared primitives.

Both import forms are supported (``mill.x`` with ``pipelines/`` on
``sys.path``, and ``pipelines.mill.x`` from the repository root). Every
other module imports only its siblings and ``_contract``. Every module
ends with ``bind_import_twin(__name__)``.
"""

from __future__ import annotations

import json

if __name__.startswith("pipelines."):
    from ..curate_coding import contains_hidden_reasoning_key
    from ..exact_json import ExactJSONFloat, dumps_exact_json
    from ..oracle_grounded import distill_contract as oc
    from ..oracle_grounded import distill_vocabulary as vocab
    from ..oracle_grounded import envelope, refusals, rng
    from ..oracle_grounded.import_twins import bind_import_twin
    from ..raw_tree_guard import is_under_raw
    from ..tag_jsonutil import reject_duplicate_object_keys, reject_json_constant
else:
    from curate_coding import contains_hidden_reasoning_key
    from exact_json import ExactJSONFloat, dumps_exact_json
    from oracle_grounded import distill_contract as oc
    from oracle_grounded import distill_vocabulary as vocab
    from oracle_grounded import envelope, refusals, rng
    from oracle_grounded.import_twins import bind_import_twin
    from raw_tree_guard import is_under_raw
    from tag_jsonutil import reject_duplicate_object_keys, reject_json_constant

__all__ = [
    "ExactJSONFloat",
    "bind_import_twin",
    "contains_hidden_reasoning_key",
    "dumps_exact_json",
    "envelope",
    "is_under_raw",
    "load_strict_json",
    "oc",
    "refusals",
    "rng",
    "vocab",
]


def load_strict_json(payload: str | bytes):
    """Keep exact decimal tokens at mill catalog and record boundaries."""
    return json.loads(
        payload,
        object_pairs_hook=reject_duplicate_object_keys,
        parse_constant=reject_json_constant,
        parse_float=ExactJSONFloat,
    )


bind_import_twin(__name__)
