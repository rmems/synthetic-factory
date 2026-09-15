#!/usr/bin/env python3
"""Validate a dated factory run under outputs/raw/<date>/.

Checks every .jsonl file: each line must parse as JSON, and any embedded
ThalamicTrajectory (top-level, chosen/rejected pair, or language_view.trajectory)
must satisfy schemas/thalamic-trajectory.schema.json's constraints. Coding
episodes are checked against their own shape. Prints totals JSON to stdout
and errors to stderr; exits nonzero if any file has errors. Does not write
manifest.json unless --write is passed.

Usage: python3 pipelines/validate_run.py [--write] <run_dir>
"""

import argparse
import json
import math
import posixpath
import re
import sys
from pathlib import Path

if __package__:
    # Import-twin helpers join the package import lock; import-order tests cover this edge.
    from . import _assert_direct_sibling, _expose_package_sibling  # pylint: disable=cyclic-import
    _assert_direct_sibling("validate_run")
    from . import validate_run_spikes as _validate_run_spikes
    from . import validate_run_provenance as _validate_run_provenance
    from . import validate_run_rewards as _validate_run_rewards
    from . import validate_run_reward_total as _validate_run_reward_total
    from . import validate_run_thalamic as _validate_run_thalamic
    from . import validate_run_safety as _validate_run_safety
    from .validate_run_input import parse_exact_json_record as _parse_exact_json_record
else:
    import validate_run_spikes as _validate_run_spikes
    import validate_run_provenance as _validate_run_provenance
    import validate_run_rewards as _validate_run_rewards
    import validate_run_reward_total as _validate_run_reward_total
    import validate_run_thalamic as _validate_run_thalamic
    import validate_run_safety as _validate_run_safety
    from validate_run_input import parse_exact_json_record as _parse_exact_json_record

# Historical public compatibility surface. Explicit binding keeps these names
# importable without asking static analyzers to treat unused imports as use.
BRIDGE_SPIKE_EVENT_KEYS = _validate_run_spikes.BRIDGE_SPIKE_EVENT_KEYS
REPO = _validate_run_spikes.REPO
SCHEMA_PATH = _validate_run_spikes.SCHEMA_PATH
SPIKE_CLOCK_DOMAIN_KEYS = _validate_run_spikes.SPIKE_CLOCK_DOMAIN_KEYS
SPIKE_CLOCK_DOMAIN_MISMATCH = _validate_run_spikes.SPIKE_CLOCK_DOMAIN_MISMATCH
SPIKE_EVENT_NUMBER_KEYS = _validate_run_spikes.SPIKE_EVENT_NUMBER_KEYS
SPIKE_EVENT_STRING_KEYS = _validate_run_spikes.SPIKE_EVENT_STRING_KEYS
SPIKE_ORDER_MISMATCH = _validate_run_spikes.SPIKE_ORDER_MISMATCH
SPIKE_TIME_KEYS = _validate_run_spikes.SPIKE_TIME_KEYS
SPIKE_TIME_KEY_MISMATCH = _validate_run_spikes.SPIKE_TIME_KEY_MISMATCH
THALAMIC_SCHEMA = _validate_run_spikes.THALAMIC_SCHEMA
_check_spike_order = _validate_run_spikes.check_spike_order
_check_spike_stream = _validate_run_spikes.check_spike_stream
_declared_clock_domains = _validate_run_spikes.declared_clock_domains
_event_time = _validate_run_spikes.event_time
_is_number = _validate_run_spikes.is_number
_typed_enum_errors = _validate_run_provenance.typed_enum_errors
check_provenance_publish = _validate_run_provenance.check_provenance_publish

