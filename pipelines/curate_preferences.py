#!/usr/bin/env python3
"""Conservatively curate same-context preference pairs.

The transform never mutates its input objects. A pair is retained only when
``chosen`` and ``rejected`` have canonically identical ``state`` and
``proposed_action`` values. An impure pair is repaired only when one branch
contains an exact copy of the intended context and the other branch explicitly
attests that identity in a narrowly bounded annotation. All other impure pairs
are excluded with machine-readable reason codes.

Read-only corpus inspection::

    python3 pipelines/curate_preferences.py scan <source> --json

Write a new preference JSONL and manifest (both destinations must be absent)::

    python3 pipelines/curate_preferences.py curate <source> \
      --output <new-preferences.jsonl> --manifest <new-manifest.jsonl>

``source`` may be one JSONL file or a directory scanned recursively. Records
without preference-pair fields are counted and skipped; malformed preference
candidates are explicitly excluded rather than silently dropped.

Writing anywhere under ``outputs/raw/`` is refused: raw runs are immutable
evidence, and that includes adding new files beside them.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any


TRANSFORM_NAME = "same-context-preference-curation"
TRANSFORM_VERSION = "1.0.0"
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
RAW_OUTPUT_ROOT = REPOSITORY_ROOT / "outputs" / "raw"

ACTION_RETAINED = "retained"
ACTION_REPAIRED = "repaired"
ACTION_EXCLUDED = "excluded"


class PreferenceCurationError(RuntimeError):
    """Raised when source or destination handling would be unsafe."""


@dataclass(frozen=True)
class CurationDecision:
    """One deterministic record-level curation decision."""

    action: str
    classification: str
    reason_codes: tuple[str, ...]
    record: dict[str, Any] | None
    context_diff_paths: tuple[str, ...]
    changed_context_fields: tuple[str, ...] = ()


@dataclass(frozen=True)
class CurationRun:
    """Curated records, manifest entries, and aggregate counts for one source."""

    records: tuple[dict[str, Any], ...]
    manifest: tuple[dict[str, Any], ...]
    summary: dict[str, Any]


@dataclass
class _ScanState:
    records: list[dict[str, Any]]
    manifest: list[dict[str, Any]]
    actions: Counter[str]
    classifications: Counter[str]
    reasons: Counter[str]
    skipped_non_preferences: int = 0
    json_records_seen: int = 0


@dataclass(frozen=True)
class _SourceLine:
    relative_path: str
    number: int
    payload: bytes
    file_sha256: str


def canonical_json(value: Any) -> str:
    """Return the canonical JSON representation used for context equality."""

    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _has_raw_tree_components(path: Path) -> bool:
    """Whether normalized ``path`` names an ``outputs/raw`` tree."""

    parts = path.parts
    return any(
        parts[index : index + 2] == ("outputs", "raw")
        for index in range(len(parts) - 1)
    )


def _stat_identity(path: Path) -> tuple[int, int] | None:
    try:
        state = path.stat()
    except OSError:
        return None
    return state.st_dev, state.st_ino


def _ancestor_identities(path: Path) -> set[tuple[int, int]]:
    """Device/inode identities of ``path`` and existing ancestors.

    Bind mounts and case-insensitive directory spellings keep distinct
    pathnames after ``resolve()`` but share the raw tree's identity.
    """

    identities: set[tuple[int, int]] = set()
    current = Path(os.path.abspath(path))
    seen: set[Path] = set()
    while current not in seen:
        seen.add(current)
        identity = _stat_identity(current)
        if identity is not None:
            identities.add(identity)
        parent = current.parent
        if parent == current:
            break
        current = parent
    return identities


def _names_raw_tree(path: Path) -> bool:
    """Whether the lexical or resolved spelling names ``outputs/raw``.

    Resolving ``outputs/raw`` when it is itself a symlink removes those path
    components and would otherwise let a write through the immutable tree.
    Callers can also name that same target through a mount path or a second
    symlink whose spelling never contains ``outputs/raw``.
    """

    lexical_path = Path(os.path.abspath(path))
    resolved_path = path.resolve(strict=False)
    if _has_raw_tree_components(lexical_path):
        return True
    if _has_raw_tree_components(resolved_path):
        return True
    resolved_raw_root = RAW_OUTPUT_ROOT.resolve(strict=False)
    if resolved_path == resolved_raw_root:
        return True
    return resolved_raw_root in resolved_path.parents


def _shares_raw_identity(path: Path) -> bool:
    """Whether ``path`` shares the raw tree's device/inode identity.

    Bind-mount and case-folded aliases keep distinct pathnames after
    ``resolve()`` but share the raw tree's identity.
    """

    resolved_raw_root = RAW_OUTPUT_ROOT.resolve(strict=False)
    raw_identity = _stat_identity(RAW_OUTPUT_ROOT)
    if raw_identity is None:
        raw_identity = _stat_identity(resolved_raw_root)
    if raw_identity is None:
        return False
    if raw_identity in _ancestor_identities(path):
        return True
    return raw_identity in _ancestor_identities(path.parent)


def _is_under_raw(path: Path) -> bool:
    """Whether ``path`` names or aliases the repository's raw output tree."""

    return _names_raw_tree(path) or _shares_raw_identity(path)


