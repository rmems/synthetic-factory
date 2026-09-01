#!/usr/bin/env python3
"""Trajectory-preference routing and the fail-closed compatible gate core.

Split out of ``compose_curated.py`` by responsibility: classify a preference
pair's side families, curate each episode side through the coding lane, and
apply the reviewed PR #93 trajectory gate (or its fail-closed compatible core
until that sibling module is stacked).
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path
from typing import Any, Mapping

if __package__:
    from . import curate_agentic, curate_coding
    from .compose_contract import (
        ACTION_EXCLUDED,
        ACTION_NOT_APPLICABLE,
        ACTION_RETAINED,
        PREFERENCE_CANDIDATE_KEYS,
        REASON_TRAJECTORY_GATE_PASSED,
        REASON_TRAJECTORY_GOAL_NORMALIZED,
        REASON_TRAJECTORY_IDENTICAL,
        REASON_TRAJECTORY_OUTCOME_MISSING,
        REASON_TRAJECTORY_OUTCOME_NOT_DIVERGENT,
        REASON_TRAJECTORY_PREFIX_ABSENT,
        REASON_TRAJECTORY_REWARD_MISSING,
        REASON_TRAJECTORY_REWARD_NOT_DIVERGENT,
        REASON_TRAJECTORY_SIDE_INVALID,
        REASON_TRAJECTORY_STEPS_EMPTY,
        REASON_TRAJECTORY_STEPS_INVALID,
        TRAJECTORY_GOAL_LOCATIONS,
        _TrajectoryPreferenceDecision,
        _canonical_sha256,
        canonical_json,
    )
    from .record_kind import PREFERENCE_SIDE_KINDS
    from .trajectory_pair_gate import preference_direction_failures
    from .validate_run import THALAMIC_CORE_KEYS, check_episode
else:
    _PIPELINES = Path(__file__).resolve().parent
    if str(_PIPELINES) not in sys.path:
        sys.path.insert(0, str(_PIPELINES))
    import curate_agentic
    import curate_coding
    from compose_contract import (
        ACTION_EXCLUDED,
        ACTION_NOT_APPLICABLE,
        ACTION_RETAINED,
        PREFERENCE_CANDIDATE_KEYS,
        REASON_TRAJECTORY_GATE_PASSED,
        REASON_TRAJECTORY_GOAL_NORMALIZED,
        REASON_TRAJECTORY_IDENTICAL,
        REASON_TRAJECTORY_OUTCOME_MISSING,
        REASON_TRAJECTORY_OUTCOME_NOT_DIVERGENT,
        REASON_TRAJECTORY_PREFIX_ABSENT,
        REASON_TRAJECTORY_REWARD_MISSING,
        REASON_TRAJECTORY_REWARD_NOT_DIVERGENT,
        REASON_TRAJECTORY_SIDE_INVALID,
        REASON_TRAJECTORY_STEPS_EMPTY,
        REASON_TRAJECTORY_STEPS_INVALID,
        TRAJECTORY_GOAL_LOCATIONS,
        _TrajectoryPreferenceDecision,
        _canonical_sha256,
        canonical_json,
    )
    from record_kind import PREFERENCE_SIDE_KINDS
    from trajectory_pair_gate import preference_direction_failures
    from validate_run import THALAMIC_CORE_KEYS, check_episode

def is_bridge_record(record: Mapping[str, Any]) -> bool:
    """Mirror the shape gate ``curate_bridge.curate_record`` applies itself."""

    return (
        isinstance(record, Mapping)
        and "language_view" in record
        and isinstance(record.get("spike_events"), list)
    )


def is_preference_record(record: Mapping[str, Any]) -> bool:
    """Mirror the candidate gate ``curate_preferences`` applies to a corpus."""

    return isinstance(record, Mapping) and any(
        key in record for key in PREFERENCE_CANDIDATE_KEYS
    )


def is_episode_record(record: Mapping[str, Any]) -> bool:
    """Mirror the shape gate ``curate_coding.curate_episode`` applies itself.

    A retained Thalamic wrap keeps its coding episode under
    ``executed_action``, so its steps live one level down.  ``curate_coding``
    supports that layout through ``steps_path``; routing only on a top-level
    ``steps`` array would send a repairable wrap straight to the strict audit
    with its hidden reasoning and ungrounded ``decision_basis`` intact.
    """

    return (
        isinstance(record, Mapping)
        and curate_coding.steps_path(dict(record)) is not None
    )


def _mixed_preference_families(side_kinds: tuple[str, str]) -> bool:
    """Whether two recognized preference-side families disagree."""

    return (
        all(kind in PREFERENCE_SIDE_KINDS for kind in side_kinds)
        and side_kinds[0] != side_kinds[1]
    )


def _is_same_state_pair(record: Mapping[str, Any]) -> bool:
    """Match PR #93's precedence for Fable same-context preference pairs.

    A side can carry episode fields in addition to ``state`` and
    ``proposed_action``.  Those extra fields must not move the pair into the
    trajectory lane and bypass its state/proposal equality contract.
    """

    sides = (record.get("chosen"), record.get("rejected"))
    return all(
        isinstance(side, Mapping)
        and all(
            isinstance(side.get(field_name), Mapping)
            for field_name in ("state", "proposed_action")
        )
        for side in sides
    )


def _trajectory_side_validation_errors(
    record: Mapping[str, Any],
) -> dict[str, tuple[str, ...]]:
    """Run the canonical episode validator over each trajectory-preference side."""

    found: dict[str, tuple[str, ...]] = {}
    for side_name in ("chosen", "rejected"):
        side = record.get(side_name)
        if not isinstance(side, dict):
            continue
        errors = check_episode(side, side_name, require_goal=False)
        if all(key in side for key in THALAMIC_CORE_KEYS):
            errors.append(f"{side_name}: Thalamic trajectory side is not an episode")
        if errors:
            found[side_name] = tuple(errors)
    return found


def _trajectory_goal_owner(
    record: dict[str, Any], path: tuple[str, ...]
) -> dict[str, Any] | None:
    owner: Any = record
    for key in path[:-1]:
        owner = owner.get(key) if isinstance(owner, dict) else None
    return owner if isinstance(owner, dict) else None


def _present_trajectory_goals(
    record: dict[str, Any],
) -> list[tuple[tuple[str, ...], str]]:
    """Every goal location this record actually carries as a string."""

    present: list[tuple[tuple[str, ...], str]] = []
    for path in TRAJECTORY_GOAL_LOCATIONS:
        owner = _trajectory_goal_owner(record, path)
        if owner is None:
            continue
        value = owner.get(path[-1])
        if isinstance(value, str):
            present.append((path, value))
    return present


def _whitespace_only_goal(present: list[tuple[tuple[str, ...], str]]) -> str | None:
    """The single canonical goal, when the goals differ only in whitespace.

    ``None`` whenever the repair would invent evidence: fewer than two goals
    to reconcile, goals that already agree, goals that still differ once
    whitespace is collapsed, or a goal that collapses to nothing.
    """

    if len(present) < 2:
        return None
    values = [value for _path, value in present]
    normalized = {" ".join(value.split()) for value in values}
    if len(set(values)) == 1 or len(normalized) != 1:
        return None
    return normalized.pop() or None


def _normalize_trajectory_goal_whitespace(
    record: dict[str, Any],
) -> dict[str, Any] | None:
    """Apply PR #93's evidence-preserving goal whitespace repair."""

    present = _present_trajectory_goals(record)
    canonical_goal = _whitespace_only_goal(present)
    if canonical_goal is None:
        return None

    repaired = copy.deepcopy(record)
    for path, _value in present:
        owner = _trajectory_goal_owner(repaired, path)
        if owner is not None:
            owner[path[-1]] = canonical_goal
    return repaired


