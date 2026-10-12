#!/usr/bin/env python3
"""Shared constants and helpers for the release-delegation test modules.

The delegation surface is exercised through the committed
``release-delegation`` pack by two sibling modules (surface, plans). They
share the pack's task ids, paths and edit anchors, the ``agent`` tool
wrappers, and the environment builders that strip the fault menu, arm one
fault row, or replace the worker roster.
"""

from __future__ import annotations

import dataclasses

from tests import tool_world_test_support as support

from tool_world import faults as faults_mod

PACK = "release-delegation"
SHIP = "release.ship-feature"
VERIFY = "release.verify-claims"
SMOKE = "release.smoke-and-notes"
FACTORY = "tool-world-delegation-factory"
SEEDS = (1, 2, 3, 7)
BRIEF = "Create src/feature.py defining feature() and bump VERSION"
FEATURE_DEF = "def feature():"
FEATURE_PY = "src/feature.py"
APP_PY = "src/app.py"
CHANGELOG = "CHANGELOG.md"
SMOKE_TEST = "tests/test_feature.py"


def agent(env, action: str, **args) -> str:
    return env.step({"name": "agent", "args": {"action": action, **args}}).text


def spawn(env, role: str, **args) -> str:
    return agent(env, "spawn", role=role, brief=BRIEF, **args)


def workspace_call(env, name: str, **args) -> str:
    return env.step({"name": name, "args": args}).text


def report(env, value: str = "done") -> str:
    return env.step({"name": "report_result", "args": {"value": value}}).text


def plain_env(task_id: str = SHIP, seed: int = 0):
    """An environment on the task with its fault menu removed, so no seed can interfere."""
    pack = support.load_pack(PACK)
    task = dataclasses.replace(pack.task(task_id), faults=())
    return support.env_mod.Environment(pack, task, seed)


def fault_row(kind: str, role: str, **overrides) -> dict:
    row = {
        "id": f"test-{kind}",
        "surface": "delegation",
        "kind": kind,
        "tool": "agent",
        "selector": {"action": "spawn", "role": role},
        "occurrence": 1,
        "probability_percent": 100,
        "marker": "unused",
        "recovery": [],
        "retry": True,
    }
    row.update(overrides)
    return row


def row_env(row: dict, task_id: str = SHIP, seed: int = 0):
    """An environment whose task declares exactly the one fault ``row`` describes."""
    pack = support.load_pack(PACK)
    spec = faults_mod.fault_spec_from_row(row, "test")
    task = dataclasses.replace(pack.task(task_id), faults=(spec,))
    return support.env_mod.Environment(pack, task, seed)


def fault_env(kind: str, role: str, task_id: str = SHIP, seed: int = 0):
    """An environment whose task declares exactly one always-armed ``kind`` fault on ``role``."""
    return row_env(fault_row(kind, role), task_id, seed)


def workers_env(workers: dict, task_id: str = SHIP):
    """An environment on the pack with its workers replaced and the task's fault menu removed."""
    pack = support.load_pack(PACK)
    patched = dataclasses.replace(pack, workers=workers)
    task = dataclasses.replace(patched.task(task_id), faults=())
    return support.env_mod.Environment(patched, task, 0)


def files(env) -> dict[str, str]:
    return env.surface("workspace").files


def declared_faults(pack) -> list[tuple]:
    """Every ``(task, fault_spec)`` pair the pack's tasks declare, in task order."""
    return [(task, spec) for task in pack.tasks for spec in task.faults]
