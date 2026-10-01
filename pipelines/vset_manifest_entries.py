"""Per-entry checks for vset-release-manifest-v1 documents.

Split out of ``vset_manifest.py`` for file health. Manifest entries are
projections of released records, so the record contract follows them
into the manifest: the accept gate, oracle independence, reason-code
uniqueness, and identity rules are enforced here too.
"""

from __future__ import annotations

import sys
from typing import Any, Mapping

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("vset_manifest_entries")
    from .vset_constants import (
        CURATION_DECISIONS,
        ENTRY_TOP_LEVEL_KEYS,
        IDENTITY_UNRESOLVED_PROVENANCE,
        MANIFEST_ROLES,
        ORACLE_STATUSES,
        RECORD_KINDS,
        REVIEW_REQUIRED_KINDS,
        VSetValidationError,
        _check_actor,
        _is_sha256,
        _mapping_or_empty,
        nonfinite_error,
        reason_codes_error,
    )
    from .vset_oracle_check import validated_oracle_independence_errors
    from .vset_source import source_kind_errors
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "vset_manifest_entries"
    )
    from vset_constants import (
        CURATION_DECISIONS,
        ENTRY_TOP_LEVEL_KEYS,
        IDENTITY_UNRESOLVED_PROVENANCE,
        MANIFEST_ROLES,
        ORACLE_STATUSES,
        RECORD_KINDS,
        REVIEW_REQUIRED_KINDS,
        VSetValidationError,
        _check_actor,
        _is_sha256,
        _mapping_or_empty,
        nonfinite_error,
        reason_codes_error,
    )
    from vset_oracle_check import validated_oracle_independence_errors
    from vset_source import source_kind_errors


def manifest_entry_errors(
    index: int, entry: Any, pin: Mapping[str, str]
) -> list[VSetValidationError]:
    where = f"entries[{index}]"
    if not isinstance(entry, dict):
        return [VSetValidationError("vset.record_not_object", f"{where} must be an object")]
    errors: list[VSetValidationError] = []
    unknown = sorted(set(entry) - ENTRY_TOP_LEVEL_KEYS)
    if unknown:
        errors.append(
            VSetValidationError(
                "vset.payload_invalid", f"{where} has undeclared fields {unknown}"
            )
        )
    if entry.get("record_kind") not in RECORD_KINDS:
        errors.append(
            VSetValidationError("vset.record_kind_invalid", f"{where}.record_kind is not a VSET kind")
        )
    errors.extend(source_kind_errors(entry))
    errors.extend(_entry_role_errors(where, entry))
    errors.extend(_entry_actor_pair_errors(where, entry))
    errors.extend(_entry_reviewer_errors(where, entry))
    errors.extend(_entry_environment_errors(where, entry))
    errors.extend(_entry_oracle_errors(where, entry))
    errors.extend(_entry_curation_errors(where, entry))
    errors.extend(_entry_release_pin_errors(where, entry, pin))
    nonfinite = nonfinite_error(entry, where)
    if nonfinite is not None:
        errors.append(nonfinite)
    return errors


def _entry_role_errors(where: str, entry: Mapping[str, Any]) -> list[VSetValidationError]:
    return [
        VSetValidationError(
            "vset.missing_actor_role",
            f"{where} is missing actor-graph role {role}",
        )
        for role in MANIFEST_ROLES
        if role not in entry
    ]


def _entry_actor_pair_errors(where: str, entry: Mapping[str, Any]) -> list[VSetValidationError]:
    if "task_author" not in entry or "solver" not in entry:
        return []
    try:
        author = _check_actor(entry["task_author"], f"{where}.task_author", require_prompt_hash=True)
        solver = _check_actor(entry["solver"], f"{where}.solver", require_tool_policy=True)
    except VSetValidationError as exc:
        return [exc]
    if author["run_id"] == solver["run_id"]:
        return [
            VSetValidationError(
                "vset.actors_conflated",
                f"{where} task_author.run_id and solver.run_id must remain distinct",
            )
        ]
    return []


def _entry_reviewer_errors(where: str, entry: Mapping[str, Any]) -> list[VSetValidationError]:
    reviewer = entry.get("reviewer")
    if entry.get("record_kind") in REVIEW_REQUIRED_KINDS and not isinstance(reviewer, dict):
        return [
            VSetValidationError(
                "vset.reviewer_required",
                f"{where} review_remediation_v1 requires an explicit reviewer",
            )
        ]
    if reviewer is None:
        return []
    try:
        _check_actor(reviewer, f"{where}.reviewer")
    except VSetValidationError as exc:
        return [exc]
    return []


def _entry_environment_errors(where: str, entry: Mapping[str, Any]) -> list[VSetValidationError]:
    environment = entry.get("environment")
    env_where = f"{where}.environment"
    if environment is None:
        return []
    if not isinstance(environment, Mapping):
        return [VSetValidationError("vset.payload_invalid", f"{env_where} must be an object")]
    errors: list[VSetValidationError] = []
    if not _is_sha256(environment.get("repo_snapshot_hash")):
        errors.append(
            VSetValidationError(
                "vset.actor_fields_invalid",
                f"{env_where}.repo_snapshot_hash must be sha256:<64 hex>",
            )
        )
    task_id = environment.get("task_id")
    if not isinstance(task_id, str) or not task_id.strip():
        errors.append(
            VSetValidationError(
                "vset.payload_invalid", f"{env_where}.task_id must be a non-empty string"
            )
        )
    return errors


