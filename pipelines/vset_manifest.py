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
    MANIFEST_SCHEMA_VERSION,
    MANIFEST_TOP_LEVEL_KEYS,
    ORACLE_STATUSES,
    RECORD_KINDS,
    VSetValidationError,
    _canonical_json,
    _sha256_text,
    nonfinite_error,
    registry_pin,
)
from vset_manifest_entries import (  # noqa: E402
    _is_invalid_or_impossible,
    manifest_entry_errors,
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
    unknown = sorted(set(manifest) - MANIFEST_TOP_LEVEL_KEYS)
    if unknown:
        errors.append(
            VSetValidationError(
                "vset.payload_invalid", f"manifest has undeclared fields {unknown}"
            )
        )
    nonfinite = nonfinite_error(manifest, "manifest")
    if nonfinite is not None:
        errors.append(nonfinite)
    errors.extend(_manifest_header_errors(manifest, registry_path))
    entries = manifest.get("entries")
    if not isinstance(entries, list) or not entries:
        errors.append(
            VSetValidationError("vset.payload_invalid", "manifest.entries must be a non-empty list")
        )
        return errors
    pin = registry_pin(registry_path)
    for index, entry in enumerate(entries):
        errors.extend(manifest_entry_errors(index, entry, pin))
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
            _count_map(entries, ("record_kind",), RECORD_KINDS),
            "counts.by_record_kind must be zero-filled over every VSET record kind",
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
