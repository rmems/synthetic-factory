#!/usr/bin/env python3
"""Per-mapping field and emission checks for manifest provenance entries.

Split out of ``curate_identity_manifest.py`` (CodeScene/qlty: High total
complexity) by responsibility; the manifest orchestrator stays in
``curate_identity_manifest`` and every name remains re-exported from
``curate_identity`` so existing ``curate_identity.X`` call sites and test
seams resolve unchanged.

Each sealed provenance mapping must target an emitted owner whose emitted
payload carries the canonical provenance the mapping declares.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from typing import Any, Mapping

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("curate_identity_manifest_fields")
    from . import curate_identity_evidence as _evidence
    from . import curate_identity_json as _identity_json
    from . import curate_identity_materialize as _materialize
    from . import curate_identity_provenance as _provenance
    from . import curate_identity_sources as _sources
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "curate_identity_manifest_fields"
    )
    import curate_identity_evidence as _evidence
    import curate_identity_json as _identity_json
    import curate_identity_materialize as _materialize
    import curate_identity_provenance as _provenance
    import curate_identity_sources as _sources

IdentityTreeError = _identity_json.IdentityTreeError
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
SHAPE_BASIS = _materialize.SHAPE_BASIS
CANONICAL_PROVENANCE = _provenance.CANONICAL_PROVENANCE
ManifestDependencies = _evidence.ManifestDependencies


def _fail(error: IdentityTreeError) -> None:
    """Raise ``error``; one raise site keeps fail-closed checks branch-light."""

    raise error


@dataclass(frozen=True)
class ProvenanceCheck:
    """One emitted record's provenance-validation inputs."""

    item: Any
    kind: str
    owner_paths: list[str]
    expected_mapping: Mapping[str, Any]


@dataclass(frozen=True)
class _EmittedTarget:
    record: Mapping[str, Any]
    owner_path: str
    state_path: str | None
    owner: Mapping[str, Any]
    basis: str
    canonical: Mapping[str, Any]


@dataclass
class _TargetIndex:
    seen_targets: set = field(default_factory=set)
    mappings_by_target: dict = field(default_factory=dict)
    covered_owners: set = field(default_factory=set)


def _mapping_digest_valid(provenance_mapping: Mapping[str, Any]) -> bool:
    mapping_sha256 = provenance_mapping.get("mapping_sha256")
    if not isinstance(mapping_sha256, str):
        return False
    if not SHA256_RE.fullmatch(mapping_sha256):
        return False
    return mapping_sha256 == _provenance.provenance_mapping_sha256(provenance_mapping)


def _require_mapping_seal(provenance_mapping: Any, where: str) -> None:
    if not isinstance(provenance_mapping, Mapping):
        _fail(IdentityTreeError(f"{where} must be an object"))
    if not _mapping_digest_valid(provenance_mapping):
        _fail(IdentityTreeError(f"{where} provenance mapping digest is invalid"))


def _emitted_owner_path(
    provenance_mapping: Mapping[str, Any], check: ProvenanceCheck, where: str
) -> str:
    owner_path = provenance_mapping.get("owner_path")
    if not isinstance(owner_path, str):
        _fail(IdentityTreeError(f"{where}.owner_path does not name an emitted owner"))
    if owner_path not in set(check.owner_paths):
        _fail(IdentityTreeError(f"{where}.owner_path does not name an emitted owner"))
    return owner_path


def _target_state_path(provenance_mapping: Mapping[str, Any], where: str) -> str | None:
    state_path = provenance_mapping.get("state_path")
    if state_path is None:
        return None
    if not isinstance(state_path, str):
        _fail(IdentityTreeError(f"{where}.state_path must be a string"))
    return state_path


def _provenance_owner_target(
    provenance_mapping: Mapping[str, Any], check: ProvenanceCheck, where: str
):
    owner_path = _emitted_owner_path(provenance_mapping, check, where)
    owner = _sources.pointer_value(check.item.record, owner_path)
    if not isinstance(owner, Mapping):
        _fail(IdentityTreeError(f"{where}.owner_path must name an object"))
    return owner_path, _target_state_path(provenance_mapping, where), owner


def _canonical_basis(provenance_mapping: Mapping[str, Any], where: str) -> str:
    basis = provenance_mapping.get("basis")
    if not isinstance(basis, str):
        _fail(IdentityTreeError(f"{where}.basis must be a non-empty string"))
    if not basis:
        _fail(IdentityTreeError(f"{where}.basis must be a non-empty string"))
    return basis


def _canonical_provenance_object(provenance_mapping: Mapping[str, Any], where: str):
    canonical = provenance_mapping.get("canonical")
    if not isinstance(canonical, Mapping):
        _fail(IdentityTreeError(f"{where}.canonical must be a provenance object"))
    if "claimed" not in canonical:
        _fail(IdentityTreeError(f"{where}.canonical must be a provenance object"))
    return canonical


def _canonical_fields(provenance_mapping: Mapping[str, Any], where: str):
    return (
        _canonical_basis(provenance_mapping, where),
        _canonical_provenance_object(provenance_mapping, where),
    )


