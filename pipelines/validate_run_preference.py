#!/usr/bin/env python3
"""Preference staging and pair-shape checks for the run validator."""

import sys
from typing import NamedTuple

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling
    _assert_direct_sibling("validate_run_preference")
    from . import validate_run_episode_turns as _validate_run_episode_turns
    from . import validate_run_preference_context as _validate_run_preference_context
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "validate_run_preference"
    )
    import validate_run_episode_turns as _validate_run_episode_turns
    import validate_run_preference_context as _validate_run_preference_context


preference_side_context_anchors = (
    _validate_run_preference_context.preference_side_context_anchors
)


class _SideCheck(NamedTuple):
    """Episode-vs-thalamic dispatch for one preference side."""

    episode_pref: bool
    episode_kwargs: dict
    hooks: object


class _PreferenceCall(NamedTuple):
    """Where/staging/hooks for one preference record."""

    where: str
    factory_staging: bool
    hooks: object


def _normalized_goal(value):
    if not isinstance(value, str):
        return None
    if not value.strip():
        return None
    return " ".join(value.split())


def _preference_goal_values(obj):
    chosen = obj.get("chosen")
    rejected = obj.get("rejected")
    return {
        "goal": obj.get("goal"),
        "chosen.goal": chosen.get("goal") if isinstance(chosen, dict) else None,
        "rejected.goal": rejected.get("goal") if isinstance(rejected, dict) else None,
    }


def _normalized_preference_goals(raw_goals, where):
    normalized = {}
    errors = []
    for path, value in raw_goals.items():
        if value is None:
            continue
        goal = _normalized_goal(value)
        if goal is None:
            errors.append(f"{where}: {path} must be a non-empty string when present")
            continue
        normalized[path] = goal
    return normalized, errors


def _sides_share_no_context(chosen_context, rejected_context):
    if not chosen_context:
        return False
    if not rejected_context:
        return False
    return chosen_context.isdisjoint(rejected_context)


def _preference_context_errors(obj, where):
    chosen = obj.get("chosen")
    rejected = obj.get("rejected")
    if not isinstance(chosen, dict):
        return []
    if not isinstance(rejected, dict):
        return []
    chosen_context = preference_side_context_anchors(chosen)
    rejected_context = preference_side_context_anchors(rejected)
    if not _sides_share_no_context(chosen_context, rejected_context):
        return []
    return [
        f"{where}: preference sides must share observable file, API, "
        "target, or success-criterion context"
    ]


def _missing_inherited_side_goals(raw_goals, normalized):
    if raw_goals["goal"] is not None:
        return False
    if "chosen.goal" not in normalized:
        return True
    return "rejected.goal" not in normalized


def staging_preference_goal_errors(obj, where):
    """Require explicit or inherited agreement on one preference problem."""
    raw_goals = _preference_goal_values(obj)
    normalized, errors = _normalized_preference_goals(raw_goals, where)
    if not normalized:
        return [f"{where}: preference needs a shared non-empty goal"]
    if _missing_inherited_side_goals(raw_goals, normalized):
        errors.append(
            f"{where}: preference needs both side goals when no top-level goal is present"
        )
    if len(set(normalized.values())) > 1:
        errors.append(
            f"{where}: top-level and side goals must describe the same problem"
        )
    return errors + _preference_context_errors(obj, where)


def preference_side_errors(side, label, check):
    """Validate one preference side as an episode or as a ThalamicTrajectory."""
    if not isinstance(side, dict):
        return [f"{label} must be an object"]
    if check.episode_pref:
        return check.hooks.check_episode(side, label, **check.episode_kwargs)
    return check.hooks.check_thalamic(side, label)


def _missing_preference_episode_goal(obj, chosen):
    if "goal" in obj:
        return False
    if not isinstance(chosen, dict):
        return True
    return "goal" not in chosen


def _wrapper_success_must_be_true(reward, factory_staging):
    if not factory_staging:
        return False
    if not isinstance(reward, dict):
        return False
    success = reward.get("success")
    if not isinstance(success, bool):
        return False
    return success is not True


def preference_episode_wrapper_errors(obj, chosen, call):
    """Wrapper-level invariants that only apply to episode preferences."""
    where = call.where
    errs = []
    if _missing_preference_episode_goal(obj, chosen):
        errs.append(f"{where}: preference episode needs a shared or chosen goal")
    errs += call.hooks.require_reward(obj, where)
    if _wrapper_success_must_be_true(obj.get("reward"), call.factory_staging):
        errs.append(f"{where}: preference wrapper reward.success must be true")
    return errs


def _preference_critique_errors(obj, where):
    if _validate_run_episode_turns.nonempty_text(obj.get("critique")):
        return []
    return [f"{where}: preference record needs a non-empty critique"]


def _episode_preference(chosen, rejected, hooks):
    if hooks.episode_like(chosen):
        return True
    return hooks.episode_like(rejected)


def route_preference(obj, where, factory_staging, hooks):
    errs = []
    chosen = obj.get("chosen")
    rejected = obj.get("rejected")
    episode_pref = _episode_preference(chosen, rejected, hooks)
    side_check = _SideCheck(
        episode_pref,
        {
            "require_goal": "goal" not in obj,
            "forbid_hidden_thought": factory_staging,
        },
        hooks,
    )
    errs += preference_side_errors(chosen, f"{where}.chosen", side_check)
    errs += preference_side_errors(rejected, f"{where}.rejected", side_check)
    if episode_pref:
        errs += preference_episode_wrapper_errors(
            obj, chosen, _PreferenceCall(where, factory_staging, hooks)
        )
    return errs + _preference_critique_errors(obj, where)


if __package__:
    _expose_package_sibling(__name__)
