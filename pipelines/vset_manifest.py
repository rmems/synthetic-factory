"""vset-release-manifest-v1 fail-closed checks."""

from __future__ import annotations

import copy
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from vset_constants import (  # noqa: E402
    ACTOR_PROVENANCE_VERSION,
    CURATION_DECISIONS,
    IDENTITY_UNRESOLVED_PROVENANCE,
    MANIFEST_ROLES,
    MANIFEST_SCHEMA_VERSION,
    ORACLE_STATUSES,
    RECORD_KINDS,
    REVIEW_REQUIRED_KINDS,
    SOURCE_KINDS,
    VSetValidationError,
    _canonical_json,
    _check_actor,
    _is_sha256,
    _sha256_text,
    registry_pin,
)


def manifest_entry_from_record(record: Mapping[str, Any]) -> dict[str, Any]:
    """Project the #154 actor graph a later release candidate can consume."""

    oracle = record.get("oracle") if isinstance(record.get("oracle"), Mapping) else {}
    curation = record.get("curation") if isinstance(record.get("curation"), Mapping) else {}
    environment = (
        record.get("environment") if isinstance(record.get("environment"), Mapping) else {}
    )
    release = record.get("release") if isinstance(record.get("release"), Mapping) else {}
    reviewer = record.get("reviewer")
    return {
        "record_kind": record.get("record_kind"),
        "source_kind": record.get("source_kind"),
        "task_author": copy.deepcopy(record.get("task_author")),
        "solver": copy.deepcopy(record.get("solver")),
        "reviewer": None if reviewer is None else copy.deepcopy(reviewer),
        "oracle": {
            key: oracle[key]
            for key in ("kind", "status", "result_hash", "certifier")
            if key in oracle
        },
        "curation": {
            "decision": curation.get("decision"),
            "reason_codes": list(curation.get("reason_codes") or []),
        },
        "environment": {
            key: environment[key]
            for key in ("repo_snapshot_hash", "task_id", "repo_pack_id")
            if key in environment
        },
        "release": {
            key: release[key]
            for key in ("factory_contract_version", "factory_registry_sha256")
            if key in release
        },
    }


def _is_invalid_or_impossible(entry: Mapping[str, Any]) -> bool:
    if not isinstance(entry, Mapping):
        return False
    oracle = entry.get("oracle") if isinstance(entry.get("oracle"), Mapping) else {}
    curation = entry.get("curation") if isinstance(entry.get("curation"), Mapping) else {}
    reasons = curation.get("reason_codes") if isinstance(curation.get("reason_codes"), list) else []
    return oracle.get("status") == "invalid" or "vset.impossible_task" in reasons


def manifest_body_hash(manifest: Mapping[str, Any]) -> str:
    """Hash the actor graph + counts + registry pin, excluding manifest_hash."""

    body = {
        "schema_version": manifest.get("schema_version"),
        "actor_provenance_schema_version": manifest.get("actor_provenance_schema_version"),
        "factory_contract_version": manifest.get("factory_contract_version"),
        "factory_registry_sha256": manifest.get("factory_registry_sha256"),
        "counts": manifest.get("counts"),
        "entries": manifest.get("entries"),
    }
    return _sha256_text(_canonical_json(body))


def _count_map(
    entries: list[Mapping[str, Any]],
    key_path: tuple[str, ...],
    allowed: Iterable[str] | None = None,
) -> dict[str, int]:
    tallies: dict[str, int] = {name: 0 for name in allowed} if allowed is not None else {}
    for entry in entries:
        cursor: Any = entry
        for key in key_path:
            cursor = cursor.get(key) if isinstance(cursor, Mapping) else None
        if not isinstance(cursor, str):
            continue
        tallies[cursor] = tallies.get(cursor, 0) + 1
    return tallies


