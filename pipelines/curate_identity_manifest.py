#!/usr/bin/env python3
"""Emitted provenance-mapping and retained-id validation for the manifest.

Split out of ``curate_identity.py`` (CodeScene: Lines of Code in a Single
File) by responsibility; every name is re-exported from ``curate_identity``
so existing ``curate_identity.X`` call sites and test seams resolve
unchanged.

Emission validation proves each sealed provenance mapping targets an emitted
owner, that the emitted payload carries its canonical provenance, that owner
coverage is complete, and that every target matches the deterministic replay
of the hash-verified source snapshot.  Per-mapping field and emission checks
live in ``curate_identity_manifest_fields``; source-snapshot and evidence
helpers live in ``curate_identity_evidence``.
"""

from __future__ import annotations

import re
import sys
from typing import Any, Mapping

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("curate_identity_manifest")
    from . import curate_identity_checks as _identity_checks
    from . import curate_identity_evidence as _evidence
    from . import curate_identity_json as _identity_json
    from . import curate_identity_manifest_fields as _manifest_fields
    from . import curate_identity_materialize as _materialize
    from . import curate_identity_sources as _sources
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "curate_identity_manifest"
    )
    import curate_identity_checks as _identity_checks
    import curate_identity_evidence as _evidence
    import curate_identity_json as _identity_json
    import curate_identity_manifest_fields as _manifest_fields
    import curate_identity_materialize as _materialize
    import curate_identity_sources as _sources

IdentityTreeError = _identity_json.IdentityTreeError
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
SHAPE_BASIS = _materialize.SHAPE_BASIS
PRESERVED_KINDS = _sources.PRESERVED_KINDS
ManifestDependencies = _evidence.ManifestDependencies
ProvenanceCheck = _manifest_fields.ProvenanceCheck


def _fail(error: IdentityTreeError) -> None:
    """Raise ``error``; one raise site keeps fail-closed checks branch-light."""

    raise error


def _emitted_provenance_owner(record: Mapping[str, Any], owner_path: str) -> bool:
    owner = _sources.pointer_value(record, owner_path)
    if not isinstance(owner, Mapping):
        return False
    return isinstance(owner.get("provenance"), Mapping)


def _require_covered_owners(check: ProvenanceCheck, covered_owners: set) -> None:
    required_owners = {
        owner_path
        for owner_path in check.owner_paths
        if _emitted_provenance_owner(check.item.record, owner_path)
    }
    if covered_owners != required_owners:
        _fail(IdentityTreeError(
            f"IDENTITY-MANIFEST.json[{check.item.index}].provenance_mappings owner "
            "paths do not match emitted provenance owners"
        ))


def _canonical_pair_bound(owner_canonical: Any, state_canonical: Any, basis: str) -> bool:
    if not isinstance(owner_canonical, Mapping):
        return False
    if not isinstance(state_canonical, Mapping):
        return False
    if owner_canonical.get("basis") != basis:
        return False
    if owner_canonical.get("kind") != state_canonical.get("kind"):
        return False
    return _identity_json._canonical_json_equal(
        owner_canonical.get("claimed"), state_canonical.get("claimed")
    )


def _owner_basis_bound(owner_mapping: Mapping[str, Any], state_mapping: Any) -> bool:
    if not isinstance(state_mapping, Mapping):
        return False
    basis = owner_mapping["basis"]
    if basis != state_mapping.get("basis"):
        return False
    return _canonical_pair_bound(
        owner_mapping["canonical"], state_mapping.get("canonical"), basis
    )


def _require_owner_basis_bindings(
    index, expected_targets, item_index: int
) -> None:
    for owner_path, state_path in expected_targets:
        if state_path is not None:
            continue
        owner_mapping = index.mappings_by_target[(owner_path, None)]
        basis = owner_mapping["basis"]
        if basis == "nested_trajectory_aggregate":
            continue
        if basis in SHAPE_BASIS.values():
            continue
        state_mapping = index.mappings_by_target.get(
            (owner_path, _sources.pointer(owner_path, "state"))
        )
        if not _owner_basis_bound(owner_mapping, state_mapping):
            _fail(IdentityTreeError(
                f"IDENTITY-MANIFEST.json[{item_index}] owner provenance basis is not "
                "bound to its original state resolution"
            ))


