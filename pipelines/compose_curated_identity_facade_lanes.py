#!/usr/bin/env python3
"""Live compatibility adapters for the identity and bridge composition lanes."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from types import ModuleType
from typing import Any, Mapping

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("compose_curated_identity_facade_lanes")
    from . import compose_contract as _contract
    from . import compose_curated_identity as _identity_impl
    from .compose_curated_context import SourceCoordinates, StageDefinition
    from .compose_curated_identity_facade_binding import _facade
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "compose_curated_identity_facade_lanes"
    )
    import compose_contract as _contract
    import compose_curated_identity as _identity_impl
    from compose_curated_context import SourceCoordinates, StageDefinition
    from compose_curated_identity_facade_binding import _facade

ACTION_EXCLUDED = _contract.ACTION_EXCLUDED
ACTION_RETAINED = _contract.ACTION_RETAINED
ComposeDecision = _contract.ComposeDecision


def _container_calibration_id_candidates(container: Mapping[str, Any]):
    facade = _facade()
    for key in facade.curate_identity.LEGACY_ID_KEYS:
        value = container.get(key)
        if isinstance(value, str) and value.strip():
            yield value.strip()


def _owner_calibration_id_candidates(owner: Mapping[str, Any]):
    facade = _facade()
    for container in (owner, owner.get("meta"), owner.get("state")):
        if isinstance(container, Mapping):
            yield from facade._container_calibration_id_candidates(container)


def _calibration_id_candidates(record: Mapping[str, Any]):
    facade = _facade()
    yield from facade._owner_calibration_id_candidates(record)
    for side in ("chosen", "rejected"):
        owner = record.get(side)
        if isinstance(owner, Mapping):
            yield from facade._owner_calibration_id_candidates(owner)


def calibration_for(record: Mapping[str, Any], catalog: Mapping[str, Any] | None) -> Any:
    facade = _facade()
    if not catalog or not isinstance(record, Mapping):
        return None
    candidates = facade._facade_delegate(facade._calibration_id_candidates, record)
    for candidate in candidates:
        calibration = catalog.get(facade.curate_rewards.catalog_record_key(candidate))
        if calibration is not None:
            return calibration
    return None


def _is_bridge_order_only_rejection(mapping: Mapping[str, Any]) -> bool:
    facade = _facade()
    return facade._only_identity_shape_details(
        mapping, lambda detail: facade.BRIDGE_ORDER_ERROR_FRAGMENT in detail
    )


def _is_coding_step_only_rejection(mapping: Mapping[str, Any]) -> bool:
    facade = _facade()
    return facade._only_identity_shape_details(
        mapping, lambda detail: facade.CODING_STEP_ERROR_RE.match(detail) is not None
    )


def _source_preference_shape(record: Any) -> tuple[Any, bool]:
    facade = _facade()
    if not (facade.is_preference_record(record) and isinstance(record, Mapping)):
        return None, False
    side_kinds = facade.preference_side_kinds(record)
    mixed = not facade._is_same_state_pair(record) and facade._mixed_preference_families(side_kinds)
    return side_kinds, mixed


def _identity_stage_evidence(
    identity_result: Any,
    deferred_lane: str | None,
    source_side_kinds: Any,
    mixed_preference_families: bool,
) -> tuple[list[str], dict[str, Any]]:
    return _identity_impl._identity_stage_evidence(
        identity_result,
        deferred_lane,
        source_side_kinds,
        mixed_preference_families,
    )


def _bridge_order_repaired_copy(
    record: Mapping[str, Any],
    *,
    source_path: str,
    source_line: int,
    source_sha256: str,
) -> dict[str, Any] | None:
    facade = _facade()
    decision: Any = facade._PROBE_FAILED
    with facade.contextlib.suppress(Exception):
        decision = facade.curate_bridge.curate_record(
            record,
            source_path=source_path,
            source_line=source_line,
            source_hash=source_sha256,
            source_file_hash=None,
        )
    if decision is facade._PROBE_FAILED:
        return None
    if decision.action != "repair" or not isinstance(decision.output_record, dict):
        return None
    return decision.output_record


@dataclass(frozen=True)
class DeferredRepairService:
    """Build ordered lane repairs from live facade bindings."""

    facade: ModuleType
    source: SourceCoordinates

    def _facade_lane(self, lane: str, applies: bool, repair_name: str):
        repair = getattr(self.facade, repair_name)
        return _identity_impl.DeferredLaneRepair(
            lane,
            applies,
            lambda current: repair(
                current,
                source_path=self.source.path,
                source_line=self.source.line,
                source_sha256=self.source.sha256,
            ),
        )

    def _bridge(self, record: Mapping[str, Any], result: Any):
        applies = self.facade.is_bridge_record(
            record
        ) and self.facade._is_bridge_order_only_rejection(result.mapping)
        return self._facade_lane("bridge", applies, "_bridge_order_repaired_copy")

    def _coding(self, record: Mapping[str, Any], result: Any):
        applies = isinstance(
            record.get("steps"), list
        ) and self.facade._is_coding_step_only_rejection(result.mapping)
        return self._facade_lane("coding", applies, "_coding_steps_repaired_copy")

    def _preferences(self, record: Mapping[str, Any], result: Any):
        applies = (
            self.facade.is_preference_record(record)
            and self.facade.preference_side_kinds(record) == ("episode", "episode")
            and _identity_impl._is_preference_step_only_rejection(result.mapping)
        )
        return _identity_impl.DeferredLaneRepair(
            "preferences",
            applies,
            lambda current: _identity_impl._preference_steps_repaired_copy_with_source(
                current, self.source
            ),
        )

    def run(self, record: Any, result: Any) -> tuple[Any, str | None]:
        if result.action == "retained" or not isinstance(record, Mapping):
            return result, None
        lanes = (
            self._bridge(record, result),
            self._coding(record, result),
            self._preferences(record, result),
        )
        return _identity_impl._run_deferred_lane_repairs(
            record,
            result,
            lanes,
            lambda repaired: self.facade._identity_retry(
                repaired,
                source_path=self.source.path,
                source_line=self.source.line,
                source_sha256=self.source.sha256,
            ),
        )


def _deferred_lane_repair(
    record: Any,
    identity_result: Any,
    source: SourceCoordinates,
) -> tuple[Any, str | None]:
    return DeferredRepairService(_facade(), source).run(record, identity_result)


def _compose_identity_stage(
    record: Any,
    stages: list[dict[str, Any]],
    source: SourceCoordinates,
) -> "ComposeDecision | tuple[dict[str, Any], Any]":
    facade = _facade()
    side_kinds, mixed = facade._source_preference_shape(record)
    result = facade.curate_identity.curate_record(
        facade.curate_identity.SourceRecord(record, source.path, source.line, source.sha256)
    )
    result, deferred = facade._deferred_lane_repair(record, result, source)
    reasons, detail = facade._identity_stage_evidence(result, deferred, side_kinds, mixed)
    retained = not mixed and result.action == "retained"
    public_action = ACTION_RETAINED if retained else ACTION_EXCLUDED
    stages.append(
        facade._stage(
            StageDefinition(
                "identity",
                facade.curate_identity.TRANSFORM_NAME,
                facade.curate_identity.TRANSFORM_VERSION,
            ),
            public_action,
            reason_codes=reasons,
            lane_action=result.action,
            detail=detail,
        )
    )
    if not retained or result.record is None:
        return ComposeDecision(ACTION_EXCLUDED, None, tuple(reasons), tuple(stages), None, None)
    current: dict[str, Any] = result.record
    _identity_impl._restore_deferred_payload(current, record, deferred)
    return current, result.mapping.get("record_kind")


def _compose_bridge_stage(
    current: dict[str, Any],
    stages: list[dict[str, Any]],
    source: SourceCoordinates,
) -> "ComposeDecision | dict[str, Any]":
    facade = _facade()
    definition = StageDefinition(
        "bridge",
        facade.curate_bridge.TRANSFORM_NAME,
        facade.curate_bridge.TRANSFORM_VERSION,
    )
    if not facade.is_bridge_record(current):
        stages.append(
            facade._stage(
                definition,
                facade.ACTION_NOT_APPLICABLE,
                lane_action=facade.ACTION_NOT_APPLICABLE,
            )
        )
        return current
    decision = facade.curate_bridge.curate_record(
        current,
        source_path=source.path,
        source_line=source.line,
        source_hash=source.sha256,
        source_file_hash=source.file_sha256,
    )
    reasons = list(decision.manifest.get("reason_codes", []))
    retained = decision.output_record is not None
    stages.append(
        facade._stage(
            definition,
            ACTION_RETAINED if retained else ACTION_EXCLUDED,
            reason_codes=reasons,
            lane_action=decision.action,
            detail=decision.manifest,
        )
    )
    if not retained:
        return ComposeDecision(ACTION_EXCLUDED, None, tuple(reasons), tuple(stages), None, None)
    return decision.output_record


if __package__:
    _expose_package_sibling(__name__)
