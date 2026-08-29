#!/usr/bin/env python3
"""Conservatively curate Fable same-state/same-proposal preference pairs.

Scope: this is the Fable ``state``/``proposed_action`` gate, not a universal
preference curator. A pair whose sides are *trajectories* (``chosen.steps`` /
``rejected.steps`` under one shared ``goal``, as in the Grok 4.6 preference
dumps) carries no ``state``/``proposed_action`` to compare. Such pairs are
excluded here as ``PREFERENCE_PAIR_IS_A_TRAJECTORY_PAIR`` — never coerced into
a fabricated same-state shape — and belong to
``pipelines/curate_trajectory_preferences.py`` (see
``docs/trajectory-preference-gate.md``).

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

Writing anywhere under ``outputs/raw/`` is refused: raw runs are immutable
evidence, and that includes adding new files beside them.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import sys
from collections import Counter
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

import leftover_mill  # noqa: E402

try:
    from pipelines.raw_tree_guard import is_under_raw as _guard_is_under_raw
except ImportError:  # python3 pipelines/curate_preferences.py
    from raw_tree_guard import is_under_raw as _guard_is_under_raw


TRANSFORM_NAME = "same-context-preference-curation"
TRANSFORM_VERSION = "1.3.0"
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
RAW_OUTPUT_ROOT = REPOSITORY_ROOT / "outputs" / "raw"

AUDIT_NAME = "same-context-preference-audit"
AUDIT_SCHEMA_VERSION = "1.1.0"

REASON_TRAJECTORY_PAIR = "PREFERENCE_PAIR_IS_A_TRAJECTORY_PAIR"
CLASSIFICATION_TRAJECTORY_PAIR = "trajectory_pair_out_of_scope"

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
    source_files: tuple[dict[str, str], ...] = ()


@dataclass
class _ScanState:
    records: list[dict[str, Any]]
    manifest: list[dict[str, Any]]
    actions: Counter[str]
    classifications: Counter[str]
    reasons: Counter[str]
    skipped_non_preferences: int = 0
    json_records_seen: int = 0
    # Subset of skipped records whose payload kind names a different
    # generation mill. Tracked separately so a preference yield can never
    # quietly absorb them into a pair denominator.
    leftover_mill_kinds: Counter[str] = field(default_factory=Counter)
    # Per-field source-side context agreement, tallied by ``_agreement_labels``.
    agreement: Counter[str] = field(default_factory=Counter)
    # Inventory of the source files this scan actually read, so a published
    # audit can be bound to the exact bytes behind it.
    source_files: list[dict[str, str]] = field(default_factory=list)
    # Pairs that must not reach ``round_txn.py publish``: every impure pair
    # plus every pair excluded for a non-context defect. Tracked per pair
    # because the two sets overlap and neither counter alone covers both.
    unpublishable_pairs: int = 0


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


def _is_under_raw(path: Path) -> bool:
    """Whether ``path`` names or aliases the repository's raw output tree."""

    return _guard_is_under_raw(path, RAW_OUTPUT_ROOT)


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
        isinstance(side.get(field_name), dict)
        for side in (chosen, rejected)
        for field_name in ("state", "proposed_action")
    ):
        return None
    return chosen, rejected


def _is_trajectory_pair(record: dict[str, Any]) -> bool:
    """Whether both sides are step trajectories rather than same-state sides.

    Trajectory pairs are curated by ``curate_trajectory_preferences.py``; this
    predicate exists only so their exclusion here is named honestly.
    """

    sides = (record.get("chosen"), record.get("rejected"))
    return all(isinstance(side, dict) and isinstance(side.get("steps"), list) for side in sides)


def context_is_pure(record: dict[str, Any]) -> bool:
    """Whether a preference record has canonical same-state/same-proposal context."""

    context = _preference_context(record)
    if context is None:
        return False
    chosen, rejected = context
    try:
        return all(
            canonical_json(chosen[field_name]) == canonical_json(rejected[field_name])
            for field_name in ("state", "proposed_action")
        )
    except (UnicodeEncodeError, ValueError, TypeError):
        return False


