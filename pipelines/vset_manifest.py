"""vset-release-manifest-v1 fail-closed checks."""

from __future__ import annotations

import copy
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping

if __package__:  # pragma: no cover - package-child import path
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("vset_manifest")
    from .vset_constants import (
        ACTOR_PROVENANCE_VERSION,
        CURATION_DECISIONS,
        ERR_PAYLOAD_INVALID,
        ERR_RELEASE_CONTRACT_MISMATCH,
        MANIFEST_SCHEMA_VERSION,
        MANIFEST_TOP_LEVEL_KEYS,
        ORACLE_STATUSES,
        RECORD_KINDS,
        VSetValidationError,
        _canonical_json,
        _mapping_or_empty,
        _pick,
        _sha256_text,
        nonfinite_error,
        registry_pin,
)
    from .vset_manifest_entries import manifest_entry_errors
    from .vset_manifest_entry_oracle import _is_invalid_or_impossible
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "vset_manifest"
    )
    from vset_constants import (
        ACTOR_PROVENANCE_VERSION,
        CURATION_DECISIONS,
        ERR_PAYLOAD_INVALID,
        ERR_RELEASE_CONTRACT_MISMATCH,
        MANIFEST_SCHEMA_VERSION,
        MANIFEST_TOP_LEVEL_KEYS,
        ORACLE_STATUSES,
        RECORD_KINDS,
        VSetValidationError,
        _canonical_json,
        _mapping_or_empty,
        _pick,
        _sha256_text,
        nonfinite_error,
        registry_pin,
)
    from vset_manifest_entries import manifest_entry_errors
    from vset_manifest_entry_oracle import _is_invalid_or_impossible


def manifest_entry_from_record(record: Mapping[str, Any]) -> dict[str, Any]:
    """Project the #154 actor graph a later release candidate can consume."""

    oracle = _mapping_or_empty(record.get("oracle"))
    curation = _mapping_or_empty(record.get("curation"))
    environment = _mapping_or_empty(record.get("environment"))
    release = _mapping_or_empty(record.get("release"))
    reviewer = record.get("reviewer")
    return {
        "record_kind": record.get("record_kind"),
        "source_kind": record.get("source_kind"),
        "task_author": copy.deepcopy(record.get("task_author")),
        "solver": copy.deepcopy(record.get("solver")),
        "reviewer": None if reviewer is None else copy.deepcopy(reviewer),
        "oracle": _pick(oracle, ("kind", "status", "result_hash", "certifier")),
        "curation": {
            "decision": curation.get("decision"),
            "reason_codes": list(curation.get("reason_codes") or []),
        },
        "environment": _pick(
            environment, ("repo_snapshot_hash", "task_id", "repo_pack_id")
        ),
        "release": _pick(
            release, ("factory_contract_version", "factory_registry_sha256")
        ),
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
    tallies: dict[str, int] = dict.fromkeys(allowed, 0) if allowed is not None else {}
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
                ERR_PAYLOAD_INVALID, f"manifest has undeclared fields {unknown}"
            )
        )
    nonfinite = nonfinite_error(manifest, "manifest")
    if nonfinite is not None:
        errors.append(nonfinite)
    errors.extend(_manifest_header_errors(manifest, registry_path))
    entries = manifest.get("entries")
    if not isinstance(entries, list) or not entries:
        errors.append(
            VSetValidationError(ERR_PAYLOAD_INVALID, "manifest.entries must be a non-empty list")
        )
        return errors
    pin = registry_pin(registry_path)
    for index, entry in enumerate(entries):
        errors.extend(manifest_entry_errors(index, entry, pin))
    errors.extend(_manifest_count_errors(manifest, entries))
    if manifest.get("manifest_hash") != manifest_body_hash(manifest):
        errors.append(
            VSetValidationError(
                ERR_RELEASE_CONTRACT_MISMATCH,
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
                ERR_RELEASE_CONTRACT_MISMATCH,
                f"factory_contract_version must be {pin['schema_version']}",
            )
        )
    if not manifest.get("factory_registry_sha256") or manifest.get("factory_registry_sha256") != pin["sha256"]:
        errors.append(
            VSetValidationError(
                ERR_RELEASE_CONTRACT_MISMATCH,
                "factory_registry_sha256 must match the reviewed FACTORY-REGISTRY.json bytes",
            )
        )
    return errors


def _bool_counts_in(value: Any) -> bool:
    if isinstance(value, bool):
        return True
    if isinstance(value, Mapping):
        return any(_bool_counts_in(item) for item in value.values())
    return False


def _count_mismatch(actual: Any, expected: Any, message: str) -> list[VSetValidationError]:
    # ``True == 1`` in Python, so a JSON boolean would silently satisfy an
    # integer count without this check.
    if _bool_counts_in(actual):
        return [
            VSetValidationError(
                ERR_PAYLOAD_INVALID,
                "counts must be integers, not booleans: " + message,
            )
        ]
    if actual == expected:
        return []
    return [VSetValidationError(ERR_PAYLOAD_INVALID, message)]


def _invalid_or_impossible_count_errors(
    counts: Mapping[str, Any], expected_invalid: int
) -> list[VSetValidationError]:
    if "invalid_or_impossible" not in counts:
        return [
            VSetValidationError(
                ERR_PAYLOAD_INVALID,
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
        return [VSetValidationError(ERR_PAYLOAD_INVALID, "manifest.counts must be an object")]
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


if __package__:  # pragma: no cover - package-child import path
    _expose_package_sibling(__name__)
