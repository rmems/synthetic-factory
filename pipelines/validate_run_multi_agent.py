#!/usr/bin/env python3
"""Multi-agent coordination checks shared by the run validator's routes."""

import sys
from typing import NamedTuple

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling
    _assert_direct_sibling("validate_run_multi_agent")
    from . import validate_run_episode as _validate_run_episode
    from . import validate_run_episode_turns as _validate_run_episode_turns
    from . import validate_run_multi_agent_roster as _validate_run_multi_agent_roster
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "validate_run_multi_agent"
    )
    import validate_run_episode as _validate_run_episode
    import validate_run_episode_turns as _validate_run_episode_turns
    import validate_run_multi_agent_roster as _validate_run_multi_agent_roster


REQUIRED_KEYS = (
    "goal",
    "agents",
    "transcript",
    "disagreements",
    "resolution",
    "joint_outcome",
    "reward",
)


class _TurnCheck(NamedTuple):
    index: int
    where: str
    roles: set
    factory_staging: bool
    hooks: object


def _missing_field_errors(obj, where):
    return [
        f"{where}: multi_agent missing '{key}'"
        for key in REQUIRED_KEYS
        if key not in obj
    ]


def _invalid_disagreement_item(item):
    if not isinstance(item, str):
        return True
    return not item.strip()


def _invalid_disagreements(disagreements):
    if not isinstance(disagreements, list):
        return True
    if not disagreements:
        return True
    return any(_invalid_disagreement_item(item) for item in disagreements)


def _disagreement_errors(obj, where):
    if _invalid_disagreements(obj.get("disagreements")):
        return [f"{where}: disagreements must be a non-empty array of strings"]
    return []


def _undeclared_speaker(role, roles):
    if not roles:
        return False
    return role not in roles


def _speaker_errors(turn, label, roles):
    speaker = turn.get("speaker")
    if not isinstance(speaker, str):
        return [f"{label} missing speaker"], None
    role = speaker.strip()
    if not role:
        return [f"{label} missing speaker"], None
    if _undeclared_speaker(role, roles):
        return [f"{label} speaker {speaker!r} is not a declared agent role"], None
    return [], role


def _content_errors(turn, label):
    if _validate_run_episode_turns.nonempty_text(turn.get("content")):
        return []
    return [f"{label} needs non-empty content"]


def _staged_tool_turn_errors(turn, label, check):
    if not check.factory_staging:
        return []
    if "tool_call" not in turn:
        return []
    return _validate_run_episode_turns.staging_tool_turn_errors(
        turn, label, observable_basis_re=check.hooks.observable_basis_re
    )


def _transcript_turn_errors(turn, check):
    """Validate one transcript turn and return (errors, participating_role)."""
    label = f"{check.where}: transcript[{check.index}]"
    if not isinstance(turn, dict):
        return [f"{label} must be an object"], None
    speaker_errors, participating = _speaker_errors(turn, label, check.roles)
    errors = speaker_errors
    errors += _content_errors(turn, label)
    errors += _staged_tool_turn_errors(turn, label, check)
    return errors, participating


def _empty_transcript(transcript):
    if not isinstance(transcript, list):
        return True
    return not transcript


def _too_few_participants(roles, participating_roles):
    if not roles:
        return False
    return len(participating_roles) < 2


def _transcript_errors(obj, check):
    transcript = obj.get("transcript")
    if _empty_transcript(transcript):
        return [f"{check.where}: transcript must be a non-empty array"]
    errors = []
    participating_roles = set()
    for index, turn in enumerate(transcript):
        turn_check = _TurnCheck(
            index, check.where, check.roles, check.factory_staging, check.hooks
        )
        turn_errors, participating = _transcript_turn_errors(turn, turn_check)
        errors += turn_errors
        if participating is not None:
            participating_roles.add(participating)
    if _too_few_participants(check.roles, participating_roles):
        errors.append(
            f"{check.where}: transcript must include substantive turns "
            "from at least two declared roles"
        )
    return errors


def _joint_outcome_errors(obj, where, hooks):
    reward = obj.get("reward")
    success = reward.get("success") if isinstance(reward, dict) else None
    if not isinstance(success, bool):
        return []
    if hooks.terminal_outcome_agrees(obj.get("joint_outcome"), success):
        return []
    return [f"{where}: joint_outcome must agree with reward.success"]


def check_multi_agent(obj, where, factory_staging=False, hooks=None):
    """Validate a multi-agent coordination record."""
    hooks = _validate_run_episode.default_hooks() if hooks is None else hooks
    errs = _missing_field_errors(obj, where)
    errs += hooks.nonempty_text_field_errors(
        obj, where, ("goal", "resolution", "joint_outcome")
    )
    errs += _disagreement_errors(obj, where)
    roster_errors, roles = _validate_run_multi_agent_roster.agent_roster_errors(
        obj, where, factory_staging
    )
    errs += roster_errors
    turn_check = _TurnCheck(0, where, roles, factory_staging, hooks)
    errs += _transcript_errors(obj, turn_check)
    errs += hooks.require_reward(obj, where)
    return errs + _joint_outcome_errors(obj, where, hooks)


if __package__:
    _expose_package_sibling(__name__)
