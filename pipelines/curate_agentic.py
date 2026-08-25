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
the source supplies at least two factories for mill-ownership resolution.

Inspired by ToolMind turn-level filtering (Yang et al., 2025) and DPO
prefix sharing (Wang & Hegde, 2024): drop hidden CoT, flag ungrounded
turns, keep the preference contrast on one problem.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from check_records import reject_json_constant
from mill_family import (
    REASON_FOREIGN_MILL_GOAL_FAMILY,
    REASON_FOREIGN_MILL_ID_PREFIX,
    REASON_FOREIGN_PAYLOAD_FACTORY,
    MillFinding,
    MillIndex,
    summarize as summarize_mill_mix,
)
from round_txn import (
    FACTORY_QUOTAS,
    TransactionError,
    committed_jsonl_paths,
    marker_mode_path,
)


TRANSFORM_NAME = "agentic_observability"
TRANSFORM_VERSION = "2"

HIDDEN_THOUGHT_KEYS = frozenset(
    {"thought", "chain_of_thought", "scratch", "inner_monologue"}
)
THALAMIC_CORE_KEYS = (
    "state",
    "proposed_action",
    "safety_decision",
    "executed_action",
    "future_outcome",
    "reward_components",
)
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
REASON_GOAL_DIVERGES = "PREFERENCE_GOAL_DIVERGES"
REASON_GOAL_MISSING = "PREFERENCE_GOAL_MISSING"
REASON_GOAL_NOT_TEXT = "PREFERENCE_GOAL_NOT_TEXT"
REASON_SIDES_NOT_OBJECTS = "PREFERENCE_SIDES_NOT_OBJECTS"
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


