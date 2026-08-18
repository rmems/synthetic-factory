#!/usr/bin/env python3
"""Deterministic record-level identity and provenance curation.

This module is intentionally pure: it never reads or writes a corpus tree.  A
caller supplies one decoded JSON record and its immutable source coordinate;
the result contains either a retained copy plus a reversible mapping, or an
explicit exclusion mapping when provenance cannot be resolved without guessing.

Canonical IDs are identities of source records, not hashes of output order or
legacy IDs.  Their digest covers the transform version, normalized relative
source path, source line, record kind, and owner role.  Full SHA-256 digests are
kept to make cross-factory collisions negligibly likely and independently
detectable by :func:`curate_records`.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any, Iterable, Mapping

TRANSFORM_NAME = "curate_identity"
TRANSFORM_VERSION = "identity-provenance-v1"
ID_NAMESPACE = "spikenaut.synthetic-factory.curated-record"

CANONICAL_PROVENANCE = frozenset({"designed", "simulated", "hil"})
EPISODE_FACTORY = "agentic-coding-trajectory-factory"
LEGACY_ID_KEYS = ("id", "record_id", "trajectory_id", "episode_id", "pair_id")
THALAMIC_REQUIRED = (
    "state",
    "proposed_action",
    "safety_decision",
    "executed_action",
    "future_outcome",
    "reward_components",
)
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
HIL_RE = re.compile(r"\bhil\b", re.IGNORECASE)


class IdentityCurationError(ValueError):
    """Base class for caller-contract and batch-integrity failures."""


class CanonicalIdCollision(IdentityCurationError):
    """Raised when two retained source records resolve to one canonical ID."""


@dataclass(frozen=True)
class SourceRecord:
    """A decoded record paired with its immutable, run-relative source identity.

    When supplied, ``source_sha256`` is the digest of the exact UTF-8 JSONL
    record bytes with the line terminator excluded.  Minimal fixtures may omit
    it; their mapping records that canonical JSON was hashed instead.
    """

    record: Mapping[str, Any]
    source_path: str
    source_line: int
    source_sha256: str | None = None


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


def canonical_json(value: Any) -> str:
    """Serialize JSON data byte-stably for hashes, tests, and output sidecars."""

    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    except (TypeError, ValueError) as exc:
        raise IdentityCurationError(f"record is not canonical JSON data: {exc}") from exc


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _normalize_source_path(value: str) -> tuple[str, str]:
    if not isinstance(value, str) or not value.strip():
        raise IdentityCurationError("source_path must be a non-empty relative path")
    raw = value.strip().replace("\\", "/")
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
        raise IdentityCurationError(
            f"source_path is not normalized: {value!r}; use {normalized!r}"
        )
    return normalized, path.parts[0]


def _source_identity(source: SourceRecord) -> _SourceIdentity:
    if (
        not isinstance(source.source_line, int)
        or isinstance(source.source_line, bool)
        or source.source_line < 1
    ):
        raise IdentityCurationError("source_line must be a positive integer")
    path, factory = _normalize_source_path(source.source_path)
    if source.source_sha256 is None:
        digest = _sha256_json(source.record)
        basis = "canonical-json-sha256"
    else:
        digest = str(source.source_sha256).lower()
        if not SHA256_RE.fullmatch(digest):
            raise IdentityCurationError(
                "source_sha256 must be exactly 64 hexadecimal characters"
            )
        basis = "source-json-line-sha256"
    return _SourceIdentity(path, source.source_line, factory, digest, basis)


def record_kind(record: Mapping[str, Any]) -> str:
    """Classify the four shapes owned by this curation lane."""

    if not isinstance(record, Mapping):
        raise IdentityCurationError("record must be a JSON object")
    if "chosen" in record and "rejected" in record:
        return "preference"
    if "language_view" in record and "spike_events" in record:
        return "bridge_pair"
    if "goal" in record and "steps" in record:
        return "episode"
    if all(key in record for key in THALAMIC_REQUIRED):
        return "thalamic"
    raise IdentityCurationError(
        f"unsupported record shape (keys: {sorted(map(str, record.keys()))[:8]})"
    )


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


def _owner_specs(record: Mapping[str, Any], kind: str) -> list[tuple[str, Mapping[str, Any]]]:
    if kind == "thalamic":
        return [("/", record)]
    if kind == "preference":
        owners = []
        for side in ("chosen", "rejected"):
            owner = record.get(side)
            if not isinstance(owner, Mapping):
                raise IdentityCurationError(f"preference {side} must be an object")
            owners.append((f"/{side}", owner))
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
    if (
        value.startswith("real")
        or value.startswith("live")
        or "actions live" in value
        or "production" in value
    ):
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
    }


def _base_mapping(
    source: _SourceIdentity,
    kind: str,
    root_original_ids: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "transform": {"name": TRANSFORM_NAME, "version": TRANSFORM_VERSION},
        "source": _source_mapping(source),
        "factory": source.factory,
        "record_kind": kind,
        "original_ids": root_original_ids,
    }


def curate_record(source_record: SourceRecord) -> CurationResult:
    """Curate one source record without mutating the caller's object.

    Missing or ambiguous trajectory provenance returns ``action == 'exclude'``
    with machine-readable reason details.  It is intentionally not converted to
    ``designed`` merely because it lives in a synthetic corpus.
    """

    if not isinstance(source_record, SourceRecord):
        raise IdentityCurationError("curate_record expects a SourceRecord")
    source = _source_identity(source_record)
    kind = record_kind(source_record.record)
    original = source_record.record
    root_original_ids = _legacy_ids(original, "/")
    mapping = _base_mapping(source, kind, root_original_ids)

    try:
        owner_specs = _owner_specs(original, kind)
    except IdentityCurationError as exc:
        mapping.update(
            {
                "action": "exclude",
                "reason_codes": ["identity.invalid_nested_shape"],
                "details": [str(exc)],
            }
        )
        return CurationResult("exclude", None, mapping)

    # Keep one flattened source index as well as the per-owner mappings below.
    # This remains useful on exclusions, where no canonical owner IDs are
    # emitted but every legacy identifier must still be recoverable.
    all_original_ids = list(root_original_ids)
    for owner_path, owner in owner_specs:
        if owner_path != "/":
            all_original_ids.extend(_legacy_ids(owner, owner_path))
    mapping["original_ids"] = all_original_ids

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

    if kind == "episode":
        if source.factory != EPISODE_FACTORY:
            unresolved.append(
                {
                    "path": "/",
                    "reason": "episode_source_factory_not_authoritative",
                    "factory": source.factory,
                }
            )

    if unresolved:
        mapping.update(
            {
                "action": "exclude",
                "reason_codes": ["identity.unresolved_provenance"],
                "unresolved_provenance": unresolved,
            }
        )
        return CurationResult("exclude", None, mapping)

    curated: dict[str, Any] = copy.deepcopy(dict(original))
    output_id = _canonical_id(source, kind, "/")
    curated["id"] = output_id

    id_mappings: list[dict[str, Any]] = [
        {
            "owner_path": "/",
            "original_ids": root_original_ids,
            "output_id": output_id,
        }
    ]
    provenance_mappings: list[dict[str, Any]] = []

    if kind == "episode":
        episode_provenance = {
            "kind": "designed",
            "claimed": None,
            "basis": "synthetic_factory_episode_shape",
        }
        original_provenance = {
            "present": "provenance" in original,
            "value": copy.deepcopy(original.get("provenance")),
        }
        curated["provenance"] = episode_provenance
        provenance_mappings.append(
            {
                "owner_path": "/",
                "original": {"owner_provenance": original_provenance},
                "canonical": copy.deepcopy(episode_provenance),
            }
        )
    else:
        curated_owners = _owner_specs(curated, kind)
        canonical_provenances = []
        for resolution, (owner_path, owner) in zip(
            provenance_resolutions, curated_owners, strict=True
        ):
            nested_id = output_id
            if owner_path != "/":
                nested_id = _canonical_id(source, kind, owner_path)
                owner["id"] = nested_id
                original_owner = dict(_owner_specs(original, kind))[owner_path]
                id_mappings.append(
                    {
                        "owner_path": owner_path,
                        "original_ids": _legacy_ids(original_owner, owner_path),
                        "output_id": nested_id,
                    }
                )

            state = owner["state"]
            canonical_provenance = {
                "kind": resolution["kind"],
                "claimed": copy.deepcopy(resolution["claimed"]),
            }
            state["sim_or_real"] = resolution["kind"]
            state["provenance"] = copy.deepcopy(canonical_provenance)
            owner["provenance"] = copy.deepcopy(canonical_provenance)
            canonical_provenances.append(canonical_provenance)
            provenance_mappings.append(
                {
                    "owner_path": owner_path,
                    "state_path": resolution["state_path"],
                    "basis": resolution["basis"],
                    "original": resolution["original"],
                    "canonical": copy.deepcopy(canonical_provenance),
                }
            )

        if kind in {"preference", "bridge_pair"}:
            kinds = {item["kind"] for item in canonical_provenances}
            if len(kinds) == 1:
                wrapper_kind = next(iter(kinds))
                claims = [item["claimed"] for item in canonical_provenances]
                wrapper_claimed = claims[0] if all(item == claims[0] for item in claims) else claims
            else:
                wrapper_kind = "unknown"
                wrapper_claimed = [item["claimed"] for item in canonical_provenances]
            curated["provenance"] = {
                "kind": wrapper_kind,
                "claimed": copy.deepcopy(wrapper_claimed),
            }
            provenance_mappings.append(
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

    mapping.update(
        {
            "action": "retained",
            "reason_codes": ["identity.assigned", "provenance.canonicalized"],
            "output_id": output_id,
            "output_sha256": _sha256_json(curated),
            "id_mappings": id_mappings,
            "provenance_mappings": provenance_mappings,
        }
    )
    return CurationResult("retained", curated, mapping)


def curate_records(records: Iterable[SourceRecord]) -> tuple[CurationResult, ...]:
    """Curate a batch and independently reject any duplicate emitted ID."""

    results: list[CurationResult] = []
    seen: dict[str, tuple[dict[str, Any], str]] = {}
    for source_record in records:
        result = curate_record(source_record)
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
