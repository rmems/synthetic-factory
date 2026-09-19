#!/usr/bin/env python3
"""Deterministic record-level identity and provenance curation.

``curate_record`` is a pure function: a caller supplies one decoded JSON
record and its immutable source coordinate.  Authority comes from the
reviewed factory registry at ``config/FACTORY-REGISTRY.json`` (exact
``path_id`` then exact ``payload_factory``), not from a hard-coded slug.
Onboard a generator by adding a reviewed registry row and adding or updating
its exact generator/provider/channel assignment in
``_REVIEWED_GENERATOR_RIGHTS``; both reviewed entries are required.

``write_run`` is the tree writer.  A cleaned/curated destination receives
the exact reviewed ``FACTORY-REGISTRY.json`` bytes plus
``IDENTITY-MANIFEST.json`` (a list of mappings).  The writer pins both exact
sidecar byte sequences during its immediate validation.  A later unpinned
manifest validation proves only internal consistency; callers need an
externally retained manifest digest for replacement detection.  Registry
version is not stamped onto record payloads.

This module is a compatibility facade: responsibilities live in the
``curate_identity_*`` siblings (sources, owners, provenance, materialize,
procedural, evidence, manifest, tree, writer, stages, checks, json,
registry, output).  Every historical public and private spelling is
re-exported here, and the dependency bundles the siblings consume are built
from this module's namespace per call so documented patch seams such as
``curate_identity._map_claim`` stay live.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping, NamedTuple

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("curate_identity")
    from .curate_identity_simulator_process import replay_session
    from . import curate_identity_checks as _identity_checks
    from . import curate_identity_evidence as _evidence
    from . import curate_identity_json as _identity_json
    from . import curate_identity_manifest as _manifest
    from . import curate_identity_materialize as _materialize
    from . import curate_identity_output as _identity_output
    from . import curate_identity_owners as _owners
    from . import curate_identity_procedural as _procedural
    from . import curate_identity_provenance as _provenance
    from . import curate_identity_registry as _identity_registry
    from . import curate_identity_shapes as _shapes
    from . import curate_identity_source_iter as _source_iter
    from . import curate_identity_sources as _sources
    from . import curate_identity_stages as _identity_stages
    from . import curate_identity_tree as _tree
    from . import curate_identity_writer as _writer
    from . import operator_paths as _operator_paths
    from . import record_kind as _record_kind
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "curate_identity"
    )
    from curate_identity_simulator_process import replay_session
    import curate_identity_checks as _identity_checks
    import curate_identity_evidence as _evidence
    import curate_identity_json as _identity_json
    import curate_identity_manifest as _manifest
    import curate_identity_materialize as _materialize
    import curate_identity_output as _identity_output
    import curate_identity_owners as _owners
    import curate_identity_procedural as _procedural
    import curate_identity_provenance as _provenance
    import curate_identity_registry as _identity_registry
    import curate_identity_shapes as _shapes
    import curate_identity_source_iter as _source_iter
    import curate_identity_sources as _sources
    import curate_identity_stages as _identity_stages
    import curate_identity_tree as _tree
    import curate_identity_writer as _writer
    import operator_paths as _operator_paths
    import record_kind as _record_kind

FactoryRow = _identity_registry.FactoryRow
FactoryRegistry = _identity_registry.FactoryRegistry
operator_path = _operator_paths.operator_path
os = _writer.os
copy = _materialize.copy
hashlib = _sources.hashlib
dataclass = _materialize.dataclass
PurePosixPath = _sources.PurePosixPath
PREFERENCE_SIDE_KINDS = _record_kind.PREFERENCE_SIDE_KINDS
SUPPORTED_RECORD_KINDS = _record_kind.SUPPORTED_RECORD_KINDS
classify_kind = _record_kind.classify_kind
preference_side_kinds = _record_kind.preference_side_kinds
TRANSFORM_NAME = _sources.TRANSFORM_NAME
TRANSFORM_VERSION = _sources.TRANSFORM_VERSION
ID_NAMESPACE = _sources.ID_NAMESPACE

CANONICAL_PROVENANCE = _provenance.CANONICAL_PROVENANCE
CONTRACT_REQUIRE_STATE = "require_state_claim"
CONTRACT_SHAPE_DESIGNED = "synthetic_shape_implies_designed"
ALLOWED_CONTRACTS = frozenset({CONTRACT_REQUIRE_STATE, CONTRACT_SHAPE_DESIGNED})
SHAPE_BASIS = _materialize.SHAPE_BASIS
LEGACY_ID_KEYS = _owners.LEGACY_ID_KEYS
# Procedural routes that retain the generated bytes verbatim: their envelope is
# the measurement's attribution, so curation preserves the generated family ID
# and output bytes instead of deriving a canonical identity ID.
PRESERVED_KINDS = _sources.PRESERVED_KINDS
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
HIL_RE = _provenance.HIL_RE
# Standalone 'real'/'live' claims only: 'realistic' and 'real-time' describe a
# simulation and must not be read as a real-world deployment claim.
REAL_WORLD_RE = _provenance.REAL_WORLD_RE

FACTORY_REGISTRY_SIDECAR = "FACTORY-REGISTRY.json"
IDENTITY_MANIFEST_SIDECAR = "IDENTITY-MANIFEST.json"
FACTORY_REGISTRY_PATH = _identity_registry.FACTORY_REGISTRY_PATH
REGISTRY_SCHEMA_VERSION = _identity_registry.REGISTRY_SCHEMA_VERSION
HOSTED_REGISTRY_SCHEMA_VERSION = _identity_registry.HOSTED_REGISTRY_SCHEMA_VERSION
LEGACY_REGISTRY_SCHEMA_VERSION = _identity_registry.LEGACY_REGISTRY_SCHEMA_VERSION
SUPPORTED_REGISTRY_SCHEMA_VERSIONS = _identity_registry.SUPPORTED_REGISTRY_SCHEMA_VERSIONS
_RIGHTS_ROW_FIELDS = _identity_registry._RIGHTS_ROW_FIELDS
_REVIEWED_GENERATOR_RIGHTS = _identity_registry._REVIEWED_GENERATOR_RIGHTS
CANONICAL_PROVIDERS = _identity_registry.CANONICAL_PROVIDERS
CHANNELS = _identity_registry.CHANNELS
HOSTED_FRONTIER_PROFILE_ID = _identity_registry.HOSTED_FRONTIER_PROFILE_ID
INTENDED_USES = _identity_registry.INTENDED_USES
PROJECT_TRAINING_POLICIES = _identity_registry.PROJECT_TRAINING_POLICIES
PROVIDERS = _identity_registry.PROVIDERS
RIGHTS_AUTHORIZATIONS = _identity_registry.RIGHTS_AUTHORIZATIONS
RIGHTS_CHANNELS = _identity_registry.RIGHTS_CHANNELS
RIGHTS_PROFILE_IDS = _identity_registry.RIGHTS_PROFILE_IDS
# Facade-owned process cache: publication-boundary tests patch this name.
# Copy a sibling cache that default_registry already populated so load-once
# survives importing the facade second.
_DEFAULT_REGISTRY = _identity_registry._DEFAULT_REGISTRY


IdentityCurationError = _identity_json.IdentityCurationError
CanonicalIdCollision = _identity_json.CanonicalIdCollision
IdentityTreeError = _identity_json.IdentityTreeError

SourceRecord = _sources.SourceRecord
CurationResult = _sources.CurationResult
SourceIdentity = _sources.SourceIdentity
_SourceIdentity = SourceIdentity
_ManifestReplay = _tree.ManifestReplay

_reject_unpaired_surrogates = _identity_json._reject_unpaired_surrogates
canonical_json = _identity_json.canonical_json
sha256_json = _identity_json.sha256_json
ExactJSONFloat = _identity_json.ExactJSONFloat
dumps_exact_json = _identity_json.dumps_exact_json
_canonical_json_equal = _identity_json._canonical_json_equal
_require_canonical_json_equal = _identity_json._require_canonical_json_equal
_reject_json_constant = _identity_json._reject_json_constant
parse_finite_json_float = _identity_json.parse_finite_json_float
reject_duplicate_object_keys = _identity_json.reject_duplicate_object_keys
_strict_json_loads = _identity_json._strict_json_loads
_is_json_whitespace = _identity_json._is_json_whitespace
_reject_training_ready_true = _identity_json._reject_training_ready_true

_generator_identity = _identity_registry._generator_identity
_legacy_generator_identity = _identity_registry._legacy_generator_identity
_parse_factory_row = _identity_registry._parse_factory_row
_legacy_registry_row = _identity_registry._legacy_registry_row
_is_procedural_row = _identity_registry._is_procedural_row
_registry_row_for_validation = _identity_registry._registry_row_for_validation
_parse_procedural_row = _identity_registry._parse_procedural_row
load_registry = _identity_registry.load_registry
default_registry = _identity_registry.default_registry

sha256_bytes = _identity_checks.sha256_bytes

_normalize_source_path = _sources.normalize_source_path
_declared_factory = _sources.declared_factory
_payload_factory = _sources.payload_factory
_canonical_id = _sources.canonical_id
canonical_id = _canonical_id
_pointer = _sources.pointer
_pointer_value = _sources.pointer_value
record_kind = _sources.record_kind

_legacy_ids = _owners.legacy_ids
_discover_original_ids = _owners.discover_original_ids
_owner_specs = _owners.owner_specs
_payload_has_state_claim = _owners.payload_has_state_claim
_shape_validation_errors = _shapes.shape_validation_errors

_provenance_snapshot = _provenance.provenance_snapshot
_map_claim = _provenance.map_claim
_existing_claimed = _provenance.existing_claimed
_is_real_world_claim = _provenance.is_real_world_claim
_training_ready_true_paths = _provenance.training_ready_true_paths
_residual_real_claim_paths = _provenance.residual_real_claim_paths
_provenance_mapping_sha256 = _provenance.provenance_mapping_sha256
_seal_provenance_mapping = _provenance.seal_provenance_mapping

_source_mapping = _materialize.source_mapping
_exclude = _materialize.exclude
_curated_resolve_owners = _materialize.curated_resolve_owners

_curate_code_repair = _procedural.curate_code_repair
_curate_fault_recovery = _procedural.curate_fault_recovery
_curate_oracle = _procedural.curate_oracle
_curate_known_kind = _procedural.curate_known_kind
_attach_retained_rights = _procedural.attach_retained_rights

_is_under_raw = _writer.is_under_raw
_write_exclusive = _writer.write_exclusive
_ensure_output_directory = _writer.ensure_output_directory
_committed_source_paths = _source_iter.committed_source_paths
_registered_factory_ancestor = _source_iter.registered_factory_ancestor
_source_relative_path = _source_iter.source_relative_path

_validate_presence_snapshot = _evidence.validate_presence_snapshot
_aggregate_owner_provenance = _evidence.aggregate_owner_provenance
_expected_provenance_by_target = _evidence.expected_provenance_by_target


def _identity_check_dependencies():
    return _identity_checks.Dependencies(
        curation_error=IdentityCurationError,
        tree_error=IdentityTreeError,
        is_json_whitespace=_is_json_whitespace,
        strict_json_loads=_strict_json_loads,
        canonical_json=canonical_json,
        sha256_pattern=SHA256_RE,
        sha256_bytes=sha256_bytes,
        canonical_id=_canonical_id,
        payload_factory=_payload_factory,
        training_ready_true_paths=_training_ready_true_paths,
        residual_real_claim_paths=_residual_real_claim_paths,
        shape_validation_errors=_shape_validation_errors,
        owner_specs=_owner_specs,
        pointer_value=_pointer_value,
        shape_designed=CONTRACT_SHAPE_DESIGNED,
        supported_kinds=SUPPORTED_RECORD_KINDS,
        classify_kind=classify_kind,
    )


def _provenance_dependencies():
    return _provenance.ProvenanceDependencies(map_claim=_map_claim)


def _manifest_dependencies():
    return _evidence.ManifestDependencies(
        resolve_provenance=_resolve_provenance,
        check_dependencies=_identity_check_dependencies,
        strict_json_loads=_strict_json_loads,
        is_json_whitespace=_is_json_whitespace,
        canonical_json=canonical_json,
        sha256_bytes=sha256_bytes,
    )


def _output_dependencies():
    return _identity_output.IdentityOutputDependencies(
        canonical_json=canonical_json,
        identity_curation_error=IdentityCurationError,
        identity_tree_error=IdentityTreeError,
        replay_manifest_mapping=_replay_manifest_mapping,
        sha256_pattern=SHA256_RE,
        strict_json_loads=_strict_json_loads,
    )


def _tree_dependencies():
    return _tree.TreeDependencies(
        source_identity=_source_identity,
        curate_record=curate_record,
        replay_manifest_mapping=_replay_manifest_mapping,
        resolve_provenance=_resolve_provenance,
        check_dependencies=_identity_check_dependencies,
        strict_json_loads=_strict_json_loads,
        is_json_whitespace=_is_json_whitespace,
        canonical_json=canonical_json,
        sha256_bytes=sha256_bytes,
    )


def _source_iter_dependencies():
    return _source_iter.SourceIterDependencies(
        strict_json_loads=_strict_json_loads,
        is_json_whitespace=_is_json_whitespace,
    )


def _writer_dependencies():
    return _writer.WriterDependencies(
        write_exclusive=_write_exclusive,
        validate_identity_tree=validate_identity_tree,
        iter_source_records=iter_source_records,
        curate_records=curate_records,
        check_dependencies=_identity_check_dependencies,
        default_registry=default_registry,
        strict_json_loads=_strict_json_loads,
        is_json_whitespace=_is_json_whitespace,
    )


def _source_identity(source: SourceRecord) -> _SourceIdentity:
    return _sources.source_identity(source, _identity_check_dependencies())


def _resolve_provenance(owner: Mapping[str, Any], state: Mapping[str, Any]):
    return _provenance.resolve_provenance(owner, state, _provenance_dependencies())


def _collect_state_resolutions(owner_specs):
    return _provenance.collect_state_resolutions(
        owner_specs, _provenance_dependencies()
    )


def _base_mapping(source, kind, *rest):
    root_original_ids, registry, row, contract = rest
    return _materialize.base_mapping(
        _materialize.MappingContext(
            source, kind, root_original_ids, registry, row, contract
        )
    )


def _assign_nested_ids(curated, *rest):
    original, source, kind, owner_specs, output_id, root_ids = rest
    spec = _materialize.ApplySpec(
        original, source, kind, owner_specs, output_id, root_ids
    )
    return _materialize.assign_nested_ids(curated, spec)


def _apply_resolved_state(*args):
    curated, original, source, kind, owner_specs, resolve_owners, resolutions, output_id, root_ids = args
    spec = _materialize.ApplySpec(
        original, source, kind, owner_specs, output_id, root_ids
    )
    return _materialize.apply_resolved_state(
        curated, spec, resolve_owners, resolutions
    )


def _apply_shape_designed(*args):
    curated, original, source, kind, owner_specs, output_id, root_ids = args
    spec = _materialize.ApplySpec(
        original, source, kind, owner_specs, output_id, root_ids
    )
    return _materialize.apply_shape_designed(curated, spec)


def _hash_verified_manifest_source(source_meta: Mapping[str, Any], index: int):
    return _evidence.hash_verified_manifest_source(
        source_meta, index, _manifest_dependencies()
    )


def _validate_provenance_original(provenance_mapping, canonical, where):
    _evidence.validate_provenance_original(
        provenance_mapping, canonical, where, _manifest_dependencies()
    )


def _validate_manifest_provenance(*args):
    mapping, record, index, kind, owner_paths, expected_mapping = args
    item = _identity_checks.ManifestRecord(mapping, record, index)
    check = _manifest.ProvenanceCheck(item, kind, owner_paths, expected_mapping)
    _manifest.validate_manifest_provenance(check, _manifest_dependencies())


def _validate_manifest_ids(*args):
    mapping, record, index, registry, replay = args
    item = _identity_checks.ManifestRecord(mapping, record, index)
    _manifest.validate_manifest_ids(item, registry, replay, _manifest_dependencies())


def _replay_manifest_mapping(mapping, index, registry):
    return _tree.replay_manifest_mapping(
        mapping, index, registry, _tree_dependencies()
    )


def _expected_identity_outputs(manifest, registry):
    return _identity_output.expected_identity_outputs(
        manifest, registry, _output_dependencies()
    )


def _validate_identity_outputs(expected_outputs, actual_paths, registry):
    """Verify preserved bytes, coordinates and identities for every manifest output."""
    _tree.validate_identity_outputs(
        expected_outputs, actual_paths, registry, _tree_dependencies()
    )


def _classify_source_record(original):
    try:
        kind = record_kind(original)
        kind_error = None
    except IdentityCurationError as exc:
        kind = "unknown"
        kind_error = exc
    return kind, kind_error


def curate_record(
    source_record: SourceRecord,
    registry: FactoryRegistry | None = None,
) -> CurationResult:
    """Curate one source record without mutating the caller's object.

    Kind is classified from the payload first.  Factory authority is the
    reviewed ``path_id`` + ``payload_factory`` row.  Missing or ambiguous
    trajectory provenance returns ``action == 'exclude'``.  Designed is
    never invented from factory membership unless the row's kind contract
    is ``synthetic_shape_implies_designed`` and the payload has no
    ``state.sim_or_real`` claim.
    """

    if not isinstance(source_record, SourceRecord):
        raise IdentityCurationError("curate_record expects a SourceRecord")
    source = _source_identity(source_record)
    original = source_record.record
    registry = default_registry() if registry is None else registry
    row = registry.by_path_id.get(source.factory)
    kind, kind_error = _classify_source_record(original)
    root_original_ids, all_original_ids = _discover_original_ids(original)
    contract = row.provenance_contract_by_kind.get(kind) if row is not None else None
    mapping = _base_mapping(source, kind, root_original_ids, registry, row, contract)
    mapping["original_ids"] = all_original_ids
    if kind_error is not None:
        result = _exclude(
            mapping,
            "identity.unsupported_record_shape",
            details=[str(kind_error)],
        )
    elif row is None:
        result = _exclude(mapping, "identity.unknown_factory")
    else:
        result = _curate_known_kind(kind, original, row, mapping)
    if result is None:
        context = _identity_stages.CurationContext(
            original=original,
            source=source,
            row=row,
            kind=kind,
            contract=contract,
            root_original_ids=root_original_ids,
            mapping=mapping,
        )
        dependencies = _identity_stages.CurationDependencies(
            allowed_contracts=ALLOWED_CONTRACTS,
            apply_resolved_state=_apply_resolved_state,
            apply_shape_designed=_apply_shape_designed,
            canonical_id=_canonical_id,
            collect_state_resolutions=_collect_state_resolutions,
            curation_result=CurationResult,
            exclude=_exclude,
            identity_curation_error=IdentityCurationError,
            owner_specs=_owner_specs,
            payload_factory=_payload_factory,
            payload_has_state_claim=_payload_has_state_claim,
            require_state_contract=CONTRACT_REQUIRE_STATE,
            residual_real_claim_paths=_residual_real_claim_paths,
            sha256_json=sha256_json,
            shape_basis=SHAPE_BASIS,
            shape_validation_errors=_shape_validation_errors,
            training_ready_true_paths=_training_ready_true_paths,
        )
        result = _identity_stages.curate_nonprocedural_record(context, dependencies)
    return _attach_retained_rights(result, row, source.sha256, registry.sha256)


def _register_retained_ids(
    result: CurationResult,
    seen: dict[str, tuple[dict[str, Any], str]],
) -> None:
    """Record a retained result's emitted IDs, rejecting any duplicate."""

    if result.action != "retained":
        return
    source = result.mapping["source"]
    for id_mapping in result.mapping["id_mappings"]:
        output_id = id_mapping["output_id"]
        owner_path = id_mapping["owner_path"]
        if output_id in seen:
            first, first_owner = seen[output_id]
            raise CanonicalIdCollision(
                f"canonical ID collision {output_id!r}: "
                f"{first['path']}:{first['line']}{first_owner} and "
                f"{source['path']}:{source['line']}{owner_path}"
            )
        seen[output_id] = (source, owner_path)


