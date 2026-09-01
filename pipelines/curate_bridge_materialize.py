#!/usr/bin/env python3
"""Atomic, fail-closed materialization for curated Bridge decisions."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Sequence


from curate_bridge_materialize_fs import (
    BridgeCurationError,
    _is_under_raw,
    _manifest_path,
    _materialization_sources,
    _rename_linux as _fs_rename_linux,
    _rename_noreplace,
    _rename_windows as _fs_rename_windows,
    _safe_relative_path,
    _symlinked_ancestor,
    _unsafe_relative_path as _fs_unsafe_relative_path,
    _write_exclusive,
)

# Compatibility exports used by focused atomic-publication tests.
_rename_linux = _fs_rename_linux
_rename_windows = _fs_rename_windows
_unsafe_relative_path = _fs_unsafe_relative_path


@dataclass(frozen=True)
class MaterializationConfig:
    """Inputs that define one immutable materialized Bridge tree."""

    source_root: str | Path
    output_dir: str | Path
    manifest_name: str
    require_raster: bool
    require_routing_table: bool = True


@dataclass(frozen=True)
class MaterializationContext:
    """Curation-specific operations used by the generic tree publisher."""

    canonical_json_bytes: Callable[[Any], bytes]
    canonical_json_line: Callable[[Any], bytes]
    curate_paths: Callable[..., list[Any]]
    parse_json_float: Callable[[str], float]
    reject_json_constant: Callable[[str], None]
    sha256_hex: Callable[[bytes], str]


def _read_manifest(path: Path, context: MaterializationContext) -> list[Any]:
    try:
        document = json.loads(
            path.read_bytes().decode("utf-8"),
            parse_constant=context.reject_json_constant,
            parse_float=context.parse_json_float,
        )
    except (OSError, ValueError) as exc:
        raise BridgeCurationError(f"invalid staged Bridge manifest: {exc}") from exc
    if not isinstance(document, list):
        raise BridgeCurationError("invalid staged Bridge manifest: expected a JSON array")
    return document


def _expected_outputs(decisions: Sequence[Any]) -> dict[str, list[str]]:
    expected: dict[str, list[str]] = {}
    for decision in decisions:
        if decision.output_record is None:
            continue
        expected.setdefault(decision.manifest["source_path"], []).append(
            decision.manifest["output_hash"]
        )
    return expected


def _actual_outputs(root: Path, manifest_path: Path) -> dict[str, Path]:
    actual: dict[str, Path] = {}
    for path in sorted(root.rglob("*.jsonl")):
        if not path.is_file():
            continue
        if path == manifest_path:
            continue
        actual[path.relative_to(root).as_posix()] = path
    return actual


def _read_output_hashes(
    path: Path,
    relative: str,
    context: MaterializationContext,
) -> list[str]:
    hashes: list[str] = []
    for line in path.read_bytes().split(b"\n"):
        if not line.strip():
            continue
        try:
            record = json.loads(
                line.decode("utf-8"),
                parse_constant=context.reject_json_constant,
                parse_float=context.parse_json_float,
            )
        except ValueError as exc:
            raise BridgeCurationError(f"invalid staged Bridge output {relative}: {exc}") from exc
        hashes.append(context.sha256_hex(context.canonical_json_bytes(record)))
    return hashes


def _validate_output_paths(actual: dict[str, Path], expected: dict[str, list[str]]) -> None:
    if set(actual) == set(expected):
        return
    raise BridgeCurationError(
        "staged Bridge output paths differ from manifest: "
        f"expected={sorted(expected)}, actual={sorted(actual)}"
    )


def _validate_output_hashes(
    actual: dict[str, Path],
    expected: dict[str, list[str]],
    context: MaterializationContext,
) -> None:
    for relative, expected_hashes in sorted(expected.items()):
        actual_hashes = _read_output_hashes(actual[relative], relative, context)
        if actual_hashes != expected_hashes:
            raise BridgeCurationError(
                f"staged Bridge output hashes differ from manifest: {relative}"
            )


def _validate_materialized_tree(
    root: Path,
    decisions: Sequence[Any],
    manifest_relative: Path,
    context: MaterializationContext,
) -> None:
    """Authenticate staged output records and manifest before publication."""

    manifest_path = root / manifest_relative
    manifest_lines = _read_manifest(manifest_path, context)
    expected_manifest = [decision.manifest for decision in decisions]
    if manifest_lines != expected_manifest:
        raise BridgeCurationError("staged Bridge manifest differs from decisions")
    expected = _expected_outputs(decisions)
    actual = _actual_outputs(root, manifest_path)
    _validate_output_paths(actual, expected)
    _validate_output_hashes(actual, expected, context)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise BridgeCurationError(message)


def _materialization_roots(
    source_root: str | Path,
    output_dir: str | Path,
) -> tuple[Path, Path, Path]:
    root = Path(source_root)
    destination = Path(output_dir)
    _require(root.is_dir(), f"source_root must be a real directory: {root}")
    _require(not root.is_symlink(), f"source_root must be a real directory: {root}")
    _require(
        not os.path.lexists(destination),
        f"destination already exists; refusing overwrite: {destination}",
    )
    _require(
        destination.parent.is_dir(),
        f"destination parent must be a real directory: {destination.parent}",
    )
    _require(
        not destination.parent.is_symlink(),
        f"destination parent must be a real directory: {destination.parent}",
    )
    linked_ancestor = _symlinked_ancestor(destination.parent)
    _require(
        linked_ancestor is None,
        f"destination parent has a symlinked ancestor: {linked_ancestor}",
    )
    _require(
        not _is_under_raw(destination),
        f"refusing to write inside immutable raw evidence: {destination}",
    )
    root_resolved = root.resolve(strict=True)
    destination_resolved = destination.resolve(strict=False)
    if destination_resolved == root_resolved:
        raise BridgeCurationError(f"destination cannot be inside source_root: {destination}")
    if root_resolved in destination_resolved.parents:
        raise BridgeCurationError(f"destination cannot be inside source_root: {destination}")
    return root, destination, root_resolved


def _records_by_path(decisions: Sequence[Any]) -> dict[Path, list[dict[str, Any]]]:
    by_path: dict[Path, list[dict[str, Any]]] = {}
    for decision in decisions:
        if decision.output_record is None:
            continue
        relative = _safe_relative_path(
            decision.manifest["source_path"],
            label="manifest source_path",
        )
        by_path.setdefault(relative, []).append(decision.output_record)
    return by_path


def _write_outputs(
    staged: Path,
    by_path: dict[Path, list[dict[str, Any]]],
    context: MaterializationContext,
) -> None:
    for relative, records in sorted(by_path.items(), key=lambda item: item[0].as_posix()):
        target = staged / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = b"".join(context.canonical_json_line(record) for record in records)
        _write_exclusive(target, payload)


def _write_materialized_tree(
    staged: Path,
    decisions: Sequence[Any],
    manifest_relative: Path,
    context: MaterializationContext,
) -> None:
    _write_outputs(staged, _records_by_path(decisions), context)
    manifest_path = staged / manifest_relative
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    payload = context.canonical_json_bytes([item.manifest for item in decisions]) + b"\n"
    _write_exclusive(manifest_path, payload)


def _publish_materialized_tree(
    destination: Path,
    decisions: Sequence[Any],
    manifest_relative: Path,
    context: MaterializationContext,
) -> None:
    stage_root = Path(
        tempfile.mkdtemp(prefix=f".{destination.name}.staging-", dir=destination.parent)
    )
    staged = stage_root / "tree"
    try:
        staged.mkdir()
        _write_materialized_tree(staged, decisions, manifest_relative, context)
        _validate_materialized_tree(staged, decisions, manifest_relative, context)
        _rename_noreplace(staged, destination)
    finally:
        shutil.rmtree(stage_root, ignore_errors=True)


def _output_paths(decisions: Sequence[Any]) -> set[Path]:
    return {
        _safe_relative_path(decision.manifest["source_path"], label="manifest source_path")
        for decision in decisions
        if decision.output_record is not None
    }


def _materialized_raster_evidence(decision: Any) -> dict[str, Any] | None:
    if decision.output_record is None:
        return None
    evidence = decision.manifest.get("evidence")
    if not isinstance(evidence, dict):
        return None
    raster = evidence.get("raster")
    if not isinstance(raster, dict) or not raster.get("raster_present"):
        return None
    return raster


def _require_batch_gate_coverage(decisions: Sequence[Any]) -> None:
    covered: dict[str, bool] = {}
    for decision in decisions:
        evidence = _materialized_raster_evidence(decision)
        if evidence is None:
            continue
        source_path = decision.manifest["source_path"]
        covered[source_path] = covered.get(source_path, False) or bool(
            evidence.get("gate_snn_valid")
        )
    missing = sorted(path for path, has_gate in covered.items() if not has_gate)
    if missing:
        raise BridgeCurationError(
            "materialized raster-backed source batches require at least one valid "
            f"spike-implemented gate: {missing}"
        )


def materialize_paths(
    sources: Iterable[str | Path],
    config: MaterializationConfig,
    context: MaterializationContext,
) -> list[Any]:
    """Publish one atomically validated, gate-compatible Bridge lane tree."""

    _require(
        config.require_raster is True,
        "materialize_paths require_raster contract cannot be disabled",
    )
    root, destination, root_resolved = _materialization_roots(
        config.source_root,
        config.output_dir,
    )
    source_paths = list(map(Path, sources))
    if not source_paths:
        raise BridgeCurationError("at least one Bridge JSONL source is required")
    source_paths = _materialization_sources(source_paths, root_resolved)
    decisions = context.curate_paths(
        source_paths,
        source_root=root,
        require_raster=config.require_raster,
        require_routing_table=config.require_routing_table,
    )
    _require_batch_gate_coverage(decisions)
    manifest_relative = _manifest_path(config.manifest_name)
    if manifest_relative in _output_paths(decisions):
        raise BridgeCurationError(
            f"manifest path collides with a curated output: {manifest_relative}"
        )
    _publish_materialized_tree(destination, decisions, manifest_relative, context)
    return decisions
