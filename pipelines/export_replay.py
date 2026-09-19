#!/usr/bin/env python3
"""Deterministic source replay: prove the published compose reproduces.

Split out of ``export_hf.py`` by responsibility. Every current source line is
re-composed under the published contract and the replayed manifest, sidecars,
outputs, and counts must agree exactly with what was published.
"""

from __future__ import annotations

import hashlib
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Sequence

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

import compose_oracle_selection  # noqa: E402
import compose_curated  # noqa: E402
import compose_curated_rights  # noqa: E402
import compose_mill  # noqa: E402
from compose_curated_run import authenticated_published_snapshot  # noqa: E402
from compose_curated_run_lines import add_physical_source_evidence  # noqa: E402
from compose_contract import (  # noqa: E402
    ComposeError,
    EmittedRecord,
    default_units_migration_path,
    emitted_record_line,
    published_source_snapshot,
    retained_json_line,
)
from census import factory_identity_for_path  # noqa: E402
from round_txn import TransactionError  # noqa: E402
from export_contract import CuratedFile, ExportError  # noqa: E402
from export_members import (  # noqa: E402
    _read_exact_regular_file,
    _require_exact_directory,
    _stable_file_identity,
)
import export_replay_verify as _replay_verify  # noqa: E402

# Verification helpers re-bound through the sibling so the historical
# ``export_replay.X`` call sites and patch seams resolve unchanged.
_PublishedReplay = _replay_verify._PublishedReplay
_authenticated_calibration_state = _replay_verify._authenticated_calibration_state
_calibration_evidence_identity = _replay_verify._calibration_evidence_identity
_require_calibration_state_unchanged = _replay_verify._require_calibration_state_unchanged
_require_replayed_counts = _replay_verify._require_replayed_counts
_require_replayed_documents = _replay_verify._require_replayed_documents
_verify_replay_matches = _replay_verify._verify_replay_matches
_verify_replay_matches_context = _replay_verify._verify_replay_matches_context


@dataclass(frozen=True)
class _ReplaySnapshot:
    """Everything replaying the source lines accumulates for authentication.

    ``expected_*`` are what the compose lanes deterministically produce from
    the current source snapshot; the caller compares them against the
    already-published manifest, sidecars, and outputs.
    """

    counts: Counter[str]
    exclusions: Counter[str]
    lane_actions: dict[str, Counter[str]]
    expected_manifest: list[dict[str, Any]]
    expected_sidecars: list[dict[str, Any]]
    expected_outputs: list[dict[str, Any]]
    expected_payloads: dict[str, bytes]
    source_files: list[dict[str, Any]]
    rights_lanes: Counter[str]


@dataclass
class _ReplayState:
    """Mutable accumulators shared by every replayed source line."""

    oracle_selection: str = "all"

    counts: Counter[str] = field(default_factory=Counter)
    exclusions: Counter[str] = field(default_factory=Counter)
    lane_actions: dict[str, Counter[str]] = field(
        default_factory=lambda: {lane: Counter() for lane in compose_curated.LANE_ORDER}
    )
    expected_manifest: list[dict[str, Any]] = field(default_factory=list)
    expected_sidecars: list[dict[str, Any]] = field(default_factory=list)
    expected_outputs: list[dict[str, Any]] = field(default_factory=list)
    expected_payloads: dict[str, bytes] = field(default_factory=dict)
    emitted_ids: dict[str, str] = field(default_factory=dict)
    source_files: list[dict[str, Any]] = field(default_factory=list)
    seen_source_semantics: dict[str, tuple[str, int]] = field(default_factory=dict)
    seen_curated_semantics: dict[str, tuple[str, int]] = field(default_factory=dict)
    rights_lanes: Counter[str] = field(default_factory=Counter)


@dataclass(frozen=True)
class _SourceReplay:
    """Captured inputs needed to replay one source file."""

    relative: str
    raw_file: bytes
    catalog: Any
    mill_findings: dict[tuple[str, int], Any]
    physical_source_path: str | None = None


