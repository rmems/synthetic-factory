#!/usr/bin/env python3
"""Integration-plan loading for the curation gate.

Split out of ``curate_gate.py`` (CodeScene: Lines of Code in a Single File) by
responsibility; ``load_plan`` is re-exported from ``curate_gate`` so existing
``curate_gate.load_plan`` call sites resolve unchanged.

The plan is the reviewable record of which lane produced a corpus, so it is
captured once as bytes and every field below is read from that one capture --
a plan rewritten mid-load cannot change what the manifest later claims. Each
declaration is resolved by a single-responsibility helper that owns its own
refusals, in the order the plan declares them.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("curate_gate_plan")
    from . import curate_gate_contract as _contract
    from . import curate_gate_digest as _digest
    from . import curate_gate_paths as _paths
    from .check_records import reject_json_constant
    from .exact_json import parse_finite_json_float
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "curate_gate_plan"
    )
    _PIPELINES = Path(__file__).resolve().parent
    if str(_PIPELINES) not in sys.path:
        sys.path.insert(0, str(_PIPELINES))
    import curate_gate_contract as _contract
    import curate_gate_digest as _digest
    import curate_gate_paths as _paths
    from check_records import reject_json_constant
    from exact_json import parse_finite_json_float

PLAN_SCHEMA = _contract.PLAN_SCHEMA
REQUIRED_LANES = _contract.REQUIRED_LANES
REWARD_ARTIFACT_KINDS = _contract.REWARD_ARTIFACT_KINDS
REWARD_SIDECAR_KIND = _contract.REWARD_SIDECAR_KIND
GateError = _contract.GateError
_read_regular_file_snapshot = _digest._read_regular_file_snapshot
_lane_manifest_format = _paths._lane_manifest_format
_relative_artifact_destination = _paths._relative_artifact_destination
_resolve_declared_path = _paths._resolve_declared_path
_resolve_source_run_path = _paths._resolve_source_run_path

# Every lane declaration needs these three as non-empty strings, in this order.
_LANE_STRING_FIELDS = ("transform", "version", "outputs")


def _lane_label(plan_path: Path, index: int, transform: Any) -> str:
    return f"{plan_path}: lane {index} ({transform})"


def _plan_snapshot(plan_path: Path) -> tuple[dict[str, Any], str]:
    """Capture the plan once and parse those exact bytes."""
    payload, plan_sha256, _plan_size = _read_regular_file_snapshot(plan_path, "integration plan")
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise GateError(f"{plan_path}: integration plan is not UTF-8: {exc}") from exc
    try:
        plan = json.loads(
            text,
            parse_constant=reject_json_constant,
            parse_float=parse_finite_json_float,
        )
    # ``JSONDecodeError`` is a ``ValueError``, as is the refusal raised by the
    # exact-JSON float hook, so one clause covers both without widening it.
    except ValueError as exc:
        raise GateError(f"{plan_path}: invalid JSON: {exc}") from exc
    if not isinstance(plan, dict):
        raise GateError(f"{plan_path}: plan must be a JSON object")
    schema = plan.get("schema")
    if schema is not None and schema != PLAN_SCHEMA:
        raise GateError(f"{plan_path}: unsupported plan schema {schema!r}")
    return plan, plan_sha256


def _plan_source_run(
    plan: dict[str, Any],
    plan_path: Path,
    base: Path,
    repo_root: Path,
    raw_output_root: Path,
) -> tuple[str, Path]:
    """The immutable source tree the lanes were derived from."""
    source_run = plan.get("source_run")
    if not isinstance(source_run, str) or not source_run.strip():
        raise GateError(f"{plan_path}: plan needs a non-empty string 'source_run'")
    source_run_dir = _resolve_source_run_path(
        base,
        source_run,
        f"{plan_path}: source_run",
        repo_root,
        raw_output_root,
    )
    if not source_run_dir.is_dir():
        raise GateError(f"{plan_path}: source_run directory is missing: {source_run_dir}")
    return source_run, source_run_dir


def _lane_declaration(
    plan_path: Path,
    index: int,
    lane: Any,
    versions: dict[str, str],
) -> tuple[str, str, str]:
    """The three required strings, with one version per transform."""
    if not isinstance(lane, dict):
        raise GateError(f"{plan_path}: lane {index} must be an object")
    declared = tuple(lane.get(field) for field in _LANE_STRING_FIELDS)
    for field, value in zip(_LANE_STRING_FIELDS, declared):
        if not isinstance(value, str) or not value.strip():
            raise GateError(f"{plan_path}: lane {index} needs a non-empty string '{field}'")
    transform, version, outputs = declared
    previous = versions.get(transform)
    if previous is not None and previous != version:
        raise GateError(
            f"{plan_path}: transform {transform!r} declared at two versions "
            f"({previous!r} and {version!r})"
        )
    versions[transform] = version
    return transform, version, outputs


def _lane_outputs_dir(
    plan_path: Path,
    base: Path,
    index: int,
    transform: str,
    outputs: str,
    seen_outputs: dict[Path, str],
) -> Path:
    """One lane's curated output tree, which no other lane may reuse."""
    label = _lane_label(plan_path, index, transform)
    outputs_path = _resolve_declared_path(base, outputs, f"{label} outputs")
    if not outputs_path.is_dir():
        raise GateError(f"{label} outputs directory is missing: {outputs_path}")
    if outputs_path in seen_outputs:
        raise GateError(
            f"{label} reuses the outputs directory of "
            f"lane {seen_outputs[outputs_path]}: {outputs_path}"
        )
    seen_outputs[outputs_path] = f"{index} ({transform})"
    return outputs_path


