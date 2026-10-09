#!/usr/bin/env python3
"""The deterministic environment: tools, state, observations, faults, verdict.

A solver proposes a tool call; the environment validates its arguments,
decides from the seeded schedule whether a fault fires, hands the call to the
owning surface, bounds the observation, and logs the event. Replay rebuilds
the same environment from ``(pack, task, seed)`` and feeds it the same calls,
so every observation digest and the final state digest must agree.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from . import faults, predicates, schema_lite, surfaces
from . import vocabulary as cv
from ._contract import bind_import_twin, rng, sha256_bytes, sha256_canonical
from .surfaces.base import ToolSpec, error_text

__all__ = ["Environment", "Event", "Observation", "bound_observation"]


@dataclass(frozen=True)
class Observation:
    text: str
    full_sha256: str
    truncated: bool
    fault_id: str | None


@dataclass(frozen=True)
class Event:
    n: int
    tool_call: Mapping[str, Any]
    observation_sha256: str
    fault_id: str | None
    truncated: bool

    def row(self) -> dict[str, Any]:
        return {
            "n": self.n,
            "tool_call": {"name": self.tool_call["name"], "args": dict(self.tool_call["args"])},
            "observation_sha256": self.observation_sha256,
            "fault_id": self.fault_id,
            "truncated": self.truncated,
        }


def bound_observation(text: str) -> tuple[str, bool]:
    if len(text) <= cv.MAX_OBSERVATION_CHARS:
        return text, False
    omitted = len(text) - cv.MAX_OBSERVATION_CHARS
    return text[: cv.MAX_OBSERVATION_CHARS] + f"\n[truncated {omitted} chars]", True


_CORE_TOOLS = (
    ToolSpec(
        cv.TOOL_REPORT,
        cv.CORE_SURFACE,
        "Report the final result of the task. Ends the useful part of the episode.",
        {
            "type": "object",
            "required": ["value"],
            "properties": {"value": {"type": "string"}},
            "additionalProperties": False,
        },
    ),
    ToolSpec(
        cv.TOOL_CONFIRM,
        cv.CORE_SURFACE,
        "Confirm an irreversible action before calling the tool that performs it.",
        {
            "type": "object",
            "required": ["action"],
            "properties": {"action": {"type": "string"}},
            "additionalProperties": False,
        },
    ),
)


class Environment:
    def __init__(self, pack: Any, task: Any, seed: int) -> None:
        cv.check_seed(seed)
        self.pack = pack
        self.task = task
        self.seed = seed
        self._stream = rng.DrawStream(seed)
        self._fault_engine = faults.FaultEngine(faults.schedule_faults(task.faults, self._stream))
        self._surfaces: dict[str, Any] = {}
        for name in task.surfaces:
            cv.refuse_when(
                name not in surfaces.REGISTRY,
                cv.FINDING_SURFACE_UNKNOWN,
                f"unknown surface {name!r}",
            )
            self._surfaces[name] = surfaces.REGISTRY[name](pack, task, self)
        for spec in task.faults:
            cv.refuse_when(
                spec.surface not in self._surfaces,
                cv.FINDING_FAULT_UNKNOWN,
                f"fault {spec.fault_id} names surface {spec.surface!r}, "
                "which the task does not use",
            )
            self._surfaces[spec.surface].check_fault_kind(spec.kind)
        self._tools: dict[str, ToolSpec] = {spec.name: spec for spec in _CORE_TOOLS}
        for surface in self._surfaces.values():
            for spec in surface.tools():
                cv.refuse_when(
                    spec.name in self._tools,
                    cv.FINDING_TOOL_UNKNOWN,
                    f"duplicate tool {spec.name!r}",
                )
                self._tools[spec.name] = spec
        for spec in task.faults:
            self._check_fault_target(spec)
        self._events: list[Event] = []
        self.reported: str | None = None
        self._confirmations: list[str] = []
        self.unconfirmed_irreversible = 0

    def _check_fault_target(self, spec: Any) -> None:
        """A fault names a registered tool of its own surface and selector keys that tool takes."""
        tool = self._tools.get(spec.tool)
        cv.refuse_when(
            tool is None or tool.surface != spec.surface,
            cv.FINDING_FAULT_UNKNOWN,
            f"fault {spec.fault_id} names tool {spec.tool!r}, which the {spec.surface} surface "
            "does not register",
        )
        properties = tool.input_schema.get("properties") or {}
        stray = sorted(key for key in spec.selector if key.split(".", 1)[0] not in properties)
        cv.refuse_when(
            bool(stray),
            cv.FINDING_FAULT_UNKNOWN,
            f"fault {spec.fault_id}: selector keys {stray} are not arguments of {spec.tool}; "
            f"known: {sorted(properties)}",
        )

    # --- introspection -----------------------------------------------------

    def surface(self, name: str) -> Any:
        cv.refuse_when(
            name not in self._surfaces,
            cv.FINDING_SURFACE_UNKNOWN,
            f"task {self.task.task_id} has no {name} surface",
        )
        return self._surfaces[name]

    @property
    def surfaces(self) -> Mapping[str, Any]:
        return dict(self._surfaces)

    @property
    def events(self) -> tuple[Event, ...]:
        return tuple(self._events)

    @property
    def fault_engine(self) -> faults.FaultEngine:
        return self._fault_engine

    @property
    def done(self) -> bool:
        return len(self._events) >= self.task.max_steps

    def tools(self) -> tuple[ToolSpec, ...]:
        return tuple(self._tools.values())

    def tool(self, name: str) -> ToolSpec | None:
        return self._tools.get(name)

    def last_observation_text(self) -> str:
        return self._last_text

    # --- stepping ------------------------------------------------------------

    def step(self, tool_call: Any) -> Observation:
        cv.refuse_when(
            self.done,
            cv.FINDING_BUDGET_EXHAUSTED,
            f"task {self.task.task_id} allows {self.task.max_steps} steps",
        )
        cv.refuse_when(
            not _is_tool_call(tool_call),
            cv.FINDING_TOOL_CALL_MALFORMED,
            "tool_call must carry a string name and an object args",
        )
        name, args = tool_call["name"], dict(tool_call["args"])
        text, fault_id = self._dispatch(name, args)
        bounded, truncated = bound_observation(text)
        full_sha256 = sha256_bytes(text.encode("utf-8"))
        self._events.append(
            Event(
                len(self._events) + 1,
                {"name": name, "args": args},
                full_sha256,
                fault_id,
                truncated,
            )
        )
        self._last_text = bounded
        return Observation(bounded, full_sha256, truncated, fault_id)

    _last_text = ""

    def _dispatch(self, name: str, args: Mapping[str, Any]) -> tuple[str, str | None]:
        """The observation text and the fault that fired on this call.

        An unknown tool and invalid arguments are errors that fire nothing; a
        valid call consults the schedule before the owning surface runs it.
        """
        spec = self._tools.get(name)
        if spec is None:
            return error_text(f"unknown tool {name!r}; available: {sorted(self._tools)}"), None
        problems = _validate(spec, args)
        if problems:
            return error_text(f"invalid arguments for {name}: " + "; ".join(problems)), None
        fault = self._fault_engine.check(name, args)
        fault_id = fault.fault_id if fault is not None else None
        return self._execute(spec, args, fault), fault_id

    def _execute(self, spec: ToolSpec, args: Mapping[str, Any], fault: Any) -> str:
        if spec.name == cv.TOOL_REPORT:
            self.reported = args["value"]
            return f"recorded result: {args['value']}"
        if spec.name == cv.TOOL_CONFIRM:
            self._confirmations.append(args["action"])
            return f"confirmed: {args['action']}"
        if spec.irreversible and not _unperformed(fault):
            self._account_irreversible(spec.name)
        return self._surfaces[spec.surface].execute(spec.name, args, fault)

    def _account_irreversible(self, name: str) -> None:
        """One pending confirmation naming the tool covers one performed irreversible call."""
        if name in self._confirmations:
            self._confirmations.remove(name)
        else:
            self.unconfirmed_irreversible += 1

    # --- digests and verdicts ----------------------------------------------

    def snapshot_digest(self) -> str:
        return sha256_canonical(
            {
                "surfaces": {
                    name: surface.state_view() for name, surface in self._surfaces.items()
                },
                "reported": self.reported,
                "confirmations": list(self._confirmations),
                "unconfirmed_irreversible": self.unconfirmed_irreversible,
            }
        )

    def replay_digest(self) -> str:
        """sha256 over the canonical ``(n, tool_call, observation_sha256, fault_id)`` sequence."""
        rows = [
            [event.n, event.row()["tool_call"], event.observation_sha256, event.fault_id]
            for event in self._events
        ]
        return sha256_canonical(rows)

    def verdict(self) -> dict[str, Any]:
        public = predicates.evaluate_all(self.task.public_predicates, self)
        hidden = predicates.evaluate_all(self.task.hidden_predicates, self)
        return {
            "public": public,
            "hidden": hidden,
            "success": all(public.values()) and all(hidden.values()),
        }


def _is_tool_call(value: Any) -> bool:
    """An object carrying a string ``name`` and an object ``args``."""
    return (
        isinstance(value, Mapping)
        and isinstance(value.get("name"), str)
        and isinstance(value.get("args"), Mapping)
    )


def _validate(spec: ToolSpec, args: Mapping[str, Any]) -> list[str]:
    return schema_lite.validate_args(spec.input_schema, args)


def _unperformed(fault: Any) -> bool:
    """A transient fault stops the call before the tool runs; a confirmation waits for the retry."""
    return fault is not None and fault.spec.kind == cv.FAULT_KIND_TRANSIENT


bind_import_twin(__name__)
