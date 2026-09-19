#!/usr/bin/env python3
"""Apply resolved provenance to the curated copy and build the mapping.

Split out of ``curate_identity.py`` (CodeScene: Lines of Code in a Single
File) by responsibility; every name is re-exported from ``curate_identity``
so existing ``curate_identity.X`` call sites and test seams resolve
unchanged.

Both apply routes share one ``ApplySpec``: the resolved-state route rewrites
each owner's state and provenance from collected resolutions, while the
shape-designed route stamps the contract's canonical designed provenance.
Owner IDs are always canonical preimages over the source coordinate.
"""

from __future__ import annotations

import copy
import sys
from dataclasses import dataclass
from typing import Any, Mapping

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("curate_identity_materialize")
    from . import (
        curate_identity_json as _identity_json,
        curate_identity_owners as _owners,
        curate_identity_provenance as _provenance,
        curate_identity_sources as _sources,
    )
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "curate_identity_materialize"
    )
    import curate_identity_json as _identity_json
    import curate_identity_owners as _owners
    import curate_identity_provenance as _provenance
    import curate_identity_sources as _sources

IdentityCurationError = _identity_json.IdentityCurationError
CurationResult = _sources.CurationResult

TRANSFORM_NAME = _sources.TRANSFORM_NAME
TRANSFORM_VERSION = _sources.TRANSFORM_VERSION

SHAPE_BASIS = {
    "episode": "synthetic_factory_episode_shape",
    "preference": "synthetic_factory_preference_shape",
    "safety_case": "synthetic_factory_safety_case_shape",
    "multi_agent": "synthetic_factory_multi_agent_shape",
    "oracle": "synthetic_factory_oracle_shape",
}


@dataclass(frozen=True)
class ApplySpec:
    """Curated-record materialization inputs shared by both apply routes."""

    original: Mapping[str, Any]
    source: Any
    kind: str
    owner_specs: list[tuple[str, Mapping[str, Any]]]
    output_id: str
    root_original_ids: list[dict[str, Any]]


@dataclass(frozen=True)
class MappingContext:
    """Authority and identity inputs for the base decision mapping."""

    source: Any
    kind: str
    root_original_ids: list[dict[str, Any]]
    registry: Any
    row: Any
    contract: str | None


def source_mapping(source) -> dict[str, Any]:
    return {
        "path": source.path,
        "line": source.line,
        "sha256": source.sha256,
        "hash_basis": source.hash_basis,
        "original": source.original,
    }


def base_mapping(context: MappingContext) -> dict[str, Any]:
    row = context.row
    return {
        "transform": {"name": TRANSFORM_NAME, "version": TRANSFORM_VERSION},
        "source": source_mapping(context.source),
        "factory": context.source.factory,
        "record_kind": context.kind,
        "original_ids": context.root_original_ids,
        "path_id": context.source.factory,
        "factory_id": None if row is None else row.payload_factory,
        "identity_authoritative": False if row is None else row.identity_authoritative,
        "provenance_contract": context.contract,
        "registry": {
            "schema_version": context.registry.schema_version,
            "sha256": context.registry.sha256,
        },
    }


def exclude(mapping: dict[str, Any], reason: str, **extra: Any) -> CurationResult:
    payload = {"action": "exclude", "reason_codes": [reason]}
    payload.update(extra)
    mapping.update(payload)
    return CurationResult("exclude", None, mapping)


def assign_nested_ids(curated: dict[str, Any], spec: ApplySpec) -> list[dict[str, Any]]:
    id_mappings: list[dict[str, Any]] = [
        {
            "owner_path": "/",
            "original_ids": spec.root_original_ids,
            "output_id": spec.output_id,
        }
    ]
    curated_owners = (
        dict(_owners.owner_specs(curated, spec.kind)) if spec.owner_specs else {}
    )
    for owner_path, _owner in spec.owner_specs:
        if owner_path == "/":
            continue
        nested_id = _sources.canonical_id(spec.source, spec.kind, owner_path)
        curated_owners[owner_path]["id"] = nested_id
        original_owner = dict(_owners.owner_specs(spec.original, spec.kind))[owner_path]
        id_mappings.append(
            {
                "owner_path": owner_path,
                "original_ids": _owners.legacy_ids(original_owner, owner_path),
                "output_id": nested_id,
            }
        )
    return id_mappings


def curated_resolve_owners(
    curated: dict[str, Any],
    kind: str,
    resolve_owners: list[tuple[str, Mapping[str, Any]]],
) -> list[tuple[str, Mapping[str, Any]]]:
    specs = _owners.owner_specs(curated, kind)
    if specs:
        return specs
    if resolve_owners:
        return [("/", curated)]
    return []


def _canonical_owner_provenance(resolution: Mapping[str, Any]) -> dict[str, Any]:
    canonical_provenance = {
        "kind": resolution["kind"],
        "claimed": copy.deepcopy(resolution["claimed"]),
    }
    if canonical_provenance["kind"] == "real":
        raise IdentityCurationError("identity must never emit provenance.kind=real")
    return canonical_provenance


