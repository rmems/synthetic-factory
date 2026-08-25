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
import copy
import hashlib
import json
import math
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

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


TRANSFORM_NAME = "trajectory-pair-preference-curation"
TRANSFORM_VERSION = "1.2.0"

ACTION_RETAINED = "retained"
ACTION_REPAIRED = "repaired"
ACTION_EXCLUDED = "excluded"
ACTION_SKIPPED = "skipped"

REASON_RECORD_NOT_OBJECT = "TRAJECTORY_RECORD_NOT_AN_OBJECT"
REASON_NOT_A_PAIR = "NOT_A_PREFERENCE_PAIR_RECORD"
REASON_SIDES_NOT_OBJECTS = "TRAJECTORY_PAIR_SIDES_NOT_OBJECTS"
REASON_SAME_STATE_SCHEMA = "SAME_STATE_PAIR_DEFERRED_TO_CURATE_PREFERENCES"
REASON_PAIR_ENVELOPE_INVALID = "TRAJECTORY_PAIR_ENVELOPE_INVALID"
REASON_SIDE_EPISODE_INVALID = "TRAJECTORY_PAIR_SIDE_EPISODE_INVALID"
REASON_STEPS_INVALID = "TRAJECTORY_STEPS_MISSING_OR_INVALID"
REASON_STEPS_EMPTY = "TRAJECTORY_STEPS_EMPTY"
REASON_PAIR_IDENTICAL = "TRAJECTORY_PAIR_IDENTICAL"
REASON_PREFIX_ABSENT = "TRAJECTORY_PREFIX_OVERLAP_ABSENT"
REASON_BRANCH_LABEL_ONLY = "FIRST_STEP_DIFFERS_BY_BRANCH_LABEL_ONLY"
REASON_OUTCOME_MISSING = "TRAJECTORY_OUTCOME_MISSING"
REASON_OUTCOME_INVALID = "TRAJECTORY_OUTCOME_INVALID"
REASON_OUTCOME_NOT_DIVERGENT = "TRAJECTORY_OUTCOME_DOES_NOT_DIVERGE"
REASON_REWARD_MISSING = "TRAJECTORY_REWARD_MISSING"
REASON_REWARD_INVALID = "TRAJECTORY_REWARD_INVALID"
REASON_REWARD_NOT_DIVERGENT = "TRAJECTORY_REWARD_DOES_NOT_DIVERGE"
REASON_PREFERENCE_DIRECTION_INVALID = "TRAJECTORY_PREFERENCE_DIRECTION_INVALID"
REASON_GATE_PASSED = "TRAJECTORY_PAIR_SHARED_GOAL_AND_PREFIX"
REASON_GOAL_WHITESPACE_NORMALIZED = "TRAJECTORY_GOAL_WHITESPACE_NORMALIZED"

# A step whose only cross-branch difference is the literal word "chosen" or
# "rejected" leaks the branch label into the trajectory itself. It is reported
# on the reject path as native impurity; it is never repaired here, because
# rewriting generated step text would fabricate evidence.
BRANCH_LABEL_RE = re.compile(r"\b(?:chosen|rejected)\b", re.IGNORECASE)
BRANCH_LABEL_MASK = "<branch>"

# Goal vocabulary is shared with curate_agentic so the two lanes never
# disagree about what "one problem" means.
GOAL_REASONS = (REASON_GOAL_MISSING, REASON_GOAL_NOT_TEXT, REASON_GOAL_DIVERGES)
SAME_STATE_FIELDS = ("state", "proposed_action")
GOAL_LOCATIONS = (("goal",), ("chosen", "goal"), ("rejected", "goal"))


class TrajectoryCurationError(PreferenceCurationError):
    """Raised when trajectory-pair source or destination handling is unsafe."""


def _parse_finite_json_float(text: str) -> float:
    """Decode one JSON float without accepting finite-token overflow."""

    value = float(text)
    if not math.isfinite(value):
        raise ValueError(f"non-finite JSON number {text}")
    return value


def _is_finite_json_number(value: Any) -> bool:
    """Accept arbitrary-size JSON integers and finite floats, but not booleans."""

    return type(value) is int or (type(value) is float and math.isfinite(value))


@dataclass(frozen=True)
class TrajectoryDecision:
    """One deterministic record-level trajectory-pair decision."""

    action: str
    classification: str
    reason_codes: tuple[str, ...]
    record: dict[str, Any] | None
    shared_goal: bool | None = None
    overlap: dict[str, Any] | None = None
    changed_fields: tuple[str, ...] = ()
    pair_validation_errors: tuple[str, ...] | None = None
    side_validation_errors: dict[str, tuple[str, ...]] | None = None


