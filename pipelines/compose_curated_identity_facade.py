#!/usr/bin/env python3
"""Live compatibility adapters for identity and bridge composition lanes."""

from __future__ import annotations

import copy
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any, Mapping, MutableMapping

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("compose_curated_identity_facade")
    from . import (
        compose_curated_identity as _identity_impl,
        compose_curated_source as _source_impl,
    )
    from .compose_contract import (
        ACTION_EXCLUDED,
        ACTION_RETAINED,
        COMPOSE_NAME,
        COMPOSE_VERSION,
        ComposeDecision,
        ComposeError,
        REASON_DUPLICATE_CURATED_RECORD,
    )
    from .compose_curated_calibration import CalibrationContext, CalibrationServices
    from .compose_curated_context import SourceCoordinates
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "compose_curated_identity_facade"
    )
    import compose_curated_identity as _identity_impl
    import compose_curated_source as _source_impl
    from compose_contract import (
        ACTION_EXCLUDED,
        ACTION_RETAINED,
        COMPOSE_NAME,
        COMPOSE_VERSION,
        ComposeDecision,
        ComposeError,
        REASON_DUPLICATE_CURATED_RECORD,
    )
    from compose_curated_calibration import CalibrationContext, CalibrationServices
    from compose_curated_context import SourceCoordinates


_FACADE: ModuleType | None = None


def bind_facade(facade: ModuleType) -> None:
    """Bind this module instance to its matching live compatibility facade."""

    global _FACADE
    _FACADE = facade


def _facade() -> ModuleType:
    global _FACADE
    resolver = getattr(sys.modules.get("pipelines"), "_canonical_sibling_binding", None)
    if resolver is not None:
        _FACADE = resolver("compose_curated", _FACADE)
    if _FACADE is None:
        raise RuntimeError("compose_curated facade is not bound")
    return _FACADE


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
    *,
    source_path: str,
    source_line: int,
    source_sha256: str,
) -> tuple[Any, str | None]:
    source = SourceCoordinates(source_path, source_line, source_sha256)
    return DeferredRepairService(_facade(), source).run(record, identity_result)