def validate_manifest(
    manifest: Any,
    *,
    registry_path: Path | None = None,
) -> list[VSetValidationError]:
    """Fail-closed checks for vset-release-manifest-v1."""

    if not isinstance(manifest, dict):
        return [VSetValidationError("vset.record_not_object", "manifest must be a JSON object")]
    errors: list[VSetValidationError] = []
    errors.extend(_manifest_header_errors(manifest, registry_path))
    entries = manifest.get("entries")
    if not isinstance(entries, list) or not entries:
        errors.append(
            VSetValidationError("vset.payload_invalid", "manifest.entries must be a non-empty list")
        )
        return errors
    pin = registry_pin(registry_path)
    for index, entry in enumerate(entries):
        errors.extend(_one_manifest_entry_errors(index, entry, pin))
    errors.extend(_manifest_count_errors(manifest, entries))
    if manifest.get("manifest_hash") != manifest_body_hash(manifest):
        errors.append(
            VSetValidationError(
                "vset.release_contract_mismatch",
                "manifest_hash does not match the canonical actor-graph body",
            )
        )
    return errors


def _manifest_header_errors(
    manifest: dict[str, Any], registry_path: Path | None
) -> list[VSetValidationError]:
    errors: list[VSetValidationError] = []
    if manifest.get("schema_version") != MANIFEST_SCHEMA_VERSION:
        errors.append(
            VSetValidationError(
                "vset.schema_version_invalid",
                f"schema_version must be {MANIFEST_SCHEMA_VERSION}",
            )
        )
    if manifest.get("actor_provenance_schema_version") != ACTOR_PROVENANCE_VERSION:
        errors.append(
            VSetValidationError(
                "vset.schema_version_invalid",
                f"actor_provenance_schema_version must be {ACTOR_PROVENANCE_VERSION}",
            )
        )
    pin = registry_pin(registry_path)
    if manifest.get("factory_contract_version") != pin["schema_version"]:
        errors.append(
            VSetValidationError(
                "vset.release_contract_mismatch",
                f"factory_contract_version must be {pin['schema_version']}",
            )
        )
    if manifest.get("factory_registry_sha256") != pin["sha256"]:
        errors.append(
            VSetValidationError(
                "vset.release_contract_mismatch",
                "factory_registry_sha256 must match the reviewed FACTORY-REGISTRY.json bytes",
            )
        )
    return errors


def _one_manifest_entry_errors(
    index: int, entry: Any, pin: Mapping[str, str]
) -> list[VSetValidationError]:
    where = f"entries[{index}]"
    if not isinstance(entry, dict):
        return [VSetValidationError("vset.record_not_object", f"{where} must be an object")]
    errors: list[VSetValidationError] = []
    errors.extend(_entry_kind_errors(where, entry))
    errors.extend(_entry_role_errors(where, entry))
    errors.extend(_entry_actor_pair_errors(where, entry))
    errors.extend(_entry_reviewer_errors(where, entry))
    errors.extend(_entry_evidence_errors(where, entry, pin))
    return errors


def _entry_kind_errors(where: str, entry: dict[str, Any]) -> list[VSetValidationError]:
    errors: list[VSetValidationError] = []
    if entry.get("record_kind") not in RECORD_KINDS:
        errors.append(
            VSetValidationError("vset.record_kind_invalid", f"{where}.record_kind is not a VSET kind")
        )
    if entry.get("source_kind") not in SOURCE_KINDS:
        errors.append(
            VSetValidationError("vset.source_kind_invalid", f"{where}.source_kind is invalid")
        )
    return errors


def _entry_role_errors(where: str, entry: dict[str, Any]) -> list[VSetValidationError]:
    errors: list[VSetValidationError] = []
    for role in MANIFEST_ROLES:
        if role not in entry:
            errors.append(
                VSetValidationError(
                    "vset.missing_actor_role",
                    f"{where} is missing actor-graph role {role}",
                )
            )
    return errors


def _entry_actor_pair_errors(where: str, entry: dict[str, Any]) -> list[VSetValidationError]:
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