@replay_session()
def curate_records(
    records: Iterable[SourceRecord],
    registry: FactoryRegistry | None = None,
) -> tuple[CurationResult, ...]:
    """Curate a batch and independently reject any duplicate emitted ID."""

    registry = default_registry() if registry is None else registry
    results: list[CurationResult] = []
    seen: dict[str, tuple[dict[str, Any], str]] = {}
    for source_record in records:
        result = curate_record(source_record, registry=registry)
        _register_retained_ids(result, seen)
        results.append(result)
    return tuple(results)


def replay_identity_mapping(
    mapping: Mapping[str, Any], registry: FactoryRegistry | None = None
) -> CurationResult:
    """Verify embedded source bytes and recompute the complete identity decision."""
    replay = _replay_manifest_mapping(mapping, 0, registry or default_registry())
    _require_canonical_json_equal(
        mapping, replay.result.mapping, "replayed identity mapping"
    )
    return replay.result


def validate_identity_tree(
    dest: Path,
    expected_registry_digest: str | None = None,
    expected_manifest_digest: str | None = None,
) -> FactoryRegistry:
    """Validate a written identity tree.

    Without ``expected_manifest_digest`` this proves internal consistency only:
    each embedded source snapshot matches its adjacent digest and deterministically
    replays to the declared mapping and output. Supplying an externally retained
    SHA-256 of the exact manifest bytes additionally makes manifest/source-ledger
    replacement tamper-evident. ``expected_registry_digest`` independently pins
    the reviewed registry bytes.
    """

    return _tree.validate_identity_tree(
        dest,
        expected_registry_digest,
        expected_manifest_digest,
        _tree_dependencies(),
    )