def _field_agreement(record: Any, field_name: str) -> bool | None:
    """Measure one context field without depending on the other field."""

    if not isinstance(record, dict):
        return None
    chosen = record.get("chosen")
    rejected = record.get("rejected")
    if not isinstance(chosen, dict) or not isinstance(rejected, dict):
        return None
    chosen_value = chosen.get(field_name)
    rejected_value = rejected.get(field_name)
    if not isinstance(chosen_value, dict) or not isinstance(rejected_value, dict):
        return None
    try:
        return canonical_json(chosen_value) == canonical_json(rejected_value)
    except (UnicodeEncodeError, ValueError, TypeError):
        return None


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

    return (
        _field_agreement(record, "state"),
        _field_agreement(record, "proposed_action"),
    )


def _all_context_diffs(chosen: dict[str, Any], rejected: dict[str, Any]) -> tuple[str, ...]:
    paths: list[str] = []
    for field_name in ("state", "proposed_action"):
        paths.extend(
            _context_diff_paths(chosen[field_name], rejected[field_name], field_name)
        )
    return tuple(paths)


def _identity_annotation_reference(
    chosen_value: dict[str, Any],
    rejected_value: dict[str, Any],
    field_name: str,
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
        expected_prefix = f"IDENTICAL to {reference_name}.{field_name}"
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

    for field_name in ("state", "proposed_action"):
        if canonical_json(chosen[field_name]) == canonical_json(rejected[field_name]):
            continue
        reference = _identity_annotation_reference(
            chosen[field_name], rejected[field_name], field_name
        )
        if reference is None:
            return None
        exact_value, attester_name, reference_name = reference
        repaired[attester_name][field_name] = copy.deepcopy(exact_value)
        repaired[reference_name][field_name] = copy.deepcopy(exact_value)
        changed.append(f"{attester_name}.{field_name}")

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
        if not isinstance(attester_source, str) or not isinstance(reference_source, str):
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


def _absent_context_decision(
    record: dict[str, Any], same_state: Any, same_proposed_action: Any
) -> CurationDecision:
    """Name a pair that carries no same-state context, by the lane that owns it."""

    if _is_trajectory_pair(record):
        # A shared-goal trajectory pair is a different schema, not a
        # malformed same-state pair. Naming that keeps a 0% same-state
        # yield readable and stops anyone from inventing state here.
        return CurationDecision(
            action=ACTION_EXCLUDED,
            classification=CLASSIFICATION_TRAJECTORY_PAIR,
            reason_codes=(REASON_TRAJECTORY_PAIR,),
            record=None,
            context_diff_paths=(),
        )
    return CurationDecision(
        action=ACTION_EXCLUDED,
        classification="malformed_preference_context",
        reason_codes=("PREFERENCE_CONTEXT_MISSING_OR_INVALID",),
        record=None,
        context_diff_paths=(),
        same_state=same_state,
        same_proposed_action=same_proposed_action,
    )


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
    same_state, same_proposed_action = context_field_agreement(record)
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
            same_state=same_state,
            same_proposed_action=same_proposed_action,
        )
    context = _preference_context(record)
    if context is None:
        return _absent_context_decision(record, same_state, same_proposed_action)

    chosen, rejected = context
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
        # Same canonicalizability guard the preference rows use. record_id()
        # keeps its meta.id fallback; only a value the destination cannot
        # encode is dropped.
        "source_record_id": _canonicalizable_manifest_id(
            leftover_mill.record_id(record)
        ),
        "transform": {"name": TRANSFORM_NAME, "version": TRANSFORM_VERSION},
        "action": ACTION_QUARANTINED,
        "classification": f"leftover_mill_{mill_kind}",
        "reason_codes": [leftover_mill.REASON_KIND_MIX],
        "context_diff_paths": [],
        "changed_context_fields": [],
        "output_id": None,
        "output_sha256": None,
    }