def _is_canonicalizable(value: Any) -> bool:
    """Whether ``value`` survives canonical JSON and UTF-8 encoding.

    ``json.loads`` accepts the non-standard ``NaN``/``Infinity`` literals, so a
    raw JSONL line can carry floats that cannot be re-encoded. Such a pair is
    excluded with a reason code instead of aborting the whole corpus scan.
    Escaped lone surrogates also pass JSON parsing but cannot be written to the
    UTF-8 JSONL destination, so exercise the actual output encoding here too.
    """

    try:
        canonical_json(value).encode("utf-8")
    except (UnicodeEncodeError, ValueError, TypeError):
        return False
    return True


def _dict_diff_paths(left: dict[str, Any], right: dict[str, Any], prefix: str) -> list[str]:
    paths: list[str] = []
    for key in sorted(set(left) | set(right)):
        path = f"{prefix}.{key}"
        if key not in left:
            paths.append(path)
            continue
        if key not in right:
            paths.append(path)
            continue
        paths.extend(_context_diff_paths(left[key], right[key], path))
    return paths


def _list_diff_paths(left: list[Any], right: list[Any], prefix: str) -> list[str]:
    if len(left) != len(right):
        return [prefix]
    paths: list[str] = []
    for index, (left_item, right_item) in enumerate(zip(left, right)):
        paths.extend(_context_diff_paths(left_item, right_item, f"{prefix}[{index}]"))
    return paths


def _context_diff_paths(left: Any, right: Any, prefix: str) -> list[str]:
    """Return stable leaf paths whose values differ."""

    if type(left) is not type(right):
        return [prefix]
    if isinstance(left, dict):
        return _dict_diff_paths(left, right, prefix)
    if isinstance(left, list):
        return _list_diff_paths(left, right, prefix)
    if left == right:
        return []
    return [prefix]


def _preference_context(
    record: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]] | None:
    chosen = record.get("chosen")
    rejected = record.get("rejected")
    if not isinstance(chosen, dict) or not isinstance(rejected, dict):
        return None
    if not all(
        isinstance(side.get(field), dict)
        for side in (chosen, rejected)
        for field in ("state", "proposed_action")
    ):
        return None
    return chosen, rejected


def context_is_pure(record: dict[str, Any]) -> bool:
    """Whether a preference record has canonical same-state/same-proposal context."""

    context = _preference_context(record)
    if context is None:
        return False
    chosen, rejected = context
    return all(
        canonical_json(chosen[field]) == canonical_json(rejected[field])
        for field in ("state", "proposed_action")
    )


def _all_context_diffs(
    chosen: dict[str, Any], rejected: dict[str, Any]
) -> tuple[str, ...]:
    paths: list[str] = []
    for field in ("state", "proposed_action"):
        paths.extend(_context_diff_paths(chosen[field], rejected[field], field))
    return tuple(paths)


def _identity_annotation_reference(
    chosen_value: dict[str, Any],
    rejected_value: dict[str, Any],
    field: str,
) -> tuple[dict[str, Any], str, str] | None:
    """Find an exact reference side for a top-level ``identity_note`` diff.

    The attesting side must become byte-equivalent to the other side after
    removing exactly one top-level annotation, and that annotation must start
    with a literal identity claim naming the other side and context field.
    """

    candidates = (
        ("chosen", chosen_value, "rejected", rejected_value),
        ("rejected", rejected_value, "chosen", chosen_value),
    )
    for attester_name, attester, reference_name, reference in candidates:
        note = attester.get("identity_note")
        if "identity_note" in reference or not isinstance(note, str):
            continue
        expected_prefix = f"IDENTICAL to {reference_name}.{field}"
        if not note.strip().startswith(expected_prefix):
            continue
        stripped = copy.deepcopy(attester)
        stripped.pop("identity_note")
        if canonical_json(stripped) == canonical_json(reference):
            return copy.deepcopy(reference), attester_name, reference_name
    return None


