#!/usr/bin/env python3
"""The delegation surface: scripted workers an orchestrator spawns, briefs, and awaits.

Workers are pack members with reliability profiles (``delegation_workers``).
The environment authors every worker, so it knows the ground truth of each
report: whether a "done" claim is backed by the effects the worker actually
applied to the workspace. Verification before merge is therefore observable
in the event log.

Everything a profile or a task fault can get wrong is refused when the
environment is built, never mid-episode: a profile is shape-checked, a
delegation fault must attach to the ``spawn`` action of a role whose worker
declares a profile named after the fault kind, so no fault can fire without a
symptom and no episode can be aborted by a worker it has already spawned.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from .. import vocabulary as cv
from .._contract import bind_import_twin
from .base import Surface, ToolSpec, error_text
from .delegation_workers import FAULT_KINDS, PROFILE_DEFAULT, apply_effects, check_worker

__all__ = ["DelegationSurface"]

_ACTION_SPAWN = "spawn"
_ACTIONS = (_ACTION_SPAWN, "await", "send", "cancel", "list")
_CLAIM_DONE = "done"
# The workspace tools a claim is verified by; the workspace counts the qualifying calls.
_TOOL_RUN_TESTS = "run_tests"
_TOOL_READ_FILE = "read_file"


def _agent_schema(roles: list[str]) -> dict[str, Any]:
    return {
        "type": "object",
        "required": ["action"],
        "properties": {
            "action": {"type": "string", "enum": list(_ACTIONS)},
            "role": {"type": "string", "enum": roles},
            "brief": {"type": "string", "minLength": 1},
            "scope": {"type": "array", "items": {"type": "string"}},
            "agent_id": {"type": "string"},
            "message": {"type": "string"},
        },
        "additionalProperties": False,
    }


_SELECTOR_KEYS = frozenset(_agent_schema([])["properties"])


@dataclass
class _Agent:
    agent_id: str
    role: str
    brief: str
    scope: tuple[str, ...]
    profile_name: str
    profile: Mapping[str, Any]
    awaits: int = 0
    status: str = "working"
    answered: bool = False
    done_at: int | None = None
    effects_applied: bool = False
    messages: list[str] = field(default_factory=list)

    def view(self) -> dict[str, Any]:
        return {
            "role": self.role,
            "profile": self.profile_name,
            "status": self.status,
            "awaits": self.awaits,
            "done_at": self.done_at,
            "scope": list(self.scope),
        }


# --- verification evidence read from the event log ------------------------


def _in_scope(path: Any, scope: tuple[str, ...]) -> bool:
    return isinstance(path, str) and any(
        path == entry or path.startswith(entry.rstrip("/") + "/") for entry in scope
    )


def _verifies(tool_call: Mapping[str, Any], scope: tuple[str, ...]) -> bool:
    """A test run verifies any claim; a read verifies one only inside the claim's scope."""
    if tool_call["name"] == _TOOL_RUN_TESTS:
        return True
    return tool_call["name"] == _TOOL_READ_FILE and _in_scope(tool_call["args"].get("path"), scope)


