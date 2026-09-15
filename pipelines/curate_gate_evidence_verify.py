#!/usr/bin/env python3
"""Re-verification of sealed governance evidence for the curation gate.

Split out of ``curate_gate.py`` (CodeScene: Lines of Code in a Single File) by
responsibility; every name is re-exported from ``curate_gate`` so existing
``curate_gate.X`` call sites resolve unchanged.

``curate_gate_evidence`` seals each authenticated lane manifest and reward
artifact into the cleaned tree. This module is the other half of that round
trip: before a promotion it rebuilds every lane decision from nothing but those
sealed bytes -- re-hashing each copy, re-parsing and re-authenticating every
manifest entry, re-deriving the reward documents, proving the governance file
set and ``governance_outputs`` metadata match exactly, and binding each
retained identity entry back to its source-original attestation.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, NamedTuple, Sequence

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("curate_gate_evidence_verify")
    from . import curate_gate_contract as _contract
    from . import curate_gate_digest as _digest
    from . import curate_gate_evidence as _evidence
    from . import curate_gate_manifests as _manifests
    from . import curate_gate_paths as _paths
    from . import curate_rewards
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "curate_gate_evidence_verify"
    )
    _PIPELINES = Path(__file__).resolve().parent
    if str(_PIPELINES) not in sys.path:
        sys.path.insert(0, str(_PIPELINES))
    import curate_gate_contract as _contract
    import curate_gate_digest as _digest
    import curate_gate_evidence as _evidence
    import curate_gate_manifests as _manifests
    import curate_gate_paths as _paths
    import curate_rewards

GateError = _contract.GateError
GOVERNANCE_DIRNAME = _contract.GOVERNANCE_DIRNAME
REQUIRED_LANES = _contract.REQUIRED_LANES
RETAIN_ACTIONS = _contract.RETAIN_ACTIONS
REWARD_ARTIFACT_KINDS = _contract.REWARD_ARTIFACT_KINDS
REWARD_CALIBRATION_KIND = _contract.REWARD_CALIBRATION_KIND
_normalized_sha256 = _digest._normalized_sha256
_read_regular_file_snapshot = _digest._read_regular_file_snapshot
_logical_source_path = _paths._logical_source_path
collect_lane_manifests = _manifests.collect_lane_manifests
RetentionView = _manifests.RetentionView
_manifest_entries = _manifests._manifest_entries
_normalize_entry = _manifests._normalize_entry
_evidence_file = _evidence._evidence_file
_load_reward_sidecars = _evidence._load_reward_sidecars


def _verify_lane_manifest_file(
    cleaned: Path, index: int, manifest_meta: dict[str, Any]
) -> tuple[Path, bytes, str, int]:
    """Locate and authenticate one lane's sealed manifest copy."""
    manifest_path = _evidence_file(
        cleaned, manifest_meta.get("path"), f"lane_evidence[{index}].manifest"
    )
    expected_sha = _normalized_sha256(
        manifest_meta.get("sha256"), f"lane_evidence[{index}].manifest.sha256"
    )
    manifest_payload, actual_manifest_sha, manifest_bytes = _read_regular_file_snapshot(
        manifest_path,
        f"lane_evidence[{index}] manifest",
    )
    if actual_manifest_sha != expected_sha:
        raise GateError(f"lane_evidence[{index}] manifest hash mismatch")
    if manifest_meta.get("bytes") != manifest_bytes:
        raise GateError(f"lane_evidence[{index}] manifest byte count mismatch")
    return manifest_path, manifest_payload, expected_sha, manifest_bytes


def _authenticate_evidence_entry(
    raw_entry: dict[str, Any],
    lane: dict[str, Any],
    label: str,
    seen_sources: set[tuple[str, int]],
) -> dict[str, Any]:
    """Normalize one sealed manifest entry and pin its source identity."""
    entry = _normalize_entry(raw_entry, lane)
    if entry["declared_transform"] != lane["transform"] or entry["declared_version"] != (
        lane["version"]
    ):
        raise GateError(f"{label} no longer matches its lane contract")
    source_path = _logical_source_path(entry["source_path"], f"{label} source_path")
    source_line = entry["source_line"]
    if not isinstance(source_line, int) or isinstance(source_line, bool) or source_line < 1:
        raise GateError(f"{label} source_line must be a positive integer")
    source_key = (source_path, source_line)
    if source_key in seen_sources:
        raise GateError(f"{label} duplicates source identity {source_path}:{source_line}")
    seen_sources.add(source_key)
    entry["source_path"] = source_path
    entry["source_hash"] = _normalized_sha256(entry.get("source_hash"), f"{label} source hash")
    entry["_source_key"] = source_key
    if entry.get("output_hash") is not None:
        entry["output_hash"] = _normalized_sha256(entry["output_hash"], f"{label} output hash")
    return entry


