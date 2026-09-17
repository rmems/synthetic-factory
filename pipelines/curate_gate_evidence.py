#!/usr/bin/env python3
"""Governance-evidence loading for the curation gate.

Split out of ``curate_gate.py`` (CodeScene: Lines of Code in a Single File) by
responsibility; every name is re-exported from ``curate_gate`` so existing
``curate_gate.X`` call sites resolve unchanged.

The reward lane pairs its outputs with a ``reward_source_sidecars`` JSONL
artifact. This module parses that artifact from captured bytes and validates
every document against the reward ontology before the lane is admitted.

It also seals that evidence: ``copy_lane_evidence`` writes every authenticated
lane manifest and reward artifact into the cleaned tree's governance directory
and re-hashes each copy. The other half of the round trip -- rebuilding the
lane decisions from nothing but those sealed copies -- lives in
``curate_gate_evidence_verify``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Sequence

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("curate_gate_evidence")
    from . import curate_gate_contract as _contract
    from . import curate_gate_digest as _digest
    from . import curate_gate_paths as _paths
    from . import curate_rewards
    from .check_records import reject_json_constant
    from .exact_json import parse_finite_json_float
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "curate_gate_evidence"
    )
    _PIPELINES = Path(__file__).resolve().parent
    if str(_PIPELINES) not in sys.path:
        sys.path.insert(0, str(_PIPELINES))
    import curate_gate_contract as _contract
    import curate_gate_digest as _digest
    import curate_gate_paths as _paths
    import curate_rewards
    from check_records import reject_json_constant
    from exact_json import parse_finite_json_float

GateError = _contract.GateError
GOVERNANCE_DIRNAME = _contract.GOVERNANCE_DIRNAME
LANE_MANIFEST_DIRNAME = _contract.LANE_MANIFEST_DIRNAME
REWARD_CALIBRATION_DIRNAME = _contract.REWARD_CALIBRATION_DIRNAME
REWARD_CALIBRATION_KIND = _contract.REWARD_CALIBRATION_KIND
REWARD_SIDECAR_DIRNAME = _contract.REWARD_SIDECAR_DIRNAME
file_sha256 = _digest.file_sha256
_lf_lines = _digest._lf_lines
_read_regular_file_snapshot = _digest._read_regular_file_snapshot
_assert_no_symlink = _paths._assert_no_symlink
_relative_artifact_destination = _paths._relative_artifact_destination


def _load_reward_sidecars(
    path: Path,
    *,
    payload: bytes | None = None,
) -> list[dict[str, Any]]:
    documents: list[dict[str, Any]] = []
    if payload is None:
        payload, _digest, _size = _read_regular_file_snapshot(path, "reward sidecars")
    try:
        text = payload.decode("utf-8")
    except UnicodeError as exc:
        raise GateError(f"cannot decode reward sidecars {path}: {exc}") from exc
    for line_number, line in enumerate(_lf_lines(text), 1):
        if not line.strip():
            continue
        try:
            document = json.loads(
                line,
                parse_constant=reject_json_constant,
                parse_float=parse_finite_json_float,
            )
        except ValueError as exc:
            raise GateError(f"{path}:{line_number}: invalid reward sidecar JSON: {exc}") from exc
        if (
            not isinstance(document, dict)
            or document.get("document_type") != "reward_source_sidecar"
        ):
            raise GateError(f"{path}:{line_number}: expected a reward_source_sidecar document")
        try:
            curate_rewards.validate_ontology_document(document)
        except curate_rewards.RewardOntologyError as exc:
            raise GateError(f"{path}:{line_number}: invalid reward sidecar: {exc}") from exc
        documents.append(document)
    if not documents:
        raise GateError(f"{path}: reward sidecar artifact is empty")
    ids = [document["sidecar_id"] for document in documents]
    if len(ids) != len(set(ids)):
        raise GateError(f"{path}: duplicate reward sidecar_id")
    return documents


# ---------------------------------------------------------------------------
# sealing authenticated lane evidence into the cleaned governance tree
# ---------------------------------------------------------------------------


def _copy_lane_manifest_evidence(
    lane: dict[str, Any], destination: Path, lane_token: str
) -> dict[str, Any]:
    manifest_relative = (
        Path(GOVERNANCE_DIRNAME)
        / LANE_MANIFEST_DIRNAME
        / lane_token
        / f"manifest{lane['manifest_path'].suffix}.evidence"
    )
    manifest_target = destination / manifest_relative
    manifest_target.parent.mkdir(parents=True, exist_ok=True)
    manifest_target.write_bytes(lane["manifest_payload"])
    if file_sha256(manifest_target) != lane["manifest_sha256"]:
        raise GateError(f"lane manifest copy hash mismatch: {lane['manifest_path']}")
    return {
        "path": manifest_relative.as_posix(),
        "sha256": lane["manifest_sha256"],
        "bytes": lane["manifest_bytes"],
        "format": lane["manifest_format"],
    }


def _copy_lane_artifact(
    artifact: dict[str, Any], destination: Path, lane_token: str
) -> dict[str, Any]:
    artifact_relative = (
        Path(GOVERNANCE_DIRNAME)
        / (
            REWARD_CALIBRATION_DIRNAME
            if artifact["kind"] == REWARD_CALIBRATION_KIND
            else REWARD_SIDECAR_DIRNAME
        )
        / lane_token
        / f"{artifact['destination']}.evidence"
    )
    target = destination / artifact_relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(artifact["_payload"])
    digest = artifact["_sha256"]
    if file_sha256(target) != digest:
        raise GateError(f"governance artifact copy hash mismatch: {artifact['source_path']}")
    return {
        "kind": artifact["kind"],
        "path": artifact_relative.as_posix(),
        "sha256": digest,
        "bytes": artifact["_bytes"],
        "documents": artifact["_documents"],
    }


def copy_lane_evidence(
    prepared_lanes: Sequence[dict[str, Any]], destination: Path
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Copy authenticated manifests/artifacts into the cleaned governance tree."""
    lane_evidence: list[dict[str, Any]] = []
    governance_outputs: list[dict[str, Any]] = []
    for lane in prepared_lanes:
        lane_token = f"{lane['order']:02d}"
        manifest_evidence = _copy_lane_manifest_evidence(lane, destination, lane_token)
        governance_outputs.append({**manifest_evidence, "kind": "lane_manifest"})

        artifact_evidence: list[dict[str, Any]] = []
        for artifact in lane["artifacts"]:
            evidence = _copy_lane_artifact(artifact, destination, lane_token)
            artifact_evidence.append(evidence)
            governance_outputs.append(evidence)

        lane_evidence.append(
            {
                "lane_order": lane["order"],
                "bead": lane["bead"],
                "transform": lane["transform"],
                "version": lane["version"],
                "manifest": manifest_evidence,
                "artifacts": artifact_evidence,
            }
        )
    return lane_evidence, governance_outputs


def _evidence_file(cleaned: Path, value: Any, label: str) -> Path:
    relative = _relative_artifact_destination(value, label)
    path = cleaned / relative
    if not path.is_file():
        raise GateError(f"{label} is missing: {path}")
    _assert_no_symlink(cleaned, path, label)
    return path


if __package__:
    _expose_package_sibling(__name__)