@dataclass(frozen=True)
class CurationRun:
    """Curated records, manifest entries, and aggregate counts for one source."""

    records: tuple[dict[str, Any], ...]
    manifest: tuple[dict[str, Any], ...]
    summary: dict[str, Any]


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _is_pair_candidate(record: Any) -> bool:
    return isinstance(record, dict) and ("chosen" in record or "rejected" in record)


def _is_same_state_pair(record: dict[str, Any]) -> bool:
    """Whether both sides carry the Fable ``state``/``proposed_action`` schema."""

    sides = (record.get("chosen"), record.get("rejected"))
    return all(
        isinstance(side, dict)
        and all(isinstance(side.get(field_name), dict) for field_name in SAME_STATE_FIELDS)
        for side in sides
    )


def _steps(side: Any) -> list[Any] | None:
    if not isinstance(side, dict):
        return None
    steps = side.get("steps")
    return steps if isinstance(steps, list) else None


def _pair_envelope_validation_errors(record: dict[str, Any]) -> tuple[str, ...]:
    """Return errors for the trajectory-pair fields outside its two arms."""

    errors: list[str] = []
    for field_name in ("id", "outcome"):
        value = record.get(field_name)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"pair: {field_name} must be a non-empty string")
    for field_name in ("reward", "meta"):
        if not isinstance(record.get(field_name), dict):
            errors.append(f"pair: {field_name} must be an object")
    if "critique" in record and (
        not isinstance(record["critique"], str) or not record["critique"].strip()
    ):
        errors.append("pair: critique must be a non-empty string when present")
    return tuple(errors)


def _step_number_errors(side: dict[str, Any], side_name: str) -> tuple[str, ...]:
    """Require exact, one-based step ordinals without bool-as-int coercion."""

    steps = side.get("steps")
    if not isinstance(steps, list):
        return ()
    errors: list[str] = []
    for index, step in enumerate(steps, 1):
        if not isinstance(step, dict):
            continue
        ordinal = step.get("n")
        if type(ordinal) is not int or ordinal != index:
            errors.append(f"{side_name} step {index - 1}: n must be the integer {index}")
    return tuple(errors)


def _side_episode_validation_errors(
    record: dict[str, Any],
) -> dict[str, tuple[str, ...]]:
    """Return canonical episode-shape errors for each preference side."""

    found: dict[str, tuple[str, ...]] = {}
    for side_name in ("chosen", "rejected"):
        side = record.get(side_name)
        if not isinstance(side, dict):
            continue
        errors = check_episode(
            side,
            side_name,
            require_goal=False,
            forbid_hidden_thought=True,
        )
        errors.extend(_step_number_errors(side, side_name))
        if all(key in side for key in THALAMIC_CORE_KEYS):
            errors.append(f"{side_name}: Thalamic trajectory side is not an episode")
        if errors:
            found[side_name] = tuple(errors)
    return found


def classify_pair_schema(record: Any) -> str:
    """Route one record to the lane that owns it."""

    if not isinstance(record, dict):
        return "not_an_object"
    if not _is_pair_candidate(record):
        return "non_preference_record"
    if not all(isinstance(record.get(side), dict) for side in ("chosen", "rejected")):
        return "sides_not_objects"
    if _is_same_state_pair(record):
        return "same_state_pair"
    if _pair_envelope_validation_errors(record) or _side_episode_validation_errors(record):
        return "malformed_trajectory_pair"
    return "trajectory_pair"


