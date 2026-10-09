#!/usr/bin/env python3
"""The scripted solver: a task's gold plan, reacting to faults it reads in observations.

The policy sees only observation text. It detects a fault by the marker the
task declared, runs that fault's recovery actions, retries the interrupted
action when the fault says so, and captures values (an agent id, a ref, a
cursor) out of observations with the regexes the plan declares. Perturbed
variants make a declared mistake so the environment, not the author, labels
the resulting trajectory.
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .. import pack as pk
from .. import vocabulary as cv
from .._contract import OBSERVABLE_BASIS_RE, bind_import_twin

__all__ = ["Step", "Trajectory", "decision_basis", "policy_sha256", "run", "substitute"]

_CAPTURE_KEY = "$capture"
_GIVE_UP_TEXT = "giving up: the environment failed and no recovery is planned"


@dataclass(frozen=True)
class Step:
    n: int
    decision_basis: str
    tool_call: Mapping[str, Any]
    observation: str
    fault_id: str | None


@dataclass(frozen=True)
class Trajectory:
    variant: str
    steps: tuple[Step, ...]
    gave_up: bool
    faults_recovered: int


def policy_sha256() -> str:
    """Digest of this module's source bytes: the solver's version."""
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def decision_basis(prefix: str, intent: str) -> str:
    basis = f"{prefix}: {intent}"
    cv.refuse_when(
        prefix not in cv.DB_PREFIXES,
        cv.FINDING_DECISION_BASIS_INVALID,
        f"unknown basis prefix {prefix!r}",
    )
    cv.refuse_when(
        len(basis) > cv.MAX_DECISION_BASIS,
        cv.FINDING_DECISION_BASIS_INVALID,
        f"decision_basis exceeds {cv.MAX_DECISION_BASIS} chars: {basis[:60]!r}",
    )
    cv.refuse_when(
        OBSERVABLE_BASIS_RE.search(basis) is None,
        cv.FINDING_DECISION_BASIS_INVALID,
        f"decision_basis cites no observable evidence: {basis!r}",
    )
    return basis


def substitute(value: Any, captures: Mapping[str, str]) -> Any:
    """Replace ``{"$capture": name}`` leaves with captured observation text."""
    if isinstance(value, Mapping):
        if set(value) == {_CAPTURE_KEY}:
            name = value[_CAPTURE_KEY]
            cv.refuse_when(
                name not in captures, cv.FINDING_CAPTURE_FAILED, f"capture {name!r} was never taken"
            )
            return captures[name]
        return {key: substitute(item, captures) for key, item in value.items()}
    if isinstance(value, list):
        return [substitute(item, captures) for item in value]
    return value


def _capture(action: pk.Action, text: str, captures: dict[str, str]) -> None:
    for name, pattern in action.captures.items():
        match = re.search(pattern, text)
        cv.refuse_when(
            match is None or not match.groups(),
            cv.FINDING_CAPTURE_FAILED,
            f"capture {name!r} ({pattern!r}) found nothing in the observation",
        )
        captures[name] = match.group(1)


def _mangle(action: pk.Action) -> pk.Action:
    """A copy of the action whose first argument has the wrong type."""
    args = dict(action.tool_call["args"])
    cv.refuse_when(
        not args, cv.FINDING_TASK_FIELD_INVALID, "wrong_arg_type needs an action with arguments"
    )
    key = next(iter(args))
    args[key] = 7 if isinstance(args[key], str) else str(args[key])
    return pk.Action(
        intent=f"{action.intent} (first attempt sends the wrong argument type)",
        tool_call={"name": action.tool_call["name"], "args": args},
        captures={},
        verification=action.verification,
        confirmation=action.confirmation,
    )


def _plan(task: pk.Task, variant: str) -> list[tuple[str, pk.Action]]:
    cv.refuse_when(
        variant != cv.VARIANT_GOLD and variant not in task.perturbations,
        cv.FINDING_TASK_FIELD_INVALID,
        f"task {task.task_id} does not declare perturbation {variant!r}",
    )
    actions = list(task.gold)
    if variant == cv.PERTURBATION_SKIP_VERIFICATION:
        actions = [action for action in actions if not action.verification]
    if variant == cv.PERTURBATION_SKIP_CONFIRMATION:
        actions = [action for action in actions if not action.confirmation]
    plan = [(cv.DB_PLAN, action) for action in actions]
    if variant == cv.PERTURBATION_WRONG_ARG_TYPE:
        plan.insert(0, (cv.DB_PLAN, _mangle(actions[0])))
    return plan


def _fault_for(text: str, task: pk.Task) -> Any:
    return next((spec for spec in task.faults if spec.marker in text), None)


def _recovery(fault: Any, action: pk.Action, where: str) -> list[tuple[str, pk.Action]]:
    steps = [
        (cv.DB_OBSERVATION, pk.action_from_row(row, f"{where}.recovery[{index}]"))
        for index, row in enumerate(fault.recovery)
    ]
    if fault.retry:
        retry = pk.Action(
            intent=f"the observation reported {fault.marker!r}; retry the interrupted tool call",
            tool_call=action.tool_call,
            captures=action.captures,
            verification=action.verification,
            confirmation=action.confirmation,
        )
        steps.append((cv.DB_OBSERVATION, retry))
    return steps


def run(env: Any, variant: str = cv.VARIANT_GOLD) -> Trajectory:
    """Drive ``env`` with the task's plan until it ends, gives up, or exhausts its budget."""
    task = env.task
    queue = _plan(task, variant)
    captures: dict[str, str] = {}
    steps: list[Step] = []
    recovered = 0
    gave_up = False
    while queue and not env.done:
        prefix, action = queue.pop(0)
        call = substitute(action.tool_call, captures)
        basis = decision_basis(prefix, action.intent)
        observation = env.step(call)
        steps.append(Step(len(steps) + 1, basis, call, observation.text, observation.fault_id))
        fault = _fault_for(observation.text, task)
        if fault is None:
            _capture(action, observation.text, captures)
            continue
        if variant == cv.PERTURBATION_GIVE_UP:
            gave_up = True
            if not env.done:
                report = {"name": cv.TOOL_REPORT, "args": {"value": _GIVE_UP_TEXT}}
                final = env.step(report)
                basis = decision_basis(
                    cv.DB_OBSERVATION, f"the tool call failed with {fault.marker!r}; stop here"
                )
                steps.append(Step(len(steps) + 1, basis, report, final.text, final.fault_id))
            break
        recovered += 1
        queue = _recovery(fault, action, f"{task.task_id}/{fault.fault_id}") + queue
    return Trajectory(variant, tuple(steps), gave_up, recovered)


bind_import_twin(__name__)
