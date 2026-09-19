#!/usr/bin/env python3
"""Hash-verified source snapshots and provenance evidence for the manifest.

Split out of ``curate_identity.py`` (CodeScene: Lines of Code in a Single
File) by responsibility; every name is re-exported from ``curate_identity``
so existing ``curate_identity.X`` call sites and test seams resolve
unchanged.

Each manifest entry embeds a source snapshot whose adjacent digest detects
corruption relative to the embedded bytes; it is not an external
authenticity anchor.  Provenance originals are validated by re-resolving the
recorded snapshot through ``resolve_provenance``, supplied per call so the
facade's patch seams stay live.
"""

from __future__ import annotations

import copy
import re
import sys
from dataclasses import dataclass
from typing import Any, Callable, Mapping

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("curate_identity_evidence")
    from . import curate_identity_json as _identity_json
    from . import curate_identity_sources as _sources
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "curate_identity_evidence"
    )
    import curate_identity_json as _identity_json
    import curate_identity_sources as _sources

IdentityCurationError = _identity_json.IdentityCurationError
IdentityTreeError = _identity_json.IdentityTreeError
SourceRecord = _sources.SourceRecord
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _fail(error: IdentityTreeError) -> None:
    """Raise ``error``; one raise site keeps fail-closed checks branch-light."""

    raise error


def _fail_chained(error: IdentityTreeError, cause: BaseException) -> None:
    """Raise ``error`` from ``cause`` for the single chained raise site."""

    raise error from cause



@dataclass(frozen=True)
class ManifestDependencies:
    """Live facade operations used while validating manifest evidence."""

    resolve_provenance: Callable[..., Any]
    check_dependencies: Callable[[], Any]
    strict_json_loads: Callable[..., Any]
    is_json_whitespace: Callable[[str], bool]
    canonical_json: Callable[[Any], str]
    sha256_bytes: Callable[[bytes], str]


def _manifest_source_path(source_meta: Mapping[str, Any], where: str) -> str:
    try:
        source_path, _factory = _sources.normalize_source_path(source_meta.get("path"))
    except IdentityCurationError as exc:
        _fail_chained(IdentityTreeError(f"{where}.path is invalid: {exc}"), exc)
    return source_path


def _manifest_source_line(source_meta: Mapping[str, Any], where: str) -> int:
    source_line = source_meta.get("line")
    if not _sources._is_valid_source_line(source_line):
        _fail(IdentityTreeError(f"{where}.line must be positive"))
    return source_line


def _manifest_source_digest(source_meta: Mapping[str, Any], where: str) -> str:
    source_sha256 = source_meta.get("sha256")
    if not isinstance(source_sha256, str):
        _fail(IdentityTreeError(f"{where}.sha256 must be a SHA-256"))
    if not SHA256_RE.fullmatch(source_sha256):
        _fail(IdentityTreeError(f"{where}.sha256 must be a SHA-256"))
    return source_sha256


def _manifest_hash_basis(source_meta: Mapping[str, Any], where: str) -> str:
    hash_basis = source_meta.get("hash_basis")
    if hash_basis not in {"canonical-json-sha256", "source-json-line-sha256"}:
        _fail(IdentityTreeError(f"{where}.hash_basis is invalid"))
    return hash_basis


@dataclass(frozen=True)
class _SnapshotCheck:
    """The hash-verification inputs for one embedded source snapshot."""

    source_meta: Mapping[str, Any]
    source_sha256: str
    hash_basis: str
    where: str


def _snapshot_text(check: _SnapshotCheck, deps: ManifestDependencies) -> str:
    original = check.source_meta.get("original")
    if not isinstance(original, str):
        _fail(IdentityTreeError(
            f"{check.where}.original must be a hash-verifiable JSONL snapshot"
        ))
    if not original or deps.is_json_whitespace(original):
        _fail(IdentityTreeError(
            f"{check.where}.original must be a hash-verifiable JSONL snapshot"
        ))
    if "\n" in original:
        _fail(IdentityTreeError(
            f"{check.where}.original must contain exactly one JSONL record"
        ))
    return original


def _snapshot_record(
    original: str, check: _SnapshotCheck, deps: ManifestDependencies
):
    if deps.sha256_bytes(original.encode("utf-8")) != check.source_sha256:
        _fail(IdentityTreeError(
            f"{check.where}.original does not match source.sha256"
        ))
    try:
        return deps.strict_json_loads(original)
    except ValueError as exc:
        _fail_chained(IdentityTreeError(
            f"{check.where}.original is not strict JSON: {exc}"
        ), exc)


