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
from collections.abc import Callable, Mapping
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
        OBSERVABLE_BASIS_RE.search(intent) is None,
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
        if match is None or not match.groups():
            raise cv.ToolWorldRefusal(
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


def _unchanged(actions: list[pk.Action]) -> list[pk.Action]:
    return actions


def _without_verification(actions: list[pk.Action]) -> list[pk.Action]:
    return [action for action in actions if not action.verification]


def _without_confirmation(actions: list[pk.Action]) -> list[pk.Action]:
    return [action for action in actions if not action.confirmation]


def _mistyped_first(actions: list[pk.Action]) -> list[pk.Action]:
    """The gold plan behind one attempt whose first argument has the wrong type."""
    return [_mangle(actions[0]), *actions]


# variant -> the edit it makes to the gold plan before the first step
_PLAN_EDITS: Mapping[str, Callable[[list[pk.Action]], list[pk.Action]]] = {
    cv.VARIANT_GOLD: _unchanged,
    cv.PERTURBATION_SKIP_VERIFICATION: _without_verification,
    cv.PERTURBATION_SKIP_CONFIRMATION: _without_confirmation,
    cv.PERTURBATION_WRONG_ARG_TYPE: _mistyped_first,
    cv.PERTURBATION_GIVE_UP: _unchanged,
}


def _plan(task: pk.Task, variant: str) -> list[tuple[str, pk.Action]]:
    cv.refuse_when(
        variant != cv.VARIANT_GOLD and variant not in task.perturbations,
        cv.FINDING_TASK_FIELD_INVALID,
        f"task {task.task_id} does not declare perturbation {variant!r}",
    )
    return [(cv.DB_PLAN, action) for action in _PLAN_EDITS[variant](list(task.gold))]


def _fault_for(text: str, task: pk.Task) -> Any:
    return next((spec for spec in task.faults if spec.marker in text), None)


def _recovery(fault: Any, action: pk.Action) -> list[tuple[str, pk.Action]]:
    steps = [(cv.DB_OBSERVATION, recovery) for recovery in fault.recovery]
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


class _Episode:
    """One scripted run in progress: the plan queue, captures, steps, and how it ended."""

    def __init__(self, env: Any, variant: str) -> None:
        self.env = env
        self.task = env.task
        self.variant = variant
        self.queue = _plan(env.task, variant)
        self.captures: dict[str, str] = {}
        self.steps: list[Step] = []
        self.recovered = 0
        self.gave_up = False

    def record(self, basis: str, call: Any, observation: Any) -> None:
        self.steps.append(
            Step(len(self.steps) + 1, basis, call, observation.text, observation.fault_id)
        )

    def advance(self) -> bool:
        """Take the next planned step; False once the policy has given up."""
        prefix, action = self.queue.pop(0)
        call = substitute(action.tool_call, self.captures)
        observation = self.env.step(call)
        self.record(decision_basis(prefix, action.intent), call, observation)
        fault = _fault_for(observation.text, self.task)
        if fault is None:
            _capture(action, observation.text, self.captures)
        elif self.variant == cv.PERTURBATION_GIVE_UP:
            self.give_up(fault)
        else:
            self.recovered += 1
            self.queue[:0] = _recovery(fault, action)
        return not self.gave_up

    def give_up(self, fault: Any) -> None:
        """Stop at the first fault, reporting the give-up text unless the budget ended the run."""
        self.gave_up = True
        if self.env.done:
            return
        report = {"name": cv.TOOL_REPORT, "args": {"value": _GIVE_UP_TEXT}}
        basis = decision_basis(
            cv.DB_OBSERVATION, f"the tool call failed with {fault.marker!r}; stop here"
        )
        self.record(basis, report, self.env.step(report))

    def pending(self) -> bool:
        """Whether a planned step is still due: the queue is not empty and the budget holds."""
        return bool(self.queue) and not self.env.done

    def trajectory(self) -> Trajectory:
        return Trajectory(self.variant, tuple(self.steps), self.gave_up, self.recovered)


def run(env: Any, variant: str = cv.VARIANT_GOLD) -> Trajectory:
    """Drive ``env`` with the task's plan until it ends, gives up, or exhausts its budget."""
    episode = _Episode(env, variant)
    going = True
    while going and episode.pending():
        going = episode.advance()
    return episode.trajectory()


bind_import_twin(__name__)