@dataclass(frozen=True)
class _LineReplay:
    """Stable coordinate and policy inputs for one replayed source line."""

    relative: str
    line_number: int
    output_line: int
    source_file_sha256: str
    catalog: Any
    mill_finding: Any
    physical_source_path: str | None = None
    source_terminator: str = "\n"


def _selection_result(function, *args):
    """Keep selection refusals inside the exporter's public error contract."""
    try:
        return function(*args)
    except ComposeError as exc:
        raise ExportError(str(exc)) from exc


def _replay_physical_lines(raw_file: bytes) -> list[bytes]:
    """Split LF-framed JSONL exactly as the compose writer framed it."""

    return compose_curated.jsonl_physical_lines(raw_file)


def _replayed_manifest_entry(
    decision: Any, relative: str, line_number: int, digests: tuple[str, str]
) -> dict[str, Any]:
    """The manifest entry one replayed line is expected to have produced."""

    source_sha256, source_file_sha256 = digests
    return {
        "compose_name": compose_curated.COMPOSE_NAME,
        "compose_version": compose_curated.COMPOSE_VERSION,
        "lane_order": list(compose_curated.LANE_ORDER),
        "source_path": relative,
        "source_line": line_number,
        "source_sha256": source_sha256,
        "source_file_sha256": source_file_sha256,
        "action": decision.action,
        "reason_codes": list(decision.reason_codes),
        "stages": [dict(stage) for stage in decision.stages],
    }


def _claim_replayed_output_id(state: _ReplayState, output_id: Any, location: str) -> None:
    """Reserve a canonical ID across the replay, or refuse the export."""

    if output_id is None:
        return
    previous = state.emitted_ids.get(output_id)
    if previous is not None:
        raise ExportError(
            f"replayed canonical ID collision {output_id!r}: {previous} and {location}"
        )
    state.emitted_ids[output_id] = location


def _record_replayed_retained_context(
    state: _ReplayState,
    decision: Any,
    entry: dict[str, Any],
    replay: _LineReplay,
) -> EmittedRecord:
    """Account one replayed record that compose would have emitted."""

    try:
        line = retained_json_line(decision)
    except ComposeError as exc:
        raise ExportError(str(exc)) from exc
    _claim_replayed_output_id(state, decision.output_id, f"{replay.relative}:{replay.line_number}")
    entry.update(
        {
            "output_path": f"{compose_curated.RECORDS_DIRNAME}/{replay.relative}",
            "output_line": replay.output_line,
            "output_id": decision.output_id,
            "output_sha256": hashlib.sha256(line.encode("utf-8")).hexdigest(),
        }
    )
    state.counts["retained"] += 1
    if decision.reward_sidecar is not None:
        entry["reward_sidecar_id"] = decision.reward_sidecar["sidecar_id"]
        state.expected_sidecars.append(decision.reward_sidecar)
    return emitted_record_line(decision, line, replay.source_terminator)


def _record_replayed_retained(
    state: _ReplayState,
    *legacy: Any,
) -> None:
    """Adapt ``(decision, entry, relative, emitted)`` to replay context."""

    decision, entry, relative, emitted = legacy
    emitted.append(
        _record_replayed_retained_context(
            state,
            decision,
            entry,
            _LineReplay(
                relative=relative,
                line_number=entry["source_line"],
                output_line=len(emitted) + 1,
                source_file_sha256="",
                catalog=None,
                mill_finding=None,
            ),
        )
    )


def _record_replayed_excluded(state: _ReplayState, decision: Any, entry: dict[str, Any]) -> None:
    """Account one replayed record that compose would have excluded."""

    entry.update(
        {
            "output_path": None,
            "output_line": None,
            "output_id": None,
            "output_sha256": None,
        }
    )
    state.counts["excluded"] += 1
    for reason in decision.reason_codes or ("compose.unspecified",):
        state.exclusions[reason] += 1


