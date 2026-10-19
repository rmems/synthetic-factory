#!/usr/bin/env python3
"""The one place the task gate reaches main's shared primitives.

Both import forms work (``task_gate.x`` with ``pipelines/`` on ``sys.path`` and
``pipelines.task_gate.x`` from the repository root). Every module ends with
``bind_import_twin(__name__)`` so the two spellings are one object.
"""

from __future__ import annotations

if __name__.startswith("pipelines."):
    from ..compose_destination_rename import rename_noreplace
    from ..exact_json import dumps_exact_json
    from ..oracle_grounded.import_twins import bind_import_twin
    from ..raw_tree_guard import is_under_raw
    from ..strict_jsonl import StrictJsonlError, strict_lf_jsonl_lines
    from ..tag_jsonutil import reject_duplicate_object_keys, reject_json_constant
else:
    from compose_destination_rename import rename_noreplace
    from exact_json import dumps_exact_json
    from oracle_grounded.import_twins import bind_import_twin
    from raw_tree_guard import is_under_raw
    from strict_jsonl import StrictJsonlError, strict_lf_jsonl_lines
    from tag_jsonutil import reject_duplicate_object_keys, reject_json_constant

import json
from typing import Any

__all__ = [
    "StrictJsonlError",
    "bind_import_twin",
    "dumps_exact_json",
    "is_under_raw",
    "load_strict_json",
    "rename_noreplace",
    "strict_lf_jsonl_lines",
]


def load_strict_json(text: str) -> Any:
    """Parse one JSON value, refusing duplicate keys and ``NaN``/``Infinity`` constants."""

    return json.loads(
        text, object_pairs_hook=reject_duplicate_object_keys, parse_constant=reject_json_constant,
    )


bind_import_twin(__name__)
