#!/usr/bin/env python3
"""Preference-goal agreement checks shared by the run validator's routes.

A staged preference must describe one problem: its top-level and side goals
agree, and both sides share observable file, API, target, or success-criterion
context. The context vocabulary and the artifact pattern are module-level
data so a reviewer can audit what counts as an anchor.
"""

import posixpath
import re
import sys

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling
    _assert_direct_sibling("validate_run_preference")
else:
    # Join a qualified twin without importing pipelines during normal CLI use.
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "validate_run_preference"
    )


# A string under a key naming one of these terms is an observable anchor.
CONTEXT_KEY_TERMS = (
    "api",
    "criterion",
    "criteria",
    "endpoint",
    "file",
    "path",
    "repo",
    "repository",
    "resource",
    "target",
    "url",
)
# URLs, source/config file names, and absolute paths found anywhere in text.
ARTIFACT_RE = re.compile(
    r"https?://[^\s\"']+|"
    r"(?:[a-z0-9_.-]+/)*[a-z0-9_.-]+\."
    r"(?:csv|env|go|java|js|json|md|py|rs|sql|toml|ts|txt|ya?ml)|"
    r"/(?:[a-z0-9_{}.-]+/)*[a-z0-9_{}.-]+",
    re.IGNORECASE,
)
GOAL_PATHS = ("goal", "chosen.goal", "rejected.goal")


def normalized_goal(value):
    """Collapse whitespace in a goal string; None when it is not usable text."""
    if not isinstance(value, str) or not value.strip():
        return None
    return " ".join(value.split())


def _normalized_artifact(artifact_text):
    artifact = artifact_text.rstrip(".,;:").casefold()
    if artifact.startswith(("http://", "https://")):
        return artifact
    return posixpath.normpath(artifact)


def _string_anchors(text, key):
    """Anchors one string contributes: its field value and any artifacts."""
    anchors = set()
    if key and any(term in key for term in CONTEXT_KEY_TERMS):
        anchors.add(f"field:{' '.join(text.split()).casefold()}")
    anchors.update(
        f"artifact:{_normalized_artifact(match.group(0))}"
        for match in ARTIFACT_RE.finditer(text)
    )
    return anchors


def _collect_anchors(node, key, anchors):
    """Walk a JSON value, adding every anchor under its casefolded key."""
    if isinstance(node, dict):
        for child_key, child in node.items():
            _collect_anchors(child, str(child_key).casefold(), anchors)
    elif isinstance(node, list):
        for child in node:
            _collect_anchors(child, key, anchors)
    elif isinstance(node, str):
        anchors |= _string_anchors(node, key)


def preference_side_context_anchors(value):
    """Return observable file/API/criterion anchors from one preference side."""
    anchors = set()
    _collect_anchors(value, "", anchors)
    return anchors


def _side_goal(side):
    return side.get("goal") if isinstance(side, dict) else None


def _raw_goals(obj):
    """Map each goal path to its raw value (None when absent)."""
    values = (obj.get("goal"), _side_goal(obj.get("chosen")), _side_goal(obj.get("rejected")))
    return dict(zip(GOAL_PATHS, values))


def _normalize_goals(raw_goals, where):
    """Return (errors, normalized goals) for every goal that is present."""
    errors = []
    normalized = {}
    for path, value in raw_goals.items():
        if value is None:
            continue
        goal = normalized_goal(value)
        if goal is None:
            errors.append(f"{where}: {path} must be a non-empty string when present")
        else:
            normalized[path] = goal
    return errors, normalized


def _goal_agreement_errors(raw_goals, normalized, where):
    """Side goals stand in for a missing top-level goal and must agree with it."""
    errors = []
    if raw_goals["goal"] is None and not all(
        path in normalized for path in GOAL_PATHS[1:]
    ):
        errors.append(
            f"{where}: preference needs both side goals when no top-level goal is present"
        )
    if len(set(normalized.values())) > 1:
        errors.append(f"{where}: top-level and side goals must describe the same problem")
    return errors


def _shared_context_errors(chosen, rejected, where):
    """Both sides, when they carry anchors, must share at least one."""
    if not isinstance(chosen, dict) or not isinstance(rejected, dict):
        return []
    chosen_context = preference_side_context_anchors(chosen)
    rejected_context = preference_side_context_anchors(rejected)
    if chosen_context and rejected_context and chosen_context.isdisjoint(rejected_context):
        return [
            f"{where}: preference sides must share observable file, API, "
            "target, or success-criterion context"
        ]
    return []


def staging_preference_goal_errors(obj, where):
    """Require explicit or inherited agreement on one preference problem."""
    raw_goals = _raw_goals(obj)
    errors, normalized = _normalize_goals(raw_goals, where)
    if not normalized:
        return [f"{where}: preference needs a shared non-empty goal"]
    errors += _goal_agreement_errors(raw_goals, normalized, where)
    errors += _shared_context_errors(obj.get("chosen"), obj.get("rejected"), where)
    return errors


if __package__:
    _expose_package_sibling(__name__)
