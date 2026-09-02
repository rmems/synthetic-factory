#!/usr/bin/env python3
"""Identity and bridge stages for curated record composition."""

from __future__ import annotations

import copy
import sys
from typing import Any, Mapping

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("compose_curated_identity")
    from . import compose_curated_calibration_lookup as _calibration_lookup
    from . import compose_curated_identity_deferral as _deferral
    from . import compose_curated_identity_repairs as _repairs
    from . import curate_bridge, curate_identity
    from .compose_contract import (
        ACTION_EXCLUDED,
        ACTION_NOT_APPLICABLE,
        ACTION_RETAINED,
        ComposeDecision,
        REASON_MIXED_PREFERENCE_FAMILIES,
    )
    from .compose_curated_context import SourceCoordinates, StageDefinition, stage
    from .compose_trajectory import (
        _is_same_state_pair,
        _mixed_preference_families,
        is_bridge_record,
        is_preference_record,
    )
    from .record_kind import preference_side_kinds
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "compose_curated_identity"
    )
    import compose_curated_calibration_lookup as _calibration_lookup
    import compose_curated_identity_deferral as _deferral
    import compose_curated_identity_repairs as _repairs
    import curate_bridge
    import curate_identity
    from compose_contract import (
        ACTION_EXCLUDED,
        ACTION_NOT_APPLICABLE,
        ACTION_RETAINED,
        ComposeDecision,
        REASON_MIXED_PREFERENCE_FAMILIES,
    )
    from compose_curated_context import SourceCoordinates, StageDefinition, stage
    from compose_trajectory import (
        _is_same_state_pair,
        _mixed_preference_families,
        is_bridge_record,
        is_preference_record,
    )
    from record_kind import preference_side_kinds

# Calibration lookup by pre-identity identifiers, re-exported for importers.
_container_calibration_id_candidates = _calibration_lookup.container_calibration_id_candidates
_usable_calibration_id = _calibration_lookup.usable_calibration_id
_owner_calibration_id_candidates = _calibration_lookup.owner_calibration_id_candidates
_calibration_id_candidates = _calibration_lookup.calibration_id_candidates
calibration_for = _calibration_lookup.calibration_for

# Narrow-refusal classification and lane-repair probes, re-exported likewise.
REASON_IDENTITY_INVALID_PAYLOAD_SHAPE = _repairs.REASON_IDENTITY_INVALID_PAYLOAD_SHAPE
BRIDGE_ORDER_ERROR_FRAGMENT = _repairs.BRIDGE_ORDER_ERROR_FRAGMENT
CODING_STEP_ERROR_RE = _repairs.CODING_STEP_ERROR_RE
PREFERENCE_STEP_ERROR_RE = _repairs.PREFERENCE_STEP_ERROR_RE
PROBE_FAILED = _repairs.PROBE_FAILED
only_identity_shape_details = _repairs.only_identity_shape_details
_is_bridge_order_only_rejection = _repairs.is_bridge_order_only_rejection
_bridge_order_repaired_copy_with_source = _repairs.bridge_order_repaired_copy_with_source
_is_coding_step_only_rejection = _repairs.is_coding_step_only_rejection
_coding_steps_repaired_copy_with_source = _repairs.coding_steps_repaired_copy_with_source
_is_preference_step_only_rejection = _repairs.is_preference_step_only_rejection
_replace_coding_steps = _repairs.replace_coding_steps
_preference_steps_repaired_copy_with_source = _repairs.preference_steps_repaired_copy_with_source
_restore_deferred_payload = _repairs.restore_deferred_payload

# Deferred downstream-lane repair orchestration, re-exported likewise.
DeferredLaneRepair = _deferral.DeferredLaneRepair
_identity_retry_with_source = _deferral.identity_retry_with_source
_lane_retry = _deferral.lane_retry
_run_deferred_lane_repairs = _deferral.run_deferred_lane_repairs
_deferred_lane_repair_with_source = _deferral.deferred_lane_repair_with_source

__all__ = """
BRIDGE_ORDER_ERROR_FRAGMENT BRIDGE_STAGE CODING_STEP_ERROR_RE DeferredLaneRepair
IDENTITY_STAGE PREFERENCE_STEP_ERROR_RE PROBE_FAILED REASON_IDENTITY_INVALID_PAYLOAD_SHAPE
SourceCoordinates _PROBE_FAILED _bridge_order_repaired_copy_with_source
_calibration_id_candidates _coding_steps_repaired_copy_with_source
_compose_bridge_stage_with_source _compose_identity_stage_with_source
_container_calibration_id_candidates _deferred_lane_repair_with_source
_identity_retry_with_source _identity_stage_evidence _is_bridge_order_only_rejection
_is_coding_step_only_rejection _is_preference_step_only_rejection _lane_retry
_only_identity_shape_details _owner_calibration_id_candidates
_preference_steps_repaired_copy_with_source _replace_coding_steps
_restore_deferred_payload _run_deferred_lane_repairs _source_preference_shape
_usable_calibration_id calibration_for only_identity_shape_details
""".split()