def _apply_owner_resolutions(
    curated_owners: list[tuple[str, Mapping[str, Any]]],
    resolutions: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    provenance_mappings: list[dict[str, Any]] = []
    canonical_provenances: list[dict[str, Any]] = []
    for resolution, (owner_path, owner) in zip(
        resolutions, curated_owners, strict=True
    ):
        state = owner["state"]
        canonical_provenance = _canonical_owner_provenance(resolution)
        state["sim_or_real"] = resolution["kind"]
        state["provenance"] = copy.deepcopy(canonical_provenance)
        owner["provenance"] = copy.deepcopy(canonical_provenance)
        canonical_provenances.append(canonical_provenance)
        provenance_mappings.append(
            _provenance.seal_provenance_mapping(
                {
                    "owner_path": owner_path,
                    "state_path": resolution["state_path"],
                    "basis": resolution["basis"],
                    "original": resolution["original"],
                    "canonical": copy.deepcopy(canonical_provenance),
                }
            )
        )
    return provenance_mappings, canonical_provenances


def _owner_provenance_original(original: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "owner_provenance": {
            "present": "provenance" in original,
            "value": copy.deepcopy(original.get("provenance")),
        }
    }


def _aggregate_wrapper_provenance(
    canonical_provenances: list[dict[str, Any]],
) -> dict[str, Any]:
    kinds = {item["kind"] for item in canonical_provenances}
    claims = [item["claimed"] for item in canonical_provenances]
    if len(kinds) == 1:
        wrapper_kind = next(iter(kinds))
        wrapper_claimed = (
            claims[0]
            if all(_identity_json._canonical_json_equal(item, claims[0]) for item in claims)
            else claims
        )
    else:
        wrapper_kind = "unknown"
        wrapper_claimed = claims
    return {"kind": wrapper_kind, "claimed": copy.deepcopy(wrapper_claimed)}


def _aggregate_provenance_mapping(
    curated: dict[str, Any],
    spec: ApplySpec,
    canonical_provenances: list[dict[str, Any]],
) -> dict[str, Any]:
    curated["provenance"] = _aggregate_wrapper_provenance(canonical_provenances)
    return _provenance.seal_provenance_mapping(
        {
            "owner_path": "/",
            "basis": "nested_trajectory_aggregate",
            "original": _owner_provenance_original(spec.original),
            "canonical": copy.deepcopy(curated["provenance"]),
        }
    )


def _root_provenance_mapping(
    curated: dict[str, Any],
    spec: ApplySpec,
    resolution: Mapping[str, Any],
) -> dict[str, Any]:
    root = {
        "kind": resolution["kind"],
        "claimed": copy.deepcopy(resolution["claimed"]),
        "basis": resolution["basis"],
    }
    curated["provenance"] = root
    return _provenance.seal_provenance_mapping(
        {
            "owner_path": "/",
            "basis": resolution["basis"],
            "original": _owner_provenance_original(spec.original),
            "canonical": copy.deepcopy(root),
        }
    )


def apply_resolved_state(
    curated: dict[str, Any],
    spec: ApplySpec,
    resolve_owners: list[tuple[str, Mapping[str, Any]]],
    resolutions: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    id_mappings = assign_nested_ids(curated, spec)
    curated_owners = curated_resolve_owners(curated, spec.kind, resolve_owners)
    provenance_mappings, canonical_provenances = _apply_owner_resolutions(
        curated_owners, resolutions
    )
    if spec.kind in {"preference", "bridge_pair"}:
        provenance_mappings.append(
            _aggregate_provenance_mapping(curated, spec, canonical_provenances)
        )
    elif spec.kind in {"episode", "safety_case", "multi_agent"} and resolutions:
        provenance_mappings.append(
            _root_provenance_mapping(curated, spec, resolutions[0])
        )
    return id_mappings, provenance_mappings


def _designed_owner_mappings(
    curated: dict[str, Any], spec: ApplySpec, basis: str
) -> list[dict[str, Any]]:
    original_owners = dict(_owners.owner_specs(spec.original, spec.kind))
    provenance_mappings: list[dict[str, Any]] = []
    for owner_path, owner in _owners.owner_specs(curated, spec.kind):
        nested_designed = {"kind": "designed", "claimed": None, "basis": basis}
        owner["provenance"] = copy.deepcopy(nested_designed)
        original_owner = original_owners[owner_path]
        provenance_mappings.append(
            _provenance.seal_provenance_mapping(
                {
                    "owner_path": owner_path,
                    "basis": basis,
                    "original": _owner_provenance_original(original_owner),
                    "canonical": copy.deepcopy(nested_designed),
                }
            )
        )
    return provenance_mappings


def apply_shape_designed(
    curated: dict[str, Any], spec: ApplySpec
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    basis = SHAPE_BASIS[spec.kind]
    designed = {"kind": "designed", "claimed": None, "basis": basis}
    curated["provenance"] = copy.deepcopy(designed)
    id_mappings = assign_nested_ids(curated, spec)
    provenance_mappings = [
        _provenance.seal_provenance_mapping(
            {
                "owner_path": "/",
                "basis": basis,
                "original": _owner_provenance_original(spec.original),
                "canonical": copy.deepcopy(designed),
            }
        )
    ]
    if spec.owner_specs:
        provenance_mappings.extend(_designed_owner_mappings(curated, spec, basis))
    return id_mappings, provenance_mappings


if __package__:
    _expose_package_sibling(__name__)
