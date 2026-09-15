#!/usr/bin/env python3
"""Episode shape checks shared by the run validator's routes.

Every rule reads observable fields only: the tool turns of an episode and
the hidden-reasoning vocabulary that must not appear on staged records.
The observable-basis pattern is module-level data so a reviewer can audit
what is forbidden and what counts as evidence without stepping through
control flow. Multi-agent coordination records live in
validate_run_multi_agent.
"""

import re
import sys

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling
    _assert_direct_sibling("validate_run_episode")
    from . import validate_run_rewards as _validate_run_rewards
    from . import validate_run_safety as _validate_run_safety
    from . import validate_run_thalamic as _validate_run_thalamic
else:
    # Join a qualified twin without importing pipelines during normal CLI use.
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "validate_run_episode"
    )
    import validate_run_rewards as _validate_run_rewards
    import validate_run_safety as _validate_run_safety
    import validate_run_thalamic as _validate_run_thalamic


HIDDEN_THOUGHT_KEYS = frozenset(
    {"thought", "chain_of_thought", "scratch", "inner_monologue"}
)
# Keys are normalised to snake_case before the vocabulary lookup so
# ``chainOfThought`` and ``Chain-Of-Thought`` are caught as well.
_CAMEL_BOUNDARY_RE = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")
_NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")
OBSERVABLE_BASIS_RE = re.compile(
    r"\b(?:artifacts?|diagnos\w*|diff|errors?|evidence|fail\w*|fault|files?|found|goal|"
    r"inspect\w*|locks?|logs?|manifest|observ\w*|plan|read|reflection|report\w*|"
    r"request|requirement|results?|retr(?:y|ies|ied|ying)|schema|self-check|"
    r"show\w*|status|tests?|tool (?:call|output|result)|verif\w*)\b",
    re.IGNORECASE,
)
EPISODE_REQUIRED_KEYS = ("goal", "steps", "outcome", "reward")
STEP_REQUIRED_KEYS = ("tool_call", "observation")

require_reward = _validate_run_rewards.require_reward
terminal_outcome_agrees = _validate_run_rewards.terminal_outcome_agrees
nonempty_text_field_errors = _validate_run_safety.nonempty_text_field_errors


def episode_like(obj):
    """True when an object is a coding/agent episode rather than Thalamic."""
    return (
        isinstance(obj, dict)
        and "steps" in obj
        and not all(key in obj for key in _validate_run_thalamic.THALAMIC_CORE_KEYS)
    )


def _normalized_hidden_key(key):
    camel_split = _CAMEL_BOUNDARY_RE.sub("_", str(key)).casefold()
    return _NON_ALNUM_RE.sub("_", camel_split).strip("_")


def hidden_thought_paths(value, path=""):
    """Return every nested forbidden hidden-reasoning key and its path."""
    found = []
    if isinstance(value, dict):
        for key, item in value.items():
            child_path = f"{path}.{key}" if path else key
            if _normalized_hidden_key(key) in HIDDEN_THOUGHT_KEYS:
                found.append((key, child_path))
            found.extend(hidden_thought_paths(item, child_path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            found.extend(hidden_thought_paths(item, f"{path}[{index}]"))
    return found


def staging_hidden_thought_errors(obj, where):
    """Reject every hidden-reasoning key a staged record carries, recursively."""
    return [
        f"{where}: hidden '{key}' is forbidden at {path}; use observable fields"
        for key, path in hidden_thought_paths(obj)
    ]


def _decision_basis_errors(basis, where):
    if not isinstance(basis, str) or not basis.strip():
        return [f"{where}: decision_basis must be a non-empty string"]
    if OBSERVABLE_BASIS_RE.search(basis) is None:
        return [
            f"{where}: decision_basis must cite observable plan, observation, "
            "tool-result, file/test status, or request evidence"
        ]
    return []


def _tool_call_errors(tool_call, where):
    if not isinstance(tool_call, dict):
        return [f"{where}: tool_call must be an object"]
    errors = []
    if not isinstance(tool_call.get("name"), str) or not tool_call["name"].strip():
        errors.append(f"{where}: tool_call.name must be a non-empty string")
    if not isinstance(tool_call.get("args"), dict):
        errors.append(f"{where}: tool_call.args must be an object")
    return errors


def staging_tool_turn_errors(turn, where):
    """Validate an observable structured tool turn in staged agentic data."""
    errors = _decision_basis_errors(turn.get("decision_basis"), where)
    errors += _tool_call_errors(turn.get("tool_call"), where)
    observation = turn.get("observation")
    if not isinstance(observation, str) or not observation.strip():
        errors.append(f"{where}: observation must be a non-empty string")
    return errors


def _outcome_agreement_errors(obj, where, outcome_key):
    """The terminal outcome text must agree with a boolean reward.success."""
    reward = obj.get("reward")
    success = reward.get("success") if isinstance(reward, dict) else None
    if isinstance(success, bool) and not terminal_outcome_agrees(obj.get(outcome_key), success):
        return [f"{where}: {outcome_key} must agree with reward.success"]
    return []


def _step_errors(step, where, forbid_hidden_thought):
    """Validate one episode step; ``where`` already names the step."""
    if not isinstance(step, dict):
        return [f"{where}: must be an object"]
    errs = [f"{where}: missing '{key}'" for key in STEP_REQUIRED_KEYS if key not in step]
    # Existing non-staged records may still use the legacy ``thought``
    # field; retain the audit warning path for those historical runs.
    # Transactional agentic publication always uses the strict branch
    # below and rejects every hidden-reasoning key recursively.
    if "decision_basis" not in step and (forbid_hidden_thought or "thought" not in step):
        errs.append(f"{where}: missing 'decision_basis'")
    if forbid_hidden_thought:
        errs += staging_tool_turn_errors(step, where)
    return errs


def _steps_errors(steps, where, forbid_hidden_thought):
    if not isinstance(steps, list) or not steps:
        return [f"{where}: steps must be a non-empty array"]
    return [
        error
        for index, step in enumerate(steps)
        for error in _step_errors(step, f"{where} step {index}", forbid_hidden_thought)
    ]


def check_episode(
    obj,
    where,
    require_goal=True,
    forbid_hidden_thought=False,
    enforce_terminal_outcome=False,
):
    """Validate a coding/agent episode: required keys, reward, and every step."""
    required = EPISODE_REQUIRED_KEYS if require_goal else EPISODE_REQUIRED_KEYS[1:]
    errs = [f"{where}: episode missing '{key}'" for key in required if key not in obj]
    errs += nonempty_text_field_errors(obj, where, ("goal", "outcome"))
    errs += require_reward(obj, where)
    if enforce_terminal_outcome:
        errs += _outcome_agreement_errors(obj, where, "outcome")
    errs += _steps_errors(obj.get("steps"), where, forbid_hidden_thought)
    return errs


if __package__:
    _expose_package_sibling(__name__)
