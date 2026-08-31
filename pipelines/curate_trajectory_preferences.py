#!/usr/bin/env python3
"""Curate trajectory-pair preferences (shared-goal, shared-prefix DPO).

``curate_preferences.py`` is the Fable *same-state* gate: it requires
``chosen``/``rejected`` to carry dict ``state`` and ``proposed_action`` and it
compares those two subtrees. Grok 4.6 preference dumps do not use that schema.
Their sides are trajectories — ``steps`` / ``outcome`` / ``reward`` under one
top-level ``goal`` — so the same-state gate reports
``PREFERENCE_CONTEXT_MISSING_OR_INVALID`` for every pair and yields nothing.

This module is the missing lane. It never invents ``state`` or
``proposed_action``; it gates the contrast that trajectory pairs actually
carry:

* both sides describe one problem (shared normalized ``goal``),
* the trajectories share a leading step prefix (> 0 steps),
* the trajectories are not identical,
* ``outcome`` diverges,
* ``reward`` diverges.

Pairs that already satisfy the Fable schema are *skipped*, not judged here, so
the two lanes never share a denominator. Records that are not preference pairs
at all (for example leftover mill episodes) are skipped and counted.

This file owns the source scan and the command line. The gate itself lives in
``trajectory_pair_vocabulary`` (reason codes and policy),
``trajectory_pair_shape`` (what a well-formed pair is), ``trajectory_pair_gate``
(which pairs carry contrast), and ``trajectory_pair_curation`` (repairs and the
per-record decision). Every public name from those modules is re-exported here,
so importers keep using ``curate_trajectory_preferences`` alone.

Read-only corpus inspection::

    python3 pipelines/curate_trajectory_preferences.py scan <source> --json

Write a new JSONL plus manifest (both destinations must be absent)::

    python3 pipelines/curate_trajectory_preferences.py curate <source> \
      --output <new-pairs.jsonl> --manifest <new-manifest.jsonl>

Sources are read-only. Destinations under ``outputs/raw/`` are refused: raw
evidence is never rewritten, and no curated view is written back over a Hub
mirror.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

from check_records import reject_json_constant
from curate_agentic import (
    REASON_GOAL_DIVERGES,
    REASON_GOAL_MISSING,
    REASON_GOAL_NOT_TEXT,
    REASON_THOUGHT_REMOVED,
    canonical_json,
    prefix_overlap,
    shared_preference_goal,
    strip_hidden_thought_keys,
)
from curate_preferences import PreferenceCurationError, write_run
from validate_run import THALAMIC_CORE_KEYS, check_episode
from trajectory_pair_curation import (
    changed_top_level_fields,
    curate_trajectory_pair,
    normalize_goal_whitespace,
)
from trajectory_pair_gate import (
    first_step_differs_by_branch_label_only,
    gate_failures,
    pair_passes_gate,
    preference_direction_failures,
    side_field_failures,
)
from trajectory_pair_shape import (
    classify_pair_schema,
    is_pair_candidate,
    is_same_state_pair,
    pair_envelope_validation_errors,
    side_episode_validation_errors,
    step_number_errors,
    steps_of,
)
from trajectory_pair_vocabulary import (
    ACTION_EXCLUDED,
    ACTION_REPAIRED,
    ACTION_RETAINED,
    ACTION_SKIPPED,
    BRANCH_LABEL_MASK,
    BRANCH_LABEL_RE,
    DEFAULT_POLICY,
    GOAL_LOCATIONS,
    GOAL_REASONS,
    PAIR_SIDES,
    REASON_BRANCH_LABEL_ONLY,
    REASON_GATE_PASSED,
    REASON_GOAL_WHITESPACE_NORMALIZED,
    REASON_NOT_A_PAIR,
    REASON_OUTCOME_INVALID,
    REASON_OUTCOME_MISSING,
    REASON_OUTCOME_NOT_DIVERGENT,
    REASON_PAIR_ENVELOPE_INVALID,
    REASON_PAIR_IDENTICAL,
    REASON_PREFERENCE_DIRECTION_INVALID,
    REASON_PREFIX_ABSENT,
    REASON_RECORD_NOT_OBJECT,
    REASON_REWARD_INVALID,
    REASON_REWARD_MISSING,
    REASON_REWARD_NOT_DIVERGENT,
    REASON_SAME_STATE_SCHEMA,
    REASON_SIDE_EPISODE_INVALID,
    REASON_SIDES_NOT_OBJECTS,
    REASON_STEPS_EMPTY,
    REASON_STEPS_INVALID,
    SAME_STATE_FIELDS,
    TRANSFORM_NAME,
    TRANSFORM_VERSION,
    CurationRun,
    GatePolicy,
    TrajectoryCurationError,
    TrajectoryDecision,
    is_finite_json_number,
    parse_finite_json_float,
)

__all__ = [
    "ACTION_EXCLUDED",
    "ACTION_REPAIRED",
    "ACTION_RETAINED",
    "ACTION_SKIPPED",
    "BRANCH_LABEL_MASK",
    "BRANCH_LABEL_RE",
    "DEFAULT_POLICY",
    "GOAL_LOCATIONS",
    "GOAL_REASONS",
    "PAIR_SIDES",
    "REASON_BRANCH_LABEL_ONLY",
    "REASON_GATE_PASSED",
    "REASON_GOAL_DIVERGES",
    "REASON_GOAL_MISSING",
    "REASON_GOAL_NOT_TEXT",
    "REASON_GOAL_WHITESPACE_NORMALIZED",
    "REASON_NOT_A_PAIR",
    "REASON_OUTCOME_INVALID",
    "REASON_OUTCOME_MISSING",
    "REASON_OUTCOME_NOT_DIVERGENT",
    "REASON_PAIR_ENVELOPE_INVALID",
    "REASON_PAIR_IDENTICAL",
    "REASON_PREFERENCE_DIRECTION_INVALID",
    "REASON_PREFIX_ABSENT",
    "REASON_RECORD_NOT_OBJECT",
    "REASON_REWARD_INVALID",
    "REASON_REWARD_MISSING",
    "REASON_REWARD_NOT_DIVERGENT",
    "REASON_SAME_STATE_SCHEMA",
    "REASON_SIDE_EPISODE_INVALID",
    "REASON_SIDES_NOT_OBJECTS",
    "REASON_STEPS_EMPTY",
    "REASON_STEPS_INVALID",
    "REASON_THOUGHT_REMOVED",
    "SAME_STATE_FIELDS",
    "THALAMIC_CORE_KEYS",
    "TRANSFORM_NAME",
    "TRANSFORM_VERSION",
    "CurationRun",
    "GatePolicy",
    "TrajectoryCurationError",
    "TrajectoryDecision",
    "canonical_json",
    "changed_top_level_fields",
    "check_episode",
    "classify_pair_schema",
    "curate_source",
    "curate_trajectory_pair",
    "first_step_differs_by_branch_label_only",
    "gate_failures",
    "is_finite_json_number",
    "is_pair_candidate",
    "is_same_state_pair",
    "main",
    "normalize_goal_whitespace",
    "pair_envelope_validation_errors",
    "pair_passes_gate",
    "parse_args",
    "parse_finite_json_float",
    "prefix_overlap",
    "preference_direction_failures",
    "sha256_hex",
    "shared_preference_goal",
    "side_episode_validation_errors",
    "side_field_failures",
    "step_number_errors",
    "steps_of",
    "strip_hidden_thought_keys",
]


@dataclass(frozen=True)
class SourceLine:
    """One non-blank JSONL line and the provenance needed to record it."""

    relative_path: str
    line_number: int
    raw_line: bytes
    file_sha256: str

    @property
    def location(self) -> str:
        return f"{self.relative_path}:{self.line_number}"


def sha256_hex(payload: bytes) -> str:
    """Hex SHA-256 of ``payload``."""

    return hashlib.sha256(payload).hexdigest()


def _single_source_file(source: Path) -> tuple[Path, ...]:
    if source.suffix != ".jsonl":
        raise TrajectoryCurationError(f"source file must be JSONL: {source}")
    return (source,)


def _source_tree_files(source: Path) -> tuple[Path, ...]:
    files = tuple(sorted(source.rglob("*.jsonl")))
    if not files:
        raise TrajectoryCurationError(f"no JSONL files under source: {source}")
    return files


def _source_files(source: Path) -> tuple[Path, ...]:
    if source.is_file():
        return _single_source_file(source)
    if source.is_dir():
        return _source_tree_files(source)
    raise TrajectoryCurationError(f"source does not exist: {source}")


def _relative_source_path(source: Path, path: Path) -> str:
    if source.is_dir():
        return path.relative_to(source).as_posix()
    return path.name


def _source_lines(source: Path) -> Iterator[SourceLine]:
    """Yield every non-blank JSONL line under ``source`` in a stable order."""

    for path in _source_files(source):
        payload = path.read_bytes()
        file_hash = sha256_hex(payload)
        relative_path = _relative_source_path(source, path)
        for line_number, raw_line in enumerate(payload.splitlines(), 1):
            if raw_line.strip():
                yield SourceLine(relative_path, line_number, raw_line, file_hash)


def _decode_line(line: SourceLine) -> str:
    try:
        return line.raw_line.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise TrajectoryCurationError(f"{line.location}: invalid UTF-8: {exc}") from exc


def _load_record(line: SourceLine) -> Any:
    """Parse one JSONL line, refusing every non-finite number spelling."""

    try:
        # ``parse_constant`` refuses explicit NaN/Infinity tokens.
        # ``parse_float`` additionally refuses finite-looking JSON numbers such
        # as ``1e999`` that overflow Python's float and would otherwise
        # reappear as an invalid Infinity token.
        return json.loads(
            _decode_line(line),
            parse_constant=reject_json_constant,
            parse_float=parse_finite_json_float,
        )
    except (json.JSONDecodeError, ValueError) as exc:
        raise TrajectoryCurationError(f"{line.location}: invalid JSON: {exc}") from exc


def _emitted_line(
    decision: TrajectoryDecision, location: str, policy: GatePolicy
) -> bytes | None:
    """Canonical bytes for an emitted record, re-checked against the gate."""

    if decision.record is None:
        return None
    if not pair_passes_gate(decision.record, policy):
        raise TrajectoryCurationError(
            f"internal error: emitted a pair that fails the gate at {location}"
        )
    return canonical_json(decision.record).encode("utf-8")


def _manifest_entry(
    decision: TrajectoryDecision,
    record: Any,
    line: SourceLine,
    output_line: bytes | None,
) -> dict[str, Any]:
    """One deterministic manifest row for a single source record."""

    return {
        "source_path": line.relative_path,
        "source_line": line.line_number,
        # Hash excludes the JSONL line terminator by definition.
        "source_sha256": sha256_hex(line.raw_line),
        "source_file_sha256": line.file_sha256,
        "source_record_id": record.get("id") if isinstance(record, dict) else None,
        "transform": {"name": TRANSFORM_NAME, "version": TRANSFORM_VERSION},
        "action": decision.action,
        "classification": decision.classification,
        "reason_codes": list(decision.reason_codes),
        "shared_goal": decision.shared_goal,
        "prefix_overlap": decision.overlap,
        "changed_fields": list(decision.changed_fields),
        "pair_validation_errors": list(decision.pair_validation_errors or ()),
        "side_validation_errors": {
            side: list(errors)
            for side, errors in (decision.side_validation_errors or {}).items()
        },
        "output_id": decision.record.get("id") if decision.record is not None else None,
        "output_sha256": sha256_hex(output_line) if output_line is not None else None,
    }


def _summary(
    source: Path,
    policy: GatePolicy,
    total_json_records: int,
    tallies: dict[str, Counter[str]],
) -> dict[str, Any]:
    """Aggregate counts for one scan, derived only from the tallies."""

    actions = tallies["actions"]
    classifications = tallies["classifications"]
    reasons = tallies["reasons"]
    considered = actions[ACTION_RETAINED] + actions[ACTION_REPAIRED] + actions[ACTION_EXCLUDED]
    retained = actions[ACTION_RETAINED] + actions[ACTION_REPAIRED]
    return {
        "transform": {"name": TRANSFORM_NAME, "version": TRANSFORM_VERSION},
        "source": str(source),
        "enforce_outcome_agreement": policy.enforce_outcome_agreement,
        "json_records_seen": total_json_records,
        "trajectory_pairs_considered": considered,
        "skipped_same_state_pairs": classifications["same_state_pair_out_of_scope"],
        "skipped_non_preference_records": classifications["non_preference_record"],
        "retained_pairs": retained,
        "repaired_pairs": actions[ACTION_REPAIRED],
        "excluded_pairs": actions[ACTION_EXCLUDED],
        "prefix_overlap_absent_pairs": reasons[REASON_PREFIX_ABSENT],
        "branch_label_only_first_step_pairs": reasons[REASON_BRANCH_LABEL_ONLY],
        "actions": dict(sorted(actions.items())),
        "classifications": dict(sorted(classifications.items())),
        "reason_codes": dict(sorted(reasons.items())),
        "retained_gate_pass_pct": round(100.0 * retained / considered, 4) if considered else 0.0,
    }


def curate_source(source: Path, policy: GatePolicy = DEFAULT_POLICY) -> CurationRun:
    """Read and classify every record under ``source`` without writing."""

    source = Path(source)
    output_records: list[dict[str, Any]] = []
    manifest: list[dict[str, Any]] = []
    tallies: dict[str, Counter[str]] = {
        "actions": Counter(),
        "classifications": Counter(),
        "reasons": Counter(),
    }
    total_json_records = 0

    for line in _source_lines(source):
        total_json_records += 1
        record = _load_record(line)
        decision = curate_trajectory_pair(record, policy)
        tallies["actions"][decision.action] += 1
        tallies["classifications"][decision.classification] += 1
        tallies["reasons"].update(decision.reason_codes)

        output_line = _emitted_line(decision, line.location, policy)
        if output_line is not None:
            output_records.append(decision.record)
        manifest.append(_manifest_entry(decision, record, line, output_line))

    summary = _summary(source, policy, total_json_records, tallies)
    return CurationRun(tuple(output_records), tuple(manifest), summary)


def _reject_raw_destination(destination: Path, label: str) -> None:
    """Refuse any destination inside an ``outputs/raw`` tree.

    ``curate_agentic`` applies the same rule to its own writer; raw evidence is
    immutable and a curated view never lands on top of it.
    """

    parts = destination.resolve(strict=False).parts
    if any(parts[index : index + 2] == ("outputs", "raw") for index in range(len(parts) - 1)):
        raise TrajectoryCurationError(
            f"{label} must not be written under outputs/raw/: {destination}"
        )


def _render_human(run: CurationRun) -> str:
    summary = run.summary
    lines = [
        f"Trajectory pairs considered: {summary['trajectory_pairs_considered']}",
        f"Retained: {summary['retained_pairs']} (repaired {summary['repaired_pairs']})",
        f"Excluded: {summary['excluded_pairs']}",
        f"No shared prefix: {summary['prefix_overlap_absent_pairs']} "
        f"(branch-label-only first step: "
        f"{summary['branch_label_only_first_step_pairs']})",
        f"Skipped same-state pairs: {summary['skipped_same_state_pairs']}",
        f"Skipped non-preference records: {summary['skipped_non_preference_records']}",
        f"Gate pass rate: {summary['retained_gate_pass_pct']:.1f}%",
        "Decisions:",
    ]
    for entry in run.manifest:
        location = f"{entry['source_path']}:{entry['source_line']}"
        record_id = entry["source_record_id"] or "<no-id>"
        codes = ",".join(entry["reason_codes"])
        lines.append(f"- {location} {record_id}: {entry['action']} [{codes}]")
    return "\n".join(lines)


def _add_policy_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--enforce-outcome-agreement",
        action="store_true",
        help=(
            "also require each arm's outcome prose to agree with its own "
            "reward.success label, as round_txn does at publication time. Off "
            "by default: the check is lexical and misfires on external corpora "
            "whose outcome vocabulary this lane does not control (see "
            "docs/trajectory-preference-gate.md)."
        ),
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan = subparsers.add_parser("scan", help="classify pairs without writing")
    scan.add_argument("source", type=Path)
    scan.add_argument("--json", action="store_true", help="emit summary and decisions as JSON")
    _add_policy_argument(scan)

    curate = subparsers.add_parser("curate", help="write gate-passing pairs and a manifest")
    curate.add_argument("source", type=Path)
    curate.add_argument("--output", type=Path, required=True)
    curate.add_argument("--manifest", type=Path, required=True)
    _add_policy_argument(curate)
    return parser.parse_args(argv)


def _render_scan(run: CurationRun, as_json: bool) -> str:
    if not as_json:
        return _render_human(run)
    return json.dumps(
        {"summary": run.summary, "decisions": run.manifest},
        indent=2,
        sort_keys=True,
        ensure_ascii=False,
    )


def _run_command(args: argparse.Namespace) -> int:
    policy = GatePolicy(enforce_outcome_agreement=args.enforce_outcome_agreement)
    if args.command == "curate":
        _reject_raw_destination(args.output, "output")
        _reject_raw_destination(args.manifest, "manifest")

    run = curate_source(args.source, policy)
    if args.command == "scan":
        print(_render_scan(run, args.json))
        return 0

    write_run(run, args.source, args.output, args.manifest)
    print(json.dumps(run.summary, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        return _run_command(args)
    except (OSError, PreferenceCurationError, ValueError) as exc:
        print(f"trajectory preference curation failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
