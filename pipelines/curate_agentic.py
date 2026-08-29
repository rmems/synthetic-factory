#!/usr/bin/env python3
"""Curate Grok 4.6 agentic JSONL without rewriting raw.

Reads episode / episode-preference / multi_agent / safety_case records.
Drops hidden-thought keys recursively, including nested payload keys with
reserved names, flags missing ``decision_basis``, and requires preference
sides to share a goal. Prefix overlap of leading steps is noted in the
report and is not a hard fail.

Records whose mill signals belong to another factory are quarantined rather
than composed into the cleaned tree. Mill identity is keyed on the declared
payload factory, the mill id prefix, and the goal family (``mill_family.py``);
it is deliberately not keyed on ``leftover`` appearing in a record id, nor on
a destination-specific field being absent.

Never writes into ``outputs/raw/``. Default is a ``--dry-run`` JSON report
on stdout. ``--out DIR`` writes a brand-new cleaned tree only when passed and
the source supplies resolved, verified multi-factory ownership evidence.

Inspired by ToolMind turn-level filtering (Yang et al., 2025) and DPO
prefix sharing (Wang & Hegde, 2024): drop hidden CoT, flag ungrounded
turns, keep the preference contrast on one problem.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from check_records import reject_json_constant
from curate_agentic_output import (
    preflight_out as _preflight_out,
    write_cleaned_tree,
)
from curate_agentic_shapes import (
    HIDDEN_THOUGHT_KEYS,
    INVALID_PREFERENCE_KIND,
    REASON_GOAL_DIVERGES,
    REASON_GOAL_MISSING,
    REASON_GOAL_NOT_TEXT,
    REASON_SIDES_NOT_OBJECTS,
    canonical_json,
    classify_record,
    contains_hidden_thought_key,
    hash_bytes,
    hash_value,
    iter_turn_locations,
    missing_decision_basis_paths,
    normalized_key_name,
    preference_goals,
    prefix_overlap,
    record_identifier as _record_id,
    shared_preference_goal,
    strip_hidden_thought_keys,
)
from curate_identity import default_registry
from mill_family import (
    REASON_FOREIGN_MILL_GOAL_FAMILY,
    REASON_FOREIGN_MILL_ID_PREFIX,
    REASON_FOREIGN_PAYLOAD_FACTORY,
    MillFinding,
    MillIndex,
    factory_identity_for_path,
    summarize as summarize_mill_mix,
)
from record_kind import preference_side_kinds
from round_txn import (
    TransactionError,
    committed_jsonl_paths,
    marker_mode_path,
)


TRANSFORM_NAME = "agentic_observability"
TRANSFORM_VERSION = "2"

SAFETY_CASE_TYPES = frozenset(
    {"correct_refusal", "incorrect_refusal", "missed_refusal"}
)
AGENTIC_KINDS = frozenset(
    {"episode", "preference", "multi_agent", "safety_case"}
)

ACTION_RETAINED = "retained"
ACTION_MODIFIED = "modified"
ACTION_FLAGGED = "flagged"
ACTION_EXCLUDED = "excluded"
ACTION_SKIPPED = "skipped"

REASON_THOUGHT_REMOVED = "HIDDEN_THOUGHT_REMOVED"
REASON_MISSING_BASIS = "MISSING_DECISION_BASIS"
REASON_SIDE_SHAPE_INVALID = "PREFERENCE_SIDE_SHAPE_INVALID"
REASON_PREFERENCE_COLLAPSED = "PREFERENCE_COLLAPSED_AFTER_THOUGHT_STRIP"
REASON_SAFETY_CASE_TYPE_INVALID = "SAFETY_CASE_TYPE_INVALID"
REASON_PREFIX_OVERLAP = "PREFIX_OVERLAP_NOTED"
REASON_RECORD_NOT_OBJECT = "RECORD_NOT_OBJECT"
REASON_INVALID_JSON = "INVALID_JSON"
REASON_INVALID_UTF8 = "INVALID_UTF8"
REASON_SKIPPED_KIND = "SKIPPED_NON_AGENTIC"
# Foreign-mill quarantine codes, resolved across the whole source tree rather
# than per record; re-exported so callers import one curation vocabulary.
MILL_FAMILY_REASON_CODES = (
    REASON_FOREIGN_PAYLOAD_FACTORY,
    REASON_FOREIGN_MILL_ID_PREFIX,
    REASON_FOREIGN_MILL_GOAL_FAMILY,
)


# Every name callers import from this module, including the ones re-exported
# from curate_agentic_shapes / curate_agentic_output after the split.
__all__ = [
    "ACTION_EXCLUDED",
    "ACTION_FLAGGED",
    "ACTION_MODIFIED",
    "ACTION_RETAINED",
    "ACTION_SKIPPED",
    "AGENTIC_KINDS",
    "HIDDEN_THOUGHT_KEYS",
    "INVALID_PREFERENCE_KIND",
    "MILL_FAMILY_REASON_CODES",
    "PREFERENCE_GOAL_IMPURE_REASONS",
    "REASON_FOREIGN_MILL_GOAL_FAMILY",
    "REASON_FOREIGN_MILL_ID_PREFIX",
    "REASON_FOREIGN_PAYLOAD_FACTORY",
    "REASON_GOAL_DIVERGES",
    "REASON_GOAL_MISSING",
    "REASON_GOAL_NOT_TEXT",
    "REASON_INVALID_JSON",
    "REASON_INVALID_UTF8",
    "REASON_MISSING_BASIS",
    "REASON_PREFERENCE_COLLAPSED",
    "REASON_PREFIX_OVERLAP",
    "REASON_RECORD_NOT_OBJECT",
    "REASON_SAFETY_CASE_TYPE_INVALID",
    "REASON_SIDES_NOT_OBJECTS",
    "REASON_SIDE_SHAPE_INVALID",
    "REASON_SKIPPED_KIND",
    "REASON_THOUGHT_REMOVED",
    "SAFETY_CASE_TYPES",
    "TRANSFORM_NAME",
    "TRANSFORM_VERSION",
    "canonical_json",
    "classify_record",
    "contains_hidden_thought_key",
    "curate_record",
    "curate_source",
    "hash_bytes",
    "hash_value",
    "iter_turn_locations",
    "main",
    "missing_decision_basis_paths",
    "normalized_key_name",
    "parse_args",
    "preference_goals",
    "prefix_overlap",
    "shared_preference_goal",
    "strip_hidden_thought_keys",
    "write_cleaned_tree",
]


def _base_decision(
    *,
    source_path: str,
    source_line: int,
    source_hash: str,
    kind: str,
) -> dict[str, Any]:
    return {
        "source_path": source_path,
        "source_line": source_line,
        "source_hash": source_hash,
        "transform": TRANSFORM_NAME,
        "transform_version": TRANSFORM_VERSION,
        "kind": kind,
        "action": ACTION_EXCLUDED,
        "reason_codes": [],
        "output_id": None,
        "output_hash": None,
        "thought_fields_removed": 0,
        "missing_decision_basis": [],
        "prefix_overlap": None,
    }


def curate_record(
    record: Any,
    *,
    source_path: str = "<memory>",
    source_line: int = 1,
    source_hash: str | None = None,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    """Curate one decoded record. Never mutates ``record``."""
    digest = source_hash or hash_value(record)
    kind = classify_record(record)
    decision = _base_decision(
        source_path=source_path,
        source_line=source_line,
        source_hash=digest,
        kind=kind,
    )
    if not isinstance(record, dict):
        decision["reason_codes"] = [REASON_RECORD_NOT_OBJECT]
        return None, decision
    if kind == INVALID_PREFERENCE_KIND:
        decision["reason_codes"] = [REASON_SIDE_SHAPE_INVALID]
        return None, decision
    if kind not in AGENTIC_KINDS:
        decision["action"] = ACTION_SKIPPED
        decision["reason_codes"] = [REASON_SKIPPED_KIND]
        return None, decision

    cleaned, removed = strip_hidden_thought_keys(record)
    decision["thought_fields_removed"] = removed
    reasons: list[str] = []
    if removed:
        reasons.append(REASON_THOUGHT_REMOVED)

    if kind == "preference":
        ok, goal_reason = shared_preference_goal(record)
        if not ok:
            decision["reason_codes"] = reasons + [goal_reason]
            return None, decision
        if preference_side_kinds(record) != ("episode", "episode"):
            decision["reason_codes"] = reasons + [REASON_SIDE_SHAPE_INVALID]
            return None, decision
        cleaned_chosen = cleaned.get("chosen")
        cleaned_rejected = cleaned.get("rejected")
        if all(
            cleaned_chosen.get(field) == cleaned_rejected.get(field)
            for field in ("steps", "outcome")
        ):
            decision["reason_codes"] = reasons + [REASON_PREFERENCE_COLLAPSED]
            return None, decision
        overlap = prefix_overlap(record.get("chosen"), record.get("rejected"))
        decision["prefix_overlap"] = overlap
        if overlap["noted"]:
            reasons.append(REASON_PREFIX_OVERLAP)
    if kind == "safety_case":
        case_type = record.get("case_type")
        if not isinstance(case_type, str) or case_type not in SAFETY_CASE_TYPES:
            decision["reason_codes"] = reasons + [REASON_SAFETY_CASE_TYPE_INVALID]
            return None, decision

    missing = missing_decision_basis_paths(cleaned)
    decision["missing_decision_basis"] = missing
    if missing:
        reasons.append(REASON_MISSING_BASIS)

    if contains_hidden_thought_key(cleaned):
        raise AssertionError("agentic curation emitted a hidden thought key")

    changed = cleaned != record
    if missing:
        action = ACTION_FLAGGED
    elif changed:
        action = ACTION_MODIFIED
    else:
        action = ACTION_RETAINED

    decision.update(
        {
            "action": action,
            "reason_codes": reasons,
            "output_id": _record_id(cleaned),
            "output_hash": hash_value(cleaned),
        }
    )
    return cleaned, decision


def _source_jsonl_entries(source: Path) -> tuple[tuple[Path, str, bool], ...]:
    """Return visible JSONL paths paired with their enclosing factory names."""

    if not source.exists():
        return ()
    if source.is_file():
        paths = (source,) if source.suffix == ".jsonl" and not source.is_symlink() else ()
    else:
        paths = tuple(
            sorted(
                path
                for path in source.rglob("*.jsonl")
                if path.is_file() and not path.is_symlink()
            )
        )

    visible_by_factory: dict[Path, set[Path]] = {}
    enclosing_factory: dict[Path, Path | None] = {}

    def marker_factory(path: Path) -> Path | None:
        visited = []
        current = path.parent
        while True:
            if current in enclosing_factory:
                factory = enclosing_factory[current]
                break
            visited.append(current)
            if marker_mode_path(current) is not None:
                factory = current
                break
            parent = current.parent
            if parent == current:
                factory = None
                break
            current = parent
        for directory in visited:
            enclosing_factory[directory] = factory
        return factory

    def visible(path: Path) -> bool:
        factory = marker_factory(path)
        if factory is None:
            return True
        if factory not in visible_by_factory:
            visible_by_factory[factory] = {
                candidate.resolve() for candidate in committed_jsonl_paths(factory)
            }
        return path.resolve() in visible_by_factory[factory]

    def factory_identity(path: Path) -> tuple[str, bool]:
        return factory_identity_for_path(
            source,
            path,
            marker_root=marker_factory(path),
            # The reviewed factory registry is the source of truth for which
            # directory names are a known factory. The round-quota table
            # (FACTORY_QUOTAS) only covers factories with an active quota;
            # a registered-but-unquota'd factory (e.g. an identity-only
            # generator) would otherwise be treated as unverified, letting
            # an all-foreign batch under that root redefine the destination
            # from its own payload majority instead of being quarantined.
            known_factories=default_registry().by_path_id,
        )

    return tuple(
        (path, *factory_identity(path)) for path in paths if visible(path)
    )


def _relative_source_path(source: Path, path: Path) -> str:
    if source.is_dir():
        return path.relative_to(source).as_posix()
    return path.name


def _quarantine_foreign_mills(
    scan: "_SourceScan", findings: tuple[MillFinding, ...]
) -> list[MillFinding]:
    """Flip surviving records whose mill is foreign to their directory.

    Mill ownership can only be resolved once the whole source has been read,
    so this runs after the per-record pass and rewrites the affected decisions
    in place. Records this pass already excluded keep their original reason.
    """
    survivors = {
        index
        for _relative, index, _curated, _factory, _verified in scan.kept
    }
    quarantined = []
    for finding in findings:
        if finding.ref not in survivors:
            continue
        decision = scan.decisions[finding.ref]
        scan.tally.actions[decision["action"]] -= 1
        scan.tally.actions[ACTION_EXCLUDED] += 1
        decision["action"] = ACTION_EXCLUDED
        decision["reason_codes"] = list(decision["reason_codes"]) + list(
            finding.reason_codes
        )
        decision["output_id"] = None
        decision["output_hash"] = None
        decision["mill_family"] = finding.as_dict()
        scan.tally.reasons.update(finding.reason_codes)
        quarantined.append(finding)
    return quarantined


# The preference verdicts that mean "these two sides are not one problem".
# Collected as a set so the per-record tally asks one membership question
# instead of a four-way ``or`` chain.
PREFERENCE_GOAL_IMPURE_REASONS = frozenset(
    {
        REASON_GOAL_DIVERGES,
        REASON_GOAL_MISSING,
        REASON_GOAL_NOT_TEXT,
        REASON_SIDES_NOT_OBJECTS,
    }
)


@dataclass
class _CurationTally:
    """Running counters the per-record pass accumulates for one source."""

    actions: Counter[str] = field(default_factory=Counter)
    kinds: Counter[str] = field(default_factory=Counter)
    reasons: Counter[str] = field(default_factory=Counter)
    thought_removed: int = 0
    missing_basis: int = 0
    preference_pairs: int = 0
    preference_shared: int = 0
    preference_diverged: int = 0
    overlap_shared_total: int = 0
    overlap_zero: int = 0
    files: int = 0
    input_records: int = 0


@dataclass
class _SourceScan:
    """What the per-record pass produces before mill ownership is known.

    ``kept`` is (relative source file, index into ``decisions``, curated
    record, enclosing factory, factory-verified flag) for every record that
    survived per-record curation. The cleaned tree is assembled from it only
    after the cross-record mill-family pass has run.
    """

    decisions: list[dict[str, Any]] = field(default_factory=list)
    kept: list[tuple[str, int, dict[str, Any], str, bool]] = field(
        default_factory=list
    )
    mills: MillIndex = field(default_factory=MillIndex)
    tally: _CurationTally = field(default_factory=_CurationTally)


@dataclass(frozen=True)
class _RecordSite:
    """Where one source line came from, and which factory published it."""

    relative: str
    line_number: int
    source_hash: str
    factory: str
    factory_verified: bool


def _record_undecodable(
    scan: _SourceScan, site: _RecordSite, reason: str
) -> None:
    """Record one source line that could not be decoded into a record at all."""
    decision = _base_decision(
        source_path=site.relative,
        source_line=site.line_number,
        source_hash=site.source_hash,
        kind="unknown",
    )
    decision["reason_codes"] = [reason]
    scan.decisions.append(decision)
    scan.tally.actions[ACTION_EXCLUDED] += 1
    scan.tally.reasons[reason] += 1


def _tally_preference(decision: dict[str, Any], tally: _CurationTally) -> None:
    """Fold one preference decision into the preference statistics."""
    tally.preference_pairs += 1
    impure = not PREFERENCE_GOAL_IMPURE_REASONS.isdisjoint(
        decision["reason_codes"]
    )
    if decision["action"] == ACTION_EXCLUDED and impure:
        tally.preference_diverged += 1
    elif decision["action"] != ACTION_SKIPPED:
        tally.preference_shared += 1
    overlap = decision.get("prefix_overlap") or {}
    tally.overlap_shared_total += int(overlap.get("shared_steps") or 0)
    if overlap and not overlap.get("noted"):
        tally.overlap_zero += 1


def _tally_decision(decision: dict[str, Any], tally: _CurationTally) -> None:
    """Fold one curated decision into the running counters."""
    tally.actions[decision["action"]] += 1
    tally.kinds[decision["kind"]] += 1
    tally.reasons.update(decision["reason_codes"])
    tally.thought_removed += decision["thought_fields_removed"]
    tally.missing_basis += len(decision["missing_decision_basis"])
    if decision["kind"] == "preference":
        _tally_preference(decision, tally)


def _keep_curated(
    scan: _SourceScan, site: _RecordSite, curated: dict[str, Any]
) -> None:
    """Index one surviving record for the cross-record mill-family pass."""
    decision_index = len(scan.decisions) - 1
    # Only records that survive ordinary curation may teach mill identity.
    # Skipped or already-excluded objects are not native ownership evidence
    # and cannot poison the cross-record model.
    scan.mills.add(
        site.factory,
        curated,
        decision_index,
        factory_verified=site.factory_verified,
    )
    scan.kept.append(
        (
            site.relative,
            decision_index,
            curated,
            site.factory,
            site.factory_verified,
        )
    )


def _scan_line(scan: _SourceScan, site: _RecordSite, raw_line: bytes) -> None:
    """Decode and curate one source line into ``scan``."""
    try:
        text = raw_line.decode("utf-8")
    except UnicodeDecodeError:
        _record_undecodable(scan, site, REASON_INVALID_UTF8)
        return
    try:
        record = json.loads(text, parse_constant=reject_json_constant)
    except (json.JSONDecodeError, ValueError):
        _record_undecodable(scan, site, REASON_INVALID_JSON)
        return

    curated, decision = curate_record(
        record,
        source_path=site.relative,
        source_line=site.line_number,
        source_hash=site.source_hash,
    )
    scan.decisions.append(decision)
    _tally_decision(decision, scan.tally)
    if curated is not None:
        _keep_curated(scan, site, curated)


def _scan_source(source: Path) -> _SourceScan:
    """Run the per-record curation pass over every visible line of ``source``."""
    scan = _SourceScan()
    for path, factory, factory_verified in _source_jsonl_entries(source):
        scan.tally.files += 1
        relative = _relative_source_path(source, path)
        for line_number, raw_line in enumerate(
            path.read_bytes().splitlines(), 1
        ):
            if not raw_line.strip():
                continue
            scan.tally.input_records += 1
            _scan_line(
                scan,
                _RecordSite(
                    relative=relative,
                    line_number=line_number,
                    source_hash=hash_bytes(raw_line),
                    factory=factory,
                    factory_verified=factory_verified,
                ),
                raw_line,
            )
    return scan


def _mill_summary(
    mill_findings: tuple[MillFinding, ...], ownership: dict[str, Any]
) -> dict[str, Any]:
    """The mill-mix block, plus why ownership was or was not resolved.

    A partial dry run cannot safely mutate records, but it must still report
    every foreign-mill finding that is independently determinable.
    """
    context_complete = ownership["complete"]
    summary = summarize_mill_mix(mill_findings)
    summary.update(
        {
            "context_complete": context_complete,
            "reference_scope_complete": ownership["reference_scope_complete"],
            "context_factories": ownership["verified_factories"],
            "unresolved_destinations": ownership["unresolved_destinations"],
            "unresolved_prefixes": ownership["unresolved_prefixes"],
            "unresolved_goal_records": ownership["unresolved_goal_records"],
            "missing_home_factories": ownership["missing_home_factories"],
            "quarantine_applied": context_complete,
        }
    )
    return summary


def _records_by_rel(
    kept: list[tuple[str, int, dict[str, Any], str, bool]],
    dropped: set[int],
) -> dict[str, list[dict[str, Any]]]:
    """Group surviving curated records by source file, dropping emptied files."""
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for relative, index, curated, _factory, _verified in kept:
        if index not in dropped:
            grouped[relative].append(curated)
    return {
        relative: items
        for relative, items in sorted(grouped.items())
        if items
    }


def _build_summary(
    source: Path,
    tally: _CurationTally,
    mill_summary: dict[str, Any],
    totals: tuple[int, int],
) -> dict[str, Any]:
    """Assemble the report summary block."""
    output_records, quarantined_records = totals
    return {
        "transform": {"name": TRANSFORM_NAME, "version": TRANSFORM_VERSION},
        "source": str(source),
        "files": tally.files,
        "input_records": tally.input_records,
        "output_records": output_records,
        "excluded_records": tally.actions[ACTION_EXCLUDED],
        "skipped_records": tally.actions[ACTION_SKIPPED],
        "quarantined_foreign_mill_records": quarantined_records,
        "thought_fields_removed": tally.thought_removed,
        "missing_decision_basis_turns": tally.missing_basis,
        "by_kind": dict(sorted(tally.kinds.items())),
        "actions": {
            action: count
            for action, count in sorted(tally.actions.items())
            if count
        },
        "reason_codes": dict(sorted(tally.reasons.items())),
        "mill_family": mill_summary,
        "preference": {
            "pairs": tally.preference_pairs,
            "shared_goal": tally.preference_shared,
            "goal_impure": tally.preference_diverged,
            "prefix_overlap_zero": tally.overlap_zero,
            "prefix_overlap_shared_steps_sum": tally.overlap_shared_total,
        },
    }


def curate_source(source: Path) -> dict[str, Any]:
    """Read-only scan of ``source`` (file or directory). Missing paths are empty."""
    source = Path(source)
    scan = _scan_source(source)

    ownership = scan.mills.ownership_context()
    mill_findings = scan.mills.findings()
    quarantined = (
        _quarantine_foreign_mills(scan, mill_findings)
        if ownership["complete"]
        else []
    )
    dropped = {finding.ref for finding in quarantined}
    records_by_rel = _records_by_rel(scan.kept, dropped)
    output_records = sum(len(items) for items in records_by_rel.values())
    return {
        "records_by_rel": records_by_rel,
        "decisions": scan.decisions,
        "summary": _build_summary(
            source,
            scan.tally,
            _mill_summary(mill_findings, ownership),
            (output_records, len(quarantined)),
        ),
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "source",
        type=Path,
        help=(
            "JSONL file or run directory (missing/empty is a zero report; "
            "cleaned output requires multi-factory context)"
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print the report only (default when --out is omitted)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        help="write a NEW cleaned tree; refused under outputs/raw/",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.out is not None and args.dry_run:
        print("curate_agentic: refusing --out with --dry-run", file=sys.stderr)
        return 2
    dry_run = args.out is None
    try:
        if args.out is not None:
            _preflight_out(args.source, args.out)
        run = curate_source(args.source)
        run["summary"]["dry_run"] = dry_run
        if args.out is not None:
            write_cleaned_tree(run, args.out)
            run["summary"]["out"] = str(args.out)
        print(json.dumps(run["summary"], ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    except (OSError, ValueError, FileExistsError, TransactionError) as exc:
        print(f"agentic curation failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
