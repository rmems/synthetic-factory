#!/usr/bin/env python3
"""Trajectory-preference routing and the fail-closed compatible gate core.

Split out of ``compose_curated.py`` by responsibility: classify a preference
pair's side families, curate each episode side through the coding lane, and
apply the reviewed PR #93 trajectory gate (or its fail-closed compatible core
until that sibling module is stacked).  Goal repair lives in
``compose_trajectory_goals`` and the compatible gate core in
``compose_trajectory_gate``; both are re-exported here so ``compose_curated``
keeps one trajectory surface.
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path
from typing import Any, Mapping

if __package__:
    from . import compose_trajectory_gate as _gate_module
    from . import compose_trajectory_goals as _goals_module
    from . import curate_agentic, curate_coding
    from .compose_contract import (
        ACTION_NOT_APPLICABLE,
        PREFERENCE_CANDIDATE_KEYS,
        _canonical_sha256,
    )
    from .record_kind import PREFERENCE_SIDE_KINDS
else:
    _PIPELINES = Path(__file__).resolve().parent
    if str(_PIPELINES) not in sys.path:
        sys.path.insert(0, str(_PIPELINES))
    import compose_trajectory_gate as _gate_module
    import compose_trajectory_goals as _goals_module
    import curate_agentic
    import curate_coding
    from compose_contract import (
        ACTION_NOT_APPLICABLE,
        PREFERENCE_CANDIDATE_KEYS,
        _canonical_sha256,
    )
    from record_kind import PREFERENCE_SIDE_KINDS

_normalize_trajectory_goal_whitespace = _goals_module.normalize_trajectory_goal_whitespace
_present_trajectory_goals = _goals_module.present_trajectory_goals
_trajectory_goal_owner = _goals_module.trajectory_goal_owner
_trajectory_side_validation_errors = _goals_module.trajectory_side_validation_errors
_whitespace_only_goal = _goals_module.whitespace_only_goal
_TRAJECTORY_DIVERGENCE_FIELDS = _gate_module.TRAJECTORY_DIVERGENCE_FIELDS
_compat_trajectory_preference = _gate_module.compat_trajectory_preference
_trajectory_divergence_reasons = _gate_module.trajectory_divergence_reasons
_trajectory_gate_passed = _gate_module.trajectory_gate_passed
_trajectory_step_reasons = _gate_module.trajectory_step_reasons
_trajectory_step_shape_reason = _gate_module.trajectory_step_shape_reason
_trajectory_steps = _gate_module.trajectory_steps

__all__ = (
    "_TRAJECTORY_DIVERGENCE_FIELDS",
    "_compat_trajectory_preference",
    "_curate_one_trajectory_side",
    "_curate_trajectory_sides",
    "_is_same_state_pair",
    "_mixed_preference_families",
    "_normalize_trajectory_goal_whitespace",
    "_present_trajectory_goals",
    "_strip_hidden_only_side",
    "_trajectory_divergence_reasons",
    "_trajectory_gate_passed",
    "_trajectory_goal_owner",
    "_trajectory_side_needs_coding",
    "_trajectory_side_validation_errors",
    "_trajectory_step_reasons",
    "_trajectory_step_shape_reason",
    "_trajectory_steps",
    "_whitespace_only_goal",
    "is_bridge_record",
    "is_episode_record",
    "is_preference_record",
)


def is_bridge_record(record: Mapping[str, Any]) -> bool:
    """Mirror the shape gate ``curate_bridge.curate_record`` applies itself."""

    return (
        isinstance(record, Mapping)
        and "language_view" in record
        and isinstance(record.get("spike_events"), list)
    )


def is_preference_record(record: Mapping[str, Any]) -> bool:
    """Mirror the candidate gate ``curate_preferences`` applies to a corpus."""

    return isinstance(record, Mapping) and any(key in record for key in PREFERENCE_CANDIDATE_KEYS)


def is_episode_record(record: Mapping[str, Any]) -> bool:
    """Mirror the shape gate ``curate_coding.curate_episode`` applies itself.

    A retained Thalamic wrap keeps its coding episode under
    ``executed_action``, so its steps live one level down.  ``curate_coding``
    supports that layout through ``steps_path``; routing only on a top-level
    ``steps`` array would send a repairable wrap straight to the strict audit
    with its hidden reasoning and ungrounded ``decision_basis`` intact.
    """

    return isinstance(record, Mapping) and curate_coding.steps_path(dict(record)) is not None


def _mixed_preference_families(side_kinds: tuple[str, str]) -> bool:
    """Whether two recognized preference-side families disagree."""

    return (
        all(kind in PREFERENCE_SIDE_KINDS for kind in side_kinds) and side_kinds[0] != side_kinds[1]
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
            isinstance(side.get(field_name), Mapping) for field_name in ("state", "proposed_action")
        )
        for side in sides
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
        "reason_codes": ([curate_agentic.REASON_THOUGHT_REMOVED] if removed else []),
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