def _field_agreement_label(field_name: str, same: bool | None) -> str:
    """The per-field bucket one context field falls in."""

    if same:
        return f"same_{field_name}"
    if same is False:
        return f"{field_name}_divergent"
    return f"{field_name}_undetermined"


def _pair_agreement_bucket(
    same_state: bool | None, same_proposed_action: bool | None
) -> str | None:
    """The one disjoint pair-level bucket, or ``None`` for a pure pair.

    A pair that agrees on both fields lands in no bucket at all: the four
    buckets exist to partition the *impure* pairs, and ``_curation_summary``
    sums exactly them.
    """

    if same_state is None or same_proposed_action is None:
        return "undetermined"
    if not same_state and not same_proposed_action:
        return "both_divergent"
    if not same_state:
        return "state_only_divergent"
    if not same_proposed_action:
        return "proposed_action_only_divergent"
    return None


def _agreement_labels(decision: CurationDecision) -> tuple[str, ...]:
    """Return per-field totals plus one disjoint pair-level bucket."""

    labels = [
        _field_agreement_label("state", decision.same_state),
        _field_agreement_label("proposed_action", decision.same_proposed_action),
    ]
    bucket = _pair_agreement_bucket(
        decision.same_state, decision.same_proposed_action
    )
    if bucket is not None:
        labels.append(bucket)
    return tuple(labels)
# The four disjoint context-divergence/comparability buckets that make a pair
# impure. ``_curation_summary`` sums exactly these, and a pair landing in any
# of them is unpublishable no matter which curation action it drew.
_IMPURE_AGREEMENT_LABELS = frozenset(
    {
        "state_only_divergent",
        "proposed_action_only_divergent",
        "both_divergent",
        "undetermined",
    }
)


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


def _canonicalizable_manifest_id(value: Any) -> Any:
    """Drop a manifest identifier the JSONL destination cannot encode.

    ``json.loads`` accepts an escaped lone surrogate, so a source id can be a
    perfectly good Python string that ``write_run`` cannot serialize. Losing
    the id costs nothing an auditor needs: the source reference survives as
    path, line, and hash either way, whereas losing the row would delete the
    evidence that this record was quarantined at all.
    """
    return value if _is_canonicalizable(value) else None


def _manifest_source_id(record: Any) -> Any:
    # An excluded record may itself hold a non-encodable id; the source
    # reference survives as path, line, and hash either way.
    return _canonicalizable_manifest_id(
        record.get("id") if isinstance(record, dict) else None
    )


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
    agreement_labels = _agreement_labels(decision)
    state.agreement.update(agreement_labels)
    if decision.action == ACTION_EXCLUDED or _IMPURE_AGREEMENT_LABELS.intersection(
        agreement_labels
    ):
        state.unpublishable_pairs += 1
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
            "same_state": decision.same_state,
            "same_proposed_action": decision.same_proposed_action,
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
    state.source_files.append(
        {
            "source_file_sha256": file_hash,
            "source_path": relative_path,
        }
    )
    for line_number, raw_line in _jsonl_payload_lines(file_payload):
        line = _SourceLine(relative_path, line_number, raw_line, file_hash)
        state.json_records_seen += 1
        record = _load_jsonl_record(line)
        mill_kind = leftover_mill.kind_mix_kind(record, "preference")
        if mill_kind is not None:
            # A concrete foreign generation kind takes precedence over the
            # loose candidate heuristic. An episode carrying reward_delta,
            # for example, is still an episode and must never enter the
            # preference denominator as a malformed pair.
            state.skipped_non_preferences += 1
            state.leftover_mill_kinds[mill_kind] += 1
            state.manifest.append(
                _skipped_manifest_entry(
                    relative_path, line_number, raw_line, file_hash, record, mill_kind
                )
            )
            continue
        if not _is_preference_candidate(record):
            state.skipped_non_preferences += 1
            continue
        _record_preference(state, line, record)


