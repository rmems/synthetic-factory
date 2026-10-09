#!/usr/bin/env python3
"""The one place the tool-world package reaches main's shared primitives.

Both import forms are supported (``tool_world.x`` with ``pipelines/`` on
``sys.path``, and ``pipelines.tool_world.x`` from the repository root). Every
other module imports only its siblings and ``_contract``, and every module
ends with ``bind_import_twin(__name__)``.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

if __name__.startswith("pipelines."):
    from ..curate_coding import contains_hidden_reasoning_key
    from ..exact_json import ExactJSONFloat, dumps_exact_json
    from ..oracle_grounded import envelope, refusals, rng
    from ..oracle_grounded.import_twins import bind_import_twin
    from ..raw_tree_guard import is_under_raw
    from ..tag_jsonutil import reject_duplicate_object_keys, reject_json_constant
    from ..validate_run import check_episode
    from ..validate_run_episode_turns import OBSERVABLE_BASIS_RE
    from ..validate_run_outcomes import terminal_outcome_agrees
else:
    from curate_coding import contains_hidden_reasoning_key
    from exact_json import ExactJSONFloat, dumps_exact_json
    from oracle_grounded import envelope, refusals, rng
    from oracle_grounded.import_twins import bind_import_twin
    from raw_tree_guard import is_under_raw
    from tag_jsonutil import reject_duplicate_object_keys, reject_json_constant
    from validate_run import check_episode
    from validate_run_episode_turns import OBSERVABLE_BASIS_RE
    from validate_run_outcomes import terminal_outcome_agrees

__all__ = [
    "OBSERVABLE_BASIS_RE",
    "ExactJSONFloat",
    "bind_import_twin",
    "canonical_bytes",
    "check_episode",
    "contains_hidden_reasoning_key",
    "dumps_exact_json",
    "envelope",
    "is_under_raw",
    "load_strict_json",
    "refusals",
    "rng",
    "sha256_bytes",
    "sha256_canonical",
    "terminal_outcome_agrees",
]


def load_strict_json(payload: str | bytes) -> Any:
    """Keep exact decimal tokens at pack and record boundaries."""
    return json.loads(
        payload,
        object_pairs_hook=reject_duplicate_object_keys,
        parse_constant=reject_json_constant,
        parse_float=ExactJSONFloat,
    )


def canonical_bytes(value: Any) -> bytes:
    """Sorted-key, ASCII, no-whitespace JSON: the bytes every digest is taken over."""
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    ).encode("ascii")


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_canonical(value: Any) -> str:
    return sha256_bytes(canonical_bytes(value))


bind_import_twin(__name__)
