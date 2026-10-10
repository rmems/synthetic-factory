#!/usr/bin/env python3
"""What every surface shares: the tool spec, the surface protocol, text helpers."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

from .. import vocabulary as cv
from .._contract import bind_import_twin, canonical_bytes

__all__ = ["Surface", "ToolSpec", "canonical_text", "error_text"]


@dataclass(frozen=True)
class ToolSpec:
    name: str
    surface: str
    description: str
    input_schema: Mapping[str, Any]
    irreversible: bool = False
    actions: tuple[str, ...] = field(default_factory=tuple)

    def declared(self) -> dict[str, Any]:
        """The description a solver is shown, canonical and free of state."""
        row = {
            "name": self.name,
            "surface": self.surface,
            "description": self.description,
            "input_schema": self.input_schema,
            "irreversible": self.irreversible,
        }
        if self.actions:
            row["actions"] = list(self.actions)
        return row


def canonical_text(value: Any) -> str:
    return canonical_bytes(value).decode("ascii")


def error_text(message: str) -> str:
    return f"error: {message}"


class Surface:
    """A tool surface: state plus the tools that read and write it.

    ``execute`` receives the scheduled fault that fires on this call, or
    ``None``; it is the only place a fault turns into an observation, so the
    fault's effect is as computed as any other observation.
    """

    NAME = ""
    FAULT_KINDS: frozenset[str] = frozenset()
    # Fault kinds whose symptom only some calls can show, each by a predicate over the call's
    # arguments; a kind absent here shows on every call its selector matches.
    SHOWS_ON: Mapping[str, Callable[[Mapping[str, Any]], bool]] = MappingProxyType({})

    def __init__(self, pack: Any, task: Any, env: Any) -> None:
        self.pack = pack
        self.task = task
        self.env = env

    def tools(self) -> tuple[ToolSpec, ...]:
        raise NotImplementedError

    def execute(self, name: str, args: Mapping[str, Any], fault: Any) -> str:
        raise NotImplementedError

    def state_view(self) -> Any:
        raise NotImplementedError

    def fault_shows(self, spec: Any, args: Mapping[str, Any]) -> bool:
        """Whether a call with ``args`` could show the fault's symptom; one that could not is skipped."""
        shows = self.SHOWS_ON.get(spec.kind)
        return shows is None or shows(args)

    def check_fault_kind(self, kind: str) -> None:
        cv.refuse_when(
            kind not in self.FAULT_KINDS,
            cv.FINDING_FAULT_UNKNOWN,
            f"surface {self.NAME} has no fault kind {kind!r}; known: {sorted(self.FAULT_KINDS)}",
        )


bind_import_twin(__name__)