def _count_replayed_stages(state: _ReplayState, decision: Any) -> None:
    for stage in decision.stages:
        lane = stage["lane"]
        if lane in state.lane_actions:
            state.lane_actions[lane][stage["action"]] += 1



def _replay_one_line_context(
    state: _ReplayState,
    physical_line: bytes,
    replay: _LineReplay,
) -> EmittedRecord | None:
    """Replay one non-blank source line through the compose lanes."""

    state.counts["source_records"] += 1
    if replay.mill_finding is not None:
        decision = compose_curated.mill_quarantined_decision(replay.mill_finding)
    else:
        decision = compose_curated.compose_source_line(
            physical_line,
            compose_curated.SourceLineCoordinate(
                replay.relative, replay.line_number, replay.source_file_sha256
            ),
            calibration_catalog=replay.catalog,
            semantics=compose_curated.SemanticRegistry(
                state.seen_source_semantics, state.seen_curated_semantics
            ),
        )
    decision = _selection_result(
        compose_oracle_selection.apply_selection, decision, state.oracle_selection
    )
    entry = _replayed_manifest_entry(
        decision,
        replay.relative,
        replay.line_number,
        (hashlib.sha256(physical_line).hexdigest(), replay.source_file_sha256),
    )
    add_physical_source_evidence(entry, replay.physical_source_path, physical_line)
    _count_replayed_stages(state, decision)

    if decision.action == compose_curated.ACTION_RETAINED and decision.record is not None:
        emitted_line = _record_replayed_retained_context(state, decision, entry, replay)
        try:
            compose_curated_rights.bind_retained_rights(state, entry, decision, physical_line)
        except ComposeError as exc:
            raise ExportError(f"replayed rights envelope failed closed: {exc}") from exc
    else:
        _record_replayed_excluded(state, decision, entry)
        emitted_line = None
    state.expected_manifest.append(entry)
    return emitted_line


def _replay_one_line(
    state: _ReplayState,
    physical_line: bytes,
    *legacy: Any,
) -> None:
    """Adapt ``(coordinate, context, mill_findings)`` to line context."""

    coordinate, context, mill_findings = legacy
    relative, line_number = coordinate
    source_file_sha256, catalog, emitted = context
    emitted_line = _replay_one_line_context(
        state,
        physical_line,
        _LineReplay(
            relative=relative,
            line_number=line_number,
            output_line=len(emitted) + 1,
            source_file_sha256=source_file_sha256,
            catalog=catalog,
            mill_finding=mill_findings.get((relative, line_number)),
        ),
    )
    if emitted_line is not None:
        emitted.append(emitted_line)


def _record_replayed_output_file(state: _ReplayState, relative: str, emitted: list[EmittedRecord]) -> None:
    """Record the output file one replayed source file would have produced."""

    output_path = f"{compose_curated.RECORDS_DIRNAME}/{relative}"
    if __package__:
        from .compose_contract import emitted_records_text
    else:
        from compose_contract import emitted_records_text
    payload = emitted_records_text(emitted).encode("utf-8")
    state.expected_payloads[output_path] = payload
    state.expected_outputs.append(
        {
            "path": output_path,
            "records": len(emitted),
            "sha256": hashlib.sha256(payload).hexdigest(),
        }
    )
    state.counts["output_files"] += 1


def _replay_source_file_context(
    state: _ReplayState,
    replay: _SourceReplay,
) -> None:
    """Replay every record of one captured source file and its output."""

    source_file_sha256 = hashlib.sha256(replay.raw_file).hexdigest()
    state.source_files.append(
        {
            "path": replay.relative,
            "bytes": len(replay.raw_file),
            "sha256": source_file_sha256,
        }
    )
    state.counts["source_files"] += 1
    emitted: list[EmittedRecord] = []
    if __package__:
        from .compose_contract import source_terminators
    else:
        from compose_contract import source_terminators
    terminators = source_terminators(replay.raw_file)

    for line_number, physical_line in enumerate(_replay_physical_lines(replay.raw_file), 1):
        if not physical_line.strip():
            state.counts["blank_lines"] += 1
            continue
        emitted_line = _replay_one_line_context(
            state,
            physical_line,
            _LineReplay(
                relative=replay.relative,
                line_number=line_number,
                output_line=len(emitted) + 1,
                source_file_sha256=source_file_sha256,
                catalog=replay.catalog,
                mill_finding=replay.mill_findings.get((replay.relative, line_number)),
                source_terminator=terminators[line_number - 1],
                physical_source_path=replay.physical_source_path,
            ),
        )
        if emitted_line is not None:
            emitted.append(emitted_line)

    if emitted:
        _record_replayed_output_file(state, replay.relative, emitted)


