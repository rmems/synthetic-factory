"""Record-level VSET actor-provenance validation."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("vset_record")
    from .curate_coding import contains_hidden_reasoning_key
    from .curate_identity import REGISTRY_SCHEMA_VERSION
    from .vset_constants import (
        ACTOR_PROVENANCE_VERSION,
        CURATION_DECISIONS,
        IDENTITY_UNRESOLVED_PROVENANCE,
        RECORD_KINDS,
        RECORD_TOP_LEVEL_KEYS,
        REVIEW_REQUIRED_KINDS,
        SCHEMA_VERSION,
        VSetValidationError,
        _check_actor,
        _is_nonempty,
        _is_sha256,
        nonfinite_error,
        reason_codes_error,
        registry_pin,
    )
    from .vset_oracle_check import oracle_errors
    from .vset_source import payload_errors, source_kind_errors
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "vset_record"
    )
    from curate_coding import contains_hidden_reasoning_key
    from curate_identity import REGISTRY_SCHEMA_VERSION
    from vset_constants import (
        ACTOR_PROVENANCE_VERSION,
        CURATION_DECISIONS,
        IDENTITY_UNRESOLVED_PROVENANCE,
        RECORD_KINDS,
        RECORD_TOP_LEVEL_KEYS,
        REVIEW_REQUIRED_KINDS,
        SCHEMA_VERSION,
        VSetValidationError,
        _check_actor,
        _is_nonempty,
        _is_sha256,
        nonfinite_error,
        reason_codes_error,
        registry_pin,
    )
    from vset_oracle_check import oracle_errors
    from vset_source import payload_errors, source_kind_errors


def validate_record(
    record: Any,
    *,
    registry_path: Path | None = None,
    require_registry_sha: bool = False,
) -> list[VSetValidationError]:
    """Return every fail-closed violation. Empty means the record is well-formed."""

    if not isinstance(record, dict):
        return [VSetValidationError("vset.record_not_object", "record must be a JSON object")]
    errors, kind = _record_head_errors(record)
    errors.extend(source_kind_errors(record))
    errors.extend(_required_role_errors(record))
    errors.extend(_actor_graph_errors(record, kind))
    if isinstance(record.get("oracle"), dict):
        errors.extend(oracle_errors(record, record["oracle"]))
    if isinstance(record.get("curation"), dict):
        errors.extend(_curation_errors(record, record["curation"]))
    if isinstance(record.get("environment"), dict):
        errors.extend(_environment_errors(record["environment"]))
    errors.extend(_release_errors(record.get("release"), registry_path, require_registry_sha))
    if kind is not None:
        errors.extend(payload_errors(kind, record.get("payload")))
    errors.extend(_training_view_errors(record.get("training_view")))
    return errors


def _record_head_errors(
    record: dict[str, Any],
) -> tuple[list[VSetValidationError], str | None]:
    errors = _schema_header_errors(record)
    nonfinite = nonfinite_error(record, "record")
    if nonfinite is not None:
        errors.append(nonfinite)
    errors.extend(_unknown_top_level_errors(record))
    kind = record.get("record_kind")
    if not isinstance(kind, str) or kind not in RECORD_KINDS:
        errors.append(
            VSetValidationError(
                "vset.record_kind_invalid",
                "record_kind must be issue_patch_v1, review_remediation_v1, or failure_recovery_v1",
            )
        )
        kind = None
    return errors, kind


def _unknown_top_level_errors(record: dict[str, Any]) -> list[VSetValidationError]:
    return [
        VSetValidationError(
            "vset.payload_invalid",
            f"undeclared top-level record field {key!r}",
        )
        for key in sorted(set(record) - RECORD_TOP_LEVEL_KEYS)
    ]


def _schema_header_errors(record: dict[str, Any]) -> list[VSetValidationError]:
    errors: list[VSetValidationError] = []
    if record.get("schema_version") != SCHEMA_VERSION:
        errors.append(
            VSetValidationError(
                "vset.schema_version_invalid",
                f"schema_version must be {SCHEMA_VERSION}",
            )
        )
    if record.get("actor_provenance_schema_version") != ACTOR_PROVENANCE_VERSION:
        errors.append(
            VSetValidationError(
                "vset.schema_version_invalid",
                f"actor_provenance_schema_version must be {ACTOR_PROVENANCE_VERSION}",
            )
        )
    return errors


def _required_role_errors(record: dict[str, Any]) -> list[VSetValidationError]:
    errors: list[VSetValidationError] = []
    for role in ("task_author", "solver", "oracle", "curation", "environment", "release"):
        if role not in record or record[role] is None:
            errors.append(
                VSetValidationError("vset.missing_actor_role", f"required role {role} is missing")
            )
        elif not isinstance(record[role], dict):
            errors.append(
                VSetValidationError(
                    "vset.actor_fields_invalid",
                    f"{role} must be a JSON object",
                )
            )
    return errors


def _try_check_actor(
    record: dict[str, Any], role: str, **kwargs: Any
) -> tuple[dict[str, Any] | None, list[VSetValidationError]]:
    value = record.get(role)
    if not isinstance(value, dict):
        return None, []
    try:
        return _check_actor(value, role, **kwargs), []
    except VSetValidationError as exc:
        return None, [exc]


def _author_solver_conflated(
    author: dict[str, Any] | None, solver: dict[str, Any] | None
) -> list[VSetValidationError]:
    if author is None or solver is None:
        return []
    if author["run_id"] != solver["run_id"]:
        return []
    return [
        VSetValidationError(
            "vset.actors_conflated",
            "task_author.run_id and solver.run_id must remain distinct",
        )
    ]


def _actor_graph_errors(record: dict[str, Any], kind: str | None) -> list[VSetValidationError]:
    author, errors = _try_check_actor(record, "task_author", require_prompt_hash=True)
    solver, solver_errors = _try_check_actor(record, "solver", require_tool_policy=True)
    errors.extend(solver_errors)
    errors.extend(_author_solver_conflated(author, solver))
    errors.extend(_reviewer_errors(record.get("reviewer", None), kind))
    return errors


def _reviewer_errors(reviewer: Any, kind: str | None) -> list[VSetValidationError]:
    if kind in REVIEW_REQUIRED_KINDS:
        if not isinstance(reviewer, dict):
            return [
                VSetValidationError(
                    "vset.reviewer_required",
                    "review_remediation_v1 requires an explicit reviewer object",
                )
            ]
        return _checked_actor(reviewer, "reviewer")
    if reviewer is None:
        return []
    if not isinstance(reviewer, dict):
        return [
            VSetValidationError(
                "vset.actor_fields_invalid",
                "reviewer must be an object when present",
            )
        ]
    return _checked_actor(reviewer, "reviewer")


def _checked_actor(value: Any, role: str) -> list[VSetValidationError]:
    try:
        _check_actor(value, role)
    except VSetValidationError as exc:
        return [exc]
    return []


def _curation_errors(
    record: dict[str, Any], curation: dict[str, Any]
) -> list[VSetValidationError]:
    errors: list[VSetValidationError] = []
    if not _is_nonempty(curation.get("pipeline_version")):
        errors.append(
            VSetValidationError(
                "vset.actor_fields_invalid",
                "curation.pipeline_version must be a non-empty string",
            )
        )
    decision = curation.get("decision")
    if decision not in CURATION_DECISIONS:
        errors.append(
            VSetValidationError(
                "vset.actor_fields_invalid",
                "curation.decision must be accept, exclude, or measure",
            )
        )
    errors.extend(_curation_reason_errors(curation.get("reason_codes")))
    oracle_status = (
        record["oracle"].get("status") if isinstance(record.get("oracle"), dict) else None
    )
    errors.extend(_accept_gate_errors(record, decision, oracle_status))
    errors.extend(_invalid_outcome_errors(curation, decision, oracle_status))
    return errors


def _invalid_outcome_errors(
    curation: dict[str, Any], decision: Any, oracle_status: Any
) -> list[VSetValidationError]:
    """Invalid or impossible tasks stay first-class measured outcomes."""

    reasons = curation.get("reason_codes")
    impossible = isinstance(reasons, list) and "vset.impossible_task" in reasons
    if oracle_status != "invalid" and not impossible:
        return []
    if decision == "measure" and isinstance(reasons, list) and reasons:
        return []
    return [
        VSetValidationError(
            "vset.invalid_outcome_dropped",
            "invalid or impossible tasks require decision=measure with an "
            "explanatory reason code",
        )
    ]


def _accept_gate_errors(
    record: dict[str, Any], decision: Any, oracle_status: Any
) -> list[VSetValidationError]:
    if decision != "accept":
        return []
    errors: list[VSetValidationError] = []
    if record.get("source_kind") != "synthetic":
        errors.append(
            VSetValidationError(
                "vset.accept_requires_synthetic",
                "positive VSET accept requires source_kind=synthetic",
            )
        )
    if oracle_status != "validated":
        errors.append(
            VSetValidationError(
                "vset.accept_requires_validated_oracle",
                "positive accept requires oracle.status=validated",
            )
        )
    return errors


def _curation_reason_errors(reasons: Any) -> list[VSetValidationError]:
    errors = reason_codes_error(reasons, "curation")
    if errors:
        return errors
    if IDENTITY_UNRESOLVED_PROVENANCE not in reasons:
        return []
    return [
        VSetValidationError(
            "vset.identity_reason_collision",
            "identity.unresolved_provenance is the state.sim_or_real remap gap; "
            "missing actor roles use vset.missing_actor_role",
        )
    ]


def _environment_errors(environment: dict[str, Any]) -> list[VSetValidationError]:
    errors: list[VSetValidationError] = []
    if not _is_sha256(environment.get("repo_snapshot_hash")):
        errors.append(
            VSetValidationError(
                "vset.actor_fields_invalid",
                "environment.repo_snapshot_hash must be sha256:<64 hex>",
            )
        )
    if not _is_nonempty(environment.get("task_id")):
        errors.append(
            VSetValidationError(
                "vset.actor_fields_invalid",
                "environment.task_id must be a non-empty string",
            )
        )
    return errors


def _release_errors(
    release: Any,
    registry_path: Path | None,
    require_registry_sha: bool,
) -> list[VSetValidationError]:
    pin = registry_pin(registry_path)
    if not isinstance(release, dict):
        return []
    errors: list[VSetValidationError] = []
    if release.get("factory_contract_version") != pin["schema_version"]:
        errors.append(
            VSetValidationError(
                "vset.release_contract_mismatch",
                f"release.factory_contract_version must be {pin['schema_version']}",
            )
        )
    if not _is_sha256(release.get("manifest_hash")):
        errors.append(
            VSetValidationError(
                "vset.actor_fields_invalid",
                "release.manifest_hash must be sha256:<64 hex>",
            )
        )
    errors.extend(_stamped_registry_errors(release, pin, require_registry_sha))
    if pin["schema_version"] != REGISTRY_SCHEMA_VERSION:
        errors.append(
            VSetValidationError(
                "vset.release_contract_mismatch",
                "loaded registry schema_version drifted from identity's REGISTRY_SCHEMA_VERSION",
            )
        )
    return errors


def _stamped_registry_errors(
    release: dict[str, Any], pin: dict[str, str], require_registry_sha: bool
) -> list[VSetValidationError]:
    stamped = release.get("factory_registry_sha256")
    if stamped is None and not require_registry_sha:
        return []
    if stamped == pin["sha256"]:
        return []
    return [
        VSetValidationError(
            "vset.release_contract_mismatch",
            "release.factory_registry_sha256 must match the reviewed FACTORY-REGISTRY.json bytes",
        )
    ]


def _training_view_errors(training_view: Any) -> list[VSetValidationError]:
    if not isinstance(training_view, dict):
        return [
            VSetValidationError(
                "vset.hidden_reasoning_in_training_view",
                "training_view is required and must be an object",
            )
        ]
    if contains_hidden_reasoning_key(training_view):
        return [
            VSetValidationError(
                "vset.hidden_reasoning_in_training_view",
                "training_view must not contain thought / internal_reasoning*",
            )
        ]
    return []


if __package__:
    _expose_package_sibling(__name__)
