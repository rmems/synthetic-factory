#!/usr/bin/env python3
"""Identity source-claim authentication for the curation gate.

Split out of ``curate_gate.py`` (CodeScene: Lines of Code in a Single File) by
responsibility; every name is re-exported from ``curate_gate`` so existing
``curate_gate.X`` call sites resolve unchanged.

The identity lane's manifest claims which original ids and provenance fields
each source record carried. This module rederives that evidence from the
immutable source record itself and refuses an entry whose claims differ, so
the retained mapping is authenticated rather than trusted.

``_canonical_identity_output_id`` belongs to the same responsibility: it is
the deterministic id a source coordinate and owner pointer must produce, and
it is derived through ``curate_identity`` rather than restated here. The
manifest-wide walk that consumes it lives in ``curate_gate_identity_mapping``.
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path
from typing import Any, NamedTuple

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("curate_gate_identity_gate")
    from . import curate_gate_contract as _contract
    from . import curate_gate_digest as _digest
    from . import curate_gate_merge as _merge
    from . import curate_identity
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "curate_gate_identity_gate"
    )
    _PIPELINES = Path(__file__).resolve().parent
    if str(_PIPELINES) not in sys.path:
        sys.path.insert(0, str(_PIPELINES))
    import curate_gate_contract as _contract
    import curate_gate_digest as _digest
    import curate_gate_merge as _merge
    import curate_identity

GateError = _contract.GateError
record_sha256 = _digest.record_sha256
_same_json = _merge._same_json
_MISSING = _merge._MISSING

if __package__:
    from .curate_gate_rights import replay_gate_identity
else:
    from curate_gate_rights import replay_gate_identity

# Record kinds whose top-level object carries its own provenance mapping in
# addition to the per-owner state mappings.
_ROOT_PROVENANCE_KINDS = frozenset(
    {"preference", "bridge_pair", "episode", "safety_case", "multi_agent"}
)


def _mapping_value(document: Any, pointer: Any, label: str) -> Any:
    if pointer == "/":
        return document
    if not isinstance(pointer, str) or not pointer.startswith("/"):
        raise GateError(f"{label} must be a JSON pointer")
    value = document
    for raw_token in pointer[1:].split("/"):
        token = raw_token.replace("~1", "/").replace("~0", "~")
        if isinstance(value, list):
            try:
                value = value[int(token)]
            except (ValueError, IndexError) as exc:
                raise GateError(f"{label} does not resolve") from exc
        elif isinstance(value, dict) and token in value:
            value = value[token]
        else:
            raise GateError(f"{label} does not resolve")
    return value


def _mapping_pointer(base: str, key: str) -> str:
    token = key.replace("~", "~0").replace("/", "~1")
    return f"/{token}" if base == "/" else f"{base}/{token}"


def _identity_owner_specs(
    source_record: dict[str, Any],
    kind: str,
    label: str,
) -> list[tuple[str, dict[str, Any]]]:
    if kind == "thalamic":
        return [("/", source_record)]
    if kind == "preference":
        paths = ("/chosen", "/rejected")
    elif kind == "bridge_pair":
        paths = ("/language_view/trajectory",)
    else:
        return []
    owners: list[tuple[str, dict[str, Any]]] = []
    for path in paths:
        owner = _mapping_value(source_record, path, f"{label}{path}")
        if not isinstance(owner, dict):
            raise GateError(f"{label}{path} does not identify a source object")
        owners.append((path, owner))
    return owners


def _source_original_ids(
    source_record: dict[str, Any], owner_path: str, label: str
) -> list[dict[str, Any]]:
    owner = _mapping_value(source_record, owner_path, f"{label}.owner_path")
    if not isinstance(owner, dict):
        raise GateError(f"{label}.owner_path does not identify a source object")
    originals: list[dict[str, Any]] = []
    for container, base in (
        (owner, owner_path),
        (owner.get("meta"), _mapping_pointer(owner_path, "meta")),
        (owner.get("state"), _mapping_pointer(owner_path, "state")),
    ):
        if not isinstance(container, dict):
            continue
        for key in curate_identity.LEGACY_ID_KEYS:
            if key in container:
                originals.append(
                    {
                        "path": _mapping_pointer(base, key),
                        "value": copy.deepcopy(container[key]),
                    }
                )
    return originals


def _source_original_provenance(
    source_record: dict[str, Any], owner_path: str, state_path: str | None, label: str
) -> dict[str, Any]:
    owner = _mapping_value(source_record, owner_path, f"{label}.owner_path")
    if not isinstance(owner, dict):
        raise GateError(f"{label}.owner_path does not identify a source object")
    owner_snapshot = {
        "present": "provenance" in owner,
        "value": copy.deepcopy(owner.get("provenance")),
    }
    if state_path is None:
        return {"owner_provenance": owner_snapshot}
    state = _mapping_value(source_record, state_path, f"{label}.state_path")
    if not isinstance(state, dict):
        raise GateError(f"{label}.state_path does not identify a source object")
    return {
        "sim_or_real": {
            "present": "sim_or_real" in state,
            "value": copy.deepcopy(state.get("sim_or_real")),
        },
        "state_provenance": {
            "present": "provenance" in state,
            "value": copy.deepcopy(state.get("provenance")),
        },
        "owner_provenance": owner_snapshot,
    }


def _claimed_identity_source_evidence(entry: dict[str, Any], label: str) -> dict[str, Any]:
    id_mappings = entry.get("id_mappings")
    provenance_mappings = entry.get("provenance_mappings")
    if not isinstance(id_mappings, list) or not id_mappings:
        raise GateError(f"{label}.id_mappings must be non-empty")
    if not isinstance(provenance_mappings, list) or not provenance_mappings:
        raise GateError(f"{label}.provenance_mappings must be non-empty")
    claimed_ids: list[dict[str, Any]] = []
    for index, mapping in enumerate(id_mappings, 1):
        mapping_label = f"{label}.id_mappings[{index}]"
        if not isinstance(mapping, dict):
            raise GateError(f"{mapping_label} must be an object")
        originals = mapping.get("original_ids")
        if not isinstance(originals, list):
            raise GateError(f"{mapping_label}.original_ids must be a list")
        claimed_ids.append(
            {
                "owner_path": mapping.get("owner_path"),
                "original_ids": copy.deepcopy(originals),
            }
        )
    claimed_provenance: list[dict[str, Any]] = []
    for index, mapping in enumerate(provenance_mappings, 1):
        mapping_label = f"{label}.provenance_mappings[{index}]"
        if not isinstance(mapping, dict):
            raise GateError(f"{mapping_label} must be an object")
        original = mapping.get("original")
        if not isinstance(original, dict):
            raise GateError(f"{mapping_label}.original must be an object")
        claimed_provenance.append(
            {
                "owner_path": mapping.get("owner_path"),
                "state_path": mapping.get("state_path"),
                "original": copy.deepcopy(original),
            }
        )
    return {
        "id_mappings": claimed_ids,
        "provenance_mappings": claimed_provenance,
    }


def _expected_identity_ids(
    source_record: dict[str, Any],
    owners: list[tuple[str, dict[str, Any]]],
    label: str,
) -> list[dict[str, Any]]:
    """The original ids the source record carries at the root and each owner."""
    id_owner_paths = ["/", *(path for path, _owner in owners if path != "/")]
    return [
        {
            "owner_path": owner_path,
            "original_ids": _source_original_ids(
                source_record,
                owner_path,
                f"{label}.id_mappings[{index}]",
            ),
        }
        for index, owner_path in enumerate(id_owner_paths, 1)
    ]


def _identity_provenance_paths(
    source_record: dict[str, Any],
    kind: str,
    owners: list[tuple[str, dict[str, Any]]],
    label: str,
) -> list[tuple[str, str | None]]:
    """Which (owner, state) pointers the provenance claims must cover."""
    state_owners = owners or [("/", source_record)]
    use_state = any(
        isinstance(state := owner.get("state"), dict)
        and ("sim_or_real" in state or "provenance" in state)
        for _owner_path, owner in state_owners
    )
    if not use_state:
        return [("/", None)]
    provenance_paths: list[tuple[str, str | None]] = []
    for owner_path, owner in state_owners:
        state_path = _mapping_pointer(owner_path, "state")
        if not isinstance(owner.get("state"), dict):
            raise GateError(f"{label}{state_path} does not identify a source object")
        provenance_paths.append((owner_path, state_path))
    if kind in _ROOT_PROVENANCE_KINDS:
        provenance_paths.append(("/", None))
    return provenance_paths


def _expected_identity_provenance(
    source_record: dict[str, Any],
    kind: str,
    owners: list[tuple[str, dict[str, Any]]],
    label: str,
) -> list[dict[str, Any]]:
    """The provenance snapshot the source record carries at each covered pointer."""
    provenance_paths = _identity_provenance_paths(source_record, kind, owners, label)
    return [
        {
            "owner_path": owner_path,
            "state_path": state_path,
            "original": _source_original_provenance(
                source_record,
                owner_path,
                state_path,
                f"{label}.provenance_mappings[{index}]",
            ),
        }
        for index, (owner_path, state_path) in enumerate(provenance_paths, 1)
    ]


def _authenticate_procedural_source(entry: dict[str, Any], source_record: dict, label: str) -> str:
    try:
        replay = replay_gate_identity(entry)
    except ValueError as exc:
        raise GateError(f"{label}: {exc}") from exc
    if not _same_json(replay.record, source_record):
        raise GateError(f"{label}: procedural identity does not preserve source record")
    return record_sha256(entry["identity_detail"])


def _authenticate_identity_source_claims(
    entry: dict[str, Any], source_record: Any, label: str
) -> str:
    if not isinstance(source_record, dict):
        raise GateError(f"{label} cannot authenticate identity claims for a non-object source")
    if __package__:
        from .curate_parity import authenticate, is_native
    else:
        from curate_parity import authenticate, is_native
    if is_native(entry, source_record):
        return authenticate(entry, source_record, label)
    kind = curate_identity.classify_kind(source_record)
    if kind == "fault_recovery":
        # Preserved simulator records authenticate by full mapping replay, the
        # same contract as native parity — no rewritten identity evidence.
        return authenticate(entry, source_record, label)
    if kind == "code_repair":
        return _authenticate_procedural_source(entry, source_record, label)
    return _authenticate_rewritten_identity(entry, source_record, label)


def _authenticate_rewritten_identity(entry, source_record, label):
    claimed = _claimed_identity_source_evidence(entry, label)
    try:
        kind = curate_identity.record_kind(source_record)
    except curate_identity.IdentityCurationError as exc:
        raise GateError(f"{label} source record has no supported identity shape: {exc}") from exc
    owners = _identity_owner_specs(source_record, kind, label)
    expected = {
        "id_mappings": _expected_identity_ids(source_record, owners, label),
        "provenance_mappings": _expected_identity_provenance(source_record, kind, owners, label),
    }
    if not _same_json(claimed, expected):
        raise GateError(
            f"{label} original identity evidence does not match the source record or is incomplete"
        )
    return record_sha256(expected)


def _canonical_identity_output_id(
    source_path: str, source_line: int, kind: str, owner_path: str
) -> str:
    """The canonical id a retained owner pointer must carry for its source."""
    factory = source_path.split("/", 1)[0]
    source = curate_identity.SourceIdentity(
        source_path,
        source_line,
        factory,
        "0" * 64,
        "source-coordinate",
        None,
    )
    return curate_identity.canonical_id(source, kind, owner_path)


class _IdMappingScope(NamedTuple):
    """Everything a single ``id_mappings`` row is checked against."""

    record: dict[str, Any]
    kind: str
    source_path: Any
    source_line: Any
    seen_owners: set[Any]


def _output_id_matches(owner: Any, output_id: Any) -> bool:
    return (
        isinstance(owner, dict)
        and isinstance(output_id, str)
        and owner.get("id") == output_id
    )


def _expected_output_id(scope: _IdMappingScope, owner_path: Any, label: str) -> str:
    """The canonical output id for an authenticated source coordinate."""
    if not isinstance(scope.source_path, str) or not isinstance(scope.source_line, int):
        raise GateError(f"{label} is missing an authenticated source coordinate")
    return _canonical_identity_output_id(
        scope.source_path,
        scope.source_line,
        scope.kind,
        owner_path,
    )


def _check_id_mapping(scope: _IdMappingScope, mapping: Any, label: str) -> None:
    """Refuse one ``id_mappings`` row that does not authenticate."""
    if not isinstance(mapping, dict):
        raise GateError(f"{label} must be an object")
    owner_path = mapping.get("owner_path")
    if owner_path in scope.seen_owners:
        raise GateError(f"{label} duplicates owner_path {owner_path!r}")
    scope.seen_owners.add(owner_path)
    owner = _mapping_value(scope.record, owner_path, f"{label}.owner_path")
    if not _output_id_matches(owner, mapping.get("output_id")):
        raise GateError(f"{label}.output_id does not match output owner")
    output_id = mapping.get("output_id")
    expected_id = _expected_output_id(scope, owner_path, label)
    if output_id is not None and output_id != expected_id:
        raise GateError(f"{label}.output_id is not the deterministic canonical identity")


def _carries_provenance(container: Any, canonical: dict[str, Any]) -> bool:
    return isinstance(container, dict) and _same_json(
        container.get("provenance", _MISSING), canonical
    )


def _check_provenance_mapping(record: dict[str, Any], mapping: Any, label: str) -> None:
    """Refuse one ``provenance_mappings`` row that does not authenticate."""
    if not isinstance(mapping, dict):
        raise GateError(f"{label} must be an object")
    canonical = mapping.get("canonical")
    if not isinstance(canonical, dict):
        raise GateError(f"{label}.canonical must be an object")
    owner = _mapping_value(record, mapping.get("owner_path"), f"{label}.owner_path")
    if not _carries_provenance(owner, canonical):
        raise GateError(f"{label}.canonical does not match output provenance")
    state_path = mapping.get("state_path")
    if state_path is None:
        return
    state = _mapping_value(record, state_path, f"{label}.state_path")
    if (
        not _carries_provenance(state, canonical)
        or state.get("sim_or_real") != canonical.get("kind")
    ):
        raise GateError(f"{label}.canonical does not match output state")


if __package__:
    _expose_package_sibling(__name__)
