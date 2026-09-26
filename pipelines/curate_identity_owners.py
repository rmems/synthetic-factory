#!/usr/bin/env python3
"""Owner decomposition and payload shape validation for identity curation.

Split out of ``curate_identity.py`` (CodeScene: Lines of Code in a Single
File) by responsibility; every name is re-exported from ``curate_identity``
so existing ``curate_identity.X`` call sites and test seams resolve
unchanged.

Owner specs decompose a classified record into the trajectory owners whose
IDs and provenance are rewritten; shape validation applies the run-level
structural checks while intentionally accepting the legacy provenance
vocabulary that canonicalization rewrites below.
"""

from __future__ import annotations

import copy
import sys
from typing import Any, Mapping

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("curate_identity_owners")
    from . import curate_identity_json as _identity_json
    from . import curate_identity_sources as _sources
    from .record_kind import PREFERENCE_SIDE_KINDS, preference_side_kinds
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "curate_identity_owners"
    )
    import curate_identity_json as _identity_json
    import curate_identity_sources as _sources
    from record_kind import PREFERENCE_SIDE_KINDS, preference_side_kinds

IdentityCurationError = _identity_json.IdentityCurationError

LEGACY_ID_KEYS = ("id", "record_id", "trajectory_id", "episode_id", "pair_id")


def legacy_ids(owner: Mapping[str, Any], owner_path: str) -> list[dict[str, Any]]:
    forms: list[dict[str, Any]] = []

    def collect(container: Any, base: str) -> None:
        if not isinstance(container, Mapping):
            return
        for key in LEGACY_ID_KEYS:
            if key in container:
                forms.append(
                    {
                        "path": _sources.pointer(base, key),
                        "value": copy.deepcopy(container[key]),
                    }
                )

    collect(owner, owner_path)
    collect(owner.get("meta"), _sources.pointer(owner_path, "meta"))
    collect(owner.get("state"), _sources.pointer(owner_path, "state"))
    return forms


def discover_original_ids(
    record: Any,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Collect reversible IDs without granting shape or factory authority.

    This walk intentionally uses only safely discoverable object boundaries.
    It therefore remains useful on malformed or unauthorized wrappers without
    treating those wrappers as valid owner specifications.
    """

    if not isinstance(record, Mapping):
        return [], []
    root_ids = legacy_ids(record, "/")
    all_ids = list(root_ids)
    nested = [(f"/{side}", record.get(side)) for side in ("chosen", "rejected")]
    view = record.get("language_view")
    if isinstance(view, Mapping):
        nested.append(("/language_view/trajectory", view.get("trajectory")))
    for owner_path, owner in nested:
        if isinstance(owner, Mapping):
            all_ids.extend(legacy_ids(owner, owner_path))
    return root_ids, all_ids


def _preference_owners(record: Mapping[str, Any]) -> list[tuple[str, Mapping[str, Any]]]:
    owners = []
    for side in ("chosen", "rejected"):
        owner = record.get(side)
        if not isinstance(owner, Mapping):
            raise IdentityCurationError(f"preference {side} must be an object")
        owners.append((f"/{side}", owner))
    return owners


def _require_homogeneous_side_kinds(side_kinds) -> None:
    if side_kinds[0] != side_kinds[1]:
        raise IdentityCurationError(
            "preference sides must be a homogeneous episode or thalamic pair "
            f"(got chosen={side_kinds[0]}, rejected={side_kinds[1]})"
        )
    if side_kinds[0] not in PREFERENCE_SIDE_KINDS:
        raise IdentityCurationError(
            "preference sides must be a homogeneous episode or thalamic pair "
            f"(got chosen={side_kinds[0]}, rejected={side_kinds[1]})"
        )


def _require_allowed_side_kind(
    side_kind: str, allowed_preference_side_kinds: frozenset[str] | None
) -> None:
    if allowed_preference_side_kinds is None:
        return
    if side_kind not in allowed_preference_side_kinds:
        raise IdentityCurationError(
            "preference side kind is not authorized by the factory contract "
            f"(got {side_kind}, allowed="
            f"{sorted(allowed_preference_side_kinds)})"
        )


def _preference_owner_specs(
    record: Mapping[str, Any], allowed_preference_side_kinds: frozenset[str] | None
) -> list[tuple[str, Mapping[str, Any]]]:
    owners = _preference_owners(record)
    side_kinds = preference_side_kinds(record)
    _require_homogeneous_side_kinds(side_kinds)
    _require_allowed_side_kind(side_kinds[0], allowed_preference_side_kinds)
    return owners


def _bridge_owner_specs(record: Mapping[str, Any]) -> list[tuple[str, Mapping[str, Any]]]:
    language_view = record.get("language_view")
    if not isinstance(language_view, Mapping):
        raise IdentityCurationError("bridge language_view must be an object")
    trajectory = language_view.get("trajectory")
    if not isinstance(trajectory, Mapping):
        raise IdentityCurationError("bridge language_view.trajectory must be an object")
    return [("/language_view/trajectory", trajectory)]


def owner_specs(
    record: Mapping[str, Any],
    kind: str,
    allowed_preference_side_kinds: frozenset[str] | None = None,
) -> list[tuple[str, Mapping[str, Any]]]:
    if kind == "thalamic":
        return [("/", record)]
    if kind == "preference":
        return _preference_owner_specs(record, allowed_preference_side_kinds)
    if kind == "bridge_pair":
        return _bridge_owner_specs(record)
    return []


def _owner_state_claims(owner: Mapping[str, Any]) -> bool:
    state = owner.get("state")
    if not isinstance(state, Mapping):
        return False
    if "sim_or_real" in state:
        return True
    return "provenance" in state


def payload_has_state_claim(
    record: Mapping[str, Any], owners: list[tuple[str, Mapping[str, Any]]]
) -> bool:
    candidates = owners if owners else [("/", record)]
    return any(_owner_state_claims(owner) for _path, owner in candidates)


if __package__:
    _expose_package_sibling(__name__)