class DelegationSurface(Surface):
    NAME = cv.SURFACE_DELEGATION
    FAULT_KINDS = FAULT_KINDS

    def __init__(self, pack: Any, task: Any, env: Any) -> None:
        super().__init__(pack, task, env)
        cv.refuse_when(
            not pack.workers,
            cv.FINDING_PACK_FIELD_INVALID,
            f"pack {pack.pack_id} declares no workers",
        )
        cv.refuse_when(
            cv.SURFACE_WORKSPACE not in task.surfaces,
            cv.FINDING_TASK_FIELD_INVALID,
            f"task {task.task_id}: delegation needs the workspace surface for worker effects",
        )
        for role, spec in pack.workers.items():
            check_worker(role, spec)
        for spec in task.faults:
            if spec.surface == self.NAME:
                self._check_fault(spec)
        self.agents: dict[str, _Agent] = {}
        self.claims: list[tuple[str, int]] = []

    def _check_fault(self, spec: Any) -> None:
        """A delegation fault is a worker profile, so it must attach to a spawn that has one."""
        where = f"task {self.task.task_id}: fault {spec.fault_id}"
        self.check_fault_kind(spec.kind)
        stray = sorted(set(spec.selector) - _SELECTOR_KEYS)
        cv.refuse_first(
            (
                (
                    spec.tool != cv.TOOL_AGENT,
                    cv.FINDING_TASK_FIELD_INVALID,
                    f"{where} must attach to the {cv.TOOL_AGENT} tool, not {spec.tool!r}",
                ),
                (
                    bool(stray),
                    cv.FINDING_TASK_FIELD_INVALID,
                    f"{where}: selector keys {stray} are not {cv.TOOL_AGENT} arguments",
                ),
                (
                    spec.selector.get("action") != _ACTION_SPAWN,
                    cv.FINDING_TASK_FIELD_INVALID,
                    (
                        f"{where}: selector must name action {_ACTION_SPAWN!r}; "
                        "a profile attaches when a worker is spawned"
                    ),
                ),
            )
        )
        for role in self._roles_matching(spec.selector, where):
            cv.refuse_when(
                spec.kind not in self.pack.workers[role]["profiles"],
                cv.FINDING_TASK_FIELD_INVALID,
                f"{where}: worker {role} declares no {spec.kind!r} profile",
            )

    def _roles_matching(self, selector: Mapping[str, Any], where: str) -> list[str]:
        role = selector.get("role")
        if role is None:
            return sorted(self.pack.workers)
        cv.refuse_when(
            role not in self.pack.workers,
            cv.FINDING_TASK_FIELD_INVALID,
            f"{where}: selector role {role!r} is not a worker of pack {self.pack.pack_id}",
        )
        return [role]

    def tools(self) -> tuple[ToolSpec, ...]:
        return (
            ToolSpec(
                cv.TOOL_AGENT,
                self.NAME,
                "Orchestrate workers: spawn a role with a brief and scope, "
                "then await, send, cancel, or list.",
                _agent_schema(sorted(self.pack.workers)),
                actions=_ACTIONS,
            ),
        )

    def execute(self, name: str, args: Mapping[str, Any], fault: Any) -> str:
        action = args["action"]
        if action == _ACTION_SPAWN:
            return self._spawn(args, fault)
        if action == "list":
            return self._list()
        agent = self.agents.get(args.get("agent_id", ""))
        if agent is None:
            return error_text(
                f"unknown agent_id {args.get('agent_id')!r}; known: {sorted(self.agents)}"
            )
        handlers = {
            "await": lambda: self._await(agent),
            "send": lambda: self._send(agent, args),
            "cancel": lambda: self._cancel(agent),
        }
        return handlers[action]()

    # --- actions -----------------------------------------------------------

    def _spawn(self, args: Mapping[str, Any], fault: Any) -> str:
        role = args.get("role")
        if role is None:
            return error_text("spawn needs role")
        if not args.get("brief"):
            return error_text("spawn needs a nonempty brief")
        profile_name = fault.spec.kind if fault is not None else PROFILE_DEFAULT
        agent_id = f"w{len(self.agents) + 1}"
        agent = _Agent(
            agent_id,
            role,
            args["brief"],
            tuple(args.get("scope") or ()),
            profile_name,
            self.pack.workers[role]["profiles"][profile_name],
        )
        self.agents[agent_id] = agent
        scope = ", ".join(agent.scope) if agent.scope else "(unscoped)"
        return f"spawned {agent_id} as {role}; scope: {scope}; brief acknowledged"

    def _await(self, agent: _Agent) -> str:
        if agent.status in ("cancelled", "done"):
            return self._settled(agent)
        question = agent.profile.get("question")
        if question and not agent.answered:
            agent.status = "question"
            return f"{agent.agent_id} asks: {question}"
        agent.awaits += 1
        if agent.awaits < agent.profile.get("awaits_needed", 1):
            return f"{agent.agent_id}: pending (still working on: {agent.brief})"
        self._complete(agent)
        report = agent.profile.get("report", "")
        claim = agent.profile.get("claim", _CLAIM_DONE)
        return f"{agent.agent_id} reports: {report} (claims: {claim})"

    @staticmethod
    def _settled(agent: _Agent) -> str:
        """An await on a delegate that already stopped repeats how it stopped."""
        if agent.status == "cancelled":
            return f"{agent.agent_id}: cancelled"
        claim = agent.profile.get("claim", _CLAIM_DONE)
        return f"{agent.agent_id}: already reported ({claim})"

    def _complete(self, agent: _Agent) -> None:
        agent.status = "done"
        agent.done_at = len(self.env.events) + 1
        if agent.profile.get("claim", _CLAIM_DONE) == _CLAIM_DONE:
            self.claims.append((agent.agent_id, agent.done_at))
        if not agent.effects_applied:
            agent.effects_applied = True
            files = self.env.surface(cv.SURFACE_WORKSPACE).files
            apply_effects(files, agent.profile.get("effects") or [])

    @staticmethod
    def _send(agent: _Agent, args: Mapping[str, Any]) -> str:
        message = args.get("message")
        if not message:
            return error_text("send needs message")
        agent.messages.append(message)
        if agent.status == "question":
            agent.answered, agent.status = True, "working"
            return f"{agent.agent_id} acknowledged the answer and resumed"
        return f"{agent.agent_id} acknowledged: {message}"

    @staticmethod
    def _cancel(agent: _Agent) -> str:
        agent.status = "cancelled"
        return f"cancelled {agent.agent_id}"

    def _list(self) -> str:
        if not self.agents:
            return "no agents spawned"
        return "\n".join(
            f"{agent.agent_id} ({agent.role}): {agent.status}" for agent in self.agents.values()
        )

    # --- predicates --------------------------------------------------------

    def verified_before_merge(self) -> bool:
        """At least one done claim, each checked against its scope before the result was reported.

        A ``run_tests`` call verifies any claim; a ``read_file`` call verifies a claim only
        when it reads a path inside the claiming worker's scope, so an unscoped claim needs a
        test run. Only calls the workspace counted (an existing file, a declared suite) qualify,
        and a trajectory that never obtained a done claim has verified nothing.
        """
        if not self.claims:
            return False
        report_at = next(
            (event.n for event in self.env.events if event.tool_call["name"] == cv.TOOL_REPORT),
            len(self.env.events) + 1,
        )
        return all(
            self._verified(self.agents[agent_id].scope, done_at, report_at)
            for agent_id, done_at in self.claims
        )

    def _verified(self, scope: tuple[str, ...], done_at: int, report_at: int) -> bool:
        counted = set(self.env.surface(cv.SURFACE_WORKSPACE).verification_events)
        return any(
            event.n in counted and _verifies(event.tool_call, scope)
            for event in self.env.events
            if done_at < event.n < report_at
        )

    def pending_count(self) -> int:
        return sum(1 for agent in self.agents.values() if agent.status in ("working", "question"))

    def spawned_count(self) -> int:
        return len(self.agents)

    def state_view(self) -> Any:
        return {agent_id: agent.view() for agent_id, agent in sorted(self.agents.items())}


bind_import_twin(__name__)
