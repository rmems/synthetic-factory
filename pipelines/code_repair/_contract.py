#!/usr/bin/env python3
"""The one place the code-repair family reaches main's shared primitives.

Both import forms are supported (``code_repair.x`` with ``pipelines/`` on
``sys.path``, and ``pipelines.code_repair.x`` from the repository root); this
shim resolves the contract facade, the envelope, the shared draw stream and
refusal base, the raw-tree guard and the hidden-reasoning key check under one
name each, so every other module in the package imports only its siblings and
``_contract``. Every module ends with ``bind_import_twin(__name__)`` so the two
spellings are one object (the ``oracle_grounded`` convention).
"""

from __future__ import annotations

import json

if __name__.startswith("pipelines."):
    from ..exact_json import ExactJSONFloat, exact_fraction
    from ..curate_coding import contains_hidden_reasoning_key
    from ..oracle_grounded import distill_contract as oc
    from ..oracle_grounded import distill_vocabulary as vocab
    from ..oracle_grounded import envelope, refusals, rng
    from ..oracle_grounded.import_twins import bind_import_twin
    from ..raw_tree_guard import is_under_raw
    from ..tag_jsonutil import reject_duplicate_object_keys, reject_json_constant
    from ..validate_run_provenance import check_provenance_publish
else:
    from exact_json import ExactJSONFloat, exact_fraction
    from curate_coding import contains_hidden_reasoning_key
    from oracle_grounded import distill_contract as oc
    from oracle_grounded import distill_vocabulary as vocab
    from oracle_grounded import envelope, refusals, rng
    from oracle_grounded.import_twins import bind_import_twin
    from raw_tree_guard import is_under_raw
    from tag_jsonutil import reject_duplicate_object_keys, reject_json_constant
    from validate_run_provenance import check_provenance_publish

__all__ = [
    "ExactJSONFloat",
    "bind_import_twin",
    "contains_hidden_reasoning_key",
    "check_provenance_publish",
    "envelope",
    "exact_fraction",
    "is_under_raw",
    "load_strict_json",
    "oc",
    "refusals",
    "rng",
    "vocab",
]

def load_strict_json(payload: str | bytes):
    """Keep exact decimal tokens at code-repair evidence and metadata boundaries."""
    return json.loads(payload, object_pairs_hook=reject_duplicate_object_keys,
                      parse_constant=reject_json_constant, parse_float=ExactJSONFloat)


bind_import_twin(__name__)
