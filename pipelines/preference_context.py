#!/usr/bin/env python3
"""Compare the two branches of a preference pair, field by field.

``chosen`` and ``rejected`` are supposed to describe the *same* situation and
differ only in what the model did about it. This module answers the two
questions that claim rests on: where exactly the two branches' canonical
context diverges, and whether each canonical field agreed on the source side
before anything was repaired.

Comparison is by canonical JSON, never by Python object identity, and the
diff paths it reports are the vocabulary the exclusion reason codes are
derived from. Nothing here mutates a record or decides its fate.
"""

from __future__ import annotations

import sys
from typing import Any

if __package__:
    from . import _expose_package_sibling, _local_sibling_module, _require_local_sibling

    if _local_sibling_module("preference_context", allow_initializing=True):
        import preference_context as _direct_preference_context

        _require_local_sibling(_direct_preference_context, "preference_context")
        del _direct_preference_context
    from .preference_model import canonical_json
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "preference_context"
    )
    from preference_model import canonical_json

__all__ = [
    "all_context_diffs",
    "context_field_agreement",
    "context_is_pure",
    "diff_paths_between",
    "is_trajectory_pair",
    "pair_context",
]


def _dict_diff_paths(left: dict[str, Any], right: dict[str, Any], prefix: str) -> list[str]:
    paths: list[str] = []
    for key in sorted(set(left) | set(right)):
        paths.extend(_dict_key_diff_paths(left, right, prefix, key))
    return paths


def _dict_key_diff_paths(
    left: dict[str, Any],
    right: dict[str, Any],
    prefix: str,
    key: str,
) -> list[str]:
    """Return the diff paths contributed by one dictionary key."""

    path = f"{prefix}.{key}"
    if key not in left or key not in right:
        return [path]
    return diff_paths_between(left[key], right[key], path)


def _list_diff_paths(left: list[Any], right: list[Any], prefix: str) -> list[str]:
    if len(left) != len(right):
        return [prefix]
    paths: list[str] = []
    for index, (left_item, right_item) in enumerate(zip(left, right)):
        paths.extend(diff_paths_between(left_item, right_item, f"{prefix}[{index}]"))
    return paths


def diff_paths_between(left: Any, right: Any, prefix: str) -> list[str]:
    """Return stable leaf paths whose values differ."""

    if type(left) is not type(right):
        return [prefix]
    if isinstance(left, dict):
        return _dict_diff_paths(left, right, prefix)
    if isinstance(left, list):
        return _list_diff_paths(left, right, prefix)
    if left == right:
        return []
    return [prefix]


def pair_context(
    record: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]] | None:
    chosen = record.get("chosen")
    rejected = record.get("rejected")
    if not isinstance(chosen, dict) or not isinstance(rejected, dict):
        return None
    if not all(
        isinstance(side.get(field), dict)
        for side in (chosen, rejected)
        for field in ("state", "proposed_action")
    ):
        return None
    return chosen, rejected


def is_trajectory_pair(record: dict[str, Any]) -> bool:
    """Whether both sides are step trajectories rather than same-state sides.

    Trajectory pairs are curated by ``curate_trajectory_preferences.py``; this
    predicate exists only so their exclusion here is named honestly.
    """

    sides = (record.get("chosen"), record.get("rejected"))
    return all(
        isinstance(side, dict) and isinstance(side.get("steps"), list)
        for side in sides
    )


def context_is_pure(record: dict[str, Any]) -> bool:
    """Whether a preference record has canonical same-state/same-proposal context."""

    context = pair_context(record)
    if context is None:
        return False
    chosen, rejected = context
    try:
        return all(
            canonical_json(chosen[field]) == canonical_json(rejected[field])
            for field in ("state", "proposed_action")
        )
    except (ValueError, TypeError):
        # UnicodeEncodeError is a ValueError, so a lone surrogate is
        # caught here too; naming it as well would be redundant.
        return False


def _field_agreement(record: Any, field: str) -> bool | None:
    """Measure one context field without depending on the other field."""

    if not isinstance(record, dict):
        return None
    chosen = record.get("chosen")
    rejected = record.get("rejected")
    if not isinstance(chosen, dict) or not isinstance(rejected, dict):
        return None
    chosen_value = chosen.get(field)
    rejected_value = rejected.get(field)
    if not isinstance(chosen_value, dict) or not isinstance(rejected_value, dict):
        return None
    try:
        return canonical_json(chosen_value) == canonical_json(rejected_value)
    except (ValueError, TypeError):
        # UnicodeEncodeError is a ValueError, so a lone surrogate is
        # caught here too; naming it as well would be redundant.
        return None


def context_field_agreement(
    record: Any,
) -> tuple[bool | None, bool | None]:
    """Return ``(same_state, same_proposed_action)`` for one source pair.

    ``same_state`` is exactly the invariant a Hub-side ``same_state`` audit
    measures. ``same_proposed_action`` is the second half of the same-context
    contract, which such an audit does not see: a pair may hold state constant
    and still swap the proposed action. Both are ``None`` when the record
    carries no comparable preference context.
    """

    return (
        _field_agreement(record, "state"),
        _field_agreement(record, "proposed_action"),
    )


def all_context_diffs(chosen: dict[str, Any], rejected: dict[str, Any]) -> tuple[str, ...]:
    paths: list[str] = []
    for field in ("state", "proposed_action"):
        paths.extend(diff_paths_between(chosen[field], rejected[field], field))
    return tuple(paths)


if __package__:
    _expose_package_sibling(__name__)
