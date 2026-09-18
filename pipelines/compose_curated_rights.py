#!/usr/bin/env python3
"""Bind identity rights envelopes onto retained compose-manifest entries.

Compose keeps LANE_ORDER unchanged. Research-only versus training is an
accounting lane on the identity mapping and the compose-manifest entry,
not a sixth transform. Tampered or missing envelopes fail the compose run.
"""

from __future__ import annotations

import sys
from typing import Any, Mapping

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("compose_curated_rights")
    from .compose_contract import ACTION_RETAINED, ComposeError
    from .curate_identity_registry import default_registry
    from .curate_identity_json import sha256_json
    from .curate_identity import _hash_verified_manifest_source
    from .compose_curated_context import SourceCoordinates
    from .compose_curated_identity import _compose_identity_stage_with_source
    from .rights_mapping import RightsPolicyError
    from .rights_record import (
        BoundRights,
        procedural_eligibility,
        ENVELOPE_FIELD,
        LANE_FIELD,
        LANE_RESEARCH,
        LANE_TRAINING,
        envelope_lane,
        identity_envelope,
        verify_bound_envelope,
    )
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "compose_curated_rights"
    )
    from compose_contract import ACTION_RETAINED, ComposeError
    from curate_identity_registry import default_registry
    from curate_identity_json import sha256_json
    from curate_identity import _hash_verified_manifest_source
    from compose_curated_context import SourceCoordinates
    from compose_curated_identity import _compose_identity_stage_with_source
    from rights_mapping import RightsPolicyError
    from rights_record import (
        BoundRights,
        procedural_eligibility,
        ENVELOPE_FIELD,
        LANE_FIELD,
        LANE_RESEARCH,
        LANE_TRAINING,
        envelope_lane,
        identity_envelope,
        verify_bound_envelope,
    )


def identity_mapping(decision: Any) -> dict[str, Any] | None:
    """Return the identity-stage detail mapping from one compose decision."""

    for stage in getattr(decision, "stages", ()) or ():
        if not isinstance(stage, Mapping) or stage.get("lane") != "identity":
            continue
        detail = stage.get("detail")
        if isinstance(detail, dict):
            return detail
    return None


def _registry_row(mapping: Mapping[str, Any], registry: Any):
    path_id = mapping.get("path_id") or mapping.get("factory")
    if not isinstance(path_id, str):
        return None
    return registry.by_path_id.get(path_id)


def _verified_envelope(mapping: Mapping, envelope: Mapping, physical_line: bytes) -> dict:
    registry = default_registry()
    row = _registry_row(mapping, registry)
    try:
        eligible, reasons = procedural_eligibility(mapping)
        return verify_bound_envelope(
            envelope,
            BoundRights(physical_line, registry.raw_bytes, row, eligible, reasons),
        )
    except RightsPolicyError as exc:
        raise ComposeError(str(exc)) from exc


def bind_retained_rights(
    state: Any,
    entry: dict[str, Any],
    decision: Any,
    physical_line: bytes,
) -> None:
    """Attach a verified rights envelope onto one retained compose-manifest entry."""

    if decision.action != ACTION_RETAINED or decision.record is None:
        return
    mapping = identity_mapping(decision)
    if mapping is None:
        raise ComposeError("retained record has no identity mapping for rights binding")
    envelope = identity_envelope(mapping)
    if envelope is None:
        raise ComposeError("retained record lacks a bound rights envelope")
    verified = _verified_envelope(mapping, envelope, physical_line)
    mapping["source"] = {**mapping["source"], "original": physical_line.decode("utf-8")}
    lane = envelope_lane(verified)
    entry[ENVELOPE_FIELD] = verified
    entry[LANE_FIELD] = lane
    state.rights_lanes[lane] += 1


def _verified_composed_source(mapping: Mapping):
    source_meta = mapping.get("source")
    if not isinstance(source_meta, Mapping):
        raise ValueError("composed identity lacks source bytes")
    return _hash_verified_manifest_source(source_meta, 0)


def _replayed_identity_stage(source) -> dict:
    stages = []
    _compose_identity_stage_with_source(
        source.record, stages,
        SourceCoordinates(source.source_path, source.source_line, source.source_sha256),
    )
    identity = stages[0]
    if identity["action"] != ACTION_RETAINED:
        raise ValueError("composed identity source does not replay to retention")
    expected = identity["detail"]
    expected["source"] = {**expected["source"], "original": source.source_json}
    return expected


def replay_composed_identity(mapping: Mapping[str, Any]) -> Mapping[str, Any]:
    """Reproduce identity plus compose's declared preference/deferred-repair evidence."""
    expected = _replayed_identity_stage(_verified_composed_source(mapping))
    if sha256_json(mapping) != sha256_json(expected):
        raise ValueError("composed identity proof does not match source replay")
    return expected[ENVELOPE_FIELD]


def rights_summary(state: Any) -> dict[str, Any]:
    """Return compose-summary accounting for research versus training lanes."""

    lanes = {
        LANE_RESEARCH: int(state.rights_lanes[LANE_RESEARCH]),
        LANE_TRAINING: int(state.rights_lanes[LANE_TRAINING]),
    }
    retained = int(state.counts["retained"])
    return {
        "lanes": lanes,
        "training_exportable": (
            retained > 0 and lanes[LANE_TRAINING] == retained and lanes[LANE_RESEARCH] == 0
        ),
    }


if __package__:
    _expose_package_sibling(__name__)