def _snapshot_digest(
    original: str, original_record: Any, check: _SnapshotCheck, deps
) -> str | None:
    if check.hash_basis != "canonical-json-sha256":
        return check.source_sha256
    if original != deps.canonical_json(original_record):
        _fail(IdentityTreeError(
            f"{check.where}.original does not match canonical-json-sha256 basis"
        ))
    return None


def _manifest_original_snapshot(check: _SnapshotCheck, deps: ManifestDependencies):
    original = _snapshot_text(check, deps)
    original_record = _snapshot_record(original, check, deps)
    digest = _snapshot_digest(original, original_record, check, deps)
    return original_record, digest, original


def hash_verified_manifest_source(
    source_meta: Mapping[str, Any], index: int, deps: ManifestDependencies
) -> SourceRecord:
    """Recover one source record from internally hash-consistent manifest evidence.

    The adjacent digest detects corruption relative to the embedded snapshot. It
    is not an external authenticity anchor; callers need ``expected_manifest_digest``
    for tamper-evident validation of the manifest as a whole.
    """

    where = f"IDENTITY-MANIFEST.json[{index}].source"
    source_path = _manifest_source_path(source_meta, where)
    source_line = _manifest_source_line(source_meta, where)
    source_sha256 = _manifest_source_digest(source_meta, where)
    hash_basis = _manifest_hash_basis(source_meta, where)
    check = _SnapshotCheck(source_meta, source_sha256, hash_basis, where)
    original_record, digest, original = _manifest_original_snapshot(check, deps)
    return SourceRecord(original_record, source_path, source_line, digest, original)


def _require_exact_mapping(value: Any, expected: set[str], message: str) -> Mapping:
    if not isinstance(value, Mapping):
        _fail(IdentityTreeError(message))
    if set(value) != expected:
        _fail(IdentityTreeError(message))
    return value


def validate_presence_snapshot(snapshot: Any, where: str) -> tuple[bool, Any]:
    snapshot = _require_exact_mapping(
        snapshot,
        {"present", "value"},
        f"{where} must contain exactly boolean present and value",
    )
    present = snapshot["present"]
    value = snapshot["value"]
    if not isinstance(present, bool):
        _fail(IdentityTreeError(f"{where}.present must be a boolean"))
    if not present and value is not None:
        _fail(IdentityTreeError(f"{where}.value must be null when absent"))
    return present, value


def _owner_snapshot_original(original: Any, where: str) -> None:
    original = _require_exact_mapping(
        original,
        {"owner_provenance"},
        f"{where}.original must contain exactly owner_provenance",
    )
    validate_presence_snapshot(
        original["owner_provenance"],
        f"{where}.original.owner_provenance",
    )


def _state_snapshot_originals(original: Any, where: str) -> tuple[dict, dict]:
    expected = {"sim_or_real", "state_provenance", "owner_provenance"}
    original = _require_exact_mapping(
        original,
        expected,
        f"{where}.original must contain the complete state provenance snapshot",
    )
    snapshots = {
        key: validate_presence_snapshot(original[key], f"{where}.original.{key}")
        for key in expected
    }
    original_state: dict[str, Any] = {}
    original_owner: dict[str, Any] = {}
    if snapshots["sim_or_real"][0]:
        original_state["sim_or_real"] = copy.deepcopy(snapshots["sim_or_real"][1])
    if snapshots["state_provenance"][0]:
        original_state["provenance"] = copy.deepcopy(snapshots["state_provenance"][1])
    if snapshots["owner_provenance"][0]:
        original_owner["provenance"] = copy.deepcopy(snapshots["owner_provenance"][1])
    return original_owner, original_state


