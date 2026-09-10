#!/usr/bin/env python3
"""Record-level measurements used by the corpus training audit.

This module classifies read-only record views, preference context, reward
shapes, and observable/hidden reasoning fields. Corpus aggregation and report
policy remain in ``training_audit`` and ``training_audit_report``.
"""

from __future__ import annotations

import sys

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("training_audit_record")
    from .curate_coding import (
        HIDDEN_REASONING_KEYS,
        HIDDEN_REASONING_PREFIX,
        normalized_key_name,
    )
    from .exact_json import dumps_exact_json
    from .quality_gate_identity import canonical_numeric_value
    from .validate_run import HIDDEN_THOUGHT_KEYS, episode_like
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "training_audit_record"
    )
    from curate_coding import (
        HIDDEN_REASONING_KEYS,
        HIDDEN_REASONING_PREFIX,
        normalized_key_name,
    )
    from exact_json import dumps_exact_json
    from quality_gate_identity import canonical_numeric_value
    from validate_run import HIDDEN_THOUGHT_KEYS, episode_like


CURATED_FORBIDDEN_REASONING_KEYS = HIDDEN_THOUGHT_KEYS | HIDDEN_REASONING_KEYS


def canonical_blob(value):
    return dumps_exact_json(value, sort_keys=True, ensure_ascii=False)


def dict_field(value, key):
    """Return a nested mapping, treating malformed values as absent."""
    if not isinstance(value, dict):
        return {}
    nested = value.get(key)
    return nested if isinstance(nested, dict) else {}


def thalamic_views(obj, kind):
    if kind == "thalamic":
        yield "record", obj
    elif kind == "preference":
        for side in ("chosen", "rejected"):
            value = obj.get(side)
            if isinstance(value, dict):
                yield side, value
    elif kind == "bridge_pair":
        view = obj.get("language_view")
        if isinstance(view, dict) and isinstance(view.get("trajectory"), dict):
            yield "language_view.trajectory", view["trajectory"]


def wrapped_agentic_episodes(obj, kind):
    """Yield coding episodes embedded in any supported Thalamic view."""
    for view_path, trajectory in thalamic_views(obj, kind):
        executed_action = trajectory.get("executed_action")
        if not isinstance(executed_action, dict):
            continue
        if "steps" not in executed_action and not all(
            key in executed_action for key in ("goal", "outcome", "reward")
        ):
            continue
        path = "executed_action" if view_path == "record" else f"{view_path}.executed_action"
        yield path, executed_action


def _reward_shape_type(value):
    if isinstance(value, dict):
        return "value-object" if isinstance(value.get("value"), (int, float)) else "object"
    if isinstance(value, list):
        return "array"
    if isinstance(value, float):
        return "float"
    return type(value).__name__


def reward_shape(value):
    if not isinstance(value, dict):
        return _reward_shape_type(value)
    return "|".join(f"{key}:{_reward_shape_type(item)}" for key, item in sorted(value.items()))


def _thalamic_context_purity(chosen, rejected):
    valid_context = bool(chosen and rejected) and all(
        isinstance(side.get(key), dict)
        for side in (chosen, rejected)
        for key in ("state", "proposed_action")
    )
    same_state = valid_context and (
        canonical_numeric_value(chosen["state"]) == canonical_numeric_value(rejected["state"])
    )
    same_proposal = valid_context and (
        canonical_numeric_value(chosen["proposed_action"])
        == canonical_numeric_value(rejected["proposed_action"])
    )
    return {
        "episode_pair": False,
        "pure": same_state and same_proposal,
        "same_state": same_state,
        "same_proposal": same_proposal,
        "same_goal": None,
    }


def _normalized_goals(raw_goals):
    normalized = []
    for value in raw_goals:
        if value is None:
            continue
        if not isinstance(value, str) or not value.strip():
            return []
        normalized.append(" ".join(value.split()))
    return normalized


def _episode_context_purity(obj, chosen, rejected):
    raw_goals = (
        obj.get("goal"),
        chosen.get("goal") if isinstance(chosen, dict) else None,
        rejected.get("goal") if isinstance(rejected, dict) else None,
    )
    normalized_goals = _normalized_goals(raw_goals)
    outer_goal = raw_goals[0]
    if isinstance(outer_goal, str) and outer_goal.strip():
        same_goal = bool(normalized_goals) and len(set(normalized_goals)) == 1
    else:
        same_goal = len(normalized_goals) == 2 and len(set(normalized_goals)) == 1
    return {
        "episode_pair": True,
        "pure": same_goal,
        "same_state": None,
        "same_proposal": None,
        "same_goal": same_goal,
    }


def preference_context_purity(obj, chosen, rejected):
    """Return the applicable DPO context invariant for a preference pair."""
    if episode_like(chosen) or episode_like(rejected):
        return _episode_context_purity(obj, chosen, rejected)
    return _thalamic_context_purity(chosen, rejected)


def _list_field(value, key):
    items = value.get(key) if isinstance(value, dict) else None
    return items if isinstance(items, list) else ()


def _preference_turns(obj):
    for side_name in ("chosen", "rejected"):
        side = dict_field(obj, side_name)
        if episode_like(side):
            yield from _list_field(side, "steps")


def _coordination_turns(obj):
    for turn in _list_field(obj, "transcript"):
        if isinstance(turn, dict) and "tool_call" in turn:
            yield turn


def agentic_turns(obj, kind):
    """Yield each observable decision turn used by agentic curation."""
    if kind in {"episode", "safety_case"}:
        yield from _list_field(obj, "steps")
    elif kind == "preference":
        yield from _preference_turns(obj)
    elif kind == "multi_agent":
        yield from _coordination_turns(obj)
    for _path, episode in wrapped_agentic_episodes(obj, kind):
        yield from _list_field(episode, "steps")


def has_observable_decision_basis(turn):
    return (
        isinstance(turn, dict)
        and isinstance(turn.get("decision_basis"), str)
        and bool(turn["decision_basis"].strip())
    )


def is_hidden_thought_key(key):
    """Return whether a JSON key names model-private reasoning text."""
    normalized = normalized_key_name(key)
    return normalized in CURATED_FORBIDDEN_REASONING_KEYS or normalized.startswith(
        HIDDEN_REASONING_PREFIX
    )


def hidden_thought_paths(value, path=""):
    """Yield every recursively hidden-reasoning field in one record."""
    if isinstance(value, dict):
        for key, item in value.items():
            child_path = f"{path}.{key}" if path else key
            if is_hidden_thought_key(key):
                yield child_path
            yield from hidden_thought_paths(item, child_path)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from hidden_thought_paths(item, f"{path}[{index}]")


if __package__:
    _expose_package_sibling(__name__)