def _curation_summary(source: Path, state: _ScanState) -> dict[str, Any]:
    preference_records = sum(state.actions.values())
    agreement = state.agreement
    # Curation action and context purity are related but not synonymous.  A
    # pair can have equal, fully comparable context and still be excluded for
    # a non-context defect such as a non-finite reward.  Count only the four
    # disjoint context-divergence/comparability buckets as impure so the public
    # same-context audit remains truthful and balanced.
    impure_pairs = sum(agreement[label] for label in _IMPURE_AGREEMENT_LABELS)
    retained_pairs = state.actions[ACTION_RETAINED] + state.actions[ACTION_REPAIRED]
    # Measured over the records actually emitted rather than asserted as a
    # constant, so the reported purity is evidence and not a restatement of
    # the invariant the loop above enforces.
    pure_outputs = sum(1 for emitted in state.records if context_is_pure(emitted))
    purity_pct = 0.0
    if retained_pairs:
        purity_pct = round(100.0 * pure_outputs / retained_pairs, 1)
    summary = {
        "transform": {"name": TRANSFORM_NAME, "version": TRANSFORM_VERSION},
        "source": str(source),
        "json_records_seen": state.json_records_seen,
        "preference_records": preference_records,
        "skipped_non_preference_records": state.skipped_non_preferences,
        # Subset of the skipped records whose payload kind names a different
        # generation mill. Reported separately so a preference yield can never
        # quietly absorb them into a pair denominator.
        "leftover_mill_records": sum(state.leftover_mill_kinds.values()),
        "leftover_mill_kinds": dict(sorted(state.leftover_mill_kinds.items())),
        "impure_pairs": impure_pairs,
        "retained_pairs": retained_pairs,
        "excluded_pairs": state.actions[ACTION_EXCLUDED],
        # The publication gate total. ``impure_pairs`` counts context
        # divergence only, so a pair whose context is equal and comparable but
        # which still cannot be emitted -- a non-finite ``reward_delta``, say
        # -- is invisible there and would clear a gate reading that field
        # alone. This counts every pair that is impure *or* unemittable, and
        # docs/preference-isolation.md gates ``round_txn.py publish`` on it.
        "unpublishable_pairs": state.unpublishable_pairs,
        # Reconciliation between a state-only Hub audit and this scan: a
        # ``same_state``-only measurement cannot see a pair that holds state
        # constant and diverges on the proposed action.
        "same_state_pairs": agreement["same_state"],
        "state_divergent_pairs": agreement["state_divergent"],
        "state_undetermined_pairs": agreement["state_undetermined"],
        "same_proposed_action_pairs": agreement["same_proposed_action"],
        "proposed_action_divergent_pairs": agreement["proposed_action_divergent"],
        "proposed_action_undetermined_pairs": agreement["proposed_action_undetermined"],
        "state_only_divergent_pairs": agreement["state_only_divergent"],
        "proposed_action_only_divergent_pairs": agreement["proposed_action_only_divergent"],
        "both_context_fields_divergent_pairs": agreement["both_divergent"],
        "context_undetermined_pairs": agreement["undetermined"],
        "out_of_scope_trajectory_pairs": state.classifications[
            CLASSIFICATION_TRAJECTORY_PAIR
        ],
        "actions": dict(sorted(state.actions.items())),
        "classifications": dict(sorted(state.classifications.items())),
        "reason_codes": dict(sorted(state.reasons.items())),
        "retained_context_purity_pct": purity_pct,
    }
    for field_name in ("state", "proposed_action"):
        measured = (
            summary[f"same_{field_name}_pairs"]
            + summary[f"{field_name}_divergent_pairs"]
            + summary[f"{field_name}_undetermined_pairs"]
        )
        if measured != preference_records:
            raise PreferenceCurationError(
                f"internal error: {field_name} agreement does not balance "
                f"({measured} measured, {preference_records} preference records)"
            )
    return summary


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
        tuple(state.source_files),
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


def _open_destination_parent(path: Path) -> int:
    flags = os.O_RDONLY | os.O_DIRECTORY | getattr(os, "O_NOFOLLOW", 0)
    try:
        return os.open(path.parent, flags)
    except OSError as exc:
        raise PreferenceCurationError(
            f"destination parent is not a pinned directory: {path.parent}"
        ) from exc


