#!/usr/bin/env python3
"""Manifest replay and whole-tree validation for written identity trees.

Split out of ``curate_identity.py`` (CodeScene: Lines of Code in a Single
File) by responsibility; every name is re-exported from ``curate_identity``
so existing ``curate_identity.X`` call sites and test seams resolve
unchanged.

Validation replays every manifest entry from its hash-verified source
snapshot before trusting the declared action, then proves the written JSONL
outputs match the replayed bytes, coordinates, and identities.  The facade
supplies its live ``source_identity``, ``curate_record``, and
``replay_manifest_mapping`` seams per call.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("curate_identity_tree")
    from . import curate_identity_checks as _identity_checks
    from . import curate_identity_evidence as _evidence
    from . import curate_identity_json as _identity_json
    from . import curate_identity_manifest as _manifest
    from . import curate_identity_output as _identity_output
    from . import curate_identity_registry as _identity_registry
    from . import curate_identity_sources as _sources
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "curate_identity_tree"
    )
    import curate_identity_checks as _identity_checks
    import curate_identity_evidence as _evidence
    import curate_identity_json as _identity_json
    import curate_identity_manifest as _manifest
    import curate_identity_output as _identity_output
    import curate_identity_registry as _identity_registry
    import curate_identity_sources as _sources

IdentityCurationError = _identity_json.IdentityCurationError
IdentityTreeError = _identity_json.IdentityTreeError

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
PRESERVED_KINDS = _sources.PRESERVED_KINDS
FACTORY_REGISTRY_SIDECAR = "FACTORY-REGISTRY.json"
IDENTITY_MANIFEST_SIDECAR = "IDENTITY-MANIFEST.json"


@dataclass(frozen=True)
class TreeDependencies:
    """Live facade operations used while replaying and validating a tree."""

    source_identity: Callable[..., Any]
    curate_record: Callable[..., Any]
    replay_manifest_mapping: Callable[..., Any]
    resolve_provenance: Callable[..., Any]
    check_dependencies: Callable[[], Any]
    strict_json_loads: Callable[..., Any]
    is_json_whitespace: Callable[[str], bool]
    canonical_json: Callable[[Any], str]
    sha256_bytes: Callable[[bytes], str]


@dataclass(frozen=True)
class ManifestReplay:
    source: Any
    result: Any


def _output_dependencies(deps: TreeDependencies):
    return _identity_output.IdentityOutputDependencies(
        canonical_json=deps.canonical_json,
        identity_curation_error=IdentityCurationError,
        identity_tree_error=IdentityTreeError,
        replay_manifest_mapping=deps.replay_manifest_mapping,
        sha256_pattern=SHA256_RE,
        strict_json_loads=deps.strict_json_loads,
    )


def _manifest_dependencies(deps: TreeDependencies):
    return _evidence.ManifestDependencies(
        resolve_provenance=deps.resolve_provenance,
        check_dependencies=deps.check_dependencies,
        strict_json_loads=deps.strict_json_loads,
        is_json_whitespace=deps.is_json_whitespace,
        canonical_json=deps.canonical_json,
        sha256_bytes=deps.sha256_bytes,
    )


def _replay_source_record(
    mapping: Mapping[str, Any], index: int, registry, deps: TreeDependencies
) -> ManifestReplay:
    """Rebuild the identity decision from the hash-verified source snapshot."""

    source_meta = mapping.get("source")
    if not isinstance(source_meta, Mapping):
        raise IdentityTreeError(
            f"IDENTITY-MANIFEST.json[{index}].source must be an object"
        )
    source_record = _evidence.hash_verified_manifest_source(
        source_meta, index, _manifest_dependencies(deps)
    )
    try:
        source_identity = deps.source_identity(source_record)
        expected_result = deps.curate_record(source_record, registry=registry)
    except IdentityCurationError as exc:
        raise IdentityTreeError(
            f"IDENTITY-MANIFEST.json[{index}] hash-verified source replay failed: {exc}"
        ) from exc
    return ManifestReplay(source_identity, expected_result)


def replay_manifest_mapping(
    mapping: Mapping[str, Any], index: int, registry, deps: TreeDependencies
) -> ManifestReplay:
    """Replay one mapping before trusting its declared retain/exclude action."""

    action = mapping.get("action")
    if action not in {"retained", "exclude"}:
        raise IdentityTreeError(
            f"IDENTITY-MANIFEST.json[{index}].action must be retained or exclude"
        )
    replay = _replay_source_record(mapping, index, registry, deps)
    if action != replay.result.action:
        raise IdentityTreeError(
            f"IDENTITY-MANIFEST.json[{index}].action does not match the "
            "hash-verified source replay"
        )
    if replay.result.action == "exclude":
        _identity_json._require_canonical_json_equal(
            mapping,
            replay.result.mapping,
            f"IDENTITY-MANIFEST.json[{index}] exclusion mapping",
        )
    return replay


def _expected_output_hash(output_record: Any, rel: str, line_no: int, replay) -> None:
    try:
        actual_hash = _identity_json.sha256_json(output_record)
    except IdentityCurationError as exc:
        raise IdentityTreeError(
            f"identity output is not canonical JSON data: {rel}:{line_no}: {exc}"
        ) from exc
    expected_output_sha256 = replay.result.mapping.get("output_sha256")
    if actual_hash != expected_output_sha256:
        raise IdentityTreeError(
            f"identity output hashes do not match manifest: {rel}:{line_no}"
        )


def _validate_expected_outputs(lines, rel: str, registry, deps: TreeDependencies) -> None:
    expected_by_line, actual_by_line = lines
    manifest_deps = _manifest_dependencies(deps)
    for line_no, (index, mapping, replay) in expected_by_line.items():
        output_record = actual_by_line[line_no]
        _expected_output_hash(output_record, rel, line_no, replay)
        _manifest.validate_manifest_ids(
            _identity_checks.ManifestRecord(mapping, output_record, index),
            registry,
            replay,
            manifest_deps,
        )


def validate_identity_outputs(
    expected_outputs, actual_paths, registry, deps: TreeDependencies
) -> None:
    """Verify preserved bytes, coordinates and identities for every manifest output."""

    output_deps = _output_dependencies(deps)
    for rel, expected_by_line in sorted(expected_outputs.items()):
        preserved_sources = {
            line_no: replay.source.original.encode("utf-8")
            for line_no, (_, _, replay) in expected_by_line.items()
            if replay.result.mapping.get("record_kind") in PRESERVED_KINDS
        }
        actual_by_line = _identity_output.read_identity_output(
            actual_paths[rel], rel, preserved_sources, output_deps
        )
        if set(actual_by_line) != set(expected_by_line):
            raise IdentityTreeError(
                f"identity output line coordinates do not match manifest: {rel}"
            )
        _validate_expected_outputs(
            (expected_by_line, actual_by_line), rel, registry, deps
        )


def _require_plain_tree(dest: Path) -> None:
    if dest.is_symlink():
        raise IdentityTreeError("identity tree root must not be a symlink")
    symlinks = [
        path.relative_to(dest).as_posix()
        for path in dest.rglob("*")
        if path.is_symlink()
    ]
    if symlinks:
        raise IdentityTreeError(
            f"identity tree must not contain symlinks: {symlinks}"
        )


def _tree_sidecars(dest: Path) -> tuple[Path, Path]:
    sidecar = dest / FACTORY_REGISTRY_SIDECAR
    manifest_path = dest / IDENTITY_MANIFEST_SIDECAR
    if not sidecar.is_file():
        raise IdentityTreeError("identity tree missing FACTORY-REGISTRY.json")
    if not manifest_path.is_file():
        raise IdentityTreeError("identity tree missing IDENTITY-MANIFEST.json")
    return sidecar, manifest_path


def _pinned_tree_registry(sidecar: Path, expected_registry_digest: str | None):
    try:
        registry = _identity_registry.load_registry(sidecar)
    except IdentityCurationError as exc:
        raise IdentityTreeError(
            f"FACTORY-REGISTRY.json is invalid: {exc}"
        ) from exc
    if (
        expected_registry_digest is not None
        and registry.sha256 != expected_registry_digest
    ):
        raise IdentityTreeError(
            f"registry digest mismatch: expected {expected_registry_digest}, "
            f"got {registry.sha256}"
        )
    return registry


def _actual_output_paths(dest: Path) -> dict[str, Path]:
    return {
        path.relative_to(dest).as_posix(): path
        for path in sorted(dest.rglob("*.jsonl"))
        if path.is_file()
    }


def _require_output_paths(expected_outputs, actual_paths) -> None:
    if set(actual_paths) != set(expected_outputs):
        missing = sorted(set(expected_outputs) - set(actual_paths))
        extra = sorted(set(actual_paths) - set(expected_outputs))
        raise IdentityTreeError(
            f"identity output paths do not match manifest: "
            f"missing={missing}, extra={extra}"
        )


def validate_identity_tree(
    dest: Path,
    expected_registry_digest: str | None,
    expected_manifest_digest: str | None,
    deps: TreeDependencies,
):
    """Validate a written identity tree.

    Without ``expected_manifest_digest`` this proves internal consistency only:
    each embedded source snapshot matches its adjacent digest and deterministically
    replays to the declared mapping and output. Supplying an externally retained
    SHA-256 of the exact manifest bytes additionally makes manifest/source-ledger
    replacement tamper-evident. ``expected_registry_digest`` independently pins
    the reviewed registry bytes.
    """

    dest = Path(dest)
    _require_plain_tree(dest)
    sidecar, manifest_path = _tree_sidecars(dest)
    registry = _pinned_tree_registry(sidecar, expected_registry_digest)
    manifest = _identity_checks.read_identity_manifest(
        manifest_path, expected_manifest_digest, deps.check_dependencies()
    )
    expected_outputs = _identity_output.expected_identity_outputs(
        manifest, registry, _output_dependencies(deps)
    )
    actual_paths = _actual_output_paths(dest)
    _require_output_paths(expected_outputs, actual_paths)
    validate_identity_outputs(expected_outputs, actual_paths, registry, deps)
    return registry


if __package__:
    _expose_package_sibling(__name__)