def _lane_manifest(
    plan_path: Path,
    base: Path,
    index: int,
    transform: str,
    lane: dict[str, Any],
) -> tuple[Path, str]:
    """The record-level manifest every lane must pair with its outputs."""
    label = _lane_label(plan_path, index, transform)
    manifest = lane.get("manifest")
    if not isinstance(manifest, str) or not manifest.strip():
        raise GateError(f"{label} needs a non-empty string 'manifest'")
    manifest_path = _resolve_declared_path(base, manifest, f"{label} manifest")
    if not manifest_path.is_file():
        raise GateError(f"{label} manifest is missing: {manifest_path}")
    manifest_format = _lane_manifest_format(manifest_path, f"{label} manifest")
    return manifest_path, manifest_format


def _lane_artifact(
    base: Path,
    artifact: Any,
    label: str,
    manifest_path: Path,
) -> dict[str, Any]:
    """One declared sidecar or calibration artifact, resolved and confined."""
    if not isinstance(artifact, dict):
        raise GateError(f"{label} must be an object")
    kind = artifact.get("kind")
    if kind not in REWARD_ARTIFACT_KINDS:
        raise GateError(f"{label} has unsupported kind {kind!r}")
    value = artifact.get("path")
    if not isinstance(value, str) or not value.strip():
        raise GateError(f"{label} path must be a non-empty string")
    artifact_path = _resolve_declared_path(base, value, f"{label} path")
    if not artifact_path.is_file():
        raise GateError(f"{label} is missing: {artifact_path}")
    if artifact_path == manifest_path:
        raise GateError(f"{label} cannot reuse the lane manifest")
    destination_name = artifact.get("destination", artifact_path.name)
    destination = _relative_artifact_destination(destination_name, f"{label} destination")
    return {
        "kind": kind,
        "source_path": artifact_path,
        "destination": destination,
    }


