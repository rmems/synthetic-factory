#!/usr/bin/env python3
"""Semantic normalisation and post-transform deduplication of curated records."""

from __future__ import annotations

import copy
import sys
from typing import TYPE_CHECKING, Any, Mapping

if TYPE_CHECKING:
    from compose_curated_source import SourceLineContext

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("compose_curated_source_semantics")
    from . import compose_contract as _compose_contract
    from . import curate_rewards
    from .compose_curated_context import StageDefinition, stage
    from .compose_curated_source_pointers import (
        _identity_owner,
        _mapped_legacy_id_paths,
        _pop_json_pointer,
    )
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "compose_curated_source_semantics"
    )
    import compose_contract as _compose_contract
    import curate_rewards
    from compose_curated_context import StageDefinition, stage
    from compose_curated_source_pointers import (
        _identity_owner,
        _mapped_legacy_id_paths,
        _pop_json_pointer,
    )

ACTION_EXCLUDED = _compose_contract.ACTION_EXCLUDED
ACTION_RETAINED = _compose_contract.ACTION_RETAINED
ComposeDecision = _compose_contract.ComposeDecision
ComposeError = _compose_contract.ComposeError
REASON_DUPLICATE_CURATED_RECORD = _compose_contract.REASON_DUPLICATE_CURATED_RECORD

DEDUP_STAGE = StageDefinition(
    "post_transform_dedup", _compose_contract.COMPOSE_NAME, _compose_contract.COMPOSE_VERSION
)


def _semantic_identity_owners(record: dict[str, Any]) -> list[dict[str, Any]]:
    """Return every owner whose production labels are not training content."""

    owners = [record]
    for side in ("chosen", "rejected"):
        owner = record.get(side)
        if isinstance(owner, dict):
            owners.append(owner)
    view = record.get("language_view")
    trajectory = view.get("trajectory") if isinstance(view, Mapping) else None
    if isinstance(trajectory, dict):
        owners.append(trajectory)
    return owners


def _identity_stage_detail_of(decision: ComposeDecision) -> dict[str, Any] | None:
    """Return the recorded identity-stage detail mapping."""

    identity_stage = next(
        (item for item in decision.stages if item.get("lane") == "identity"), None
    )
    detail = identity_stage.get("detail") if isinstance(identity_stage, dict) else None
    return detail if isinstance(detail, dict) else None


def _strip_assigned_ids(semantic: dict[str, Any], detail: dict[str, Any] | None) -> None:
    """Drop coordinate-derived identifiers assigned by identity curation."""

    mappings = detail.get("id_mappings") if isinstance(detail, dict) else None
    for mapping in mappings if isinstance(mappings, list) else ():
        if not isinstance(mapping, dict):
            continue
        owner = _identity_owner(semantic, mapping.get("owner_path"))
        if owner is not None and owner.get("id") == mapping.get("output_id"):
            owner.pop("id", None)
    for path in _mapped_legacy_id_paths(detail):
        _pop_json_pointer(semantic, path)


def _strip_provenance_labels(semantic: dict[str, Any]) -> None:
    """Drop pipeline provenance labels from every semantic identity owner."""

    labels = ("factory", "generator", "generator_version", "run", "round")
    for owner in _semantic_identity_owners(semantic):
        meta = owner.get("meta")
        if not isinstance(meta, dict):
            continue
        for label in labels:
            meta.pop(label, None)


def _strip_sidecar_binding(semantic: dict[str, Any]) -> None:
    """Drop source-coordinate bindings while retaining reward semantics."""

    annotation = semantic.get(curate_rewards.ANNOTATION_FIELD)
    if not isinstance(annotation, dict):
        return
    annotation.pop("source_sidecar_id", None)
    magnitude = annotation.get("magnitude")
    values = magnitude.get("values") if isinstance(magnitude, dict) else None
    for value in values if isinstance(values, list) else ():
        if isinstance(value, dict):
            value.pop("calibration_source", None)


def _post_transform_semantic_sha256(
    decision: ComposeDecision, context: SourceLineContext
) -> str:
    """Hash training content without coordinate-derived bindings."""

    if decision.record is None:
        raise ComposeError("cannot hash a missing curated record")
    semantic = copy.deepcopy(decision.record)
    _strip_assigned_ids(semantic, _identity_stage_detail_of(decision))
    _strip_provenance_labels(semantic)
    _strip_sidecar_binding(semantic)
    return context.canonical_sha256(semantic)


def _is_retained_record(decision: ComposeDecision) -> bool:
    """Whether a decision carries a record eligible for semantic indexing."""

    return decision.action == ACTION_RETAINED and decision.record is not None


def _deduplicate_curated_record(
    decision: ComposeDecision, context: SourceLineContext
) -> ComposeDecision:
    """Exclude records that converge only after lossy curation lanes."""

    seen = context.seen_curated_semantics
    if seen is None or not _is_retained_record(decision):
        return decision
    semantic_sha256 = _post_transform_semantic_sha256(decision, context)
    first = seen.get(semantic_sha256)
    if first is None:
        seen[semantic_sha256] = (context.source_path, context.source_line)
        return decision
    duplicate = stage(
        DEDUP_STAGE,
        ACTION_EXCLUDED,
        reason_codes=[REASON_DUPLICATE_CURATED_RECORD],
        semantic_sha256=semantic_sha256,
        first_source_path=first[0],
        first_source_line=first[1],
    )
    return ComposeDecision(
        ACTION_EXCLUDED,
        None,
        (REASON_DUPLICATE_CURATED_RECORD,),
        (*decision.stages, duplicate),
        None,
        None,
    )


if __package__:
    _expose_package_sibling(__name__)