def _entry_reviewer_errors(where: str, entry: dict[str, Any]) -> list[VSetValidationError]:
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


def _entry_evidence_errors(
    where: str, entry: dict[str, Any], pin: Mapping[str, str]
) -> list[VSetValidationError]:
    errors: list[VSetValidationError] = []
    oracle = entry.get("oracle") if isinstance(entry.get("oracle"), dict) else {}
    environment = entry.get("environment") if isinstance(entry.get("environment"), dict) else {}
    curation = entry.get("curation") if isinstance(entry.get("curation"), dict) else {}
    release = entry.get("release") if isinstance(entry.get("release"), dict) else {}
    if not _is_sha256(environment.get("repo_snapshot_hash")):
        errors.append(
            VSetValidationError(
                "vset.actor_fields_invalid",
                f"{where}.environment.repo_snapshot_hash must be sha256:<64 hex>",
            )
        )
    if oracle.get("status") == "validated" and not _is_sha256(oracle.get("result_hash")):
        errors.append(
            VSetValidationError(
                "vset.oracle_validated_without_evidence",
                f"{where} validated oracle requires result_hash",
            )
        )
    reasons = curation.get("reason_codes") if isinstance(curation.get("reason_codes"), list) else []
    if IDENTITY_UNRESOLVED_PROVENANCE in reasons:
        errors.append(
            VSetValidationError(
                "vset.identity_reason_collision",
                f"{where} must not reuse identity.unresolved_provenance for an actor gap",
            )
        )
    if _is_invalid_or_impossible(entry) and curation.get("decision") != "measure":
        errors.append(
            VSetValidationError(
                "vset.accept_requires_validated_oracle",
                f"{where} invalid/impossible tasks must remain measure outcomes",
            )
        )
    if release.get("factory_contract_version") not in {None, pin["schema_version"]}:
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


def _count_mismatch(actual: Any, expected: Any, message: str) -> list[VSetValidationError]:
    if actual == expected:
        return []
    return [VSetValidationError("vset.payload_invalid", message)]


def _invalid_or_impossible_count_errors(
    counts: Mapping[str, Any], expected_invalid: int
) -> list[VSetValidationError]:
    if "invalid_or_impossible" not in counts:
        return [
            VSetValidationError(
                "vset.payload_invalid",
                "counts.invalid_or_impossible is required; invalid tasks are not silent drops",
            )
        ]
    return _count_mismatch(
        counts.get("invalid_or_impossible"),
        expected_invalid,
        "counts.invalid_or_impossible does not match retained invalid/impossible entries",
    )


def _manifest_count_errors(
    manifest: Mapping[str, Any], entries: list[Mapping[str, Any]]
) -> list[VSetValidationError]:
    counts = manifest.get("counts")
    if not isinstance(counts, dict):
        return [VSetValidationError("vset.payload_invalid", "manifest.counts must be an object")]
    errors: list[VSetValidationError] = []
    errors.extend(
        _count_mismatch(
            counts.get("records"),
            len(entries),
            "counts.records must equal the number of retained actor-graph entries",
        )
    )
    errors.extend(
        _count_mismatch(
            counts.get("by_record_kind"),
            _count_map(entries, ("record_kind",)),
            "counts.by_record_kind does not match entries",
        )
    )
    errors.extend(
        _count_mismatch(
            counts.get("by_oracle_status"),
            _count_map(entries, ("oracle", "status"), ORACLE_STATUSES),
            "counts.by_oracle_status does not match entries",
        )
    )
    errors.extend(
        _count_mismatch(
            counts.get("by_curation_decision"),
            _count_map(entries, ("curation", "decision"), CURATION_DECISIONS),
            "counts.by_curation_decision does not match entries",
        )
    )
    expected_invalid = sum(1 for entry in entries if _is_invalid_or_impossible(entry))
    errors.extend(_invalid_or_impossible_count_errors(counts, expected_invalid))
    return errors
