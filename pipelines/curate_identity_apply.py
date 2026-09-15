#!/usr/bin/env python3
"""Apply a validated provenance plan onto a curated identity record.

Split out of ``curate_identity.py`` (A11 of #211). The nine-argument
``_apply_resolved_state`` / seven-argument ``_apply_shape_designed`` seams stay
on the facade so ``CurationDependencies`` and the identity tests keep patching
and calling the historical names. This module takes those arguments as
parameter objects and stamps canonical provenance without changing mapping
order or error strings.
"""

from __future__ import annotations

import copy
import sys
from collections.abc import Callable, Mapping
from typing import Any, NamedTuple

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("curate_identity_apply")
    from .curate_identity_json import sha256_json
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "curate_identity_apply"
    )
    from curate_identity_json import sha256_json


class ResolvedStatePlan(NamedTuple):
    """The curated object plus the state resolutions that stamp it."""

    curated: dict[str, Any]
    original: Mapping[str, Any]
    source: Any
    kind: str
    native_owner_specs: list[tuple[str, Mapping[str, Any]]]
    resolve_owners: list[tuple[str, Mapping[str, Any]]]
    resolutions: list[dict[str, Any]]
    output_id: str
    root_original_ids: list[dict[str, Any]]


class ShapeDesignedPlan(NamedTuple):
    """The curated object plus the owners that receive the designed contract."""

    curated: dict[str, Any]
    original: Mapping[str, Any]
    source: Any
    kind: str
    owner_specs: list[tuple[str, Mapping[str, Any]]]
    output_id: str
    root_original_ids: list[dict[str, Any]]


class ApplyIds(NamedTuple):
    """Live identity helpers the apply step reads from the facade."""

    owner_specs: Callable[..., Any]
    canonical_id: Callable[..., str]
    legacy_ids: Callable[..., list[dict[str, Any]]]
    canonical_json_equal: Callable[..., bool]
    error_type: type[Exception]
    shape_basis: Mapping[str, str]


def provenance_mapping_sha256(mapping: Mapping[str, Any]) -> str:
    payload = dict(mapping)
    payload.pop("mapping_sha256", None)
    return sha256_json(payload)


def seal_provenance_mapping(mapping: Mapping[str, Any]) -> dict[str, Any]:
    sealed = copy.deepcopy(dict(mapping))
    sealed["mapping_sha256"] = provenance_mapping_sha256(sealed)
    return sealed


def _owner_provenance_original(owner: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "owner_provenance": {
            "present": "provenance" in owner,
            "value": copy.deepcopy(owner.get("provenance")),
        }
    }


def assign_nested_ids(
    curated: dict[str, Any],
    original: Mapping[str, Any],
    source: Any,
    kind: str,
    owner_specs: list[tuple[str, Mapping[str, Any]]],
    output_id: str,
    root_original_ids: list[dict[str, Any]],
    ids: ApplyIds,
) -> list[dict[str, Any]]:
    id_mappings: list[dict[str, Any]] = [
        {
            "owner_path": "/",
            "original_ids": root_original_ids,
            "output_id": output_id,
        }
    ]
    curated_owners = dict(ids.owner_specs(curated, kind)) if owner_specs else {}
    for owner_path, _owner in owner_specs:
        if owner_path == "/":
            continue
        nested_id = ids.canonical_id(source, kind, owner_path)
        curated_owners[owner_path]["id"] = nested_id
        original_owner = dict(ids.owner_specs(original, kind))[owner_path]
        id_mappings.append(
            {
                "owner_path": owner_path,
                "original_ids": ids.legacy_ids(original_owner, owner_path),
                "output_id": nested_id,
            }
        )
    return id_mappings


def curated_resolve_owners(
    curated: dict[str, Any],
    kind: str,
    resolve_owners: list[tuple[str, Mapping[str, Any]]],
    ids: ApplyIds,
) -> list[tuple[str, Mapping[str, Any]]]:
    specs = ids.owner_specs(curated, kind)
    if specs:
        return specs
    if resolve_owners:
        return [("/", curated)]
    return []


def _stamp_resolved_owner(
    owner: Mapping[str, Any],
    resolution: Mapping[str, Any],
    error_type: type[Exception],
) -> dict[str, Any]:
    canonical_provenance = {
        "kind": resolution["kind"],
        "claimed": copy.deepcopy(resolution["claimed"]),
    }
    if canonical_provenance["kind"] == "real":
        raise error_type("identity must never emit provenance.kind=real")
    owner["state"]["sim_or_real"] = resolution["kind"]
    owner["state"]["provenance"] = copy.deepcopy(canonical_provenance)
    owner["provenance"] = copy.deepcopy(canonical_provenance)
    return canonical_provenance


def _sealed_state_mapping(
    owner_path: str,
    resolution: Mapping[str, Any],
    canonical_provenance: Mapping[str, Any],
) -> dict[str, Any]:
    return seal_provenance_mapping(
        {
            "owner_path": owner_path,
            "state_path": resolution["state_path"],
            "basis": resolution["basis"],
            "original": resolution["original"],
            "canonical": copy.deepcopy(canonical_provenance),
        }
    )


