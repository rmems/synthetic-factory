#!/usr/bin/env python3
"""Run-level payload shape validation for identity curation.

Split out of ``curate_identity_owners.py`` (CodeScene/qlty: High total
complexity) by responsibility; ``shape_validation_errors`` remains
re-exported from ``curate_identity`` so existing ``curate_identity.X`` call
sites and test seams resolve unchanged.

The checks delegate to the shared ``validate_run`` shape checkers while
intentionally accepting the legacy provenance vocabulary that
canonicalization rewrites below; only the structural invariants gate entry
into a cleaned tree.
"""

from __future__ import annotations

import sys
from typing import Any, Mapping

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("curate_identity_shapes")
    from . import curate_identity_json as _identity_json
    from . import curate_identity_owners as _owners
    from .record_kind import preference_side_kinds
    from .validate_run import (
        check_episode,
        check_multi_agent,
        check_safety_case,
        check_spike_order,
        check_thalamic,
    )
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "curate_identity_shapes"
    )
    import curate_identity_json as _identity_json
    import curate_identity_owners as _owners
    from record_kind import preference_side_kinds
    from validate_run import (
        check_episode,
        check_multi_agent,
        check_safety_case,
        check_spike_order,
        check_thalamic,
    )

IdentityCurationError = _identity_json.IdentityCurationError


def structural_thalamic_errors(owner: Mapping[str, Any], owner_where: str) -> list[str]:
    # Identity intentionally accepts the legacy provenance vocabulary and
    # canonicalizes it below. Every other Thalamic invariant is
    # structural and must pass before the record can enter a cleaned tree.
    return [
        error
        for error in check_thalamic(owner, owner_where)
        if not error.startswith(f"{owner_where}: state.sim_or_real must ")
    ]


def _missing_side_goal(side_specs) -> bool:
    for (_owner_path, owner), side_kind in side_specs:
        if side_kind != "episode":
            continue
        if "goal" not in owner:
            return True
    return False


def _preference_goal_errors(record: Mapping[str, Any], side_specs) -> list[str]:
    if "goal" not in record:
        return []
    if not _missing_side_goal(side_specs):
        return []
    wrapper_goal = record["goal"]
    if not isinstance(wrapper_goal, str):
        return ["record: inherited goal must be a non-empty string"]
    if not wrapper_goal.strip():
        return ["record: inherited goal must be a non-empty string"]
    return []


def _preference_side_errors(
    owner_path: str,
    owner: Mapping[str, Any],
    side_kind: str,
    record: Mapping[str, Any],
) -> list[str]:
    if side_kind == "episode":
        return check_episode(
            owner,
            f"record{owner_path}",
            require_goal="goal" not in record,
        )
    if side_kind == "thalamic":
        return structural_thalamic_errors(owner, f"record{owner_path}")
    return [f"record{owner_path}: unsupported preference-side shape"]


def _preference_shape_errors(record: Mapping[str, Any], owners) -> list[str]:
    if owners is None:
        try:
            owners = _owners.owner_specs(record, "preference")
        except IdentityCurationError as exc:
            return [str(exc)]
    side_specs = tuple(zip(owners, preference_side_kinds(record), strict=True))
    errors = _preference_goal_errors(record, side_specs)
    for (owner_path, owner), side_kind in side_specs:
        errors.extend(_preference_side_errors(owner_path, owner, side_kind, record))
    return errors


def _bridge_shape_errors(record: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    events = record.get("spike_events")
    if not isinstance(events, list):
        errors.append("record: spike_events must be a non-empty array")
    elif not events:
        errors.append("record: spike_events must be a non-empty array")
    else:
        errors.extend(check_spike_order(events, "record", enclosing=record))
    language_view = record.get("language_view")
    if not isinstance(language_view, Mapping):
        errors.append("record: language_view must be an object")
        return errors
    trajectory = language_view.get("trajectory")
    if not isinstance(trajectory, Mapping):
        errors.append("record: language_view.trajectory missing or not an object")
        return errors
    errors.extend(
        structural_thalamic_errors(trajectory, "record.language_view.trajectory")
    )
    return errors


_SIMPLE_SHAPE_CHECKS = {
    "episode": check_episode,
    "safety_case": check_safety_case,
    "multi_agent": check_multi_agent,
}


def shape_validation_errors(
    record: Mapping[str, Any],
    kind: str,
    owners: list[tuple[str, Mapping[str, Any]]] | None = None,
) -> list[str]:
    if kind == "thalamic":
        return structural_thalamic_errors(record, "record")
    if kind == "preference":
        return _preference_shape_errors(record, owners)
    if kind == "bridge_pair":
        return _bridge_shape_errors(record)
    handler = _SIMPLE_SHAPE_CHECKS.get(kind)
    return [] if handler is None else handler(record, "record")


if __package__:
    _expose_package_sibling(__name__)
