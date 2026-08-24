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

Read-only impure-pair audit (public ID list plus reason codes)::

    python3 pipelines/curate_preferences.py audit <source> --json
    python3 pipelines/curate_preferences.py audit <source> --markdown
    python3 pipelines/curate_preferences.py audit <source> --expect <audit.json>

Read-only agreement check between two copies of one corpus::

    python3 pipelines/curate_preferences.py reconcile <source-a> <source-b>

Write a new preference JSONL and manifest (both destinations must be absent)::

    python3 pipelines/curate_preferences.py curate <source> \
      --output <new-preferences.jsonl> --manifest <new-manifest.jsonl>

``source`` may be one JSONL file or a directory scanned recursively. Records
without preference-pair fields are counted and skipped; malformed preference
candidates are explicitly excluded rather than silently dropped.

A skipped record whose payload kind names a different generation mill (an
agentic episode inside a preference tree, for example) is *quarantined*: it
gets its own manifest row and its own summary counter so it can never be
absorbed into a preference-pair denominator. See ``pipelines/leftover_mill.py``
and ``docs/leftover-mill-quarantine.md``.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import sys
from collections import Counter
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

import leftover_mill  # noqa: E402


TRANSFORM_NAME = "same-context-preference-curation"
TRANSFORM_VERSION = "1.1.0"

AUDIT_NAME = "same-context-preference-audit"
AUDIT_SCHEMA_VERSION = "1.0.0"

ACTION_RETAINED = "retained"
ACTION_REPAIRED = "repaired"
ACTION_EXCLUDED = "excluded"
# Quarantine is not a preference decision: a leftover-mill record never was a
# pair, so it is recorded separately and never counted in a pair denominator.
ACTION_QUARANTINED = "quarantined"


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
    # Source-side agreement per canonical context field, before any repair.
    # ``None`` on both means the pair carries no comparable context at all.
    same_state: bool | None = None
    same_proposed_action: bool | None = None


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


