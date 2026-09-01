#!/usr/bin/env python3
"""Identity and bridge stages for curated record composition."""

from __future__ import annotations

import contextlib
import copy
import re
import sys
from dataclasses import dataclass
from typing import Any, Callable, Mapping

if __package__:
    from . import _expose_package_sibling, _local_sibling_module, _require_local_sibling

    if _local_sibling_module("compose_curated_identity", allow_initializing=True):
        import compose_curated_identity as _direct_compose_curated_identity

        _require_local_sibling(
            _direct_compose_curated_identity,
            "compose_curated_identity",
        )
        del _direct_compose_curated_identity
    from . import curate_bridge, curate_coding, curate_identity, curate_rewards
    from .compose_contract import (
        ACTION_EXCLUDED,
        ACTION_NOT_APPLICABLE,
        ACTION_RETAINED,
        ComposeDecision,
        REASON_MIXED_PREFERENCE_FAMILIES,
    )
    from .compose_curated_context import SourceCoordinates, StageDefinition, stage
    from .compose_trajectory import (
        _curate_trajectory_sides,
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
    import curate_bridge
    import curate_coding
    import curate_identity
    import curate_rewards
    from compose_contract import (
        ACTION_EXCLUDED,
        ACTION_NOT_APPLICABLE,
        ACTION_RETAINED,
        ComposeDecision,
        REASON_MIXED_PREFERENCE_FAMILIES,
    )
    from compose_curated_context import SourceCoordinates, StageDefinition, stage
    from compose_trajectory import (
        _curate_trajectory_sides,
        _is_same_state_pair,
        _mixed_preference_families,
        is_bridge_record,
        is_preference_record,
    )
    from record_kind import preference_side_kinds


IDENTITY_STAGE = StageDefinition(
    "identity", curate_identity.TRANSFORM_NAME, curate_identity.TRANSFORM_VERSION
)
BRIDGE_STAGE = StageDefinition(
    "bridge", curate_bridge.TRANSFORM_NAME, curate_bridge.TRANSFORM_VERSION
)
REASON_IDENTITY_INVALID_PAYLOAD_SHAPE = "identity.invalid_payload_shape"
BRIDGE_ORDER_ERROR_FRAGMENT = "spike_events not globally non-decreasing"
CODING_STEP_ERROR_RE = re.compile(r"^record step \d+: ")
PREFERENCE_STEP_ERROR_RE = re.compile(r"^record/(?:chosen|rejected) step \d+: ")
_PROBE_FAILED: Any = object()


@dataclass(frozen=True)
class DeferredLaneRepair:
    """One downstream lane that may repair an identity-only refusal."""

    lane: str
    applies: bool
    repair: Callable[[Mapping[str, Any]], dict[str, Any] | None]


def _container_calibration_id_candidates(container: Mapping[str, Any]):
    """Yield usable legacy IDs from one identity container."""

    values = map(container.get, curate_identity.LEGACY_ID_KEYS)
    yield from filter(None, map(_usable_calibration_id, values))


def _usable_calibration_id(value: Any) -> str | None:
    """Normalize one legacy identifier without nesting generator branches."""

    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _owner_calibration_id_candidates(owner: Mapping[str, Any]):
    """Yield legacy IDs from one identity owner and its nested containers."""

    for container in (owner, owner.get("meta"), owner.get("state")):
        if isinstance(container, Mapping):
            yield from _container_calibration_id_candidates(container)


def _calibration_id_candidates(record: Mapping[str, Any]):
    """Yield source identifiers using the identity lane's vocabulary/order."""

    yield from _owner_calibration_id_candidates(record)
    for side in ("chosen", "rejected"):
        owner = record.get(side)
        if isinstance(owner, Mapping):
            yield from _owner_calibration_id_candidates(owner)


def calibration_for(record: Mapping[str, Any], catalog: Mapping[str, Any] | None) -> Any:
    """Look up calibration by pre-identity source identifiers."""

    if not catalog or not isinstance(record, Mapping):
        return None
    for candidate in _calibration_id_candidates(record):
        calibration = catalog.get(curate_rewards.catalog_record_key(candidate))
        if calibration is not None:
            return calibration
    return None


def _only_identity_shape_details(mapping: Mapping[str, Any], matches) -> bool:
    """Whether identity's only diagnostics all match one lane-owned defect."""

    if list(mapping.get("reason_codes", [])) != [
        REASON_IDENTITY_INVALID_PAYLOAD_SHAPE
    ]:
        return False
    details = mapping.get("details")
    if not isinstance(details, list) or not details:
        return False
    return all(isinstance(detail, str) and matches(detail) for detail in details)


def _is_bridge_order_only_rejection(mapping: Mapping[str, Any]) -> bool:
    """Whether identity refused a record for spike ordering and nothing else."""

    return _only_identity_shape_details(
        mapping, lambda detail: BRIDGE_ORDER_ERROR_FRAGMENT in detail
    )


def _bridge_order_repaired_copy_with_source(
    record: Mapping[str, Any], source: SourceCoordinates
) -> dict[str, Any] | None:
    """Return the bridge lane's stable-sorted copy when it can repair."""

    decision: Any = _PROBE_FAILED
    with contextlib.suppress(Exception):
        decision = curate_bridge.curate_record(
            record,
            source_path=source.path,
            source_line=source.line,
            source_hash=source.sha256,
            source_file_hash=None,
        )
    if decision is _PROBE_FAILED:
        return None
    if decision.action != "repair" or not isinstance(decision.output_record, dict):
        return None
    return decision.output_record


def _is_coding_step_only_rejection(mapping: Mapping[str, Any]) -> bool:
    """Whether identity refused an episode for step shape and nothing else."""

    return _only_identity_shape_details(
        mapping, lambda detail: CODING_STEP_ERROR_RE.match(detail) is not None
    )


def _coding_steps_repaired_copy_with_source(
    record: Mapping[str, Any], source: SourceCoordinates
) -> dict[str, Any] | None:
    """Return the coding lane's repaired copy when it can retain the episode."""

    curated: Any = _PROBE_FAILED
    with contextlib.suppress(Exception):
        curated, _manifest = curate_coding.curate_episode(
            copy.deepcopy(dict(record)),
            source_path=source.path,
            source_line=source.line,
            source_hash=source.sha256,
        )
    if curated is _PROBE_FAILED:
        return None
    return curated if isinstance(curated, dict) else None


def _is_preference_step_only_rejection(mapping: Mapping[str, Any]) -> bool:
    """Whether identity refused only coding-owned preference-side steps."""

    return _only_identity_shape_details(
        mapping, lambda detail: PREFERENCE_STEP_ERROR_RE.match(detail) is not None
    )


def _replace_coding_steps(
    target: dict[str, Any], curated: Mapping[str, Any]
) -> bool:
    """Copy only a coding lane's repaired step array into ``target``."""

    steps_path = curate_coding.steps_path(dict(curated))
    if steps_path == "steps":
        target["steps"] = copy.deepcopy(curated["steps"])
        return True
    if steps_path == "executed_action.steps":
        target_action = target.get("executed_action")
        curated_action = curated.get("executed_action")
        if not isinstance(target_action, dict) or not isinstance(curated_action, Mapping):
            return False
        target_action["steps"] = copy.deepcopy(curated_action["steps"])
        return True
    return False


def _preference_steps_repaired_copy_with_source(
    record: Mapping[str, Any], source: SourceCoordinates
) -> dict[str, Any] | None:
    """Probe the canonical side repair without leaking unrelated changes."""

    curated, _manifests, _reasons, _changed = _curate_trajectory_sides(
        dict(record),
        source_path=source.path,
        source_line=source.line,
    )
    if not isinstance(curated, Mapping):
        return None
    repaired = copy.deepcopy(dict(record))
    for side_name in ("chosen", "rejected"):
        target = repaired.get(side_name)
        curated_side = curated.get(side_name)
        if not isinstance(curated_side, Mapping) or not isinstance(target, dict):
            return None
        if not _replace_coding_steps(target, curated_side):
            return None
    return repaired


def _source_preference_shape(record: Any) -> tuple[Any, bool]:
    """Return side kinds and whether source sides mix record families."""

    if not (is_preference_record(record) and isinstance(record, Mapping)):
        return None, False
    side_kinds = preference_side_kinds(record)
    mixed = not _is_same_state_pair(record) and _mixed_preference_families(
        side_kinds
    )
    return side_kinds, mixed


def _identity_retry_with_source(
    repaired: dict[str, Any] | None, source: SourceCoordinates
):
    """Revalidate identity against a downstream lane's repaired copy."""

    if repaired is None:
        return None
    retry = curate_identity.curate_record(
        curate_identity.SourceRecord(
            record=repaired,
            source_path=source.path,
            source_line=source.line,
            source_sha256=source.sha256,
        )
    )
    if retry.action == "retained" and isinstance(retry.record, dict):
        return retry
    return None


def _lane_retry(
    applies: bool,
    repair,
    record: Mapping[str, Any],
    source: SourceCoordinates,
):
    """Try one owning lane's repair and identity revalidation."""

    if not applies:
        return None
    return _identity_retry_with_source(repair(record, source), source)


def _run_deferred_lane_repairs(
    record: Any,
    identity_result: Any,
    lanes: tuple[DeferredLaneRepair, ...],
    retry: Callable[[dict[str, Any] | None], Any],
) -> tuple[Any, str | None]:
    """Return the first identity-valid downstream repair, in lane order."""

    if identity_result.action == "retained" or not isinstance(record, Mapping):
        return identity_result, None
    for lane in lanes:
        if not lane.applies:
            continue
        repaired = retry(lane.repair(record))
        if repaired is not None:
            return repaired, lane.lane
    return identity_result, None


def _deferred_lane_repair_with_source(
    record: Any,
    identity_result: Any,
    source: SourceCoordinates,
) -> tuple[Any, str | None]:
    """Let the owning downstream lane repair a narrowly refused invariant."""

    if identity_result.action == "retained" or not isinstance(record, Mapping):
        return identity_result, None
    lanes = (
        DeferredLaneRepair(
            "bridge",
            is_bridge_record(record)
            and _is_bridge_order_only_rejection(identity_result.mapping),
            lambda current: _bridge_order_repaired_copy_with_source(current, source),
        ),
        DeferredLaneRepair(
            "coding",
            isinstance(record.get("steps"), list)
            and _is_coding_step_only_rejection(identity_result.mapping),
            lambda current: _coding_steps_repaired_copy_with_source(current, source),
        ),
        DeferredLaneRepair(
            "preferences",
            is_preference_record(record)
            and preference_side_kinds(record) == ("episode", "episode")
            and _is_preference_step_only_rejection(identity_result.mapping),
            lambda current: _preference_steps_repaired_copy_with_source(
                current, source
            ),
        ),
    )
    return _run_deferred_lane_repairs(
        record,
        identity_result,
        lanes,
        lambda repaired: _identity_retry_with_source(repaired, source),
    )


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


def _restore_deferred_payload(
    current: dict[str, Any], record: Mapping[str, Any], deferred_lane: str | None
) -> None:
    """Restore source-owned data so the downstream lane records its repair."""

    if deferred_lane == "bridge":
        current["spike_events"] = copy.deepcopy(record["spike_events"])
    if deferred_lane == "coding":
        current["steps"] = copy.deepcopy(record["steps"])
    if deferred_lane == "preferences":
        for side_name in ("chosen", "rejected"):
            source_side = record.get(side_name)
            current_side = current.get(side_name)
            if not isinstance(source_side, Mapping) or not isinstance(current_side, dict):
                continue
            _replace_coding_steps(current_side, source_side)


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
    public_action = (
        ACTION_RETAINED if result.action == "retained" else ACTION_EXCLUDED
    )
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
        return ComposeDecision(
            ACTION_EXCLUDED, None, tuple(reasons), tuple(stages), None, None
        )
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
        return ComposeDecision(
            ACTION_EXCLUDED, None, tuple(reasons), tuple(stages), None, None
        )
    return decision.output_record


if __package__:
    _expose_package_sibling(__name__)