# The spike-train surface lived here before it split into validate_run_spikes;
# ``__all__`` declares the names this module still re-exports so existing
# ``validate_run.X`` consumers (the CLI tests among them) resolve unchanged.
__all__ = [
    "ALLOWED_PROVENANCE_KIND",
    "ALLOWED_SIM_OR_REAL",
    "BRIDGE_SPIKE_EVENT_KEYS",
    "HIDDEN_THOUGHT_KEYS",
    "OBSERVABLE_BASIS_RE",
    "Path",
    "REPO",
    "REWARD_ARITHMETIC_MARKERS",
    "REWARD_NON_COMPONENT_KEYS",
    "REWARD_TOL",
    "REWARD_UNWEIGHTED_MISMATCH",
    "REWARD_WEIGHTED_MISMATCH",
    "SAFETY_CASE_DECISIONS",
    "SAFETY_CASE_SUCCESS",
    "SAFETY_CASE_TYPES",
    "SAFETY_DECISIONS",
    "SCHEMA_PATH",
    "SPIKE_CLOCK_DOMAIN_KEYS",
    "SPIKE_CLOCK_DOMAIN_MISMATCH",
    "SPIKE_EVENT_NUMBER_KEYS",
    "SPIKE_EVENT_STRING_KEYS",
    "SPIKE_ORDER_MISMATCH",
    "SPIKE_TIME_KEYS",
    "SPIKE_TIME_KEY_MISMATCH",
    "THALAMIC_CORE_KEYS",
    "THALAMIC_OBJECT_KEYS",
    "THALAMIC_REQUIRED",
    "THALAMIC_SCHEMA",
    "THALAMIC_STRING_KEYS",
    "argparse",
    "check_episode",
    "check_line",
    "check_meta_round",
    "check_multi_agent",
    "check_provenance",
    "check_provenance_publish",
    "check_reward_total",
    "check_safety_case",
    "check_spike_order",
    "check_spike_stream",
    "check_thalamic",
    "declared_clock_domains",
    "event_time",
    "episode_like",
    "is_number",
    "json",
    "main",
    "math",
    "parse_args",
    "posixpath",
    "re",
    "reject_json_constant",
    "sys",
    "terminal_outcome_agrees",
]

# Thalamic shape vocabulary lives in validate_run_thalamic; the facade rebinds
# it here so routing, compose_trajectory_goals, and the CLI tests keep
# resolving validate_run.THALAMIC_* unchanged.
THALAMIC_REQUIRED = _validate_run_thalamic.THALAMIC_REQUIRED
THALAMIC_OBJECT_KEYS = _validate_run_thalamic.THALAMIC_OBJECT_KEYS
THALAMIC_STRING_KEYS = _validate_run_thalamic.THALAMIC_STRING_KEYS
THALAMIC_CORE_KEYS = _validate_run_thalamic.THALAMIC_CORE_KEYS
SAFETY_DECISIONS = _validate_run_thalamic.SAFETY_DECISIONS

# provenance.kind allows 'unknown'; state.sim_or_real does not. Both
# vocabularies are the schema's own enums.
ALLOWED_PROVENANCE_KIND = _validate_run_provenance.ALLOWED_PROVENANCE_KIND
ALLOWED_SIM_OR_REAL = _validate_run_provenance.ALLOWED_SIM_OR_REAL
# Reward arithmetic lives in validate_run_rewards; the facade rebinds its
# vocabulary here so check_records and the CLI tests keep resolving
# validate_run.REWARD_* (including mock.patch.object targets) unchanged.
REWARD_NON_COMPONENT_KEYS = _validate_run_rewards.REWARD_NON_COMPONENT_KEYS
REWARD_TOL = _validate_run_rewards.REWARD_TOL
OBSERVABLE_BASIS_RE = re.compile(
    r"\b(?:artifacts?|diagnos\w*|diff|errors?|evidence|fail\w*|fault|files?|found|goal|"
    r"inspect\w*|locks?|logs?|manifest|observ\w*|plan|read|reflection|report\w*|"
    r"request|requirement|results?|retr(?:y|ies|ied|ying)|schema|self-check|"
    r"show\w*|status|tests?|tool (?:call|output|result)|verif\w*)\b",
    re.IGNORECASE,
)


def reject_json_constant(value):
    """Reject Python's non-standard NaN and Infinity JSON extensions."""
    raise ValueError(f"non-standard JSON numeric constant {value}")


def is_number(value):
    """Compatibility facade for the shared finite-number predicate."""
    return _is_number(value)


def event_time(event):
    """Compatibility facade for schema-derived spike timestamps."""
    return _event_time(event)


def declared_clock_domains(events, enclosing=None):
    """Compatibility facade for spike clock-domain discovery."""
    return _declared_clock_domains(events, enclosing)


def check_spike_order(
    events,
    where,
    require_keys=BRIDGE_SPIKE_EVENT_KEYS,
    *,
    enclosing=None,
):
    """Compatibility facade for strict spike-stream validation."""
    return _check_spike_order(
        events,
        where,
        require_keys=require_keys,
        enclosing=enclosing,
    )


