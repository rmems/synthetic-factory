#!/usr/bin/env python3
"""Shape routing for the run validator: kind dispatch and preference staging."""

import posixpath
import re
import sys
from typing import NamedTuple

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling
    _assert_direct_sibling("validate_run_routes")
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "validate_run_routes"
    )


STAGING_FINISHED_KINDS = frozenset(
    {"preference", "safety_case", "multi_agent", "episode"}
)
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
ARTIFACT_RE = re.compile(
    r"https?://[^\s\"']+|"
    r"(?:[a-z0-9_.-]+/)*[a-z0-9_.-]+\."
    r"(?:csv|env|go|java|js|json|md|py|rs|sql|toml|ts|txt|ya?ml)|"
    r"/(?:[a-z0-9_{}.-]+/)*[a-z0-9_{}.-]+",
    re.IGNORECASE,
)


class LineHooks(NamedTuple):
    """Live checkers and vocabularies ``check_line`` reads per call.

    The validate_run facade builds this from its own compatibility names so
    patching check_thalamic, check_episode, THALAMIC_CORE_KEYS, and the
    staging finishers keeps flowing through the router.
    """

    thalamic_core_keys: tuple
    check_thalamic: object
    check_episode: object
    check_safety_case: object
    check_multi_agent: object
    check_spike_order: object
    episode_like: object
    require_reward: object
    check_provenance_publish: object
    hidden_thought_errors: object
    preference_goal_errors: object


def _normalized_goal(value):
    if not isinstance(value, str) or not value.strip():
        return None
    return " ".join(value.split())


def _normalized_artifact(artifact_text):
    artifact = artifact_text.rstrip(".,;:").casefold()
    if artifact.startswith(("http://", "https://")):
        return artifact
    return posixpath.normpath(artifact)


def _collect_context_anchors(node, anchors, key=""):
    if isinstance(node, dict):
        for child_key, child in node.items():
            _collect_context_anchors(child, anchors, str(child_key).casefold())
        return
    if isinstance(node, list):
        for child in node:
            _collect_context_anchors(child, anchors, key)
        return
    if not isinstance(node, str):
        return
    normalized = " ".join(node.split()).casefold()
    if key and any(term in key for term in CONTEXT_KEY_TERMS):
        anchors.add(f"field:{normalized}")
    anchors.update(
        f"artifact:{_normalized_artifact(match.group(0))}"
        for match in ARTIFACT_RE.finditer(node)
    )


def preference_side_context_anchors(value):
    """Return observable file/API/criterion anchors from one preference side."""
    anchors = set()
    _collect_context_anchors(value, anchors)
    return anchors


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
        else:
            normalized[path] = goal
    return normalized, errors


def _preference_context_errors(obj, where):
    chosen = obj.get("chosen")
    rejected = obj.get("rejected")
    if not isinstance(chosen, dict) or not isinstance(rejected, dict):
        return []
    chosen_context = preference_side_context_anchors(chosen)
    rejected_context = preference_side_context_anchors(rejected)
    if (
        chosen_context
        and rejected_context
        and chosen_context.isdisjoint(rejected_context)
    ):
        return [
            f"{where}: preference sides must share observable file, API, "
            "target, or success-criterion context"
        ]
    return []


def staging_preference_goal_errors(obj, where):
    """Require explicit or inherited agreement on one preference problem."""
    raw_goals = _preference_goal_values(obj)
    normalized, errors = _normalized_preference_goals(raw_goals, where)
    if not normalized:
        return [f"{where}: preference needs a shared non-empty goal"]
    if raw_goals["goal"] is None and (
        "chosen.goal" not in normalized or "rejected.goal" not in normalized
    ):
        errors.append(
            f"{where}: preference needs both side goals when no top-level goal is present"
        )
    if len(set(normalized.values())) > 1:
        errors.append(
            f"{where}: top-level and side goals must describe the same problem"
        )
    return errors + _preference_context_errors(obj, where)


def preference_side_errors(side, label, episode_pref, episode_kwargs, hooks):
    """Validate one preference side as an episode or as a ThalamicTrajectory."""
    if not isinstance(side, dict):
        return [f"{label} must be an object"]
    if episode_pref:
        return hooks.check_episode(side, label, **episode_kwargs)
    return hooks.check_thalamic(side, label)


def preference_episode_wrapper_errors(obj, where, chosen, factory_staging, hooks):
    """Wrapper-level invariants that only apply to episode preferences."""
    errs = []
    if "goal" not in obj and not (isinstance(chosen, dict) and "goal" in chosen):
        errs.append(f"{where}: preference episode needs a shared or chosen goal")
    errs += hooks.require_reward(obj, where)
    reward = obj.get("reward")
    if (
        factory_staging
        and isinstance(reward, dict)
        and isinstance(reward.get("success"), bool)
        and reward["success"] is not True
    ):
        errs.append(f"{where}: preference wrapper reward.success must be true")
    return errs