def _lane_artifacts(
    plan_path: Path,
    base: Path,
    index: int,
    transform: str,
    lane: dict[str, Any],
    manifest_path: Path,
) -> list[dict[str, Any]]:
    """Every artifact this lane declares, each at its own destination."""
    prefix = _lane_label(plan_path, index, transform)
    raw_artifacts = lane.get("artifacts", [])
    if not isinstance(raw_artifacts, list):
        raise GateError(f"{prefix} artifacts must be a list")
    artifacts: list[dict[str, Any]] = []
    destinations: set[Path] = set()
    for artifact_index, artifact in enumerate(raw_artifacts, 1):
        label = f"{prefix} artifact {artifact_index}"
        resolved = _lane_artifact(base, artifact, label, manifest_path)
        destination = resolved["destination"]
        if destination in destinations:
            raise GateError(f"{label} reuses artifact destination {destination}")
        destinations.add(destination)
        artifacts.append(resolved)
    return artifacts


def _resolve_lane(
    plan_path: Path,
    base: Path,
    index: int,
    lane: Any,
    versions: dict[str, str],
    seen_outputs: dict[Path, str],
) -> dict[str, Any]:
    """One fully resolved lane declaration."""
    transform, version, outputs = _lane_declaration(plan_path, index, lane, versions)
    outputs_path = _lane_outputs_dir(plan_path, base, index, transform, outputs, seen_outputs)
    manifest_path, manifest_format = _lane_manifest(plan_path, base, index, transform, lane)
    artifacts = _lane_artifacts(plan_path, base, index, transform, lane, manifest_path)
    return {
        "order": index,
        "bead": lane.get("bead"),
        "transform": transform,
        "version": version,
        "outputs_dir": outputs_path,
        "manifest_path": manifest_path,
        "manifest_format": manifest_format,
        "artifacts": artifacts,
    }


def _resolve_lanes(
    plan_path: Path,
    base: Path,
    lanes: list[Any],
) -> tuple[list[dict[str, Any]], dict[str, str]]:
    """Resolve every lane in declaration order, refusing the first bad one."""
    resolved: list[dict[str, Any]] = []
    versions: dict[str, str] = {}
    seen_outputs: dict[Path, str] = {}
    for index, lane in enumerate(lanes, 1):
        resolved.append(_resolve_lane(plan_path, base, index, lane, versions, seen_outputs))
    return resolved, versions


def _assert_lane_contracts(plan_path: Path, resolved: list[dict[str, Any]]) -> None:
    """The six reviewed contracts, in order, with reward evidence declared."""
    declared_lanes = tuple((lane["bead"], lane["transform"]) for lane in resolved)
    if declared_lanes != REQUIRED_LANES:
        expected = ", ".join(f"{bead}:{transform}" for bead, transform in REQUIRED_LANES)
        actual = ", ".join(f"{bead}:{transform}" for bead, transform in declared_lanes)
        raise GateError(
            f"{plan_path}: lanes must be the six required contracts in order; "
            f"expected [{expected}], got [{actual}]"
        )

    reward_lane = next(lane for lane in resolved if lane["transform"] == "reward_ontology")
    if not reward_lane["artifacts"]:
        raise GateError(
            f"{plan_path}: reward_ontology must declare at least one "
            f"{REWARD_SIDECAR_KIND!r} artifact"
        )


def load_plan(plan_path: Path, *, repo_root: Path, raw_output_root: Path) -> dict[str, Any]:
    """Read and validate an integration plan; resolve its lane paths."""
    plan_path = Path(plan_path).resolve()
    plan, plan_sha256 = _plan_snapshot(plan_path)
    base = plan_path.parent
    source_run, source_run_dir = _plan_source_run(
        plan,
        plan_path,
        base,
        repo_root,
        raw_output_root,
    )

    lanes = plan.get("lanes")
    if not isinstance(lanes, list) or not lanes:
        raise GateError(f"{plan_path}: plan needs a non-empty 'lanes' list")

    resolved, versions = _resolve_lanes(plan_path, base, lanes)
    _assert_lane_contracts(plan_path, resolved)

    return {
        "plan_path": plan_path,
        "plan_sha256": plan_sha256,
        "source_run": source_run,
        "source_run_dir": source_run_dir,
        "lanes": resolved,
        "transform_versions": dict(sorted(versions.items())),
    }


if __package__:
    _expose_package_sibling(__name__)
