#!/usr/bin/env python3
"""Shared primitives for the model-channel generator package.

Both import forms are supported (``model_channel.x`` with ``pipelines/`` on
``sys.path``, and ``pipelines.model_channel.x`` from the repository root).
"""

from __future__ import annotations

import json
from types import MappingProxyType
from typing import Any

if __name__.startswith("pipelines."):
    from ..compose_destination_rename import rename_noreplace
    from ..exact_json import ExactJSONFloat, dumps_exact_json
    from ..oracle_grounded.import_twins import bind_import_twin
    from ..raw_tree_guard import is_under_raw
    from ..tag_jsonutil import reject_duplicate_object_keys, reject_json_constant
    from ..validate_run import check_episode
    from ..validate_run_episode_turns import _normalized_hidden_key as normalized_key
else:
    from compose_destination_rename import rename_noreplace
    from exact_json import ExactJSONFloat, dumps_exact_json
    from oracle_grounded.import_twins import bind_import_twin
    from raw_tree_guard import is_under_raw
    from tag_jsonutil import reject_duplicate_object_keys, reject_json_constant
    from validate_run import check_episode
    from validate_run_episode_turns import _normalized_hidden_key as normalized_key

__all__ = [
    "ExactJSONFloat",
    "bind_import_twin",
    "check_episode",
    "dumps_exact_json",
    "freeze",
    "is_under_raw",
    "load_strict_json",
    "normalized_key",
    "rename_noreplace",
]


def load_strict_json(payload: str | bytes):
    """Keep exact decimal tokens at model-channel evidence boundaries."""
    return json.loads(
        payload,
        object_pairs_hook=reject_duplicate_object_keys,
        parse_constant=reject_json_constant,
        parse_float=ExactJSONFloat,
    )


def freeze(value: Any) -> Any:
    """Keep loaded model policy and generation-time snapshots immutable."""
    if isinstance(value, dict):
        return MappingProxyType({key: freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(freeze(item) for item in value)
    return value


bind_import_twin(__name__)