def iter_source_records(
    source: Path,
    registry: FactoryRegistry | None = None,
) -> list[SourceRecord]:
    """Read JSONL records under ``source`` as identity source coordinates."""

    registry = default_registry() if registry is None else registry
    return _source_iter.iter_source_records(
        source, registry, _source_iter_dependencies()
    )


def write_run(
    source: Path,
    dest: Path,
    registry: FactoryRegistry | None = None,
) -> tuple[CurationResult, ...]:
    """Curate a source tree into a new destination with identity sidecars."""

    return _writer.write_run(source, dest, registry, _writer_dependencies())


def _summary(results: Iterable[CurationResult], registry: FactoryRegistry) -> dict[str, Any]:
    results = list(results)
    reasons: Counter[str] = Counter()
    retained = 0
    for result in results:
        if result.action == "retained":
            retained += 1
        for code in result.mapping.get("reason_codes", []):
            reasons[code] += 1
    return {
        "transform": {"name": TRANSFORM_NAME, "version": TRANSFORM_VERSION},
        "registry": {
            "schema_version": registry.schema_version,
            "sha256": registry.sha256,
        },
        "records": len(results),
        "retained": retained,
        "excluded": len(results) - retained,
        "reason_codes": dict(sorted(reasons.items())),
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="JSONL file or run directory")
    parser.add_argument(
        "--out",
        type=Path,
        help="write a NEW cleaned tree with FACTORY-REGISTRY.json and IDENTITY-MANIFEST.json",
    )
    return parser


