#!/usr/bin/env python3
"""Identity and bridge stages for curated record composition."""

from __future__ import annotations

import contextlib
import copy
import re
import sys
from pathlib import Path
from typing import Any, Mapping

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

import curate_bridge  # noqa: E402
import curate_coding  # noqa: E402
import curate_identity  # noqa: E402
import curate_rewards  # noqa: E402
from compose_contract import (  # noqa: E402
    ACTION_EXCLUDED,
    ACTION_NOT_APPLICABLE,
    ACTION_RETAINED,
    ComposeDecision,
    REASON_MIXED_PREFERENCE_FAMILIES,
)
from compose_curated_context import (  # noqa: E402
    SourceCoordinates,
    StageDefinition,
    stage,
)
from compose_trajectory import (  # noqa: E402
    _is_same_state_pair,
    _mixed_preference_families,
    is_bridge_record,
    is_preference_record,
)
from record_kind import preference_side_kinds  # noqa: E402


IDENTITY_STAGE = StageDefinition(
    "identity", curate_identity.TRANSFORM_NAME, curate_identity.TRANSFORM_VERSION
)
BRIDGE_STAGE = StageDefinition(
    "bridge", curate_bridge.TRANSFORM_NAME, curate_bridge.TRANSFORM_VERSION
)
REASON_IDENTITY_INVALID_PAYLOAD_SHAPE = "identity.invalid_payload_shape"
BRIDGE_ORDER_ERROR_FRAGMENT = "spike_events not globally non-decreasing"
CODING_STEP_ERROR_RE = re.compile(r"^record step \d+: ")
_PROBE_FAILED: Any = object()


def _container_calibration_id_candidates(container: Mapping[str, Any]):
    """Yield usable legacy IDs from one identity container."""

    for key in curate_identity.LEGACY_ID_KEYS:
        value = container.get(key)
        if isinstance(value, str) and value.strip():
            yield value.strip()


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


def _bridge_order_repaired_copy(
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


def _coding_steps_repaired_copy(
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


def _source_preference_shape(record: Any) -> tuple[Any, bool]:
    """Return side kinds and whether source sides mix record families."""

    if not (is_preference_record(record) and isinstance(record, Mapping)):
        return None, False
    side_kinds = preference_side_kinds(record)
    mixed = not _is_same_state_pair(record) and _mixed_preference_families(
        side_kinds
    )
    return side_kinds, mixed


def _identity_retry(repaired: dict[str, Any] | None, source: SourceCoordinates):
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
    return _identity_retry(repair(record, source), source)


def _deferred_lane_repair(
    record: Any,
    identity_result: Any,
    source: SourceCoordinates,
) -> tuple[Any, str | None]:
    """Let the bridge or coding owner repair a narrowly refused invariant."""

    if identity_result.action == "retained" or not isinstance(record, Mapping):
        return identity_result, None
    retry = _lane_retry(
        is_bridge_record(record)
        and _is_bridge_order_only_rejection(identity_result.mapping),
        _bridge_order_repaired_copy,
        record,
        source,
    )
    if retry is not None:
        return retry, "bridge"
    retry = _lane_retry(
        isinstance(record.get("steps"), list)
        and _is_coding_step_only_rejection(identity_result.mapping),
        _coding_steps_repaired_copy,
        record,
        source,
    )
    if retry is not None:
        return retry, "coding"
    return identity_result, None


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


def _compose_identity_stage(
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
    result, deferred_lane = _deferred_lane_repair(record, result, source)
    reasons, detail = _identity_stage_evidence(
        result, deferred_lane, source_side_kinds, mixed_families
    )
    stages.append(
        stage(
            IDENTITY_STAGE,
            ACTION_RETAINED if result.action == "retained" else ACTION_EXCLUDED,
            reason_codes=reasons,
            lane_action=result.action,
            detail=detail,
        )
    )
    if result.action != "retained" or result.record is None:
        return ComposeDecision(
            ACTION_EXCLUDED, None, tuple(reasons), tuple(stages), None, None
        )
    current: dict[str, Any] = result.record
    _restore_deferred_payload(current, record, deferred_lane)
    return current, result.mapping.get("record_kind")


def _compose_bridge_stage(
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