def check_spike_stream(obj, where):
    """Compatibility facade for optional trajectory spike streams."""
    return _check_spike_stream(obj, where)


_component_numeric = _validate_run_rewards.component_numeric
REWARD_WEIGHTED_MISMATCH = _validate_run_rewards.REWARD_WEIGHTED_MISMATCH
REWARD_UNWEIGHTED_MISMATCH = _validate_run_rewards.REWARD_UNWEIGHTED_MISMATCH
REWARD_ARITHMETIC_MARKERS = _validate_run_rewards.REWARD_ARITHMETIC_MARKERS


def check_reward_total(rc, where):
    """Compatibility facade for reward arithmetic (see validate_run_reward_total).

    The tolerance and bookkeeping vocabulary are this module's live bindings,
    so rebinding REWARD_TOL or REWARD_NON_COMPONENT_KEYS here keeps flowing
    through exactly as when the check lived inline.
    """
    settings = _validate_run_rewards.RewardSettings(REWARD_TOL, REWARD_NON_COMPONENT_KEYS)
    return _validate_run_reward_total.check_reward_total(rc, where, settings)


def _state_provenance_errors(obj, where):
    """Validate state provenance using this facade's live vocabulary seam."""
    return _validate_run_provenance.state_provenance_errors(
        obj,
        where,
        ALLOWED_SIM_OR_REAL,
        _typed_enum_errors,
    )


def _provenance_object_errors(obj, where):
    """Validate provenance using this facade's live vocabulary seam."""
    return _validate_run_provenance.provenance_object_errors(
        obj,
        where,
        ALLOWED_PROVENANCE_KIND,
        _typed_enum_errors,
    )


def check_provenance(obj, where):
    """Validate direct state and provenance objects for every trajectory route."""
    return _state_provenance_errors(obj, where) + _provenance_object_errors(obj, where)


check_meta_round = _validate_run_thalamic.check_meta_round


def check_thalamic(obj, where):
    """Compatibility facade for thalamic validation (see validate_run_thalamic).

    Provenance runs through this module's live gates so vocabulary
    rebinding (mock.patch.object on this module) keeps flowing through,
    exactly as when the whole check lived inline.
    """
    hooks = _validate_run_thalamic.ThalamicHooks(
        SAFETY_DECISIONS,
        check_reward_total,
        THALAMIC_OBJECT_KEYS,
        THALAMIC_STRING_KEYS,
        check_meta_round,
        check_spike_stream,
    )
    errs = _validate_run_thalamic.thalamic_core_errors(obj, where, hooks)
    errs += check_provenance(obj, where)
    # Deep publish-time provenance: any nested 'real' fails
    errs += [e for e in check_provenance_publish(obj, where) if e not in errs]
    errs += _validate_run_thalamic.thalamic_tail_errors(obj, where, hooks)
    return errs


SAFETY_CASE_TYPES = _validate_run_safety.SAFETY_CASE_TYPES
SAFETY_CASE_DECISIONS = _validate_run_safety.SAFETY_CASE_DECISIONS
SAFETY_CASE_SUCCESS = _validate_run_safety.SAFETY_CASE_SUCCESS
HIDDEN_THOUGHT_KEYS = frozenset(
    {"thought", "chain_of_thought", "scratch", "inner_monologue"}
)


def episode_like(obj):
    """True when an object is a coding/agent episode rather than Thalamic."""
    return (
        isinstance(obj, dict)
        and "steps" in obj
        and not all(key in obj for key in THALAMIC_CORE_KEYS)
    )


# Compatibility alias for callers of the pre-split validator surface.
_episode_like = episode_like