def _verify_lane_entries(
    lane: dict[str, Any], manifest_path: Path, manifest_payload: bytes, manifest_format: str
) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    seen_sources: set[tuple[str, int]] = set()
    for entry_index, raw_entry in enumerate(
        _manifest_entries(
            manifest_path,
            manifest_format,
            payload=manifest_payload,
        ),
        1,
    ):
        entries.append(
            _authenticate_evidence_entry(
                raw_entry, lane, f"{manifest_path}: entry {entry_index}", seen_sources
            )
        )
    return entries


def _artifact_catalog_documents(
    artifact: dict[str, Any], artifact_path: Path, artifact_payload: bytes, index: int
) -> tuple[Any, list[dict[str, Any]]]:
    if artifact.get("kind") == REWARD_CALIBRATION_KIND:
        try:
            catalog = curate_rewards.load_units_migration_bytes(
                artifact_payload,
                label=artifact_path.as_posix(),
            )
        except curate_rewards.RewardOntologyError as exc:
            raise GateError(
                f"lane_evidence[{index}] calibration artifact is invalid: {exc}"
            ) from exc
        return catalog, []
    return None, _load_reward_sidecars(artifact_path, payload=artifact_payload)


def _verify_lane_artifact(
    cleaned: Path, index: int, artifact_index: int, artifact: Any
) -> tuple[Path, str, int, list[dict[str, Any]], Any]:
    if not isinstance(artifact, dict) or artifact.get("kind") not in REWARD_ARTIFACT_KINDS:
        raise GateError(f"lane_evidence[{index}].artifacts[{artifact_index}] is invalid")
    artifact_path = _evidence_file(
        cleaned,
        artifact.get("path"),
        f"lane_evidence[{index}].artifacts[{artifact_index}]",
    )
    expected_sha = _normalized_sha256(
        artifact.get("sha256"),
        f"lane_evidence[{index}].artifacts[{artifact_index}].sha256",
    )
    artifact_payload, actual_artifact_sha, artifact_bytes = _read_regular_file_snapshot(
        artifact_path,
        f"lane_evidence[{index}] artifact {artifact_index}",
    )
    if actual_artifact_sha != expected_sha:
        raise GateError(f"lane_evidence[{index}] artifact hash mismatch")
    catalog, documents = _artifact_catalog_documents(
        artifact, artifact_path, artifact_payload, index
    )
    if artifact.get("documents") != len(documents):
        raise GateError(f"lane_evidence[{index}] artifact document count mismatch")
    if artifact.get("bytes") != artifact_bytes:
        raise GateError(f"lane_evidence[{index}] artifact byte count mismatch")
    return artifact_path, expected_sha, artifact_bytes, documents, catalog


class _GovernanceTally(NamedTuple):
    """Every sealed governance file the manifest must account for, exactly."""

    files: set[str]
    outputs: list[dict[str, Any]]


def _verify_lane_artifacts(
    cleaned: Path,
    evidence: dict[str, Any],
    lane: dict[str, Any],
    tally: _GovernanceTally,
) -> None:
    index = lane["order"]
    expected_files = tally.files
    expected_governance_outputs = tally.outputs
    artifacts = evidence.get("artifacts", [])
    if not isinstance(artifacts, list):
        raise GateError(f"lane_evidence[{index}].artifacts must be a list")
    for artifact_index, artifact in enumerate(artifacts, 1):
        path, expected_sha, artifact_bytes, documents, catalog = _verify_lane_artifact(
            cleaned, index, artifact_index, artifact
        )
        expected_files.add(path.relative_to(cleaned).as_posix())
        expected_governance_outputs.append(
            {
                "kind": artifact.get("kind"),
                "path": path.relative_to(cleaned).as_posix(),
                "sha256": expected_sha,
                "bytes": artifact_bytes,
                "documents": len(documents),
            }
        )
        artifacts_for_lane = lane.setdefault("artifacts", [])
        artifacts_for_lane.append(
            {
                "kind": artifact.get("kind"),
                "source_path": path,
                "_catalog": catalog,
            }
        )


def _verify_lane_evidence_row(
    cleaned: Path,
    index: int,
    evidence: Any,
    tally: _GovernanceTally,
) -> tuple[dict[str, Any], tuple[Any, Any]]:
    """Rebuild one lane from its sealed manifest, entries and artifacts."""
    expected_files = tally.files
    expected_governance_outputs = tally.outputs
    if not isinstance(evidence, dict):
        raise GateError(f"lane_evidence[{index}] must be an object")
    order = evidence.get("lane_order")
    transform = evidence.get("transform")
    version = evidence.get("version")
    bead = evidence.get("bead")
    if order != index or not isinstance(version, str):
        raise GateError(f"lane_evidence[{index}] has invalid lane metadata")
    manifest_meta = evidence.get("manifest")
    if not isinstance(manifest_meta, dict):
        raise GateError(f"lane_evidence[{index}].manifest must be an object")
    manifest_path, manifest_payload, expected_sha, manifest_bytes = _verify_lane_manifest_file(
        cleaned, index, manifest_meta
    )
    expected_files.add(manifest_path.relative_to(cleaned).as_posix())
    expected_governance_outputs.append(
        {
            "path": manifest_path.relative_to(cleaned).as_posix(),
            "sha256": expected_sha,
            "bytes": manifest_bytes,
            "format": manifest_meta.get("format"),
            "kind": "lane_manifest",
        }
    )

    lane = {
        "order": index,
        "bead": bead,
        "transform": transform,
        "version": version,
        "manifest_path": manifest_path,
    }
    manifest_format = manifest_meta.get("format")
    if manifest_format not in {"json", "jsonl"}:
        raise GateError(f"lane_evidence[{index}].manifest has invalid format metadata")
    entries = _verify_lane_entries(lane, manifest_path, manifest_payload, manifest_format)
    _verify_lane_artifacts(cleaned, evidence, lane, tally)
    return {**lane, "entries": entries}, (bead, transform)