def _replay_source_file(
    state: _ReplayState,
    *legacy: Any,
) -> None:
    """Adapt ``(relative, raw_file, catalog, findings)`` to source context."""

    relative, raw_file, catalog, mill_findings = legacy
    _replay_source_file_context(
        state,
        _SourceReplay(
            relative=relative,
            raw_file=raw_file,
            catalog=catalog,
            mill_findings=mill_findings,
        ),
    )


def _member_identity(source_root: Path, relative: str) -> tuple[tuple[int, ...], str, bool]:
    path = source_root.joinpath(*relative.split("/"))
    try:
        entry = path.lstat()
    except OSError as exc:
        raise ExportError(f"compose source {relative}: member cannot be inspected: {exc}") from exc
    factory, verified = factory_identity_for_path(source_root, path)
    return _stable_file_identity(entry), factory, verified


def _member_identities(
    source_root: Path, source_members: tuple[str, ...]
) -> dict[str, tuple[tuple[int, ...], str, bool]]:
    return {relative: _member_identity(source_root, relative) for relative in source_members}


def _require_coherent_capture(
    source_root: Path,
    source_members: tuple[str, ...],
    identities_before: dict[str, tuple[tuple[int, ...], str, bool]],
) -> None:
    """Refuse a capture whose members changed while it was being taken.

    Each member read is individually alias- and identity-checked, but a
    member rewritten after its own read — while a later member is still being
    captured — would let replay authenticate a hybrid of source states that
    never coexisted. Comparing every member's identity from before the first
    read to after the last one refuses that interleaving. Identity checks
    only cover the members enumerated before the first read, so member
    discovery reruns here too: a visible JSONL added to the tree mid-capture
    would otherwise let export authenticate and publish the old subset of a
    source run that no longer exists.
    """
    try:
        members_now = compose_curated.source_jsonl_members(source_root)
    except (compose_curated.ComposeError, TransactionError) as exc:
        raise ExportError(f"COMPOSE source tree cannot be replayed safely: {exc}") from exc
    if tuple(members_now) != tuple(source_members):
        raise ExportError(
            "compose source: the visible member set changed while the replay "
            "snapshot was being captured"
        )
    for relative in source_members:
        if _member_identity(source_root, relative) != identities_before[relative]:
            raise ExportError(
                f"compose source {relative}: member changed while the replay "
                "snapshot was being captured"
            )


def _capture_source_members(
    source_root: Path, source_members: tuple[str, ...]
) -> tuple[tuple[str, ...], dict[str, bytes], dict[str, Any], dict[tuple[str, int], Any]]:
    """Capture every member once, then index corpus-level mill ownership.

    The capture and the mill resolution run over exactly those bytes — the same
    order of operations compose_run applies, so a quarantined line replays as
    the same exclusion.
    """

    identities_before = _member_identities(source_root, source_members)
    payload_by_member = {
        relative: _read_exact_regular_file(source_root, relative, f"compose source {relative}")[1]
        for relative in source_members
    }
    _require_coherent_capture(source_root, source_members, identities_before)
    factory_identities = {
        relative: (factory, verified)
        for relative, (_file_identity, factory, verified) in identities_before.items()
    }
    try:
        source_members, payload_by_member, factory_identities, physical_source_paths = authenticated_published_snapshot(
            source_root, source_members, payload_by_member, factory_identities
        )
    except ComposeError as exc:
        raise ExportError(f"COMPOSE source coordinates cannot be replayed safely: {exc}") from exc
    mill_findings = compose_mill.index_compose_mills(
        payload_by_member, factory_identities, _replay_physical_lines
    )
    return source_members, payload_by_member, physical_source_paths, mill_findings


