#!/usr/bin/env python3
"""Ordered non-procedural identity curation stages.

The facade supplies a fresh dependency bundle for every record.  This keeps
its documented patch and instrumentation seams live while the ordered stage
logic has a focused module boundary.
"""

from __future__ import annotations

import copy
import sys
from dataclasses import dataclass
from typing import Any, Callable, Collection, Mapping

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("curate_identity_stages")
else:
    def _ignore_package_sibling(_name):
        return None


    getattr(
        sys.modules.get("pipelines"),
        "_join_package_sibling",
        _ignore_package_sibling,
    )("curate_identity_stages")


@dataclass(frozen=True)
class CurationContext:
    """Authority and identity inputs shared by non-procedural stages."""

    original: Any
    source: Any
    row: Any
    kind: str
    contract: str | None
    root_original_ids: list[dict[str, Any]]
    mapping: dict[str, Any]


@dataclass(frozen=True)
class CurationDependencies:
    """Live facade operations needed by the ordered curation stages."""

    allowed_contracts: Collection[str]
    apply_resolved_state: Callable[..., Any]
    apply_shape_designed: Callable[..., Any]
    canonical_id: Callable[..., str]
    collect_state_resolutions: Callable[..., Any]
    curation_result: Callable[..., Any]
    exclude: Callable[..., Any]
    identity_curation_error: type[Exception]
    owner_specs: Callable[..., Any]
    payload_factory: Callable[..., str | None]
    payload_has_state_claim: Callable[..., bool]
    require_state_contract: str
    residual_real_claim_paths: Callable[..., list[str]]
    sha256_json: Callable[[Any], str]
    shape_basis: Mapping[str, str]
    shape_validation_errors: Callable[..., list[Any]]
    training_ready_true_paths: Callable[..., list[str]]


def _identity_route_exclusion(context, dependencies):
    """Return the first route/policy rejection, preserving gate order."""

    payload_factory = dependencies.payload_factory(context.original)
    if payload_factory != context.row.payload_factory:
        rejection = dependencies.exclude(
            context.mapping,
            "identity.factory_path_payload_mismatch",
            details=[
                {
                    "path_id": context.row.path_id,
                    "expected_payload_factory": context.row.payload_factory,
                    "payload_factory": payload_factory,
                }
            ],
        )
    elif context.kind not in context.row.record_kinds:
        rejection = dependencies.exclude(
            context.mapping,
            "identity.factory_not_authorized_for_kind",
            details=[
                {
                    "record_kind": context.kind,
                    "authorized_kinds": sorted(context.row.record_kinds),
                }
            ],
        )
    elif not context.row.identity_authoritative:
        rejection = dependencies.exclude(
            context.mapping,
            "identity.factory_not_identity_authoritative",
        )
    elif context.contract not in dependencies.allowed_contracts:
        rejection = dependencies.exclude(
            context.mapping,
            "identity.factory_contract_invalid",
            details=[
                {
                    "record_kind": context.kind,
                    "provenance_contract": context.contract,
                }
            ],
        )
    else:
        rejection = _identity_readiness_exclusion(context, dependencies)
    return rejection


def _identity_readiness_exclusion(context, dependencies):
    """Reject a readiness claim forbidden by an otherwise authorized route."""

    if context.row.training_ready_policy == "never":
        ready_claims = dependencies.training_ready_true_paths(context.original)
        if ready_claims:
            return dependencies.exclude(
                context.mapping,
                "identity.training_ready_policy_violation",
                details=[{"paths": ready_claims, "policy": "never"}],
            )
    return None


def _identity_owner_specs(context, dependencies):
    """Resolve nested identity owners or return their shape rejection."""

    try:
        owner_specs = dependencies.owner_specs(
            context.original,
            context.kind,
            context.row.preference_side_kinds if context.kind == "preference" else None,
        )
    except dependencies.identity_curation_error as exc:
        return None, dependencies.exclude(
            context.mapping,
            "identity.invalid_nested_shape",
            details=[str(exc)],
        )
    shape_errors = dependencies.shape_validation_errors(
        context.original,
        context.kind,
        owner_specs,
    )
    rejection = None
    if shape_errors:
        rejection = dependencies.exclude(
            context.mapping,
            "identity.invalid_payload_shape",
            details=shape_errors,
        )
    return owner_specs, rejection


def _identity_provenance_plan(context, owner_specs, dependencies):
    """Resolve state evidence or the shape-designed application plan."""

    use_state = (
        context.contract == dependencies.require_state_contract
        or dependencies.payload_has_state_claim(context.original, owner_specs)
    )
    state_owners = owner_specs if owner_specs else [("/", context.original)]
    if use_state:
        resolutions, unresolved = dependencies.collect_state_resolutions(state_owners)
        if unresolved:
            return None, dependencies.exclude(
                context.mapping,
                "identity.unresolved_provenance",
                unresolved_provenance=unresolved,
            )
        plan = (True, owner_specs, state_owners, resolutions)
    elif context.kind not in dependencies.shape_basis:
        return None, dependencies.exclude(
            context.mapping,
            "identity.factory_contract_invalid",
            details=[
                {
                    "record_kind": context.kind,
                    "provenance_contract": context.contract,
                }
            ],
        )
    else:
        plan = (False, owner_specs, owner_specs, [])
    return plan, None


def _materialize_identity_record(context, plan, dependencies):
    """Apply a validated provenance plan and seal the retained mapping."""

    use_state, owner_specs, apply_owners, resolutions = plan
    curated = copy.deepcopy(dict(context.original))
    output_id = dependencies.canonical_id(context.source, context.kind, "/")
    curated["id"] = output_id
    if use_state:
        id_mappings, provenance_mappings = dependencies.apply_resolved_state(
            curated,
            context.original,
            context.source,
            context.kind,
            owner_specs,
            apply_owners,
            resolutions,
            output_id,
            context.root_original_ids,
        )
    else:
        id_mappings, provenance_mappings = dependencies.apply_shape_designed(
            curated,
            context.original,
            context.source,
            context.kind,
            apply_owners,
            output_id,
            context.root_original_ids,
        )
    residual_real_claims = dependencies.residual_real_claim_paths(curated)
    if residual_real_claims:
        return dependencies.exclude(
            context.mapping,
            "identity.unowned_real_claim",
            details=[{"paths": residual_real_claims}],
        )
    context.mapping.update(
        {
            "action": "retained",
            "reason_codes": ["identity.assigned", "provenance.canonicalized"],
            "output_id": output_id,
            "output_sha256": dependencies.sha256_json(curated),
            "id_mappings": id_mappings,
            "provenance_mappings": provenance_mappings,
        }
    )
    return dependencies.curation_result("retained", curated, context.mapping)


def curate_nonprocedural_record(context, dependencies):
    """Run authority, shape, evidence, and materialization stages in order."""

    rejection = _identity_route_exclusion(context, dependencies)
    if rejection is not None:
        return rejection
    owner_specs, rejection = _identity_owner_specs(context, dependencies)
    if rejection is not None:
        return rejection
    plan, rejection = _identity_provenance_plan(context, owner_specs, dependencies)
    if rejection is not None:
        return rejection
    return _materialize_identity_record(context, plan, dependencies)


if __package__:
    _expose_package_sibling(__name__)