def _require_replayed_targets(check: ProvenanceCheck, index) -> None:
    expected_by_target = _evidence.expected_provenance_by_target(
        check.expected_mapping, check.item.index
    )
    expected_targets = set(expected_by_target)
    if index.seen_targets != expected_targets:
        _fail(IdentityTreeError(
            f"IDENTITY-MANIFEST.json[{check.item.index}] provenance mapping targets "
            "do not match the hash-verified source replay"
        ))
    _require_owner_basis_bindings(index, expected_targets, check.item.index)
    for target in expected_targets:
        _identity_json._require_canonical_json_equal(
            index.mappings_by_target[target],
            expected_by_target[target],
            f"IDENTITY-MANIFEST.json[{check.item.index}] provenance mapping for {target}",
        )


def validate_manifest_provenance(
    check: ProvenanceCheck, deps: ManifestDependencies
) -> None:
    item = check.item
    mappings = item.mapping.get("provenance_mappings")
    if not isinstance(mappings, list):
        _fail(IdentityTreeError(
            f"IDENTITY-MANIFEST.json[{item.index}].provenance_mappings must be a "
            "non-empty list"
        ))
    if not mappings:
        _fail(IdentityTreeError(
            f"IDENTITY-MANIFEST.json[{item.index}].provenance_mappings must be a "
            "non-empty list"
        ))
    index = _manifest_fields._TargetIndex()
    for nested in enumerate(mappings):
        _manifest_fields._validate_one_provenance_mapping(nested, check, index, deps)
    _require_covered_owners(check, index.covered_owners)
    _require_replayed_targets(check, index)


def _output_digest_matches(item, expected_result) -> bool:
    expected_output_sha256 = expected_result.mapping.get("output_sha256")
    if not isinstance(expected_output_sha256, str):
        return False
    if not SHA256_RE.fullmatch(expected_output_sha256):
        return False
    if item.mapping.get("output_sha256") != expected_output_sha256:
        return False
    if _identity_json.sha256_json(expected_result.record) != expected_output_sha256:
        return False
    return _identity_json.sha256_json(item.record) == expected_output_sha256


def validate_manifest_ids(item, registry, replay, deps: ManifestDependencies) -> None:
    expected_result = replay.result
    expected_mapping = expected_result.mapping
    if expected_mapping.get("record_kind") in PRESERVED_KINDS:
        _identity_json._require_canonical_json_equal(
            item.mapping, expected_mapping, "procedural identity mapping"
        )
        _identity_json._require_canonical_json_equal(
            item.record, expected_result.record, "preserved oracle envelope"
        )
        return
    if expected_result.action != "retained":
        _fail(IdentityTreeError(
            f"IDENTITY-MANIFEST.json[{item.index}] has output for a replayed exclusion"
        ))
    if expected_result.record is None:
        _fail(IdentityTreeError(
            f"IDENTITY-MANIFEST.json[{item.index}] has output for a replayed exclusion"
        ))
    _identity_json._require_canonical_json_equal(
        item.mapping.get("original_ids"),
        expected_mapping.get("original_ids"),
        f"IDENTITY-MANIFEST.json[{item.index}].original_ids",
    )
    _identity_json._require_canonical_json_equal(
        item.mapping.get("id_mappings"),
        expected_mapping.get("id_mappings"),
        f"IDENTITY-MANIFEST.json[{item.index}].id_mappings",
    )
    check_deps = deps.check_dependencies()
    output_id, kind, row = _identity_checks.manifest_output_authority(
        item, registry, replay.source, check_deps
    )
    owner_paths = _identity_checks.manifest_owner_paths(
        item,
        _identity_checks.OwnerContext(row, replay.source, kind, output_id),
        check_deps,
    )
    validate_manifest_provenance(
        ProvenanceCheck(item, kind, owner_paths, expected_mapping), deps
    )
    _identity_json._require_canonical_json_equal(
        item.record,
        expected_result.record,
        f"IDENTITY-MANIFEST.json[{item.index}] output",
    )
    if not _output_digest_matches(item, expected_result):
        _fail(IdentityTreeError(
            f"IDENTITY-MANIFEST.json[{item.index}].output_sha256 does not match the "
            "source replay"
        ))
    _identity_json._require_canonical_json_equal(
        item.mapping,
        expected_mapping,
        f"IDENTITY-MANIFEST.json[{item.index}] retained mapping",
    )


if __package__:
    _expose_package_sibling(__name__)
