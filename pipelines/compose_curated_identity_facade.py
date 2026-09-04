#!/usr/bin/env python3
"""Live compatibility adapters for identity and bridge composition lanes.

The facade binding, the identity-lane adapters, and the semantic-identity
adapters live in the ``compose_curated_identity_facade_binding``,
``compose_curated_identity_facade_lanes``, and
``compose_curated_identity_facade_semantics`` siblings; this module keeps the
run-service adapters and re-exports every sibling name so the facade keeps one
binding surface.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import ModuleType
from typing import Any, Mapping

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("compose_curated_identity_facade")
    from . import compose_curated_identity_facade_binding as _binding
    from . import compose_curated_identity_facade_lanes as _lanes
    from . import compose_curated_identity_facade_semantics as _semantics
    from .compose_curated_calibration import CalibrationContext, CalibrationServices
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "compose_curated_identity_facade"
    )
    import compose_curated_identity_facade_binding as _binding
    import compose_curated_identity_facade_lanes as _lanes
    import compose_curated_identity_facade_semantics as _semantics
    from compose_curated_calibration import CalibrationContext, CalibrationServices

_facade = _binding._facade
DeferredRepairService = _lanes.DeferredRepairService
_bridge_order_repaired_copy = _lanes._bridge_order_repaired_copy
_calibration_id_candidates = _lanes._calibration_id_candidates
_compose_bridge_stage = _lanes._compose_bridge_stage
_compose_identity_stage = _lanes._compose_identity_stage
_container_calibration_id_candidates = _lanes._container_calibration_id_candidates
_deferred_lane_repair = _lanes._deferred_lane_repair
_identity_stage_evidence = _lanes._identity_stage_evidence
_is_bridge_order_only_rejection = _lanes._is_bridge_order_only_rejection
_is_coding_step_only_rejection = _lanes._is_coding_step_only_rejection
_owner_calibration_id_candidates = _lanes._owner_calibration_id_candidates
_source_preference_shape = _lanes._source_preference_shape
calibration_for = _lanes.calibration_for
_deduplicate_curated_record = _semantics._deduplicate_curated_record
_excluded_source_line = _semantics._excluded_source_line
_identity_owner = _semantics._identity_owner
_identity_stage_detail_of = _semantics._identity_stage_detail_of
_json_pointer_tokens = _semantics._json_pointer_tokens
_mapped_legacy_id_paths = _semantics._mapped_legacy_id_paths
_original_id_paths = _semantics._original_id_paths
_pop_json_pointer = _semantics._pop_json_pointer
_post_transform_semantic_sha256 = _semantics._post_transform_semantic_sha256
_semantic_identity_owners = _semantics._semantic_identity_owners
_strip_assigned_ids = _semantics._strip_assigned_ids
_strip_provenance_labels = _semantics._strip_provenance_labels
_strip_sidecar_binding = _semantics._strip_sidecar_binding


def bind_facade(facade: ModuleType) -> None:
    """Bind this module instance to its matching live compatibility facade."""

    _binding.bind_facade(facade)


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
_calibration_services
""".split()


if __package__:
    _expose_package_sibling(__name__)