def context_field_agreement(
    record: Any,
) -> tuple[bool | None, bool | None]:
    """Return ``(same_state, same_proposed_action)`` for one source pair.

    ``same_state`` is exactly the invariant a Hub-side ``same_state`` audit
    measures. ``same_proposed_action`` is the second half of the same-context
    contract, which such an audit does not see: a pair may hold state constant
    and still swap the proposed action. Both are ``None`` when the record
    carries no comparable preference context.
    """

    context = _preference_context(record) if isinstance(record, dict) else None
    if context is None:
        return None, None
    chosen, rejected = context
    return (
        canonical_json(chosen["state"]) == canonical_json(rejected["state"]),
        canonical_json(chosen["proposed_action"])
        == canonical_json(rejected["proposed_action"]),
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
    same_state, same_proposed_action = context_field_agreement(record)
    context_diff_paths = _all_context_diffs(chosen, rejected)
    if not context_diff_paths:
        return CurationDecision(
            action=ACTION_RETAINED,
            classification="already_same_context",
            reason_codes=("PREFERENCE_CONTEXT_ALREADY_IDENTICAL",),
            record=copy.deepcopy(record),
            context_diff_paths=(),
            same_state=same_state,
            same_proposed_action=same_proposed_action,
        )

    # Repairs report the agreement of the *source* pair, not of their own
    # output: the audit has to keep naming a repaired pair as impure evidence.
    for repair in (_repair_identity_annotations, _repair_proposal_annotations):
        repaired = repair(record)
        if repaired is not None:
            return replace(
                repaired,
                same_state=same_state,
                same_proposed_action=same_proposed_action,
            )

    return CurationDecision(
        action=ACTION_EXCLUDED,
        classification="unsupported_context_divergence",
        reason_codes=_exclusion_reasons(context_diff_paths),
        record=None,
        context_diff_paths=context_diff_paths,
        same_state=same_state,
        same_proposed_action=same_proposed_action,
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


def _skipped_manifest_entry(
    relative_path: str,
    line_number: int,
    raw_line: bytes,
    file_hash: str,
    record: Any,
    mill_kind: str,
) -> dict[str, Any]:
    """Return a manifest row for a quarantined leftover-mill record."""

    return {
        "source_path": relative_path,
        "source_line": line_number,
        "source_sha256": _sha256(raw_line),
        "source_file_sha256": file_hash,
        "source_record_id": leftover_mill.record_id(record),
        "transform": {"name": TRANSFORM_NAME, "version": TRANSFORM_VERSION},
        "action": ACTION_QUARANTINED,
        "classification": f"leftover_mill_{mill_kind}",
        "reason_codes": [leftover_mill.REASON_KIND_MIX],
        "context_diff_paths": [],
        "changed_context_fields": [],
        "output_id": None,
        "output_sha256": None,
    }


def _agreement_labels(decision: CurationDecision) -> tuple[str, ...]:
    """Return the disjoint agreement buckets one decision contributes to."""

    if decision.same_state is None or decision.same_proposed_action is None:
        return ("undetermined",)
    labels: list[str] = []
    if decision.same_state:
        labels.append("same_state")
    if decision.same_proposed_action:
        labels.append("same_proposed_action")
    if not decision.same_state and not decision.same_proposed_action:
        labels.append("both_divergent")
    elif not decision.same_state:
        labels.append("state_only_divergent")
    elif not decision.same_proposed_action:
        labels.append("proposed_action_only_divergent")
    return tuple(labels)


def curate_source(source: Path) -> CurationRun:
    """Read and classify all preference candidates under ``source``."""

    source = Path(source)
    output_records: list[dict[str, Any]] = []
    manifest: list[dict[str, Any]] = []
    actions: Counter[str] = Counter()
    classifications: Counter[str] = Counter()
    reasons: Counter[str] = Counter()
    agreement: Counter[str] = Counter()
    skipped_non_preferences = 0
    leftover_mill_kinds: Counter[str] = Counter()
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
            mill_kind = leftover_mill.kind_mix_kind(record, "preference")
            if mill_kind is not None:
                # A concrete foreign generation kind takes precedence over the
                # loose candidate heuristic. An episode carrying reward_delta,
                # for example, is still an episode and must never enter the
                # preference denominator as a malformed pair.
                skipped_non_preferences += 1
                leftover_mill_kinds[mill_kind] += 1
                manifest.append(
                    _skipped_manifest_entry(
                        relative_path,
                        line_number,
                        raw_line,
                        file_hash,
                        record,
                        mill_kind,
                    )
                )
                continue
            if not _is_preference_candidate(record):
                skipped_non_preferences += 1
                continue

            decision = curate_preference_record(record)
            actions[decision.action] += 1
            classifications[decision.classification] += 1
            reasons.update(decision.reason_codes)
            agreement.update(_agreement_labels(decision))

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
                    "same_state": decision.same_state,
                    "same_proposed_action": decision.same_proposed_action,
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
        # Subset of the skipped records whose payload kind names a different
        # generation mill. Reported separately so a preference yield can never
        # quietly absorb them into a pair denominator.
        "leftover_mill_records": sum(leftover_mill_kinds.values()),
        "leftover_mill_kinds": dict(sorted(leftover_mill_kinds.items())),
        "impure_pairs": impure_pairs,
        "retained_pairs": retained_pairs,
        "excluded_pairs": actions[ACTION_EXCLUDED],
        # Reconciliation between a state-only Hub audit and this scan: a
        # ``same_state``-only measurement cannot see a pair that holds state
        # constant and diverges on the proposed action.
        "same_state_pairs": agreement["same_state"],
        "state_divergent_pairs": (
            agreement["state_only_divergent"] + agreement["both_divergent"]
        ),
        "same_proposed_action_pairs": agreement["same_proposed_action"],
        "proposed_action_divergent_pairs": (
            agreement["proposed_action_only_divergent"] + agreement["both_divergent"]
        ),
        "state_only_divergent_pairs": agreement["state_only_divergent"],
        "proposed_action_only_divergent_pairs": agreement[
            "proposed_action_only_divergent"
        ],
        "both_context_fields_divergent_pairs": agreement["both_divergent"],
        "context_undetermined_pairs": agreement["undetermined"],
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


def _divergent_context_fields(entry: dict[str, Any]) -> list[str]:
    """Return the canonical context fields that differ across the two sides."""

    if entry.get("same_state") is None or entry.get("same_proposed_action") is None:
        return []
    fields = []
    if not entry["same_state"]:
        fields.append("state")
    if not entry["same_proposed_action"]:
        fields.append("proposed_action")
    return fields


def build_audit(run: CurationRun) -> dict[str, Any]:
    """Return the public impure-pair audit document for one curation run.

    The document is the machine-readable half of the published audit: every
    impure pair by source location and record id, the reason codes behind its
    curation decision, and the state/proposal split that reconciles a
    ``same_state``-only count against the full same-context count.
    """

    summary = run.summary
    impure_pairs = [
        {
            "source_path": entry["source_path"],
            "source_line": entry["source_line"],
            "source_sha256": entry["source_sha256"],
            "record_id": entry["source_record_id"],
            "action": entry["action"],
            "classification": entry["classification"],
            "reason_codes": list(entry["reason_codes"]),
            "same_state": entry["same_state"],
            "same_proposed_action": entry["same_proposed_action"],
            "divergent_context_fields": _divergent_context_fields(entry),
            "context_diff_paths": list(entry["context_diff_paths"]),
        }
        for entry in run.manifest
        if entry["action"] != ACTION_RETAINED
    ]
    balanced = (
        summary["state_only_divergent_pairs"]
        + summary["proposed_action_only_divergent_pairs"]
        + summary["both_context_fields_divergent_pairs"]
        + summary["context_undetermined_pairs"]
    )
    if (
        balanced != summary["impure_pairs"]
        or len(impure_pairs) != summary["impure_pairs"]
    ):
        raise PreferenceCurationError(
            "internal error: impure-pair reconciliation does not balance "
            f"({len(impure_pairs)} listed, {balanced} bucketed, "
            f"{summary['impure_pairs']} impure)"
        )
    return {
        "schema_version": AUDIT_SCHEMA_VERSION,
        "audit": AUDIT_NAME,
        "transform": dict(summary["transform"]),
        "summary": {
            "preference_pairs": summary["preference_records"],
            "impure_pairs": summary["impure_pairs"],
            "same_state_pairs": summary["same_state_pairs"],
            "state_divergent_pairs": summary["state_divergent_pairs"],
            "proposed_action_divergent_pairs": summary[
                "proposed_action_divergent_pairs"
            ],
            "state_only_divergent_pairs": summary["state_only_divergent_pairs"],
            "proposed_action_only_divergent_pairs": summary[
                "proposed_action_only_divergent_pairs"
            ],
            "both_context_fields_divergent_pairs": summary[
                "both_context_fields_divergent_pairs"
            ],
            "context_undetermined_pairs": summary["context_undetermined_pairs"],
            "curated_retained_pairs": summary["retained_pairs"],
            "curated_repaired_pairs": summary["actions"].get(ACTION_REPAIRED, 0),
            "curated_excluded_pairs": summary["excluded_pairs"],
            "retained_context_purity_pct": summary["retained_context_purity_pct"],
        },
        "impure_pairs": impure_pairs,
    }


def _yes_no(value: bool | None) -> str:
    if value is None:
        return "n/a"
    return "yes" if value else "no"


def render_audit_markdown(audit: dict[str, Any]) -> str:
    """Render the audit document as the published Markdown tables."""

    summary = audit["summary"]
    lines = [
        "| Measure | Pairs |",
        "| --- | ---: |",
        f"| Published preference pairs | {summary['preference_pairs']} |",
        "| `same_state = false` (state diverges) | "
        f"{summary['state_divergent_pairs']} |",
        "| `same_proposed_action = false` (proposal diverges) | "
        f"{summary['proposed_action_divergent_pairs']} |",
        f"| Impure pairs (either field diverges) | {summary['impure_pairs']} |",
        f"| - state only | {summary['state_only_divergent_pairs']} |",
        "| - proposed action only | "
        f"{summary['proposed_action_only_divergent_pairs']} |",
        f"| - both fields | {summary['both_context_fields_divergent_pairs']} |",
        f"| - context not comparable | {summary['context_undetermined_pairs']} |",
        "| Curated keep (already identical + repaired) | "
        f"{summary['curated_retained_pairs']} |",
        f"| Curated exclude | {summary['curated_excluded_pairs']} |",
        "| Curated same-context purity | "
        f"{summary['retained_context_purity_pct']:.1f}% |",
        "",
        "| Pair | Source | `same_state` | `same_proposed_action` | Curation "
        "| Reason codes |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for pair in audit["impure_pairs"]:
        record_id = pair["record_id"]
        identifier = f"`{record_id}`" if record_id else "_(no record id)_"
        reasons = ", ".join(f"`{code}`" for code in pair["reason_codes"]) or "_(none)_"
        lines.append(
            f"| {identifier} "
            f"| `{pair['source_path']}:{pair['source_line']}` "
            f"| {_yes_no(pair['same_state'])} "
            f"| {_yes_no(pair['same_proposed_action'])} "
            f"| {pair['action']} "
            f"| {reasons} |"
        )
    return "\n".join(lines)


def _location_sort_key(location: tuple[Any, Any]) -> tuple[str, int, str]:
    path_part, line_part = location
    line_number = line_part if isinstance(line_part, int) else 0
    return (str(path_part), line_number, str(line_part))


def _pairs_by_location(pairs: Any) -> dict[tuple[Any, Any], dict[str, Any]]:
    located: dict[tuple[Any, Any], dict[str, Any]] = {}
    for pair in pairs if isinstance(pairs, list) else ():
        if isinstance(pair, dict):
            located[(pair.get("source_path"), pair.get("source_line"))] = pair
    return located


AUDIT_PAIR_FIELDS = (
    "source_sha256",
    "record_id",
    "action",
    "classification",
    "reason_codes",
    "same_state",
    "same_proposed_action",
    "divergent_context_fields",
    "context_diff_paths",
)


def audit_differences(expected: Any, actual: dict[str, Any]) -> list[str]:
    """Return every way ``actual`` departs from a previously published audit."""

    if not isinstance(expected, dict):
        return ["expected audit document is not a JSON object"]
    differences: list[str] = []
    for key in ("schema_version", "audit", "transform"):
        if expected.get(key) != actual.get(key):
            differences.append(
                f"{key}: expected {expected.get(key)!r}, got {actual.get(key)!r}"
            )
    expected_summary = expected.get("summary")
    expected_summary = expected_summary if isinstance(expected_summary, dict) else {}
    for key in sorted(set(expected_summary) | set(actual["summary"])):
        if expected_summary.get(key) != actual["summary"].get(key):
            differences.append(
                f"summary.{key}: expected {expected_summary.get(key)!r}, "
                f"got {actual['summary'].get(key)!r}"
            )

    expected_pairs = _pairs_by_location(expected.get("impure_pairs"))
    actual_pairs = _pairs_by_location(actual["impure_pairs"])
    for location in sorted(
        set(expected_pairs) - set(actual_pairs), key=_location_sort_key
    ):
        differences.append(
            f"{location[0]}:{location[1]}: "
            "audited impure pair is absent from this scan"
        )
    for location in sorted(
        set(actual_pairs) - set(expected_pairs), key=_location_sort_key
    ):
        differences.append(
            f"{location[0]}:{location[1]}: impure pair is absent from the audit"
        )
    for location in sorted(
        set(expected_pairs) & set(actual_pairs), key=_location_sort_key
    ):
        for field in AUDIT_PAIR_FIELDS:
            want = expected_pairs[location].get(field)
            got = actual_pairs[location].get(field)
            if want != got:
                differences.append(
                    f"{location[0]}:{location[1]}: {field}: "
                    f"expected {want!r}, got {got!r}"
                )
    return differences


RECONCILE_DECISION_FIELDS = (
    "action",
    "classification",
    "reason_codes",
    "same_state",
    "same_proposed_action",
    "context_diff_paths",
)
RECONCILE_PAYLOAD_FIELDS = ("source_sha256", "source_record_id")
RECONCILE_COVERAGE_KEYS = (
    "json_records_seen",
    "preference_records",
    "skipped_non_preference_records",
)


def reconcile_runs(first: CurationRun, second: CurationRun) -> dict[str, list[str]]:
    """Compare two scans of one corpus, keyed by source path and line.

    ``coverage`` reports records one copy has and the other does not,
    ``decisions`` reports curation verdicts that disagree, and ``payload``
    reports agreeing verdicts reached from different source bytes.
    """

    coverage: list[str] = []
    decisions: list[str] = []
    payload: list[str] = []

    for key in RECONCILE_COVERAGE_KEYS:
        if first.summary[key] != second.summary[key]:
            coverage.append(
                f"summary.{key}: first {first.summary[key]}, "
                f"second {second.summary[key]}"
            )

    def located(run: CurationRun) -> dict[tuple[str, int], dict[str, Any]]:
        return {
            (entry["source_path"], entry["source_line"]): entry
            for entry in run.manifest
        }

    first_entries = located(first)
    second_entries = located(second)
    for location in sorted(
        set(first_entries) - set(second_entries), key=_location_sort_key
    ):
        coverage.append(f"{location[0]}:{location[1]}: present in the first source only")
    for location in sorted(
        set(second_entries) - set(first_entries), key=_location_sort_key
    ):
        coverage.append(
            f"{location[0]}:{location[1]}: present in the second source only"
        )

    for location in sorted(
        set(first_entries) & set(second_entries), key=_location_sort_key
    ):
        for field, bucket in (
            *((field, decisions) for field in RECONCILE_DECISION_FIELDS),
            *((field, payload) for field in RECONCILE_PAYLOAD_FIELDS),
        ):
            if first_entries[location][field] != second_entries[location][field]:
                bucket.append(
                    f"{location[0]}:{location[1]}: {field}: "
                    f"first {first_entries[location][field]!r}, "
                    f"second {second_entries[location][field]!r}"
                )
    return {"coverage": coverage, "decisions": decisions, "payload": payload}


def _render_human(run: CurationRun) -> str:
    summary = run.summary
    lines = [
        f"Preference records: {summary['preference_records']}",
        f"Impure: {summary['impure_pairs']}",
        f"State-divergent (same_state=false): {summary['state_divergent_pairs']}",
        "Proposal-divergent (same_proposed_action=false): "
        f"{summary['proposed_action_divergent_pairs']}",
        f"Proposal-divergent only: {summary['proposed_action_only_divergent_pairs']}",
        f"Retained: {summary['retained_pairs']}",
        f"Excluded: {summary['excluded_pairs']}",
        f"Leftover mill (quarantined): {summary['leftover_mill_records']}",
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

    audit = subparsers.add_parser(
        "audit", help="list impure pairs with reason codes without writing"
    )
    audit.add_argument("source", type=Path)
    audit_format = audit.add_mutually_exclusive_group()
    audit_format.add_argument(
        "--json", action="store_true", help="emit the audit document as JSON"
    )
    audit_format.add_argument(
        "--markdown", action="store_true", help="emit the published Markdown tables"
    )
    audit.add_argument(
        "--expect",
        type=Path,
        default=None,
        help="compare against a published audit document and fail on drift",
    )

    reconcile = subparsers.add_parser(
        "reconcile", help="prove two copies of one corpus scan identically"
    )
    reconcile.add_argument("first", type=Path)
    reconcile.add_argument("second", type=Path)
    reconcile.add_argument(
        "--json", action="store_true", help="emit the differences as JSON"
    )

    curate = subparsers.add_parser(
        "curate", help="write retained preferences and manifest"
    )
    curate.add_argument("source", type=Path)
    curate.add_argument("--output", type=Path, required=True)
    curate.add_argument("--manifest", type=Path, required=True)
    return parser.parse_args(argv)


def _run_audit(args: argparse.Namespace, run: CurationRun) -> int:
    audit = build_audit(run)
    if args.markdown:
        print(render_audit_markdown(audit))
    elif args.json:
        print(json.dumps(audit, indent=2, sort_keys=True, ensure_ascii=False))
    else:
        summary = audit["summary"]
        print(
            f"Preference pairs: {summary['preference_pairs']}\n"
            f"Impure pairs: {summary['impure_pairs']} "
            f"(state {summary['state_divergent_pairs']}, "
            f"proposal {summary['proposed_action_divergent_pairs']}, "
            f"proposal only {summary['proposed_action_only_divergent_pairs']})\n"
            f"Curated keep: {summary['curated_retained_pairs']} "
            f"at {summary['retained_context_purity_pct']:.1f}% same-context purity"
        )
        for pair in audit["impure_pairs"]:
            location = f"{pair['source_path']}:{pair['source_line']}"
            identifier = pair["record_id"] or "<no-id>"
            fields = ",".join(pair["divergent_context_fields"]) or "<none>"
            reasons = ",".join(pair["reason_codes"])
            print(
                f"- {location} {identifier}: {pair['action']} "
                f"[{fields}] [{reasons}]"
            )
    if args.expect is None:
        return 0
    try:
        expected = json.loads(args.expect.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PreferenceCurationError(f"{args.expect}: invalid JSON: {exc}") from exc
    differences = audit_differences(expected, audit)
    if not differences:
        return 0
    print(f"audit drift against {args.expect}:", file=sys.stderr)
    for difference in differences:
        print(f"- {difference}", file=sys.stderr)
    return 1


def _run_reconcile(args: argparse.Namespace) -> int:
    differences = reconcile_runs(
        curate_source(args.first), curate_source(args.second)
    )
    total = sum(len(values) for values in differences.values())
    if args.json:
        print(
            json.dumps(
                {"differences": differences, "difference_count": total},
                indent=2,
                sort_keys=True,
                ensure_ascii=False,
            )
        )
    elif not total:
        print(f"{args.first} and {args.second} scan identically")
    else:
        print(f"{total} difference(s) between {args.first} and {args.second}")
        for label in sorted(differences):
            for difference in differences[label]:
                print(f"- {label}: {difference}")
    return 0 if not total else 1


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.command == "reconcile":
            return _run_reconcile(args)
        run = curate_source(args.source)
        if args.command == "audit":
            return _run_audit(args, run)
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