def _hidden_thought_paths(value, path=""):
    """Return every nested forbidden hidden-reasoning key and its path."""
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
            if normalized_key in HIDDEN_THOUGHT_KEYS:
                found.append((key, child_path))
            found.extend(_hidden_thought_paths(item, child_path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            found.extend(_hidden_thought_paths(item, f"{path}[{index}]"))
    return found


def _staging_hidden_thought_errors(obj, where):
    return [
        f"{where}: hidden '{key}' is forbidden at {path}; use observable fields"
        for key, path in _hidden_thought_paths(obj)
    ]


def _normalized_goal(value):
    if not isinstance(value, str) or not value.strip():
        return None
    return " ".join(value.split())


def _preference_side_context_anchors(value):
    """Return observable file/API/criterion anchors from one preference side."""
    anchors = set()
    context_key_terms = (
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
    artifact_re = re.compile(
        r"https?://[^\s\"']+|"
        r"(?:[a-z0-9_.-]+/)*[a-z0-9_.-]+\."
        r"(?:csv|env|go|java|js|json|md|py|rs|sql|toml|ts|txt|ya?ml)|"
        r"/(?:[a-z0-9_{}.-]+/)*[a-z0-9_{}.-]+",
        re.IGNORECASE,
    )

    def normalized_artifact(artifact_text):
        artifact = artifact_text.rstrip(".,;:").casefold()
        if artifact.startswith(("http://", "https://")):
            return artifact
        return posixpath.normpath(artifact)

    def walk(node, key=""):
        if isinstance(node, dict):
            for child_key, child in node.items():
                walk(child, str(child_key).casefold())
        elif isinstance(node, list):
            for child in node:
                walk(child, key)
        elif isinstance(node, str):
            normalized = " ".join(node.split()).casefold()
            if key and any(term in key for term in context_key_terms):
                anchors.add(f"field:{normalized}")
            anchors.update(
                f"artifact:{normalized_artifact(match.group(0))}"
                for match in artifact_re.finditer(node)
            )

    walk(value)
    return anchors


def _staging_preference_goal_errors(obj, where):
    """Require explicit or inherited agreement on one preference problem."""
    chosen = obj.get("chosen")
    rejected = obj.get("rejected")
    raw_goals = {
        "goal": obj.get("goal"),
        "chosen.goal": chosen.get("goal") if isinstance(chosen, dict) else None,
        "rejected.goal": rejected.get("goal") if isinstance(rejected, dict) else None,
    }
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
    if not normalized:
        return [f"{where}: preference needs a shared non-empty goal"]
    if raw_goals["goal"] is None and (
        "chosen.goal" not in normalized or "rejected.goal" not in normalized
    ):
        errors.append(
            f"{where}: preference needs both side goals when no top-level goal is present"
        )
    if len(set(normalized.values())) > 1:
        errors.append(f"{where}: top-level and side goals must describe the same problem")
    if isinstance(chosen, dict) and isinstance(rejected, dict):
        chosen_context = _preference_side_context_anchors(chosen)
        rejected_context = _preference_side_context_anchors(rejected)
        if (
            chosen_context
            and rejected_context
            and chosen_context.isdisjoint(rejected_context)
        ):
            errors.append(
                f"{where}: preference sides must share observable file, API, "
                "target, or success-criterion context"
            )
    return errors


_require_reward = _validate_run_rewards.require_reward


terminal_outcome_agrees = _validate_run_rewards.terminal_outcome_agrees


def _staging_tool_turn_errors(turn, where):
    """Validate an observable structured tool turn in staged agentic data."""
    errors = []
    basis = turn.get("decision_basis")
    if not isinstance(basis, str) or not basis.strip():
        errors.append(f"{where}: decision_basis must be a non-empty string")
    elif OBSERVABLE_BASIS_RE.search(basis) is None:
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


_nonempty_text_field_errors = _validate_run_safety.nonempty_text_field_errors


def check_episode(
    obj,
    where,
    require_goal=True,
    forbid_hidden_thought=False,
    enforce_terminal_outcome=False,
):
    errs = []
    required = ("goal", "steps", "outcome", "reward") if require_goal else (
        "steps",
        "outcome",
        "reward",
    )
    for key in required:
        if key not in obj:
            errs.append(f"{where}: episode missing '{key}'")
    errs += _nonempty_text_field_errors(obj, where, ("goal", "outcome"))
    errs += _require_reward(obj, where)
    reward = obj.get("reward")
    success = reward.get("success") if isinstance(reward, dict) else None
    if (
        enforce_terminal_outcome
        and isinstance(success, bool)
        and not terminal_outcome_agrees(obj.get("outcome"), success)
    ):
        errs.append(f"{where}: outcome must agree with reward.success")
    steps = obj.get("steps")
    if not isinstance(steps, list) or not steps:
        errs.append(f"{where}: steps must be a non-empty array")
    else:
        for i, step in enumerate(steps):
            if not isinstance(step, dict):
                errs.append(f"{where} step {i}: must be an object")
                continue
            for key in ("tool_call", "observation"):
                if key not in step:
                    errs.append(f"{where} step {i}: missing '{key}'")
            # Existing non-staged records may still use the legacy ``thought``
            # field; retain the audit warning path for those historical runs.
            # Transactional agentic publication always uses the strict branch
            # below and rejects every hidden-reasoning key recursively.
            if "decision_basis" not in step and (
                forbid_hidden_thought or "thought" not in step
            ):
                errs.append(f"{where} step {i}: missing 'decision_basis'")
            if forbid_hidden_thought:
                errs += _staging_tool_turn_errors(step, f"{where} step {i}")
    return errs


def check_multi_agent(obj, where, factory_staging=False):
    errs = []
    for key in (
        "goal",
        "agents",
        "transcript",
        "disagreements",
        "resolution",
        "joint_outcome",
        "reward",
    ):
        if key not in obj:
            errs.append(f"{where}: multi_agent missing '{key}'")
    errs += _nonempty_text_field_errors(obj, where, ("goal", "resolution", "joint_outcome"))
    disagreements = obj.get("disagreements")
    if (
        not isinstance(disagreements, list)
        or not disagreements
        or any(
            not isinstance(item, str) or not item.strip()
            for item in disagreements
        )
    ):
        errs.append(f"{where}: disagreements must be a non-empty array of strings")
    agents = obj.get("agents")
    roles = set()
    mandates = set()
    if not isinstance(agents, list) or len(agents) < 2:
        errs.append(f"{where}: agents must be an array of at least 2 roles")
    else:
        if factory_staging and len(agents) > 4:
            errs.append(f"{where}: coordination records allow at most 4 agents")
        for i, agent in enumerate(agents):
            role = agent.get("role") if isinstance(agent, dict) else None
            if not isinstance(role, str) or not role.strip():
                errs.append(f"{where}: agents[{i}] needs a non-empty role")
            else:
                roles.add(role.strip())
            if factory_staging:
                mandate = agent.get("mandate") if isinstance(agent, dict) else None
                if not isinstance(mandate, str) or not mandate.strip():
                    errs.append(f"{where}: agents[{i}] needs a non-empty mandate")
                else:
                    mandates.add(mandate.strip())
        if len(roles) < 2:
            errs.append(f"{where}: agents must declare at least two distinct roles")
        if factory_staging and len(mandates) != len(agents):
            errs.append(f"{where}: agents must declare distinct mandates")
    transcript = obj.get("transcript")
    if not isinstance(transcript, list) or not transcript:
        errs.append(f"{where}: transcript must be a non-empty array")
    else:
        participating_roles = set()
        for i, turn in enumerate(transcript):
            if not isinstance(turn, dict):
                errs.append(f"{where}: transcript[{i}] must be an object")
                continue
            speaker = turn.get("speaker")
            if not isinstance(speaker, str) or not speaker.strip():
                errs.append(f"{where}: transcript[{i}] missing speaker")
            elif roles and speaker.strip() not in roles:
                errs.append(
                    f"{where}: transcript[{i}] speaker {speaker!r} is not a declared agent role"
                )
            else:
                participating_roles.add(speaker.strip())
            content = turn.get("content")
            if not isinstance(content, str) or not content.strip():
                errs.append(f"{where}: transcript[{i}] needs non-empty content")
            if factory_staging and "tool_call" in turn:
                errs += _staging_tool_turn_errors(turn, f"{where}: transcript[{i}]")
        if roles and len(participating_roles) < 2:
            errs.append(
                f"{where}: transcript must include substantive turns from at least two declared roles"
            )
    errs += _require_reward(obj, where)
    reward = obj.get("reward")
    success = reward.get("success") if isinstance(reward, dict) else None
    if isinstance(success, bool) and not terminal_outcome_agrees(
        obj.get("joint_outcome"), success
    ):
        errs.append(f"{where}: joint_outcome must agree with reward.success")
    return errs


def check_safety_case(obj, where, factory_staging=False):
    """Safety-case rules live in validate_run_safety; the episode/reward tail stays here.

    Vocabularies are this module's live SAFETY_CASE_* bindings, so
    rebinding those compatibility names keeps flowing through exactly as
    when the rules lived inline.
    """
    vocab = _validate_run_safety.SafetyCaseVocab(
        SAFETY_CASE_TYPES, SAFETY_CASE_DECISIONS, SAFETY_CASE_SUCCESS
    )
    errs = _validate_run_safety.safety_case_core_errors(
        obj, where, factory_staging, vocab
    )
    if "steps" in obj:
        errs += check_episode(
            obj, where, require_goal=False, forbid_hidden_thought=factory_staging
        )
    else:
        errs += _require_reward(obj, where)
    return errs


def _route_thalamic(obj, where, _factory_staging):
    return check_thalamic(obj, where)


def _preference_side_errors(side, label, episode_pref, episode_kwargs):
    """Validate one preference side as an episode or as a ThalamicTrajectory."""
    if not isinstance(side, dict):
        return [f"{label} must be an object"]
    if episode_pref:
        return check_episode(side, label, **episode_kwargs)
    return check_thalamic(side, label)


def _preference_episode_wrapper_errors(obj, where, chosen, factory_staging):
    """Wrapper-level invariants that only apply to episode preferences."""
    errs = []
    if "goal" not in obj and not (isinstance(chosen, dict) and "goal" in chosen):
        errs.append(f"{where}: preference episode needs a shared or chosen goal")
    errs += _require_reward(obj, where)
    reward = obj.get("reward")
    if (
        factory_staging
        and isinstance(reward, dict)
        and isinstance(reward.get("success"), bool)
        and reward["success"] is not True
    ):
        errs.append(f"{where}: preference wrapper reward.success must be true")
    return errs


def _route_preference(obj, where, factory_staging):
    errs = []
    chosen = obj.get("chosen")
    rejected = obj.get("rejected")
    episode_pref = episode_like(chosen) or episode_like(rejected)
    episode_kwargs = {
        "require_goal": "goal" not in obj,
        "forbid_hidden_thought": factory_staging,
    }
    errs += _preference_side_errors(chosen, f"{where}.chosen", episode_pref, episode_kwargs)
    errs += _preference_side_errors(rejected, f"{where}.rejected", episode_pref, episode_kwargs)
    if episode_pref:
        errs += _preference_episode_wrapper_errors(obj, where, chosen, factory_staging)
    if not isinstance(obj.get("critique"), str) or not obj["critique"].strip():
        errs.append(f"{where}: preference record needs a non-empty critique")
    return errs


def _route_bridge_pair(obj, where, _factory_staging):
    errs = []
    events = obj["spike_events"]
    if not isinstance(events, list) or not events:
        errs.append(f"{where}: spike_events must be a non-empty array")
    else:
        errs += check_spike_order(events, where, enclosing=obj)
    view = obj.get("language_view")
    if not isinstance(view, dict):
        errs.append(f"{where}: language_view must be an object")
    else:
        traj = view.get("trajectory")
        if isinstance(traj, dict):
            errs += check_thalamic(traj, f"{where}.language_view.trajectory")
        else:
            errs.append(f"{where}: language_view.trajectory missing or not an object")
    return errs


def _route_safety_case(obj, where, factory_staging):
    return check_safety_case(obj, where, factory_staging=factory_staging)


def _route_multi_agent(obj, where, factory_staging):
    return check_multi_agent(obj, where, factory_staging=factory_staging)


def _route_episode(obj, where, factory_staging):
    return check_episode(
        obj,
        where,
        forbid_hidden_thought=factory_staging,
        enforce_terminal_outcome=factory_staging,
    )


# Route on the object-typed trajectory fields so legacy v1 records
# (no canonical `id` yet) still reach the thalamic checker and have their
# state / reward / provenance / meta.round invariants enforced instead of
# being skipped as an unrecognized shape. Canonical `id` coverage is owned
# by the deep layer (check_records / training_audit); this layer only
# type-checks an `id` that is present. A record matches a route when every
# listed key is present; precedence is positional, so thalamic outranks
# preference, which outranks bridge pairs, safety cases, multi-agent
# transcripts, and episodes.
def _line_routes():
    """Return the ordered (required_keys, kind, route) table ``check_line`` walks."""
    return (
        (THALAMIC_CORE_KEYS, "thalamic", _route_thalamic),
        (("chosen", "rejected"), "preference", _route_preference),
        (("language_view", "spike_events"), "bridge_pair", _route_bridge_pair),
        (("case_type",), "safety_case", _route_safety_case),
        (("transcript", "agents"), "multi_agent", _route_multi_agent),
        (("goal", "steps"), "episode", _route_episode),
    )


_LINE_ROUTES = _line_routes()

# Kinds whose factory-staging pass also runs the shared agentic finishers.
_STAGING_FINISHED_KINDS = frozenset({"preference", "safety_case", "multi_agent", "episode"})


def _finish_agentic(errors, obj, where, kind):
    errors += _staging_hidden_thought_errors(obj, where)
    errors += [
        error for error in check_provenance_publish(obj, where) if error not in errors
    ]
    if kind == "preference":
        errors += _staging_preference_goal_errors(obj, where)
    return errors


def _route_code_repair(obj, where):
    """Bind operational family checks to the sealed source without execution."""
    if __package__:
        from .code_repair.admission import sealed_record_findings
    else:
        from code_repair.admission import sealed_record_findings
    return sealed_record_findings(obj, where), "code_repair"


def check_line(obj, where, factory_staging=False):
    """Route an object to the right checker based on its shape."""
    if not isinstance(obj, dict):
        return [f"{where}: record must be a JSON object"], "unknown"
    if obj.get("family") == "python-function-repair":
        return _route_code_repair(obj, where)
    for required_keys, kind, route in _LINE_ROUTES:
        if not all(k in obj for k in required_keys):
            continue
        errors = route(obj, where, factory_staging)
        if factory_staging and kind in _STAGING_FINISHED_KINDS:
            errors = _finish_agentic(errors, obj, where, kind)
        return errors, kind
    return [f"{where}: unrecognized record shape (keys: {sorted(obj)[:8]})"], "unknown"


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Validate a dated factory run under outputs/raw/<date>/.",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="write manifest.json into run_dir (default: print totals only)",
    )
    parser.add_argument("run_dir", help="run directory containing .jsonl files")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    run_dir = Path(args.run_dir).resolve()
    manifest = {"run_dir": str(run_dir), "files": [], "totals": {}, "errors": []}
    kind_totals = {}

    for path in sorted(run_dir.rglob("*.jsonl")):
        rel = path.relative_to(run_dir)
        entry = {"file": str(rel), "records": 0, "kinds": {}, "errors": []}
        try:
            # Decode the physical bytes without universal-newline translation.
            # JSONL uses literal LF delimiters; a bare CR is JSON whitespace
            # inside one physical record, not a second record boundary.
            text = path.read_bytes().decode("utf-8")
        except UnicodeDecodeError as exc:
            entry["errors"].append(f"{rel}: invalid UTF-8: {exc}")
            manifest["files"].append(entry)
            manifest["errors"].extend(entry["errors"])
            continue
        # JSONL is delimited by literal LF bytes.  ``str.splitlines()`` also
        # splits at U+2028/U+2029, which are valid characters inside a JSON
        # string and would turn one valid record into several invalid lines.
        for lineno, line in enumerate(text.split("\n"), 1):
            if not line.strip():
                continue
            where = f"{rel}:{lineno}"
            obj, input_error = _parse_exact_json_record(line)
            if input_error is not None:
                entry["errors"].append(f"{where}: {input_error}")
                continue
            errs, kind = check_line(obj, where)
            entry["records"] += 1
            entry["kinds"][kind] = entry["kinds"].get(kind, 0) + 1
            kind_totals[kind] = kind_totals.get(kind, 0) + 1
            entry["errors"].extend(errs)
        manifest["files"].append(entry)
        manifest["errors"].extend(entry["errors"])

    manifest["totals"] = {
        "files": len(manifest["files"]),
        "records": sum(f["records"] for f in manifest["files"]),
        "by_kind": kind_totals,
        "error_count": len(manifest["errors"]),
    }
    if args.write:
        (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")

    print(json.dumps(manifest["totals"], indent=2))
    for err in manifest["errors"]:
        print("ERROR:", err, file=sys.stderr)
    sys.exit(1 if manifest["errors"] else 0)


if __package__:
    _expose_package_sibling(__name__)


if __name__ == "__main__":
    main()
