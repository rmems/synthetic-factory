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
    from .rights_mapping import RightsPolicyError
    from .rights_record import (
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
    from rights_mapping import RightsPolicyError
    from rights_record import (
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


def _procedural_eligibility(mapping: Mapping[str, Any]) -> tuple[bool | None, list[str]]:
    authority = mapping.get("procedural_authority")
    if not isinstance(authority, Mapping):
        return None, []
    eligible = authority.get("eligible_training_candidate")
    raw_reasons = authority.get("ineligibility_reasons") or ()
    reasons = (
        [str(item) for item in raw_reasons] if isinstance(raw_reasons, (list, tuple)) else []
    )
    return (bool(eligible) if eligible is not None else None), reasons


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
    registry = default_registry()
    row = _registry_row(mapping, registry)
    eligible, reasons = _procedural_eligibility(mapping)
    try:
        verified = verify_bound_envelope(
            envelope,
            source_bytes=physical_line,
            factory_registry_bytes=registry.raw_bytes,
            expected_row=row,
            eligible=eligible,
            ineligibility_reasons=reasons,
        )
    except RightsPolicyError as exc:
        raise ComposeError(str(exc)) from exc
    lane = envelope_lane(verified)
    entry[ENVELOPE_FIELD] = verified
    entry[LANE_FIELD] = lane
    state.rights_lanes[lane] += 1


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