_TRAJECTORY_DIVERGENCE_FIELDS = (
    (
        "outcome",
        REASON_TRAJECTORY_OUTCOME_MISSING,
        REASON_TRAJECTORY_OUTCOME_NOT_DIVERGENT,
    ),
    (
        "reward",
        REASON_TRAJECTORY_REWARD_MISSING,
        REASON_TRAJECTORY_REWARD_NOT_DIVERGENT,
    ),
)


def _trajectory_step_reasons(
    chosen: Any, rejected: Any, overlap: Mapping[str, Any]
) -> list[str]:
    """Why the pair's step arrays fail PR #93's gate, in gate order."""

    chosen_steps = chosen.get("steps") if isinstance(chosen, dict) else None
    rejected_steps = rejected.get("steps") if isinstance(rejected, dict) else None
    if not all(isinstance(steps, list) for steps in (chosen_steps, rejected_steps)):
        return [REASON_TRAJECTORY_STEPS_INVALID]
    if not chosen_steps or not rejected_steps:
        return [REASON_TRAJECTORY_STEPS_EMPTY]

    reasons: list[str] = []
    if canonical_json(chosen_steps) == canonical_json(rejected_steps):
        reasons.append(REASON_TRAJECTORY_IDENTICAL)
    if not overlap["shared_steps"]:
        reasons.append(REASON_TRAJECTORY_PREFIX_ABSENT)
    return reasons


