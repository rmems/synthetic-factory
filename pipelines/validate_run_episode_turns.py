#!/usr/bin/env python3
"""Hidden-reasoning walks and staged tool-turn checks for episodes."""

import re
import sys

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling
    _assert_direct_sibling("validate_run_episode_turns")
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "validate_run_episode_turns"
    )


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


def _normalized_hidden_key(key):
    camel = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", str(key))
    return re.sub(r"[^a-z0-9]+", "_", camel.casefold()).strip("_")


def _child_path(path, key):
    if path:
        return f"{path}.{key}"
    return key


def _hidden_thoughts_in_mapping(value, path, keys):
    found = []
    for key, item in value.items():
        child_path = _child_path(path, key)
        if _normalized_hidden_key(key) in keys:
            found.append((key, child_path))
        found.extend(hidden_thought_paths(item, child_path, keys=keys))
    return found


def _hidden_thoughts_in_sequence(value, path, keys):
    found = []
    for index, item in enumerate(value):
        found.extend(hidden_thought_paths(item, f"{path}[{index}]", keys=keys))
    return found


def hidden_thought_paths(value, path="", keys=None):
    """Return every nested forbidden hidden-reasoning key and its path."""
    forbidden = HIDDEN_THOUGHT_KEYS if keys is None else keys
    if isinstance(value, dict):
        return _hidden_thoughts_in_mapping(value, path, forbidden)
    if isinstance(value, list):
        return _hidden_thoughts_in_sequence(value, path, forbidden)
    return []


def staging_hidden_thought_errors(obj, where, keys=None):
    """Reject every hidden-reasoning key under factory staging."""
    return [
        f"{where}: hidden '{key}' is forbidden at {path}; use observable fields"
        for key, path in hidden_thought_paths(obj, keys=keys)
    ]


def nonempty_text(value):
    if not isinstance(value, str):
        return False
    return bool(value.strip())


def _decision_basis_errors(turn, where, basis_re):
    basis = turn.get("decision_basis")
    if not nonempty_text(basis):
        return [f"{where}: decision_basis must be a non-empty string"]
    if basis_re.search(basis) is not None:
        return []
    return [
        f"{where}: decision_basis must cite observable plan, observation, "
        "tool-result, file/test status, or request evidence"
    ]


def _tool_call_field_errors(tool_call, where):
    errors = []
    if not nonempty_text(tool_call.get("name")):
        errors.append(f"{where}: tool_call.name must be a non-empty string")
    if not isinstance(tool_call.get("args"), dict):
        errors.append(f"{where}: tool_call.args must be an object")
    return errors


def _tool_call_errors(turn, where):
    tool_call = turn.get("tool_call")
    if isinstance(tool_call, dict):
        return _tool_call_field_errors(tool_call, where)
    return [f"{where}: tool_call must be an object"]


def _observation_errors(turn, where):
    if nonempty_text(turn.get("observation")):
        return []
    return [f"{where}: observation must be a non-empty string"]


def staging_tool_turn_errors(turn, where, observable_basis_re=None):
    """Validate an observable structured tool turn in staged agentic data."""
    basis_re = OBSERVABLE_BASIS_RE if observable_basis_re is None else observable_basis_re
    return (
        _decision_basis_errors(turn, where, basis_re)
        + _tool_call_errors(turn, where)
        + _observation_errors(turn, where)
    )


if __package__:
    _expose_package_sibling(__name__)