def _repair_identity_annotations(record: dict[str, Any]) -> CurationDecision | None:
    """Repair context that differs only by explicit branch identity notes."""

    context = _preference_context(record)
    if context is None:
        return None
    chosen, rejected = context
    repaired = copy.deepcopy(record)
    changed: list[str] = []

    for field in ("state", "proposed_action"):
        if canonical_json(chosen[field]) == canonical_json(rejected[field]):
            continue
        reference = _identity_annotation_reference(
            chosen[field], rejected[field], field
        )
        if reference is None:
            return None
        exact_value, attester_name, reference_name = reference
        repaired[attester_name][field] = copy.deepcopy(exact_value)
        repaired[reference_name][field] = copy.deepcopy(exact_value)
        changed.append(f"{attester_name}.{field}")

    if not changed or not context_is_pure(repaired):
        return None
    source_chosen, source_rejected = context
    return CurationDecision(
        action=ACTION_REPAIRED,
        classification="attested_identity_annotation_only",
        reason_codes=(
            "EXACT_CONTEXT_COPIED_FROM_ATTESTED_REFERENCE",
            "BRANCH_ONLY_IDENTITY_NOTE_REMOVED",
        ),
        record=repaired,
        context_diff_paths=_all_context_diffs(source_chosen, source_rejected),
        changed_context_fields=tuple(changed),
    )


def _without_proposal_annotations(value: dict[str, Any]) -> dict[str, Any]:
    stripped = copy.deepcopy(value)
    stripped.pop("source", None)
    readout = stripped.get("snn_readout")
    if isinstance(readout, dict):
        readout.pop("note", None)
    return stripped


def _proposal_annotation_reference(
    chosen: dict[str, Any], rejected: dict[str, Any]
) -> tuple[dict[str, Any], str, str] | None:
    """Find an exact proposal reference under a literal branch-identity claim."""

    diff_paths = set(_context_diff_paths(chosen, rejected, "proposed_action"))
    allowed_paths = {
        "proposed_action.source",
        "proposed_action.snn_readout.note",
    }
    if not diff_paths or not diff_paths.issubset(allowed_paths):
        return None
    if canonical_json(_without_proposal_annotations(chosen)) != canonical_json(
        _without_proposal_annotations(rejected)
    ):
        return None

    candidates = (
        ("chosen", chosen, "rejected", rejected),
        ("rejected", rejected, "chosen", chosen),
    )
    for attester_name, attester, reference_name, reference in candidates:
        attester_source = attester.get("source")
        reference_source = reference.get("source")
        if not isinstance(attester_source, str) or not isinstance(
            reference_source, str
        ):
            continue
        marker = f" — IDENTICAL proposal to the {reference_name} branch"
        if attester_source.startswith(reference_source + marker):
            return copy.deepcopy(reference), attester_name, reference_name
    return None


def _repair_proposal_annotations(record: dict[str, Any]) -> CurationDecision | None:
    """Repair an attested proposal whose only differences are annotations."""

    context = _preference_context(record)
    if context is None:
        return None
    chosen, rejected = context
    if canonical_json(chosen["state"]) != canonical_json(rejected["state"]):
        return None
    reference = _proposal_annotation_reference(
        chosen["proposed_action"], rejected["proposed_action"]
    )
    if reference is None:
        return None

    exact_value, attester_name, reference_name = reference
    repaired = copy.deepcopy(record)
    repaired[attester_name]["proposed_action"] = copy.deepcopy(exact_value)
    repaired[reference_name]["proposed_action"] = copy.deepcopy(exact_value)
    if not context_is_pure(repaired):
        return None
    return CurationDecision(
        action=ACTION_REPAIRED,
        classification="attested_proposal_annotation_only",
        reason_codes=(
            "EXACT_PROPOSAL_COPIED_FROM_ATTESTED_REFERENCE",
            "BRANCH_ONLY_PROPOSAL_ANNOTATION_REMOVED",
        ),
        record=repaired,
        context_diff_paths=_all_context_diffs(chosen, rejected),
        changed_context_fields=(f"{attester_name}.proposed_action",),
    )


def _paths_with_prefix(paths: tuple[str, ...], prefix: str) -> list[str]:
    return [path for path in paths if path.startswith(prefix)]