def _assert_governance_file_set(cleaned: Path, expected_files: set[str]) -> None:
    actual_files = {
        path.relative_to(cleaned).as_posix()
        for path in sorted((cleaned / GOVERNANCE_DIRNAME).rglob("*"))
        if path.is_file()
    }
    if actual_files != expected_files:
        raise GateError(
            "governance evidence file set mismatch: "
            f"missing={sorted(expected_files - actual_files)}, "
            f"extra={sorted(actual_files - expected_files)}"
        )


def _identity_attestations(manifest: dict[str, Any]) -> dict[tuple[str, int, str], str]:
    """Index the manifest's retained identity source-original attestations."""
    raw_identity_mappings = manifest.get("identity_mappings")
    if not isinstance(raw_identity_mappings, list):
        raise GateError("curation manifest needs retained identity mappings")
    attestations: dict[tuple[str, int, str], str] = {}
    for index, mapping in enumerate(raw_identity_mappings, 1):
        label = f"identity_mappings[{index}]"
        if not isinstance(mapping, dict):
            raise GateError(f"{label} must be an object")
        source_path = _logical_source_path(mapping.get("source_path"), f"{label}.source_path")
        source_line = mapping.get("source_line")
        if not isinstance(source_line, int) or isinstance(source_line, bool) or source_line < 1:
            raise GateError(f"{label}.source_line must be a positive integer")
        manifest_entry_sha256 = _normalized_sha256(
            mapping.get("manifest_entry_sha256"),
            f"{label}.manifest_entry_sha256",
        )
        key = (source_path, source_line, manifest_entry_sha256)
        if key in attestations:
            raise GateError(f"{label} duplicates retained identity evidence")
        attestations[key] = _normalized_sha256(
            mapping.get("source_originals_sha256"),
            f"{label}.source_originals_sha256",
        )
    return attestations


def _restore_identity_attestations(
    prepared: Sequence[dict[str, Any]],
    attestations: dict[tuple[str, int, str], str],
    retained_source_keys: set[tuple[str, int]] | None,
) -> None:
    """Bind every retained identity entry back to its sealed attestation."""
    restored: set[tuple[str, int, str]] = set()
    for lane in prepared:
        if lane["transform"] != "curate_identity":
            continue
        for entry in lane["entries"]:
            source_key = entry["_source_key"]
            action = str(entry.get("action") or "").strip().lower()
            if action not in RETAIN_ACTIONS or (
                retained_source_keys is not None and source_key not in retained_source_keys
            ):
                continue
            key = (*source_key, entry["manifest_entry_sha256"])
            attestation = attestations.get(key)
            if attestation is None:
                raise GateError(
                    "curation manifest lacks source-original attestation for retained "
                    f"identity entry {source_key[0]}:{source_key[1]}"
                )
            entry["_source_originals_sha256"] = attestation
            restored.add(key)
    if restored != set(attestations):
        raise GateError("curation manifest has orphan retained identity attestations")


def verify_lane_evidence(
    cleaned: Path,
    manifest: dict[str, Any],
    view: RetentionView = RetentionView(),
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Rebuild lane decisions only from the sealed copies in ``cleaned``."""
    retained_source_keys = view.retained_source_keys
    raw_evidence = manifest.get("lane_evidence")
    if not isinstance(raw_evidence, list) or len(raw_evidence) != len(REQUIRED_LANES):
        raise GateError("curation manifest needs evidence for all six lanes")

    tally = _GovernanceTally(set(), [])
    expected_files = tally.files
    expected_governance_outputs = tally.outputs
    prepared: list[dict[str, Any]] = []
    declared: list[tuple[Any, Any]] = []
    for index, evidence in enumerate(raw_evidence, 1):
        lane, contract = _verify_lane_evidence_row(cleaned, index, evidence, tally)
        prepared.append(lane)
        declared.append(contract)

    if tuple(declared) != REQUIRED_LANES:
        raise GateError("lane evidence does not match the six required contracts in order")
    _assert_governance_file_set(cleaned, expected_files)
    if manifest.get("governance_outputs") != expected_governance_outputs:
        raise GateError("governance_outputs metadata does not match copied evidence bytes")

    attestations = _identity_attestations(manifest)
    _restore_identity_attestations(prepared, attestations, retained_source_keys)
    return prepared, collect_lane_manifests(
        prepared,
        view.retained_source_keys,
        view.source_record_sha256_by_key,
    )


if __package__:
    _expose_package_sibling(__name__)