def _trajectory_divergence_reasons(chosen: Any, rejected: Any) -> list[str]:
    """Why the pair's outcome and reward evidence fails to diverge."""

    if not isinstance(chosen, dict) or not isinstance(rejected, dict):
        return []

    reasons: list[str] = []
    for field_name, missing_reason, same_reason in _TRAJECTORY_DIVERGENCE_FIELDS:
        if chosen.get(field_name) is None or rejected.get(field_name) is None:
            reasons.append(missing_reason)
        elif canonical_json(chosen[field_name]) == canonical_json(rejected[field_name]):
            reasons.append(same_reason)
    return reasons


def _trajectory_gate_passed(
    curated: dict[str, Any],
    overlap: Mapping[str, Any],
    *,
    removed_thoughts: Any,
    normalized: Any,
) -> _TrajectoryPreferenceDecision:
    """The accepted decision, repaired if the gate had to touch the record."""

    repaired = bool(removed_thoughts) or normalized is not None
    reasons: list[str] = []
    if removed_thoughts:
        reasons.append(curate_agentic.REASON_THOUGHT_REMOVED)
    if normalized is not None:
        reasons.append(REASON_TRAJECTORY_GOAL_NORMALIZED)
    reasons.append(REASON_TRAJECTORY_GATE_PASSED)
    return _TrajectoryPreferenceDecision(
        action="repaired" if repaired else ACTION_RETAINED,
        classification=(
            "trajectory_pair_repaired" if repaired else "trajectory_pair_gate_passed"
        ),
        reason_codes=tuple(reasons),
        record=curated,
        shared_goal=True,
        overlap=overlap,
    )


def _compat_trajectory_preference(
    record: dict[str, Any],
) -> _TrajectoryPreferenceDecision:
    """Enforce PR #93's non-repairing core when its sibling module is absent.

    The sibling owns richer reject diagnostics. This compatibility path keeps
    its acceptance contract and evidence-preserving repairs: valid episode
    sides, one goal, a non-empty shared step prefix, non-identical trajectories,
    divergent outcome and reward evidence, hidden-thought removal, and
    whitespace-only goal normalization.
    """

    curated, removed_thoughts = curate_agentic.strip_hidden_thought_keys(record)
    normalized = _normalize_trajectory_goal_whitespace(curated)
    if normalized is not None:
        curated = normalized

    shared_goal, goal_reason = curate_agentic.shared_preference_goal(curated)
    side_errors = _trajectory_side_validation_errors(curated)
    chosen = curated.get("chosen")
    rejected = curated.get("rejected")
    overlap = curate_agentic.prefix_overlap(chosen, rejected)

    # Collected in gate order: the reason codes are public evidence, so the
    # sequence a reader sees has to stay stable.
    reasons: list[str] = []
    if not shared_goal and goal_reason is not None:
        reasons.append(goal_reason)
    if side_errors:
        reasons.append(REASON_TRAJECTORY_SIDE_INVALID)
    reasons.extend(_trajectory_step_reasons(chosen, rejected, overlap))
    reasons.extend(_trajectory_divergence_reasons(chosen, rejected))
    reasons.extend(preference_direction_failures(curated))

    if reasons:
        return _TrajectoryPreferenceDecision(
            action=ACTION_EXCLUDED,
            classification="unsupported_trajectory_pair",
            reason_codes=tuple(dict.fromkeys(reasons)),
            record=None,
            shared_goal=shared_goal,
            overlap=overlap,
            side_validation_errors=side_errors or None,
        )
    return _trajectory_gate_passed(
        curated,
        overlap,
        removed_thoughts=removed_thoughts,
        normalized=normalized,
    )


