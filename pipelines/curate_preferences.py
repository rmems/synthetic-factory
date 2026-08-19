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


def _context_diff_paths(left: Any, right: Any, prefix: str) -> list[str]:
    """Return stable leaf paths whose values differ."""

    if type(left) is not type(right):
        return [prefix]
    if isinstance(left, dict):
        paths: list[str] = []
        for key in sorted(set(left) | set(right)):
            path = f"{prefix}.{key}"
            if key not in left or key not in right:
                paths.append(path)
            else:
                paths.extend(_context_diff_paths(left[key], right[key], path))
        return paths
    if isinstance(left, list):
        if len(left) != len(right):
            return [prefix]
        paths = []
        for index, (left_item, right_item) in enumerate(zip(left, right)):
            paths.extend(
                _context_diff_paths(left_item, right_item, f"{prefix}[{index}]")
            )
        return paths
    return [] if left == right else [prefix]


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


def _exclusion_reasons(context_diff_paths: tuple[str, ...]) -> tuple[str, ...]:
    reasons: list[str] = []
    state_paths = [path for path in context_diff_paths if path.startswith("state")]
    proposal_paths = [
        path for path in context_diff_paths if path.startswith("proposed_action")
    ]

    if state_paths and set(state_paths).issubset({"state.episode_id", "state.note"}):
        reasons.append("BRANCH_SPECIFIC_STATE_METADATA_UNSAFE_TO_NORMALIZE")
    elif any(path.startswith("state.agent.gate_memory") for path in state_paths):
        reasons.append("POLICY_MEMORY_CONTEXT_DIVERGES")
    elif state_paths:
        reasons.append("STATE_CONTEXT_DIVERGES")

    if proposal_paths:
        reasons.append("PROPOSED_ACTION_CONTEXT_DIVERGES")
    return tuple(reasons or ("PREFERENCE_CONTEXT_DIVERGES",))


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


def curate_source(source: Path) -> CurationRun:
    """Read and classify all preference candidates under ``source``."""

    source = Path(source)
    output_records: list[dict[str, Any]] = []
    manifest: list[dict[str, Any]] = []
    actions: Counter[str] = Counter()
    classifications: Counter[str] = Counter()
    reasons: Counter[str] = Counter()
    skipped_non_preferences = 0
    total_json_records = 0

    for path in _source_files(source):
        file_payload = path.read_bytes()
        file_hash = _sha256(file_payload)
        relative_path = _relative_source_path(source, path)
        for line_number, raw_line in enumerate(file_payload.splitlines(), 1):
            if not raw_line.strip():
                continue
            total_json_records += 1
            try:
                text = raw_line.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise PreferenceCurationError(
                    f"{relative_path}:{line_number}: invalid UTF-8: {exc}"
                ) from exc
            try:
                record = json.loads(text)
            except json.JSONDecodeError as exc:
                raise PreferenceCurationError(
                    f"{relative_path}:{line_number}: invalid JSON: {exc}"
                ) from exc
            if not _is_preference_candidate(record):
                skipped_non_preferences += 1
                continue

            decision = curate_preference_record(record)
            actions[decision.action] += 1
            classifications[decision.classification] += 1
            reasons.update(decision.reason_codes)

            output_hash = None
            output_id = None
            if decision.record is not None:
                if not context_is_pure(decision.record):
                    raise PreferenceCurationError(
                        f"internal error: emitted impure pair at {relative_path}:{line_number}"
                    )
                output_line = canonical_json(decision.record).encode("utf-8")
                output_hash = _sha256(output_line)
                output_id = decision.record.get("id")
                output_records.append(decision.record)

            manifest.append(
                {
                    "source_path": relative_path,
                    "source_line": line_number,
                    # Hash excludes the JSONL line terminator by definition.
                    "source_sha256": _sha256(raw_line),
                    "source_file_sha256": file_hash,
                    "source_record_id": record.get("id")
                    if isinstance(record, dict)
                    else None,
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

    preference_records = sum(actions.values())
    impure_pairs = actions[ACTION_REPAIRED] + actions[ACTION_EXCLUDED]
    retained_pairs = actions[ACTION_RETAINED] + actions[ACTION_REPAIRED]
    summary = {
        "transform": {"name": TRANSFORM_NAME, "version": TRANSFORM_VERSION},
        "source": str(source),
        "json_records_seen": total_json_records,
        "preference_records": preference_records,
        "skipped_non_preference_records": skipped_non_preferences,
        "impure_pairs": impure_pairs,
        "retained_pairs": retained_pairs,
        "excluded_pairs": actions[ACTION_EXCLUDED],
        "actions": dict(sorted(actions.items())),
        "classifications": dict(sorted(classifications.items())),
        "reason_codes": dict(sorted(reasons.items())),
        "retained_context_purity_pct": 100.0 if retained_pairs else 0.0,
    }
    return CurationRun(tuple(output_records), tuple(manifest), summary)


def _assert_new_destination(source: Path, destination: Path, label: str) -> None:
    source_resolved = source.resolve()
    destination_resolved = destination.resolve(strict=False)
    if destination.exists():
        raise PreferenceCurationError(
            f"{label} already exists; refusing overwrite: {destination}"
        )
    if not destination.parent.is_dir():
        raise PreferenceCurationError(
            f"{label} parent does not exist: {destination.parent}"
        )
    if source_resolved == destination_resolved:
        raise PreferenceCurationError(f"{label} cannot replace source: {destination}")
    if source.is_dir() and source_resolved in destination_resolved.parents:
        raise PreferenceCurationError(
            f"{label} cannot be written inside source: {destination}"
        )


def write_run(run: CurationRun, source: Path, output: Path, manifest: Path) -> None:
    """Write a curation run to two absent destinations without clobbering."""

    source = Path(source)
    output = Path(output)
    manifest = Path(manifest)
    if output.resolve(strict=False) == manifest.resolve(strict=False):
        raise PreferenceCurationError("output and manifest destinations must differ")
    _assert_new_destination(source, output, "output")
    _assert_new_destination(source, manifest, "manifest")

    output_payload = "".join(canonical_json(record) + "\n" for record in run.records)
    manifest_payload = "".join(canonical_json(entry) + "\n" for entry in run.manifest)
    created: list[Path] = []
    try:
        for path, payload in ((output, output_payload), (manifest, manifest_payload)):
            descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
            created.append(path)
            with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
        # Durable file contents still need a durable directory entry.
        for directory in dict.fromkeys(path.parent for path in created):
            directory_descriptor = os.open(directory, os.O_RDONLY)
            try:
                os.fsync(directory_descriptor)
            finally:
                os.close(directory_descriptor)
    except Exception:
        # Remove only files this invocation created; pre-existing paths are
        # rejected before and during O_EXCL creation.
        for path in created:
            try:
                path.unlink()
            except FileNotFoundError:
                pass
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