def _compose_identity_stage(
    record: Any,
    stages: list[dict[str, Any]],
    *,
    source_path: str,
    source_line: int,
    source_sha256: str,
) -> "ComposeDecision | tuple[dict[str, Any], Any]":
    facade = _facade()
    side_kinds, mixed = facade._source_preference_shape(record)
    result = facade.curate_identity.curate_record(
        facade.curate_identity.SourceRecord(record, source_path, source_line, source_sha256)
    )
    result, deferred = facade._deferred_lane_repair(
        record,
        result,
        source_path=source_path,
        source_line=source_line,
        source_sha256=source_sha256,
    )
    reasons, detail = facade._identity_stage_evidence(result, deferred, side_kinds, mixed)
    retained = not mixed and result.action == "retained"
    public_action = ACTION_RETAINED if retained else ACTION_EXCLUDED
    stages.append(
        facade._stage(
            "identity",
            facade.curate_identity.TRANSFORM_NAME,
            facade.curate_identity.TRANSFORM_VERSION,
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
    *,
    source_path: str,
    source_line: int,
    source_sha256: str,
    source_file_sha256: str | None,
) -> "ComposeDecision | dict[str, Any]":
    facade = _facade()
    if not facade.is_bridge_record(current):
        stages.append(
            facade._stage(
                "bridge",
                facade.curate_bridge.TRANSFORM_NAME,
                facade.curate_bridge.TRANSFORM_VERSION,
                facade.ACTION_NOT_APPLICABLE,
                lane_action=facade.ACTION_NOT_APPLICABLE,
            )
        )
        return current
    decision = facade.curate_bridge.curate_record(
        current,
        source_path=source_path,
        source_line=source_line,
        source_hash=source_sha256,
        source_file_hash=source_file_sha256,
    )
    reasons = list(decision.manifest.get("reason_codes", []))
    retained = decision.output_record is not None
    stages.append(
        facade._stage(
            "bridge",
            facade.curate_bridge.TRANSFORM_NAME,
            facade.curate_bridge.TRANSFORM_VERSION,
            ACTION_RETAINED if retained else ACTION_EXCLUDED,
            reason_codes=reasons,
            lane_action=decision.action,
            detail=decision.manifest,
        )
    )
    if not retained:
        return ComposeDecision(ACTION_EXCLUDED, None, tuple(reasons), tuple(stages), None, None)
    return decision.output_record


def _identity_owner(record: dict[str, Any], pointer: Any) -> dict[str, Any] | None:
    if pointer == "/":
        return record
    tokens = _facade()._json_pointer_tokens(pointer)
    return _source_impl._descendant_mapping(record, tokens) if tokens is not None else None


def _json_pointer_tokens(pointer: Any) -> list[str] | None:
    return _source_impl._json_pointer_tokens(pointer)


def _pop_json_pointer(record: dict[str, Any], pointer: Any) -> None:
    tokens = _facade()._json_pointer_tokens(pointer)
    if tokens is None:
        return
    owner: Any = record
    for token in tokens[:-1]:
        if not isinstance(owner, dict):
            return
        owner = owner.get(token)
    if isinstance(owner, dict) and tokens[-1]:
        owner.pop(tokens[-1], None)


def _original_id_paths(originals: Any) -> list[str]:
    return _source_impl._original_id_paths(originals)


def _mapped_legacy_id_paths(detail: Mapping[str, Any] | None) -> tuple[str, ...]:
    if not isinstance(detail, Mapping):
        return ()
    facade = _facade()
    paths = facade._original_id_paths(detail.get("original_ids"))
    mappings = detail.get("id_mappings")
    for mapping in mappings if isinstance(mappings, list) else ():
        if isinstance(mapping, dict):
            paths.extend(facade._original_id_paths(mapping.get("original_ids")))
    return tuple(dict.fromkeys(paths))


def _semantic_identity_owners(record: dict[str, Any]) -> list[dict[str, Any]]:
    return _source_impl._semantic_identity_owners(record)


def _identity_stage_detail_of(decision: ComposeDecision) -> dict[str, Any] | None:
    return _source_impl._identity_stage_detail_of(decision)


def _strip_assigned_ids(semantic: dict[str, Any], detail: dict[str, Any] | None) -> None:
    facade = _facade()
    mappings = detail.get("id_mappings") if isinstance(detail, dict) else None
    for mapping in mappings if isinstance(mappings, list) else ():
        if not isinstance(mapping, dict):
            continue
        owner = facade._identity_owner(semantic, mapping.get("owner_path"))
        if owner is not None and owner.get("id") == mapping.get("output_id"):
            owner.pop("id", None)
    for path in facade._mapped_legacy_id_paths(detail):
        facade._pop_json_pointer(semantic, path)


def _strip_provenance_labels(semantic: dict[str, Any]) -> None:
    for owner in _facade()._semantic_identity_owners(semantic):
        meta = owner.get("meta")
        if not isinstance(meta, dict):
            continue
        for label in ("factory", "generator", "generator_version", "run", "round"):
            meta.pop(label, None)


def _strip_sidecar_binding(semantic: dict[str, Any]) -> None:
    return _source_impl._strip_sidecar_binding(semantic)


def _post_transform_semantic_sha256(decision: ComposeDecision) -> str:
    facade = _facade()
    if decision.record is None:
        raise ComposeError("cannot hash a missing curated record")
    semantic = copy.deepcopy(decision.record)
    facade._strip_assigned_ids(semantic, facade._identity_stage_detail_of(decision))
    facade._strip_provenance_labels(semantic)
    facade._strip_sidecar_binding(semantic)
    return facade._canonical_sha256(semantic)


def _deduplicate_curated_record(
    decision: ComposeDecision,
    *,
    source_path: str,
    source_line: int,
    seen_curated_semantics: MutableMapping[str, tuple[str, int]] | None,
) -> ComposeDecision:
    facade = _facade()
    retained = decision.action == ACTION_RETAINED and decision.record is not None
    if seen_curated_semantics is None or not retained:
        return decision
    digest = facade._post_transform_semantic_sha256(decision)
    first = seen_curated_semantics.get(digest)
    if first is None:
        seen_curated_semantics[digest] = (source_path, source_line)
        return decision
    duplicate = facade._stage(
        "post_transform_dedup",
        COMPOSE_NAME,
        COMPOSE_VERSION,
        ACTION_EXCLUDED,
        reason_codes=[REASON_DUPLICATE_CURATED_RECORD],
        semantic_sha256=digest,
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


def _excluded_source_line(reason: str, detail: dict[str, Any]) -> ComposeDecision:
    evidence = _facade()._stage(
        "source",
        COMPOSE_NAME,
        COMPOSE_VERSION,
        ACTION_EXCLUDED,
        reason_codes=[reason],
        detail=detail,
    )
    return ComposeDecision(ACTION_EXCLUDED, None, (reason,), (evidence,), None, None)


def transform_contract() -> dict[str, Any]:
    facade = _facade()
    return facade._facade_delegate(
        facade._transform_contract_impl, facade.curate_trajectory_preferences
    )


def _source_snapshot_identities(
    resolved_source: Path, source_members: tuple[str, ...]
) -> dict[str, tuple[tuple[int, ...], str, bool]]:
    facade = _facade()
    identities = {}
    for relative in source_members:
        path = facade._facade_delegate(
            facade._source_member_path,
            resolved_source,
            relative,
            f"compose source {relative}",
        )
        factory, verified = facade._facade_delegate(
            facade.factory_identity_for_path, resolved_source, path
        )
        identities[relative] = (
            facade._stable_file_identity(path.lstat()),
            factory,
            verified,
        )
    return identities


def _captured_source_payloads(
    resolved_source: Path, source_members: tuple[str, ...]
) -> dict[str, bytes]:
    facade = _facade()
    return facade._facade_delegate(
        facade._captured_source_payloads_impl,
        resolved_source,
        source_members,
        facade._read_exact_regular_file,
    )


def _calibration_services() -> CalibrationServices:
    facade = _facade()
    return CalibrationServices(
        facade._read_exact_child_file,
        facade._reject_duplicate_object_keys,
        facade.reject_json_constant,
        facade._parse_finite_json_float,
        facade.curate_rewards.units_migration_catalog,
        facade.sha256_hex,
        facade.training_audit.audit_run,
    )


def _load_calibration(
    source_run: Path, units_migration: Path | None
) -> tuple[dict[str, Any], dict[str, Any]]:
    facade = _facade()
    return facade._facade_delegate(
        facade._load_calibration_impl,
        CalibrationContext(source_run, units_migration),
        facade._calibration_services(),
    )


def compact_audit_report(report: Mapping[str, Any] | None, record_count: int) -> dict[str, Any]:
    facade = _facade()
    return facade._facade_delegate(facade._compact_audit_report_impl, report, record_count)


def _audit_records(records_dir: Path, record_count: int) -> dict[str, Any]:
    facade = _facade()
    report = facade.training_audit.audit_run(records_dir) if record_count else None
    return facade._facade_delegate(facade.compact_audit_report, report, record_count)


__all__ = """
_audit_records _bridge_order_repaired_copy _calibration_id_candidates
_captured_source_payloads _deduplicate_curated_record _excluded_source_line
_compose_bridge_stage _compose_identity_stage
_container_calibration_id_candidates _deferred_lane_repair
_identity_owner _identity_stage_detail_of _identity_stage_evidence
_is_bridge_order_only_rejection
_is_coding_step_only_rejection _owner_calibration_id_candidates
_json_pointer_tokens _load_calibration _mapped_legacy_id_paths
_original_id_paths _pop_json_pointer _post_transform_semantic_sha256
_semantic_identity_owners _source_preference_shape _source_snapshot_identities
_strip_assigned_ids _strip_provenance_labels _strip_sidecar_binding
calibration_for compact_audit_report transform_contract
""".split()


if __package__:
    _expose_package_sibling(__name__)
