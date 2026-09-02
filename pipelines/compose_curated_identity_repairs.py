#!/usr/bin/env python3
"""Narrow identity refusals and the downstream lane probes that repair them."""

from __future__ import annotations

import contextlib
import copy
import re
import sys
from typing import Any, Mapping

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("compose_curated_identity_repairs")
    from . import curate_bridge, curate_coding
    from .compose_curated_context import SourceCoordinates
    from .compose_trajectory import _curate_trajectory_sides
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "compose_curated_identity_repairs"
    )
    import curate_bridge
    import curate_coding
    from compose_curated_context import SourceCoordinates
    from compose_trajectory import _curate_trajectory_sides


REASON_IDENTITY_INVALID_PAYLOAD_SHAPE = "identity.invalid_payload_shape"
BRIDGE_ORDER_ERROR_FRAGMENT = "spike_events not globally non-decreasing"
CODING_STEP_ERROR_RE = re.compile(r"^record step \d+: ")
PREFERENCE_STEP_ERROR_RE = re.compile(r"^record/(?:chosen|rejected) step \d+: ")
PROBE_FAILED: Any = object()


def only_identity_shape_details(mapping: Mapping[str, Any], matches: Any) -> bool:
    """Whether identity's only diagnostics all match one lane-owned defect."""

    if list(mapping.get("reason_codes", [])) != [REASON_IDENTITY_INVALID_PAYLOAD_SHAPE]:
        return False
    details = mapping.get("details")
    if not isinstance(details, list) or not details:
        return False
    return all(isinstance(detail, str) and matches(detail) for detail in details)


def is_bridge_order_only_rejection(mapping: Mapping[str, Any]) -> bool:
    """Whether identity refused a record for spike ordering and nothing else."""

    return only_identity_shape_details(
        mapping, lambda detail: BRIDGE_ORDER_ERROR_FRAGMENT in detail
    )


def bridge_order_repaired_copy_with_source(
    record: Mapping[str, Any], source: SourceCoordinates
) -> dict[str, Any] | None:
    """Return the bridge lane's stable-sorted copy when it can repair."""

    decision: Any = PROBE_FAILED
    with contextlib.suppress(Exception):
        decision = curate_bridge.curate_record(
            record,
            source_path=source.path,
            source_line=source.line,
            source_hash=source.sha256,
            source_file_hash=None,
        )
    if decision is PROBE_FAILED:
        return None
    if decision.action != "repair" or not isinstance(decision.output_record, dict):
        return None
    return decision.output_record


def is_coding_step_only_rejection(mapping: Mapping[str, Any]) -> bool:
    """Whether identity refused an episode for step shape and nothing else."""

    return only_identity_shape_details(
        mapping, lambda detail: CODING_STEP_ERROR_RE.match(detail) is not None
    )


def coding_steps_repaired_copy_with_source(
    record: Mapping[str, Any], source: SourceCoordinates
) -> dict[str, Any] | None:
    """Return the coding lane's repaired copy when it can retain the episode."""

    curated: Any = PROBE_FAILED
    with contextlib.suppress(Exception):
        curated, _manifest = curate_coding.curate_episode(
            copy.deepcopy(dict(record)),
            source_path=source.path,
            source_line=source.line,
            source_hash=source.sha256,
        )
    if curated is PROBE_FAILED:
        return None
    return curated if isinstance(curated, dict) else None


def is_preference_step_only_rejection(mapping: Mapping[str, Any]) -> bool:
    """Whether identity refused only coding-owned preference-side steps."""

    return only_identity_shape_details(
        mapping, lambda detail: PREFERENCE_STEP_ERROR_RE.match(detail) is not None
    )


def replace_coding_steps(target: dict[str, Any], curated: Mapping[str, Any]) -> bool:
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


def preference_steps_repaired_copy_with_source(
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
        if not replace_coding_steps(target, curated_side):
            return None
    return repaired


def restore_deferred_payload(
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
            replace_coding_steps(current_side, source_side)


if __package__:
    _expose_package_sibling(__name__)