def _trajectory_side_needs_coding(side: Any) -> bool:
    """Whether an episode side runs the coding lane before preference checks.

    Every side that carries a step array does — wherever the record keeps it:
    a plain side holds ``steps`` at its root, while a Thalamic wrap embeds the
    coding episode at ``executed_action.steps`` (``curate_coding.steps_path``
    is the one wrap-aware answer). A nonblank ``decision_basis`` is not
    evidence that the basis is *grounded*: ``curate_coding`` derives it from
    the step's visible plan, observation, and tool call and overwrites
    whatever was there, while the later audit only checks that the field is
    nonempty. Skipping a side whose steps already hold some text would let an
    ungrounded value such as "private hunch" survive into a ``training_ready``
    export. The lane is idempotent, so an already-grounded side is retained
    unchanged and only its manifest gains the evidence-source reason.
    """

    if not isinstance(side, dict):
        return False
    return curate_coding.steps_path(side) is not None


def _not_applicable_side_manifest() -> dict[str, Any]:
    return {
        "transform_name": curate_coding.TRANSFORM_NAME,
        "transform_version": curate_coding.TRANSFORM_VERSION,
        "action": ACTION_NOT_APPLICABLE,
        "reason_codes": [],
    }


def _strip_hidden_only_side(side: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Strip hidden reasoning from a side that carries no coding steps.

    A legacy Thalamic side with ``proposed_action.internal_reasoning`` but no
    step array is not a coding episode: routing it through
    ``curate_coding.curate_episode`` can only fail (``coding_steps_not_array``)
    and would exclude an otherwise valid pair. The generic recursive stripper
    removes exactly what the audit refuses while leaving the shape alone.
    """

    cleaned, removed = curate_agentic.strip_hidden_thought_keys(side)
    manifest = {
        "transform_name": curate_agentic.TRANSFORM_NAME,
        "transform_version": curate_agentic.TRANSFORM_VERSION,
        "action": "modified" if removed else ACTION_NOT_APPLICABLE,
        "reason_codes": (
            [curate_agentic.REASON_THOUGHT_REMOVED] if removed else []
        ),
        "hidden_reasoning_fields_removed": removed,
    }
    return cleaned, manifest


def _curate_one_trajectory_side(
    side: dict[str, Any],
    side_name: str,
    *,
    source_path: str,
    source_line: int,
) -> tuple[bool, dict[str, Any] | None, dict[str, Any]]:
    """Return whether curation applies, its result, and its manifest."""

    if _trajectory_side_needs_coding(side):
        curated_side, manifest = curate_coding.curate_episode(
            side,
            source_path=f"{source_path}#{side_name}",
            source_line=source_line,
            source_hash=_canonical_sha256(side),
        )
        detail = copy.deepcopy(manifest)
        detail["transform_name"] = curate_coding.TRANSFORM_NAME
        detail["transform_version"] = curate_coding.TRANSFORM_VERSION
        return True, curated_side, detail
    if isinstance(side, dict) and curate_coding.contains_hidden_reasoning_key(side):
        curated_side, detail = _strip_hidden_only_side(side)
        return True, curated_side, detail
    return False, None, _not_applicable_side_manifest()


def _curate_trajectory_sides(
    record: dict[str, Any],
    *,
    source_path: str,
    source_line: int,
) -> tuple[dict[str, Any] | None, dict[str, dict[str, Any]], list[str], bool]:
    """Migrate repairable episode sides before the trajectory preference gate."""

    curated = copy.deepcopy(record)
    manifests: dict[str, dict[str, Any]] = {}
    reasons: list[str] = []
    changed = False
    failed = False
    for side_name in ("chosen", "rejected"):
        side = curated.get(side_name)
        applicable, curated_side, detail = _curate_one_trajectory_side(
            side,
            side_name,
            source_path=source_path,
            source_line=source_line,
        )
        manifests[side_name] = detail
        if not applicable:
            continue
        reasons.extend(detail.get("reason_codes", []))
        if curated_side is None:
            failed = True
            continue
        changed = changed or curated_side != side
        curated[side_name] = curated_side
    return (
        None if failed else curated,
        manifests,
        list(dict.fromkeys(reasons)),
        changed,
    )
