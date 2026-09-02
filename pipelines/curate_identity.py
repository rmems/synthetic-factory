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
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import os
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from types import MappingProxyType
from typing import Any, Iterable, Mapping

if __package__:
    from .record_kind import (
        PREFERENCE_SIDE_KINDS,
        SUPPORTED_RECORD_KINDS,
        classify_kind,
        preference_side_kinds,
    )
    from .round_txn import TransactionError, committed_jsonl_paths, marker_mode_path
    from .validate_run import (
        check_episode,
        check_multi_agent,
        check_safety_case,
        check_spike_order,
        check_thalamic,
    )
    from .rights_mapping import (
        CANONICAL_PROVIDERS,
        CHANNELS,
        HOSTED_FRONTIER_PROFILE_ID,
        INTENDED_USES,
        PROJECT_TRAINING_POLICIES,
    )
    from .rights_policy import (
        PROVIDERS,
        RIGHTS_AUTHORIZATIONS,
        RIGHTS_CHANNELS,
        RIGHTS_PROFILE_IDS,
    )
else:
    from record_kind import (
        PREFERENCE_SIDE_KINDS,
        SUPPORTED_RECORD_KINDS,
        classify_kind,
        preference_side_kinds,
    )
    from round_txn import TransactionError, committed_jsonl_paths, marker_mode_path
    from validate_run import (
        check_episode,
        check_multi_agent,
        check_safety_case,
        check_spike_order,
        check_thalamic,
    )
    from rights_mapping import (
        CANONICAL_PROVIDERS,
        CHANNELS,
        HOSTED_FRONTIER_PROFILE_ID,
        INTENDED_USES,
        PROJECT_TRAINING_POLICIES,
    )
    from rights_policy import (
        PROVIDERS,
        RIGHTS_AUTHORIZATIONS,
        RIGHTS_CHANNELS,
        RIGHTS_PROFILE_IDS,
    )

TRANSFORM_NAME = "curate_identity"
TRANSFORM_VERSION = "identity-provenance-v2"
ID_NAMESPACE = "spikenaut.synthetic-factory.curated-record"

CANONICAL_PROVENANCE = frozenset({"designed", "simulated", "hil"})
CONTRACT_REQUIRE_STATE = "require_state_claim"
CONTRACT_SHAPE_DESIGNED = "synthetic_shape_implies_designed"
ALLOWED_CONTRACTS = frozenset({CONTRACT_REQUIRE_STATE, CONTRACT_SHAPE_DESIGNED})
SHAPE_BASIS = {
    "episode": "synthetic_factory_episode_shape",
    "preference": "synthetic_factory_preference_shape",
    "safety_case": "synthetic_factory_safety_case_shape",
    "multi_agent": "synthetic_factory_multi_agent_shape",
}
LEGACY_ID_KEYS = ("id", "record_id", "trajectory_id", "episode_id", "pair_id")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
HIL_RE = re.compile(r"\bhil\b", re.IGNORECASE)
# Standalone 'real'/'live' claims only: 'realistic' and 'real-time' describe a
# simulation and must not be read as a real-world deployment claim.
REAL_WORLD_RE = re.compile(r"^(?:real|live)(?![\w-])", re.IGNORECASE)

FACTORY_REGISTRY_PATH = Path(__file__).resolve().parents[1] / "config" / "FACTORY-REGISTRY.json"
FACTORY_REGISTRY_SIDECAR = "FACTORY-REGISTRY.json"
IDENTITY_MANIFEST_SIDECAR = "IDENTITY-MANIFEST.json"
REGISTRY_SCHEMA_VERSION = "factory-registry-v0.2"

_REVIEWED_GENERATOR_RIGHTS = MappingProxyType(
    {
        "fable-5": ("anthropic", "consumer"),
        "gpt-5.6-sol": ("openai", "consumer"),
        "grok-4.6": ("xai", "consumer"),
        "muse-spark-1.2": ("meta", "api"),
    }
)
if PROVIDERS != CANONICAL_PROVIDERS or RIGHTS_CHANNELS != CHANNELS:
    raise RuntimeError("loaded rights policy vocabulary drifted from sealed mapping")

_DEFAULT_REGISTRY: FactoryRegistry | None = None


class IdentityCurationError(ValueError):
    """Base class for caller-contract and batch-integrity failures."""


class CanonicalIdCollision(IdentityCurationError):
    """Raised when two retained source records resolve to one canonical ID."""


class IdentityTreeError(IdentityCurationError):
    """Raised when a cleaned tree is missing or mismatched identity sidecars."""


@dataclass(frozen=True)
class SourceRecord:
    """A decoded record paired with its immutable, run-relative source identity.

    ``record`` may be any strict JSON value.  Non-object values are carried to
    curation so they can be recorded as deterministic unsupported-shape
    exclusions; only supported object shapes can be retained.

    When supplied, ``source_sha256`` is the digest of the normalized UTF-8
    JSONL payload: LF is excluded together with one immediately preceding CR,
    while a CR not followed by LF remains payload.  Minimal fixtures may omit
    the digest; their mapping records that canonical JSON was hashed instead.

    ``source_json`` carries those exact JSONL bytes as decoded text when they
    are available.  It lets an identity manifest retain a source snapshot that
    can be checked against ``source_sha256`` before the transform is replayed.
    """

    record: Any
    source_path: str
    source_line: int
    source_sha256: str | None = None
    source_json: str | None = None


@dataclass(frozen=True)
class CurationResult:
    """One deterministic retain/exclude decision and its reversible mapping."""

    action: str
    record: dict[str, Any] | None
    mapping: dict[str, Any]


@dataclass(frozen=True)
class _SourceIdentity:
    path: str
    line: int
    factory: str
    sha256: str
    hash_basis: str
    original: str | None


SourceIdentity = _SourceIdentity


@dataclass(frozen=True)
class _ManifestReplay:
    source: _SourceIdentity
    result: CurationResult


@dataclass(frozen=True)
class FactoryRow:
    path_id: str
    payload_factory: str
    generator: str
    generator_version: str
    provider: str
    channel: str
    rights_profile_id: str
    intended_use: str
    project_training_policy: str
    record_kinds: frozenset[str]
    identity_authoritative: bool
    publication_target: str | None
    training_ready_policy: str
    allowed_curation_lanes: tuple[str, ...]
    provenance_contract_by_kind: Mapping[str, str]
    preference_side_kinds: frozenset[str] = frozenset()


@dataclass(frozen=True)
class FactoryRegistry:
    """Reviewed factory table plus the exact bytes that pin a cleaned tree."""

    schema_version: str
    sha256: str
    raw_bytes: bytes
    by_path_id: Mapping[str, FactoryRow]


def _reject_unpaired_surrogates(value: Any, path: str = "$") -> None:
    """Reject strings that cannot be represented as Unicode scalar-value text."""

    if isinstance(value, str):
        if any(0xD800 <= ord(character) <= 0xDFFF for character in value):
            raise ValueError(f"unpaired UTF-16 surrogate in JSON string at {path}")
        return
    if isinstance(value, Mapping):
        for index, (key, item) in enumerate(value.items()):
            if isinstance(key, str):
                _reject_unpaired_surrogates(key, f"{path}.<member-name:{index}>")
            _reject_unpaired_surrogates(item, f"{path}[{index}]")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _reject_unpaired_surrogates(item, f"{path}[{index}]")


def canonical_json(value: Any) -> str:
    """Serialize JSON data byte-stably for hashes, tests, and output sidecars."""

    try:
        _reject_unpaired_surrogates(value)
        payload = json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        # Keep the public serializer's promise byte-stable: callers must never
        # receive text that fails only when a downstream hash or writer encodes it.
        payload.encode("utf-8")
        return payload
    except (TypeError, ValueError, UnicodeError) as exc:
        raise IdentityCurationError(f"record is not canonical JSON data: {exc}") from exc


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _canonical_json_equal(left: Any, right: Any) -> bool:
    """Compare JSON values without Python's bool/int/float equivalence."""

    return canonical_json(left) == canonical_json(right)


def _require_canonical_json_equal(actual: Any, expected: Any, where: str) -> None:
    try:
        equal = _canonical_json_equal(actual, expected)
    except IdentityCurationError as exc:
        raise IdentityTreeError(f"{where} is not canonical JSON data: {exc}") from exc
    if not equal:
        raise IdentityTreeError(f"{where} does not match the hash-verified source replay")


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"non-standard JSON numeric constant {value}")


def parse_finite_json_float(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed):
        raise ValueError(f"JSON numeric literal is not finitely representable: {value}")
    return parsed


def reject_duplicate_object_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON object key {key!r}")
        value[key] = item
    return value


def _strict_json_loads(payload: str) -> Any:
    """Decode strict JSON with deterministic object semantics at every depth."""

    value = json.loads(
        payload,
        object_pairs_hook=reject_duplicate_object_keys,
        parse_constant=_reject_json_constant,
        parse_float=parse_finite_json_float,
    )
    _reject_unpaired_surrogates(value)
    return value


def _is_json_whitespace(value: str) -> bool:
    """Return whether non-empty text contains only RFC 8259 JSON whitespace."""

    return bool(value) and all(character in " \t\r\n" for character in value)


