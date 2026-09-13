"""Identity source and manifest checks with live facade-owned policy dependencies."""
from __future__ import annotations

import contextlib
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Pattern


@dataclass(frozen=True)
class Dependencies:
    """Operations supplied for each call so registry and validation seams stay live."""
    curation_error: type[Exception]
    tree_error: type[Exception]
    is_json_whitespace: Callable[[str], bool]
    strict_json_loads: Callable[..., Any]
    canonical_json: Callable[[Any], str]
    sha256_pattern: Pattern[str]
    sha256_bytes: Callable[[bytes], str]
    canonical_id: Callable[..., str]
    payload_factory: Callable[..., str | None]
    training_ready_true_paths: Callable[..., Any]
    residual_real_claim_paths: Callable[..., Any]
    shape_validation_errors: Callable[..., Any]
    owner_specs: Callable[..., Any]
    pointer_value: Callable[..., Any]
    shape_designed: str
    supported_kinds: frozenset[str]
    classify_kind: Callable[..., str]


@dataclass(frozen=True)
class ManifestRecord:
    mapping: Mapping[str, Any]
    record: Mapping[str, Any]
    index: int


@dataclass(frozen=True)
class OwnerContext:
    row: Any
    source_identity: Any
    kind: str
    output_id: str


def _refuse_when(condition, message, error_type):
    if condition:
        raise error_type(message)


def _require_source_text(original, deps):
    if not isinstance(original, str):
        raise deps.curation_error("source_json must be a non-empty JSON string")
    _refuse_when(
        not original or deps.is_json_whitespace(original),
        "source_json must be a non-empty JSON string",
        deps.curation_error,
    )
    # LF is the physical JSONL record separator. A CR is retained payload
    # when it is not the single CR in a CRLF terminator.
    _refuse_when(
        "\n" in original,
        "source_json must contain exactly one JSONL record",
        deps.curation_error,
    )


def validate_source_json(original: str, canonical_source: str, deps: Dependencies) -> None:
    _require_source_text(original, deps)
    try:
        parsed_original = deps.strict_json_loads(original)
    except ValueError as exc:
        raise deps.curation_error(f"source_json is not strict JSON: {exc}") from exc
    _refuse_when(
        deps.canonical_json(parsed_original) != canonical_source,
        "source_json does not decode to source record",
        deps.curation_error,
    )


def _factory_binding_matches(item, expected, payload_factory, deps):
    return (all(item.mapping.get(key) == value for key, value in expected.items())
            and deps.payload_factory(item.record) == payload_factory)


def _require_training_policy(item, owner, deps):
    _refuse_when(
        owner.row.training_ready_policy == "never" and deps.training_ready_true_paths(item.record),
        f"IDENTITY-MANIFEST.json[{item.index}] violates training_ready_policy=never",
        deps.tree_error,
    )


def _require_output_policy(item, owner, contract, deps):
    _require_training_policy(item, owner, deps)
    _refuse_when(
        deps.residual_real_claim_paths(item.record),
        f"IDENTITY-MANIFEST.json[{item.index}] contains a residual real claim",
        deps.tree_error,
    )
    _refuse_when(
        contract == deps.shape_designed and deps.shape_validation_errors(item.record, owner.kind),
        f"IDENTITY-MANIFEST.json[{item.index}] output payload shape is invalid",
        deps.tree_error,
    )


def require_factory_contract(item: ManifestRecord, owner: OwnerContext, deps: Dependencies):
    contract = owner.row.provenance_contract_by_kind.get(owner.kind)
    expected = {"factory": owner.source_identity.factory,
                "path_id": owner.source_identity.factory,
                "factory_id": owner.row.payload_factory,
                "provenance_contract": contract}
    _refuse_when(
        not _factory_binding_matches(item, expected, owner.row.payload_factory, deps),
        f"IDENTITY-MANIFEST.json[{item.index}] factory contract does not match output",
        deps.tree_error,
    )
    _require_output_policy(item, owner, contract, deps)


def _row_authorizes(row, kind):
    return row is not None and kind in row.record_kinds and row.identity_authoritative


def _manifest_root_identifiers(item, deps):
    output_id = item.mapping.get("output_id")
    if not isinstance(output_id, str) or item.record.get("id") != output_id:
        raise deps.tree_error(
            f"IDENTITY-MANIFEST.json[{item.index}].output_id does not match emitted record"
        )
    kind = item.mapping.get("record_kind")
    _refuse_when(
        kind not in deps.supported_kinds or deps.classify_kind(item.record) != kind,
        f"IDENTITY-MANIFEST.json[{item.index}].record_kind does not match emitted record",
        deps.tree_error,
    )
    return output_id, kind


def manifest_output_authority(item: ManifestRecord, registry, source_identity, deps: Dependencies):
    output_id, kind = _manifest_root_identifiers(item, deps)
    source_factory = source_identity.factory
    _refuse_when(
        output_id != deps.canonical_id(source_identity, kind, "/"),
        f"IDENTITY-MANIFEST.json[{item.index}].output_id is not canonical",
        deps.tree_error,
    )
    row = registry.by_path_id.get(source_factory)
    _refuse_when(
        not _row_authorizes(row, kind),
        f"IDENTITY-MANIFEST.json[{item.index}] factory authority is invalid",
        deps.tree_error,
    )
    require_factory_contract(item, OwnerContext(row, source_identity, kind, output_id), deps)
    return output_id, kind, row


