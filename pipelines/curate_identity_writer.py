#!/usr/bin/env python3
"""Committed source iteration and the exclusive identity-tree writer.

Split out of ``curate_identity.py`` (CodeScene: Lines of Code in a Single
File) by responsibility; every name is re-exported from ``curate_identity``
so existing ``curate_identity.X`` call sites and test seams resolve
unchanged.

Source iteration yields only committed JSONL coordinates: symlinked entries,
uncommitted transaction payloads, and undecodable lines are refused rather
than skipped silently.  The writer targets a brand-new destination, pins the
reviewed registry and manifest bytes, replays validation immediately, and
rolls back the partial tree on any failure.  The facade supplies its live
``write_exclusive``, ``iter_source_records``, ``curate_records``, and
``validate_identity_tree`` seams per call.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("curate_identity_writer")
    from . import curate_identity_checks as _identity_checks
    from . import curate_identity_json as _identity_json
    from . import curate_identity_registry as _identity_registry
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "curate_identity_writer"
    )
    import curate_identity_checks as _identity_checks
    import curate_identity_json as _identity_json
    import curate_identity_registry as _identity_registry

IdentityCurationError = _identity_json.IdentityCurationError


def _fail(error: IdentityCurationError) -> None:
    """Raise ``error``; one raise site keeps fail-closed checks branch-light."""

    raise error


FACTORY_REGISTRY_SIDECAR = "FACTORY-REGISTRY.json"
IDENTITY_MANIFEST_SIDECAR = "IDENTITY-MANIFEST.json"
HOSTED_REGISTRY_SCHEMA_VERSION = _identity_registry.HOSTED_REGISTRY_SCHEMA_VERSION
REGISTRY_SCHEMA_VERSION = _identity_registry.REGISTRY_SCHEMA_VERSION


@dataclass(frozen=True)
class WriterDependencies:
    """Live facade operations used while writing an identity tree."""

    write_exclusive: Callable[[Path, bytes], None]
    validate_identity_tree: Callable[..., Any]
    iter_source_records: Callable[..., Any]
    curate_records: Callable[..., Any]
    check_dependencies: Callable[[], Any]
    default_registry: Callable[[], Any]
    strict_json_loads: Callable[..., Any]
    is_json_whitespace: Callable[[str], bool]


def is_under_raw(path: Path) -> bool:
    parts = path.resolve(strict=False).parts
    return any(
        parts[index : index + 2] == ("outputs", "raw")
        for index in range(len(parts) - 1)
    )


def write_exclusive(path: Path, payload: bytes) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    try:
        try:
            handle = os.fdopen(descriptor, "wb")
        except BaseException:
            os.close(descriptor)
            raise
        with handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        # Fsync parent directory to ensure durable directory entry
        parent_descriptor = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(parent_descriptor)
        finally:
            os.close(parent_descriptor)
    except BaseException:
        path.unlink(missing_ok=True)
        raise


def ensure_output_directory(
    root: Path,
    directory: Path,
    created_directories: list[Path],
) -> None:
    current = root
    for part in directory.relative_to(root).parts:
        current /= part
        try:
            current.mkdir()
        except FileExistsError:
            if current.is_symlink() or not current.is_dir():
                _fail(IdentityCurationError(
                    f"identity output parent is not a directory: {current}"
                ))
        else:
            created_directories.append(current)


def _require_writer_registry(registry) -> None:
    supported = {HOSTED_REGISTRY_SCHEMA_VERSION, REGISTRY_SCHEMA_VERSION}
    if registry.schema_version not in supported:
        _fail(IdentityCurationError(
            f"write_run requires {HOSTED_REGISTRY_SCHEMA_VERSION} or "
            f"{REGISTRY_SCHEMA_VERSION} registry bytes"
        ))


def _identity_manifest_bytes(results) -> bytes:
    return (
        json.dumps(
            [result.mapping for result in results],
            ensure_ascii=False,
            allow_nan=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


@dataclass
class _CreatedPaths:
    """Files and directories the writer must roll back on failure."""

    files: list[Path]
    directories: list[Path]


def _write_identity_outputs(
    dest: Path,
    results,
    deps: WriterDependencies,
    created: _CreatedPaths,
) -> None:
    retained_by_rel = _identity_checks.retained_source_lines(
        results, deps.check_dependencies()
    )
    for rel, records_by_line in sorted(retained_by_rel.items()):
        out_path = dest / rel
        ensure_output_directory(dest, out_path.parent, created.directories)
        output_lines = [""] * max(records_by_line)
        for line_no, record_json in records_by_line.items():
            output_lines[line_no - 1] = record_json
        payload = "\n".join(output_lines) + "\n"
        deps.write_exclusive(out_path, payload.encode("utf-8"))
        created.files.append(out_path)


def write_run(
    source: Path, dest: Path, registry, deps: WriterDependencies
) -> tuple:
    """Curate a source tree into a new destination with identity sidecars."""

    source = Path(source)
    dest = Path(dest)
    if dest.exists():
        _fail(IdentityCurationError(f"destination already exists: {dest}"))
    if is_under_raw(dest):
        _fail(IdentityCurationError(
            f"refusing to write inside immutable raw evidence: {dest}"
        ))
    registry = deps.default_registry() if registry is None else registry
    _require_writer_registry(registry)
    results = deps.curate_records(
        deps.iter_source_records(source, registry=registry),
        registry=registry,
    )
    created = _CreatedPaths(files=[], directories=[])
    destination_created = False
    try:
        dest.mkdir(parents=True, exist_ok=False)
        destination_created = True
        deps.write_exclusive(dest / FACTORY_REGISTRY_SIDECAR, registry.raw_bytes)
        created.files.append(dest / FACTORY_REGISTRY_SIDECAR)
        manifest_bytes = _identity_manifest_bytes(results)
        manifest_digest = _identity_checks.sha256_bytes(manifest_bytes)
        deps.write_exclusive(dest / IDENTITY_MANIFEST_SIDECAR, manifest_bytes)
        created.files.append(dest / IDENTITY_MANIFEST_SIDECAR)
        _write_identity_outputs(dest, results, deps, created)
        deps.validate_identity_tree(
            dest,
            expected_registry_digest=registry.sha256,
            expected_manifest_digest=manifest_digest,
        )
    except BaseException:
        if destination_created:
            _identity_checks.rollback_identity_tree(
                dest, created.files, created.directories
            )
        raise
    return results


if __package__:
    _expose_package_sibling(__name__)
