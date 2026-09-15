#!/usr/bin/env python3
"""The one place the ACTF family reaches main's shared primitives.

Both import forms are supported (``actf.x`` with ``pipelines/`` on
``sys.path``, and ``pipelines.actf.x`` from the repository root). Every
module ends with ``bind_import_twin(__name__)`` so the two spellings are
one object.
"""

from __future__ import annotations

import json

if __name__.startswith("pipelines."):
    from ..exact_json import ExactJSONFloat, dumps_exact_json
    from ..oracle_grounded import envelope, refusals
    from ..oracle_grounded.import_twins import bind_import_twin
    from ..raw_tree_guard import is_under_raw
    from ..tag_jsonutil import reject_duplicate_object_keys, reject_json_constant
else:
    from exact_json import ExactJSONFloat, dumps_exact_json
    from oracle_grounded import envelope, refusals
    from oracle_grounded.import_twins import bind_import_twin
    from raw_tree_guard import is_under_raw
    from tag_jsonutil import reject_duplicate_object_keys, reject_json_constant

__all__ = [
    "ExactJSONFloat",
    "bind_import_twin",
    "dumps_exact_json",
    "envelope",
    "is_under_raw",
    "load_strict_json",
    "refusals",
]


def load_strict_json(payload: str | bytes):
    """Keep exact decimal tokens at ACTF metadata boundaries."""
    return json.loads(
        payload,
        object_pairs_hook=reject_duplicate_object_keys,
        parse_constant=reject_json_constant,
        parse_float=ExactJSONFloat,
    )


bind_import_twin(__name__)