def _replay_source_lines(source_root: Path, catalog: Any, oracle_selection="all") -> _ReplaySnapshot:
    """Run every source JSONL line back through compose and record what it yields."""

    try:
        source_members = compose_curated.source_jsonl_members(source_root)
    except (compose_curated.ComposeError, TransactionError) as exc:
        raise ExportError(f"COMPOSE source tree cannot be replayed safely: {exc}") from exc

    (
        source_members,
        payload_by_member,
        physical_source_paths,
        mill_findings,
    ) = _capture_source_members(source_root, source_members)

    _selection_result(
        compose_oracle_selection.require_authenticated_source,
        oracle_selection, source_members, physical_source_paths,
    )
    state = _ReplayState(oracle_selection=oracle_selection)
    for relative in source_members:
        _replay_source_file_context(
            state,
            _SourceReplay(
                relative=relative,
                raw_file=payload_by_member[relative],
                catalog=catalog,
                mill_findings=mill_findings,
                physical_source_path=physical_source_paths.get(relative),
            ),
        )

    state.counts["reward_sidecars"] = len(state.expected_sidecars)
    return _ReplaySnapshot(
        counts=state.counts,
        exclusions=state.exclusions,
        lane_actions=state.lane_actions,
        expected_manifest=state.expected_manifest,
        expected_sidecars=state.expected_sidecars,
        expected_outputs=state.expected_outputs,
        expected_payloads=state.expected_payloads,
        source_files=state.source_files,
        rights_lanes=state.rights_lanes,
    )


def _authenticated_source_root(summary: dict[str, Any]) -> Path:
    raw_source_root = summary.get("source_run")
    if not isinstance(raw_source_root, str) or not Path(raw_source_root).is_absolute():
        raise ExportError("COMPOSE.json: source_run must be an absolute directory string")
    source_root = _require_exact_directory(Path(raw_source_root), "COMPOSE source_run")
    if raw_source_root != str(source_root):
        raise ExportError("COMPOSE.json: source_run must use its exact canonical path")
    return source_root


def _authenticate_source_replay(
    summary: dict[str, Any],
    actual_outputs: dict[str, CuratedFile],
    manifest_documents: Sequence[Any],
    sidecar_documents: Sequence[Any],
) -> dict[str, Any]:
    """Replay current source bytes and authenticate the complete compose mapping.

    This proves that the currently available source snapshot deterministically
    produces the declared outputs.  It deliberately does not claim that the
    source directory was immutable between the original compose and this replay.
    """

    source_root = _authenticated_source_root(summary)
    calibration_state = _authenticated_calibration_state(summary, source_root)
    catalog, calibration_descriptor, _calibration_evidence = calibration_state

    selection = _selection_result(compose_oracle_selection.published_mode, summary)
    snapshot = _replay_source_lines(source_root, catalog, selection)
    _require_calibration_state_unchanged(
        calibration_state,
        _authenticated_calibration_state(summary, source_root),
    )
    _verify_replay_matches_context(
        snapshot,
        _PublishedReplay(
            summary=summary,
            actual_outputs=actual_outputs,
            manifest_documents=manifest_documents,
            sidecar_documents=sidecar_documents,
        ),
    )

    snapshot_digest = hashlib.sha256(
        compose_curated.canonical_json(snapshot.source_files).encode("utf-8")
    ).hexdigest()
    return {
        "path": str(source_root),
        "authentication_scope": "current_source_snapshot_replayed",
        "historical_immutability_proven": False,
        "files": snapshot.counts["source_files"],
        "records": snapshot.counts["source_records"],
        "blank_lines": snapshot.counts["blank_lines"],
        "snapshot_index_sha256": snapshot_digest,
        "calibration": calibration_descriptor,
    }
