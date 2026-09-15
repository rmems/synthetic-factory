#!/usr/bin/env python3
"""Multi-agent coordination checks shared by the run validator's routes."""

import sys

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling
    _assert_direct_sibling("validate_run_multi_agent")
    from . import validate_run_episode as _validate_run_episode
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "validate_run_multi_agent"
    )
    import validate_run_episode as _validate_run_episode


REQUIRED_KEYS = (
    "goal",
    "agents",
    "transcript",
    "disagreements",
    "resolution",
    "joint_outcome",
    "reward",
)


def _missing_field_errors(obj, where):
    return [
        f"{where}: multi_agent missing '{key}'"
        for key in REQUIRED_KEYS
        if key not in obj
    ]


def _disagreement_errors(obj, where):
    disagreements = obj.get("disagreements")
    if (
        not isinstance(disagreements, list)
        or not disagreements
        or any(not isinstance(item, str) or not item.strip() for item in disagreements)
    ):
        return [f"{where}: disagreements must be a non-empty array of strings"]
    return []


def _agent_entry_errors(agent, index, where, factory_staging):
    """Validate one agent roster entry and return (errors, role, mandate)."""
    errors = []
    role = agent.get("role") if isinstance(agent, dict) else None
    mandate = None
    if not isinstance(role, str) or not role.strip():
        errors.append(f"{where}: agents[{index}] needs a non-empty role")
        role = None
    else:
        role = role.strip()
    if factory_staging:
        mandate = agent.get("mandate") if isinstance(agent, dict) else None
        if not isinstance(mandate, str) or not mandate.strip():
            errors.append(f"{where}: agents[{index}] needs a non-empty mandate")
            mandate = None
        else:
            mandate = mandate.strip()
    return errors, role, mandate


def _agent_roster_errors(obj, where, factory_staging):
    """Validate the agents array and return (errors, declared_roles)."""
    agents = obj.get("agents")
    if not isinstance(agents, list) or len(agents) < 2:
        return [f"{where}: agents must be an array of at least 2 roles"], set()
    errors = []
    if factory_staging and len(agents) > 4:
        errors.append(f"{where}: coordination records allow at most 4 agents")
    roles = set()
    mandates = set()
    for index, agent in enumerate(agents):
        entry_errors, role, mandate = _agent_entry_errors(
            agent, index, where, factory_staging
        )
        errors += entry_errors
        if role is not None:
            roles.add(role)
        if mandate is not None:
            mandates.add(mandate)
    if len(roles) < 2:
        errors.append(f"{where}: agents must declare at least two distinct roles")
    if factory_staging and len(mandates) != len(agents):
        errors.append(f"{where}: agents must declare distinct mandates")
    return errors, roles


def _transcript_turn_errors(turn, index, where, roles, factory_staging, hooks):
    """Validate one transcript turn and return (errors, participating_role)."""
    label = f"{where}: transcript[{index}]"
    if not isinstance(turn, dict):
        return [f"{label} must be an object"], None
    errors = []
    speaker = turn.get("speaker")
    participating = None
    if not isinstance(speaker, str) or not speaker.strip():
        errors.append(f"{label} missing speaker")
    elif roles and speaker.strip() not in roles:
        errors.append(
            f"{label} speaker {speaker!r} is not a declared agent role"
        )
    else:
        participating = speaker.strip()
    content = turn.get("content")
    if not isinstance(content, str) or not content.strip():
        errors.append(f"{label} needs non-empty content")
    if factory_staging and "tool_call" in turn:
        errors += _validate_run_episode.staging_tool_turn_errors(
            turn, label, observable_basis_re=hooks.observable_basis_re
        )
    return errors, participating


def _transcript_errors(obj, where, roles, factory_staging, hooks):
    transcript = obj.get("transcript")
    if not isinstance(transcript, list) or not transcript:
        return [f"{where}: transcript must be a non-empty array"]
    errors = []
    participating_roles = set()
    for index, turn in enumerate(transcript):
        turn_errors, participating = _transcript_turn_errors(
            turn, index, where, roles, factory_staging, hooks
        )
        errors += turn_errors
        if participating is not None:
            participating_roles.add(participating)
    if roles and len(participating_roles) < 2:
        errors.append(
            f"{where}: transcript must include substantive turns from at least two declared roles"
        )
    return errors


def check_multi_agent(obj, where, factory_staging=False, hooks=None):
    """Validate a multi-agent coordination record."""
    hooks = _validate_run_episode.default_hooks() if hooks is None else hooks
    errs = _missing_field_errors(obj, where)
    errs += hooks.nonempty_text_field_errors(
        obj, where, ("goal", "resolution", "joint_outcome")
    )
    errs += _disagreement_errors(obj, where)
    roster_errors, roles = _agent_roster_errors(obj, where, factory_staging)
    errs += roster_errors
    errs += _transcript_errors(obj, where, roles, factory_staging, hooks)
    errs += hooks.require_reward(obj, where)
    reward = obj.get("reward")
    success = reward.get("success") if isinstance(reward, dict) else None
    if isinstance(success, bool) and not hooks.terminal_outcome_agrees(
        obj.get("joint_outcome"), success
    ):
        errs.append(f"{where}: joint_outcome must agree with reward.success")
    return errs


if __package__:
    _expose_package_sibling(__name__)
