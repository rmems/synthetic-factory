#!/usr/bin/env python3
"""Episode, hidden-reasoning, and tool-turn checks for the run validator."""

import re
import sys
from typing import NamedTuple

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling
    _assert_direct_sibling("validate_run_episode")
    from . import validate_run_rewards as _validate_run_rewards
    from . import validate_run_safety as _validate_run_safety
    from . import validate_run_thalamic as _validate_run_thalamic
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "validate_run_episode"
    )
    import validate_run_rewards as _validate_run_rewards
    import validate_run_safety as _validate_run_safety
    import validate_run_thalamic as _validate_run_thalamic


HIDDEN_THOUGHT_KEYS = frozenset(
    {"thought", "chain_of_thought", "scratch", "inner_monologue"}
)
OBSERVABLE_BASIS_RE = re.compile(
    r"\b(?:artifacts?|diagnos\w*|diff|errors?|evidence|fail\w*|fault|files?|found|goal|"
    r"inspect\w*|locks?|logs?|manifest|observ\w*|plan|read|reflection|report\w*|"
    r"request|requirement|results?|retr(?:y|ies|ied|ying)|schema|self-check|"
    r"show\w*|status|tests?|tool (?:call|output|result)|verif\w*)\b",
    re.IGNORECASE,
)


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
    return (
        isinstance(obj, dict)
        and "steps" in obj
        and not all(key in obj for key in keys)
    )


def hidden_thought_paths(value, path="", keys=None):
    """Return every nested forbidden hidden-reasoning key and its path."""
    forbidden = HIDDEN_THOUGHT_KEYS if keys is None else keys
    found = []
    if isinstance(value, dict):
        for key, item in value.items():
            child_path = f"{path}.{key}" if path else key
            normalized_key = re.sub(
                r"[^a-z0-9]+",
                "_",
                re.sub(
                    r"(?<=[a-z0-9])(?=[A-Z])", "_", str(key)
                ).casefold(),
            ).strip("_")
            if normalized_key in forbidden:
                found.append((key, child_path))
            found.extend(hidden_thought_paths(item, child_path, keys=forbidden))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            found.extend(
                hidden_thought_paths(item, f"{path}[{index}]", keys=forbidden)
            )
    return found


def staging_hidden_thought_errors(obj, where, keys=None):
    """Reject every hidden-reasoning key under factory staging."""
    return [
        f"{where}: hidden '{key}' is forbidden at {path}; use observable fields"
        for key, path in hidden_thought_paths(obj, keys=keys)
    ]


def staging_tool_turn_errors(turn, where, observable_basis_re=None):
    """Validate an observable structured tool turn in staged agentic data."""
    basis_re = OBSERVABLE_BASIS_RE if observable_basis_re is None else observable_basis_re
    errors = []
    basis = turn.get("decision_basis")
    if not isinstance(basis, str) or not basis.strip():
        errors.append(f"{where}: decision_basis must be a non-empty string")
    elif basis_re.search(basis) is None:
        errors.append(
            f"{where}: decision_basis must cite observable plan, observation, "
            "tool-result, file/test status, or request evidence"
        )
    tool_call = turn.get("tool_call")
    if not isinstance(tool_call, dict):
        errors.append(f"{where}: tool_call must be an object")
    else:
        if not isinstance(tool_call.get("name"), str) or not tool_call["name"].strip():
            errors.append(f"{where}: tool_call.name must be a non-empty string")
        if not isinstance(tool_call.get("args"), dict):
            errors.append(f"{where}: tool_call.args must be an object")
    observation = turn.get("observation")
    if not isinstance(observation, str) or not observation.strip():
        errors.append(f"{where}: observation must be a non-empty string")
    return errors


def _episode_required_keys(require_goal):
    if require_goal:
        return ("goal", "steps", "outcome", "reward")
    return ("steps", "outcome", "reward")


def _episode_step_errors(step, where, index, forbid_hidden_thought, hooks):
    """Validate one episode step object, including the staged tool-turn gate."""
    if not isinstance(step, dict):
        return [f"{where} step {index}: must be an object"]
    errors = [
        f"{where} step {index}: missing '{key}'"
        for key in ("tool_call", "observation")
        if key not in step
    ]
    # Existing non-staged records may still use the legacy ``thought``
    # field; retain the audit warning path for those historical runs.
    # Transactional agentic publication always uses the strict branch
    # below and rejects every hidden-reasoning key recursively.
    if "decision_basis" not in step and (
        forbid_hidden_thought or "thought" not in step
    ):
        errors.append(f"{where} step {index}: missing 'decision_basis'")
    if forbid_hidden_thought:
        errors += staging_tool_turn_errors(
            step,
            f"{where} step {index}",
            observable_basis_re=hooks.observable_basis_re,
        )
    return errors


def _episode_steps_errors(obj, where, forbid_hidden_thought, hooks):
    steps = obj.get("steps")
    if not isinstance(steps, list) or not steps:
        return [f"{where}: steps must be a non-empty array"]
    errors = []
    for index, step in enumerate(steps):
        errors += _episode_step_errors(
            step, where, index, forbid_hidden_thought, hooks
        )
    return errors


def check_episode(
    obj,
    where,
    require_goal=True,
    forbid_hidden_thought=False,
    enforce_terminal_outcome=False,
    hooks=None,
):
    """Validate a coding/agent episode record."""
    hooks = default_hooks() if hooks is None else hooks
    errs = [
        f"{where}: episode missing '{key}'"
        for key in _episode_required_keys(require_goal)
        if key not in obj
    ]
    errs += hooks.nonempty_text_field_errors(obj, where, ("goal", "outcome"))
    errs += hooks.require_reward(obj, where)
    reward = obj.get("reward")
    success = reward.get("success") if isinstance(reward, dict) else None
    if (
        enforce_terminal_outcome
        and isinstance(success, bool)
        and not hooks.terminal_outcome_agrees(obj.get("outcome"), success)
    ):
        errs.append(f"{where}: outcome must agree with reward.success")
    return errs + _episode_steps_errors(obj, where, forbid_hidden_thought, hooks)


if __package__:
    _expose_package_sibling(__name__)
