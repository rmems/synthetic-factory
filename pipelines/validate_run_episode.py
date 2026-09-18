#!/usr/bin/env python3
"""Episode shape checks for the run validator."""

import sys
from typing import NamedTuple

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling
    _assert_direct_sibling("validate_run_episode")
    from . import validate_run_episode_turns as _validate_run_episode_turns
    from . import validate_run_rewards as _validate_run_rewards
    from . import validate_run_safety as _validate_run_safety
    from . import validate_run_thalamic as _validate_run_thalamic
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "validate_run_episode"
    )
    import validate_run_episode_turns as _validate_run_episode_turns
    import validate_run_rewards as _validate_run_rewards
    import validate_run_safety as _validate_run_safety
    import validate_run_thalamic as _validate_run_thalamic


HIDDEN_THOUGHT_KEYS = _validate_run_episode_turns.HIDDEN_THOUGHT_KEYS
OBSERVABLE_BASIS_RE = _validate_run_episode_turns.OBSERVABLE_BASIS_RE
hidden_thought_paths = _validate_run_episode_turns.hidden_thought_paths
staging_hidden_thought_errors = _validate_run_episode_turns.staging_hidden_thought_errors
staging_tool_turn_errors = _validate_run_episode_turns.staging_tool_turn_errors
_EPISODE_CORE_KEYS = ("steps", "outcome", "reward")


class EpisodeHooks(NamedTuple):
    """Live vocabularies and checkers one episode or coordination check runs under.

    The validate_run facade builds this from its own compatibility names so
    rebinding HIDDEN_THOUGHT_KEYS, OBSERVABLE_BASIS_RE, or the reward/outcome
    helpers keeps flowing through exactly as when the checks lived inline.
    """

    hidden_thought_keys: frozenset
    observable_basis_re: object
    require_reward: object
    nonempty_text_field_errors: object
    terminal_outcome_agrees: object
    thalamic_core_keys: tuple


class EpisodeOptions(NamedTuple):
    """Flags one episode check runs under, bundled to keep call sites small."""

    require_goal: bool = True
    forbid_hidden_thought: bool = False
    enforce_terminal_outcome: bool = False


class _StepCheck(NamedTuple):
    where: str
    index: int
    options: EpisodeOptions
    hooks: EpisodeHooks


def default_hooks():
    """This module's own hooks, read at call time so patches here flow too."""
    return EpisodeHooks(
        HIDDEN_THOUGHT_KEYS,
        OBSERVABLE_BASIS_RE,
        _validate_run_rewards.require_reward,
        _validate_run_safety.nonempty_text_field_errors,
        _validate_run_rewards.terminal_outcome_agrees,
        _validate_run_thalamic.THALAMIC_CORE_KEYS,
    )


def episode_like(obj, core_keys=None):
    """True when an object is a coding/agent episode rather than Thalamic."""
    keys = _validate_run_thalamic.THALAMIC_CORE_KEYS if core_keys is None else core_keys
    if not isinstance(obj, dict):
        return False
    if "steps" not in obj:
        return False
    return not all(key in obj for key in keys)


def _episode_required_keys(require_goal):
    if require_goal:
        return ("goal",) + _EPISODE_CORE_KEYS
    return _EPISODE_CORE_KEYS


def _missing_decision_basis(step, forbid_hidden_thought):
    if "decision_basis" in step:
        return False
    if forbid_hidden_thought:
        return True
    return "thought" not in step


def _episode_step_errors(step, check):
    """Validate one episode step object, including the staged tool-turn gate."""
    label = f"{check.where} step {check.index}"
    if not isinstance(step, dict):
        return [f"{label}: must be an object"]
    errors = [
        f"{label}: missing '{key}'"
        for key in ("tool_call", "observation")
        if key not in step
    ]
    # Existing non-staged records may still use the legacy ``thought``
    # field; retain the audit warning path for those historical runs.
    # Transactional agentic publication always uses the strict branch
    # below and rejects every hidden-reasoning key recursively.
    if _missing_decision_basis(step, check.options.forbid_hidden_thought):
        errors.append(f"{label}: missing 'decision_basis'")
    if check.options.forbid_hidden_thought:
        errors += staging_tool_turn_errors(
            step, label, observable_basis_re=check.hooks.observable_basis_re
        )
    return errors


def _episode_steps_errors(obj, where, options, hooks):
    steps = obj.get("steps")
    if not isinstance(steps, list):
        return [f"{where}: steps must be a non-empty array"]
    if not steps:
        return [f"{where}: steps must be a non-empty array"]
    return [
        error
        for index, step in enumerate(steps)
        for error in _episode_step_errors(
            step, _StepCheck(where, index, options, hooks)
        )
    ]


def _reward_success(obj):
    reward = obj.get("reward")
    if isinstance(reward, dict):
        return reward.get("success")
    return None


def _terminal_outcome_errors(obj, where, options, hooks):
    if not options.enforce_terminal_outcome:
        return []
    success = _reward_success(obj)
    if not isinstance(success, bool):
        return []
    if hooks.terminal_outcome_agrees(obj.get("outcome"), success):
        return []
    return [f"{where}: outcome must agree with reward.success"]


def check_episode(obj, where, options=None, hooks=None):
    """Validate a coding/agent episode record."""
    options = EpisodeOptions() if options is None else options
    hooks = default_hooks() if hooks is None else hooks
    errs = [
        f"{where}: episode missing '{key}'"
        for key in _episode_required_keys(options.require_goal)
        if key not in obj
    ]
    errs += hooks.nonempty_text_field_errors(obj, where, ("goal", "outcome"))
    errs += hooks.require_reward(obj, where)
    errs += _terminal_outcome_errors(obj, where, options, hooks)
    return errs + _episode_steps_errors(obj, where, options, hooks)


if __package__:
    _expose_package_sibling(__name__)
