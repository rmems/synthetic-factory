#!/usr/bin/env python3
"""Payload-shape checks used before identity provenance is canonicalized.

Split out of ``curate_identity.py`` (A11 of #211). Identity still accepts the
legacy ``state.sim_or_real`` vocabulary and canonicalizes it later; every other
Thalamic, episode, preference, bridge, safety-case and multi-agent invariant
must pass before a record can enter a cleaned tree. The facade re-exports
``_shape_validation_errors`` so ``CurationDependencies`` and the identity
tests keep resolving the same name.
"""

from __future__ import annotations

import sys
from collections.abc import Callable, Mapping
from typing import Any

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("curate_identity_shape")
    from .curate_identity_json import IdentityCurationError
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
        "curate_identity_shape"
    )
    from curate_identity_json import IdentityCurationError
    from record_kind import preference_side_kinds
    from validate_run import (
        check_episode,
        check_multi_agent,
        check_safety_case,
        check_spike_order,
        check_thalamic,
    )


def _structural_thalamic_errors(owner: Mapping[str, Any], owner_where: str) -> list[str]:
    # Identity intentionally accepts the legacy provenance vocabulary and
    # canonicalizes it below. Every other Thalamic invariant is
    # structural and must pass before the record can enter a cleaned tree.
    return [
        error
        for error in check_thalamic(owner, owner_where)
        if not error.startswith(f"{owner_where}: state.sim_or_real must ")
    ]


def _inherited_preference_goal_error(
    record: Mapping[str, Any],
    side_specs: tuple[tuple[tuple[str, Mapping[str, Any]], str], ...],
) -> str | None:
    if "goal" not in record:
        return None
    if not any(
        side_kind == "episode" and "goal" not in owner
        for ((_owner_path, owner), side_kind) in side_specs
    ):
        return None
    wrapper_goal = record["goal"]
    if not isinstance(wrapper_goal, str) or not wrapper_goal.strip():
        return "record: inherited goal must be a non-empty string"
    return None


def _preference_side_errors(
    record: Mapping[str, Any],
    side_specs: tuple[tuple[tuple[str, Mapping[str, Any]], str], ...],
) -> list[str]:
    errors: list[str] = []
    inherited = _inherited_preference_goal_error(record, side_specs)
    if inherited is not None:
        errors.append(inherited)
    for (owner_path, owner), side_kind in side_specs:
        if side_kind == "episode":
            errors.extend(
                check_episode(
                    owner,
                    f"record{owner_path}",
                    require_goal="goal" not in record,
                )
            )
        elif side_kind == "thalamic":
            errors.extend(_structural_thalamic_errors(owner, f"record{owner_path}"))
        else:
            errors.append(f"record{owner_path}: unsupported preference-side shape")
    return errors


def _preference_shape_errors(
    record: Mapping[str, Any],
    owner_specs: list[tuple[str, Mapping[str, Any]]] | None,
    owner_specs_fn: Callable[..., list[tuple[str, Mapping[str, Any]]]],
) -> list[str]:
    if owner_specs is None:
        try:
            owner_specs = owner_specs_fn(record, "preference")
        except IdentityCurationError as exc:
            return [str(exc)]
    side_specs = tuple(zip(owner_specs, preference_side_kinds(record), strict=True))
    return _preference_side_errors(record, side_specs)


def _bridge_language_view_errors(record: Mapping[str, Any]) -> list[str]:
    language_view = record.get("language_view")
    if not isinstance(language_view, Mapping):
        return ["record: language_view must be an object"]
    trajectory = language_view.get("trajectory")
    if not isinstance(trajectory, Mapping):
        return ["record: language_view.trajectory missing or not an object"]
    return _structural_thalamic_errors(trajectory, "record.language_view.trajectory")


def _bridge_pair_shape_errors(record: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    events = record.get("spike_events")
    if not isinstance(events, list) or not events:
        errors.append("record: spike_events must be a non-empty array")
    else:
        errors.extend(check_spike_order(events, "record", enclosing=record))
    errors.extend(_bridge_language_view_errors(record))
    return errors


_SIMPLE_VALIDATORS = {
    "episode": check_episode,
    "safety_case": check_safety_case,
    "multi_agent": check_multi_agent,
}


def _simple_shape_errors(record: Mapping[str, Any], kind: str) -> list[str]:
    validator = _SIMPLE_VALIDATORS.get(kind)
    if validator is None:
        return []
    return validator(record, "record")


def shape_validation_errors(
    record: Mapping[str, Any],
    kind: str,
    owner_specs: list[tuple[str, Mapping[str, Any]]] | None = None,
    *,
    owner_specs_fn: Callable[..., list[tuple[str, Mapping[str, Any]]]],
) -> list[str]:
    """Return structural shape errors for one classified identity record."""

    if kind == "preference":
        return _preference_shape_errors(record, owner_specs, owner_specs_fn)
    if kind == "bridge_pair":
        return _bridge_pair_shape_errors(record)
    if kind == "thalamic":
        return _structural_thalamic_errors(record, "record")
    return _simple_shape_errors(record, kind)


if __package__:
    _expose_package_sibling(__name__)