def _refuse_opened_parent(parent_fd: int, destination: Path) -> None:
    try:
        opened = Path(os.readlink(f"/proc/self/fd/{parent_fd}"))
    except OSError:
        opened = destination.parent
    _refuse_raw_destination(opened, "destination")
    _refuse_raw_destination(opened / destination.name, "destination")


def _create_exclusive_file(path: Path, payload: str, created: list[Path]) -> None:
    parent_fd = _open_destination_parent(path)
    try:
        _refuse_opened_parent(parent_fd, path)
        descriptor = os.open(
            path.name,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL,
            0o644,
            dir_fd=parent_fd,
        )
    finally:
        os.close(parent_fd)
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


def _divergent_context_fields(entry: dict[str, Any]) -> list[str]:
    """Return the canonical context fields that differ across the two sides."""

    fields = []
    if entry.get("same_state") is False:
        fields.append("state")
    if entry.get("same_proposed_action") is False:
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
        if entry["action"] in (ACTION_REPAIRED, ACTION_EXCLUDED)
        and (
            entry["same_state"] is not True
            or entry["same_proposed_action"] is not True
        )
    ]
    balanced = (
        summary["state_only_divergent_pairs"]
        + summary["proposed_action_only_divergent_pairs"]
        + summary["both_context_fields_divergent_pairs"]
        + summary["context_undetermined_pairs"]
    )
    if balanced != summary["impure_pairs"] or len(impure_pairs) != summary["impure_pairs"]:
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
            "state_undetermined_pairs": summary["state_undetermined_pairs"],
            "proposed_action_divergent_pairs": summary["proposed_action_divergent_pairs"],
            "proposed_action_undetermined_pairs": summary["proposed_action_undetermined_pairs"],
            "state_only_divergent_pairs": summary["state_only_divergent_pairs"],
            "proposed_action_only_divergent_pairs": summary["proposed_action_only_divergent_pairs"],
            "both_context_fields_divergent_pairs": summary["both_context_fields_divergent_pairs"],
            "context_undetermined_pairs": summary["context_undetermined_pairs"],
            "curated_retained_pairs": summary["retained_pairs"],
            "curated_repaired_pairs": summary["actions"].get(ACTION_REPAIRED, 0),
            "curated_excluded_pairs": summary["excluded_pairs"],
            "retained_context_purity_pct": summary["retained_context_purity_pct"],
        },
        "source_files": [dict(entry) for entry in run.source_files],
        "impure_pairs": impure_pairs,
    }


def _yes_no(value: bool | None) -> str:
    if value is None:
        return "n/a"
    return "yes" if value else "no"


def _markdown_cell_text(value: Any) -> str:
    """Flatten a source-controlled value into exactly one Markdown table cell.

    ``record_id``, ``source_path`` and the reason codes come from the audited
    JSON rather than from a constrained internal enum. A newline ends the
    table row and a ``|`` opens the next cell -- inside a code span too -- so
    a crafted value could otherwise add columns, inject rows, or visually
    hide a record from the published per-pair evidence.
    """

    text = str(value)
    for control in ("\r\n", "\r", "\n", "\t"):
        text = text.replace(control, " ")
    return text.replace("|", "\\|")


def _markdown_code_cell(value: Any) -> str:
    """Wrap a source-controlled value in a code span it cannot break out of."""

    text = _markdown_cell_text(value)
    # CommonMark closes a code span at the first backtick run matching the
    # opening one, so the fence must be longer than the longest run inside,
    # and a value that starts or ends with a backtick needs the pad space
    # that the reader strips back off.
    longest = max((len(run) for run in re.findall("`+", text)), default=0)
    fence = "`" * (longest + 1)
    pad = " " if text.startswith("`") or text.endswith("`") else ""
    return f"{fence}{pad}{text}{pad}{fence}"


