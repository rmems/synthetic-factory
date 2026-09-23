#!/usr/bin/env python3
"""Shared shape primitives for the DB and DBM designed episodes.

Lane modules deliberately retain their own wording, commands, identifiers,
validation, and serialization.  This module only owns the stable episode
envelope shared by both generators.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


def bash(command: str) -> dict[str, Any]:
    return {"name": "bash", "args": {"command": command}}


def write(path: str, contents: str) -> dict[str, Any]:
    return {"name": "write", "args": {"path": path, "contents": contents}}


def step(
    number: int,
    decision_basis: str,
    tool_call: dict[str, Any],
    observation: str,
) -> dict[str, Any]:
    return {
        "n": number,
        "decision_basis": decision_basis,
        "tool_call": tool_call,
        "observation": observation,
    }


@dataclass(frozen=True)
class EpisodeAssembly:
    """Keyword bundle for :func:`assemble_episode` (keeps the helper arity low)."""

    episode_id: str
    goal: str
    plan: str
    steps: list[dict[str, Any]]
    outcome: str
    meta: dict[str, Any]


def assemble_episode(parts: EpisodeAssembly) -> dict[str, Any]:
    """Assemble the common envelope without changing lane-owned content."""
    return {
        "id": parts.episode_id,
        "goal": parts.goal,
        "plan": parts.plan,
        "steps": parts.steps,
        "outcome": parts.outcome,
        "reward": {
            "success": True,
            "apply_fails": 2,
            "plan_changes": 1,
            "lock_timeouts": 1,
            "tests_passed": 4,
            "cost_steps": len(parts.steps),
        },
        "meta": parts.meta,
    }