def route_thalamic(obj, where, _factory_staging, hooks):
    return hooks.check_thalamic(obj, where)


def route_preference(obj, where, factory_staging, hooks):
    errs = []
    chosen = obj.get("chosen")
    rejected = obj.get("rejected")
    episode_pref = hooks.episode_like(chosen) or hooks.episode_like(rejected)
    episode_kwargs = {
        "require_goal": "goal" not in obj,
        "forbid_hidden_thought": factory_staging,
    }
    errs += preference_side_errors(
        chosen, f"{where}.chosen", episode_pref, episode_kwargs, hooks
    )
    errs += preference_side_errors(
        rejected, f"{where}.rejected", episode_pref, episode_kwargs, hooks
    )
    if episode_pref:
        errs += preference_episode_wrapper_errors(
            obj, where, chosen, factory_staging, hooks
        )
    if not isinstance(obj.get("critique"), str) or not obj["critique"].strip():
        errs.append(f"{where}: preference record needs a non-empty critique")
    return errs


def route_bridge_pair(obj, where, _factory_staging, hooks):
    errs = []
    events = obj["spike_events"]
    if not isinstance(events, list) or not events:
        errs.append(f"{where}: spike_events must be a non-empty array")
    else:
        errs += hooks.check_spike_order(events, where, enclosing=obj)
    view = obj.get("language_view")
    if not isinstance(view, dict):
        errs.append(f"{where}: language_view must be an object")
    else:
        traj = view.get("trajectory")
        if isinstance(traj, dict):
            errs += hooks.check_thalamic(traj, f"{where}.language_view.trajectory")
        else:
            errs.append(f"{where}: language_view.trajectory missing or not an object")
    return errs


def route_safety_case(obj, where, factory_staging, hooks):
    return hooks.check_safety_case(obj, where, factory_staging=factory_staging)


def route_multi_agent(obj, where, factory_staging, hooks):
    return hooks.check_multi_agent(obj, where, factory_staging=factory_staging)


def route_episode(obj, where, factory_staging, hooks):
    return hooks.check_episode(
        obj,
        where,
        forbid_hidden_thought=factory_staging,
        enforce_terminal_outcome=factory_staging,
    )


def line_routes(hooks):
    """Return the ordered (required_keys, kind, route) table ``check_line`` walks."""
    return (
        (hooks.thalamic_core_keys, "thalamic", route_thalamic),
        (("chosen", "rejected"), "preference", route_preference),
        (("language_view", "spike_events"), "bridge_pair", route_bridge_pair),
        (("case_type",), "safety_case", route_safety_case),
        (("transcript", "agents"), "multi_agent", route_multi_agent),
        (("goal", "steps"), "episode", route_episode),
    )


def finish_agentic(errors, obj, where, kind, hooks):
    errors += hooks.hidden_thought_errors(obj, where)
    errors += [
        error for error in hooks.check_provenance_publish(obj, where) if error not in errors
    ]
    if kind == "preference":
        errors += hooks.preference_goal_errors(obj, where)
    return errors


def route_code_repair(obj, where):
    """Bind operational family checks to the sealed source without execution.

    Admission is imported here, not at module import: ``code_repair._contract``
    loads ``coding_constants``, which historically imported ``validate_run``.
    An eager import would re-enter the facade while ``check_line`` is still
    binding and would also pull the sealed-catalog stack into every CLI
    invoke that never sees a repair record.
    """
    if __package__:
        from .code_repair.admission import sealed_record_findings
    else:
        from code_repair.admission import sealed_record_findings
    return sealed_record_findings(obj, where), "code_repair"


def check_line(obj, where, factory_staging=False, hooks=None):
    """Route an object to the right checker based on its shape."""
    if hooks is None:
        raise TypeError("check_line requires LineHooks from the validate_run facade")
    if not isinstance(obj, dict):
        return [f"{where}: record must be a JSON object"], "unknown"
    if obj.get("family") == "python-function-repair":
        return route_code_repair(obj, where)
    for required_keys, kind, route in line_routes(hooks):
        if not all(k in obj for k in required_keys):
            continue
        errors = route(obj, where, factory_staging, hooks)
        if factory_staging and kind in STAGING_FINISHED_KINDS:
            errors = finish_agentic(errors, obj, where, kind, hooks)
        return errors, kind
    return [f"{where}: unrecognized record shape (keys: {sorted(obj)[:8]})"], "unknown"


if __package__:
    _expose_package_sibling(__name__)