def _state_exclusion_reason(state_paths: list[str]) -> str | None:
    if not state_paths:
        return None
    if set(state_paths).issubset({"state.episode_id", "state.note"}):
        return "BRANCH_SPECIFIC_STATE_METADATA_UNSAFE_TO_NORMALIZE"
    if any(path.startswith("state.agent.gate_memory") for path in state_paths):
        return "POLICY_MEMORY_CONTEXT_DIVERGES"
    return "STATE_CONTEXT_DIVERGES"


def _exclusion_reasons(context_diff_paths: tuple[str, ...]) -> tuple[str, ...]:
    reasons: list[str] = []
    state_reason = _state_exclusion_reason(_paths_with_prefix(context_diff_paths, "state"))
    if state_reason is not None:
        reasons.append(state_reason)
    if _paths_with_prefix(context_diff_paths, "proposed_action"):
        reasons.append("PROPOSED_ACTION_CONTEXT_DIVERGES")
    if reasons:
        return tuple(reasons)
    return ("PREFERENCE_CONTEXT_DIVERGES",)


def curate_preference_record(record: dict[str, Any]) -> CurationDecision:
    """Curate one pair without mutating ``record``."""

    if not isinstance(record, dict):
        return CurationDecision(
            action=ACTION_EXCLUDED,
            classification="malformed_preference_context",
            reason_codes=("PREFERENCE_RECORD_NOT_AN_OBJECT",),
            record=None,
            context_diff_paths=(),
        )
    if not _is_canonicalizable(record):
        # Checked before the context shape so a non-finite float anywhere in
        # the pair is reported precisely instead of surfacing as a bare
        # ValueError from the first canonical comparison.
        return CurationDecision(
            action=ACTION_EXCLUDED,
            classification="malformed_preference_context",
            reason_codes=("PREFERENCE_RECORD_NOT_JSON_SERIALIZABLE",),
            record=None,
            context_diff_paths=(),
        )
    context = _preference_context(record)
    if context is None:
        return CurationDecision(
            action=ACTION_EXCLUDED,
            classification="malformed_preference_context",
            reason_codes=("PREFERENCE_CONTEXT_MISSING_OR_INVALID",),
            record=None,
            context_diff_paths=(),
        )

    chosen, rejected = context
    context_diff_paths = _all_context_diffs(chosen, rejected)
    if not context_diff_paths:
        return CurationDecision(
            action=ACTION_RETAINED,
            classification="already_same_context",
            reason_codes=("PREFERENCE_CONTEXT_ALREADY_IDENTICAL",),
            record=copy.deepcopy(record),
            context_diff_paths=(),
        )

    repaired = _repair_identity_annotations(record)
    if repaired is not None:
        return repaired
    repaired = _repair_proposal_annotations(record)
    if repaired is not None:
        return repaired

    return CurationDecision(
        action=ACTION_EXCLUDED,
        classification="unsupported_context_divergence",
        reason_codes=_exclusion_reasons(context_diff_paths),
        record=None,
        context_diff_paths=context_diff_paths,
    )


def _is_preference_candidate(record: Any) -> bool:
    return isinstance(record, dict) and any(
        key in record for key in ("chosen", "rejected", "reward_delta")
    )


def _source_files(source: Path) -> tuple[Path, ...]:
    if source.is_file():
        if source.suffix != ".jsonl":
            raise PreferenceCurationError(f"source file must be JSONL: {source}")
        return (source,)
    if source.is_dir():
        files = tuple(sorted(source.rglob("*.jsonl")))
        if not files:
            raise PreferenceCurationError(f"no JSONL files under source: {source}")
        return files
    raise PreferenceCurationError(f"source does not exist: {source}")


def _relative_source_path(source: Path, path: Path) -> str:
    if source.is_dir():
        return path.relative_to(source).as_posix()
    return path.name


def _jsonl_payload_lines(file_payload: bytes) -> tuple[tuple[int, bytes], ...]:
    return tuple(
        (line_number, raw_line)
        for line_number, raw_line in enumerate(file_payload.splitlines(), 1)
        if raw_line.strip()
    )


def _load_jsonl_record(line: _SourceLine) -> Any:
    try:
        text = line.payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise PreferenceCurationError(
            f"{line.relative_path}:{line.number}: invalid UTF-8: {exc}"
        ) from exc
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise PreferenceCurationError(
            f"{line.relative_path}:{line.number}: invalid JSON: {exc}"
        ) from exc


