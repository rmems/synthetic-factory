#!/usr/bin/env python3
"""The retained identity/provenance mapping gate for the curation pass.

Split out of ``curate_gate.py`` (CodeScene: Lines of Code in a Single File) by
responsibility; every name is re-exported from ``curate_gate`` so existing
``curate_gate.X`` call sites resolve unchanged.

``curate_gate_identity_gate`` authenticates what a single identity entry
*claims* about its immutable source. This module is the manifest-wide walk
that consumes it: for every retained entry it pairs the claim with the record
that actually reached the cleaned tree and checks the declared output id, the
original-identity evidence, each ``id_mappings`` row against the deterministic
canonical id, and each ``provenance_mappings`` row against the output's own
provenance and state. Coverage is checked in both directions -- an entry with
no output and a retained output with no entry are both findings.

It collects findings instead of raising, so one broken entry never hides the
rest, and the report it returns is what the promotion gate reads.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, NamedTuple, Sequence

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("curate_gate_identity_mapping")
    from . import curate_gate_contract as _contract
    from . import curate_gate_digest as _digest
    from . import curate_gate_identity_gate as _identity_gate
    from . import curate_gate_merge as _merge
    from . import curate_identity
    from .curate_gate_rights import replay_gate_identity
    from .check_records import canonical_record_id
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "curate_gate_identity_mapping"
    )
    _PIPELINES = Path(__file__).resolve().parent
    if str(_PIPELINES) not in sys.path:
        sys.path.insert(0, str(_PIPELINES))
    import curate_gate_contract as _contract
    import curate_gate_digest as _digest
    import curate_gate_identity_gate as _identity_gate
    import curate_gate_merge as _merge
    import curate_identity
    from curate_gate_rights import replay_gate_identity
    from check_records import canonical_record_id

GateError = _contract.GateError
record_sha256 = _digest.record_sha256
_normalized_sha256 = _digest._normalized_sha256
_same_json = _merge._same_json
_MISSING = _merge._MISSING
_mapping_value = _identity_gate._mapping_value
_canonical_identity_output_id = _identity_gate._canonical_identity_output_id
_claimed_identity_source_evidence = _identity_gate._claimed_identity_source_evidence


@dataclass
class _MappingTally:
    """Findings and per-check counters accumulated across identity entries."""

    errors: list[dict[str, str]] = field(default_factory=list)
    checked_ids: int = 0
    checked_provenance: int = 0
    checked_source_originals: int = 0

    def refuse(self, where: str, error: str) -> None:
        self.errors.append({"source": where, "error": error})


class _MappingEntry(NamedTuple):
    """One retained identity entry paired with the output record it claims."""

    entry: dict[str, Any]
    entry_index: int
    record: dict[str, Any]
    where: str


class _IdMappingScope(NamedTuple):
    """Everything a single ``id_mappings`` row is checked against."""

    record: dict[str, Any]
    kind: str
    source_path: Any
    source_line: Any
    seen_owners: set[Any]


# ---------------------------------------------------------------------------
# per-row checks: each refuses by raising, so the caller records one finding
# ---------------------------------------------------------------------------


def _check_id_mapping(scope: _IdMappingScope, mapping: Any, label: str) -> None:
    """Refuse one ``id_mappings`` row that does not authenticate."""
    if not isinstance(mapping, dict):
        raise GateError(f"{label} must be an object")
    owner_path = mapping.get("owner_path")
    if owner_path in scope.seen_owners:
        raise GateError(f"{label} duplicates owner_path {owner_path!r}")
    scope.seen_owners.add(owner_path)
    owner = _mapping_value(scope.record, owner_path, f"{label}.owner_path")
    output_id = mapping.get("output_id")
    if (
        not isinstance(owner, dict)
        or not isinstance(output_id, str)
        or owner.get("id") != output_id
    ):
        raise GateError(f"{label}.output_id does not match output owner")
    source_path = scope.source_path
    source_line = scope.source_line
    if not isinstance(source_path, str) or not isinstance(source_line, int):
        raise GateError(f"{label} is missing an authenticated source coordinate")
    expected_id = _canonical_identity_output_id(
        source_path,
        source_line,
        scope.kind,
        owner_path,
    )
    if output_id is not None and output_id != expected_id:
        raise GateError(f"{label}.output_id is not the deterministic canonical identity")


def _check_provenance_mapping(record: dict[str, Any], mapping: Any, label: str) -> None:
    """Refuse one ``provenance_mappings`` row that does not authenticate."""
    if not isinstance(mapping, dict):
        raise GateError(f"{label} must be an object")
    canonical = mapping.get("canonical")
    if not isinstance(canonical, dict):
        raise GateError(f"{label}.canonical must be an object")
    owner = _mapping_value(record, mapping.get("owner_path"), f"{label}.owner_path")
    if not isinstance(owner, dict) or not _same_json(owner.get("provenance", _MISSING), canonical):
        raise GateError(f"{label}.canonical does not match output provenance")
    state_path = mapping.get("state_path")
    if state_path is not None:
        state = _mapping_value(record, state_path, f"{label}.state_path")
        if (
            not isinstance(state, dict)
            or not _same_json(state.get("provenance", _MISSING), canonical)
            or state.get("sim_or_real") != canonical.get("kind")
        ):
            raise GateError(f"{label}.canonical does not match output state")


# ---------------------------------------------------------------------------
# per-entry phases, in the order the gate reports them
# ---------------------------------------------------------------------------


def _tally_source_originals(tally: _MappingTally, context: _MappingEntry) -> None:
    """Rederive the entry's original-identity evidence and match its digest."""
    try:
        claimed_originals = _claimed_identity_source_evidence(
            context.entry,
            f"identity_mappings[{context.entry_index}]",
        )
        expected_originals_sha256 = _normalized_sha256(
            context.entry.get("source_originals_sha256"),
            f"identity_mappings[{context.entry_index}].source_originals_sha256",
        )
        if record_sha256(claimed_originals) != expected_originals_sha256:
            raise GateError("original identity evidence mismatches authenticated source")
        tally.checked_source_originals += 1
    except GateError as exc:
        tally.refuse(context.where, str(exc))


