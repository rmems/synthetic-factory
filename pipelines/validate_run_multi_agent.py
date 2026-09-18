#!/usr/bin/env python3
"""Multi-agent coordination-record checks shared by the run validator's routes.

Every rule reads observable fields only: the declared agent roles and
mandates, the transcript that must show those roles taking part, and the
joint outcome that must agree with reward.success. Tool turns reuse the
episode sibling's staging checker so a coordination record and an episode
reject the same hidden-reasoning and ungrounded-basis shapes.
"""

import sys
from typing import NamedTuple

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling
    _assert_direct_sibling("validate_run_multi_agent")
    from . import validate_run_episode as _validate_run_episode
    from . import validate_run_rewards as _validate_run_rewards
    from . import validate_run_safety as _validate_run_safety
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "validate_run_multi_agent"
    )
    import validate_run_episode as _validate_run_episode
    import validate_run_rewards as _validate_run_rewards
    import validate_run_safety as _validate_run_safety


MULTI_AGENT_REQUIRED_KEYS = (
    "goal",
    "agents",
    "transcript",
    "disagreements",
    "resolution",
    "joint_outcome",
    "reward",
)
MULTI_AGENT_TEXT_FIELDS = ("goal", "resolution", "joint_outcome")
# Factory staging caps a coordination record at this many agents.
STAGING_MAX_AGENTS = 4

require_reward = _validate_run_rewards.require_reward
nonempty_text_field_errors = _validate_run_safety.nonempty_text_field_errors
staging_tool_turn_errors = _validate_run_episode.staging_tool_turn_errors
_outcome_agreement_errors = _validate_run_episode._outcome_agreement_errors


class MultiAgentRecord(NamedTuple):
    """One multi-agent record with the staging mode it is validated under."""

    obj: dict
    where: str
    factory_staging: bool


def _disagreement_errors(record):
    disagreements = record.obj.get("disagreements")
    if (
        not isinstance(disagreements, list)
        or not disagreements
        or any(not isinstance(item, str) or not item.strip() for item in disagreements)
    ):
        return [f"{record.where}: disagreements must be a non-empty array of strings"]
    return []


def _stripped_field(agent, field):
    """Return the stripped non-empty string field of an agent, else None."""
    value = agent.get(field) if isinstance(agent, dict) else None
    if not isinstance(value, str) or not value.strip():
        return None
    return value.strip()


def _agent_declaration_errors(agent, index, record):
    """Return (errors, role, mandate) for one declared agent; None when missing."""
    errs = []
    role = _stripped_field(agent, "role")
    if role is None:
        errs.append(f"{record.where}: agents[{index}] needs a non-empty role")
    mandate = None
    if record.factory_staging:
        mandate = _stripped_field(agent, "mandate")
        if mandate is None:
            errs.append(f"{record.where}: agents[{index}] needs a non-empty mandate")
    return errs, role, mandate


def _agent_errors(record):
    """Return (errors, declared roles) for the agents array."""
    agents = record.obj.get("agents")
    roles = set()
    if not isinstance(agents, list) or len(agents) < 2:
        return [f"{record.where}: agents must be an array of at least 2 roles"], roles
    errs = []
    if record.factory_staging and len(agents) > STAGING_MAX_AGENTS:
        errs.append(
            f"{record.where}: coordination records allow at most {STAGING_MAX_AGENTS} agents"
        )
    mandates = set()
    for index, agent in enumerate(agents):
        agent_errs, role, mandate = _agent_declaration_errors(agent, index, record)
        errs += agent_errs
        if role is not None:
            roles.add(role)
        if mandate is not None:
            mandates.add(mandate)
    if len(roles) < 2:
        errs.append(f"{record.where}: agents must declare at least two distinct roles")
    if record.factory_staging and len(mandates) != len(agents):
        errs.append(f"{record.where}: agents must declare distinct mandates")
    return errs, roles


def _transcript_turn_errors(turn, index, roles, record):
    """Return (errors, participating role) for one transcript turn."""
    label = f"{record.where}: transcript[{index}]"
    if not isinstance(turn, dict):
        return [f"{label} must be an object"], None
    errs = []
    participant = None
    speaker = turn.get("speaker")
    if not isinstance(speaker, str) or not speaker.strip():
        errs.append(f"{label} missing speaker")
    elif roles and speaker.strip() not in roles:
        errs.append(f"{label} speaker {speaker!r} is not a declared agent role")
    else:
        participant = speaker.strip()
    content = turn.get("content")
    if not isinstance(content, str) or not content.strip():
        errs.append(f"{label} needs non-empty content")
    if record.factory_staging and "tool_call" in turn:
        errs += staging_tool_turn_errors(turn, label)
    return errs, participant


def _transcript_errors(record, roles):
    """The transcript must show substantive turns from the declared roles."""
    transcript = record.obj.get("transcript")
    if not isinstance(transcript, list) or not transcript:
        return [f"{record.where}: transcript must be a non-empty array"]
    errs = []
    participating_roles = set()
    for index, turn in enumerate(transcript):
        turn_errs, participant = _transcript_turn_errors(turn, index, roles, record)
        errs += turn_errs
        if participant is not None:
            participating_roles.add(participant)
    if roles and len(participating_roles) < 2:
        errs.append(
            f"{record.where}: transcript must include substantive turns "
            "from at least two declared roles"
        )
    return errs


def _joint_outcome_errors(record):
    errs = require_reward(record.obj, record.where)
    errs += _outcome_agreement_errors(record.obj, record.where, "joint_outcome")
    return errs


def check_multi_agent(obj, where, factory_staging=False):
    """Validate a multi-agent coordination record layer by layer."""
    record = MultiAgentRecord(obj, where, factory_staging)
    errs = [f"{where}: multi_agent missing '{key}'" for key in MULTI_AGENT_REQUIRED_KEYS
            if key not in obj]
    errs += nonempty_text_field_errors(obj, where, MULTI_AGENT_TEXT_FIELDS)
    errs += _disagreement_errors(record)
    agent_errs, roles = _agent_errors(record)
    errs += agent_errs
    errs += _transcript_errors(record, roles)
    errs += _joint_outcome_errors(record)
    return errs


if __package__:
    _expose_package_sibling(__name__)
