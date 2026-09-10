#!/usr/bin/env python3
"""Record-level measurements used by the corpus training audit.

This module classifies read-only record views, preference context, and reward
shapes. Observable-decision and hidden-reasoning traversal live in
``training_audit_reasoning``; corpus aggregation and report policy remain in
``training_audit`` and ``training_audit_report``.
"""

from __future__ import annotations

import sys
from collections.abc import Callable
from typing import Any, NamedTuple

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("training_audit_record")
    from . import training_audit_reasoning as _reasoning
    from .exact_json import dumps_exact_json
    from .quality_gate_identity import canonical_numeric_value
    from .validate_run import episode_like
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "training_audit_record"
    )
    import training_audit_reasoning as _reasoning
    from exact_json import dumps_exact_json
    from quality_gate_identity import canonical_numeric_value
    from validate_run import episode_like


CURATED_FORBIDDEN_REASONING_KEYS = _reasoning.CURATED_FORBIDDEN_REASONING_KEYS

_VIEW_PATHS = {
    "thalamic": (("record", ()),),
    "preference": (("chosen", ("chosen",)), ("rejected", ("rejected",))),
    "bridge_pair": (("language_view.trajectory", ("language_view", "trajectory")),),
}
_AGENTIC_EPISODE_KEYS = frozenset(("goal", "outcome", "reward"))


class PreferencePurityReaders(NamedTuple):
    """Live facade seams used to classify and compare preference pairs."""

    episode_check: Callable[[Any], bool]
    episode_purity: Callable[[Any, Any, Any], dict[str, Any]]
    thalamic_purity: Callable[[Any, Any], dict[str, Any]]


def canonical_blob(value):
    return dumps_exact_json(value, sort_keys=True, ensure_ascii=False)


def dict_field(value, key):
    """Return a nested mapping, treating malformed values as absent."""
    return _reasoning.dict_field(value, key)


def _nested_view(obj, keys):
    if not keys:
        return obj
    value = obj.get(keys[0])
    for key in keys[1:]:
        value = value.get(key) if isinstance(value, dict) else None
    return value if isinstance(value, dict) else None


def thalamic_views(obj, kind):
    for view_path, keys in _VIEW_PATHS.get(kind, ()):
        value = _nested_view(obj, keys)
        if not keys or value is not None:
            yield view_path, value


def _embedded_agentic_episode(trajectory):
    executed_action = dict_field(trajectory, "executed_action")
    has_episode_shape = "steps" in executed_action or _AGENTIC_EPISODE_KEYS <= executed_action.keys()
    return executed_action if has_episode_shape else None


def wrapped_agentic_episodes(obj, kind, *, view_reader=thalamic_views):
    """Yield coding episodes embedded in any supported Thalamic view."""
    for view_path, trajectory in view_reader(obj, kind):
        episode = _embedded_agentic_episode(trajectory)
        if episode is None:
            continue
        path = "executed_action" if view_path == "record" else f"{view_path}.executed_action"
        yield path, episode


def reward_shape_type(value):
    if isinstance(value, dict):
        return "value-object" if isinstance(value.get("value"), (int, float)) else "object"
    if isinstance(value, list):
        return "array"
    if isinstance(value, float):
        return "float"
    return type(value).__name__


def reward_shape(value, *, shape_type=reward_shape_type):
    if not isinstance(value, dict):
        return shape_type(value)
    return "|".join(f"{key}:{shape_type(item)}" for key, item in sorted(value.items()))


def thalamic_context_purity(chosen, rejected, *, canonicalize=canonical_numeric_value):
    valid_context = bool(chosen and rejected) and all(
        isinstance(side.get(key), dict)
        for side in (chosen, rejected)
        for key in ("state", "proposed_action")
    )
    same_state = valid_context and (
        canonicalize(chosen["state"]) == canonicalize(rejected["state"])
    )
    same_proposal = valid_context and (
        canonicalize(chosen["proposed_action"])
        == canonicalize(rejected["proposed_action"])
    )
    return {
        "episode_pair": False,
        "pure": same_state and same_proposal,
        "same_state": same_state,
        "same_proposal": same_proposal,
        "same_goal": None,
    }


def normalized_goals(raw_goals):
    normalized = []
    for value in raw_goals:
        if value is None:
            continue
        if not isinstance(value, str) or not value.strip():
            return []
        normalized.append(" ".join(value.split()))
    return normalized


def episode_context_purity(obj, chosen, rejected, *, normalize_goals=normalized_goals):
    raw_goals = (
        obj.get("goal"),
        chosen.get("goal") if isinstance(chosen, dict) else None,
        rejected.get("goal") if isinstance(rejected, dict) else None,
    )
    normalized_goals = normalize_goals(raw_goals)
    outer_goal = raw_goals[0]
    has_outer_goal = isinstance(outer_goal, str) and bool(outer_goal.strip())
    complete_pair = bool(normalized_goals) if has_outer_goal else len(normalized_goals) == 2
    same_goal = complete_pair and len(set(normalized_goals)) == 1
    return {
        "episode_pair": True,
        "pure": same_goal,
        "same_state": None,
        "same_proposal": None,
        "same_goal": same_goal,
    }


def preference_context_purity(
    obj,
    chosen,
    rejected,
    readers=None,
):
    """Return the applicable DPO context invariant for a preference pair."""
    readers = readers or PreferencePurityReaders(
        episode_like,
        episode_context_purity,
        thalamic_context_purity,
    )
    if readers.episode_check(chosen) or readers.episode_check(rejected):
        return readers.episode_purity(obj, chosen, rejected)
    return readers.thalamic_purity(chosen, rejected)


AgenticTurnReaders = _reasoning.AgenticTurnReaders
list_field = _reasoning.list_field
preference_turns = _reasoning.preference_turns
coordination_turns = _reasoning.coordination_turns
has_observable_decision_basis = _reasoning.has_observable_decision_basis
is_hidden_thought_key = _reasoning.is_hidden_thought_key
hidden_thought_paths = _reasoning.hidden_thought_paths


def agentic_turns(obj, kind, readers=None):
    readers = readers or AgenticTurnReaders(
        list_field,
        preference_turns,
        coordination_turns,
        wrapped_agentic_episodes,
    )
    yield from _reasoning.agentic_turns(obj, kind, readers)


# Preserve the original helper spellings for existing direct callers.
_reward_shape_type = reward_shape_type
_normalized_goals = normalized_goals
_thalamic_context_purity = thalamic_context_purity
_episode_context_purity = episode_context_purity
_list_field = list_field
_preference_turns = preference_turns
_coordination_turns = coordination_turns


if __package__:
    _expose_package_sibling(__name__)
