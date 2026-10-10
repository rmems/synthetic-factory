#!/usr/bin/env python3
"""Shared constants and helpers for the counter-workspace test modules.

The workspace surface is exercised through the committed ``counter-workspace``
pack by four sibling modules (tools, suites, faults, plans). They share the
pack's task ids, paths and edit anchors, the environment builders that strip
or arm faults, the scripted-run and record wrappers, and the tampering table
that fresh replay must reject.
"""

from __future__ import annotations

import dataclasses
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from tool_world_test_support import cv, env_mod, load_pack, make_env

# The support module goes first: it puts pipelines/ on sys.path for the imports below.
# isort: split
from tool_world import faults as faults_mod
from tool_world import records
from tool_world.policies import scripted

PACK = "counter-workspace"
ADD_SUB = "counter.add-sub"
DELETE_LOCK = "counter.delete-stale-lock"
DOCUMENT = "counter.document-timeout"
RENAME = "counter.rename-config-key"
TASKS = (ADD_SUB, DELETE_LOCK, DOCUMENT, RENAME)
FACTORY = "tool-world-workspace-factory"
SEEDS = (1, 2, 3, 7)
COUNTER = "src/counter.py"
LOCK = "locks/stale.lock"
NOTE = "docs/settings.md"
GET_ANCHOR = "    def get(self):"
SUB_METHOD = (
    "    def sub(self, delta):\n        self._value -= int(delta)\n        return self._value\n\n"
    "    def get(self):"
)
NO_CONFIRMATION = "no_irreversible_without_confirmation"
RENAMED_CONFIG_SHA256 = "eab60e54266f6a91d9e7b5f038a26ffcf435980403e599ebc7626932a8c95310"
EAGAIN = "error: EAGAIN temporary failure on"
TRUNCATED_TAIL = "[output truncated at 160 chars; read again with offset]"


def call(name: str, **args) -> dict:
    return {"name": name, "args": args}


def step(env, name: str, **args) -> str:
    return env.step(call(name, **args)).text


def names(trajectory) -> list[str]:
    return [item.tool_call["name"] for item in trajectory.steps]


def plain_env(task_id: str = ADD_SUB, seed: int = 0):
    """An environment on the task with its fault menu removed, so no seed can interfere."""
    pack = load_pack(PACK)
    task = dataclasses.replace(pack.task(task_id), faults=())
    return env_mod.Environment(pack, task, seed)


def fault_row(kind: str, tool: str, selector: dict | None, params: dict | None) -> dict:
    return {
        "id": f"test-{kind}",
        "surface": "workspace",
        "kind": kind,
        "tool": tool,
        "selector": selector or {},
        "occurrence": 1,
        "probability_percent": 100,
        "params": params or {},
        "marker": "unused",
        "recovery": [],
        "retry": True,
    }


def fault_env(kind: str, tool: str, selector: dict | None = None, params: dict | None = None):
    """An environment on add-sub whose task declares exactly one always-armed fault of ``kind``."""
    pack = load_pack(PACK)
    spec = faults_mod.fault_spec_from_row(fault_row(kind, tool, selector, params), "test")
    task = dataclasses.replace(pack.task(ADD_SUB), faults=(spec,))
    return env_mod.Environment(pack, task, 0)


def suites_env(suites: dict, task_id: str = ADD_SUB):
    """A fault-free environment whose pack declares exactly ``suites`` under tests/."""
    pack = dataclasses.replace(load_pack(PACK), tests=suites)
    task = dataclasses.replace(pack.task(task_id), faults=())
    return env_mod.Environment(pack, task, 0)


def add_sub(env) -> str:
    return step(env, "edit_file", path=COUNTER, old=GET_ANCHOR, new=SUB_METHOD)


def run_task(task_id: str, seed: int, variant: str = cv.VARIANT_GOLD):
    env = make_env(PACK, task_id, seed=seed)
    return env, scripted.run(env, variant)


def build_record(env, trajectory, draw: int = 1) -> dict:
    return records.build_record(
        env, trajectory, records.RunContext("0" * 64, "run", "0" * 64), draw
    )


# Replay must reject every edit to a generated record's label or projection. Each row
# names the tampering, the ``(task_id, variant)`` of the record it edits, and the edit.
MEASURED = (DOCUMENT, cv.PERTURBATION_SKIP_VERIFICATION)
FIRED = (ADD_SUB, cv.VARIANT_GOLD)
GOLD_DELETE = (DELETE_LOCK, cv.VARIANT_GOLD)


def _relabel_accept(record: dict) -> None:
    record["curation"]["decision"] = "accept"
    record["curation"]["reason_codes"] = []


def _regold(record: dict) -> None:
    record["training_view"]["meta"]["variant"] = cv.VARIANT_GOLD
    record["solver"]["tool_policy"] = "workspace-gold"


def _view_step(record: dict, index: int) -> dict:
    return record["training_view"]["steps"][index]


TAMPERINGS = (
    ("observation text", GOLD_DELETE, lambda r: _view_step(r, 0).update(observation="x")),
    (
        "training_view tool_call args",
        GOLD_DELETE,
        lambda r: _view_step(r, 3)["tool_call"]["args"].update(path=COUNTER),
    ),
    (
        "training_view tool_call name",
        GOLD_DELETE,
        lambda r: _view_step(r, 2).update(tool_call=call("delete_file", path="x")),
    ),
    ("measured record relabelled accept", MEASURED, _relabel_accept),
    ("perturbed variant relabelled gold", MEASURED, _regold),
    (
        "faults_fired emptied",
        FIRED,
        lambda r: r["payload"]["execution_evidence"].update(faults_fired=[]),
    ),
    ("hidden thought key", GOLD_DELETE, lambda r: _view_step(r, 0).update(thought="s")),
    (
        "decision_basis without evidence",
        GOLD_DELETE,
        lambda r: _view_step(r, 0).update(decision_basis="just do it"),
    ),
)
