#!/usr/bin/env python3
"""Deferred downstream-lane repair of identity-only refusals, with revalidation."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Any, Callable, Mapping

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("compose_curated_identity_deferral")
    from . import compose_curated_identity_repairs as _repairs
    from . import curate_identity
    from .compose_curated_context import SourceCoordinates
    from .compose_trajectory import is_bridge_record, is_preference_record
    from .record_kind import preference_side_kinds
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "compose_curated_identity_deferral"
    )
    import compose_curated_identity_repairs as _repairs
    import curate_identity
    from compose_curated_context import SourceCoordinates
    from compose_trajectory import is_bridge_record, is_preference_record
    from record_kind import preference_side_kinds

_is_bridge_order_only_rejection = _repairs._is_bridge_order_only_rejection
_bridge_order_repaired_copy_with_source = _repairs._bridge_order_repaired_copy_with_source
_is_coding_step_only_rejection = _repairs._is_coding_step_only_rejection
_coding_steps_repaired_copy_with_source = _repairs._coding_steps_repaired_copy_with_source
_is_preference_step_only_rejection = _repairs._is_preference_step_only_rejection
_preference_steps_repaired_copy_with_source = _repairs._preference_steps_repaired_copy_with_source


@dataclass(frozen=True)
class DeferredLaneRepair:
    """One downstream lane that may repair an identity-only refusal."""

    lane: str
    applies: bool
    repair: Callable[[Mapping[str, Any]], dict[str, Any] | None]


def _identity_retry_with_source(repaired: dict[str, Any] | None, source: SourceCoordinates):
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
            is_bridge_record(record) and _is_bridge_order_only_rejection(identity_result.mapping),
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
            lambda current: _preference_steps_repaired_copy_with_source(current, source),
        ),
    )
    return _run_deferred_lane_repairs(
        record,
        identity_result,
        lanes,
        lambda repaired: _identity_retry_with_source(repaired, source),
    )


if __package__:
    _expose_package_sibling(__name__)