def _require_canonical_kind(canonical: Mapping[str, Any], basis: str, where: str) -> None:
    allowed_kinds = set(CANONICAL_PROVENANCE)
    if basis == "nested_trajectory_aggregate":
        allowed_kinds.add("unknown")
    if canonical.get("kind") not in allowed_kinds:
        _fail(IdentityTreeError(f"{where}.canonical.kind is invalid"))


def _owner_state_emits(owner_provenance: Any, state: Mapping, canonical: Mapping) -> bool:
    if not isinstance(owner_provenance, Mapping):
        return False
    if owner_provenance.get("kind") != canonical.get("kind"):
        return False
    if not _identity_json._canonical_json_equal(
        owner_provenance.get("claimed"), canonical.get("claimed")
    ):
        return False
    return state.get("sim_or_real") == canonical.get("kind")


def _emitted_state(target: _EmittedTarget, where: str) -> Mapping[str, Any]:
    if target.state_path != _sources.pointer(target.owner_path, "state"):
        _fail(IdentityTreeError(f"{where}.state_path does not belong to owner_path"))
    state = _sources.pointer_value(target.record, target.state_path)
    if not isinstance(state, Mapping):
        _fail(IdentityTreeError(f"{where}.state_path must name an object"))
    return state


def _require_state_emission(target: _EmittedTarget, where: str) -> None:
    state = _emitted_state(target, where)
    if not _identity_json._canonical_json_equal(
        state.get("provenance"), target.canonical
    ):
        _fail(IdentityTreeError(
            f"{where}.canonical does not match emitted state provenance"
        ))
    if not _owner_state_emits(
        target.owner.get("provenance"), state, target.canonical
    ):
        _fail(IdentityTreeError(
            f"{where}.canonical does not match its emitted owner"
        ))


def _require_shape_canonical(target: _EmittedTarget, kind: str, where: str) -> None:
    expected = {"kind": "designed", "claimed": None, "basis": SHAPE_BASIS.get(kind)}
    if target.basis != SHAPE_BASIS.get(kind):
        _fail(IdentityTreeError(
            f"{where}.canonical does not match the shape contract"
        ))
    if not _identity_json._canonical_json_equal(target.canonical, expected):
        _fail(IdentityTreeError(
            f"{where}.canonical does not match the shape contract"
        ))


def _require_aggregate_canonical(
    target: _EmittedTarget, check: ProvenanceCheck, where: str
) -> None:
    if target.owner_path != "/":
        _fail(IdentityTreeError(
            f"{where}.canonical does not match nested provenance"
        ))
    aggregate = _evidence.aggregate_owner_provenance(target.record, check.owner_paths)
    if not _identity_json._canonical_json_equal(target.canonical, aggregate):
        _fail(IdentityTreeError(
            f"{where}.canonical does not match nested provenance"
        ))


def _require_emitted_basis(
    target: _EmittedTarget, check: ProvenanceCheck, where: str
) -> None:
    if target.basis == "nested_trajectory_aggregate":
        _require_aggregate_canonical(target, check, where)
        return
    if target.basis in SHAPE_BASIS.values():
        _require_shape_canonical(target, check.kind, where)


def _require_owner_emission(
    target: _EmittedTarget, check: ProvenanceCheck, where: str
) -> None:
    if not _identity_json._canonical_json_equal(
        target.owner.get("provenance"), target.canonical
    ):
        _fail(IdentityTreeError(
            f"{where}.canonical does not match emitted owner provenance"
        ))
    if "basis" in target.canonical:
        if target.canonical.get("basis") != target.basis:
            _fail(IdentityTreeError(
                f"{where}.basis does not match canonical provenance"
            ))
    _require_emitted_basis(target, check, where)


def _index_provenance_mapping(
    target: tuple[str, str | None],
    provenance_mapping: Mapping[str, Any],
    index: _TargetIndex,
    where: str,
) -> None:
    if target in index.seen_targets:
        _fail(IdentityTreeError(f"{where} repeats a provenance mapping target"))
    index.seen_targets.add(target)
    index.mappings_by_target[target] = provenance_mapping
    index.covered_owners.add(target[0])


def _validate_one_provenance_mapping(
    nested: tuple[int, Any],
    check: ProvenanceCheck,
    index: _TargetIndex,
    deps: ManifestDependencies,
) -> None:
    nested_index, provenance_mapping = nested
    where = (
        f"IDENTITY-MANIFEST.json[{check.item.index}]"
        f".provenance_mappings[{nested_index}]"
    )
    _require_mapping_seal(provenance_mapping, where)
    owner_path, state_path, owner = _provenance_owner_target(
        provenance_mapping, check, where
    )
    _index_provenance_mapping(
        (owner_path, state_path), provenance_mapping, index, where
    )
    basis, canonical = _canonical_fields(provenance_mapping, where)
    _require_canonical_kind(canonical, basis, where)
    target = _EmittedTarget(
        check.item.record, owner_path, state_path, owner, basis, canonical
    )
    if target.state_path is not None:
        _require_state_emission(target, where)
    else:
        _require_owner_emission(target, check, where)
    _evidence.validate_provenance_original(
        provenance_mapping, target.canonical, where, deps
    )


if __package__:
    _expose_package_sibling(__name__)