def _manifest_source_id(record: Any) -> Any:
    # An excluded record may itself hold a non-encodable id; the source
    # reference survives as path, line, and hash either way.
    source_record_id = record.get("id") if isinstance(record, dict) else None
    if _is_canonicalizable(source_record_id):
        return source_record_id
    return None


def _kept_output(
    decision: CurationDecision, location: str
) -> tuple[dict[str, Any] | None, Any, str | None]:
    record = decision.record
    if record is None:
        return None, None, None
    if not context_is_pure(record):
        raise PreferenceCurationError(
            f"internal error: emitted impure pair at {location}"
        )
    output_hash = _sha256(canonical_json(record).encode("utf-8"))
    return record, record.get("id"), output_hash


def _record_preference(state: _ScanState, line: _SourceLine, record: Any) -> None:
    decision = curate_preference_record(record)
    state.actions[decision.action] += 1
    state.classifications[decision.classification] += 1
    state.reasons.update(decision.reason_codes)
    emitted, output_id, output_hash = _kept_output(
        decision, f"{line.relative_path}:{line.number}"
    )
    if emitted is not None:
        state.records.append(emitted)
    state.manifest.append(
        {
            "source_path": line.relative_path,
            "source_line": line.number,
            # Hash excludes the JSONL line terminator by definition.
            "source_sha256": _sha256(line.payload),
            "source_file_sha256": line.file_sha256,
            "source_record_id": _manifest_source_id(record),
            "transform": {
                "name": TRANSFORM_NAME,
                "version": TRANSFORM_VERSION,
            },
            "action": decision.action,
            "classification": decision.classification,
            "reason_codes": list(decision.reason_codes),
            "context_diff_paths": list(decision.context_diff_paths),
            "changed_context_fields": list(decision.changed_context_fields),
            "output_id": output_id,
            "output_sha256": output_hash,
        }
    )


def _curate_jsonl_file(source: Path, path: Path, state: _ScanState) -> None:
    file_payload = path.read_bytes()
    file_hash = _sha256(file_payload)
    relative_path = _relative_source_path(source, path)
    for line_number, raw_line in _jsonl_payload_lines(file_payload):
        line = _SourceLine(relative_path, line_number, raw_line, file_hash)
        state.json_records_seen += 1
        record = _load_jsonl_record(line)
        if not _is_preference_candidate(record):
            state.skipped_non_preferences += 1
            continue
        _record_preference(state, line, record)


def _curation_summary(source: Path, state: _ScanState) -> dict[str, Any]:
    preference_records = sum(state.actions.values())
    impure_pairs = state.actions[ACTION_REPAIRED] + state.actions[ACTION_EXCLUDED]
    retained_pairs = state.actions[ACTION_RETAINED] + state.actions[ACTION_REPAIRED]
    # Measured over the records actually emitted rather than asserted as a
    # constant, so the reported purity is evidence and not a restatement of
    # the invariant the loop above enforces.
    pure_outputs = sum(1 for emitted in state.records if context_is_pure(emitted))
    purity_pct = 0.0
    if retained_pairs:
        purity_pct = round(100.0 * pure_outputs / retained_pairs, 1)
    return {
        "transform": {"name": TRANSFORM_NAME, "version": TRANSFORM_VERSION},
        "source": str(source),
        "json_records_seen": state.json_records_seen,
        "preference_records": preference_records,
        "skipped_non_preference_records": state.skipped_non_preferences,
        "impure_pairs": impure_pairs,
        "retained_pairs": retained_pairs,
        "excluded_pairs": state.actions[ACTION_EXCLUDED],
        "actions": dict(sorted(state.actions.items())),
        "classifications": dict(sorted(state.classifications.items())),
        "reason_codes": dict(sorted(state.reasons.items())),
        "retained_context_purity_pct": purity_pct,
    }


def curate_source(source: Path) -> CurationRun:
    """Read and classify all preference candidates under ``source``."""

    source = Path(source)
    state = _ScanState([], [], Counter(), Counter(), Counter())
    for path in _source_files(source):
        _curate_jsonl_file(source, path, state)
    return CurationRun(
        tuple(state.records),
        tuple(state.manifest),
        _curation_summary(source, state),
    )


def _refuse_raw_destination(destination: Path, label: str) -> None:
    if not _is_under_raw(destination):
        return
    # A file source has no directory to nest inside, and a directory source
    # does not contain its own siblings, so the remaining destination checks
    # cannot keep a curated write out of the immutable raw tree on their own.
    raise PreferenceCurationError(
        f"{label} would write inside immutable raw evidence: {destination}"
    )