IDENTITY_STAGE = StageDefinition(
    "identity", curate_identity.TRANSFORM_NAME, curate_identity.TRANSFORM_VERSION
)
BRIDGE_STAGE = StageDefinition(
    "bridge", curate_bridge.TRANSFORM_NAME, curate_bridge.TRANSFORM_VERSION
)


def _source_preference_shape(record: Any) -> tuple[Any, bool]:
    """Return side kinds and whether source sides mix record families."""

    if not (is_preference_record(record) and isinstance(record, Mapping)):
        return None, False
    side_kinds = preference_side_kinds(record)
    mixed = not _is_same_state_pair(record) and _mixed_preference_families(side_kinds)
    return side_kinds, mixed


def _identity_stage_evidence(
    identity_result: Any,
    deferred_lane: str | None,
    source_side_kinds: Any,
    mixed_preference_families: bool,
) -> tuple[list[str], dict[str, Any]]:
    """Assemble identity-stage reasons and detail."""

    identity_reasons = list(identity_result.mapping.get("reason_codes", []))
    identity_detail = copy.deepcopy(identity_result.mapping)
    if deferred_lane == "bridge":
        identity_detail["bridge_order_deferred_to_bridge_lane"] = True
    if deferred_lane == "coding":
        identity_detail["coding_steps_deferred_to_coding_lane"] = True
    if deferred_lane == "preferences":
        identity_detail["preference_steps_deferred_to_preferences_lane"] = True
    if source_side_kinds is not None:
        identity_detail["preference_side_kinds"] = list(source_side_kinds)
    if mixed_preference_families:
        identity_detail["identity_reason_codes"] = identity_reasons
        identity_reasons = [REASON_MIXED_PREFERENCE_FAMILIES]
    return identity_reasons, identity_detail


def _compose_identity_stage_with_source(
    record: Any,
    stages: list[dict[str, Any]],
    source: SourceCoordinates,
) -> "ComposeDecision | tuple[dict[str, Any], Any]":
    """Run identity, retaining explicit evidence for any deferred repair."""

    source_side_kinds, mixed_families = _source_preference_shape(record)
    result = curate_identity.curate_record(
        curate_identity.SourceRecord(
            record=record,
            source_path=source.path,
            source_line=source.line,
            source_sha256=source.sha256,
        )
    )
    result, deferred_lane = _deferred_lane_repair_with_source(record, result, source)
    reasons, detail = _identity_stage_evidence(
        result, deferred_lane, source_side_kinds, mixed_families
    )
    public_action = ACTION_RETAINED if result.action == "retained" else ACTION_EXCLUDED
    if mixed_families:
        public_action = ACTION_EXCLUDED
    stages.append(
        stage(
            IDENTITY_STAGE,
            public_action,
            reason_codes=reasons,
            lane_action=result.action,
            detail=detail,
        )
    )
    if public_action == ACTION_EXCLUDED or result.record is None:
        return ComposeDecision(ACTION_EXCLUDED, None, tuple(reasons), tuple(stages), None, None)
    current: dict[str, Any] = result.record
    _restore_deferred_payload(current, record, deferred_lane)
    return current, result.mapping.get("record_kind")


def _compose_bridge_stage_with_source(
    current: dict[str, Any],
    stages: list[dict[str, Any]],
    source: SourceCoordinates,
) -> "ComposeDecision | dict[str, Any]":
    """Run the bridge lane when the record belongs to it."""

    if not is_bridge_record(current):
        stages.append(
            stage(
                BRIDGE_STAGE,
                ACTION_NOT_APPLICABLE,
                lane_action=ACTION_NOT_APPLICABLE,
            )
        )
        return current
    decision = curate_bridge.curate_record(
        current,
        source_path=source.path,
        source_line=source.line,
        source_hash=source.sha256,
        source_file_hash=source.file_sha256,
    )
    reasons = list(decision.manifest.get("reason_codes", []))
    retained = decision.output_record is not None
    stages.append(
        stage(
            BRIDGE_STAGE,
            ACTION_RETAINED if retained else ACTION_EXCLUDED,
            reason_codes=reasons,
            lane_action=decision.action,
            detail=decision.manifest,
        )
    )
    if not retained:
        return ComposeDecision(ACTION_EXCLUDED, None, tuple(reasons), tuple(stages), None, None)
    return decision.output_record


# Historical private spellings, kept for direct importers and tests.
_PROBE_FAILED = PROBE_FAILED
_only_identity_shape_details = only_identity_shape_details


if __package__:
    _expose_package_sibling(__name__)