def _mask_branch_labels(value: Any) -> Any:
    if isinstance(value, str):
        return BRANCH_LABEL_RE.sub(BRANCH_LABEL_MASK, value)
    if isinstance(value, dict):
        return {key: _mask_branch_labels(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_mask_branch_labels(item) for item in value]
    return value


def first_step_differs_by_branch_label_only(
    chosen_steps: list[Any], rejected_steps: list[Any]
) -> bool:
    """Whether step 1 matches once the words ``chosen``/``rejected`` are masked."""

    if not chosen_steps or not rejected_steps:
        return False
    left, right = chosen_steps[0], rejected_steps[0]
    if canonical_json(left) == canonical_json(right):
        return False
    return canonical_json(_mask_branch_labels(left)) == canonical_json(_mask_branch_labels(right))


def _field_has_validation_error(
    errors: dict[str, tuple[str, ...]], side_name: str, field_name: str
) -> bool:
    marker = f"{side_name}: {field_name}"
    return any(error.startswith(marker) for error in errors.get(side_name, ()))


def _side_field_failures(record: dict[str, Any], errors: dict[str, tuple[str, ...]]) -> list[str]:
    """Reject reasons for missing or non-divergent ``outcome`` / ``reward``."""

    failures: list[str] = []
    for name, missing, invalid, not_divergent in (
        (
            "outcome",
            REASON_OUTCOME_MISSING,
            REASON_OUTCOME_INVALID,
            REASON_OUTCOME_NOT_DIVERGENT,
        ),
        (
            "reward",
            REASON_REWARD_MISSING,
            REASON_REWARD_INVALID,
            REASON_REWARD_NOT_DIVERGENT,
        ),
    ):
        chosen = record["chosen"].get(name)
        rejected = record["rejected"].get(name)
        if chosen is None or rejected is None:
            failures.append(missing)
        elif any(
            _field_has_validation_error(errors, side_name, name)
            for side_name in ("chosen", "rejected")
        ):
            failures.append(invalid)
        elif canonical_json(chosen) == canonical_json(rejected):
            failures.append(not_divergent)
    return failures


def _preference_direction_failures(record: dict[str, Any]) -> list[str]:
    """Bind side labels and pair-level directional evidence to one ordering."""

    expected = (("chosen", True), ("rejected", False))
    for side_name, required_success in expected:
        side = record[side_name]
        reward = side.get("reward") if isinstance(side, dict) else None
        success = reward.get("success") if isinstance(reward, dict) else None
        if success is not required_success:
            return [REASON_PREFERENCE_DIRECTION_INVALID]

    pair_reward = record.get("reward")
    if not isinstance(pair_reward, dict):
        return []
    if "success" in pair_reward and pair_reward["success"] is not True:
        return [REASON_PREFERENCE_DIRECTION_INVALID]
    for field_name in ("preference_margin", "delta"):
        if field_name not in pair_reward:
            continue
        value = pair_reward[field_name]
        if not _is_finite_json_number(value) or value <= 0:
            return [REASON_PREFERENCE_DIRECTION_INVALID]
    if "same_goal" in pair_reward:
        same_goal = pair_reward["same_goal"]
        if not _is_finite_json_number(same_goal) or same_goal != 1.0:
            return [REASON_PREFERENCE_DIRECTION_INVALID]
    return []


def gate_failures(record: dict[str, Any]) -> tuple[str, ...]:
    """Return every reason a well-shaped trajectory pair fails the gate.

    ``record`` must have object-valued sides. Reasons accumulate in a fixed
    order so manifests are byte-stable across runs. Step-dependent checks are
    skipped when the steps are unsafe to inspect, but independent outcome and
    reward findings are still reported in the same pass.
    """

    failures: list[str] = []
    ok, goal_reason = shared_preference_goal(record)
    if not ok:
        # Sides are known objects here, so a goal failure is always a goal code;
        # the side-shape reason is mapped back to this lane's vocabulary anyway.
        failures.append(goal_reason if goal_reason in GOAL_REASONS else REASON_SIDES_NOT_OBJECTS)

    pair_errors = _pair_envelope_validation_errors(record)
    if pair_errors:
        failures.append(REASON_PAIR_ENVELOPE_INVALID)

    side_errors = _side_episode_validation_errors(record)
    if side_errors:
        failures.append(REASON_SIDE_EPISODE_INVALID)

    chosen_steps = _steps(record.get("chosen"))
    rejected_steps = _steps(record.get("rejected"))
    if chosen_steps is None or rejected_steps is None:
        failures.append(REASON_STEPS_INVALID)
    elif not chosen_steps or not rejected_steps:
        failures.append(REASON_STEPS_EMPTY)
    elif any(
        error.startswith((f"{side_name}: steps", f"{side_name} step "))
        for side_name, errors in side_errors.items()
        for error in errors
    ):
        failures.append(REASON_STEPS_INVALID)
    else:
        if canonical_json(chosen_steps) == canonical_json(rejected_steps):
            failures.append(REASON_PAIR_IDENTICAL)
        overlap = prefix_overlap(record["chosen"], record["rejected"])
        if not overlap["shared_steps"]:
            failures.append(REASON_PREFIX_ABSENT)
            if first_step_differs_by_branch_label_only(chosen_steps, rejected_steps):
                failures.append(REASON_BRANCH_LABEL_ONLY)

    failures.extend(_side_field_failures(record, side_errors))
    failures.extend(_preference_direction_failures(record))
    return tuple(failures)


def pair_passes_gate(record: Any) -> bool:
    """Whether ``record`` is a trajectory pair that satisfies the gate."""

    return classify_pair_schema(record) == "trajectory_pair" and not gate_failures(record)


def _normalize_goal_whitespace(record: dict[str, Any]) -> dict[str, Any] | None:
    """Collapse goal whitespace when that is the only goal difference.

    Applied only when at least two goal strings are present, they are not all
    byte-identical, and they are all identical after whitespace normalization.
    The repair rewrites nothing else and invents no goal text.
    """

    present: list[tuple[tuple[str, ...], str]] = []
    for path in GOAL_LOCATIONS:
        owner = _goal_owner(record, path)
        if owner is None:
            continue
        value = owner.get(path[-1])
        if isinstance(value, str):
            present.append((path, value))

    if len(present) < 2:
        return None
    values = [value for _path, value in present]
    normalized = {" ".join(value.split()) for value in values}
    if len(set(values)) == 1 or len(normalized) != 1:
        return None
    canonical_goal = normalized.pop()
    if not canonical_goal:
        return None

    repaired = copy.deepcopy(record)
    for path, _value in present:
        owner = _goal_owner(repaired, path)
        if owner is not None:
            owner[path[-1]] = canonical_goal
    return repaired


def _goal_owner(record: dict[str, Any], path: tuple[str, ...]) -> dict[str, Any] | None:
    owner: Any = record
    for key in path[:-1]:
        owner = owner.get(key) if isinstance(owner, dict) else None
    return owner if isinstance(owner, dict) else None


def _changed_top_level_fields(source: dict[str, Any], curated: dict[str, Any]) -> tuple[str, ...]:
    """Top-level keys whose canonical value a repair changed."""

    return tuple(
        key
        for key in sorted(set(source) | set(curated))
        if canonical_json(source.get(key)) != canonical_json(curated.get(key))
    )


def curate_trajectory_pair(record: Any) -> TrajectoryDecision:
    """Curate one record without mutating it."""

    schema = classify_pair_schema(record)
    if schema == "not_an_object":
        return TrajectoryDecision(
            action=ACTION_EXCLUDED,
            classification="malformed_trajectory_pair",
            reason_codes=(REASON_RECORD_NOT_OBJECT,),
            record=None,
        )
    if schema == "non_preference_record":
        return TrajectoryDecision(
            action=ACTION_SKIPPED,
            classification="non_preference_record",
            reason_codes=(REASON_NOT_A_PAIR,),
            record=None,
        )
    if schema == "sides_not_objects":
        return TrajectoryDecision(
            action=ACTION_EXCLUDED,
            classification="malformed_trajectory_pair",
            reason_codes=(REASON_SIDES_NOT_OBJECTS,),
            record=None,
        )
    if schema == "same_state_pair":
        # Fable FFPC pairs belong to curate_preferences. Skipping them keeps the
        # two lanes' retain rates on separate denominators.
        return TrajectoryDecision(
            action=ACTION_SKIPPED,
            classification="same_state_pair_out_of_scope",
            reason_codes=(REASON_SAME_STATE_SCHEMA,),
            record=None,
        )

    if schema == "malformed_trajectory_pair":
        pair_errors = _pair_envelope_validation_errors(record)
        side_errors = _side_episode_validation_errors(record)
        return TrajectoryDecision(
            action=ACTION_EXCLUDED,
            classification="malformed_trajectory_pair",
            reason_codes=gate_failures(record),
            record=None,
            shared_goal=shared_preference_goal(record)[0],
            overlap=prefix_overlap(record.get("chosen"), record.get("rejected")),
            pair_validation_errors=pair_errors or None,
            side_validation_errors=side_errors,
        )

    repairs: list[str] = []
    curated, removed_thoughts = strip_hidden_thought_keys(record)
    if removed_thoughts:
        repairs.append(REASON_THOUGHT_REMOVED)

    normalized = _normalize_goal_whitespace(curated)
    if normalized is not None:
        curated = normalized
        repairs.append(REASON_GOAL_WHITESPACE_NORMALIZED)

    failures = gate_failures(curated)
    pair_errors = _pair_envelope_validation_errors(curated)
    side_errors = _side_episode_validation_errors(curated)
    shared_goal, _ = shared_preference_goal(curated)
    overlap = prefix_overlap(curated.get("chosen"), curated.get("rejected"))
    if failures:
        return TrajectoryDecision(
            action=ACTION_EXCLUDED,
            classification="unsupported_trajectory_pair",
            reason_codes=failures,
            record=None,
            shared_goal=shared_goal,
            overlap=overlap,
            pair_validation_errors=pair_errors or None,
            side_validation_errors=side_errors or None,
        )

    if repairs:
        return TrajectoryDecision(
            action=ACTION_REPAIRED,
            classification="trajectory_pair_repaired",
            reason_codes=tuple(repairs) + (REASON_GATE_PASSED,),
            record=curated,
            shared_goal=shared_goal,
            overlap=overlap,
            changed_fields=_changed_top_level_fields(record, curated),
        )
    return TrajectoryDecision(
        action=ACTION_RETAINED,
        classification="trajectory_pair_gate_passed",
        reason_codes=(REASON_GATE_PASSED,),
        record=curated,
        shared_goal=shared_goal,
        overlap=overlap,
    )


def _source_files(source: Path) -> tuple[Path, ...]:
    if source.is_file():
        if source.suffix != ".jsonl":
            raise TrajectoryCurationError(f"source file must be JSONL: {source}")
        return (source,)
    if source.is_dir():
        files = tuple(sorted(source.rglob("*.jsonl")))
        if not files:
            raise TrajectoryCurationError(f"no JSONL files under source: {source}")
        return files
    raise TrajectoryCurationError(f"source does not exist: {source}")


def _relative_source_path(source: Path, path: Path) -> str:
    if source.is_dir():
        return path.relative_to(source).as_posix()
    return path.name


def curate_source(source: Path) -> CurationRun:
    """Read and classify every record under ``source`` without writing."""

    source = Path(source)
    output_records: list[dict[str, Any]] = []
    manifest: list[dict[str, Any]] = []
    actions: Counter[str] = Counter()
    classifications: Counter[str] = Counter()
    reasons: Counter[str] = Counter()
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
                raise TrajectoryCurationError(
                    f"{relative_path}:{line_number}: invalid UTF-8: {exc}"
                ) from exc
            try:
                # ``parse_constant`` refuses explicit NaN/Infinity tokens.
                # ``parse_float`` additionally refuses finite-looking JSON
                # numbers such as ``1e999`` that overflow Python's float and
                # would otherwise reappear as an invalid Infinity token.
                record = json.loads(
                    text,
                    parse_constant=reject_json_constant,
                    parse_float=_parse_finite_json_float,
                )
            except (json.JSONDecodeError, ValueError) as exc:
                raise TrajectoryCurationError(
                    f"{relative_path}:{line_number}: invalid JSON: {exc}"
                ) from exc

            decision = curate_trajectory_pair(record)
            actions[decision.action] += 1
            classifications[decision.classification] += 1
            reasons.update(decision.reason_codes)

            output_hash = None
            output_id = None
            if decision.record is not None:
                if not pair_passes_gate(decision.record):
                    raise TrajectoryCurationError(
                        "internal error: emitted a pair that fails the gate at "
                        f"{relative_path}:{line_number}"
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
                    "source_record_id": record.get("id") if isinstance(record, dict) else None,
                    "transform": {
                        "name": TRANSFORM_NAME,
                        "version": TRANSFORM_VERSION,
                    },
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
                    "output_id": output_id,
                    "output_sha256": output_hash,
                }
            )

    considered = actions[ACTION_RETAINED] + actions[ACTION_REPAIRED] + actions[ACTION_EXCLUDED]
    retained = actions[ACTION_RETAINED] + actions[ACTION_REPAIRED]
    summary = {
        "transform": {"name": TRANSFORM_NAME, "version": TRANSFORM_VERSION},
        "source": str(source),
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


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan = subparsers.add_parser("scan", help="classify pairs without writing")
    scan.add_argument("source", type=Path)
    scan.add_argument("--json", action="store_true", help="emit summary and decisions as JSON")

    curate = subparsers.add_parser("curate", help="write gate-passing pairs and a manifest")
    curate.add_argument("source", type=Path)
    curate.add_argument("--output", type=Path, required=True)
    curate.add_argument("--manifest", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.command == "curate":
            _reject_raw_destination(args.output, "output")
            _reject_raw_destination(args.manifest, "manifest")
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
        print(f"trajectory preference curation failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