def _nested_wrapper_kind(
    canonical_provenances: list[dict[str, Any]],
    equal: Callable[..., bool],
) -> tuple[str, Any]:
    kinds = {item["kind"] for item in canonical_provenances}
    if len(kinds) != 1:
        return "unknown", [item["claimed"] for item in canonical_provenances]
    wrapper_kind = next(iter(kinds))
    claims = [item["claimed"] for item in canonical_provenances]
    if all(equal(item, claims[0]) for item in claims):
        return wrapper_kind, claims[0]
    return wrapper_kind, claims


def _append_nested_wrapper_mapping(
    curated: dict[str, Any],
    original: Mapping[str, Any],
    canonical_provenances: list[dict[str, Any]],
    provenance_mappings: list[dict[str, Any]],
    equal: Callable[..., bool],
) -> None:
    wrapper_kind, wrapper_claimed = _nested_wrapper_kind(canonical_provenances, equal)
    curated["provenance"] = {
        "kind": wrapper_kind,
        "claimed": copy.deepcopy(wrapper_claimed),
    }
    provenance_mappings.append(
        seal_provenance_mapping(
            {
                "owner_path": "/",
                "basis": "nested_trajectory_aggregate",
                "original": _owner_provenance_original(original),
                "canonical": copy.deepcopy(curated["provenance"]),
            }
        )
    )


def _append_root_resolution_mapping(
    curated: dict[str, Any],
    original: Mapping[str, Any],
    resolutions: list[dict[str, Any]],
    provenance_mappings: list[dict[str, Any]],
) -> None:
    root = {
        "kind": resolutions[0]["kind"],
        "claimed": copy.deepcopy(resolutions[0]["claimed"]),
        "basis": resolutions[0]["basis"],
    }
    curated["provenance"] = root
    provenance_mappings.append(
        seal_provenance_mapping(
            {
                "owner_path": "/",
                "basis": resolutions[0]["basis"],
                "original": _owner_provenance_original(original),
                "canonical": copy.deepcopy(root),
            }
        )
    )


def apply_resolved_state(plan: ResolvedStatePlan, ids: ApplyIds):
    """Stamp canonical state provenance onto ``plan.curated``."""

    id_mappings = assign_nested_ids(
        plan.curated,
        plan.original,
        plan.source,
        plan.kind,
        plan.native_owner_specs,
        plan.output_id,
        plan.root_original_ids,
        ids,
    )
    curated_owners = curated_resolve_owners(
        plan.curated, plan.kind, plan.resolve_owners, ids
    )
    provenance_mappings: list[dict[str, Any]] = []
    canonical_provenances: list[dict[str, Any]] = []
    for resolution, (owner_path, owner) in zip(
        plan.resolutions, curated_owners, strict=True
    ):
        canonical_provenance = _stamp_resolved_owner(owner, resolution, ids.error_type)
        canonical_provenances.append(canonical_provenance)
        provenance_mappings.append(
            _sealed_state_mapping(owner_path, resolution, canonical_provenance)
        )

    if plan.kind in {"preference", "bridge_pair"}:
        _append_nested_wrapper_mapping(
            plan.curated,
            plan.original,
            canonical_provenances,
            provenance_mappings,
            ids.canonical_json_equal,
        )
    elif plan.kind in {"episode", "safety_case", "multi_agent"} and plan.resolutions:
        _append_root_resolution_mapping(
            plan.curated, plan.original, plan.resolutions, provenance_mappings
        )
    return id_mappings, provenance_mappings


def _designed_provenance(kind: str, ids: ApplyIds) -> dict[str, Any]:
    return {"kind": "designed", "claimed": None, "basis": ids.shape_basis[kind]}


def _append_designed_owner_mappings(
    plan: ShapeDesignedPlan,
    provenance_mappings: list[dict[str, Any]],
    ids: ApplyIds,
) -> None:
    original_owners = dict(ids.owner_specs(plan.original, plan.kind))
    for owner_path, owner in ids.owner_specs(plan.curated, plan.kind):
        nested_designed = _designed_provenance(plan.kind, ids)
        owner["provenance"] = copy.deepcopy(nested_designed)
        original_owner = original_owners[owner_path]
        provenance_mappings.append(
            seal_provenance_mapping(
                {
                    "owner_path": owner_path,
                    "basis": nested_designed["basis"],
                    "original": _owner_provenance_original(original_owner),
                    "canonical": copy.deepcopy(nested_designed),
                }
            )
        )


def apply_shape_designed(plan: ShapeDesignedPlan, ids: ApplyIds):
    """Stamp the synthetic-shape-implies-designed contract onto ``plan.curated``."""

    designed = _designed_provenance(plan.kind, ids)
    plan.curated["provenance"] = copy.deepcopy(designed)
    id_mappings = assign_nested_ids(
        plan.curated,
        plan.original,
        plan.source,
        plan.kind,
        plan.owner_specs,
        plan.output_id,
        plan.root_original_ids,
        ids,
    )
    provenance_mappings = [
        seal_provenance_mapping(
            {
                "owner_path": "/",
                "basis": designed["basis"],
                "original": _owner_provenance_original(plan.original),
                "canonical": copy.deepcopy(designed),
            }
        )
    ]
    if plan.owner_specs:
        _append_designed_owner_mappings(plan, provenance_mappings, ids)
    return id_mappings, provenance_mappings


if __package__:
    _expose_package_sibling(__name__)