def _one_owner_mapping(id_mapping, index, nested_index, deps):
    if not isinstance(id_mapping, Mapping):
        raise deps.tree_error(
            f"IDENTITY-MANIFEST.json[{index}].id_mappings[{nested_index}] must be an object"
        )
    owner_path = id_mapping.get("owner_path")
    nested_output_id = id_mapping.get("output_id")
    if not isinstance(owner_path, str) or not isinstance(nested_output_id, str):
        raise deps.tree_error(
            f"IDENTITY-MANIFEST.json[{index}].id_mappings[{nested_index}] "
            "must contain string owner_path and output_id"
        )
    return owner_path, nested_output_id


def owner_id_mappings(mapping, index, deps: Dependencies):
    id_mappings = mapping.get("id_mappings")
    if not isinstance(id_mappings, list):
        raise deps.tree_error(f"IDENTITY-MANIFEST.json[{index}].id_mappings must be a list")
    by_owner: dict[str, str] = {}
    for nested_index, id_mapping in enumerate(id_mappings):
        owner_path, nested_output_id = _one_owner_mapping(id_mapping, index, nested_index, deps)
        _refuse_when(
            owner_path in by_owner,
            f"IDENTITY-MANIFEST.json[{index}].id_mappings repeats {owner_path}",
            deps.tree_error,
        )
        by_owner[owner_path] = nested_output_id
    return by_owner


def _emitted_owner_paths(item, owner, deps):
    try:
        owner_paths = ["/"]
        for owner_path, _owner in deps.owner_specs(
            item.record,
            owner.kind,
            owner.row.preference_side_kinds if owner.kind == "preference" else None,
        ):
            if owner_path not in owner_paths:
                owner_paths.append(owner_path)
    except deps.curation_error as exc:
        raise deps.tree_error(
            f"IDENTITY-MANIFEST.json[{item.index}] emitted nested shape is invalid: {exc}"
        ) from exc
    return owner_paths


def _validate_owned_ids(item, owner, by_owner, deps):
    for owner_path, nested_output_id in by_owner.items():
        payload_owner = deps.pointer_value(item.record, owner_path)
        if not isinstance(payload_owner, Mapping) or payload_owner.get("id") != nested_output_id:
            raise deps.tree_error(
                f"IDENTITY-MANIFEST.json[{item.index}] id mapping for {owner_path} "
                "does not match emitted record"
            )
        _refuse_when(
            nested_output_id != deps.canonical_id(owner.source_identity, owner.kind, owner_path),
            f"IDENTITY-MANIFEST.json[{item.index}] id mapping for {owner_path} is not canonical",
            deps.tree_error,
        )


def manifest_owner_paths(item: ManifestRecord, owner: OwnerContext, deps: Dependencies):
    owner_paths = _emitted_owner_paths(item, owner, deps)
    by_owner = owner_id_mappings(item.mapping, item.index, deps)
    _refuse_when(
        set(by_owner) != set(owner_paths),
        f"IDENTITY-MANIFEST.json[{item.index}].id_mappings owner paths do not match emitted record",
        deps.tree_error,
    )
    _refuse_when(
        by_owner["/"] != owner.output_id,
        f"IDENTITY-MANIFEST.json[{item.index}] root id mapping does not match output_id",
        deps.tree_error,
    )
    _validate_owned_ids(item, owner, by_owner, deps)
    return owner_paths


def _require_manifest_digest(manifest_bytes, expected_manifest_digest, deps):
    manifest_digest = deps.sha256_bytes(manifest_bytes)
    if expected_manifest_digest is not None:
        if not isinstance(expected_manifest_digest, str) or not deps.sha256_pattern.fullmatch(
            expected_manifest_digest
        ):
            raise deps.tree_error("expected manifest digest must be a lowercase SHA-256")
        _refuse_when(
            manifest_digest != expected_manifest_digest,
            "manifest digest mismatch: "
                f"expected {expected_manifest_digest}, got {manifest_digest}",
            deps.tree_error,
        )


def read_identity_manifest(manifest_path: Path, expected_manifest_digest: str | None, deps: Dependencies):
    try:
        manifest_bytes = manifest_path.read_bytes()
    except OSError as exc:
        raise deps.tree_error(f"IDENTITY-MANIFEST.json is unreadable: {exc}") from exc
    _require_manifest_digest(manifest_bytes, expected_manifest_digest, deps)
    try:
        manifest = deps.strict_json_loads(manifest_bytes.decode("utf-8"))
    except ValueError as exc:
        raise deps.tree_error(f"IDENTITY-MANIFEST.json is not readable JSON: {exc}") from exc
    if not isinstance(manifest, list):
        raise deps.tree_error("IDENTITY-MANIFEST.json must be a list of mappings")
    return manifest


def retained_source_lines(results, deps: Dependencies):
    retained_by_rel: dict[str, dict[int, str]] = {}
    for result in results:
        if result.action != "retained" or result.record is None:
            continue
        source_meta = result.mapping["source"]
        by_line = retained_by_rel.setdefault(source_meta["path"], {})
        _refuse_when(
            source_meta["line"] in by_line,
            "retained records repeat source coordinate "
                f"{source_meta['path']}:{source_meta['line']}",
            deps.curation_error,
        )
        by_line[source_meta["line"]] = (
            source_meta["original"] if result.mapping["record_kind"] == "code_repair"
            else deps.canonical_json(result.record)
        )
    return retained_by_rel


def rollback_identity_tree(dest, created_files, created_directories):
    for path in reversed(created_files):
        with contextlib.suppress(FileNotFoundError):
            path.unlink()
    for directory in reversed(created_directories):
        with contextlib.suppress(OSError):
            directory.rmdir()
    with contextlib.suppress(OSError):
        dest.rmdir()


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


