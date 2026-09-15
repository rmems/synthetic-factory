#!/usr/bin/env python3
"""Agent-roster checks for multi-agent records in the run validator."""

import sys
from typing import NamedTuple

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling
    _assert_direct_sibling("validate_run_multi_agent_roster")
    from . import validate_run_episode_turns as _validate_run_episode_turns
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "validate_run_multi_agent_roster"
    )
    import validate_run_episode_turns as _validate_run_episode_turns


class RosterState(NamedTuple):
    roles: set
    mandates: set
    count: int
    where: str
    factory_staging: bool


def _nonempty_text(value):
    return _validate_run_episode_turns.nonempty_text(value)


def _agent_entry_errors(agent, index, where, factory_staging):
    """Validate one agent roster entry and return (errors, role, mandate)."""
    errors = []
    role = agent.get("role") if isinstance(agent, dict) else None
    mandate = None
    if _nonempty_text(role):
        role = role.strip()
    else:
        errors.append(f"{where}: agents[{index}] needs a non-empty role")
        role = None
    if not factory_staging:
        return errors, role, mandate
    mandate = agent.get("mandate") if isinstance(agent, dict) else None
    if _nonempty_text(mandate):
        return errors, role, mandate.strip()
    errors.append(f"{where}: agents[{index}] needs a non-empty mandate")
    return errors, role, None


def _too_few_agents(agents):
    if not isinstance(agents, list):
        return True
    return len(agents) < 2


def _collect_roster(agents, where, factory_staging):
    errors = []
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
    return errors, roles, mandates


def _roster_distinctness_errors(state):
    errors = []
    if len(state.roles) < 2:
        errors.append(
            f"{state.where}: agents must declare at least two distinct roles"
        )
    if not state.factory_staging:
        return errors
    if len(state.mandates) != state.count:
        errors.append(f"{state.where}: agents must declare distinct mandates")
    return errors


def agent_roster_errors(obj, where, factory_staging):
    """Validate the agents array and return (errors, declared_roles)."""
    agents = obj.get("agents")
    if _too_few_agents(agents):
        return [f"{where}: agents must be an array of at least 2 roles"], set()
    size_errors = []
    if factory_staging:
        if len(agents) > 4:
            size_errors.append(f"{where}: coordination records allow at most 4 agents")
    errors, roles, mandates = _collect_roster(agents, where, factory_staging)
    errors += _roster_distinctness_errors(
        RosterState(roles, mandates, len(agents), where, factory_staging)
    )
    return size_errors + errors, roles


if __package__:
    _expose_package_sibling(__name__)
