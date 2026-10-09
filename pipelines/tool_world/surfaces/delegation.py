#!/usr/bin/env python3
"""The delegation surface: scripted workers an orchestrator spawns, briefs, and awaits.

Workers are pack members with reliability profiles. The environment authors
every worker, so it knows the ground truth of each report: whether a "done"
claim is backed by the effects the worker actually applied to the workspace.
Verification before merge is therefore observable in the event log.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from .. import vocabulary as cv
from .._contract import bind_import_twin
from .base import Surface, ToolSpec, error_text

__all__ = ["DelegationSurface"]

PROFILE_DEFAULT = "default"
FAULT_LATE = "late"
FAULT_PARTIAL = "partial"
FAULT_WRONG_CLAIM = "wrong_claim"
FAULT_CONFLICTING = "conflicting"
FAULT_QUESTION = "question"
_ACTIONS = ("spawn", "await", "send", "cancel", "list")


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


class DelegationSurface(Surface):
    NAME = cv.SURFACE_DELEGATION
    FAULT_KINDS = frozenset(
        {FAULT_LATE, FAULT_PARTIAL, FAULT_WRONG_CLAIM, FAULT_CONFLICTING, FAULT_QUESTION}
    )

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
            profiles = spec.get("profiles") if isinstance(spec, Mapping) else None
            cv.refuse_when(
                not isinstance(profiles, Mapping) or PROFILE_DEFAULT not in profiles,
                cv.FINDING_PACK_FIELD_INVALID,
                f"worker {role} must declare a default profile",
            )
        self.agents: dict[str, _Agent] = {}
        self.claims: list[tuple[str, int]] = []

    def tools(self) -> tuple[ToolSpec, ...]:
        return (
            ToolSpec(
                cv.TOOL_AGENT,
                self.NAME,
                "Orchestrate workers: spawn a role with a brief and scope, await, send, cancel, list.",
                {
                    "type": "object",
                    "required": ["action"],
                    "properties": {
                        "action": {"type": "string", "enum": list(_ACTIONS)},
                        "role": {"type": "string", "enum": sorted(self.pack.workers)},
                        "brief": {"type": "string", "minLength": 1},
                        "scope": {"type": "array", "items": {"type": "string"}},
                        "agent_id": {"type": "string"},
                        "message": {"type": "string"},
                    },
                    "additionalProperties": False,
                },
                actions=_ACTIONS,
            ),
        )

    def execute(self, name: str, args: Mapping[str, Any], fault: Any) -> str:
        action = args["action"]
        if action == "spawn":
            return self._spawn(args, fault)
        if action == "list":
            return self._list()
        agent = self.agents.get(args.get("agent_id", ""))
        if agent is None:
            return error_text(
                f"unknown agent_id {args.get('agent_id')!r}; known: {sorted(self.agents)}"
            )
        return {"await": self._await, "send": self._send, "cancel": self._cancel}[action](
            agent, args
        )

    # --- actions -----------------------------------------------------------

    def _spawn(self, args: Mapping[str, Any], fault: Any) -> str:
        role = args.get("role")
        if role is None:
            return error_text("spawn needs role")
        if not args.get("brief"):
            return error_text("spawn needs a nonempty brief")
        profiles = self.pack.workers[role]["profiles"]
        profile_name = fault.spec.kind if fault is not None else PROFILE_DEFAULT
        cv.refuse_when(
            profile_name not in profiles,
            cv.FINDING_PACK_FIELD_INVALID,
            f"worker {role} declares no {profile_name!r} profile",
        )
        agent_id = f"w{len(self.agents) + 1}"
        agent = _Agent(
            agent_id,
            role,
            args["brief"],
            tuple(args.get("scope") or ()),
            profile_name,
            profiles[profile_name],
        )
        self.agents[agent_id] = agent
        scope = ", ".join(agent.scope) if agent.scope else "(unscoped)"
        return f"spawned {agent_id} as {role}; scope: {scope}; brief acknowledged"

    def _await(self, agent: _Agent, args: Mapping[str, Any]) -> str:
        if agent.status == "cancelled":
            return f"{agent.agent_id}: cancelled"
        if agent.status == "done":
            return f"{agent.agent_id}: already reported ({agent.profile.get('claim', 'done')})"
        question = agent.profile.get("question")
        if question and not agent.answered:
            agent.status = "question"
            return f"{agent.agent_id} asks: {question}"
        agent.awaits += 1
        if agent.awaits < int(agent.profile.get("awaits_needed", 1)):
            return f"{agent.agent_id}: pending (still working on: {agent.brief})"
        self._complete(agent)
        return f"{agent.agent_id} reports: {agent.profile.get('report', '')} (claims: {agent.profile.get('claim', 'done')})"

    def _complete(self, agent: _Agent) -> None:
        agent.status = "done"
        agent.done_at = len(self.env.events) + 1
        if agent.profile.get("claim", "done") == "done":
            self.claims.append((agent.agent_id, agent.done_at))
        if not agent.effects_applied:
            agent.effects_applied = True
            self._apply_effects(agent.profile.get("effects") or [])

    def _apply_effects(self, effects: list[Mapping[str, Any]]) -> None:
        files = self.env.surface(cv.SURFACE_WORKSPACE).files
        for effect in effects:
            if "write" in effect:
                files[effect["write"]] = effect.get("content", "")
            elif "append" in effect:
                files[effect["append"]] = files.get(effect["append"], "") + effect.get(
                    "content", ""
                )
            elif "delete" in effect:
                files.pop(effect["delete"], None)

    def _send(self, agent: _Agent, args: Mapping[str, Any]) -> str:
        message = args.get("message")
        if not message:
            return error_text("send needs message")
        agent.messages.append(message)
        if agent.status == "question":
            agent.answered, agent.status = True, "working"
            return f"{agent.agent_id} acknowledged the answer and resumed"
        return f"{agent.agent_id} acknowledged: {message}"

    def _cancel(self, agent: _Agent, args: Mapping[str, Any]) -> str:
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
        """Every done claim was followed by a workspace read or test run before the result was reported."""
        workspace = self.env.surface(cv.SURFACE_WORKSPACE)
        report_at = next(
            (event.n for event in self.env.events if event.tool_call["name"] == cv.TOOL_REPORT),
            len(self.env.events) + 1,
        )
        return all(
            any(done_at < at < report_at for at in workspace.verification_events)
            for _agent_id, done_at in self.claims
        )

    def pending_count(self) -> int:
        return sum(1 for agent in self.agents.values() if agent.status in ("working", "question"))

    def spawned_count(self) -> int:
        return len(self.agents)

    def state_view(self) -> Any:
        return {agent_id: agent.view() for agent_id, agent in sorted(self.agents.items())}


bind_import_twin(__name__)
