"""Record-level VSET actor-provenance validation."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

if __package__:  # pragma: no cover - package-child import path
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("vset_record")
    from .vset_constants import (
        ACTOR_PROVENANCE_VERSION,
        ERR_ACTOR_FIELDS_INVALID,
        ERR_PAYLOAD_INVALID,
        RECORD_KINDS,
        RECORD_TOP_LEVEL_KEYS,
        REVIEW_REQUIRED_KINDS,
        SCHEMA_VERSION,
        VSetValidationError,
        _check_actor,
        nonfinite_error,
)
    from .vset_oracle_check import oracle_errors
    from .vset_record_checks import (
        _curation_errors,
        _environment_errors,
        _release_errors,
        _training_view_errors,
    )
    from .vset_source import payload_errors, source_kind_errors
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "vset_record"
    )
    from vset_constants import (
        ACTOR_PROVENANCE_VERSION,
        ERR_ACTOR_FIELDS_INVALID,
        ERR_PAYLOAD_INVALID,
        RECORD_KINDS,
        RECORD_TOP_LEVEL_KEYS,
        REVIEW_REQUIRED_KINDS,
        SCHEMA_VERSION,
        VSetValidationError,
        _check_actor,
        nonfinite_error,
)
    from vset_oracle_check import oracle_errors
    from vset_record_checks import (
        _curation_errors,
        _environment_errors,
        _release_errors,
        _training_view_errors,
    )
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
            ERR_PAYLOAD_INVALID,
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
                    ERR_ACTOR_FIELDS_INVALID,
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
                ERR_ACTOR_FIELDS_INVALID,
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


if __package__:  # pragma: no cover - package-child import path
    _expose_package_sibling(__name__)