class Inputs(NamedTuple):
    """The operator's paths, each confined to the working, home and temp trees."""

    source: Path
    out: Path | None


def _inputs(parser: argparse.ArgumentParser, args: argparse.Namespace) -> Inputs:
    """Confine both path arguments right after parsing; sinks never read ``args`` again.

    ``write_run`` still applies ``_is_under_raw`` to the destination and
    ``validate_identity_tree`` afterwards; this funnel only bounds where the
    operator may point the CLI.
    """
    try:
        return Inputs(
            source=operator_path(str(args.source)),
            out=None if args.out is None else operator_path(str(args.out)),
        )
    except argparse.ArgumentTypeError as exc:
        parser.error(str(exc))


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    paths = _inputs(parser, args)
    try:
        registry = default_registry()
        if paths.out is None:
            results = curate_records(
                iter_source_records(paths.source, registry=registry),
                registry=registry,
            )
        else:
            results = write_run(paths.source, paths.out, registry=registry)
        print(json.dumps(_summary(results, registry), ensure_ascii=False, indent=2))
        return 0
    except (OSError, IdentityCurationError, ValueError) as exc:
        print(f"identity curation failed: {exc}", file=sys.stderr)
        return 1


# Historical private spellings, kept for direct importers and tests.
_parse_finite_json_float = parse_finite_json_float
_reject_duplicate_object_keys = reject_duplicate_object_keys
_sha256_bytes = sha256_bytes
_sha256_json = sha256_json


if __package__:
    _expose_package_sibling(__name__)


if __name__ == "__main__":
    raise SystemExit(main())