def canonical_json(value: Any) -> str:
    """Stable JSON used for hashes and step-prefix equality."""
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def hash_value(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def hash_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def normalized_key_name(value: Any) -> str:
    """Normalize JSON keys across case, separators, and camel-case boundaries."""
    return re.sub(
        r"[^a-z0-9]+",
        "_",
        re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", str(value)).casefold(),
    ).strip("_")


def _is_under_raw(path: Path) -> bool:
    parts = path.resolve(strict=False).parts
    return any(
        parts[index : index + 2] == ("outputs", "raw")
        for index in range(len(parts) - 1)
    )


def contains_hidden_thought_key(value: Any) -> bool:
    """Return whether any nested mapping exposes a banned hidden-thought key."""
    if isinstance(value, dict):
        return any(
            normalized_key_name(key) in HIDDEN_THOUGHT_KEYS for key in value
        ) or any(contains_hidden_thought_key(item) for item in value.values())
    if isinstance(value, list):
        return any(contains_hidden_thought_key(item) for item in value)
    return False


def strip_hidden_thought_keys(value: Any) -> tuple[Any, int]:
    """Deep-copy ``value`` while removing banned hidden-thought keys."""
    if isinstance(value, dict):
        cleaned: dict[str, Any] = {}
        removed = 0
        for key, item in value.items():
            if normalized_key_name(key) in HIDDEN_THOUGHT_KEYS:
                removed += 1
                continue
            clean_item, nested = strip_hidden_thought_keys(item)
            cleaned[key] = clean_item
            removed += nested
        return cleaned, removed
    if isinstance(value, list):
        cleaned_items = []
        removed = 0
        for item in value:
            clean_item, nested = strip_hidden_thought_keys(item)
            cleaned_items.append(clean_item)
            removed += nested
        return cleaned_items, removed
    return copy.deepcopy(value), 0


def classify_record(obj: Any) -> str:
    """Route a record to an agentic kind, or a skippable non-agentic kind."""
    if not isinstance(obj, dict):
        return "unknown"
    if all(key in obj for key in THALAMIC_CORE_KEYS):
        return "thalamic"
    if "chosen" in obj and "rejected" in obj:
        sides = (obj.get("chosen"), obj.get("rejected"))
        if any(
            isinstance(side, dict)
            and "steps" in side
            and not all(key in side for key in THALAMIC_CORE_KEYS)
            for side in sides
        ):
            return "preference"
        if all(
            isinstance(side, dict) and all(key in side for key in THALAMIC_CORE_KEYS)
            for side in sides
        ):
            # Legacy Thalamic preference pairs deliberately have chosen/rejected
            # trajectory objects rather than agentic episode sides. They belong
            # in the skipped bucket, not in the agentic goal-impurity statistics.
            return "legacy_preference"
        return "preference"
    if "language_view" in obj and "spike_events" in obj:
        return "bridge_pair"
    if "case_type" in obj:
        return "safety_case"
    if "transcript" in obj and "agents" in obj:
        return "multi_agent"
    if "goal" in obj and "steps" in obj:
        return "episode"
    return "unknown"


def _record_id(record: Any) -> str | None:
    if not isinstance(record, dict):
        return None
    value = record.get("id")
    if isinstance(value, str) and value.strip():
        return value.strip()
    meta = record.get("meta")
    if isinstance(meta, dict):
        value = meta.get("id")
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _norm_goal(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = " ".join(value.split())
    return normalized or None


def preference_goals(record: dict[str, Any]) -> tuple[str | None, ...]:
    """Return (top, chosen, rejected) normalized goals; missing sides are None."""
    chosen = record.get("chosen")
    rejected = record.get("rejected")
    top = _norm_goal(record.get("goal"))
    chosen_goal = (
        _norm_goal(chosen.get("goal")) if isinstance(chosen, dict) else None
    )
    rejected_goal = (
        _norm_goal(rejected.get("goal")) if isinstance(rejected, dict) else None
    )
    return top, chosen_goal, rejected_goal


def shared_preference_goal(record: dict[str, Any]) -> tuple[bool, str | None]:
    """Whether chosen/rejected describe one problem.

    A shared goal is required. Top-level ``goal`` may stand in for a missing
    side goal. Any present goals must be identical after whitespace normalize.
    """
    chosen = record.get("chosen")
    rejected = record.get("rejected")
    if not isinstance(chosen, dict) or not isinstance(rejected, dict):
        return False, REASON_SIDES_NOT_OBJECTS
    raw_goals = (
        record.get("goal"),
        chosen.get("goal"),
        rejected.get("goal"),
    )
    if any(value is not None and _norm_goal(value) is None for value in raw_goals):
        return False, REASON_GOAL_NOT_TEXT
    top, chosen_goal, rejected_goal = preference_goals(record)
    present = [goal for goal in (top, chosen_goal, rejected_goal) if goal is not None]
    if not present:
        return False, REASON_GOAL_MISSING
    if top is None and (chosen_goal is None or rejected_goal is None):
        return False, REASON_GOAL_MISSING
    if len(set(present)) != 1:
        return False, REASON_GOAL_DIVERGES
    return True, None


def _basis_missing(step: Any) -> bool:
    if not isinstance(step, dict):
        return True
    basis = step.get("decision_basis")
    return not (isinstance(basis, str) and basis.strip())


def iter_turn_locations(record: Any) -> list[tuple[str, Any]]:
    """ToolMind-style turn sites: ``steps`` arrays and tool-using transcript turns."""
    locations: list[tuple[str, Any]] = []
    if not isinstance(record, dict):
        return locations

    def add_steps(prefix: str, owner: Any) -> None:
        if not isinstance(owner, dict):
            return
        steps = owner.get("steps")
        if not isinstance(steps, list):
            return
        for step_index, step in enumerate(steps):
            locations.append((f"{prefix}steps[{step_index}]", step))

    add_steps("", record)
    for side in ("chosen", "rejected"):
        add_steps(f"{side}.", record.get(side))

    transcript = record.get("transcript")
    if isinstance(transcript, list):
        for turn_index, turn in enumerate(transcript):
            if isinstance(turn, dict) and "tool_call" in turn:
                locations.append((f"transcript[{turn_index}]", turn))
    return locations


def missing_decision_basis_paths(record: Any) -> list[str]:
    """Return turn paths that lack a non-empty observable ``decision_basis``."""
    return [
        path
        for path, step in iter_turn_locations(record)
        if _basis_missing(step)
    ]


def prefix_overlap(chosen: Any, rejected: Any) -> dict[str, Any]:
    """Count leading thought-stripped steps shared by chosen and rejected.

    Zero overlap is recorded and is not a fail. A positive count is an
    optional purity note: DPO prefers a shared prefix and a suffix contrast.
    """
    chosen_steps = chosen.get("steps") if isinstance(chosen, dict) else None
    rejected_steps = rejected.get("steps") if isinstance(rejected, dict) else None
    chosen_len = len(chosen_steps) if isinstance(chosen_steps, list) else 0
    rejected_len = len(rejected_steps) if isinstance(rejected_steps, list) else 0
    shared = 0
    if isinstance(chosen_steps, list) and isinstance(rejected_steps, list):
        for left, right in zip(chosen_steps, rejected_steps):
            clean_left, _ = strip_hidden_thought_keys(left)
            clean_right, _ = strip_hidden_thought_keys(right)
            if canonical_json(clean_left) != canonical_json(clean_right):
                break
            shared += 1
    return {
        "shared_steps": shared,
        "chosen_steps": chosen_len,
        "rejected_steps": rejected_len,
        "noted": shared > 0,
    }


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
        marker_root = marker_factory(path)
        if marker_root is not None:
            return marker_root.name, True
        if source.is_file():
            return path.parent.name, False
        relative = path.relative_to(source)
        source_is_factory = (
            source.name in FACTORY_QUOTAS or source.name.endswith("-factory")
        )
        if source_is_factory or len(relative.parts) == 1:
            return source.name, source_is_factory
        # A run directory encloses one directory per factory. Nested work,
        # archive, and batch directories remain attributed to that first root.
        factory = relative.parts[0]
        verified = factory in FACTORY_QUOTAS or factory.endswith("-factory")
        return factory, verified

    return tuple(
        (path, *factory_identity(path)) for path in paths if visible(path)
    )


def _relative_source_path(source: Path, path: Path) -> str:
    if source.is_dir():
        return path.relative_to(source).as_posix()
    return path.name


def _quarantine_foreign_mills(
    kept: list[tuple[str, int, dict[str, Any], str, bool]],
    decisions: list[dict[str, Any]],
    mills: MillIndex,
    actions: Counter[str],
    reasons: Counter[str],
) -> list[MillFinding]:
    """Flip surviving records whose mill is foreign to their directory.

    Mill ownership can only be resolved once the whole source has been read,
    so this runs after the per-record pass and rewrites the affected decisions
    in place. Records this pass already excluded keep their original reason.
    """
    survivors = {
        index
        for _relative, index, _curated, _factory, _verified in kept
    }
    quarantined = []
    for finding in mills.findings():
        if finding.ref not in survivors:
            continue
        decision = decisions[finding.ref]
        actions[decision["action"]] -= 1
        actions[ACTION_EXCLUDED] += 1
        decision["action"] = ACTION_EXCLUDED
        decision["reason_codes"] = list(decision["reason_codes"]) + list(
            finding.reason_codes
        )
        decision["output_id"] = None
        decision["output_hash"] = None
        decision["mill_family"] = finding.as_dict()
        reasons.update(finding.reason_codes)
        quarantined.append(finding)
    return quarantined


def curate_source(source: Path) -> dict[str, Any]:
    """Read-only scan of ``source`` (file or directory). Missing paths are empty."""
    source = Path(source)
    records_by_rel: dict[str, list[dict[str, Any]]] = defaultdict(list)
    decisions: list[dict[str, Any]] = []
    # (relative source file, index into ``decisions``, curated record) for every
    # record that survived per-record curation. The cleaned tree is assembled
    # from this only after the cross-record mill-family pass has run.
    kept: list[tuple[str, int, dict[str, Any], str, bool]] = []
    mills = MillIndex()
    actions: Counter[str] = Counter()
    kinds: Counter[str] = Counter()
    reasons: Counter[str] = Counter()
    thought_removed = 0
    missing_basis = 0
    preference_pairs = 0
    preference_shared = 0
    preference_diverged = 0
    overlap_shared_total = 0
    overlap_zero = 0
    files = 0
    input_records = 0

    for path, factory, factory_verified in _source_jsonl_entries(source):
        files += 1
        relative = _relative_source_path(source, path)
        payload = path.read_bytes()
        for line_number, raw_line in enumerate(payload.splitlines(), 1):
            if not raw_line.strip():
                continue
            input_records += 1
            source_hash = hash_bytes(raw_line)
            try:
                text = raw_line.decode("utf-8")
            except UnicodeDecodeError:
                decision = _base_decision(
                    source_path=relative,
                    source_line=line_number,
                    source_hash=source_hash,
                    kind="unknown",
                )
                decision["reason_codes"] = [REASON_INVALID_UTF8]
                decisions.append(decision)
                actions[ACTION_EXCLUDED] += 1
                reasons[REASON_INVALID_UTF8] += 1
                continue
            try:
                record = json.loads(text, parse_constant=reject_json_constant)
            except (json.JSONDecodeError, ValueError):
                decision = _base_decision(
                    source_path=relative,
                    source_line=line_number,
                    source_hash=source_hash,
                    kind="unknown",
                )
                decision["reason_codes"] = [REASON_INVALID_JSON]
                decisions.append(decision)
                actions[ACTION_EXCLUDED] += 1
                reasons[REASON_INVALID_JSON] += 1
                continue

            curated, decision = curate_record(
                record,
                source_path=relative,
                source_line=line_number,
                source_hash=source_hash,
            )
            decisions.append(decision)
            actions[decision["action"]] += 1
            kinds[decision["kind"]] += 1
            reasons.update(decision["reason_codes"])
            thought_removed += decision["thought_fields_removed"]
            missing_basis += len(decision["missing_decision_basis"])
            if decision["kind"] == "preference":
                preference_pairs += 1
                if decision["action"] == ACTION_EXCLUDED and (
                    REASON_GOAL_DIVERGES in decision["reason_codes"]
                    or REASON_GOAL_MISSING in decision["reason_codes"]
                    or REASON_GOAL_NOT_TEXT in decision["reason_codes"]
                    or REASON_SIDES_NOT_OBJECTS in decision["reason_codes"]
                ):
                    preference_diverged += 1
                elif decision["action"] != ACTION_SKIPPED:
                    preference_shared += 1
                overlap = decision.get("prefix_overlap") or {}
                overlap_shared_total += int(overlap.get("shared_steps") or 0)
                if overlap and not overlap.get("noted"):
                    overlap_zero += 1
            if curated is not None:
                decision_index = len(decisions) - 1
                # Only records that survive ordinary curation may teach mill
                # identity. Skipped or already-excluded objects are not native
                # ownership evidence and cannot poison the cross-record model.
                mills.add(factory, curated, decision_index)
                kept.append(
                    (
                        relative,
                        decision_index,
                        curated,
                        factory,
                        factory_verified,
                    )
                )

    context_factories = sorted(
        {
            factory
            for _relative, _index, _curated, factory, verified in kept
            if verified
        }
    )
    context_complete = len(context_factories) >= 2
    quarantined = (
        _quarantine_foreign_mills(kept, decisions, mills, actions, reasons)
        if context_complete
        else []
    )
    dropped = {finding.ref for finding in quarantined}
    for relative, index, curated, _factory, _verified in kept:
        if index not in dropped:
            records_by_rel[relative].append(curated)
    records_by_rel = {
        relative: items
        for relative, items in sorted(records_by_rel.items())
        if items
    }

    output_records = sum(len(items) for items in records_by_rel.values())
    mill_summary = summarize_mill_mix(quarantined)
    mill_summary.update(
        {
            "context_complete": context_complete,
            "context_factories": context_factories,
            "quarantine_applied": context_complete,
        }
    )
    summary = {
        "transform": {"name": TRANSFORM_NAME, "version": TRANSFORM_VERSION},
        "source": str(source),
        "files": files,
        "input_records": input_records,
        "output_records": output_records,
        "excluded_records": actions[ACTION_EXCLUDED],
        "skipped_records": actions[ACTION_SKIPPED],
        "quarantined_foreign_mill_records": len(quarantined),
        "thought_fields_removed": thought_removed,
        "missing_decision_basis_turns": missing_basis,
        "by_kind": dict(sorted(kinds.items())),
        "actions": {
            action: count for action, count in sorted(actions.items()) if count
        },
        "reason_codes": dict(sorted(reasons.items())),
        "mill_family": mill_summary,
        "preference": {
            "pairs": preference_pairs,
            "shared_goal": preference_shared,
            "goal_impure": preference_diverged,
            "prefix_overlap_zero": overlap_zero,
            "prefix_overlap_shared_steps_sum": overlap_shared_total,
        },
    }
    return {
        "records_by_rel": records_by_rel,
        "decisions": decisions,
        "summary": summary,
    }


def _preflight_out(source: Path, out: Path) -> None:
    source_resolved = source.resolve(strict=False)
    out_resolved = out.resolve(strict=False)
    if _is_under_raw(out):
        raise ValueError(f"refusing to write inside immutable raw evidence: {out}")
    if out.exists():
        raise FileExistsError(f"refusing to replace existing destination: {out}")
    if source_resolved == out_resolved:
        raise ValueError(f"output cannot replace source: {out}")
    if source.is_dir() and source_resolved in out_resolved.parents:
        raise ValueError(f"output cannot be written inside source: {out}")


def _write_new_jsonl(path: Path, values: list[dict[str, Any]]) -> None:
    if _is_under_raw(path):
        raise ValueError(f"refusing to write inside immutable raw evidence: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            for value in values:
                handle.write(canonical_json(value))
                handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        path.unlink(missing_ok=True)
        raise


def _write_new_json(path: Path, value: Any) -> None:
    """Write one metadata document without making it a record-scanner input."""
    if _is_under_raw(path):
        raise ValueError(f"refusing to write inside immutable raw evidence: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        path.unlink(missing_ok=True)
        raise


def write_cleaned_tree(run: dict[str, Any], out: Path) -> None:
    """Write retained JSONL plus scanner-safe JSON metadata in a new directory."""
    mill_summary = run.get("summary", {}).get("mill_family")
    if (
        isinstance(mill_summary, dict)
        and mill_summary.get("quarantine_applied") is False
    ):
        raise ValueError(
            "refusing cleaned output without multi-factory mill ownership context"
        )
    out = Path(out)
    created: list[Path] = []
    try:
        out.mkdir(parents=True, exist_ok=False)
        for relative, records in sorted(run["records_by_rel"].items()):
            dest = out / relative
            _write_new_jsonl(dest, records)
            created.append(dest)
        # Metadata must not have a .jsonl suffix: every standard validator and
        # training audit recursively treats that extension as record payload.
        manifest_path = out / "CURATE-MANIFEST.json"
        _write_new_json(manifest_path, run["decisions"])
        created.append(manifest_path)
        report_path = out / "CURATE-REPORT.json"
        _write_new_json(report_path, run["summary"])
        created.append(report_path)
    except BaseException:
        for path in reversed(created):
            try:
                path.unlink()
            except FileNotFoundError:
                pass
        if out.exists() and out.is_dir():
            for leftover in sorted(out.rglob("*"), reverse=True):
                if leftover.is_file():
                    leftover.unlink(missing_ok=True)
                elif leftover.is_dir():
                    try:
                        leftover.rmdir()
                    except OSError:
                        pass
            try:
                out.rmdir()
            except OSError:
                pass
        raise


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