def render_audit_markdown(audit: dict[str, Any]) -> str:
    """Render the audit document as the published Markdown tables."""

    summary = audit["summary"]
    lines = [
        "| Measure | Pairs |",
        "| --- | ---: |",
        f"| Published preference pairs | {summary['preference_pairs']} |",
        f"| `same_state = false` (state diverges) | {summary['state_divergent_pairs']} |",
        "| `same_proposed_action = false` (proposal diverges) | "
        f"{summary['proposed_action_divergent_pairs']} |",
        f"| Impure pairs (either field diverges) | {summary['impure_pairs']} |",
        f"| - state only | {summary['state_only_divergent_pairs']} |",
        f"| - proposed action only | {summary['proposed_action_only_divergent_pairs']} |",
        f"| - both fields | {summary['both_context_fields_divergent_pairs']} |",
        f"| - context not comparable | {summary['context_undetermined_pairs']} |",
        f"| Curated keep (already identical + repaired) | {summary['curated_retained_pairs']} |",
        f"| Curated exclude | {summary['curated_excluded_pairs']} |",
        f"| Curated same-context purity | {summary['retained_context_purity_pct']:.1f}% |",
        "",
        "| Pair | Source | `same_state` | `same_proposed_action` | Curation | Reason codes |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for pair in audit["impure_pairs"]:
        record_id = pair["record_id"]
        identifier = _markdown_code_cell(record_id) if record_id else "_(no record id)_"
        reasons = (
            ", ".join(_markdown_code_cell(code) for code in pair["reason_codes"])
            or "_(none)_"
        )
        location = _markdown_code_cell(
            f"{pair['source_path']}:{pair['source_line']}"
        )
        lines.append(
            f"| {identifier} "
            f"| {location} "
            f"| {_yes_no(pair['same_state'])} "
            f"| {_yes_no(pair['same_proposed_action'])} "
            f"| {_markdown_cell_text(pair['action'])} "
            f"| {reasons} |"
        )
    return "\n".join(lines)


def _location_sort_key(location: tuple[Any, Any]) -> tuple[str, int, str]:
    path_part, line_part = location
    line_number = line_part if isinstance(line_part, int) else 0
    return str(path_part), line_number, str(line_part)


def _pairs_by_location(pairs: Any) -> dict[tuple[Any, Any], dict[str, Any]]:
    located: dict[tuple[Any, Any], dict[str, Any]] = {}
    for pair in pairs if isinstance(pairs, list) else ():
        if isinstance(pair, dict):
            located[(pair.get("source_path"), pair.get("source_line"))] = pair
    return located


def _source_files_by_path(files: Any) -> dict[str, dict[str, Any]]:
    """Key a source-file inventory by its relative path."""

    if not isinstance(files, (list, tuple)):
        return {}
    return {
        entry["source_path"]: entry
        for entry in files
        if isinstance(entry, dict) and isinstance(entry.get("source_path"), str)
    }


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
AUDIT_SOURCE_FILE_FIELDS = ("source_file_sha256",)


def _audit_header_differences(expected: dict[str, Any], actual: dict[str, Any]) -> list[str]:
    """Identity fields that must match before any count is comparable."""

    return [
        f"{key}: expected {expected.get(key)!r}, got {actual.get(key)!r}"
        for key in ("schema_version", "audit", "transform")
        if expected.get(key) != actual.get(key)
    ]


def _audit_summary_differences(expected: dict[str, Any], actual: dict[str, Any]) -> list[str]:
    """Every summary counter present on either side that disagrees."""

    expected_summary = expected.get("summary")
    expected_summary = expected_summary if isinstance(expected_summary, dict) else {}
    return [
        f"summary.{key}: expected {expected_summary.get(key)!r}, "
        f"got {actual['summary'].get(key)!r}"
        for key in sorted(set(expected_summary) | set(actual["summary"]))
        if expected_summary.get(key) != actual["summary"].get(key)
    ]


def _audit_source_file_differences(
    expected: dict[str, Any], actual: dict[str, Any]
) -> list[str]:
    """Source-file inventory drift, by path then by field."""

    expected_files = _source_files_by_path(expected.get("source_files"))
    actual_files = _source_files_by_path(actual.get("source_files"))
    differences = [
        f"{source_path}: audited source file is absent from this scan"
        for source_path in sorted(set(expected_files) - set(actual_files))
    ]
    differences.extend(
        f"{source_path}: source file is absent from the audit"
        for source_path in sorted(set(actual_files) - set(expected_files))
    )
    for source_path in sorted(set(expected_files) & set(actual_files)):
        for field_name in AUDIT_SOURCE_FILE_FIELDS:
            want = expected_files[source_path].get(field_name)
            got = actual_files[source_path].get(field_name)
            if want != got:
                differences.append(
                    f"{source_path}: {field_name}: expected {want!r}, got {got!r}"
                )
    return differences


def _audit_impure_pair_differences(
    expected: dict[str, Any], actual: dict[str, Any]
) -> list[str]:
    """Per-pair drift, by source location then by field."""

    expected_pairs = _pairs_by_location(expected.get("impure_pairs"))
    actual_pairs = _pairs_by_location(actual["impure_pairs"])
    differences = [
        f"{location[0]}:{location[1]}: audited impure pair is absent from this scan"
        for location in sorted(
            set(expected_pairs) - set(actual_pairs), key=_location_sort_key
        )
    ]
    differences.extend(
        f"{location[0]}:{location[1]}: impure pair is absent from the audit"
        for location in sorted(
            set(actual_pairs) - set(expected_pairs), key=_location_sort_key
        )
    )
    for location in sorted(
        set(expected_pairs) & set(actual_pairs), key=_location_sort_key
    ):
        for field_name in AUDIT_PAIR_FIELDS:
            want = expected_pairs[location].get(field_name)
            got = actual_pairs[location].get(field_name)
            if want != got:
                differences.append(
                    f"{location[0]}:{location[1]}: {field_name}: "
                    f"expected {want!r}, got {got!r}"
                )
    return differences


def audit_differences(expected: Any, actual: dict[str, Any]) -> list[str]:
    """Return every way ``actual`` departs from a previously published audit."""

    if not isinstance(expected, dict):
        return ["expected audit document is not a JSON object"]
    return [
        *_audit_header_differences(expected, actual),
        *_audit_summary_differences(expected, actual),
        *_audit_source_file_differences(expected, actual),
        *_audit_impure_pair_differences(expected, actual),
    ]


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


def _manifest_by_location(run: CurationRun) -> dict[tuple[str, int], dict[str, Any]]:
    """One scan's manifest entries keyed by source path and line."""

    return {
        (entry["source_path"], entry["source_line"]): entry for entry in run.manifest
    }


def _reconcile_summary_coverage(first: CurationRun, second: CurationRun) -> list[str]:
    """Denominator counters that disagree between two scans of one corpus."""

    return [
        f"summary.{key}: first {first.summary[key]}, second {second.summary[key]}"
        for key in RECONCILE_COVERAGE_KEYS
        if first.summary[key] != second.summary[key]
    ]


def _reconcile_source_files(
    first: CurationRun, second: CurationRun
) -> tuple[list[str], list[str]]:
    """Source-file inventory drift, split into coverage and payload."""

    first_files = _source_files_by_path(first.source_files)
    second_files = _source_files_by_path(second.source_files)
    coverage = [
        f"{source_path}: file present in the first source only"
        for source_path in sorted(set(first_files) - set(second_files))
    ]
    coverage.extend(
        f"{source_path}: file present in the second source only"
        for source_path in sorted(set(second_files) - set(first_files))
    )

    payload: list[str] = []
    for source_path in sorted(set(first_files) & set(second_files)):
        for field_name in AUDIT_SOURCE_FILE_FIELDS:
            first_value = first_files[source_path].get(field_name)
            second_value = second_files[source_path].get(field_name)
            if first_value != second_value:
                payload.append(
                    f"{source_path}: {field_name}: "
                    f"first {first_value!r}, second {second_value!r}"
                )
    return coverage, payload


def _reconcile_manifest_entries(
    first_entries: dict[tuple[str, int], dict[str, Any]],
    second_entries: dict[tuple[str, int], dict[str, Any]],
) -> tuple[list[str], list[str], list[str]]:
    """Per-record drift, split into coverage, decisions, and payload."""

    coverage = [
        f"{location[0]}:{location[1]}: present in the first source only"
        for location in sorted(
            set(first_entries) - set(second_entries), key=_location_sort_key
        )
    ]
    coverage.extend(
        f"{location[0]}:{location[1]}: present in the second source only"
        for location in sorted(
            set(second_entries) - set(first_entries), key=_location_sort_key
        )
    )

    decisions: list[str] = []
    payload: list[str] = []
    for location in sorted(
        set(first_entries) & set(second_entries), key=_location_sort_key
    ):
        for field_name, bucket in (
            *((name, decisions) for name in RECONCILE_DECISION_FIELDS),
            *((name, payload) for name in RECONCILE_PAYLOAD_FIELDS),
        ):
            first_value = first_entries[location].get(field_name)
            second_value = second_entries[location].get(field_name)
            if first_value != second_value:
                bucket.append(
                    f"{location[0]}:{location[1]}: {field_name}: "
                    f"first {first_value!r}, second {second_value!r}"
                )
    return coverage, decisions, payload


def reconcile_runs(first: CurationRun, second: CurationRun) -> dict[str, list[str]]:
    """Compare two scans of one corpus, keyed by source path and line.

    ``coverage`` reports records one copy has and the other does not,
    ``decisions`` reports curation verdicts that disagree, and ``payload``
    reports agreeing verdicts reached from different source bytes.
    """

    file_coverage, file_payload = _reconcile_source_files(first, second)
    entry_coverage, decisions, entry_payload = _reconcile_manifest_entries(
        _manifest_by_location(first), _manifest_by_location(second)
    )
    return {
        "coverage": [
            *_reconcile_summary_coverage(first, second),
            *file_coverage,
            *entry_coverage,
        ],
        "decisions": decisions,
        "payload": [*file_payload, *entry_payload],
    }


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
    scan.add_argument("--json", action="store_true", help="emit summary and decisions as JSON")

    audit = subparsers.add_parser(
        "audit", help="list impure pairs with reason codes without writing"
    )
    audit.add_argument("source", type=Path)
    audit_format = audit.add_mutually_exclusive_group()
    audit_format.add_argument("--json", action="store_true", help="emit the audit document as JSON")
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
    reconcile.add_argument("--json", action="store_true", help="emit the differences as JSON")

    curate = subparsers.add_parser("curate", help="write retained preferences and manifest")
    curate.add_argument("source", type=Path)
    curate.add_argument("--output", type=Path, required=True)
    curate.add_argument("--manifest", type=Path, required=True)
    return parser.parse_args(argv)


def _print_audit_text(audit: dict[str, Any]) -> None:
    """The default human-readable audit rendering."""

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
        print(f"- {location} {identifier}: {pair['action']} [{fields}] [{reasons}]")


def _report_audit_drift(expect: Path, audit: dict[str, Any]) -> int:
    """Fail closed when this scan has drifted from a published audit."""

    try:
        expected = json.loads(expect.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PreferenceCurationError(f"{expect}: invalid JSON: {exc}") from exc
    differences = audit_differences(expected, audit)
    if not differences:
        return 0
    print(f"audit drift against {expect}:", file=sys.stderr)
    for difference in differences:
        print(f"- {difference}", file=sys.stderr)
    return 1


def _run_audit(args: argparse.Namespace, run: CurationRun) -> int:
    audit = build_audit(run)
    if args.markdown:
        print(render_audit_markdown(audit))
    elif args.json:
        print(json.dumps(audit, indent=2, sort_keys=True, ensure_ascii=False))
    else:
        _print_audit_text(audit)
    if args.expect is None:
        return 0
    return _report_audit_drift(args.expect, audit)


def _run_reconcile(args: argparse.Namespace) -> int:
    differences = reconcile_runs(curate_source(args.first), curate_source(args.second))
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