def _tally_id_mappings(tally: _MappingTally, context: _MappingEntry) -> bool:
    """Check every id mapping; ``True`` means abandon the rest of the entry."""
    id_mappings = context.entry.get("id_mappings")
    if not isinstance(id_mappings, list) or not id_mappings:
        tally.refuse(context.where, "id_mappings must be non-empty")
        return False
    try:
        kind = curate_identity.record_kind(context.record)
    except curate_identity.IdentityCurationError as exc:
        tally.refuse(
            context.where,
            f"{context.where} output has no supported identity shape: {exc}",
        )
        return True
    scope = _IdMappingScope(
        context.record,
        kind,
        context.entry.get("source_path"),
        context.entry.get("source_line"),
        set(),
    )
    for mapping_index, mapping in enumerate(id_mappings, 1):
        label = f"identity_mappings[{context.entry_index}].id_mappings[{mapping_index}]"
        try:
            _check_id_mapping(scope, mapping, label)
            tally.checked_ids += 1
        except GateError as exc:
            tally.refuse(context.where, str(exc))
    return False


def _tally_provenance_mappings(tally: _MappingTally, context: _MappingEntry) -> None:
    """Check every provenance mapping the entry declares."""
    provenance_mappings = context.entry.get("provenance_mappings")
    if not isinstance(provenance_mappings, list) or not provenance_mappings:
        tally.refuse(context.where, "provenance_mappings must be non-empty")
        return
    for mapping_index, mapping in enumerate(provenance_mappings, 1):
        label = f"identity_mappings[{context.entry_index}].provenance_mappings[{mapping_index}]"
        try:
            _check_provenance_mapping(context.record, mapping, label)
            tally.checked_provenance += 1
        except GateError as exc:
            tally.refuse(context.where, str(exc))


# ---------------------------------------------------------------------------
# the gate
# ---------------------------------------------------------------------------


def _tally_procedural_mapping(tally: _MappingTally, context: _MappingEntry) -> None:
    try:
        replay = replay_gate_identity(context.entry)
        if not _same_json(replay.record, context.record):
            raise ValueError("procedural output does not preserve reviewed source")
        if record_sha256(context.entry["identity_detail"]) != context.entry.get("source_originals_sha256"):
            raise ValueError("procedural source attestation drifted")
    except ValueError as exc:
        tally.refuse(context.where, str(exc))
        return
    tally.checked_ids += 1
    tally.checked_source_originals += 1


def _identity_mapping_gate(
    identity_entries: Sequence[dict[str, Any]],
    records_by_source: dict[tuple[str, int], Any],
) -> dict[str, Any]:
    """Authenticate every retained identity mapping against the final records."""
    tally = _MappingTally()
    identity_source_keys: set[tuple[str, int]] = set()
    for entry_index, entry in enumerate(identity_entries, 1):
        source_key = (entry.get("source_path"), entry.get("source_line"))
        identity_source_keys.add(source_key)
        where = f"{source_key[0]}:{source_key[1]}"
        record = records_by_source.get(source_key)
        if not isinstance(record, dict):
            tally.refuse(where, "retained identity mapping has no output")
            continue
        if entry.get("output_id") != canonical_record_id(record):
            tally.refuse(where, "identity output_id mismatches final record")
        context = _MappingEntry(entry, entry_index, record, where)
        if curate_identity.classify_kind(record) == "code_repair":
            _tally_procedural_mapping(tally, context)
            continue
        _tally_source_originals(tally, context)
        if _tally_id_mappings(tally, context):
            continue
        _tally_provenance_mappings(tally, context)

    for source_path, source_line in sorted(set(records_by_source) - identity_source_keys):
        tally.refuse(
            f"{source_path}:{source_line}",
            "retained record has no authenticated identity mapping",
        )

    return {
        "tool": "curate_gate retained identity/provenance mapping verifier",
        "passed": not tally.errors,
        "retained_entries": len(identity_entries),
        "id_mappings": tally.checked_ids,
        "provenance_mappings": tally.checked_provenance,
        "source_originals": tally.checked_source_originals,
        "invalid_mappings": len(tally.errors),
        "examples": tally.errors[:5],
    }


if __package__:
    _expose_package_sibling(__name__)
