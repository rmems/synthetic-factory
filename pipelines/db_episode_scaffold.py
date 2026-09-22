#!/usr/bin/env python3
"""Shared shape primitives for the DB and DBM designed episodes.

Lane modules deliberately retain their own wording, commands, identifiers,
validation, and serialization.  This module only owns the stable episode
envelope shared by both generators.
"""

from __future__ import annotations

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


def assemble_episode(
    *,
    episode_id: str,
    goal: str,
    plan: str,
    steps: list[dict[str, Any]],
    outcome: str,
    meta: dict[str, Any],
) -> dict[str, Any]:
    """Assemble the common envelope without changing lane-owned content."""
    return {
        "id": episode_id,
        "goal": goal,
        "plan": plan,
        "steps": steps,
        "outcome": outcome,
        "reward": {
            "success": True,
            "apply_fails": 2,
            "plan_changes": 1,
            "lock_timeouts": 1,
            "tests_passed": 4,
            "cost_steps": len(steps),
        },
        "meta": meta,
    }
