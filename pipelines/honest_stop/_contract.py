"""Shared primitives for the honest-stop family.

Both import forms work (``honest_stop.x`` with ``pipelines/`` on ``sys.path``
and ``pipelines.honest_stop.x``). Every module ends with
``bind_import_twin(__name__)`` so the two spellings are one object.
"""

from __future__ import annotations

import json
from typing import Any

if __name__.startswith("pipelines."):
    from ..exact_json import dumps_exact_json
    from ..oracle_grounded.import_twins import bind_import_twin
    from ..raw_tree_guard import is_under_raw
    from ..tag_jsonutil import reject_duplicate_object_keys, reject_json_constant
else:
    from exact_json import dumps_exact_json
    from oracle_grounded.import_twins import bind_import_twin
    from raw_tree_guard import is_under_raw
    from tag_jsonutil import reject_duplicate_object_keys, reject_json_constant

__all__ = [
    "bind_import_twin",
    "dumps_exact_json",
    "is_under_raw",
    "load_strict_json",
]


def load_strict_json(text: str) -> Any:
    """Parse one JSON value, refusing duplicate keys and non-standard numbers."""

    return json.loads(
        text,
        object_pairs_hook=reject_duplicate_object_keys,
        parse_constant=reject_json_constant,
    )


bind_import_twin(__name__)
