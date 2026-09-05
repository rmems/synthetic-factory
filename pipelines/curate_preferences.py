#!/usr/bin/env python3
"""Conservatively curate Fable same-state/same-proposal preference pairs.

Scope: this is the Fable ``state``/``proposed_action`` gate, not a universal
preference curator. A pair whose sides are *trajectories* (``chosen.steps`` /
``rejected.steps`` under one shared ``goal``, as in the Grok 4.6 preference
dumps) carries no ``state``/``proposed_action`` to compare. Such pairs are
excluded here as ``PREFERENCE_PAIR_IS_A_TRAJECTORY_PAIR`` -- never coerced
into a fabricated same-state shape -- and belong to
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
import json
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

if __package__:
    from . import leftover_mill
    from .preference_audit import (
        AUDIT_NAME,
        AUDIT_SCHEMA_VERSION,
        build_audit,
        render_audit_markdown,
    )
    from .preference_audit_diff import (
        AUDIT_HEADER_FIELDS,
        AUDIT_PAIR_FIELDS,
        AUDIT_SOURCE_FILE_FIELDS,
        audit_differences,
        parse_expected_audit,
    )
    from .preference_model import (
        ACTION_EXCLUDED,
        ACTION_QUARANTINED,
        ACTION_REPAIRED,
        ACTION_RETAINED,
        CLASSIFICATION_TRAJECTORY_PAIR,
        RAW_OUTPUT_ROOT,
        REASON_TRAJECTORY_PAIR,
        REPOSITORY_ROOT,
        TRANSFORM_NAME,
        TRANSFORM_VERSION,
        CurationDecision,
        CurationRun,
        PreferenceCurationError,
        canonical_json,
        is_canonicalizable as _is_canonicalizable,
        sha256_hex as _sha256,
    )
    from .preference_record import (
        context_field_agreement,
        context_is_pure,
        curate_preference_record,
    )
    from .preference_reconcile import (
        RECONCILE_COVERAGE_KEYS,
        RECONCILE_DECISION_FIELDS,
        RECONCILE_PAYLOAD_FIELDS,
        reconcile_runs,
    )
    from .preference_writer import write_run
else:
    _PIPELINES = Path(__file__).resolve().parent
    if str(_PIPELINES) not in sys.path:
        sys.path.insert(0, str(_PIPELINES))
    import leftover_mill
    from preference_audit import (
        AUDIT_NAME,
        AUDIT_SCHEMA_VERSION,
        build_audit,
        render_audit_markdown,
    )
    from preference_audit_diff import (
        AUDIT_HEADER_FIELDS,
        AUDIT_PAIR_FIELDS,
        AUDIT_SOURCE_FILE_FIELDS,
        audit_differences,
        parse_expected_audit,
    )
    from preference_model import (
        ACTION_EXCLUDED,
        ACTION_QUARANTINED,
        ACTION_REPAIRED,
        ACTION_RETAINED,
        CLASSIFICATION_TRAJECTORY_PAIR,
        RAW_OUTPUT_ROOT,
        REASON_TRAJECTORY_PAIR,
        REPOSITORY_ROOT,
        TRANSFORM_NAME,
        TRANSFORM_VERSION,
        CurationDecision,
        CurationRun,
        PreferenceCurationError,
        canonical_json,
        is_canonicalizable as _is_canonicalizable,
        sha256_hex as _sha256,
    )
    from preference_record import (
        context_field_agreement,
        context_is_pure,
        curate_preference_record,
    )
    from preference_reconcile import (
        RECONCILE_COVERAGE_KEYS,
        RECONCILE_DECISION_FIELDS,
        RECONCILE_PAYLOAD_FIELDS,
        reconcile_runs,
    )
    from preference_writer import write_run

# This module stays the one public entry point for the preference lane: the
# curation decision, the corpus scan, the writer, the audit, and the
# reconciler are all reachable as ``curate_preferences.<name>`` exactly as
# before they were split into the sibling modules imported above. ``__all__``
# is that promise written down, so a name moving house again is a test
# failure rather than a silent break for an existing caller.
__all__ = [
    "ACTION_EXCLUDED",
    "ACTION_QUARANTINED",
    "ACTION_REPAIRED",
    "ACTION_RETAINED",
    "AUDIT_HEADER_FIELDS",
    "AUDIT_NAME",
    "AUDIT_PAIR_FIELDS",
    "AUDIT_SCHEMA_VERSION",
    "AUDIT_SOURCE_FILE_FIELDS",
    "CLASSIFICATION_TRAJECTORY_PAIR",
    "REASON_TRAJECTORY_PAIR",
    "CurationDecision",
    "CurationRun",
    "PreferenceCurationError",
    "RAW_OUTPUT_ROOT",
    "RECONCILE_COVERAGE_KEYS",
    "RECONCILE_DECISION_FIELDS",
    "RECONCILE_PAYLOAD_FIELDS",
    "REPOSITORY_ROOT",
    "TRANSFORM_NAME",
    "TRANSFORM_VERSION",
    "audit_differences",
    "build_audit",
    "canonical_json",
    "parse_expected_audit",
    "context_field_agreement",
    "context_is_pure",
    "curate_preference_record",
    "curate_source",
    "main",
    "parse_args",
    "reconcile_runs",
    "render_audit_markdown",
    "write_run",
]



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


def _is_preference_candidate(record: Any) -> bool:
    return isinstance(record, dict) and any(
        key in record for key in ("chosen", "rejected", "reward_delta")
    )


def _one_source_file(source: Path) -> tuple[Path, ...]:
    if source.suffix != ".jsonl":
        raise PreferenceCurationError(f"source file must be JSONL: {source}")
    return (source,)


def _source_files_under(source: Path) -> tuple[Path, ...]:
    files = tuple(sorted(source.rglob("*.jsonl")))
    if not files:
        raise PreferenceCurationError(f"no JSONL files under source: {source}")
    return files


def _source_files(source: Path) -> tuple[Path, ...]:
    if source.is_file():
        return _one_source_file(source)
    if source.is_dir():
        return _source_files_under(source)
    raise PreferenceCurationError(f"source does not exist: {source}")


def _relative_source_path(source: Path, path: Path) -> str:
    if source.is_dir():
        return path.relative_to(source).as_posix()
    return path.name


def _skipped_manifest_entry(
    line: _SourceLine, record: Any, mill_kind: str
) -> dict[str, Any]:
    """Return a manifest row for a quarantined leftover-mill record."""

    return {
        "source_path": line.relative_path,
        "source_line": line.number,
        "source_sha256": _sha256(line.payload),
        "source_file_sha256": line.file_sha256,
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

    if same is True:
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
                _skipped_manifest_entry(line, record, mill_kind)
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
        source_id = entry["source_record_id"]
        record_id = "<no-id>" if source_id is None else source_id
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
        record_id = pair["record_id"]
        identifier = "<no-id>" if record_id is None else record_id
        fields = ",".join(pair["divergent_context_fields"]) or "<none>"
        reasons = ",".join(pair["reason_codes"])
        print(f"- {location} {identifier}: {pair['action']} [{fields}] [{reasons}]")


def _report_audit_drift(expect: Path, audit: dict[str, Any]) -> int:
    """Fail closed when this scan has drifted from a published audit."""

    try:
        expected = parse_expected_audit(expect.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PreferenceCurationError(f"{expect}: invalid JSON: {exc}") from exc
    except ValueError as exc:
        # JSONDecodeError is itself a ValueError, so this only sees the
        # repeated-member refusal above.
        raise PreferenceCurationError(f"{expect}: {exc}") from exc
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