def _reject_training_ready_true(value: Any, path: str = "$") -> None:
    if isinstance(value, Mapping):
        if value.get("training_ready"):
            raise IdentityCurationError(f"{path} must not contain training_ready: true")
        for key, item in value.items():
            _reject_training_ready_true(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _reject_training_ready_true(item, f"{path}[{index}]")


def _parse_factory_row(raw: Any, index: int) -> FactoryRow:
    if not isinstance(raw, Mapping):
        raise IdentityCurationError(f"factories[{index}] must be an object")
    required = (
        "path_id",
        "payload_factory",
        "generator",
        "generator_version",
        "provider",
        "channel",
        "rights_profile_id",
        "intended_use",
        "project_training_policy",
        "record_kinds",
        "identity_authoritative",
        "publication_target",
        "training_ready_policy",
        "allowed_curation_lanes",
        "provenance_contract_by_kind",
    )
    missing = [key for key in required if key not in raw]
    if missing:
        raise IdentityCurationError(f"factories[{index}] missing fields: {missing}")
    path_id = raw["path_id"]
    payload_factory = raw["payload_factory"]
    if not isinstance(path_id, str) or not path_id.strip():
        raise IdentityCurationError(f"factories[{index}].path_id must be a string")
    if (
        path_id != path_id.strip()
        or path_id in {".", ".."}
        or "/" in path_id
        or "\\" in path_id
        or "\x00" in path_id
        or PurePosixPath(path_id).parts != (path_id,)
    ):
        raise IdentityCurationError(
            f"factories[{index}].path_id must be exactly one normalized directory component"
        )
    if not isinstance(payload_factory, str) or not payload_factory.strip():
        raise IdentityCurationError(f"factories[{index}].payload_factory must be a string")
    for field in ("generator", "generator_version"):
        field_value = raw[field]
        if (
            not isinstance(field_value, str)
            or not field_value.strip()
            or field_value != field_value.strip()
        ):
            raise IdentityCurationError(
                f"factories[{index}].{field} must be a non-empty normalized string"
            )
    generator = raw["generator"]
    provider = raw["provider"]
    channel = raw["channel"]
    profile_id = raw["rights_profile_id"]
    intended_use = raw["intended_use"]
    project_training_policy = raw["project_training_policy"]
    rights_vocabularies = (
        ("provider", provider, PROVIDERS),
        ("channel", channel, RIGHTS_CHANNELS),
        ("rights_profile_id", profile_id, RIGHTS_PROFILE_IDS),
        ("intended_use", intended_use, INTENDED_USES),
        (
            "project_training_policy",
            project_training_policy,
            PROJECT_TRAINING_POLICIES,
        ),
    )
    for field, value, vocabulary in rights_vocabularies:
        if not isinstance(value, str) or value not in vocabulary:
            raise IdentityCurationError(f"factories[{index}] has unknown {field}")
    if profile_id != HOSTED_FRONTIER_PROFILE_ID:
        raise IdentityCurationError(
            f"factories[{index}].rights_profile_id must be "
            f"{HOSTED_FRONTIER_PROFILE_ID}"
        )
    expected_assignment = _REVIEWED_GENERATOR_RIGHTS.get(generator)
    if expected_assignment is None:
        raise IdentityCurationError(f"factories[{index}] has unknown reviewed generator")
    if (provider, channel) != expected_assignment:
        raise IdentityCurationError(
            f"factories[{index}] generator/provider/channel assignment is not reviewed"
        )
    authorization = RIGHTS_AUTHORIZATIONS.get((provider, channel, profile_id))
    if authorization is None:
        raise IdentityCurationError(
            f"factories[{index}] rights fields are not authorized by loaded policy"
        )
    if (
        intended_use != authorization.intended_use
        or project_training_policy != authorization.project_training_policy
    ):
        raise IdentityCurationError(
            f"factories[{index}] rights fields drift from loaded policy"
        )
    kinds_raw = raw["record_kinds"]
    if not isinstance(kinds_raw, list) or not kinds_raw:
        raise IdentityCurationError(f"factories[{index}].record_kinds must be a non-empty list")
    if not all(isinstance(kind, str) and kind for kind in kinds_raw):
        raise IdentityCurationError(f"factories[{index}].record_kinds must be strings")
    if len(kinds_raw) != len(set(kinds_raw)):
        raise IdentityCurationError(f"factories[{index}].record_kinds must not contain duplicates")
    unsupported_kinds = sorted(set(kinds_raw) - SUPPORTED_RECORD_KINDS)
    if unsupported_kinds:
        raise IdentityCurationError(
            f"factories[{index}].record_kinds contains unsupported kinds: {unsupported_kinds}"
        )
    kinds = frozenset(kinds_raw)
    if not isinstance(raw["identity_authoritative"], bool):
        raise IdentityCurationError(f"factories[{index}].identity_authoritative must be a boolean")
    publication_target = raw["publication_target"]
    if publication_target is not None and not isinstance(publication_target, str):
        raise IdentityCurationError(
            f"factories[{index}].publication_target must be null or a string"
        )
    policy = raw["training_ready_policy"]
    if policy not in {"never", "compose_eligible"}:
        raise IdentityCurationError(
            f"factories[{index}].training_ready_policy must be never or compose_eligible"
        )
    lanes = raw["allowed_curation_lanes"]
    if not isinstance(lanes, list) or not all(isinstance(item, str) for item in lanes):
        raise IdentityCurationError(
            f"factories[{index}].allowed_curation_lanes must be a list of strings"
        )
    contracts = raw["provenance_contract_by_kind"]
    if not isinstance(contracts, Mapping):
        raise IdentityCurationError(
            f"factories[{index}].provenance_contract_by_kind must be an object"
        )
    for kind in kinds:
        contract = contracts.get(kind)
        if contract not in ALLOWED_CONTRACTS:
            raise IdentityCurationError(
                f"factories[{index}] missing allowed provenance_contract for {kind}"
            )
        if contract == CONTRACT_SHAPE_DESIGNED and not raw["identity_authoritative"]:
            raise IdentityCurationError(
                f"factories[{index}] synthetic_shape_implies_designed requires "
                "identity_authoritative"
            )
    preference_kinds_raw = raw.get("preference_side_kinds")
    if "preference" in kinds:
        if not isinstance(preference_kinds_raw, list) or not preference_kinds_raw:
            raise IdentityCurationError(
                f"factories[{index}].preference_side_kinds must be a non-empty list"
            )
        if not all(isinstance(kind, str) for kind in preference_kinds_raw):
            raise IdentityCurationError(f"factories[{index}].preference_side_kinds must be strings")
        if len(preference_kinds_raw) != len(set(preference_kinds_raw)):
            raise IdentityCurationError(
                f"factories[{index}].preference_side_kinds must not contain duplicates"
            )
        unsupported_side_kinds = sorted(set(preference_kinds_raw) - PREFERENCE_SIDE_KINDS)
        if unsupported_side_kinds:
            raise IdentityCurationError(
                f"factories[{index}].preference_side_kinds contains unsupported "
                f"kinds: {unsupported_side_kinds}"
            )
    elif preference_kinds_raw is not None:
        raise IdentityCurationError(
            f"factories[{index}].preference_side_kinds requires preference authority"
        )
    return FactoryRow(
        path_id=path_id,
        payload_factory=payload_factory,
        generator=generator,
        generator_version=raw["generator_version"],
        provider=provider,
        channel=channel,
        rights_profile_id=profile_id,
        intended_use=intended_use,
        project_training_policy=project_training_policy,
        record_kinds=kinds,
        identity_authoritative=raw["identity_authoritative"],
        publication_target=publication_target,
        training_ready_policy=policy,
        allowed_curation_lanes=tuple(lanes),
        provenance_contract_by_kind={str(key): str(value) for key, value in contracts.items()},
        preference_side_kinds=frozenset(preference_kinds_raw or ()),
    )


def load_registry(path: Path | None = None) -> FactoryRegistry:
    """Load reviewed registry bytes. Pin = SHA-256 of those exact bytes."""

    registry_path = Path(FACTORY_REGISTRY_PATH if path is None else path)
    try:
        raw_bytes = registry_path.read_bytes()
    except OSError as exc:
        raise IdentityCurationError(
            f"factory registry is unreadable: {registry_path}: {exc}"
        ) from exc
    try:
        payload = _strict_json_loads(raw_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise IdentityCurationError(
            f"factory registry is not UTF-8 JSON: {registry_path}: {exc}"
        ) from exc
    if not isinstance(payload, Mapping):
        raise IdentityCurationError("factory registry must be a JSON object")
    _reject_training_ready_true(payload)
    schema_version = payload.get("schema_version")
    if schema_version != REGISTRY_SCHEMA_VERSION:
        raise IdentityCurationError(
            f"factory registry schema_version must be {REGISTRY_SCHEMA_VERSION}"
        )
    if payload.get("lookup_key") != "path_id":
        raise IdentityCurationError("factory registry lookup_key must be path_id")
    factories = payload.get("factories")
    if not isinstance(factories, list) or not factories:
        raise IdentityCurationError("factory registry factories must be a non-empty list")
    by_path_id: dict[str, FactoryRow] = {}
    for index, raw_row in enumerate(factories):
        row = _parse_factory_row(raw_row, index)
        if row.path_id in by_path_id:
            raise IdentityCurationError(f"duplicate registry path_id: {row.path_id}")
        by_path_id[row.path_id] = row
    return FactoryRegistry(
        schema_version=schema_version,
        sha256=sha256_bytes(raw_bytes),
        raw_bytes=raw_bytes,
        by_path_id=by_path_id,
    )


def default_registry() -> FactoryRegistry:
    """Return the committed reviewed registry, loaded once per process."""

    global _DEFAULT_REGISTRY
    if _DEFAULT_REGISTRY is None:
        _DEFAULT_REGISTRY = load_registry(FACTORY_REGISTRY_PATH)
    return _DEFAULT_REGISTRY


def _normalize_source_path(value: str) -> tuple[str, str]:
    if not isinstance(value, str) or not value.strip():
        raise IdentityCurationError("source_path must be a non-empty relative path")
    raw = value
    if raw != raw.strip() or "\\" in raw or "\x00" in raw:
        raise IdentityCurationError(
            "source_path must already be an exact normalized POSIX relative path"
        )
    path = PurePosixPath(raw)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise IdentityCurationError(
            "source_path must be normalized, relative, and contain no '.' or '..'"
        )
    if len(path.parts) < 2:
        raise IdentityCurationError(
            "source_path must include a factory directory and a source filename"
        )
    normalized = path.as_posix()
    if normalized != raw:
        raise IdentityCurationError(f"source_path is not normalized: {value!r}; use {normalized!r}")
    return normalized, path.parts[0]


def _source_identity(source: SourceRecord) -> _SourceIdentity:
    if (
        not isinstance(source.source_line, int)
        or isinstance(source.source_line, bool)
        or source.source_line < 1
    ):
        raise IdentityCurationError("source_line must be a positive integer")
    path, factory = _normalize_source_path(source.source_path)
    canonical_source = canonical_json(source.record)
    original = source.source_json
    if original is not None:
        if not isinstance(original, str) or not original or _is_json_whitespace(original):
            raise IdentityCurationError("source_json must be a non-empty JSON string")
        # LF is the physical JSONL record separator. A CR is retained payload
        # when it is not the single CR in a CRLF terminator.
        if "\n" in original:
            raise IdentityCurationError("source_json must contain exactly one JSONL record")
        try:
            parsed_original = _strict_json_loads(original)
        except (json.JSONDecodeError, ValueError) as exc:
            raise IdentityCurationError(f"source_json is not strict JSON: {exc}") from exc
        if canonical_json(parsed_original) != canonical_source:
            raise IdentityCurationError("source_json does not decode to source record")
    if source.source_sha256 is None:
        original = canonical_source
        digest = sha256_bytes(original.encode("utf-8"))
        basis = "canonical-json-sha256"
    else:
        digest = str(source.source_sha256).lower()
        if not SHA256_RE.fullmatch(digest):
            raise IdentityCurationError("source_sha256 must be exactly 64 hexadecimal characters")
        basis = "source-json-line-sha256"
        if original is not None:
            if sha256_bytes(original.encode("utf-8")) != digest:
                raise IdentityCurationError("source_json does not match source_sha256")
        elif sha256_bytes(canonical_source.encode("utf-8")) == digest:
            # A caller-provided line digest binds the canonical source
            # representation only when the bytes actually coincide. Otherwise
            # retain the digest without claiming a hash-verified snapshot.
            original = canonical_source
    return _SourceIdentity(path, source.source_line, factory, digest, basis, original)


def record_kind(record: Any) -> str:
    """Classify using the shared census-order classifier.

    Unknown shapes raise so ``curate_record`` can exclude them as
    ``identity.unsupported_record_shape``.
    """

    if not isinstance(record, Mapping):
        raise IdentityCurationError("record must be a JSON object")
    kind = classify_kind(record)
    if kind == "unknown":
        raise IdentityCurationError(
            f"unsupported record shape (keys: {sorted(map(str, record.keys()))[:8]})"
        )
    return kind


def _declared_factory(record: Any) -> str | None:
    if not isinstance(record, Mapping):
        return None
    meta = record.get("meta")
    if not isinstance(meta, Mapping):
        return None
    value = meta.get("factory")
    if not isinstance(value, str) or not value.strip():
        return None
    return value


def _payload_factory(record: Mapping[str, Any]) -> str | None:
    """Resolve one unambiguous payload factory declaration.

    Fable preference wrappers predate a wrapper-level ``meta.factory`` and
    carry the declaration on both trajectories instead.  A top-level claim
    remains sufficient for other record kinds, but every factory claim that
    is present on a preference must agree.  Without a wrapper claim, both
    sides must independently attest the same factory.
    """

    root_factory = _declared_factory(record)
    if classify_kind(record) != "preference":
        return root_factory

    side_factories = tuple(_declared_factory(record.get(side)) for side in ("chosen", "rejected"))
    declared = [value for value in (root_factory, *side_factories) if value]
    if len(set(declared)) > 1:
        return None
    if root_factory is not None:
        return root_factory
    if all(side_factories) and side_factories[0] == side_factories[1]:
        return side_factories[0]
    return None


def _canonical_id(source: _SourceIdentity, kind: str, role: str) -> str:
    preimage = canonical_json(
        {
            "namespace": ID_NAMESPACE,
            "transform_version": TRANSFORM_VERSION,
            "source_path": source.path,
            "source_line": source.line,
            "record_kind": kind,
            "owner_role": role,
        }
    )
    digest = hashlib.sha256(preimage.encode("utf-8")).hexdigest()
    role_name = "record" if role == "/" else "trajectory"
    return f"sfcur-{kind}-{role_name}-{digest}"


canonical_id = _canonical_id


def _pointer(base: str, key: str) -> str:
    escaped = key.replace("~", "~0").replace("/", "~1")
    return f"/{escaped}" if base == "/" else f"{base}/{escaped}"


def _legacy_ids(owner: Mapping[str, Any], owner_path: str) -> list[dict[str, Any]]:
    forms: list[dict[str, Any]] = []

    def collect(container: Any, base: str) -> None:
        if not isinstance(container, Mapping):
            return
        for key in LEGACY_ID_KEYS:
            if key in container:
                forms.append({"path": _pointer(base, key), "value": copy.deepcopy(container[key])})

    collect(owner, owner_path)
    collect(owner.get("meta"), _pointer(owner_path, "meta"))
    collect(owner.get("state"), _pointer(owner_path, "state"))
    return forms


def _discover_original_ids(
    record: Any,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Collect reversible IDs without granting shape or factory authority.

    This walk intentionally uses only safely discoverable object boundaries.
    It therefore remains useful on malformed or unauthorized wrappers without
    treating those wrappers as valid owner specifications.
    """

    if not isinstance(record, Mapping):
        return [], []
    root_ids = _legacy_ids(record, "/")
    all_ids = list(root_ids)
    nested = [(f"/{side}", record.get(side)) for side in ("chosen", "rejected")]
    view = record.get("language_view")
    if isinstance(view, Mapping):
        nested.append(("/language_view/trajectory", view.get("trajectory")))
    for owner_path, owner in nested:
        if isinstance(owner, Mapping):
            all_ids.extend(_legacy_ids(owner, owner_path))
    return root_ids, all_ids


def _owner_specs(
    record: Mapping[str, Any],
    kind: str,
    allowed_preference_side_kinds: frozenset[str] | None = None,
) -> list[tuple[str, Mapping[str, Any]]]:
    if kind == "thalamic":
        return [("/", record)]
    if kind == "preference":
        owners = []
        for side in ("chosen", "rejected"):
            owner = record.get(side)
            if not isinstance(owner, Mapping):
                raise IdentityCurationError(f"preference {side} must be an object")
            owners.append((f"/{side}", owner))
        side_kinds = preference_side_kinds(record)
        if side_kinds[0] != side_kinds[1] or side_kinds[0] not in PREFERENCE_SIDE_KINDS:
            raise IdentityCurationError(
                "preference sides must be a homogeneous episode or thalamic pair "
                f"(got chosen={side_kinds[0]}, rejected={side_kinds[1]})"
            )
        if (
            allowed_preference_side_kinds is not None
            and side_kinds[0] not in allowed_preference_side_kinds
        ):
            raise IdentityCurationError(
                "preference side kind is not authorized by the factory contract "
                f"(got {side_kinds[0]}, allowed="
                f"{sorted(allowed_preference_side_kinds)})"
            )
        return owners
    if kind == "bridge_pair":
        language_view = record.get("language_view")
        if not isinstance(language_view, Mapping):
            raise IdentityCurationError("bridge language_view must be an object")
        trajectory = language_view.get("trajectory")
        if not isinstance(trajectory, Mapping):
            raise IdentityCurationError("bridge language_view.trajectory must be an object")
        return [("/language_view/trajectory", trajectory)]
    return []


def _provenance_snapshot(owner: Mapping[str, Any], state: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "sim_or_real": {
            "present": "sim_or_real" in state,
            "value": copy.deepcopy(state.get("sim_or_real")),
        },
        "state_provenance": {
            "present": "provenance" in state,
            "value": copy.deepcopy(state.get("provenance")),
        },
        "owner_provenance": {
            "present": "provenance" in owner,
            "value": copy.deepcopy(owner.get("provenance")),
        },
    }


def _map_claim(claimed: Any) -> str | None:
    if not isinstance(claimed, str) or not claimed.strip():
        return None
    value = claimed.strip().lower()
    if value in CANONICAL_PROVENANCE:
        return value
    # Preserve the repository's documented first-match order.  A synthetic
    # narrative claiming live/production use remains designed even if it also
    # mentions simulated or HIL calibration.
    if _is_real_world_claim(value):
        return "designed"
    if "simulation" in value or "simulat" in value or "high-fidelity" in value:
        return "simulated"
    if "hardware-in-the-loop" in value or HIL_RE.search(value):
        return "hil"
    return None


def _existing_claimed(provenance: Any, kind: str) -> Any:
    if not isinstance(provenance, Mapping) or provenance.get("kind") != kind:
        return None
    return copy.deepcopy(provenance.get("claimed"))


def _is_real_world_claim(value: Any) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    normalized = value.strip().casefold()
    return bool(
        REAL_WORLD_RE.match(normalized)
        or "actions live" in normalized
        or "production" in normalized
    )


def _resolve_provenance(
    owner: Mapping[str, Any], state: Mapping[str, Any]
) -> tuple[str | None, Any, str]:
    state_value = state.get("sim_or_real") if "sim_or_real" in state else None
    kind = _map_claim(state_value)
    if kind is not None:
        # On a second pass over already-curated output, recover the original
        # claim so normalization remains idempotent rather than replacing it
        # with the canonical state value.
        if isinstance(state_value, str) and state_value.strip().lower() == kind:
            claimed = _existing_claimed(state.get("provenance"), kind)
            if claimed is None:
                claimed = _existing_claimed(owner.get("provenance"), kind)
            if claimed is None:
                claimed = copy.deepcopy(state_value)
        else:
            claimed = copy.deepcopy(state_value)
        return kind, claimed, "state.sim_or_real"

    for basis, provenance in (
        ("state.provenance.kind", state.get("provenance")),
        ("owner.provenance.kind", owner.get("provenance")),
    ):
        if not isinstance(provenance, Mapping):
            continue
        candidate = provenance.get("kind")
        if candidate in CANONICAL_PROVENANCE:
            return str(candidate), copy.deepcopy(provenance.get("claimed")), basis
    return None, copy.deepcopy(state_value), "unresolved"


def _source_mapping(source: _SourceIdentity) -> dict[str, Any]:
    return {
        "path": source.path,
        "line": source.line,
        "sha256": source.sha256,
        "hash_basis": source.hash_basis,
        "original": source.original,
    }


def _base_mapping(
    source: _SourceIdentity,
    kind: str,
    root_original_ids: list[dict[str, Any]],
    registry: FactoryRegistry,
    row: FactoryRow | None,
    contract: str | None,
) -> dict[str, Any]:
    return {
        "transform": {"name": TRANSFORM_NAME, "version": TRANSFORM_VERSION},
        "source": _source_mapping(source),
        "factory": source.factory,
        "record_kind": kind,
        "original_ids": root_original_ids,
        "path_id": source.factory,
        "factory_id": None if row is None else row.payload_factory,
        "identity_authoritative": False if row is None else row.identity_authoritative,
        "provenance_contract": contract,
        "registry": {
            "schema_version": registry.schema_version,
            "sha256": registry.sha256,
        },
    }


def _exclude(mapping: dict[str, Any], reason: str, **extra: Any) -> CurationResult:
    payload = {"action": "exclude", "reason_codes": [reason]}
    payload.update(extra)
    mapping.update(payload)
    return CurationResult("exclude", None, mapping)


def _payload_has_state_claim(
    record: Mapping[str, Any], owner_specs: list[tuple[str, Mapping[str, Any]]]
) -> bool:
    owners = owner_specs if owner_specs else [("/", record)]
    return any(
        isinstance(state := owner.get("state"), Mapping)
        and ("sim_or_real" in state or "provenance" in state)
        for _path, owner in owners
    )


def _training_ready_true_paths(value: Any, path: str = "$") -> list[str]:
    paths: list[str] = []
    if isinstance(value, Mapping):
        if value.get("training_ready"):
            paths.append(f"{path}.training_ready")
        for key, item in value.items():
            paths.extend(_training_ready_true_paths(item, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            paths.extend(_training_ready_true_paths(item, f"{path}[{index}]"))
    return paths


def _residual_real_claim_paths(value: Any, path: str = "$") -> list[str]:
    paths: list[str] = []
    if isinstance(value, Mapping):
        sim_or_real = value.get("sim_or_real")
        if _is_real_world_claim(sim_or_real):
            paths.append(f"{path}.sim_or_real")
        provenance = value.get("provenance")
        if isinstance(provenance, Mapping):
            provenance_kind = provenance.get("kind")
            if _is_real_world_claim(provenance_kind):
                paths.append(f"{path}.provenance.kind")
        for key, item in value.items():
            paths.extend(_residual_real_claim_paths(item, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            paths.extend(_residual_real_claim_paths(item, f"{path}[{index}]"))
    return paths


def _shape_validation_errors(
    record: Mapping[str, Any],
    kind: str,
    owner_specs: list[tuple[str, Mapping[str, Any]]] | None = None,
) -> list[str]:
    def structural_thalamic_errors(
        owner: Mapping[str, Any], owner_where: str
    ) -> list[str]:
        # Identity intentionally accepts the legacy provenance vocabulary and
        # canonicalizes it below. Every other Thalamic invariant is
        # structural and must pass before the record can enter a cleaned tree.
        return [
            error
            for error in check_thalamic(owner, owner_where)
            if not error.startswith(f"{owner_where}: state.sim_or_real must ")
        ]

    if kind == "thalamic":
        return structural_thalamic_errors(record, "record")
    if kind == "episode":
        return check_episode(record, "record")
    if kind == "preference":
        errors: list[str] = []
        if owner_specs is None:
            try:
                owner_specs = _owner_specs(record, kind)
            except IdentityCurationError as exc:
                return [str(exc)]
        side_specs = tuple(zip(owner_specs, preference_side_kinds(record), strict=True))
        if "goal" in record and any(
            side_kind == "episode" and "goal" not in owner
            for ((_owner_path, owner), side_kind) in side_specs
        ):
            wrapper_goal = record["goal"]
            if not isinstance(wrapper_goal, str) or not wrapper_goal.strip():
                errors.append("record: inherited goal must be a non-empty string")
        for (owner_path, owner), side_kind in side_specs:
            if side_kind == "episode":
                errors.extend(
                    check_episode(
                        owner,
                        f"record{owner_path}",
                        require_goal="goal" not in record,
                    )
                )
            elif side_kind == "thalamic":
                where = f"record{owner_path}"
                errors.extend(structural_thalamic_errors(owner, where))
            else:
                errors.append(f"record{owner_path}: unsupported preference-side shape")
        return errors
    if kind == "bridge_pair":
        errors: list[str] = []
        events = record.get("spike_events")
        if not isinstance(events, list) or not events:
            errors.append("record: spike_events must be a non-empty array")
        else:
            errors.extend(check_spike_order(events, "record", enclosing=record))
        language_view = record.get("language_view")
        if not isinstance(language_view, Mapping):
            errors.append("record: language_view must be an object")
        else:
            trajectory = language_view.get("trajectory")
            if not isinstance(trajectory, Mapping):
                errors.append(
                    "record: language_view.trajectory missing or not an object"
                )
            else:
                errors.extend(
                    structural_thalamic_errors(
                        trajectory, "record.language_view.trajectory"
                    )
                )
        return errors
    if kind == "safety_case":
        return check_safety_case(record, "record")
    if kind == "multi_agent":
        return check_multi_agent(record, "record")
    return []


def _collect_state_resolutions(
    owner_specs: list[tuple[str, Mapping[str, Any]]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    provenance_resolutions: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []
    for owner_path, owner in owner_specs:
        state = owner.get("state")
        state_path = _pointer(owner_path, "state")
        if not isinstance(state, Mapping):
            unresolved.append(
                {
                    "path": state_path,
                    "reason": "missing_or_non_object_state",
                    "original": copy.deepcopy(state),
                }
            )
            continue
        snapshot = _provenance_snapshot(owner, state)
        provenance_kind, claimed, basis = _resolve_provenance(owner, state)
        if provenance_kind is None:
            unresolved.append(
                {
                    "path": state_path,
                    "reason": "unresolved_provenance",
                    "original": snapshot,
                }
            )
            continue
        if provenance_kind == "real":
            raise IdentityCurationError("identity must never emit provenance.kind=real")
        provenance_resolutions.append(
            {
                "owner_path": owner_path,
                "state_path": state_path,
                "kind": provenance_kind,
                "claimed": claimed,
                "basis": basis,
                "original": snapshot,
            }
        )
    return provenance_resolutions, unresolved


def _provenance_mapping_sha256(mapping: Mapping[str, Any]) -> str:
    payload = dict(mapping)
    payload.pop("mapping_sha256", None)
    return sha256_json(payload)


def _seal_provenance_mapping(mapping: Mapping[str, Any]) -> dict[str, Any]:
    sealed = copy.deepcopy(dict(mapping))
    sealed["mapping_sha256"] = _provenance_mapping_sha256(sealed)
    return sealed


def _assign_nested_ids(
    curated: dict[str, Any],
    original: Mapping[str, Any],
    source: _SourceIdentity,
    kind: str,
    owner_specs: list[tuple[str, Mapping[str, Any]]],
    output_id: str,
    root_original_ids: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    id_mappings: list[dict[str, Any]] = [
        {
            "owner_path": "/",
            "original_ids": root_original_ids,
            "output_id": output_id,
        }
    ]
    curated_owners = dict(_owner_specs(curated, kind)) if owner_specs else {}
    for owner_path, _owner in owner_specs:
        if owner_path == "/":
            continue
        nested_id = _canonical_id(source, kind, owner_path)
        curated_owners[owner_path]["id"] = nested_id
        original_owner = dict(_owner_specs(original, kind))[owner_path]
        id_mappings.append(
            {
                "owner_path": owner_path,
                "original_ids": _legacy_ids(original_owner, owner_path),
                "output_id": nested_id,
            }
        )
    return id_mappings


def _curated_resolve_owners(
    curated: dict[str, Any],
    kind: str,
    resolve_owners: list[tuple[str, Mapping[str, Any]]],
) -> list[tuple[str, Mapping[str, Any]]]:
    specs = _owner_specs(curated, kind)
    if specs:
        return specs
    if resolve_owners:
        return [("/", curated)]
    return []


def _apply_resolved_state(
    curated: dict[str, Any],
    original: Mapping[str, Any],
    source: _SourceIdentity,
    kind: str,
    native_owner_specs: list[tuple[str, Mapping[str, Any]]],
    resolve_owners: list[tuple[str, Mapping[str, Any]]],
    resolutions: list[dict[str, Any]],
    output_id: str,
    root_original_ids: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    id_mappings = _assign_nested_ids(
        curated,
        original,
        source,
        kind,
        native_owner_specs,
        output_id,
        root_original_ids,
    )
    curated_owners = _curated_resolve_owners(curated, kind, resolve_owners)
    provenance_mappings: list[dict[str, Any]] = []
    canonical_provenances: list[dict[str, Any]] = []
    for resolution, (owner_path, owner) in zip(resolutions, curated_owners, strict=True):
        state = owner["state"]
        canonical_provenance = {
            "kind": resolution["kind"],
            "claimed": copy.deepcopy(resolution["claimed"]),
        }
        if canonical_provenance["kind"] == "real":
            raise IdentityCurationError("identity must never emit provenance.kind=real")
        state["sim_or_real"] = resolution["kind"]
        state["provenance"] = copy.deepcopy(canonical_provenance)
        owner["provenance"] = copy.deepcopy(canonical_provenance)
        canonical_provenances.append(canonical_provenance)
        provenance_mappings.append(
            _seal_provenance_mapping(
                {
                    "owner_path": owner_path,
                    "state_path": resolution["state_path"],
                    "basis": resolution["basis"],
                    "original": resolution["original"],
                    "canonical": copy.deepcopy(canonical_provenance),
                }
            )
        )

    if kind in {"preference", "bridge_pair"}:
        kinds = {item["kind"] for item in canonical_provenances}
        if len(kinds) == 1:
            wrapper_kind = next(iter(kinds))
            claims = [item["claimed"] for item in canonical_provenances]
            wrapper_claimed = (
                claims[0]
                if all(_canonical_json_equal(item, claims[0]) for item in claims)
                else claims
            )
        else:
            wrapper_kind = "unknown"
            wrapper_claimed = [item["claimed"] for item in canonical_provenances]
        curated["provenance"] = {
            "kind": wrapper_kind,
            "claimed": copy.deepcopy(wrapper_claimed),
        }
        provenance_mappings.append(
            _seal_provenance_mapping(
                {
                    "owner_path": "/",
                    "basis": "nested_trajectory_aggregate",
                    "original": {
                        "owner_provenance": {
                            "present": "provenance" in original,
                            "value": copy.deepcopy(original.get("provenance")),
                        }
                    },
                    "canonical": copy.deepcopy(curated["provenance"]),
                }
            )
        )
    elif kind in {"episode", "safety_case", "multi_agent"} and resolutions:
        root = {
            "kind": resolutions[0]["kind"],
            "claimed": copy.deepcopy(resolutions[0]["claimed"]),
            "basis": resolutions[0]["basis"],
        }
        curated["provenance"] = root
        provenance_mappings.append(
            _seal_provenance_mapping(
                {
                    "owner_path": "/",
                    "basis": resolutions[0]["basis"],
                    "original": {
                        "owner_provenance": {
                            "present": "provenance" in original,
                            "value": copy.deepcopy(original.get("provenance")),
                        }
                    },
                    "canonical": copy.deepcopy(root),
                }
            )
        )
    return id_mappings, provenance_mappings


def _apply_shape_designed(
    curated: dict[str, Any],
    original: Mapping[str, Any],
    source: _SourceIdentity,
    kind: str,
    owner_specs: list[tuple[str, Mapping[str, Any]]],
    output_id: str,
    root_original_ids: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    basis = SHAPE_BASIS[kind]
    designed = {"kind": "designed", "claimed": None, "basis": basis}
    original_provenance = {
        "present": "provenance" in original,
        "value": copy.deepcopy(original.get("provenance")),
    }
    curated["provenance"] = copy.deepcopy(designed)
    id_mappings = _assign_nested_ids(
        curated, original, source, kind, owner_specs, output_id, root_original_ids
    )
    provenance_mappings = [
        _seal_provenance_mapping(
            {
                "owner_path": "/",
                "basis": basis,
                "original": {"owner_provenance": original_provenance},
                "canonical": copy.deepcopy(designed),
            }
        )
    ]
    if owner_specs:
        original_owners = dict(_owner_specs(original, kind))
        for owner_path, owner in _owner_specs(curated, kind):
            nested_designed = {
                "kind": "designed",
                "claimed": None,
                "basis": basis,
            }
            owner["provenance"] = copy.deepcopy(nested_designed)
            original_owner = original_owners[owner_path]
            provenance_mappings.append(
                _seal_provenance_mapping(
                    {
                        "owner_path": owner_path,
                        "basis": basis,
                        "original": {
                            "owner_provenance": {
                                "present": "provenance" in original_owner,
                                "value": copy.deepcopy(original_owner.get("provenance")),
                            }
                        },
                        "canonical": copy.deepcopy(nested_designed),
                    }
                )
            )
    return id_mappings, provenance_mappings


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
    try:
        kind = record_kind(original)
        kind_error = None
    except IdentityCurationError as exc:
        kind = "unknown"
        kind_error = exc
    root_original_ids, all_original_ids = _discover_original_ids(original)
    contract = None
    if row is not None and kind != "unknown":
        contract = row.provenance_contract_by_kind.get(kind)
    mapping = _base_mapping(source, kind, root_original_ids, registry, row, contract)
    mapping["original_ids"] = all_original_ids
    if kind_error is not None:
        return _exclude(
            mapping,
            "identity.unsupported_record_shape",
            details=[str(kind_error)],
        )
    if row is None:
        return _exclude(mapping, "identity.unknown_factory")
    payload_factory = _payload_factory(original)
    if payload_factory != row.payload_factory:
        return _exclude(
            mapping,
            "identity.factory_path_payload_mismatch",
            details=[
                {
                    "path_id": row.path_id,
                    "expected_payload_factory": row.payload_factory,
                    "payload_factory": payload_factory,
                }
            ],
        )
    if kind not in row.record_kinds:
        return _exclude(
            mapping,
            "identity.factory_not_authorized_for_kind",
            details=[
                {
                    "record_kind": kind,
                    "authorized_kinds": sorted(row.record_kinds),
                }
            ],
        )
    if not row.identity_authoritative:
        return _exclude(mapping, "identity.factory_not_identity_authoritative")
    if contract not in ALLOWED_CONTRACTS:
        return _exclude(
            mapping,
            "identity.factory_contract_invalid",
            details=[{"record_kind": kind, "provenance_contract": contract}],
        )
    if row.training_ready_policy == "never":
        ready_claims = _training_ready_true_paths(original)
        if ready_claims:
            return _exclude(
                mapping,
                "identity.training_ready_policy_violation",
                details=[{"paths": ready_claims, "policy": "never"}],
            )
    try:
        owner_specs = _owner_specs(
            original,
            kind,
            row.preference_side_kinds if kind == "preference" else None,
        )
    except IdentityCurationError as exc:
        return _exclude(mapping, "identity.invalid_nested_shape", details=[str(exc)])

    shape_errors = _shape_validation_errors(original, kind, owner_specs)
    if shape_errors:
        return _exclude(
            mapping,
            "identity.invalid_payload_shape",
            details=shape_errors,
        )

    use_state = contract == CONTRACT_REQUIRE_STATE or _payload_has_state_claim(
        original, owner_specs
    )
    state_owners = owner_specs if owner_specs else [("/", original)]
    if use_state:
        resolutions, unresolved = _collect_state_resolutions(state_owners)
        if unresolved:
            return _exclude(
                mapping,
                "identity.unresolved_provenance",
                unresolved_provenance=unresolved,
            )
        apply_owners = state_owners
    else:
        if kind not in SHAPE_BASIS:
            return _exclude(
                mapping,
                "identity.factory_contract_invalid",
                details=[{"record_kind": kind, "provenance_contract": contract}],
            )
        resolutions = []
        apply_owners = owner_specs

    curated: dict[str, Any] = copy.deepcopy(dict(original))
    output_id = _canonical_id(source, kind, "/")
    curated["id"] = output_id

    if use_state:
        id_mappings, provenance_mappings = _apply_resolved_state(
            curated,
            original,
            source,
            kind,
            owner_specs,
            apply_owners,
            resolutions,
            output_id,
            root_original_ids,
        )
    else:
        id_mappings, provenance_mappings = _apply_shape_designed(
            curated,
            original,
            source,
            kind,
            apply_owners,
            output_id,
            root_original_ids,
        )

    residual_real_claims = _residual_real_claim_paths(curated)
    if residual_real_claims:
        return _exclude(
            mapping,
            "identity.unowned_real_claim",
            details=[{"paths": residual_real_claims}],
        )

    mapping.update(
        {
            "action": "retained",
            "reason_codes": ["identity.assigned", "provenance.canonicalized"],
            "output_id": output_id,
            "output_sha256": sha256_json(curated),
            "id_mappings": id_mappings,
            "provenance_mappings": provenance_mappings,
        }
    )
    return CurationResult("retained", curated, mapping)


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
        if result.action == "retained":
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
        results.append(result)
    return tuple(results)


def _is_under_raw(path: Path) -> bool:
    parts = path.resolve(strict=False).parts
    return any(parts[index : index + 2] == ("outputs", "raw") for index in range(len(parts) - 1))


def _write_exclusive(path: Path, payload: bytes) -> None:
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


def _pointer_value(value: Any, pointer: str) -> Any:
    if pointer == "/":
        return value
    if not isinstance(pointer, str) or not pointer.startswith("/"):
        raise IdentityTreeError(f"invalid owner_path: {pointer!r}")
    current = value
    for raw_part in pointer[1:].split("/"):
        part = raw_part.replace("~1", "/").replace("~0", "~")
        if isinstance(current, Mapping) and part in current:
            current = current[part]
        else:
            raise IdentityTreeError(f"owner_path does not exist: {pointer}")
    return current


def _hash_verified_manifest_source(source_meta: Mapping[str, Any], index: int) -> SourceRecord:
    """Recover one source record from internally hash-consistent manifest evidence.

    The adjacent digest detects corruption relative to the embedded snapshot. It
    is not an external authenticity anchor; callers need ``expected_manifest_digest``
    for tamper-evident validation of the manifest as a whole.
    """

    where = f"IDENTITY-MANIFEST.json[{index}].source"
    try:
        source_path, _factory = _normalize_source_path(source_meta.get("path"))
    except IdentityCurationError as exc:
        raise IdentityTreeError(f"{where}.path is invalid: {exc}") from exc
    source_line = source_meta.get("line")
    if not isinstance(source_line, int) or isinstance(source_line, bool) or source_line < 1:
        raise IdentityTreeError(f"{where}.line must be positive")
    source_sha256 = source_meta.get("sha256")
    if not isinstance(source_sha256, str) or not SHA256_RE.fullmatch(source_sha256):
        raise IdentityTreeError(f"{where}.sha256 must be a SHA-256")
    hash_basis = source_meta.get("hash_basis")
    if hash_basis not in {"canonical-json-sha256", "source-json-line-sha256"}:
        raise IdentityTreeError(f"{where}.hash_basis is invalid")
    original = source_meta.get("original")
    if not isinstance(original, str) or not original or _is_json_whitespace(original):
        raise IdentityTreeError(f"{where}.original must be a hash-verifiable JSONL snapshot")
    if "\n" in original:
        raise IdentityTreeError(f"{where}.original must contain exactly one JSONL record")
    if sha256_bytes(original.encode("utf-8")) != source_sha256:
        raise IdentityTreeError(f"{where}.original does not match source.sha256")
    try:
        original_record = _strict_json_loads(original)
    except (json.JSONDecodeError, ValueError) as exc:
        raise IdentityTreeError(f"{where}.original is not strict JSON: {exc}") from exc
    if hash_basis == "canonical-json-sha256" and original != canonical_json(original_record):
        raise IdentityTreeError(f"{where}.original does not match canonical-json-sha256 basis")
    digest = None if hash_basis == "canonical-json-sha256" else source_sha256
    return SourceRecord(original_record, source_path, source_line, digest, original)


def _validate_presence_snapshot(snapshot: Any, where: str) -> tuple[bool, Any]:
    if not isinstance(snapshot, Mapping) or set(snapshot) != {"present", "value"}:
        raise IdentityTreeError(f"{where} must contain exactly boolean present and value")
    present = snapshot["present"]
    value = snapshot["value"]
    if not isinstance(present, bool):
        raise IdentityTreeError(f"{where}.present must be a boolean")
    if not present and value is not None:
        raise IdentityTreeError(f"{where}.value must be null when absent")
    return present, value


def _validate_provenance_original(
    provenance_mapping: Mapping[str, Any],
    canonical: Mapping[str, Any],
    where: str,
) -> None:
    original = provenance_mapping.get("original")
    state_path = provenance_mapping.get("state_path")
    if state_path is None:
        if not isinstance(original, Mapping) or set(original) != {"owner_provenance"}:
            raise IdentityTreeError(f"{where}.original must contain exactly owner_provenance")
        _validate_presence_snapshot(
            original["owner_provenance"],
            f"{where}.original.owner_provenance",
        )
        return

    expected = {"sim_or_real", "state_provenance", "owner_provenance"}
    if not isinstance(original, Mapping) or set(original) != expected:
        raise IdentityTreeError(
            f"{where}.original must contain the complete state provenance snapshot"
        )
    snapshots = {
        key: _validate_presence_snapshot(original[key], f"{where}.original.{key}")
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
    resolved_kind, resolved_claimed, resolved_basis = _resolve_provenance(
        original_owner, original_state
    )
    if (
        resolved_kind != canonical.get("kind")
        or not _canonical_json_equal(resolved_claimed, canonical.get("claimed"))
        or resolved_basis != provenance_mapping.get("basis")
    ):
        raise IdentityTreeError(f"{where}.original does not resolve to its canonical provenance")


def _aggregate_owner_provenance(
    record: Mapping[str, Any], owner_paths: list[str]
) -> dict[str, Any]:
    nested: list[Mapping[str, Any]] = []
    for owner_path in owner_paths:
        if owner_path == "/":
            continue
        owner = _pointer_value(record, owner_path)
        provenance = owner.get("provenance") if isinstance(owner, Mapping) else None
        if not isinstance(provenance, Mapping):
            raise IdentityTreeError(f"provenance mapping owner {owner_path} lacks provenance")
        nested.append(provenance)
    if not nested:
        raise IdentityTreeError("aggregate provenance mapping has no nested owners")
    kinds = {item.get("kind") for item in nested}
    claims = [copy.deepcopy(item.get("claimed")) for item in nested]
    if len(kinds) == 1:
        aggregate_kind = next(iter(kinds))
        aggregate_claimed = (
            claims[0] if all(_canonical_json_equal(item, claims[0]) for item in claims) else claims
        )
    else:
        aggregate_kind = "unknown"
        aggregate_claimed = claims
    return {"kind": aggregate_kind, "claimed": aggregate_claimed}


def _expected_provenance_by_target(
    expected_mapping: Mapping[str, Any], index: int
) -> dict[tuple[str, str | None], Mapping[str, Any]]:
    """Index the provenance plan replayed from the hash-verified source snapshot."""

    expected_mappings = expected_mapping.get("provenance_mappings")
    if not isinstance(expected_mappings, list) or not expected_mappings:
        raise IdentityTreeError(
            f"IDENTITY-MANIFEST.json[{index}] hash-verified source replay "
            "did not produce provenance mappings"
        )
    by_target: dict[tuple[str, str | None], Mapping[str, Any]] = {}
    for provenance_mapping in expected_mappings:
        if not isinstance(provenance_mapping, Mapping):
            raise IdentityTreeError(
                f"IDENTITY-MANIFEST.json[{index}] hash-verified source replay "
                "produced an invalid provenance mapping"
            )
        owner_path = provenance_mapping.get("owner_path")
        state_path = provenance_mapping.get("state_path")
        if not isinstance(owner_path, str) or (
            state_path is not None and not isinstance(state_path, str)
        ):
            raise IdentityTreeError(
                f"IDENTITY-MANIFEST.json[{index}] hash-verified source replay "
                "produced an invalid provenance target"
            )
        target = (owner_path, state_path)
        if target in by_target:
            raise IdentityTreeError(
                f"IDENTITY-MANIFEST.json[{index}] hash-verified source replay "
                "repeated a provenance target"
            )
        by_target[target] = provenance_mapping
    return by_target


def _validate_manifest_provenance(
    mapping: Mapping[str, Any],
    record: Mapping[str, Any],
    index: int,
    kind: str,
    owner_paths: list[str],
    expected_mapping: Mapping[str, Any],
) -> None:
    mappings = mapping.get("provenance_mappings")
    if not isinstance(mappings, list) or not mappings:
        raise IdentityTreeError(
            f"IDENTITY-MANIFEST.json[{index}].provenance_mappings must be a non-empty list"
        )
    allowed_owners = set(owner_paths)
    covered_owners: set[str] = set()
    seen_targets: set[tuple[str, str | None]] = set()
    mappings_by_target: dict[tuple[str, str | None], Mapping[str, Any]] = {}
    for nested_index, provenance_mapping in enumerate(mappings):
        where = f"IDENTITY-MANIFEST.json[{index}].provenance_mappings[{nested_index}]"
        if not isinstance(provenance_mapping, Mapping):
            raise IdentityTreeError(f"{where} must be an object")
        mapping_sha256 = provenance_mapping.get("mapping_sha256")
        if (
            not isinstance(mapping_sha256, str)
            or not SHA256_RE.fullmatch(mapping_sha256)
            or mapping_sha256 != _provenance_mapping_sha256(provenance_mapping)
        ):
            raise IdentityTreeError(f"{where} provenance mapping digest is invalid")
        owner_path = provenance_mapping.get("owner_path")
        if not isinstance(owner_path, str) or owner_path not in allowed_owners:
            raise IdentityTreeError(f"{where}.owner_path does not name an emitted owner")
        owner = _pointer_value(record, owner_path)
        if not isinstance(owner, Mapping):
            raise IdentityTreeError(f"{where}.owner_path must name an object")
        state_path = provenance_mapping.get("state_path")
        if state_path is not None and not isinstance(state_path, str):
            raise IdentityTreeError(f"{where}.state_path must be a string")
        target = (owner_path, state_path)
        if target in seen_targets:
            raise IdentityTreeError(f"{where} repeats a provenance mapping target")
        seen_targets.add(target)
        mappings_by_target[target] = provenance_mapping
        covered_owners.add(owner_path)

        basis = provenance_mapping.get("basis")
        canonical = provenance_mapping.get("canonical")
        if not isinstance(basis, str) or not basis:
            raise IdentityTreeError(f"{where}.basis must be a non-empty string")
        if not isinstance(canonical, Mapping) or "claimed" not in canonical:
            raise IdentityTreeError(f"{where}.canonical must be a provenance object")
        canonical_kind = canonical.get("kind")
        allowed_kinds = set(CANONICAL_PROVENANCE)
        if basis == "nested_trajectory_aggregate":
            allowed_kinds.add("unknown")
        if canonical_kind not in allowed_kinds:
            raise IdentityTreeError(f"{where}.canonical.kind is invalid")

        if state_path is not None:
            expected_state_path = _pointer(owner_path, "state")
            if state_path != expected_state_path:
                raise IdentityTreeError(f"{where}.state_path does not belong to owner_path")
            state = _pointer_value(record, state_path)
            if not isinstance(state, Mapping):
                raise IdentityTreeError(f"{where}.state_path must name an object")
            if not _canonical_json_equal(state.get("provenance"), canonical):
                raise IdentityTreeError(
                    f"{where}.canonical does not match emitted state provenance"
                )
            owner_provenance = owner.get("provenance")
            if (
                not isinstance(owner_provenance, Mapping)
                or owner_provenance.get("kind") != canonical_kind
                or not _canonical_json_equal(
                    owner_provenance.get("claimed"), canonical.get("claimed")
                )
                or state.get("sim_or_real") != canonical_kind
            ):
                raise IdentityTreeError(f"{where}.canonical does not match its emitted owner")
        else:
            if not _canonical_json_equal(owner.get("provenance"), canonical):
                raise IdentityTreeError(
                    f"{where}.canonical does not match emitted owner provenance"
                )
            if "basis" in canonical and canonical.get("basis") != basis:
                raise IdentityTreeError(f"{where}.basis does not match canonical provenance")
            if basis == "nested_trajectory_aggregate":
                if owner_path != "/" or not _canonical_json_equal(
                    canonical, _aggregate_owner_provenance(record, owner_paths)
                ):
                    raise IdentityTreeError(f"{where}.canonical does not match nested provenance")
            elif basis in SHAPE_BASIS.values():
                expected = {
                    "kind": "designed",
                    "claimed": None,
                    "basis": SHAPE_BASIS.get(kind),
                }
                if basis != SHAPE_BASIS.get(kind) or not _canonical_json_equal(canonical, expected):
                    raise IdentityTreeError(f"{where}.canonical does not match the shape contract")
        _validate_provenance_original(provenance_mapping, canonical, where)

    required_owners = {
        owner_path
        for owner_path in owner_paths
        if isinstance(owner := _pointer_value(record, owner_path), Mapping)
        and isinstance(owner.get("provenance"), Mapping)
    }
    if covered_owners != required_owners:
        raise IdentityTreeError(
            f"IDENTITY-MANIFEST.json[{index}].provenance_mappings owner paths "
            "do not match emitted provenance owners"
        )
    expected_by_target = _expected_provenance_by_target(expected_mapping, index)
    expected_targets = set(expected_by_target)
    if seen_targets != expected_targets:
        raise IdentityTreeError(
            f"IDENTITY-MANIFEST.json[{index}].provenance mapping targets do not "
            "match the hash-verified source replay"
        )
    for owner_path, state_path in expected_targets:
        if state_path is not None:
            continue
        owner_mapping = mappings_by_target[(owner_path, None)]
        basis = owner_mapping["basis"]
        if basis == "nested_trajectory_aggregate" or basis in SHAPE_BASIS.values():
            continue
        state_mapping = mappings_by_target.get((owner_path, _pointer(owner_path, "state")))
        owner_canonical = owner_mapping["canonical"]
        state_canonical = (
            state_mapping.get("canonical") if isinstance(state_mapping, Mapping) else None
        )
        if (
            not isinstance(state_mapping, Mapping)
            or basis != state_mapping.get("basis")
            or not isinstance(owner_canonical, Mapping)
            or not isinstance(state_canonical, Mapping)
            or owner_canonical.get("basis") != basis
            or owner_canonical.get("kind") != state_canonical.get("kind")
            or not _canonical_json_equal(
                owner_canonical.get("claimed"), state_canonical.get("claimed")
            )
        ):
            raise IdentityTreeError(
                f"IDENTITY-MANIFEST.json[{index}] owner provenance basis is not "
                "bound to its original state resolution"
            )
    for target in expected_targets:
        _require_canonical_json_equal(
            mappings_by_target[target],
            expected_by_target[target],
            f"IDENTITY-MANIFEST.json[{index}] provenance mapping for {target}",
        )


def _replay_manifest_mapping(
    mapping: Mapping[str, Any],
    index: int,
    registry: FactoryRegistry,
) -> _ManifestReplay:
    """Replay one mapping before trusting its declared retain/exclude action."""

    action = mapping.get("action")
    if action not in {"retained", "exclude"}:
        raise IdentityTreeError(
            f"IDENTITY-MANIFEST.json[{index}].action must be retained or exclude"
        )
    source_meta = mapping.get("source")
    if not isinstance(source_meta, Mapping):
        raise IdentityTreeError(f"IDENTITY-MANIFEST.json[{index}].source must be an object")
    source_record = _hash_verified_manifest_source(source_meta, index)
    try:
        source_identity = _source_identity(source_record)
        expected_result = curate_record(source_record, registry=registry)
    except IdentityCurationError as exc:
        raise IdentityTreeError(
            f"IDENTITY-MANIFEST.json[{index}] hash-verified source replay failed: {exc}"
        ) from exc
    if action != expected_result.action:
        raise IdentityTreeError(
            f"IDENTITY-MANIFEST.json[{index}].action does not match the hash-verified source replay"
        )
    if expected_result.action == "exclude":
        _require_canonical_json_equal(
            mapping,
            expected_result.mapping,
            f"IDENTITY-MANIFEST.json[{index}] exclusion mapping",
        )
    return _ManifestReplay(source_identity, expected_result)


def _validate_manifest_ids(
    mapping: Mapping[str, Any],
    record: Mapping[str, Any],
    index: int,
    registry: FactoryRegistry,
    replay: _ManifestReplay,
) -> None:
    expected_result = replay.result
    expected_mapping = expected_result.mapping
    if expected_result.action != "retained" or expected_result.record is None:
        raise IdentityTreeError(
            f"IDENTITY-MANIFEST.json[{index}] has output for a replayed exclusion"
        )
    _require_canonical_json_equal(
        mapping.get("original_ids"),
        expected_mapping.get("original_ids"),
        f"IDENTITY-MANIFEST.json[{index}].original_ids",
    )
    _require_canonical_json_equal(
        mapping.get("id_mappings"),
        expected_mapping.get("id_mappings"),
        f"IDENTITY-MANIFEST.json[{index}].id_mappings",
    )

    output_id = mapping.get("output_id")
    if not isinstance(output_id, str) or record.get("id") != output_id:
        raise IdentityTreeError(
            f"IDENTITY-MANIFEST.json[{index}].output_id does not match emitted record"
        )
    kind = mapping.get("record_kind")
    if kind not in SUPPORTED_RECORD_KINDS or classify_kind(record) != kind:
        raise IdentityTreeError(
            f"IDENTITY-MANIFEST.json[{index}].record_kind does not match emitted record"
        )
    source_identity = replay.source
    source_factory = source_identity.factory
    if output_id != _canonical_id(source_identity, kind, "/"):
        raise IdentityTreeError(f"IDENTITY-MANIFEST.json[{index}].output_id is not canonical")
    row = registry.by_path_id.get(source_factory)
    if row is None or kind not in row.record_kinds or not row.identity_authoritative:
        raise IdentityTreeError(f"IDENTITY-MANIFEST.json[{index}] factory authority is invalid")
    contract = row.provenance_contract_by_kind.get(kind)
    if (
        mapping.get("factory") != source_factory
        or mapping.get("path_id") != source_factory
        or mapping.get("factory_id") != row.payload_factory
        or mapping.get("provenance_contract") != contract
        or _payload_factory(record) != row.payload_factory
    ):
        raise IdentityTreeError(
            f"IDENTITY-MANIFEST.json[{index}] factory contract does not match output"
        )
    if row.training_ready_policy == "never" and _training_ready_true_paths(record):
        raise IdentityTreeError(
            f"IDENTITY-MANIFEST.json[{index}] violates training_ready_policy=never"
        )
    if _residual_real_claim_paths(record):
        raise IdentityTreeError(f"IDENTITY-MANIFEST.json[{index}] contains a residual real claim")
    if contract == CONTRACT_SHAPE_DESIGNED and _shape_validation_errors(record, kind):
        raise IdentityTreeError(f"IDENTITY-MANIFEST.json[{index}] output payload shape is invalid")
    try:
        owner_paths = ["/"]
        for owner_path, _owner in _owner_specs(
            record,
            kind,
            row.preference_side_kinds if kind == "preference" else None,
        ):
            if owner_path not in owner_paths:
                owner_paths.append(owner_path)
    except IdentityCurationError as exc:
        raise IdentityTreeError(
            f"IDENTITY-MANIFEST.json[{index}] emitted nested shape is invalid: {exc}"
        ) from exc
    id_mappings = mapping.get("id_mappings")
    if not isinstance(id_mappings, list):
        raise IdentityTreeError(f"IDENTITY-MANIFEST.json[{index}].id_mappings must be a list")
    by_owner: dict[str, str] = {}
    for nested_index, id_mapping in enumerate(id_mappings):
        if not isinstance(id_mapping, Mapping):
            raise IdentityTreeError(
                f"IDENTITY-MANIFEST.json[{index}].id_mappings[{nested_index}] must be an object"
            )
        owner_path = id_mapping.get("owner_path")
        nested_output_id = id_mapping.get("output_id")
        if not isinstance(owner_path, str) or not isinstance(nested_output_id, str):
            raise IdentityTreeError(
                f"IDENTITY-MANIFEST.json[{index}].id_mappings[{nested_index}] "
                "must contain string owner_path and output_id"
            )
        if owner_path in by_owner:
            raise IdentityTreeError(
                f"IDENTITY-MANIFEST.json[{index}].id_mappings repeats {owner_path}"
            )
        by_owner[owner_path] = nested_output_id
    if set(by_owner) != set(owner_paths):
        raise IdentityTreeError(
            f"IDENTITY-MANIFEST.json[{index}].id_mappings owner paths do not match emitted record"
        )
    if by_owner["/"] != output_id:
        raise IdentityTreeError(
            f"IDENTITY-MANIFEST.json[{index}] root id mapping does not match output_id"
        )
    for owner_path, nested_output_id in by_owner.items():
        owner = _pointer_value(record, owner_path)
        if not isinstance(owner, Mapping) or owner.get("id") != nested_output_id:
            raise IdentityTreeError(
                f"IDENTITY-MANIFEST.json[{index}] id mapping for {owner_path} "
                "does not match emitted record"
            )
        if nested_output_id != _canonical_id(source_identity, kind, owner_path):
            raise IdentityTreeError(
                f"IDENTITY-MANIFEST.json[{index}] id mapping for {owner_path} is not canonical"
            )
    _validate_manifest_provenance(
        mapping,
        record,
        index,
        kind,
        owner_paths,
        expected_mapping,
    )
    _require_canonical_json_equal(
        record,
        expected_result.record,
        f"IDENTITY-MANIFEST.json[{index}] output",
    )
    expected_output_sha256 = expected_mapping.get("output_sha256")
    if (
        not isinstance(expected_output_sha256, str)
        or not SHA256_RE.fullmatch(expected_output_sha256)
        or mapping.get("output_sha256") != expected_output_sha256
        or sha256_json(expected_result.record) != expected_output_sha256
        or sha256_json(record) != expected_output_sha256
    ):
        raise IdentityTreeError(
            f"IDENTITY-MANIFEST.json[{index}].output_sha256 does not match the source replay"
        )
    _require_canonical_json_equal(
        mapping,
        expected_mapping,
        f"IDENTITY-MANIFEST.json[{index}] retained mapping",
    )


def _expected_identity_outputs(
    manifest: list[Any], registry: FactoryRegistry
) -> dict[str, dict[int, tuple[int, Mapping[str, Any], _ManifestReplay]]]:
    expected: dict[str, dict[int, tuple[int, Mapping[str, Any], _ManifestReplay]]] = {}
    seen_coordinates: dict[tuple[str, int], int] = {}
    for index, mapping in enumerate(manifest):
        if not isinstance(mapping, Mapping):
            raise IdentityTreeError(f"IDENTITY-MANIFEST.json[{index}] must be an object")
        registry_meta = mapping.get("registry")
        pin = registry_meta.get("sha256") if isinstance(registry_meta, Mapping) else None
        if pin != registry.sha256:
            raise IdentityTreeError(
                f"IDENTITY-MANIFEST.json[{index}] registry.sha256 does not match sidecar pin"
            )
        replay = _replay_manifest_mapping(mapping, index, registry)
        source = replay.source
        coordinate = (source.path, source.line)
        if coordinate in seen_coordinates:
            raise IdentityTreeError(
                f"IDENTITY-MANIFEST.json repeats source coordinate "
                f"{source.path}:{source.line} at entries "
                f"{seen_coordinates[coordinate]} and {index}"
            )
        seen_coordinates[coordinate] = index
        if replay.result.action != "retained":
            continue
        expected_mapping = replay.result.mapping
        output_sha256 = expected_mapping.get("output_sha256")
        if not isinstance(output_sha256, str) or not SHA256_RE.fullmatch(output_sha256):
            raise IdentityTreeError(
                f"IDENTITY-MANIFEST.json[{index}] source replay produced an invalid output hash"
            )
        by_line = expected.setdefault(source.path, {})
        if source.line in by_line:
            raise IdentityTreeError(
                f"IDENTITY-MANIFEST.json repeats output coordinate {source.path}:{source.line}"
            )
        by_line[source.line] = (index, mapping, replay)
    return expected


def _read_identity_output(path: Path, rel: str) -> dict[int, Mapping[str, Any]]:
    records: dict[int, Mapping[str, Any]] = {}
    try:
        output_bytes = path.read_bytes()
    except OSError as exc:
        raise IdentityTreeError(f"identity output is unreadable: {rel}: {exc}") from exc

    if not output_bytes.endswith(b"\n"):
        raise IdentityTreeError(f"identity output must end with exactly one LF: {rel}")
    framed_payload = output_bytes[:-1]
    if not framed_payload or framed_payload.endswith(b"\n"):
        raise IdentityTreeError(f"identity output must end with a canonical record: {rel}")

    for line_no, line_bytes in enumerate(framed_payload.split(b"\n"), 1):
        if not line_bytes:
            continue
        if not line_bytes.strip():
            raise IdentityTreeError(
                f"identity output blank placeholders must be empty: {rel}:{line_no}"
            )
        try:
            line = line_bytes.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise IdentityTreeError(
                f"identity output UTF-8 decode error at {rel}:{line_no}: {exc}"
            ) from exc
        try:
            output_record = _strict_json_loads(line)
        except (json.JSONDecodeError, ValueError) as exc:
            raise IdentityTreeError(
                f"identity output JSON parse error at {rel}:{line_no}: {exc}"
            ) from exc
        if not isinstance(output_record, Mapping):
            raise IdentityTreeError(f"identity output record at {rel}:{line_no} must be an object")
        try:
            canonical_payload = canonical_json(output_record).encode("utf-8")
        except (IdentityCurationError, UnicodeError) as exc:
            raise IdentityTreeError(
                f"identity output is not canonical JSON data: {rel}:{line_no}: {exc}"
            ) from exc
        if line_bytes != canonical_payload:
            raise IdentityTreeError(
                f"identity output payload is not exact canonical JSON: {rel}:{line_no}"
            )
        records[line_no] = output_record
    return records


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

    dest = Path(dest)
    if dest.is_symlink():
        raise IdentityTreeError("identity tree root must not be a symlink")
    symlinks = [path.relative_to(dest).as_posix() for path in dest.rglob("*") if path.is_symlink()]
    if symlinks:
        raise IdentityTreeError(f"identity tree must not contain symlinks: {symlinks}")
    sidecar = dest / FACTORY_REGISTRY_SIDECAR
    manifest_path = dest / IDENTITY_MANIFEST_SIDECAR
    if not sidecar.is_file():
        raise IdentityTreeError("identity tree missing FACTORY-REGISTRY.json")
    if not manifest_path.is_file():
        raise IdentityTreeError("identity tree missing IDENTITY-MANIFEST.json")
    try:
        registry = load_registry(sidecar)
    except IdentityCurationError as exc:
        raise IdentityTreeError(f"FACTORY-REGISTRY.json is invalid: {exc}") from exc
    if expected_registry_digest is not None and registry.sha256 != expected_registry_digest:
        raise IdentityTreeError(
            f"registry digest mismatch: expected {expected_registry_digest}, got {registry.sha256}"
        )
    try:
        manifest_bytes = manifest_path.read_bytes()
    except OSError as exc:
        raise IdentityTreeError(f"IDENTITY-MANIFEST.json is unreadable: {exc}") from exc
    manifest_digest = sha256_bytes(manifest_bytes)
    if expected_manifest_digest is not None:
        if not isinstance(expected_manifest_digest, str) or not SHA256_RE.fullmatch(
            expected_manifest_digest
        ):
            raise IdentityTreeError("expected manifest digest must be a lowercase SHA-256")
        if manifest_digest != expected_manifest_digest:
            raise IdentityTreeError(
                "manifest digest mismatch: "
                f"expected {expected_manifest_digest}, got {manifest_digest}"
            )
    try:
        manifest = _strict_json_loads(manifest_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise IdentityTreeError(f"IDENTITY-MANIFEST.json is not readable JSON: {exc}") from exc
    if not isinstance(manifest, list):
        raise IdentityTreeError("IDENTITY-MANIFEST.json must be a list of mappings")
    expected_outputs = _expected_identity_outputs(manifest, registry)
    actual_paths = {
        path.relative_to(dest).as_posix(): path
        for path in sorted(dest.rglob("*.jsonl"))
        if path.is_file()
    }
    expected_paths = set(expected_outputs)
    if set(actual_paths) != expected_paths:
        missing = sorted(expected_paths - set(actual_paths))
        extra = sorted(set(actual_paths) - expected_paths)
        raise IdentityTreeError(
            f"identity output paths do not match manifest: missing={missing}, extra={extra}"
        )
    for rel, expected_by_line in sorted(expected_outputs.items()):
        actual_by_line = _read_identity_output(actual_paths[rel], rel)
        if set(actual_by_line) != set(expected_by_line):
            raise IdentityTreeError(
                f"identity output line coordinates do not match manifest: {rel}"
            )
        for line_no, (index, mapping, replay) in expected_by_line.items():
            output_record = actual_by_line[line_no]
            try:
                actual_hash = sha256_json(output_record)
            except IdentityCurationError as exc:
                raise IdentityTreeError(
                    f"identity output is not canonical JSON data: {rel}:{line_no}: {exc}"
                ) from exc
            expected_output_sha256 = replay.result.mapping.get("output_sha256")
            if actual_hash != expected_output_sha256:
                raise IdentityTreeError(
                    f"identity output hashes do not match manifest: {rel}:{line_no}"
                )
            _validate_manifest_ids(mapping, output_record, index, registry, replay)
    return registry


def _registered_factory_ancestor(
    directory: Path,
    registry: FactoryRegistry,
) -> Path | None:
    for candidate in (directory, *directory.parents):
        if candidate.name in registry.by_path_id:
            return candidate
    return None


def _source_relative_path(
    path: Path,
    source: Path,
    registry: FactoryRegistry,
) -> str:
    factory_dir = _registered_factory_ancestor(path.parent, registry)
    if factory_dir is not None:
        return path.relative_to(factory_dir.parent).as_posix()
    if source.is_file() or path.parent == source:
        return path.relative_to(path.parent.parent).as_posix()
    return path.relative_to(source).as_posix()


def _committed_source_paths(paths: Iterable[Path]) -> list[Path]:
    visible_by_factory: dict[Path, set[Path]] = {}
    enclosing_factory: dict[Path, Path | None] = {}

    def marker_factory(jsonl_path: Path) -> Path | None:
        visited: list[Path] = []
        current = jsonl_path.parent
        while True:
            if current in enclosing_factory:
                marker_root = enclosing_factory[current]
                break
            visited.append(current)
            if marker_mode_path(current) is not None:
                marker_root = current
                break
            parent = current.parent
            if parent == current:
                marker_root = None
                break
            current = parent
        for directory in visited:
            enclosing_factory[directory] = marker_root
        return marker_root

    visible: list[Path] = []
    for path in paths:
        factory = marker_factory(path)
        if factory is None:
            visible.append(path)
            continue
        if factory not in visible_by_factory:
            visible_by_factory[factory] = {
                candidate.resolve() for candidate in committed_jsonl_paths(factory)
            }
        if path.resolve() in visible_by_factory[factory]:
            visible.append(path)
    return visible


def iter_source_records(
    source: Path,
    registry: FactoryRegistry | None = None,
) -> list[SourceRecord]:
    """Read JSONL records under ``source`` as identity source coordinates."""

    source = Path(source)
    registry = default_registry() if registry is None else registry
    if not source.exists():
        raise IdentityCurationError(f"source does not exist: {source}")
    if source.is_symlink():
        raise IdentityCurationError(f"source must not be a symlink: {source}")
    if source.is_file():
        if source.suffix != ".jsonl":
            raise IdentityCurationError(f"source is not a JSONL file: {source}")
        if not source.parent.name:
            raise IdentityCurationError(
                f"JSONL source must be inside a factory directory: {source}"
            )
        candidates = [source]
    elif source.is_dir():
        jsonl_entries = sorted(source.rglob("*.jsonl"))
        symlink_entries = [path for path in jsonl_entries if path.is_symlink()]
        if symlink_entries:
            rendered = ", ".join(
                path.relative_to(source).as_posix() for path in symlink_entries
            )
            raise IdentityCurationError(
                f"source tree must not contain symlinked JSONL entries: {rendered}"
            )
        candidates = [path for path in jsonl_entries if path.is_file()]
        if not candidates:
            raise IdentityCurationError(f"no JSONL files under source: {source}")
    else:
        raise IdentityCurationError(f"source is not a JSONL file or directory: {source}")
    try:
        files = _committed_source_paths(candidates)
    except TransactionError as exc:
        raise IdentityCurationError(f"invalid source transaction state: {exc}") from exc
    if not files:
        raise IdentityCurationError(f"no committed JSONL files under source: {source}")

    records: list[SourceRecord] = []
    for path in files:
        rel = _source_relative_path(path, source, registry)
        with path.open("rb") as handle:
            for line_no, physical_line in enumerate(handle, 1):
                line_bytes = physical_line
                if line_bytes.endswith(b"\n"):
                    line_bytes = line_bytes[:-1]
                    if line_bytes.endswith(b"\r"):
                        line_bytes = line_bytes[:-1]
                try:
                    line = line_bytes.decode("utf-8")
                except UnicodeDecodeError as exc:
                    raise IdentityCurationError(
                        f"UTF-8 decode error at {rel}:{line_no}: {exc}"
                    ) from exc
                if not line or _is_json_whitespace(line):
                    continue
                try:
                    obj = _strict_json_loads(line)
                except (json.JSONDecodeError, ValueError) as exc:
                    raise IdentityCurationError(
                        f"JSON parse error at {rel}:{line_no}: {exc}"
                    ) from exc
                digest = hashlib.sha256(line_bytes).hexdigest()
                records.append(SourceRecord(obj, rel, line_no, digest, line))
    return records


def _ensure_output_directory(
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
                raise IdentityCurationError(f"identity output parent is not a directory: {current}")
        else:
            created_directories.append(current)


def write_run(
    source: Path,
    dest: Path,
    registry: FactoryRegistry | None = None,
) -> tuple[CurationResult, ...]:
    """Curate a source tree into a new destination with identity sidecars."""

    source = Path(source)
    dest = Path(dest)
    if dest.exists():
        raise IdentityCurationError(f"destination already exists: {dest}")
    if _is_under_raw(dest):
        raise IdentityCurationError(f"refusing to write inside immutable raw evidence: {dest}")
    registry = default_registry() if registry is None else registry
    results = curate_records(
        iter_source_records(source, registry=registry),
        registry=registry,
    )
    created_files: list[Path] = []
    created_directories: list[Path] = []
    destination_created = False
    try:
        dest.mkdir(parents=True, exist_ok=False)
        destination_created = True
        _write_exclusive(dest / FACTORY_REGISTRY_SIDECAR, registry.raw_bytes)
        created_files.append(dest / FACTORY_REGISTRY_SIDECAR)
        manifest_bytes = (
            json.dumps(
                [result.mapping for result in results],
                ensure_ascii=False,
                allow_nan=False,
                indent=2,
                sort_keys=True,
            )
            + "\n"
        ).encode("utf-8")
        manifest_digest = sha256_bytes(manifest_bytes)
        _write_exclusive(dest / IDENTITY_MANIFEST_SIDECAR, manifest_bytes)
        created_files.append(dest / IDENTITY_MANIFEST_SIDECAR)
        retained_by_rel: dict[str, dict[int, dict[str, Any]]] = {}
        for result in results:
            if result.action != "retained" or result.record is None:
                continue
            source_meta = result.mapping["source"]
            by_line = retained_by_rel.setdefault(source_meta["path"], {})
            if source_meta["line"] in by_line:
                raise IdentityCurationError(
                    "retained records repeat source coordinate "
                    f"{source_meta['path']}:{source_meta['line']}"
                )
            by_line[source_meta["line"]] = result.record
        for rel, records_by_line in sorted(retained_by_rel.items()):
            out_path = dest / rel
            _ensure_output_directory(dest, out_path.parent, created_directories)
            output_lines = [""] * max(records_by_line)
            for line_no, record in records_by_line.items():
                output_lines[line_no - 1] = canonical_json(record)
            payload = "\n".join(output_lines) + "\n"
            _write_exclusive(out_path, payload.encode("utf-8"))
            created_files.append(out_path)
        validate_identity_tree(
            dest,
            expected_registry_digest=registry.sha256,
            expected_manifest_digest=manifest_digest,
        )
    except BaseException:
        if destination_created:
            for path in reversed(created_files):
                try:
                    path.unlink()
                except FileNotFoundError:
                    pass
            for directory in reversed(created_directories):
                try:
                    directory.rmdir()
                except OSError:
                    pass
            try:
                dest.rmdir()
            except OSError:
                pass
        raise
    return results


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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="JSONL file or run directory")
    parser.add_argument(
        "--out",
        type=Path,
        help="write a NEW cleaned tree with FACTORY-REGISTRY.json and IDENTITY-MANIFEST.json",
    )
    args = parser.parse_args(argv)
    try:
        registry = default_registry()
        if args.out is None:
            results = curate_records(
                iter_source_records(args.source, registry=registry),
                registry=registry,
            )
        else:
            results = write_run(args.source, args.out, registry=registry)
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


if __name__ == "__main__":
    raise SystemExit(main())