def validate_provenance_original(
    provenance_mapping: Mapping[str, Any],
    canonical: Mapping[str, Any],
    where: str,
    deps: ManifestDependencies,
) -> None:
    original = provenance_mapping.get("original")
    if provenance_mapping.get("state_path") is None:
        _owner_snapshot_original(original, where)
        return
    original_owner, original_state = _state_snapshot_originals(original, where)
    resolved_kind, resolved_claimed, resolved_basis = deps.resolve_provenance(
        original_owner, original_state
    )
    if resolved_kind != canonical.get("kind"):
        _fail(IdentityTreeError(
            f"{where}.original does not resolve to its canonical provenance"
        ))
    if resolved_basis != provenance_mapping.get("basis"):
        _fail(IdentityTreeError(
            f"{where}.original does not resolve to its canonical provenance"
        ))
    if not _identity_json._canonical_json_equal(
        resolved_claimed, canonical.get("claimed")
    ):
        _fail(IdentityTreeError(
            f"{where}.original does not resolve to its canonical provenance"
        ))


def _nested_owner_provenances(
    record: Mapping[str, Any], owner_paths: list[str]
) -> list[Mapping[str, Any]]:
    nested: list[Mapping[str, Any]] = []
    for owner_path in owner_paths:
        if owner_path == "/":
            continue
        owner = _sources.pointer_value(record, owner_path)
        provenance = owner.get("provenance") if isinstance(owner, Mapping) else None
        if not isinstance(provenance, Mapping):
            _fail(IdentityTreeError(
                f"provenance mapping owner {owner_path} lacks provenance"
            ))
        nested.append(provenance)
    return nested


def _aggregate_claimed(claims: list[Any]) -> Any:
    equal_claims = all(
        _identity_json._canonical_json_equal(item, claims[0]) for item in claims
    )
    return claims[0] if equal_claims else claims


def aggregate_owner_provenance(
    record: Mapping[str, Any], owner_paths: list[str]
) -> dict[str, Any]:
    nested = _nested_owner_provenances(record, owner_paths)
    if not nested:
        _fail(IdentityTreeError("aggregate provenance mapping has no nested owners"))
    kinds = {item.get("kind") for item in nested}
    claims = [copy.deepcopy(item.get("claimed")) for item in nested]
    if len(kinds) != 1:
        return {"kind": "unknown", "claimed": claims}
    return {"kind": next(iter(kinds)), "claimed": _aggregate_claimed(claims)}


def _expected_provenance_target(provenance_mapping: Mapping[str, Any], index: int):
    owner_path = provenance_mapping.get("owner_path")
    state_path = provenance_mapping.get("state_path")
    if not isinstance(owner_path, str):
        _fail(IdentityTreeError(
            f"IDENTITY-MANIFEST.json[{index}] hash-verified source replay "
            "produced an invalid provenance target"
        ))
    if state_path is not None and not isinstance(state_path, str):
        _fail(IdentityTreeError(
            f"IDENTITY-MANIFEST.json[{index}] hash-verified source replay "
            "produced an invalid provenance target"
        ))
    return owner_path, state_path


def _expected_mapping_list(expected_mapping: Mapping[str, Any], index: int) -> list:
    expected_mappings = expected_mapping.get("provenance_mappings")
    if not isinstance(expected_mappings, list):
        _fail(IdentityTreeError(
            f"IDENTITY-MANIFEST.json[{index}] hash-verified source replay "
            "did not produce provenance mappings"
        ))
    if not expected_mappings:
        _fail(IdentityTreeError(
            f"IDENTITY-MANIFEST.json[{index}] hash-verified source replay "
            "did not produce provenance mappings"
        ))
    return expected_mappings


def _index_expected_target(
    by_target: dict, provenance_mapping: Any, index: int
) -> None:
    if not isinstance(provenance_mapping, Mapping):
        _fail(IdentityTreeError(
            f"IDENTITY-MANIFEST.json[{index}] hash-verified source replay "
            "produced an invalid provenance mapping"
        ))
    target = _expected_provenance_target(provenance_mapping, index)
    if target in by_target:
        _fail(IdentityTreeError(
            f"IDENTITY-MANIFEST.json[{index}] hash-verified source replay "
            "repeated a provenance target"
        ))
    by_target[target] = provenance_mapping


def expected_provenance_by_target(
    expected_mapping: Mapping[str, Any], index: int
) -> dict[tuple[str, str | None], Mapping[str, Any]]:
    """Index the provenance plan replayed from the hash-verified source snapshot."""

    by_target: dict[tuple[str, str | None], Mapping[str, Any]] = {}
    for provenance_mapping in _expected_mapping_list(expected_mapping, index):
        _index_expected_target(by_target, provenance_mapping, index)
    return by_target


if __package__:
    _expose_package_sibling(__name__)
