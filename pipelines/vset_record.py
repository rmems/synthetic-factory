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
        ERR_RELEASE_CONTRACT_MISMATCH,
        RECORD_KINDS,
        RECORD_TOP_LEVEL_KEYS,
        REVIEW_REQUIRED_KINDS,
        SCHEMA_VERSION,
        VSetValidationError,
        _check_actor,
        _is_sha256,
        _mapping_or_empty,
        content_hash,
        normalize_identity,
)
    from .vset_oracle_check import oracle_errors
    from .vset_record_checks import (
        nonfinite_error,
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
        ERR_RELEASE_CONTRACT_MISMATCH,
        RECORD_KINDS,
        RECORD_TOP_LEVEL_KEYS,
        REVIEW_REQUIRED_KINDS,
        SCHEMA_VERSION,
        VSetValidationError,
        _check_actor,
        _is_sha256,
        _mapping_or_empty,
        content_hash,
        normalize_identity,
)
    from vset_oracle_check import oracle_errors
    from vset_record_checks import (
        nonfinite_error,
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
    errors.extend(_release_errors(record.get("release"), registry_path))
    errors.extend(_registry_flag_errors(record, require_registry_sha))
    if kind is not None:
        errors.extend(payload_errors(kind, record.get("payload")))
    errors.extend(_training_view_errors(record.get("training_view")))
    errors.extend(_trace_errors(record))
    errors.extend(_content_hash_errors(record))
    return errors


def _registry_flag_errors(
    record: dict[str, Any], require_registry_sha: bool
) -> list[VSetValidationError]:
    if not require_registry_sha:
        return []
    stamped = _mapping_or_empty(record.get("release")).get("factory_registry_sha256")
    if _is_sha256(stamped):
        return []
    return [
        VSetValidationError(
            ERR_RELEASE_CONTRACT_MISMATCH,
            "release.factory_registry_sha256 is required",
        )
    ]


def _trace_errors(record: dict[str, Any]) -> list[VSetValidationError]:
    if "trace" not in record or isinstance(record.get("trace"), dict):
        return []
    return [
        VSetValidationError(ERR_PAYLOAD_INVALID, "trace must be an object when present")
    ]


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


def _actor_key(actor: dict[str, Any]) -> tuple[str, str, str]:
    return (
        normalize_identity(actor.get("model")),
        normalize_identity(actor.get("version")),
        normalize_identity(actor.get("run_id")),
    )


def _same_run(author: dict[str, Any], solver: dict[str, Any]) -> bool:
    return normalize_identity(author.get("run_id")) == normalize_identity(solver.get("run_id"))


def _author_solver_conflated(
    author: dict[str, Any] | None, solver: dict[str, Any] | None
) -> list[VSetValidationError]:
    if author is None or solver is None:
        return []
    same_run = _same_run(author, solver)
    same_actor = _actor_key(author) == _actor_key(solver)
    if not same_run and not same_actor:
        return []
    return [
        VSetValidationError(
            "vset.actors_conflated",
            "task_author and solver must remain distinct on model, version, and run_id",
        )
    ]


def _actor_graph_errors(record: dict[str, Any], kind: str | None) -> list[VSetValidationError]:
    author, errors = _try_check_actor(record, "task_author", require_prompt_hash=True)
    solver, solver_errors = _try_check_actor(record, "solver", require_tool_policy=True)
    errors.extend(solver_errors)
    errors.extend(_author_solver_conflated(author, solver))
    reviewer, reviewer_errors = _reviewer_actor(record.get("reviewer", None), kind)
    errors.extend(reviewer_errors)
    errors.extend(_reviewer_distinct_errors(reviewer, author, solver))
    return errors


def _reviewer_actor(
    reviewer: Any, kind: str | None
) -> tuple[dict[str, Any] | None, list[VSetValidationError]]:
    if kind in REVIEW_REQUIRED_KINDS and not isinstance(reviewer, dict):
        return None, [
            VSetValidationError(
                "vset.reviewer_required",
                "review_remediation_v1 requires an explicit reviewer object",
            )
        ]
    if reviewer is None:
        return None, []
    if not isinstance(reviewer, dict):
        return None, [
            VSetValidationError(
                ERR_ACTOR_FIELDS_INVALID,
                "reviewer must be an object when present",
            )
        ]
    try:
        return _check_actor(reviewer, "reviewer"), []
    except VSetValidationError as exc:
        return None, [exc]


def _reviewer_distinct_errors(
    reviewer: dict[str, Any] | None,
    author: dict[str, Any] | None,
    solver: dict[str, Any] | None,
) -> list[VSetValidationError]:
    if reviewer is None:
        return []
    key = _actor_key(reviewer)
    if author is not None and key == _actor_key(author):
        return [
            VSetValidationError(
                "vset.actors_conflated",
                "reviewer must not be the task_author",
            )
        ]
    if solver is not None and key == _actor_key(solver):
        return [
            VSetValidationError(
                "vset.actors_conflated",
                "reviewer must not be the solver",
            )
        ]
    return []


def _text_field(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value
    return None


def _summary_field(value: Any) -> str | None:
    if not isinstance(value, dict):
        return None
    return _text_field(value.get("summary"))


def _prompt_source(payload: dict[str, Any]) -> str | None:
    for key in ("task_specification", "review_finding", "failure_evidence"):
        found = _text_field(payload.get(key)) or _summary_field(payload.get(key))
        if found is not None:
            return found
    return None


def _content_hash_errors(record: dict[str, Any]) -> list[VSetValidationError]:
    """Bind ``prompt_hash`` to the declared task text for this record kind."""

    author = record.get("task_author")
    payload = record.get("payload")
    if not isinstance(author, dict) or not isinstance(payload, dict):
        return []
    stamped = author.get("prompt_hash")
    source = _prompt_source(payload)
    if source is None:
        return [
            VSetValidationError(
                ERR_RELEASE_CONTRACT_MISMATCH,
                "task_author.prompt_hash requires declared task text",
            )
        ]
    if not isinstance(stamped, str):
        return []
    if stamped == content_hash(source):
        return []
    return [
        VSetValidationError(
            ERR_RELEASE_CONTRACT_MISMATCH,
            "task_author.prompt_hash must match the declared task text",
        )
    ]


def _checked_actor(value: Any, role: str) -> list[VSetValidationError]:
    try:
        _check_actor(value, role)
    except VSetValidationError as exc:
        return [exc]
    return []


if __package__:  # pragma: no cover - package-child import path
    _expose_package_sibling(__name__)
