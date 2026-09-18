#!/usr/bin/env python3
"""Shared strict-input and import-identity contract for leftover6 catalogs."""

from __future__ import annotations

import json
from typing import Any

if __name__.startswith("pipelines."):
    from ..oracle_grounded.import_twins import bind_import_twin
    from ..strict_jsonl import strict_lf_jsonl_lines
    from ..tag_jsonutil import reject_duplicate_object_keys, reject_json_constant
else:
    from oracle_grounded.import_twins import bind_import_twin
    from strict_jsonl import strict_lf_jsonl_lines
    from tag_jsonutil import reject_duplicate_object_keys, reject_json_constant

__all__ = ["bind_import_twin", "load_strict_json", "strict_lf_jsonl_lines"]


def load_strict_json(payload: str | bytes) -> Any:
    """Decode catalog JSON without duplicate keys or non-standard constants."""

    return json.loads(
        payload,
        object_pairs_hook=reject_duplicate_object_keys,
        parse_constant=reject_json_constant,
    )


bind_import_twin(__name__)