def _entry_oracle_status_errors(
    where: str, oracle: Mapping[str, Any]
) -> list[VSetValidationError]:
    status = oracle.get("status")
    if status is None or status in ORACLE_STATUSES:
        return []
    return [
        VSetValidationError(
            "vset.oracle_status_invalid", f"{where}.oracle.status is not a known status"
        )
    ]


def _entry_validated_oracle_errors(
    where: str, entry: Mapping[str, Any], oracle: Mapping[str, Any]
) -> list[VSetValidationError]:
    errors: list[VSetValidationError] = []
    if not _is_sha256(oracle.get("result_hash")):
        errors.append(
            VSetValidationError(
                "vset.oracle_validated_without_evidence",
                f"{where} validated oracle requires result_hash",
            )
        )
    solver: Mapping[str, Any] = _mapping_or_empty(entry.get("solver"))
    author: Mapping[str, Any] = _mapping_or_empty(entry.get("task_author"))
    errors.extend(validated_oracle_independence_errors(oracle, solver, author))
    return errors


def _entry_oracle_errors(where: str, entry: Mapping[str, Any]) -> list[VSetValidationError]:
    oracle = entry.get("oracle")
    if oracle is None:
        return []
    if not isinstance(oracle, Mapping):
        return [VSetValidationError("vset.payload_invalid", f"{where}.oracle must be an object")]
    errors = _entry_oracle_status_errors(where, oracle)
    if oracle.get("status") == "validated":
        errors.extend(_entry_validated_oracle_errors(where, entry, oracle))
    return errors


def _is_invalid_or_impossible(entry: Mapping[str, Any]) -> bool:
    if not isinstance(entry, Mapping):
        return False
    oracle = _mapping_or_empty(entry.get("oracle"))
    curation = _mapping_or_empty(entry.get("curation"))
    reasons_value = curation.get("reason_codes")
    reasons: list[Any] = reasons_value if isinstance(reasons_value, list) else []
    return oracle.get("status") == "invalid" or "vset.impossible_task" in reasons


def _entry_reason_errors(
    where: str, curation: Mapping[str, Any]
) -> list[VSetValidationError]:
    if "reason_codes" not in curation:
        return []
    errors = reason_codes_error(curation["reason_codes"], f"{where}.curation")
    reasons_value = curation["reason_codes"]
    reasons: list[Any] = reasons_value if isinstance(reasons_value, list) else []
    if IDENTITY_UNRESOLVED_PROVENANCE in reasons:
        errors.append(
            VSetValidationError(
                "vset.identity_reason_collision",
                f"{where} must not reuse identity.unresolved_provenance for an actor gap",
            )
        )
    return errors


def _entry_curation_errors(where: str, entry: Mapping[str, Any]) -> list[VSetValidationError]:
    curation = entry.get("curation")
    if curation is None:
        return []
    if not isinstance(curation, Mapping):
        return [VSetValidationError("vset.payload_invalid", f"{where}.curation must be an object")]
    errors: list[VSetValidationError] = []
    decision = curation.get("decision")
    if decision is not None and decision not in CURATION_DECISIONS:
        errors.append(
            VSetValidationError(
                "vset.actor_fields_invalid", f"{where}.curation.decision is not a known decision"
            )
        )
    errors.extend(_entry_reason_errors(where, curation))
    if _is_invalid_or_impossible(entry) and decision != "measure":
        errors.append(
            VSetValidationError(
                "vset.invalid_outcome_dropped",
                f"{where} invalid/impossible tasks must remain measure outcomes",
            )
        )
    if decision == "accept":
        errors.extend(_entry_accept_errors(where, entry))
    return errors


def _entry_accept_errors(where: str, entry: Mapping[str, Any]) -> list[VSetValidationError]:
    errors: list[VSetValidationError] = []
    if entry.get("source_kind") != "synthetic":
        errors.append(
            VSetValidationError(
                "vset.accept_requires_synthetic",
                f"{where}: accepted records must be first-party synthetic",
            )
        )
    oracle = entry.get("oracle")
    oracle_status = oracle.get("status") if isinstance(oracle, Mapping) else None
    if oracle_status != "validated":
        errors.append(
            VSetValidationError(
                "vset.accept_requires_validated_oracle",
                f"{where}: accepted records require a validated oracle",
            )
        )
    return errors


def _entry_release_pin_errors(
    where: str, entry: Mapping[str, Any], pin: Mapping[str, str]
) -> list[VSetValidationError]:
    release = entry.get("release")
    if not isinstance(release, Mapping):
        return []
    errors: list[VSetValidationError] = []
    if release.get("factory_contract_version") != pin["schema_version"]:
        errors.append(
            VSetValidationError(
                "vset.release_contract_mismatch",
                f"{where}.release.factory_contract_version must match the registry pin",
            )
        )
    if release.get("factory_registry_sha256") not in {None, pin["sha256"]}:
        errors.append(
            VSetValidationError(
                "vset.release_contract_mismatch",
                f"{where}.release.factory_registry_sha256 must match the registry pin",
            )
        )
    return errors


if __package__:
    _expose_package_sibling(__name__)