def _refuse_existing_destination(destination: Path, label: str) -> None:
    if destination.exists():
        raise PreferenceCurationError(
            f"{label} already exists; refusing overwrite: {destination}"
        )
    if destination.parent.is_dir():
        return
    raise PreferenceCurationError(
        f"{label} parent does not exist: {destination.parent}"
    )


def _destination_replaces_source(source: Path, destination: Path) -> bool:
    return source.resolve() == destination.resolve(strict=False)


def _destination_inside_source(source: Path, destination: Path) -> bool:
    if not source.is_dir():
        return False
    return source.resolve() in destination.resolve(strict=False).parents


def _refuse_source_collision(source: Path, destination: Path, label: str) -> None:
    if _destination_replaces_source(source, destination):
        raise PreferenceCurationError(f"{label} cannot replace source: {destination}")
    if not _destination_inside_source(source, destination):
        return
    raise PreferenceCurationError(
        f"{label} cannot be written inside source: {destination}"
    )


def _assert_new_destination(source: Path, destination: Path, label: str) -> None:
    _refuse_raw_destination(destination, label)
    _refuse_existing_destination(destination, label)
    _refuse_source_collision(source, destination, label)


def _jsonl_payload(records: tuple[dict[str, Any], ...]) -> str:
    return "".join(canonical_json(record) + "\n" for record in records)


def _create_exclusive_file(path: Path, payload: str, created: list[Path]) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    created.append(path)
    with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())


def _fsync_parents(paths: list[Path]) -> None:
    # Durable file contents still need a durable directory entry.
    for directory in dict.fromkeys(path.parent for path in paths):
        directory_descriptor = os.open(directory, os.O_RDONLY)
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)


def _unlink_created(created: list[Path]) -> None:
    # Remove only files this invocation created; pre-existing paths are
    # rejected before and during O_EXCL creation.
    for path in created:
        try:
            path.unlink()
        except FileNotFoundError:
            pass


def write_run(run: CurationRun, source: Path, output: Path, manifest: Path) -> None:
    """Write a curation run to two absent destinations without clobbering."""

    source = Path(source)
    output = Path(output)
    manifest = Path(manifest)
    if output.resolve(strict=False) == manifest.resolve(strict=False):
        raise PreferenceCurationError("output and manifest destinations must differ")
    _assert_new_destination(source, output, "output")
    _assert_new_destination(source, manifest, "manifest")

    created: list[Path] = []
    try:
        for path, payload in (
            (output, _jsonl_payload(run.records)),
            (manifest, _jsonl_payload(run.manifest)),
        ):
            _create_exclusive_file(path, payload, created)
        _fsync_parents(created)
    except Exception:
        _unlink_created(created)
        raise


def _render_human(run: CurationRun) -> str:
    summary = run.summary
    lines = [
        f"Preference records: {summary['preference_records']}",
        f"Impure: {summary['impure_pairs']}",
        f"Retained: {summary['retained_pairs']}",
        f"Excluded: {summary['excluded_pairs']}",
        f"Retained context purity: {summary['retained_context_purity_pct']:.1f}%",
        "Decisions:",
    ]
    for entry in run.manifest:
        location = f"{entry['source_path']}:{entry['source_line']}"
        record_id = entry["source_record_id"] or "<no-id>"
        reasons = ",".join(entry["reason_codes"])
        lines.append(f"- {location} {record_id}: {entry['action']} [{reasons}]")
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan = subparsers.add_parser("scan", help="classify preferences without writing")
    scan.add_argument("source", type=Path)
    scan.add_argument(
        "--json", action="store_true", help="emit summary and decisions as JSON"
    )

    curate = subparsers.add_parser(
        "curate", help="write retained preferences and manifest"
    )
    curate.add_argument("source", type=Path)
    curate.add_argument("--output", type=Path, required=True)
    curate.add_argument("--manifest", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        run = curate_source(args.source)
        if args.command == "scan":
            if args.json:
                print(
                    json.dumps(
                        {"summary": run.summary, "decisions": run.manifest},
                        indent=2,
                        sort_keys=True,
                        ensure_ascii=False,
                    )
                )
            else:
                print(_render_human(run))
            return 0

        write_run(run, args.source, args.output, args.manifest)
        print(json.dumps(run.summary, sort_keys=True))
        return 0
    except (OSError, PreferenceCurationError, ValueError) as exc:
        print(f"preference curation failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
